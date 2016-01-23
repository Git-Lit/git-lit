
"""
Borrowed from GITenburg project. 
Makes an organized git repo of a book folder.
"""

import codecs

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


class LocalRepo():

    def __init__(self, book):
        self.book = book
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
                    '_plain.txt'
                    }
        with CdContext(self.book.textdir):
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
                print("Error: " + e.message)


class NewFilesHandler():
    """ NewFilesHandler - templates and copies additional files to book repos
    """

    def __init__(self, book):
        self.book = book
        self.add_new_files()

    def add_new_files(self):
        self.template_readme()
        self.copy_files()
        self.write_text()

    def write_text(self):
        f = codecs.open(self.book.textdir+'/'+self.book.book_id + '_plain.txt','w','utf-8')
        f.write(self.book.text + '\n')
        f.close()
        
    def template_readme(self):
        templateFile = codecs.open('templates/README.md.j2','r','utf-8').read()
        template = jinja2.Template(templateFile)
        readme_text = template.render(
            title=self.book.title,
            author=self.book.author,
            book_id=self.book.book_id
        )

        readme_path = "{0}/{1}".format(
            self.book.textdir,
            'README.md'
        )
        with codecs.open(readme_path, 'w', 'utf-8') as readme_file:
            readme_file.write(readme_text)

    def copy_files(self):
        """ Copy the LICENSE and CONTRIBUTING files to each folder repo """
        # TODO: Add .gitattributes for line endings (and .gitignore?)
        FILES = ['LICENSE.md', 'CONTRIBUTING.md']
        this_dir = sh.pwd().strip()
        for _file in FILES:
            sh.cp(
                '{0}/templates/{1}'.format(this_dir, _file),
                '{0}/'.format(self.book.textdir)
            )


def make(book):
    # Initial commit of book files
    local_repo = LocalRepo(book)
    local_repo.add_all_files()
    local_repo.commit("Initial import from British Library originals.")

    # New files commit
    NewFilesHandler(book)

    local_repo.add_all_files()
    local_repo.commit("Add readme, contributing and license files")


def test():
    pass

if __name__ == '__main__':
    test()
