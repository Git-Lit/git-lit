'''
Fetch system number for original print book from the British Library PRIMO
catalog based on the system number of the scanned digital record (there are
separate catalog records for each).  Without this mapping, our two sets of
metadata share no common identifiers.

This ran in about 12 hours for 50K identifiers with a 0.5 second pause between
queries with only 11 of the 50K queries failing to identify the original.

Created on Jan 27, 2016

@author: Tom Morris <tfmorris@gmail.com>
@license: Apache License 2.0
'''

from lxml import etree as ET
import requests
import requests_cache
import time

CATALOG_TEMPLATE = 'http://primocat.bl.uk/F/?func=direct&local_base=PRIMO&doc_number=%s'
# Full viewer URL - http://access.bl.uk/item/viewer/lsidyv39e6ab44#ark:/81055/vdc_00000003D6EB.0x000009
# (the piece after the dot is a hex-encoded page number)
VIEWER_TEMPLATE = 'http://access.bl.uk/item/viewer/%s'

def make_throttle_hook(timeout=1.0):
    """
    Returns a response hook function which sleeps for `timeout` seconds if
    response is not cached
    """
    def hook(response, *args, **kw_args):
        if not getattr(response, 'from_cache', False):
            #print 'sleeping'
            # This doesn't account for response latency, so rate will be less
            # (perhaps much less) than 1/timeout per sec.
            time.sleep(timeout)
        return response
    return hook

def getWithRetry(session, url):
    tries = 3
    while tries:
        tries -= 1
        response = session.get(url)
        if response.status_code != requests.codes.ok:
            print('Failed to fetch %d %s' % (response.status_code, url))
            if response.status_code >= 500 and tries:
                print('Sleeping before retry')
                time.sleep(2**(3-tries))
    return response

def getPrintId(session, digitalId):
    url = CATALOG_TEMPLATE % digitalId
    originalId = None
    response = getWithRetry(session, url)

    if response.status_code == requests.codes.ok:
        doc = ET.HTML(response.content)
        relatedLinks = doc.findall('.//td[@class="td1"]/a[@href]')
        if len(relatedLinks) > 0:
            href = relatedLinks[0].attrib['href']
            candidate = href.split('=')[-1]
            if len(candidate) > 0:
                originalId = candidate
    return originalId

def getARK(session, lsid):
    """
    Get ARK from lsid
    """
    url = VIEWER_TEMPLATE % lsid
    ark = None
    response = session.get(url)
    if response.status_code == requests.codes.ok:
        doc = ET.HTML(response.content)
        inputItemId = doc.findall('.//input[@id="ItemID"]') # type = "hidden"
        ark = 'None'
        if len(inputItemId) > 0:
            ark = inputItemId[0].attrib['value']
    return ark

def main():
    requests_cache.install_cache("british-library-catalog")
    session = requests_cache.CachedSession()
    session.hooks = {'response': make_throttle_hook(0.5)} # Be polite - less than 2 req/sec

    print('\t'.join(['Print ID', 'Scan ID', 'DOM ID', 'ARK']))

    with open('metadata/booklist.tsv') as input:
        for line in input:
            if line.startswith('Aleph'): #skip header
                continue
            line = line.rstrip('\n')
            digitalId = line.split('\t')[0]
            originalId = getPrintId(session, digitalId)

            # This (disabled) section of code will translate lsid to ARK
            # in case we ever need it.  Right now the BL Viewer accepts raw
            # lsids, so it's unnecessary
            lsids = line.split('\t')[-1].split(' -- ')
            arks = []
            if False:
                for lsid in lsids:
                    ark = getARK(session, lsid)
                    arks.append(ark)

            print('\t'.join([originalId, digitalId,','.join(lsids),','.join(arks)]))



if __name__ == '__main__':
    main()