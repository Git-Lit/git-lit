'''
Created on Jan 20, 2016

@author: Tom Morris <tfmorris@gmail.com>
'''
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
        words = 0
        confidence = 0
        text = ''
        if 'STYLEREFS' in block.attrib:
            for s in block.attrib['STYLEREFS'].split():
                self.styles[s] +=1
        for tl in block:
            if tl.tag == 'TextLine':
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
                                print 'Unrecognized SUBS_TYPE', hy
                    elif elem.tag == 'SP':
                        text += ' '
                    elif elem.tag == 'HYP':
                        pass
                    else:
                        print 'Unknown tag', elem.tag
                if tl[-1].tag != 'HYP':
                    text += ' '
        return (words, confidence, text)
        
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
            self.text += '\n--- Page marker ---\n'
            for ps in page:
                if ps.tag == 'PrintSpace':
                    for tb in ps:
                        if tb.tag == 'TextBlock':
                            (w, c, t) = self.parseTextBlock(tb)
                            words += w 
                            confidence += c 
                            # TODO: Need to be more sophisticated about breaks between blocks
                            self.text += '\n' + t
                        elif tb.tag == 'ComposedBlock':
                            pass
                        else:
                            print 'Unknown tag in <PrintSpace> ', tb.tag
                elif ps.tag in ['TopMargin', 'LeftMargin', 'RightMargin','BottomMargin']:
                    pass
                else:
                    print 'Unknown tag on <Page> ', ps.tag
            page.clear() # Clear the page now that we're done with it
        if words:
            self.word_confidence = confidence / words
        self.word_count = words
        if self.pages > 1:
            # TODO: We kind of assumge one page per file now because that's the BL use case
            print 'WARNING: Multi-page file: %d pages' % self.pages

def test():
    # Simple single page test
    a = Alto('./data2/000000037/ALTO/000000037_000010.xml')
    print a.text
    print a.word_count, a.word_confidence, a.char_confidence
    
    # Run through a whole bunch of pages
    files = {'data2/000000037/000000037_0_1-42pgs__944211_dat.zip',
             'data2/000000196/000000196_0_1-164pgs__1031646_dat.zip',
             'data2/000000206/000000206_0_1-256pgs__594984_dat.zip',
             'data2/000000216/000000216_1_1-318pgs__632698_dat.zip',
             }
    from zipfile import ZipFile
    print '    File', 'Words', 'Word Confidence (0-1.0)', 'CharCount'
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
                        print 'Mismatched hyphenation count ', name, a.hyphen1_count, a.hyphen2_count
                #print name,a.word_count, a.page_accuracy, a.word_confidence, a.char_confidence
                if a.word_confidence and abs(a.word_confidence*100.0 - a.page_accuracy[0]) > 2.0: # epsilon = 2%
                    print 'Inaccurate page accuracy %2.2f %2.2f' % (a.page_accuracy[0], a.word_confidence)
            else:
                #print '   Skipped', name
                pass
        zf.close()
        #print text
        print f.split('/')[1], words, confidence/words, len(text), styles.most_common()
#         tot = sum(cc)
#         for i in range(10):
#             print i, '*'*(cc[i]*100/tot)


if __name__ == '__main__':
    test()