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
def convert(filenames): 
    """Just converts the books to markdown, without creating a git repository for it."""

    logging.info('About to convert files: %s', filenames) 
    for filename in filenames: 
        logging.info('Converting book: %s', filename) 
        book = BLText(filename)  
        with open(book.book_id + '.md','w') as f:
            f.write(book.text + '\n')

@cli.command() 
@click.argument('filenames', nargs=-1) 
@click.option('--nojekyll', is_flag=True, help="Don't make a Jekyll site out of the repo." ) 
@click.option('--push', is_flag=True, help="Push the resulting repo to GitHub." ) 
def process(filenames, nojekyll=False, push=False): 
    """Creates a local git repository for the book. Doesn't push."""
    
    logging.info('Processing files: %s', filenames) 
    if nojekyll: 
        logging.info('Not creating jekyll sites for them.')
        jekyll = False
    else: 
        logging.info('Creating jekyll sites for them, too.')
        jekyll = True

    for filename in filenames: 
        logging.info('Processing book: %s', filename) 
        book = BLText(filename)  
        logging.info('Making local repo: %s %s' % (book.book_id, book.title))
        repo = local.LocalRepo(book)
        if jekyll: 
            repo.jekyllify()

        if push: 
            gh = github.GithubRepo(book, repo.directory) 
            gh.create_and_push()
            
@cli.command() 
@click.argument('repos', nargs=-1) 
def delete(repos): 
    """ Deletes repos from GitHub. """
    click.confirm('Are you really sure you want to delete this/these repo(s)?', abort=True)
    gh = github.GitHub()
    for repo in repos: 
        gh.delete(repo)

if __name__ == '__main__':
    cli()
