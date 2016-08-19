'''
Extend our book metadata with the Aleph System Number for the original print
work in the British Library catalog and a computed language for the title.

The computed language is used both to catch errors in the existing metadata,
but, more frequently, to fill in the language for the 19k works which are 
missing it.

Created on Jan 27, 2016

@author: Tom Morris <tfmorris@gmail.com>
@license: Apache License 2.0
'''
import codecs
from collections import Counter
import iso639
import langdetect
from langdetect.lang_detect_exception import LangDetectException
import pycld2 as cld2
import re

BRACKET_RE = re.compile(r'\[[^\]]*\]')

def bib2std(code):
    """
    Translate a bibliographic variant ISO 639-2 three letter code to its 
    corresponding ISO 639-1 code which can be compared with the output from
    the language detectors.
    """
    entry = iso639.find(iso639_2=code)
    if not entry:
        pass # print('**Failed to find ISO 639-2 code: %s' % code)
        # Just return original code without translating
        # This may be a discontinued code like scc for Serbian (instead of the
        # now standard srp) since these don't appear to be included in the package
        #code = None
    elif u'iso639_1' in entry:
        code = entry[u'iso639_1']
    else:
        code = entry[u'iso639_2_t']
    return code

def cleanTitle(title):
    # Remote English boilerplate which exists in all records
    title = title.replace('[electronic resource]','').strip()
    # If the whole thing is an editorial comment, keep it.
    if title[0] == '[' and title[-1] == ']':
        title = title[1:-1]
    # Remove any other editorial comments (probably in English, so misleading)
    title = re.sub(BRACKET_RE, '', title).strip()
    return title

def main():

    lookup = dict()
    with open('metadata/crosswalk.tsv') as infile:
        for line in infile:
            if line.startswith('Print Id'):
                continue
            ids = line.split()
            if len(ids) < 2 or ids[0] == 'None': # Lines like '\tNNNN' split into a single element
                lookup[ids[0]] = None
            else:
                lookup[ids[1]] = ids[0]
    total = 0
    found = 0
    all_agree = 0
    new_agree = 0
    mismatch = 0
    langs = Counter()
    with codecs.open('metadata/booklist.tsv','r','utf-8') as infile:
        for line in infile:
            line = line.rstrip('\n')
            if line.startswith('Aleph'): # handle header
                print('Print sysnum\tFlag\tDetected Lang\tBest Lang\t%s' % line)
                continue
            total += 1
            fields = line.split('\t')
            scanId = fields[0]
            title = fields[7]
            title = cleanTitle(title)
            lang1 = 'unk'
            try:
                lang1 = langdetect.detect(title)
            except LangDetectException:
                # print(('Language detection failed for %s' % line).encode('utf-8'))
                pass
            title = title.encode('utf-8') # CLD2 needs UTF-8 bytes
            isReliable, textBytesFound, langDetails = cld2.detect(title)  # @UnusedVariable
            lang2 = 'unk'
            if isReliable:
                lang2 = langDetails[0][1]
            origLang = fields[2]
            if origLang and not origLang in ['und', 'mul']:
                origLang = bib2std(origLang)
            if not origLang:
                origLang = 'und'
            newLang = 'unk'
            flag = ''
            bestLang = origLang
            if lang1 == lang2:
                newLang = lang1
                if lang1 == origLang:
                    all_agree += 1
                elif not origLang in ['und', 'mul']:
                    mismatch += 1
                    flag = '*'
                    bestLang = lang1
                else:
                    new_agree += 1
                    if origLang != 'mul':
                        bestLang = lang1
            langs[newLang+'-'+origLang] += 1

            printId = 'None'
            if scanId in lookup:
                printId = lookup[scanId]
                found += 1

            # TODO: Blaclist pig latin, Klingon, etc
            #if lang == 'zzp':
            #    print(lang,title,line)

            print(('%s\t%s\t%s\t%s\t%s' % (printId, flag, newLang, bestLang, line)).encode('utf-8'))

    print('Found print ID for %d of %d total' % (found, total))
    print('Found %d title language mismatches, %d agreed new, %d all 3 agree, total = %d' % (mismatch, new_agree, all_agree, total))
    print('Language pair count: %d' %len(langs))
    # Print our language pairs (basically a confusion matrix)
    for k,v in langs.most_common(40):
        if k.find('-mul') < 0: # Skip multiple languages
            print("%s\t%5d\t%4.2f%%" % (k, v, v*100.0/total))

if __name__ == '__main__':
    main()
