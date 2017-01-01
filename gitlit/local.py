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
import glob
from pkg_resources import resource_filename

logger = logging.getLogger()
logger.setLevel(logging.INFO)

BASE_URL = 'https://Git-Lit.github.io/'

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
    def __init__(self, book):
        """ Requires a BLText book object as input. """ 
        self.book = book
        logging.info("Now attempting to initialize a local git repository for text: " 
                      + self.book.book_id + " a.k.a. " + self.book.title )
        self.basename = self.book.book_id
        self.directory = tempfile.mkdtemp(prefix='tmprepo%s' % self.basename, dir='.')
        if book.volume:
            self.basename += '_%02d' % self.book.volume
        # TODO: Temp dirs being created locally to ease debugging.  Remove for production
        self.add_new_files()
        self.add_all_files()
        self.commit("Initial import from British Library originals.")

    def add_new_files(self):
        shutil.copy(self.book.zipfile, self.directory)
        self.write_text()
        self.write_metadata()
        self.template_readme()
        self.copy_files()

    def write_text(self):
        with open(self.directory+'/'+ self.basename + '.md','w') as f:
            f.write(self.book.text + '\n')

    def write_metadata(self):
        with open(self.directory+'/'+self.basename + '_metadata.xml','w') as f:
            f.write(lxml.etree.tostring(self.book.metadata, encoding='unicode') + '\n')

    def template_readme(self):
        templateFilename = resource_filename(__name__, 'templates/README.md.j2')
        with open(templateFilename) as f:
            templateSrc = f.read()
        template = jinja2.Template(templateSrc)
        readme_text = template.render(
            title = self.book.title,
            author = self.book.author,
            book_id = self.book.book_id, 
            url = BASE_URL + self.book.book_id
        )

        readme_path = "{0}/{1}".format(
            self.directory,
            'README.md'
        )
        with open(readme_path, 'w') as readme_file:
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

    def add_all_files(self):
        with CdContext(self.directory):
            sh.git.init('.')
            files = glob.glob('./*')
            logging.debug("Files to add: %s")
            for file in files: 
                sh.git('add', file)

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

    def template_header(self): 
        """ Generates a Jekyll page header (YAML) from the template. """
        logging.info('Creating book headers from template.')
        headerTemplate = resource_filename(__name__, 'templates/book-header.md.j2')
        with open(headerTemplate, 'r') as templateFile: 
            templateContents = templateFile.read() 
            template = jinja2.Template(templateContents)
            header = template.render(title=self.book.title)
        return header

    def template_config(self): 
        """ Generates a _config.yml from the template. """
        logging.info('Creating _config.yml from template.')
        configTemplate = resource_filename(__name__, 'templates/_config.yml.j2')
        with open(configTemplate, 'r') as templateFile: 
            templateContents = templateFile.read()
            template = jinja2.Template(templateContents)
        configOut = template.render(
                title = self.book.title, 
                author = self.book.author,
                book_id = self.book.book_id
                )
        return configOut

    def jekyllify(self): 
        logging.info('Now creating a Jekyll site out of this repo.')

        with CdContext(self.directory):
            # Copy Jekyll skeleton files to our new directory. 
            try:
                skel_dir = resource_filename(__name__, 'jekyll-skel/') 
            except: 
                logging.warn("Couldn't find Jekyll skel directory.")
                raise IOError("Couldn't find Jekyll skel directory!")
            sh.cp('-a', skel_dir+'.', '.')

            # Create header from template. 
            header = self.template_header()

            # Prepend header to book markdown file. 
            doc = self.basename+'.md'
            with open(doc, 'r') as origFile: 
                origContent = origFile.read()
            with open(doc, 'w') as modifiedFile:
                modifiedFile.write(header + '\n' + origContent)
            sh.mv(doc, 'index.md')
            # Remove it from git, since we've renamed it to index.md
            sh.git('rm', doc) 

            # Generate config file. 
            configOut = self.template_config()
            with open('_config.yml', 'w') as outFile: 
                outFile.write(configOut)

            # Use gh-pages branch. 
            sh.git('checkout', '-b', 'gh-pages')

        self.add_all_files()
        self.commit('Create Jekyll site.')
