import sys
from distutils.core import setup

if sys.version_info[0] < 3:
    version = str(sys.version_info[0]) + '.' + str(sys.version_info[1])
    sys.exit("""
    Sorry! Your Python version is %s, but this program requires at least
    Python 3. Please upgrade your Python installation, or try using pip3
    instead of pip.""" % version)

setup(
    name='git-lit',
    packages = ['git-lit'], # this must be the same as the name above
    py_modules=['git-lit'],
    version='0.2.0',
    description = 'Scripts for making git repositories from ebooks, like those from the British Library.',
    author = 'Jonathan Reeve',
    author_email = 'jon.reeve@gmail.com',
    url = 'https://github.com/git-lit/git-lit',
    download_url = 'https://github.com/git-lit/git-lit/tarball/0.2.0',
    install_requires=[
        'click','pandas','pyyaml','sh','wget'
    ],
    entry_points='''
        [console_scripts]
        git-lit=git-lit.main:cli
    ''',
)
