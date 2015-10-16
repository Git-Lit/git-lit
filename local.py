
"""
Borrowed from GITenburg project. 
Makes an organized git repo of a book folder.
"""

import codecs
import logging
import os
from os.path import abspath, dirname

import jinja2
import sh

import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class CdContext():
    """ A context manager using `sh` to cd to a directory and back
        `with CdContext(new path to go to)`
    """
    def __init__(self, path):
        self._og_directory = str(sh.pwd()).strip('\n')
        self._dest_directory = path

    def __enter__(self):
        sh.cd(self._dest_directory)

    def __exit__(self, exception_type, exception_value, traceback):
        sh.cd(self._og_directory)

IGNORE_FILES = ""

class LocalRepo():

    def __init__(self, book):
        self.book = book
        logging.info("Now attempting to initialize a local git repository for text: " 
                      + self.book.ID + " a.k.a. " + self.book.title )

    def add_file(self, filename):
        sh.git('add', filename)

    def add_all_files(self):
        with CdContext(self.book.textdir):
            sh.git.init('.')

            logging.debug("Files to add: " + str(sh.ls()))

            # NOTE: repo.untracked_files is unreliable with CdContext
            # using sh.ls() instead, this doesn't recognize .gitignore
            for _file in sh.ls():
                for _subpath in _file.split():
                    logging.info("Adding file: " + str(_file))

                    self.add_file(_subpath)

    def commit(self, message):
        with CdContext(self.book.textdir):
            try:
                # note the double quotes around the message
                sh.git(
                    'commit',
                    '-m',
                    '{message}'.format(message=message)
                )
            except sh.ErrorReturnCode_1 as e: 
                print("Commit aborted for {0} with msg {1}".format(self.book.book_id, message))
                print("Error: " + e.value)


class NewFilesHandler():
    """ NewFilesHandler - templates and copies additional files to book repos
    """

    def __init__(self, book):
        self.book = book
        self.add_new_files()

    def add_new_files(self):
        self.template_readme()
        self.copy_files()

    def template_readme(self):
        templateFile = open('templates/README.md.j2').read()
        template = jinja2.Template(templateFile)
        readme_text = template.render(
            title=self.book.title,
            author=self.book.author,
            book_id=self.book.ID
        )

        readme_path = "{0}/{1}".format(
            self.book.textdir,
            'README.md'
        )
        with codecs.open(readme_path, 'w', 'utf-8') as readme_file:
            readme_file.write(readme_text)

    def copy_files(self):
        """ Copy the LICENSE and CONTRIBUTING files to each folder repo """
        files = ['LICENSE.md', 'CONTRIBUTING.md']
        this_dir = sh.pwd().strip()
        for _file in files:
            sh.cp(
                '{0}/templates/{1}'.format(this_dir, _file),
                '{0}/'.format(self.book.textdir)
            )

def make(book):
    # Initial commit of book files
    local_repo = LocalRepo(book)
    local_repo.add_all_files()
    local_repo.commit("initial import from British Library originals.")

    # New files commit
    NewFilesHandler(book)

    local_repo.add_all_files()
    local_repo.commit("add readme, contributing and license files to book repo")
    
#for text in c.texts: 
#    make(text)
