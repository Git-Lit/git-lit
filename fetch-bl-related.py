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

URL_TEMPLATE = 'http://primocat.bl.uk/F/?func=direct&local_base=PRIMO&doc_number=%s'

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

def main():
    requests_cache.install_cache("british-library-catalog")
    session = requests_cache.CachedSession()
    session.hooks = {'response': make_throttle_hook(0.5)} # Be polite - less than 2 req/sec

    print('\t'.join(['Print Id', 'Scan Id']))

    with open('metadata/booklist.tsv') as input:
        for line in input:
            if line.startswith('Aleph'): #skip header
                continue

            digitalId = line.split('\t')[0]
            url = URL_TEMPLATE % digitalId

            response = session.get(url)
            if response.status_code != requests.codes.ok:
                print('Failed to fetch %d %s' % (response.status_code, url))
                if response.status_code >= 500:
                     time.sleep(5)
                continue

            doc = ET.HTML(response.content)
            relatedLinks = doc.findall('.//td[@class="td1"]/a[@href]')
            originalId = 'None'
            if digitalId == '014608411':
                print(digitalId, relatedLinks)
            if len(relatedLinks) > 0:
                href = relatedLinks[0].attrib['href']
                candidate = href.split('=')[-1]
                if len(candidate) > 0:
                    originalId = candidate
            print('\t'.join([originalId, digitalId]))


if __name__ == '__main__':
    main()