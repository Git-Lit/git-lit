#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Test program to create a few repos.

Based on code from GITenburg project.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import github
import local
from reader import BLCorpus

import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# TODO: Break this up to read & create iteratively
corpus = BLCorpus('data', metadataOnly=False)
#c.df

# Only test with limited directories
testtexts = corpus.texts[2:4]

for text in testtexts: 
    logging.info('Making local repo ' + str(text))
    local.make(text)
    remote = github.GithubRepo(text)
    logging.info('Making & pushing to remote repo')
    remote.create_and_push()
    logging.info('Remote repo complete')

logging.info('All repos complete')
