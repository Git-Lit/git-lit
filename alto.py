#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on Jan 20, 2016

@author: Tom Morris <tfmorris@gmail.com>
@license: Apache License 2.0
'''
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from array import array
from collections import Counter
from lxml import etree as ET
import re
import sys

PY3 = sys.version_info[0] == 3

# TODO These can be tagged semantically with visual attributes decided later
LOW_QUALITY_STYLE = '[maroon]#%s#'
MED_QUALITY_STYLE = '[grey]#%s#'

# FIXME: This interacts poorly with other processing. Turn off for now.
LOW_QUALITY_THRESHOLD = 0.0 # 0.45
MED_QUALITY_THRESHOLD = 0.0 # 0.65 # Should be higher but generates too much noise in source

# This only matches very basic signatures (lower right page marks)
SIGNATURE_REGEX = re.compile('^[0-9\-—].$')

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
        if PY3:
            self.char_confidence = array(u'L',[0]*10) # 0=Good to 9=Bad
        else:
            self.char_confidence = array(b'L',[0]*10) # 0=Good to 9=Bad
        self.hyphen1_count = 0
        self.hyphen2_count = 0
        self.text = ''
        self.page_accuracy=[]
        self.pages = 0
        self.styles = Counter()

        self.parse_file()

    def parseTextBlock(self, block, pageStart):
        """
        Parse the lines, words, spaces, hyphens in a single text block.

        TODO: Do we need a parameter for paragraph indent, avg jitter, etc?
        """
        # TODO: Setting the threshold is key.  We should see a bimodal distribution
        # with lots of values near the left margin, a number near the nominal indent, and few in the middle
        # Perhaps pre-scan all TextBlocks/TextLines on page or in document?
        PARA_INDENT_THRESHOLD = 25 # This value is for experimentation ONLY!
        PARA_INDENT_THRESHOLD2 = 100

        words = 0
        confidence = 0
        lines = ['']
        lmargin = None
        centered = False
        if 'STYLEREFS' in block.attrib:
            for s in block.attrib['STYLEREFS'].split():
                self.styles[s] +=1
                if s == 'PAR_CENTER':
                    centered = True
        if 'HPOS' in block.attrib:
            lmargin = int(block.attrib['HPOS'])
        else:
            raise Exception("Block with no HPOS, can't continue")
        firstLine = False
        paraStart = centered # Anything centered is automatically a new paragraph to deal with chapter heads, etc.
        for tl in block:
            if tl.tag == 'TextLine':
                if 'HPOS' in tl.attrib:
                    indent = int(tl.attrib['HPOS']) - lmargin
                    # TODO: Pages ending with a single line paragraph beginning can have them
                    # split into a separate block.  Perhaps we should work off print area margin?
                    if indent > PARA_INDENT_THRESHOLD and indent < PARA_INDENT_THRESHOLD2:
                        if firstLine:
                            paraStart = True
                        lines.extend(['',''])
                        #print '    New paragraph!', indent 
                    elif indent > PARA_INDENT_THRESHOLD/4 and indent <- PARA_INDENT_THRESHOLD:
                        print(' **Indent in the middle ', indent)
                        #print '  continuation: ', indent
                    elif indent > PARA_INDENT_THRESHOLD2:
                        #print(' ** Unexpected indent -- too far right: ', indent)
                        pass
                else:
                    raise Exception('Something bad happened - no HPOS in TextLine - aborting')
                for elem in tl:
                    # TODO: we may want to assemble the physical line of text separately first
                    # so that we can do some physical line processing
                    if elem.tag == 'String': # <String> element is just a single word
                        words += 1
                        wc = float(elem.attrib['WC'])
                        confidence += wc

                        # Tag low quality words visually for ASCIIDOC
                        # TODO: Coalesce runs of same attributes
                        s = elem.attrib['CONTENT']
#                         if pageStart and s.find('CHAPTER') >= 0:
#                             print 'Chapter head', centered, lmargin, indent
                        if wc < LOW_QUALITY_THRESHOLD:
                            lines[-1] += (LOW_QUALITY_STYLE % s)
                        elif wc < MED_QUALITY_THRESHOLD:
                            lines[-1] += (MED_QUALITY_STYLE % s)
                        else:
                            lines[-1] += s

                        # Update character confidence histogram counts
                        for c in elem.attrib['CC']:
                            self.char_confidence[int(c)] += 1

                        # Tally counts for hyphenation pieces
                        if 'SUBS_TYPE' in elem.attrib:
                            hy = elem.attrib['SUBS_TYPE']
                            if hy == 'HypPart1':
                                self.hyphen1_count += 1
                            elif hy == 'HypPart2':
                                self.hyphen2_count += 1
                            else:
                                print('Unrecognized SUBS_TYPE', hy)
                    elif elem.tag == 'SP':
                        lines[-1] += ' '
                    elif elem.tag == 'HYP':
                        pass
                    else:
                        print('Unknown tag', elem.tag)
                if tl[-1].tag != 'HYP':
                    lines[-1] += ' '
                firstLine = False

        # Postprocess text
        # TODO: Escape ASCIIDOC syntax: ''', <<<, leading space on line, list markers
        for (i,l) in enumerate(lines):
            if len(l) > 1:
                if l[0] == '=': # Heading marker
                    l = '{empty}'+l
                elif l[1] == '.': # list marker
                    # Lines starting M. Girardeu get interpreted as lists
                    l = '{empty}' + l # Escape to prevent bad list processing
                elif l[0:2] == '" ':
                    # Open quote followed by extraneous space
                    # This happens more than just at beginning of line, but it's the most common case
                    # (and the others are more ambiguous and need more sophistication to repair
                    l = l[0] + l[2:]
                # directional quates are never ambiguous - clean them all up
                l = l.replace(u'“ ',u'“').replace(u' ”',u'”')
                l = l.strip() # Leading (especially) and trailing whitespace is problematic
                lines[i] = l

            # Move signature marks out of line to a footnote (need better markup)
            # TODO: handle catchwords too, if present/common in the corpus
        if len(lines) > 0 and SIGNATURE_REGEX.match(lines[-1]):
                lines[-1] = 'footnote:[Possible signature: "%s"]' % lines[-1]

        # TODO: Fix this crude chapter detector - chapter head can be in multiple blocks, among other things
        # TODO:  doesn't handle mid-page chapter heads like doc 000000206
        if pageStart and lines[0].find('CHAPTER') >= 0:
            head = lines[0]
            # Concatenate all upper case lines
            for i in range(1,len(lines)):
                if not lines[i].isupper:
                    break
                head += ' ' + lines.pop(i)
            lines[0] = head
            lines.insert(1, '-'*len(head))
            lines.insert(2, '')
            lines.insert(0,'') # Make sure we have a blank line before

        return (words, confidence, '\n'.join(lines), paraStart)

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
                pageno = ', Page: %s' % page.attrib['PRINTED_IMG_NR']
            self.text += '\n// Leaf %s ' % leaf + pageno + '\n'
            pageStart = True
            for ps in page:
                # Note: Text can also live in the margins TopMargin, BottomMargin, etc if the layout analysis messes up
                if ps.tag == 'PrintSpace':
                    blockMargin = ps.attrib['HPOS']
                    # TOOD: check for indented text blocks (block quote, etc)
                    for tb in ps:
                        if tb.tag == 'TextBlock':
                            (w, c, t, beginningPara) = self.parseTextBlock(tb, pageStart)
                            words += w 
                            confidence += c
                            if pageStart and beginningPara:
                                self.text += '\n' + t
                            else:
                                self.text += t # TODO: Deal with cross page hyphenation
                        elif tb.tag == 'ComposedBlock':
                            # TODO: Can this be anything other than a picture?
                            self.text += '\n// ComposedBlock (picture?) skipped here\n'
                        else:
                            print('Unknown tag in <PrintSpace> ', tb.tag)
                        pageStart = False
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
