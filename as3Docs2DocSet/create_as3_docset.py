#!/usr/bin/env python3
# encoding: utf-8
#
# forked from https://github.com/gpambrozio/PythonScripts
#
# Edited script to create a .docset for the as3/flex documentation
# Note that its now in python 3.
# also requires BeautifulSoup, which is included. 
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
import sys



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

            # here , we are successful, this is the as3 docs
            return argString

                

    except IOError:

        raise argparse.ArgumentTypeError("Could not find index.html, are you in the right folder?")

def verify_outputpath(argString):
    ''' verifies the output path for the argument parser
    @param argString - the argument string that gets passed to us by argument parser
    @return the same string we got, if the path is valid, else raise exception'''


    if not os.path.exists(argString):

        raise argparse.ArgumentTypeError("the path specified does not exist")

    return argString

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
    possibleDocsetutilPath= [
        "/Developer/usr/bin/docsetutil",
        "/Applications/Xcode.app/Contents/Developer/usr/bin/docsetutil",
    ]
    docsetutilPath = [path for path in possibleDocsetutilPath if os.path.exists(path)]
    if len(docsetutilPath) == 0:
        trouble("Could not find docsetutil. Please check for docsetutil's location and set it inside the script.")

    docsetutilPath = docsetutilPath[0]

    ## Script should run in the folder where the docs live
    sourceFolder = args.docPath

    # destination folder of the main as3.docset folder/file/thing
    docsetFolder = os.path.join(args.outputPath,"as3.docset")


    ## Clean up first if the output folders already exist
    if os.path.exists(docsetFolder):
        shutil.rmtree(docsetFolder)

    print(docsetFolder)

    ## Create all the necessary folder hierarchy. Don't create "documents" because the copytree will create that 
    # when we copy the as3 docs over to the "documents" foler. 
    os.makedirs(os.path.join(docsetFolder,"Contents", "Resources"))
    contentsFolder = os.path.join(docsetFolder, "Contents")

    ## Create Info.plist
    with open(os.path.join(contentsFolder, "Info.plist"), "w") as info:
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

    #Find the module's index file. This is the as3's package-list.html file. 
    #This is just a XML file that points to the main index file of your documentation
    possibleModindexPath = [
        "package-list.html"
    ]
    modindexPath = [path for path in possibleModindexPath if os.path.exists(sourceFolder + path)]

    # if we couldn't find the package index
    if len(modindexPath) == 0:
        trouble("Could not find the as3 package index. Please check your doc folder structure and try again.")

    modindexPath = modindexPath[0]

    ## Create Nodes.xml
    resourcesFolder = os.path.join(contentsFolder , "Resources")
    with open(os.path.join(resourcesFolder ,"Nodes.xml"), "w") as nodes:
        nodes.write("""<?xml version="1.0" encoding="UTF-8"?>
        <DocSetNodes version="1.0">
            <TOC>
                <Node type="folder">
                    <Name>Package Index</Name>
                    <Path>{}</Path>
                </Node>
            </TOC>
        </DocSetNodes>
        """.format(modindexPath))

    documentsFolder = os.path.join(resourcesFolder ,"Documents")

    # copy the entire langref folder over. This creates "Documents"
    shutil.copytree(sourceFolder, documentsFolder)

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

        # the html files are inside the Documents folder. 
        with open(os.path.join(documentsFolder, htmlFile), "r") as f:

            # create the soup
            soup = BeautifulSoup(f)

            # get all the <td> tags that have the class name "idxrow", which contains as a child stuff we want. 
            tmpList = soup.find_all("td", {"class": "idxrow"})

            for tag in tmpList:

                print(tag)



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
    
    parser.add_argument('--outputPath', help="the directory to place the resulting .docset. defaults to os.getcwd()", type=verify_outputpath, default=os.getcwd())
    args = parser.parse_args()

    makeDocset(args)