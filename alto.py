'''
Created on Jan 20, 2016

@author: Tom Morris <tfmorris@gmail.com>
'''
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from lxml import etree as ET
from array import array
from collections import Counter

class Alto(object):
    '''
    Class to read the ALTO XML format, as used by the British Library, for encoding OCR text.
    http://www.bl.uk/schemas/alto/alto-1-4.xsd
    
    Canonical ALTO info (current version is v3):
      https://github.com/altoxml/schema
      http://www.loc.gov/standards/alto/
      
    Interesting fields:
    
    /alto/Description/sourceImageInformation/fileName
    /alto/Styles
        TextStyle @ID FONTSIZE="10" FONTFAMILY="Courier New"
        ParagraphStyle @ID @ALIGN=Center|Left
    /alto/Layout/Page 
        Attributes: @ID @PHYSICAL_IMG_NR HEIGHT WIDTH POSITION=Cover/Left/Right/Single/Foldout QUALITY=OK ACCURACY=float% PC=1.0 (page confidence 0-1.0)
        TopMargin @HPOS VPOS WIDTH HEIGHT
        LeftMargin
        RightMargin
        BottonMargin
        PrintSpace
            ComposedBlock @TYPE=Illustration
                GraphicalElement
            TextBlock @STYLE_REFS="TXT_0 PAR_CENTER" (ids from Styles sections)
                TextLine
                    String @HPOS VPOS WIDTH HEIGHT WC="0.68" CC="00459" CONTENT="Myword" SUBS_TYPE="HypPart1|HypPart2"
                    SP space
                    HYP hyphen
    '''


    def __init__(self, xmlfile):
        '''
        Constructor
        '''
        self.xmlfile = xmlfile
        self.word_count = 0
        self.word_confidence = None # 0 - 1.0
        self.char_confidence = array('L',[0]*10) # 0=Good to 9=Bad
        self.hyphen1_count = 0
        self.hyphen2_count = 0
        self.text = ''
        self.page_accuracy=[]
        self.pages = 0
        self.styles = Counter()

        self.parse_file()

    def parseTextBlock(self, block):
        """
        Parse the lines, words, spaces, hyphens in a single text block.

        TODO: Do we need a parameter for paragraph indent, avg jitter, etc?
        """
        # TODO: Setting the threshold is key.  We should see a bimodal distribution
        # with lots of values near the left margin, a number near the nominal indent, and few in the middle
        # Perhaps pre-scan all TextBlocks/TextLines on page or in document?
        PARA_INDENT_THRESHOLD = 25 # This value is for experimentation ONLY!

        words = 0
        confidence = 0
        text = ''
        lmargin = None
        if 'STYLEREFS' in block.attrib:
            for s in block.attrib['STYLEREFS'].split():
                self.styles[s] +=1
        if 'HPOS' in block.attrib:
            lmargin = int(block.attrib['HPOS'])
            #print 'Block margin: ', lmargin
        else:
            raise Exception("Block with no HPOS, can't continue")
        firstLine = False
        paraStart = False
        for tl in block:
            if tl.tag == 'TextLine':
                if 'HPOS' in tl.attrib:
                    indent = int(tl.attrib['HPOS']) - lmargin
                    if indent > PARA_INDENT_THRESHOLD:
                        if firstLine:
                            paraStart = True
                        text += '\n\n'
                        #print '    New paragraph!', indent 
                    elif indent > PARA_INDENT_THRESHOLD/4 and indent <- PARA_INDENT_THRESHOLD:
                        print(' **Indent in the middle ', indent)
                        #print '  continuation: ', indent
                else:
                    raise Exception('Something bad happened - no HPOS in TextLine - aborting')
                for elem in tl:
                    if elem.tag == 'String':
                        text += elem.attrib['CONTENT']
                        words += 1
                        confidence += float(elem.attrib['WC'])
                        for c in elem.attrib['CC']:
                            self.char_confidence[int(c)] += 1
                        if 'SUBS_TYPE' in elem.attrib:
                            hy = elem.attrib['SUBS_TYPE']
                            if hy == 'HypPart1':
                                self.hyphen1_count += 1
                            elif hy == 'HypPart2':
                                self.hyphen2_count += 1
                            else:
                                print('Unrecognized SUBS_TYPE', hy)
                    elif elem.tag == 'SP':
                        text += ' '
                    elif elem.tag == 'HYP':
                        pass
                    else:
                        print('Unknown tag', elem.tag)
                if tl[-1].tag != 'HYP':
                    text += ' '
                firstLine = False
        return (words, confidence, text, paraStart)
        
    def parse_file(self):
        confidence = 0
        words = 0
        # TODO: Count pages, extract <Page @ACCURACY>
        # TODO: Analyze <TextBlock @STYLEREFS @ROTATION
        # TODO: Analyze <TextLine
        context = ET.iterparse(self.xmlfile, tag='Page') 
        for event, page in context:  # @UnusedVariable
            self.pages += 1
            if 'ACCURACY' in page.attrib:
                self.page_accuracy.append(float(page.attrib['ACCURACY']))
            leaf = page.attrib['PHYSICAL_IMG_NR']
            pageno=''
            if 'PRINTED_IMG_NR' in page.attrib:
                pageno = page.attrib['PRINTED_IMG_NR']
            # TODO: page markers should be moved out of band (or elided for plain text formats)
            self.text += '\n\n--Page: %s, Leaf: %s--\n' % (pageno, leaf)
            pageStart = True
            for ps in page:
                # Note: Text can also live in the margins TopMargin, BottomMargin, etc if the layout analysis messes up
                if ps.tag == 'PrintSpace':
                    for tb in ps:
                        if tb.tag == 'TextBlock':
                            (w, c, t, beginningPara) = self.parseTextBlock(tb)
                            words += w 
                            confidence += c 
                            if pageStart and not beginningPara:
                                self.text += " " + t # TODO: Deal with cross page hyphenatoin
                            else:
                                self.text += '\n\n' + t
                        elif tb.tag == 'ComposedBlock':
                            # TODO: Can this be anything other than a picture?
                            pass
                        else:
                            print('Unknown tag in <PrintSpace> ', tb.tag)
                elif ps.tag in ['TopMargin', 'LeftMargin', 'RightMargin','BottomMargin']:
                    pass
                else:
                    print('Unknown tag on <Page> ', ps.tag)
            page.clear() # Clear the page now that we're done with it
        if words:
            self.word_confidence = confidence / words
        self.word_count = words
        if self.pages > 1:
            # TODO: We kind of assumge one page per file now because that's the BL use case
            print('WARNING: Multi-page file: %d pages' % self.pages)

def test():
    # Simple single page test
    a = Alto('./data/000000037/ALTO/000000037_000010.xml')
    print(a.text)
    print(a.word_count, a.word_confidence, a.char_confidence)
    
    # Run through a whole bunch of pages
    files = {'data/000000037/000000037_0_1-42pgs__944211_dat.zip',
             'data/000000196/000000196_0_1-164pgs__1031646_dat.zip',
             'data/000000206/000000206_0_1-256pgs__594984_dat.zip',
             'data/000000216/000000216_1_1-318pgs__632698_dat.zip',
             }
    from zipfile import ZipFile
    print('    File', 'Words', 'Word Confidence (0-1.0)', 'CharCount')
    for f in files:
        words = 0
        confidence = 0
        text = ''
        cc = array('L',[0]*10)
        styles = Counter()
        zf = ZipFile(f)
        for name in zf.namelist():
            if name.startswith('ALTO/0'):
                a = Alto(zf.open(name))
                if a.word_count:
                    text += a.text
                    words += a.word_count
                    for i in range(10):
                        cc[i] += a.char_confidence[i]
                    confidence += (a.word_confidence * a.word_count)
                    styles.update(a.styles)
                    if a.hyphen1_count != a.hyphen2_count:
                        print('Mismatched hyphenation count ', name, a.hyphen1_count, a.hyphen2_count)
                #print name,a.word_count, a.page_accuracy, a.word_confidence, a.char_confidence
                if a.word_confidence and abs(a.word_confidence*100.0 - a.page_accuracy[0]) > 2.0: # epsilon = 2%
                    print('Inaccurate page accuracy %2.2f %2.2f' % (a.page_accuracy[0], a.word_confidence))
            else:
                #print '   Skipped', name
                pass
        zf.close()
        #print text
        print(f.split('/')[1], words, confidence/words, len(text), styles.most_common())
#         tot = sum(cc)
#         for i in range(10):
#             print i, '*'*(cc[i]*100/tot)


if __name__ == '__main__':
    test()
