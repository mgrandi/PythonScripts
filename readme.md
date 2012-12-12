# My Python Scripts

This was forked from https://github.com/gpambrozio/PythonScripts, so if you want the most recent versions of any of the other scripts besides as3Docs2Docset, go there

## as3Docs2Docset

Simple script to turn Actionscript 3's HTML documentation into a docset that can be browsed and quickly searched using the [Dash OSX app](http://kapeli.com/dash/). This is based off of but heavily modified from gpambrozio's original pythonDocs2Docset.

### Pre-requisites

This script uses BeautifulSoup (http://www.crummy.com/software/BeautifulSoup/) and lxml.

### Using the script

* Download the documentation for the version you want [here](http://www.adobe.com/devnet/actionscript/references.html). You should download the zip file for the HTML version of the docs.
* Expand the documentation somewhere.
* Open terminal and cd to the folder where you expanded the docs.
* Run the script from this folder.
* The script will create a as3.docset bundle with all the necessary files.
* Move the python.docset bundle to some folder. I recommend ~/Library/Developer/Shared/Documentation/DocSets
* Go to dash's preferences -> docsets, then click the + and select the as3.docset bundle you just saved somewhere
* Use it!
