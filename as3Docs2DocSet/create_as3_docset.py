#!/usr/bin/env python3
# encoding: utf-8
#
# forked from https://github.com/gpambrozio/PythonScripts
#
# Edited script to create a .docset for the as3/flex documentation
# Note that its now in python 3.
# 
# edited by Mark Grandi
# 2/21/2012
# https://github.com/mgrandi/PythonScripts
#

import re
import os
import os.path
import shutil
import subprocess
from bs4 import BeautifulSoup
import argparse



def verify_docpath(argString):
    ''' this method is the 'type' of the docPath argument, and this is called
    to 'verify' the docpath path, to make sure that there is the documentation at the specified location
    @param argString - the string that the ArgumentParser got from the command line
    @return a string, the same string that it encountered or throws an error if this path isn't the as3 docpath'''


    # make sure the path exists
    if not os.path.exists(argString):

        raise argparse.ArgumentTypeError("the path specified does not exist")

    # make sure we are in the right folder, search for "ActionScript&reg; 3.0 Reference for the Adobe&reg; Flash&reg; Platform"
    # in index.html
    try:
        with open(os.path.join(argString, "index.html"), "r") as f:

            success = False

            # see if we can find that line. if we do, break out of the loop and keep going. if not, print error and exit
            for line in f:
                search = re.search("ActionScript&reg; 3.0 Reference for the Adobe&reg; Flash&reg; Platform", line)

                if search:
                    success = True
                    break
            if not success:
                raise argparse.ArgumentTypeError("This doesn't seem to be the actionscript 3 documentation, are you in the right folder?")
                

    except IOError:

        raise argparse.ArgumentTypeError("Could not find index.html, are you in the right folder?")



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
        apple_ref = "//apple_ref/cpp/{}/{}".format(identifier, n["id"])
        new_tag = soup.new_tag("a")
        new_tag['name'] = apple_ref
        n.insert_before(new_tag)
        names.append(apple_ref)

def trouble(message):
    ''' prints an error message and exits with status 1
    @param message - the error message'''

    print(message)
    sys.exit(1)

def makeDocset(args):
    ''' does the work to make the docset
        @param args - the argument parser namespace object
        '''

    ## Tries to find docsetutil
    possible_docsetutil_path = [
        "/Developer/usr/bin/docsetutil",
        "/Applications/Xcode.app/Contents/Developer/usr/bin/docsetutil",
    ]
    docsetutil_path = [path for path in possible_docsetutil_path if os.path.exists(path)]
    if len(docsetutil_path) == 0:
        trouble("Could not find docsetutil. Please check for docsetutil's location and set it inside the script.")

    docsetutil_path = docsetutil_path[0]

    ## Script should run in the folder where the docs live
    source_folder = os.getcwd()

    # destination folder. this changes throughout the script.
    dest_folder = os.path.join(source_folder,"as3.docset")


    ## Clean up first if the output folders already exist
    if os.path.exists(dest_folder):
        shutil.rmtree(dest_folder)

    ## Create all the necessary folder hierarchy
    os.makedirs(dest_folder + "Contents/Resources/Documents/")
    docset_folder = dest_folder
    dest_folder = os.path.join(dest_folder, "Contents")

    ## Find the module's index file. this is probably the as3's class index
    possible_modindex_path = [
        "package-list.html"
    ]
    modindex_path = [path for path in possible_modindex_path if os.path.exists(source_folder + path)]
    if len(modindex_path) == 0:
        trouble("Could not find the as3 package index. Please check your doc folder structure and try again.")

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
    dest_folder = os.path.join(dest_folder , "Resources")
    with open(dest_folder + "Nodes.xml", "w") as nodes:
        nodes.write("""<?xml version="1.0" encoding="UTF-8"?>
        <DocSetNodes version="1.0">
            <TOC>
                <Node type="folder">
                    <Name>Package Index</Name>
                    <Path>{}</Path>
                </Node>
            </TOC>
        </DocSetNodes>
        """.format(modindex_path))



    dest_folder = os.path.join(dest_folder ,"Documents")

    # copy the entire langref folder over
    shutil.copytree(source_folder, dest_folder)

    ## I'll hide the header because it makes no sense in a docset
    ## and messes up Dash
    ## TODO make edits to the css file! not these though, these are for the python docs
    '''
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
    '''

    htmlPagesToParse = ["all-index-A.html",
                        "all-index-B.html",
                        "all-index-C.html",
                        "all-index-D.html",
                        "all-index-E.html",
                        "all-index-F.html",
                        "all-index-G.html",
                        "all-index-H.html",
                        "all-index-I.html",
                        "all-index-J.html",
                        "all-index-K.html",
                        "all-index-L.html",
                        "all-index-M.html",
                        "all-index-N.html",
                        "all-index-O.html",
                        "all-index-P.html",
                        "all-index-Q.html",
                        "all-index-R.html",
                        "all-index-S.html",
                        "all-index-T.html",
                        "all-index-U.html",
                        "all-index-V.html",
                        "all-index-W.html",
                        "all-index-X.html",
                        "all-index-Y.html",
                        "all-index-Z.html",
                        "all-index-Symbols.html"]

    # dictionary that will hold the pages
    # key is the html files path, and value is a list of 
    # strings that will will be of the format //apple_ref/language/type/name
    # that identifies the various classes, properties, styles, etc inside each html file.
    pages = {}

    for htmlFile in htmlPagesToParse:

        # we are in the 'langref' folder, and everything is in there
        with open(htmlFile, "r") as f:

            # create the soup
            soup = BeautifulSoup(f)

            # get all the <td> tags that have the class name "idxrow", which contains as a child stuff we want. 
            tmpList = soup.find_all("td", {"class": "idxrow"})

            for tag in tmpList:

                print(tag.string)



    '''

    ## Now write to tokens

    ## Create the tokens file
    tokens = open(dest_folder + "Tokens.xml", "w")
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
    '''


if __name__ == "__main__":
    # if we are being run as a real program

    parser = argparse.ArgumentParser(description="create a .docset file for the as3 documentation", 
        epilog="Copyright 2012 Mark Grandi, forked from https://github.com/gpambrozio/PythonScripts")

    # optional arguments, if specified these are the input and output files, if not specified, it uses stdin and stdout
    parser.add_argument('docPath', help="the directory where the as3 documentation is located", type=verify_docpath)
    
    parser.add_argument('outputPath', help="the directory to place the resulting .docset ")
    args = parser.parse_args()

    makeDocset(args)