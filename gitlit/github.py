#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Syncs a local git book repo to a remote git repo (by default, github)

Based on code from the GITenberg project
"""

import logging
import time
import github3
import sh
from gitlit.local import CdContext

try:
    from secrets import GH_USER, GH_PASSWORD
except:
    print("no secrets file found, continuing without")

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class GithubRepo():

    def __init__(self, book, directory):
        self.book = book
        self.directory = directory
        self.create_api_handler()

    def create_and_push(self):
        self.create_repo()
        self.add_remote_origin_to_local_repo()
        self.push_to_github()

    def create_api_handler(self):
        """ Creates an api handler and sets it on self """
        self.github = github3.login(username=GH_USER, password=GH_PASSWORD)
        if hasattr(self.github, 'set_user_agent'):
            self.github.set_user_agent('Jonathan Reeve: http://jonreeve.com')
        self.org = self.github.organization('Git-Lit')
        logger.debug("ratelimit: " + str(self.org.ratelimit_remaining))

    def repo_exists(self, repo): 
        """ Checks if a repo exists in the Git-Lit org. """
        repos = [repo.name for repo in self.org.iter_repos()
                # assumes that books start with 0. 
                if repo.name.startswith('0')]
        return repo in repos

    def format_desc(self):
        return '{0} by {1} is a British Library book, now on GitHub.'.format(
            self.book.title, self.book.author
        )

    def format_title(self):
        # Just using the volume ID for now.  
        return self.book.vol_id

    def create_repo(self):
        self.repo = self.org.create_repo(
            self.format_title(),
            description=self.format_desc(),
            homepage='https://Git-Lit.github.io/' + self.book.vol_id,
            private=False,
            has_issues=True,
            has_wiki=False,
        )

    def add_remote_origin_to_local_repo(self):
        with CdContext(self.directory):
            try:
                sh.git('remote', 'add', 'origin', self.repo.ssh_url)
            except sh.ErrorReturnCode_128:
                print("We may have already added a remote origin to this repo")

    def push_to_github(self):
        with CdContext(self.directory):
            try:
                sh.git('push', 'origin', 'gh-pages')
            except sh.ErrorReturnCode_128:
                logging.error(u"github repo not ready yet")
                time.sleep(10)
                sh.git('push', 'origin', 'gh-pages')

class GitHub(): 
    """ 
    A class for generic GH utility actions. 
    Ideally this could be combined with the GitHubRepo class above, 
    but keeping this separate allows us to poll GitHub without having to parse a book
    first. 
    """
    def __init__(self): 
        self.create_api_handler()

    def create_api_handler(self):
        """ Creates an api handler and sets it on self """
        self.github = github3.login(username=GH_USER, password=GH_PASSWORD)
        if hasattr(self.github, 'set_user_agent'):
            self.github.set_user_agent('Jonathan Reeve: http://jonreeve.com')
        self.org = self.github.organization('Git-Lit')
        logger.debug("ratelimit: " + str(self.org.ratelimit_remaining))

    def delete(self, repo): 
        repository = self.github.repository('git-lit', repo)
        success = repository.delete()
        if success: 
            logging.info('Repo %s successfully deleted.' % repo)
        else: 
            logging.warn("Repo %s wasn't deleted!" % repo)
