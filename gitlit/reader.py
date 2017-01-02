#!/usr/bin/python
# coding: utf-8
"""
Reader of metadata, and optionally text, for British Library
public domain corpus.
"""

from gitlit.alto import Alto
from array import array
from collections import Counter
import glob
import lxml.etree
import os
import re
import sys
import logging
#from IPython.display import display
# import pandas as pd
from unidecode import unidecode
from zipfile import ZipFile
import tempfile

# TODO: Move this to a template file for easy editing
INTRO = '<!-- This file was created from text provided by the British Library. --> \n\n\n'

class BLText:
    NAMESPACES = {'MODS': 'http://www.loc.gov/mods/v3',
                  'METS': 'http://www.loc.gov/METS/',
                  'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
                  'xlink': 'http://www.w3.org/1999/xlink'
                  }

    def __init__(self, zipfile, metadataOnly=False): 
        # Zipfiles look like:
        # 000000037_0_1-42pgs__944211_dat.zip
        # 000000216_1_1-318pgs__632698_dat.zip
        self.zipfile = zipfile
        pieces = os.path.basename(zipfile).split('_')
        self.book_id = pieces[0]
        self.volume = int(pieces[1])
        if self.volume:
            self.vol_id = self.book_id + '_%02d' % self.volume
        else: 
            self.vol_id = self.book_id

        with ZipFile(zipfile) as zf:
            # TODO: Check for an warn if there are multiple books in the same zip file
            # 00000037 is a file that can be used for testing
            fn = self.book_id + '_metadata.xml'
            with zf.open(fn) as f:
                self.metadata = lxml.etree.parse(f)

            self.pages = 0
            self.words = 0
            self.avg_word_confidence = 0
            self.text = INTRO
            self.cc = array('L',[0]*10)
            self.wc = array('L',[0]*Alto.WORD_CONFIDENCE_HISTOGRAM)
            self.styles = Counter()
    
            if not metadataOnly:
                self.loadText(zf)


    def loadText(self, zf):
        """  Parse page OCR files and merge individual page stats
        """
        confidence = 0
        continuation = None
        for name in zf.namelist():
            if name.startswith('ALTO/0'):
                with zf.open(name) as f:
                    a = Alto(f, continuation)
                    self.pages += 1
                    if a.word_count:
                        self.text += a.text
                        self.words += a.word_count
                        for i in range(10):
                            self.cc[i] += a.char_confidence[i]
                        for i in range(Alto.WORD_CONFIDENCE_HISTOGRAM):
                            self.wc[i] += a.word_confidence[i]
                        confidence += a.avg_word_confidence * a.word_count
                        self.styles.update(a.styles)
                    continuation = a.continuation
        if self.words: 
            self.avg_word_confidence = confidence / self.words
        else: 
            self.avg_word_confidence = 0


    def getText(self, xpath):
        out = self.metadata.xpath(xpath + '/text()', namespaces=self.NAMESPACES)
        if isinstance(out, list): 
            if len(out) == 1: 
                # No sense having a list of length one. Get just the string. 
                out = out[0]
        return out
    
    @property
    def title(self):
        # TODO enable caching of this result
        # Be careful not to pick up related titles, etc.
        title = self.getText('//MODS:mods/MODS:titleInfo/MODS:title')
        logging.info('Title: %s' % title)
        if type(title) == list: 
            # FIXME. We're only taking the first of multiple titles,
            # since there's no structure in place for handling
            # multiple titles yet. 
            title = title[0] 
        out = self.removeBracketed(title)
        if self.volume: 
            out += " (Volume %s)" % self.volume
        return out

    def removeBracketed(self, s):
        return re.sub(r'\[[^\]]*\]', '', s).strip()

    @property
    def author(self): 
        rawAuthor = self.getText('//MODS:name[@type="personal"]/MODS:namePart')
        # TODO: do some transformations to the text here. Get it in the appropriate case.
        # Also handle multiple authors better
        return rawAuthor

    @property
    def githubTitle(self):
        oldTitle = self.title
        textID = self.book_id
        idLength = len(textID)
        oldTitle = re.sub(r'[^\w\s-]','',oldTitle)
        titleNoSpace = re.sub(r'[\s]','-',oldTitle)
        # Replace non-ASCII characters with their closest
        # ASCII equivalents. See https://pypi.python.org/pypi/Unidecode
        cleanTitle = unidecode(titleNoSpace)
        newTitle = cleanTitle[:100-idLength]+'-'+textID
        return newTitle

    def __str__(self): 
        return "title: {}\nauthor: {}\ngithubTitle: {}\n".format(self.title, self.author, self.githubTitle)

# A collection of BLText objects. 
class BLCorpus(): 
    def __init__(self, corpus, metadataOnly=True):
        self.files = []
        if type(corpus) is str or type(corpus) is str:
            if os.path.isdir(corpus):
                self.baseDir = corpus
                for (path, dirs, files) in os.walk(corpus):  # @UnusedVariable
                    for f in files:
                        if f.endswith('_dat.zip'): # *pgs__*_dat.zip
                            self.files.append(os.path.join(path,f))
            elif os.path.isfile(corpus):
                self.baseDir = None
                with open(corpus) as f:
                    self.files = [l.rstrip('\n') for l in f.readlines()]
        elif type(corpus) is list or type(corpus) is tuple:
            # TODO: use try/except around list constructor instead of type test?
            self.files = list(corpus)
        else:
            raise Exception('Unknown corpus type')

        self.texts = []
        self.readDataDir(metadataOnly)
        #self.makeDataFrame()

    def readDataDir(self, metadataOnly): 
        #print 'Loading %d files' % len(files)
        self.texts = [ BLText(mdf, metadataOnly=metadataOnly) for mdf in self.files ]
        #print 'Loaded ',self.texts

#     def makeDataFrame(self): 
#        metadata = [ [ text.book_id, text.pages, text.title, text.author, text.githubTitle] for text in self.texts ] 
#         self.df = pd.DataFrame(metadata, columns=['ID', 'Title', 'Author'])
#         
#     def show(self): 
#         display(self.df)

def test():
    
    print('Testing corpus subdirectory constructor')
    c = BLCorpus('data')
    #c.df
    assert len(c.texts) == 10
    # assert len(c) == 10 # do we want to implement this?
    assert c.texts[0].book_id == '000000037'
    #print('Loaded %d texts. First is %s' % (len(c.texts), str(c.texts[0])))

    print('Testing corpus constructor with a list')
    c2 = BLCorpus(('data/000000037_0_1-42pgs__944211_dat.zip',
                  'data/000000196_0_1-164pgs__1031646_dat.zip',
                  'data/000000206_0_1-256pgs__594984_dat.zip',
                  ))
    assert len(c2.texts) == 3
    assert c2.texts[-1].book_id == '000000206'
    #print('Loaded %d texts. Last is %s' % (len(c2.texts), str(c2.texts[-1])))

    print('Testing file with list of filenames constructor')
    files = glob.glob('data/*pgs__*_dat.zip')
    with tempfile.NamedTemporaryFile() as tf:
        tf.write('\n'.join(files))
        tf.flush()
        c3 = BLCorpus(tf.name)
        assert len(c3.texts) == 10
        assert c3.texts[1].book_id == '000000196'
        #print('Loaded %d texts with the middle one being %s' % (len(c3.texts), c3.texts[1]))

    return c

if __name__ == '__main__':
    print('Beginning tests')
    test()
    print('Tests complete')

