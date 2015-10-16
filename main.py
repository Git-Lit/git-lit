
# coding: utf-8

# In[20]:

import lxml.etree
import os
from IPython.display import display
import pandas as pd
import sh


# In[21]:

class BLText:
    FLICKR_TEMPLATE = 'https://www.flickr.com/photos/britishlibrary/tags/sysnum%s'
    # template below is magic - stolen from Flickr entry for BL photos
    BRITLIB_TEMPLATE = 'http://explore.bl.uk/primo_library/libweb/action/search.do?cs=frb&doc=BLL01%s&dscnt=1&scp.scps=scope:(BLCONTENT)&frbg=&tab=local_tab&srt=rank&ct=search&mode=Basic&dum=true&tb=t&indx=1&vl(freeText0)=%s&fn=search&vid=BLVU1'
    NAMESPACES = {'MODS': 'http://www.loc.gov/mods/v3'}
    
    def __init__(self, textdir): 
        self.textdir = textdir
        self.ID = os.path.basename(textdir) # alias
        self.book_id = self.ID # another alias. TODO: simplify this
        self.tree = self.parseMetadata(textdir)
        self.author = self.getAuthor()
        self.flickrURL =  BLText.FLICKR_TEMPLATE % self.ID
        self.britLibURL = BLText.BRITLIB_TEMPLATE % (self.ID, self.ID)

    def parseMetadata(self, textdir):
        fullpath = textdir + '/' + self.ID + '_metadata.xml'
        return lxml.etree.parse(fullpath)
    
    def getText(self, xpath):
        out = self.tree.xpath(xpath + '/text()', namespaces=BLText.NAMESPACES)
        if isinstance(out, list): 
            if len(out) == 1: 
                # No sense having a list of length one. Get just the string. 
                out = out[0]
        return out
    
    @property
    def title(self):
        # TODO enable caching of this result
        return self.getText('//MODS:title')
        
#    def getTitle(self): 
#        return self.getText('//MODS:title')
        
    def getAuthor(self): 
        rawAuthor = self.getText('//MODS:name[@type="personal"]/MODS:namePart')
        # TODO: do some transformations to the text here. Get it in the appropriate case. 
        return rawAuthor


# In[22]:

# A collection of BLText objects. 
class BLCorpus(): 
    def __init__(self, corpusDir):
        self.baseDir = corpusDir
        self.texts = []
        self.readDataDir()
        self.makeDataFrame()

    def readDataDir(self): 
        textdirs = os.listdir(self.baseDir)
        self.texts = [ BLText(os.path.join(self.baseDir,textdir)) for textdir in textdirs ]
        self.metadata = [ [ text.ID, text.title, text.author ] for text in self.texts ] 
    
    def makeDataFrame(self): 
        self.df = pd.DataFrame(self.metadata, columns=['ID', 'Title', 'Author'])
        
    def show(self): 
        display(self.df)


# In[23]:

c = BLCorpus('data2')
c.df


# In[24]:

c.texts[0].textdir


# In[25]:

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


# In[26]:


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


# In[27]:

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
            except sh.ErrorReturnCode_1:
                print("Commit aborted for {0} with msg {1}".format(self.book.book_id, message))


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
    


# In[28]:

testtext = c.texts[0]
testtext


# In[29]:

c.texts


# In[19]:




# In[30]:

for text in c.texts: 
    make(text)


# In[32]:

# Borrowed from the GITenberg project

"""
Syncs a local git book repo to a remote git repo (by default, github)
"""

import logging
from re import sub
import time

import github3
import sh

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


# In[77]:

test = GithubRepo(testtext)


# In[50]:

test.create_and_push()


# In[84]:

for text in c.texts: 
    print(text)


# In[87]:

for text in c.texts: 
    repo = GithubRepo(text)
    repo.create_and_push()


# In[ ]:



