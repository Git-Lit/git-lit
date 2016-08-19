#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Makes an organized git repo of a book folder.

Based on code from GITenburg project.
"""

import codecs

import jinja2
import sh

import logging
import lxml
import shutil
import tempfile
from pkg_resources import resource_filename

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


class LocalRepo():

    def __init__(self, book, directory):
        self.book = book
        self.directory = directory
        logging.info("Now attempting to initialize a local git repository for text: " 
                      + self.book.book_id + " a.k.a. " + self.book.title )

    def add_file(self, filename):
        sh.git('add', filename)

    def add_all_files(self):
        SUFFIXES = {'_dat.zip',
                    '_metadata.xml',
                    'README.md',
                    'CONTRIBUTING.md',
                    'LICENSE.md',
                    '.adoc'
                    }
        with CdContext(self.directory):
            sh.git.init('.')

            logging.debug("Files to add: " + str(sh.ls()))

            # NOTE: repo.untracked_files is unreliable with CdContext
            # using sh.ls() instead, this doesn't recognize .gitignore
            for _file in sh.ls('-1'):
                # TODO: This attempts to add existing files a second time
                _file = _file.rstrip('\n')
                for suffix in SUFFIXES:
                    if _file.endswith(suffix):
                        logging.info("Adding file: " + _file)
                        self.add_file(_file)
                        break
                else:
                    logging.debug('Skipping ' + _file)

    def commit(self, message):
        with CdContext(self.directory):
            try:
                # note the double quotes around the message
                sh.git(
                    'commit',
                    '-m',
                    '{message}'.format(message=message)
                )
            except sh.ErrorReturnCode_1 as e: 
                print("Commit aborted for {0} with msg {1}".format(self.book.book_id, message))
                print("Error: " + e.message)

# TODO: It's very weird partitioning to have this as a separate class. Refactor!
class NewFilesHandler():
    """ NewFilesHandler - templates and copies additional files to book repos
    """

    def __init__(self, book):
        self.book = book
        self.basename = self.book.book_id
        if book.volume:
            self.basename += '_%02d' % self.book.volume
        # TODO: Temp dirs being created locally to ease debugging.  Remove for production
        self.directory = tempfile.mkdtemp(prefix='tmprepo%s' % self.basename, dir='.')
        self.add_new_files()

    def add_new_files(self):
        shutil.copy(self.book.zipfile, self.directory)
        self.write_metadata()
        self.write_text()
        self.template_readme()
        self.copy_files()

    def write_text(self):
        with codecs.open(self.directory+'/'+ self.basename + '.adoc','w','utf-8') as f:
            f.write(self.book.text + '\n')

    def write_metadata(self):
        with codecs.open(self.directory+'/'+self.basename + '_metadata.xml','w','utf-8') as f:
            f.write(lxml.etree.tostring(self.book.metadata, encoding='unicode') + '\n')

    def template_readme(self):
        templateFilename = resource_filename(__name__, 'templates/README.md.j2')
        with open(templateFilename) as f:
            templateSrc = f.read()
        template = jinja2.Template(templateSrc)
        readme_text = template.render(
            title=self.book.title,
            author=self.book.author,
            book_id=self.book.book_id
        )

        readme_path = "{0}/{1}".format(
            self.directory,
            'README.md'
        )
        with codecs.open(readme_path, 'w', 'utf-8') as readme_file:
            readme_file.write(readme_text)

    def copy_files(self):
        """ Copy the LICENSE and CONTRIBUTING files to each folder repo """
        # TODO: Add .gitattributes for line endings (and .gitignore?)
        # license = resource_filename(__name__, 'templates/LICENSE')
        contributing = resource_filename(__name__, 'templates/CONTRIBUTING.md')
        FILES = [contributing] 
        this_dir = sh.pwd().strip()
        for _file in FILES:
            sh.cp(
                _file,
                '{0}/'.format(self.directory)
            )


def make(book):

    # Create files from zip
    handler = NewFilesHandler(book)

    # Initial commit of book files
    local_repo = LocalRepo(book, handler.directory)
    local_repo.add_all_files()
    local_repo.commit("Initial import from British Library originals.")
    # TODO: Cleanup temp dir
    return handler.directory

def test():
    pass

if __name__ == '__main__':
    test()
