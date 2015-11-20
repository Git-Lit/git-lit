# coding: utf-8

import lxml.etree
import os
from IPython.display import display
import pandas as pd
import sh
import unicodedata
import re

class BLText:
    FLICKR_TEMPLATE = 'https://www.flickr.com/photos/britishlibrary/tags/sysnum%s'
    # template below is magic - stolen from Flickr entry for BL photos
    BRITLIB_TEMPLATE = 'http://explore.bl.uk/primo_library/libweb/action/search.do?cs=frb&doc=BLL01%s&dscnt=1&scp.scps=scope:(BLCONTENT)&frbg=&tab=local_tab&srt=rank&ct=search&mode=Basic&dum=true&tb=t&indx=1&vl(freeText0)=%s&fn=search&vid=BLVU1'
    NAMESPACES = {'MODS': 'http://www.loc.gov/mods/v3'}
    
    def __init__(self, metadataFile): 
        textdir = '12345'
        self.book_id = os.path.basename(textdir) # alias
        #self.book_id = self.ID # another alias. TODO: simplify this
        self.tree = lxml.etree.parse(metadataFile)        
        #self.flickrURL =  BLText.FLICKR_TEMPLATE % self.ID
        #self.britLibURL = BLText.BRITLIB_TEMPLATE % (self.ID, self.ID)

    def getText(self, xpath):
        out = self.tree.xpath(xpath + '/text()', namespaces=BLText.NAMESPACES)
        if isinstance(out, list): 
            if len(out) == 1: 
                # No sense having a list of length one. Get just the string. 
                out = out[0]
        return out
    
    @property
    def title(self):
        # TODO enable caching of this result
        return self.getText('//MODS:title')
        
#    def getTitle(self): 
#        return self.getText('//MODS:title')
        
    @property
    def author(self): 
        rawAuthor = self.getText('//MODS:name[@type="personal"]/MODS:namePart')
        # TODO: do some transformations to the text here. Get it in the appropriate case. 
        return rawAuthor

    @property
    def githubTitle(self):
        oldTitle = self.title
        textID = self.book_id
        idLength = len(textID)
        oldTitle = re.sub(r'[^\w\s-]','',oldTitle)
        titleNoSpace = oldTitle.replace(' ','-')
        cleanTitle = str(unicodedata.normalize('NFKD', titleNoSpace).encode('ascii', 'ignore'))
        newTitle = titleNoSpace[:100-idLength]+textID
        return newTitle

    def printOut(self): 
        print( "title: {}\nauthor: {}\ngithubTitle: {}\n".format(self.title, self.author, self.githubTitle))

# A collection of BLText objects. 
class BLCorpus(): 
    def __init__(self, corpusDir):
        self.baseDir = corpusDir
        self.texts = []
        self.readDataDir()
        #self.makeDataFrame()

    def readDataDir(self): 
        textdirs = os.listdir(self.baseDir)
        print( 'textdirs: ' )
        for textdir in textdirs: 
            print( textdir )
        self.texts = [ BLText(os.path.join(self.baseDir,textdir, textdir+'_metadata.xml')) for textdir in textdirs ]
        self.metadata = [ [ text.ID, text.title, text.author ] for text in self.texts ] 
    
    def makeDataFrame(self): 
        self.df = pd.DataFrame(self.metadata, columns=['ID', 'Title', 'Author'])
        
    def show(self): 
        display(self.df)

#c = BLCorpus('data2')
#c.df
#c.texts[0].textdir
