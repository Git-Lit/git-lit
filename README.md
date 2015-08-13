# Git-Lit

Scripts to create git repositories for ALTO XML texts, like those from the British Library's scanned documents. 

# Project Summary

This project aims to make the British Library's corpus of scanned and OCRed ALTO XML texts better available to digital humanists, by transforming the texts into useful file formats and publishing them to the Web as corpus repositories. This is intended to have a threefold effect. First, it will make public the heretofore obscure textual holdings of the British Library (with their permission, of course). Second, it will transform their verbose XML data into archival TEI XML and plain text formats that are easier to read and computationally analyze. Third, it will make this data available to text analysts, editors, and other interested parties by creating version-controlled git repositories for each text and programmatically posting them to GitHub. This will allow for crowdsourced proofreading and collaborative improvement of the texts, as well as archival storage of every subsequent revision of the text. 

# Project Planning

This project will be divided into these phases: 

*Phase I*. A script will be written to parse each text's JSON metadata and use this to create a GitHub repository title, description, and README.md file for the text. That script will then interface with the GitHub API to create a new repository, set these properties, and push a newly initialized git module for each text, which, apart from the readme file, hasn't yet been altered from its original state. At this point the texts will already be public, and will already be useful to text analysts. 

*Phase II*. Indices will be created for these texts in the form of submodule pointers. Parent repositories will be created for certain categories of texts, containing only pointers to subrepository remotes and their commit hashes. These category-based parent repositories might include "17th Century Novels," "18th Century Correspondence," or simply "Poetry," but the categories are not mutually exclusive by necessity. This will allow a literary scholar interested in a particular category to instantly assemble a corpus by `git clone`ing the parent repository and checking out its submodules with `git submodule update --init --recursive`. An early sketch of this idea is outlined in my blog post, [A Proposal for a Corpus Sharing Protocol](http://jonreeve.com/2015/03/proposal-for-a-corpus-protocol/). 

*Phase III*. A script will be written to transform the text into a more useful format, by ingesting the verbose ALTO XML and outputting Markdown editions of each text. Markdown was chosen as a plain-text file format, as it is one of the more human-readable formats, and one with the least amount of markup syntax, making it a reasonable format for computational analysis. GitHub also features an in-browser Markdown editor, which would allow any interested party to submit an edit to a text without leaving the browser. These markdown editions will be programmically committed and pushed to each repository. 

*Phase IV*. Another transformation script will be written to ingest the ALTO XML and output TEI Simple XML. TEI Simple was chosen as an archival markup format, as it is a standardized subset of TEI XML, and eliminates many of the semantic ambiguities of the TEI superset. Many XSLT stylesheets and other tools have already been written for TEI XML, and it is the most feature-rich of textual markup languages. 
