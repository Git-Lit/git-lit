# coding: utf-8

from reader import BLCorpus

c = BLCorpus('data2')
c.df


c.texts[0].textdir


"""
Borrowed from GITenburg project. 
Makes an organized git repo of a book folder.
"""


import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

from local import LocalRepo, NewFilesHandler
from github import GithubRepo

IGNORE_FILES = ""


def make(book):
    # Initial commit of book files
    local_repo = LocalRepo(book)
    local_repo.add_all_files()
    local_repo.commit("initial import from British Library originals.")

    # New files commit
    NewFilesHandler(book)

    local_repo.add_all_files()
    local_repo.commit("add readme, contributing and license files to book repo")
    

testtext = c.texts[0]
testtext

c.texts

for text in c.texts: 
    make(text)



# Borrowed from the GITenberg project

"""
Syncs a local git book repo to a remote git repo (by default, github)
"""


test = GithubRepo(testtext)

test.create_and_push()

for text in c.texts: 
    print(text)

for text in c.texts: 
    repo = GithubRepo(text)
    repo.create_and_push()
