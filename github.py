
# Borrowed from the GITenberg project

"""
Syncs a local git book repo to a remote git repo (by default, github)
"""

import logging
import time

import github3
import sh

from local import CdContext

try:
    from secrets import GH_USER, GH_PASSWORD
except:
    print("no secrets file found, continuing without")


class GithubRepo():

    def __init__(self, book):
        self.book = book
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
        self.org = self.github.organization(login='Git-Lit')
        # FIXME: logging
        print("ratelimit: " + str(self.org.ratelimit_remaining))

    def format_desc(self):
        return u'{0} by {1} is a British Library book, now on GitHub.'.format(
            self.book.title, self.book.author
        )

    def format_title(self):
        return self.book.book_id # Just using the book ID as a title for now. 

    def create_repo(self):
        self.repo = self.org.create_repo(
            self.format_title(),
            description=self.format_desc(),
            homepage=u'https://Git-Lit.github.io/',
            private=False,
            has_issues=True,
            has_wiki=False,
            has_downloads=True
        )

    def add_remote_origin_to_local_repo(self):
        with CdContext(self.book.textdir):
            try:
                sh.git('remote', 'add', 'origin', self.repo.ssh_url)
            except sh.ErrorReturnCode_128:
                print("We may have already added a remote origin to this repo")

    def push_to_github(self):
        with CdContext(self.book.textdir):
            try:
                sh.git('push', 'origin', 'master')
            except sh.ErrorReturnCode_128:
                logging.error(u"github repo not ready yet")
                time.sleep(10)
                sh.git('push', 'origin', 'master')



#test = GithubRepo(testtext)

#test.create_and_push()

#for text in c.texts: 
#    print(t1ext)

#for text in c.texts: 
#    repo = GithubRepo(text)
#    repo.create_and_push()

