'''
Created on Jan 27, 2016

@author: tfmorris
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
            time.sleep(timeout)
        return response
    return hook

def main():
    requests_cache.install_cache("british-library-catalog")
    session = requests_cache.CachedSession()
    session.hooks = {'response': make_throttle_hook(0.5)}

    print('\t'.join(['Print Id', 'Scan Id']))

    with open('metadata/booklist.tsv') as input:
        for line in input:
            digitalId = line.split('\t')[0]
            if digitalId.startswith('Aleph'): #skip header
                continue
            url = URL_TEMPLATE % digitalId
            response = session.get(url)
            if response.status_code != requests.codes.ok:
                print('Failed to fetch %d %s' % (response.status_code, url))
                if response.status_code >= 500:
                     time.sleep(5)
                continue
            doc = ET.HTML(response.content)
            foo = doc.findall('.//td[@class="td1"]/a[@href]') 
            href = foo[0].attrib['href']
            originalId = href.split('=')[-1]
            print('\t'.join([originalId, digitalId]))


if __name__ == '__main__':
    main()