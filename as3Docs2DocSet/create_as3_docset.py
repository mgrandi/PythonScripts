#!/usr/bin/env python
# encoding: utf-8
#
# forked from https://github.com/gpambrozio/PythonScripts
#
# Edited script to create a .docset for the as3/flex documentation
# 
# edited by Mark Grandi
# 2/21/2012
# https://github.com/mgrandi/PythonScripts
#

import re
import os
import shutil
import subprocess
from bs4 import BeautifulSoup

## Tries to find docsetutil
possible_docsetutil_path = [
    "/Developer/usr/bin/docsetutil",
    "/Applications/Xcode.app/Contents/Developer/usr/bin/docsetutil",
]
docsetutil_path = [path for path in possible_docsetutil_path if os.path.exists(path)]
if len(docsetutil_path) == 0:
    print "Could not find docsetutil. Please check for docsetutil's location and set it inside the script."
    exit(1)

docsetutil_path = docsetutil_path[0]

## Script should run in the folder where the docs live
source_folder = os.getcwd() + "/"

# destination folder
dest_folder = source_folder + "as3.docset/" 

# make sure we are in the right folder, search for "ActionScript&reg; 3.0 Reference for the Adobe&reg; Flash&reg; Platform"
# in index.html
try:
    with open("index.html", "r") as f:

        success = False

        # see if we can find that line. if we do, break out of the loop and keep going. if not, print error and exit
        for line in f:
            search = re.search("ActionScript&reg; 3.0 Reference for the Adobe&reg; Flash&reg; Platform", line)

            if search:
                success = True
                break
        if not success:
            print("This doesn't seem to be the actionscript 3 documentation, are you in the right folder?")
            sys.exit(1)

except IOError:

    print("Could not find index.html, are you in the right folder?")
    sys.exit(1)

    


def is_something(tag, something):
    """ Function to help BeautifulSoup find our tokens """
    return (tag.name == "dt"
            and tag.has_key("id")
            and tag.parent.name == "dl"
            and tag.parent['class'][0] == something)


def collect(soup, what, identifier, names):
    """ Collects all nodes of a certain type from a BeautifulSoup document """
    whats = soup.find_all(lambda tag: is_something(tag, what))
    for n in whats:
        apple_ref = "//apple_ref/cpp/%s/%s" % (identifier, n["id"])
        new_tag = soup.new_tag("a")
        new_tag['name'] = apple_ref
        n.insert_before(new_tag)
        names.append(apple_ref)


## Clean up first
if os.path.exists(dest_folder):
    shutil.rmtree(dest_folder)

## Create all the necessary folder hierarchy
os.makedirs(dest_folder + "Contents/Resources/Documents/")
docset_folder = dest_folder
dest_folder = dest_folder + "Contents/"

## Find the module's index file. this is probably the as3's class index
possible_modindex_path = [
    "package-list.html"
]
modindex_path = [path for path in possible_modindex_path if os.path.exists(source_folder + path)]
if len(modindex_path) == 0:
    print "Could not find the as3 package index. Please check your doc folder structure and try again."
    exit(2)
modindex_path = modindex_path[0]

## Create Info.plist
with open(dest_folder + "Info.plist", "w") as info:
    info.write("""<?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
    <plist version="1.0">
    <dict>
        <key>CFBundleIdentifier</key>
        <string>as3</string>
        <key>CFBundleName</key>
        <string>Actionscript 3</string>
        <key>DocSetPlatformFamily</key>
        <string>as3</string>
    </dict>
    </plist>
    """)

## Create Nodes.xml
dest_folder = dest_folder + "Resources/"
with open(dest_folder + "Nodes.xml", "w") as nodes:
    nodes.write("""<?xml version="1.0" encoding="UTF-8"?>
    <DocSetNodes version="1.0">
        <TOC>
            <Node type="folder">
                <Name>Package Index</Name>
                <Path>%s</Path>
            </Node>
        </TOC>
    </DocSetNodes>
    """ % modindex_path)


## Create the tokens file
tokens = open(dest_folder + "Tokens.xml", "w")
dest_folder = dest_folder + "Documents/"

## Copy some static files
# markedit i probably need to copy everything.... check on that though
shutil.copy(source_folder + "searchindex.js", dest_folder)
shutil.copy(source_folder + modindex_path, dest_folder)
shutil.copy(source_folder + "genindex-all.html", dest_folder)
shutil.copy(source_folder + "library/index.html", dest_folder)
shutil.copytree(source_folder + "_images", dest_folder + "_images")
shutil.copytree(source_folder + "_static", dest_folder + "_static")

## I'll hide the header because it makes no sense in a docset
## and messes up Dash
css = open(dest_folder + "_static/basic.css", "a+")
css.write("div.related {display:none;}\n")
css.close()
css = open(dest_folder + "_static/default.css", "a+")
css.write("a.headerlink {display:none;}\n")
css.close()

## Start of the tokens file
tokens.write("""<?xml version="1.0" encoding="UTF-8"?>
<Tokens version="1.0">
""")

## Collect pages first
pages = {}

## Collect pages from the package index
f = open(source_folder + modindex_path, 'r')
for line in f:
    search = re.search("<a href=\"(.*)#.*?\"><tt class=\"xref\">(.*?)</tt>", line)
    if search:
        href = search.group(1)
        name = search.group(2)
        if not href in pages:
            pages[href] = []

        apple_ref = "//apple_ref/cpp/cat/%s" % name # add entry for category (aka python module)
        pages[href].append(apple_ref)

f.close()

## Collect pages from the general index
f = open(source_folder + "genindex-all.html", 'r')
for line in f:
    for search in re.finditer("(<dt>|, )<a href=\"([^#]+).*?\">", line):
        href = search.group(2)
        if not href in pages:
            pages[href] = [] # NOTE FOR THESE , stuff gets added in the collect method, see below in the for in loop,
                            # we just create the entry in the dictionary with the url and an empty list if its not there

f.close()

## Collect pages from the library index
f = open(source_folder + "library/index.html", 'r')
for line in f:
    for search in re.finditer("<a class=\"reference external\" href=\"([^#\"]+).*?\">", line):
        href = "library/" + search.group(1)
        if not ("http://" in href or "https://" in href or href in pages):
            pages[href] = [] # NOTE FOR THESE , stuff gets added in the collect method, see below in the for in loop
                            # we just create the entry in the dictionary with the url and an empty list if its not there
f.close()

## Now write to tokens
for href, names in pages.items():

    soup = BeautifulSoup(open(source_folder + href))

    collect(soup, "class", "cl", names) # need to figure out what these do
    collect(soup, "method", "clm", names)
    collect(soup, "classmethod", "clm", names)
    collect(soup, "function", "func", names)
    collect(soup, "exception", "cl", names)
    collect(soup, "attribute", "instp", names)

    if len(names) > 0:
        tokens.write("<File path=\"%s\">\n" % href) # each href,names pair is a file. The "file" is the href
        for name in names:
            tokens.write("\t<Token><TokenIdentifier>%s</TokenIdentifier><Anchor>%s</Anchor></Token>\n" % (name, name))
        tokens.write("</File>\n") # the names are the things inside each html file, classes, functions, etc

        newFile = dest_folder + href
        if not os.path.exists(os.path.dirname(newFile)):
            os.makedirs(os.path.dirname(newFile))
        newFile = open(newFile, "w")
        newFile.write(str(soup))
        newFile.close()

tokens.write("</Tokens>")
tokens.close()

subprocess.call([docsetutil_path, "index", docset_folder])

## Cleanup
os.remove(docset_folder + "Contents/Resources/Nodes.xml")
os.remove(docset_folder + "Contents/Resources/Tokens.xml")
