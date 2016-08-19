#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test program to create a few repos.

Based on code from GITenburg project.
"""

import github
import local
from reader import BLCorpus

import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Smaller set for testing
corpus = BLCorpus((
                   'data/000000037_0_1-42pgs__944211_dat.zip',
                   'data/000000196_0_1-164pgs__1031646_dat.zip',
                   'data/000000206_0_1-256pgs__594984_dat.zip',
                   'data/000000216_1_1-318pgs__632698_dat.zip',
                   'data/000000216_2_1-286pgs__638718_dat.zip',
                   'data/000000218_1_1-324pgs__630262_dat.zip',
                   'data/000000218_2_1-330pgs__630265_dat.zip',
                   'data/000000218_3_1-306pgs__634403_dat.zip',
                   'data/000000428_0_1-206pgs__1025980_dat.zip',
                   'data/000000472_0_1-178pgs__999442_dat.zip',
                   ), 
                  metadataOnly=False)

# TODO: Break this up to read & create iteratively
#corpus = BLCorpus('data', metadataOnly=False)

#c.df

# Only test with limited directories
testtexts = [corpus.texts[-1]]

for text in testtexts: 
    logging.info('Making local repo: %s %s' % (text.book_id, text.title))
    directory = local.make(text)
    remote = github.GithubRepo(text, directory)
    logging.info('Making & pushing to remote repo')
    #remote.create_and_push()
    logging.info('Remote repo complete')

logging.info('All repos complete')
