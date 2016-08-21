#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gitlit.local as local
import gitlit.github as github
from gitlit.reader import BLText
import logging
import click

logger = logging.getLogger()
logger.setLevel(logging.INFO)

@click.group()
@click.option('--debug', is_flag=True, help='Turn on debugging mode for more verbose error messages.')
def cli(debug): 
    """Processes books and turns them into GitHub repositories.
    Converts ALTO XML to markdown, adds READMEs, and pushes to GitHub. 
    Only works with British Library compressed ALTO files at the moment. 
    """

@cli.command()
@click.argument('filenames', nargs=-1) 
def convert(filenames, debug): 
    """Just converts the books to markdown, without creating a git repository for it."""

    logging.info('About to convert files: %s', filenames) 
    for filename in filenames: 
        logging.info('Converting book: %s', filename) 
        book = BLText(filename)  
        with open(book.basename + '.md','w') as f:
            f.write(book.text + '\n')

@cli.command() 
@click.argument('filenames', nargs=-1) 
def process(filenames, debug): 
    """Processes a book, converting it to markdown and creating a git repository for it,
    but not pushing it to github."""

    logging.info('Processing files: %s', filenames) 
    for filename in filenames: 
        logging.info('Processing book: %s', filename) 
        book = BLText(filename)  
        logging.info('Making local repo: %s %s' % (book.book_id, book.title))
        repo = local.make(book) 

if __name__ == '__main__':
    cli()
