#!/usr/bin/python
# coding: utf-8
"""
Reader of metadata, and optionally text, for British Library
public domain corpus.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from alto import Alto
from array import array
from collections import Counter
import glob
import lxml.etree
import os
import re
#from IPython.display import display
# import pandas as pd
from unidecode import unidecode
from zipfile import ZipFile

# TODO: Move this to a template file for easy editing
INTRO = '////\nThis file was created from text provided by the British Library. \n////\n\n'

class BLText:
    NAMESPACES = {'MODS': 'http://www.loc.gov/mods/v3',
                  'METS': 'http://www.loc.gov/METS/',
                  'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
                  'xlink': 'http://www.w3.org/1999/xlink'
                  }

    def __init__(self, zipfile, metadataOnly=True): 
        # Zipfiles look like:
        # data2/000000037/000000037_0_1-42pgs__944211_dat.zip
        # data2/000000216/000000216_1_1-318pgs__632698_dat.zip
        self.book_id = os.path.basename(zipfile).split('_')[0]
        self.textdir = os.path.dirname(zipfile)
        #print 'Loading ',zipfile
        zf = ZipFile(zipfile)
        # TODO: Check for an warn if there are multiple books in the same zip file
        # 00000037 is a file that can be used for testing
        fn = self.book_id + '_metadata.xml'
        with zf.open(fn) as f:
            self.metadata = lxml.etree.parse(f)

        self.pages = 0
        self.words = 0
        self.word_confidence = 0
        self.text = INTRO
        self.cc = array('L',[0]*10)
        self.styles = Counter()
        
        if not metadataOnly:
            self.loadText(zf)

        zf.close()


    def loadText(self, zf):
        """  Parse page OCR files and merge individual page stats
        """
        confidence = 0
        for name in zf.namelist():
            if name.startswith('ALTO/0'):
                with zf.open(name) as f:
                    a = Alto(f)
                    self.pages += 1
                    if a.word_count:
                        self.text += a.text
                        self.words += a.word_count
                        for i in range(10):
                            self.cc[i] += a.char_confidence[i]
                        
                        confidence += a.word_confidence * a.word_count
                        self.styles.update(a.styles)
        self.word_confidence = confidence / self.words


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
        return self.getText('//MODS:title')
  
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
    def __init__(self, corpusDir, metadataOnly=True):
        self.baseDir = corpusDir
        self.texts = []
        self.readDataDir(metadataOnly)
        #self.makeDataFrame()

    def readDataDir(self, metadataOnly): 
        metadatafiles = glob.glob(self.baseDir + "/**/*pgs__*_dat.zip")
        #print 'Loading %d files' % len(metadatafiles)
        self.texts = [ BLText(mdf, metadataOnly=metadataOnly) for mdf in metadatafiles ]
        self.metadata = [ [ text.book_id, text.pages, text.title, text.author, text.githubTitle] for text in self.texts ] 
        #print 'Loaded ',self.metadata
    
#     def makeDataFrame(self): 
#         self.df = pd.DataFrame(self.metadata, columns=['ID', 'Title', 'Author'])
#         
#     def show(self): 
#         display(self.df)

def test():
    c = BLCorpus('data')
    #c.df
    print(c.texts[0].textdir)
    return c

if __name__ == '__main__':
    print('Beginning test')
    test()
    print('Test complete')

