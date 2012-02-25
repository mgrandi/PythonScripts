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
import bs4
import argparse
import sys
import urllib.parse



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

            # TODO REFACTOR THIS, USE BS4 NOT JUST STRAIGHT UP LINE SEARCHING
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

def isPagesLink(tag):
    """ Function to help BeautifulSoup find the <a> tags that contain a href
    to a page that we need to go through and parse. 
    @param tag - the tag that BS4 gives us
    @return boolean whether this is a tag we want or not."""
    return (tag.name == "a" 
        and tag.parent.has_attr("class") # short circut, if this is false we wont get keyerror on next line
        and tag.parent["class"][0] == "idxrow" )# class can have more then one attribute, so we use list syntax here

def getPagesFromIndex(soup, pagesDict):
    ''' goes through a all-index-LETTER.html file and gets all the links from it
    @param soup - the beautifulsoup object
    @param pagesDict - the dictonary of pages that we are adding too.'''

    # get the list of <a> tags whose href property we need to add to the dict
    tagList = soup.find_all(lambda tag: isPagesLink(tag))
    
    for tmpTag in tagList:

        # get the url, have to turn it into a list cause i can't set the fragment param on a ParseResult...grumble
        urlList = list(urllib.parse.urlparse(tmpTag["href"]))

        # clear the fragment
        urlList[5] = ""

        # resulting url without the fragment
        result = urllib.parse.urlunparse(urlList)

        # check to see if its in the dict already
        if not result in pagesDict:
            pagesDict[result] = [] # give it an empty list as a value for later on

    
def getTableTag(tableId, soup):
    ''' gets a <table> tag from the bs4 soup with a specified id.

    @param tableId - the id of the table that we want. this can either be a string or a list,
        if its a list, then we use all of the entries. 
    @param soup - the bs4 soup object we are looking for, the html page
    @return the <table> tag or none.'''

    return soup.find(lambda tag: tag.name == "table" 
            and tag.has_attr("id") 
            and tag["id"] in tableId) # this works if its a string or a list. 

def getTagListFormatOne(tableTag, tagToSearchFor, hiddenId):
    '''this method gets a list of html tags that are inside a <table> and are
    of the following format:
    <table>
        <tr>
            <td>
                <a> (or whatever tag)

    @param tableTag - the <table> html tag that we are searching for methods,properties, whatever
    @param tagToSearchFor - the tag's name to search for as a string. 
    @param hiddenId - the "id" of the <tr> tags that specifies that the whatever is hidden (as in inherited)
        and we don't want to include it.
    @return a list of BS4 tag objects.'''

    # make sure we have the right object
    if tableTag.name == "table" and isinstance(tableTag, bs4.element.Tag):

        # find descendants of the table that match what we want
        tmpList = tableTag.findAll(lambda tag: tag.name == tagToSearchFor 
            and tag.has_attr("class")
            and "signatureLink" in tag["class"] # want the signature link, not the 'type' link (like link to Boolean)
            and tag.parent is not None
            and tag.parent.name == "td"  # make sure we have the right parent
            and tag.parent.has_attr("class") 
            and "summaryTableSignatureCol" in tag.parent["class"] 
            and tag.parent.parent is not None # we don't want hidden properties. (next three lines)
            and tag.parent.parent.has_attr("class") 
            and hiddenId not in tag.parent.parent["class"])

        return tmpList

    else:

        raise ValueError("getTagListFormatOne(): the tableTag param was none or not a <table> tag! it was: {}".format(tableTag))

def getTagListFormatTwo(tableTag, tagToSearchFor, hiddenId):
    '''this method gets a list of html tags that are inside a <table> and are
    of the following format:
    <table>
        <tr>
            <td>
                <div> <-----(difference from format 1 here)
                    <a> (or whatever tag)        

    @param tableTag - the <table> html tag that we are searching for methods,properties, whatever
    @param tagToSearchFor - the tag's name to search for as a string. 
    @param hiddenId - the "id" of the <tr> tags that specifies that the whatever is hidden (as in inherited)
        and we don't want to include it. can be a string or a list. 
    @return a list of BS4 tag objects.'''

    if tableTag.name == "table" and isinstance(tableTag, bs4.element.Tag):

        tmpList = None

        # if its a list then we have to have special syntax since we can't see if an array is inside an array
        if isinstance(hiddenId, list):

            tmpList = tableTag.findAll(lambda tag: tag.name == tagToSearchFor
                and tag.has_attr("class") 
                and "signatureLink" in tag["class"]
                and tag.parent is not None
                and tag.parent.has_attr("class")
                and "summarySignature" in tag.parent["class"]
                and tag.parent.parent is not None # make sure we don't get none error
                and tag.parent.parent.parent is not None # make sure we don't get non error
                and tag.parent.parent.parent.name == "tr" # this is the element that has the 'hideWhatever' class
                and tag.parent.parent.parent.has_attr("class")
                and x not in tag.parent.parent["class"] for x in hiddenId)

        else:

            # just a string, we can do it the normal way.
            tmpList = tableTag.findAll(lambda tag: tag.name == tagToSearchFor
                and tag.has_attr("class") 
                and "signatureLink" in tag["class"]
                and tag.parent is not None
                and tag.parent.has_attr("class")
                and "summarySignature" in tag.parent["class"]
                and tag.parent.parent is not None # make sure we don't get none error
                and tag.parent.parent.parent is not None # make sure we don't get non error
                and tag.parent.parent.parent.name == "tr" # this is the element that has the 'hideWhatever' class
                and tag.parent.parent.parent.has_attr("class")
                and hiddenId not in tag.parent.parent.parent["class"])

        return tmpList

    else:

        raise ValueError("getTagListFormatTwo() the tableTag param was not a <table> tag! it was: {}".format(tableTag))

def addATagsToTokenList(tagList, refType, pageName, tokenList):
    '''this method adds <a> tags to the list of tuples that we are going to 
    serialize into the tokens.xml file. Here, the a tags are like:

    <a href="#label" class="signatureLink">label</a>

    the href is the anchor, and the text is the name of the property/method/whatever.

    @param tagList - a list of the html tags that we are getting info out of and adding to the tokenList
    @param refType - the reftype for this tag for entry into tokens.xml, see http://kapeli.com/docsets/
    @param pageName - name of the page we are on 
    @param tokenList - the list of tuples that we are adding the entry to. the tuple is of the format
        (refString, anchor)
    '''

    for tag in tagList:

        if tag.name =="a" and isinstance(tag, bs4.element.Tag):

            # convert NavigableString to a str object
            # also get rid of the # infront of the href, cause we don't write it to the tokens.xml file
            tmp = ("//apple_ref/cpp/{}/{}".format(refType, pageName + "." + str(tag.string)), tag["href"].lstrip("#"))
            tokenList.append(tmp)

        else:

            raise ValueError("addATagsToTokenList(): one of the entries in the list was not a tag obj or not a <a> tag! it was: {}".format(tag))


def addSpanTagsToTokenList(tagList, refType, pageName, anchorPrefix, tokenList):
    ''' this method adds <span> tags to the list of tuples that we are going to
    serialize into the tokens.xml file. Here, the tags look like:

    <span class="signatureLink">disabled</span>

    Notice how they don't have an anchor, because they are not <a> tags (duh). these
    actually have anchors further up the html heirarchy, but we don't need to get them
    as they are just <some prefix>:<tag name>, so we just pass in the prefix and we can
    generate the name easily.

    @param tag - a list of the html tags that we are getting info out of and adding to the tokenList
    @param refType - the reftype for this tag for entry into tokens.xml, see http://kapeli.com/docsets/
    @param anchorPrefix - since span tags don't have the anchor inside them, this is the prefix that we 
        add to the tag's string to make the anchor
    @param pageName - name of the page we are on
    @param tokenList - the list of tuples that we are adding the entry to. the tuple is of the format
        (refString, anchor)
    '''

    for tag in tagList:

        if tag.name =="span" and isinstance(tag, bs4.element.Tag):

            # convert NavigableString to a str object
            # since we dont have a href we need to create the anchor by adding the anchorPrefix + : + the tag's string value
            tmp = ("//apple_ref/cpp/{}/{}".format(refType, pageName + "." + str(tag.string)), "{}:{}".format(anchorPrefix, str(tag.string)))
            tokenList.append(tmp)

        else:

            raise ValueError("addSpanTagsToTokenList(): one of the entries in the list was not a tag obj or not a <span> tag! it was: {}".format(tag))


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
    # tuple objects, the first value is the strings that will will be of the format //apple_ref/language/type/name
    # that identifies the various classes, properties, styles, etc inside each html file. The second is the 'anchor'
    pages = {}

    # get all the pages that we need to parse
    for htmlFile in htmlPagesToParse:

        # the html files are inside the Documents folder. 
        with open(os.path.join(sourceFolder, htmlFile), "r") as f:

            # create the soup
            soup = BeautifulSoup(f)

            getPagesFromIndex(soup, pages)


    # now we need to iterate through the pages dictionary and parse each 'pageLink',
    # adding the token string to the list that is the value for every key in the pages dict
    # the things that go in the list are the '//apple_ref/cpp/func/PyByteArray_FromObject'
    # type strings. see http://kapeli.com/docsets/
    #
    # Type Mappings:
    #
    # Constant Static Property -> constant (clconst)
    # Property-> property (instp)
    # protected properties -> property (instp)
    # Skin Part -> property (clconst)
    # Event -> binding (binding)
    # Class -> class (cl)
    # method -> method (clm)
    # protected method -> method (clm)
    # Interface, package -> interface (intf)
    # Style -> property (clconst)
    # mobile theme styles -> property (clconst)
    # Package Function -> function (func)
    for pageLink, tokenList in pages.items():

        #with open(os.path.join(sourceFolder, pageLink), "r") as f:
        with open(os.path.join(sourceFolder, "spark/components/supportClasses/ButtonBase.html"), "r") as f:

            print("opening {}".format(pageLink))

            # make the beautifulsoup object that reprsents the html
            soup = BeautifulSoup(f)

            # name of the page/class, the big "title" thing on the grey bar, like "JSON" or "Top Level"
            # this also seems to have a "non breaking backspace" at the end....strip it off
            pageName = str(soup.find(lambda tag: tag.name == "convert" 
                and tag.parent is not None
                and tag.parent.has_attr("id")
                and tag.parent["id"] == "subTitle").string).strip()

            # **************************
            # properties
            # **************************

            # get the table tag 
            propertyTableTag = getTableTag("summaryTableProperty", soup)

            if propertyTableTag:
                # get the tag list
                propList = getTagListFormatOne(propertyTableTag, "a", "hideInheritedProperty")

                # add it to tokenlist
                addATagsToTokenList(propList, "clconst", pageName, tokenList)
            
            # **************************
            # protected properties
            # **************************


            # get the table tag first. This code seems to be the same as the properties one, only with different ids
            protPropertyTableTag = getTableTag("summaryTableProtectedProperty", soup)

            # only continue if we actually have a table tag (and therefore properties)
            if protPropertyTableTag:

                # get as list
                protPropList = getTagListFormatOne(protPropertyTableTag, "a", "hideInheritedProtectedProperty")

                # add to token list
                addATagsToTokenList(protPropList, "clconst", pageName, tokenList)


            # **************************
            # methods
            # **************************

            # get table tag for protected methods
            methodTableTag = getTableTag("summaryTableMethod", soup)

            # make sure we actually have methods
            if methodTableTag:

                # get as list
                methodList = getTagListFormatTwo(methodTableTag, "a", "hideInheritedMethod")

                # add to token list
                addATagsToTokenList(methodList, "clm", pageName, tokenList)
                

            # **************************
            # protected methods
            # **************************

            # get table tag for methods. The following code is pretty much the same as the "methods" only with different ID's and such
            protMethodTableTag = getTableTag("summaryTableProtectedMethod", soup)

            # make sure we actually have protected methods
            if protMethodTableTag:

                # get as list
                protMethodList = getTagListFormatTwo(protMethodTableTag, "a", "hideInheritedProtectedMethod")

                # add to token list
                addATagsToTokenList(protMethodList, "clm", pageName, tokenList)


            # **************************
            # events
            # **************************

            # get table tag
            eventTableTag = getTableTag("summaryTableEvent", soup)

            # make sure we actually have events
            if eventTableTag:

                # get as list
                eventList = getTagListFormatTwo(eventTableTag, "a", "hideInheritedEvent")

                # add to token list
                addATagsToTokenList(eventList, "binding", pageName, tokenList)


            # **************************
            # styles
            # **************************

            # get tables tag ( three of them)
            styleTableTag = getTableTag(["summaryTablecommonStyle", "summaryTablesparkStyle", "summaryTablemobileStyle"], soup)

            # make sure we actually have styles
            if styleTableTag:

                # get as list, where we exclude all elements whose class is in our list
                styleTwoList = getTagListFormatTwo(styleTableTag, "span", ["hideInheritedcommonStyle", "hideInheritedmobileStyle", "hideInheritedsparkStyle"])

                # add to token list. note these are span tags so we need a diff method
                addSpanTagsToTokenList(styleTwoList, "clconst", "style", pageName, tokenList)

            # **************************
            # skin parts
            # **************************

            # seems to be the same as methods, with it being inside a div instead of the td

            # NOTE: the skin parts don't have links, unless they are inherited. since we don't care about inherited styles
            # then we just get the non link ones which are in <span> tags. However, they do have anchors builtin,
            # which are just of the form "SkinPart:stylename"

            # **************************
            # skin states
            # **************************

            # **************************
            # effects
            # **************************

            # **************************
            # constants
            # **************************

            import pprint
            pprint.pprint(tokenList)
            break

            # do stuff with descendants

            # TODO make sure we use "in" for the class stuff since it returns a list

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

    try:
        makeDocset(args)
    except Exception as e:

        trouble("problem making the docset: error was: {}".format(e))