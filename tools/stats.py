#!/usr/bin/env python
# encoding: utf-8
'''
stats -- Dump compute and dump corpus stats

stats is a program to compute and dump statistics for books in the British Library 19th Century corpus

It defines classes_and_methods

@author:     Tom Morris

@copyright:  2016 Thomas F. Morris. All rights reserved.

@license:    Apache

@contact:    tfmorris@gmail.com
@deffield    updated: Updated
'''

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import sys
import os

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
from reader import BLCorpus
from lib2to3.pgen2.pgen import PgenGrammar

import pycld2

__all__ = []
__version__ = 0.1
__date__ = '2016-01-26'
__updated__ = '2016-01-26'

DEBUG = 0
TESTRUN = 1
PROFILE = 0

class CLIError(Exception):
    '''Generic exception to raise and log different fatal errors.'''
    def __init__(self, msg):
        super(CLIError).__init__(type(self))
        self.msg = "E: %s" % msg
    def __str__(self):
        return self.msg
    def __unicode__(self):
        return self.msg

def main(argv=None): # IGNORE:C0111
    '''Command line options.'''

    if argv is None:
        argv = sys.argv
    else:
        sys.argv.extend(argv)

    program_name = os.path.basename(sys.argv[0])
    program_version = "v%s" % __version__
    program_build_date = str(__updated__)
    program_version_message = '%%(prog)s %s (%s)' % (program_version, program_build_date)
    program_shortdesc = __import__('__main__').__doc__.split("\n")[1]
    program_license = '''%s

  Created by Tom Morris on %s.
  Copyright 2016 Thomas F. Morris. All rights reserved.

  Licensed under the Apache License 2.0
  http://www.apache.org/licenses/LICENSE-2.0

  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied.

USAGE
''' % (program_shortdesc, str(__date__))

    try:
        # Setup argument parser
        parser = ArgumentParser(description=program_license, formatter_class=RawDescriptionHelpFormatter)
        parser.add_argument("-r", "--recursive", dest="recurse", action="store_true", help="recurse into subfolders [default: %(default)s]")
        parser.add_argument("-v", "--verbose", dest="verbose", action="count", help="set verbosity level [default: %(default)s]")
        parser.add_argument("-i", "--include", dest="include", help="only include paths matching this regex pattern. Note: exclude is given preference over include. [default: %(default)s]", metavar="RE" )
        parser.add_argument("-e", "--exclude", dest="exclude", help="exclude paths matching this regex pattern. [default: %(default)s]", metavar="RE" )
        parser.add_argument('-V', '--version', action='version', version=program_version_message)
        parser.add_argument(dest="paths", help="paths to folder(s) with source file(s) [default: %(default)s]", metavar="path", nargs='+')

        # Process arguments
        args = parser.parse_args()

        paths = args.paths
        verbose = args.verbose
        recurse = args.recurse
        inpat = args.include
        expat = args.exclude

        if verbose > 0:
            print("Verbose mode on")
            if recurse:
                print("Recursive mode on")
            else:
                print("Recursive mode off")

        if inpat and expat and inpat == expat:
            raise CLIError("include and exclude pattern are equal! Nothing will be processed.")

        confidence = 0
        pages = 0
        words = 0
        chars = 0

        if recurse:
            corpus = BLCorpus(paths[0], metadataOnly=False)
            (confidence, pages, words, chars) = generate_stats(corpus)
        else:
            for path in paths:
                corpus = BLCorpus([path], metadataOnly=False)
                (conf, pg, wd, ch) = generate_stats(corpus)
                confidence += conf
                pages += pg
                words += wd
                chars += ch

        print('\t'.join(['Total|Avg', str(confidence/words), '--', str(pages), str(words), str(chars)]))

        return 0
    except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        return 0
#     except Exception, e:
#         if DEBUG or TESTRUN:
#             raise(e)
#         indent = len(program_name) * " "
#         sys.stderr.write(program_name + ": " + repr(e) + "\n")
#         sys.stderr.write(indent + "  for help use --help")
#         return 2

def generate_stats(corpus):
    confidence = 0
    pages = 0
    words = 0
    chars = 0

    for text in corpus.texts:
        if type(text.author) is list:
            author = '|'.join(text.author)
        else:
            author = text.author
        confidence += text.avg_word_confidence * text.words
        pages += text.pages
        words += text.words
        chars += len(text.text)
        vid = text.book_id
        if text.volume:
            vid += ('_%02d' % text.volume)
        isReliable, textBytesFound, langDetails = pycld2.detect(text.title.encode('utf-8'), isPlainText=True)
        if isReliable:
            language = langDetails[0][0]
            langCode = langDetails[0][1]
        else:
            language = 'Unknown'
            langCode = '--'
        print('\t'.join([vid, str(text.avg_word_confidence), langCode, str(text.pages), str(text.words), str(len(text.text)), author, text.title]))

    return(confidence, pages, words, chars)

if __name__ == "__main__":
    if DEBUG:
        sys.argv.append("-h")
        sys.argv.append("-v")
        sys.argv.append("-r")
    if TESTRUN:
        import doctest
        doctest.testmod()
    if PROFILE:
        import cProfile
        import pstats
        profile_filename = 'stats_profile.txt'
        cProfile.run('main()', profile_filename)
        statsfile = open("profile_stats.txt", "wb")
        p = pstats.Stats(profile_filename, stream=statsfile)
        stats = p.strip_dirs().sort_stats('cumulative')
        stats.print_stats()
        statsfile.close()
        sys.exit(0)
    sys.exit(main())