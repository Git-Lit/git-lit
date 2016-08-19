#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gitlit.local as local
import gitlit.github as github
from gitlit.reader import BLText
import logging
import click

logger = logging.getLogger()
logger.setLevel(logging.INFO)

@click.command()
@click.argument('filenames', nargs=-1) 
@click.option('--debug', is_flag=True, help='Turn on debugging mode for more verbose error messages.')
def cli(filenames, debug): 
    """Processes ebooks and turns them into GitHub repositories.
    Only works with British Library compressed ALTO files at the moment. 
    """
    logging.info('Processing files: %s', filenames) 
    for filename in filenames: 
        logging.info('Processing book: %s', filename) 
        book = BLText(filename)  
        logging.info('Making local repo: %s %s' % (book.book_id, book.title))
        repo = local.make(book) 

if __name__ == '__main__':
    cli()
