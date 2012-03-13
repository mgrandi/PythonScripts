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
import traceback
import sys
import urllib.parse



# misc variables
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


staticFiles = ["ajax-loader.gif",
    "asfilter.css",
    "chcsearch.css",
    "chcsearchlight.css",
    "content-fonts.css",
    "content-hyperlinks.css",
    "content-ie6.css",
    "content.css",
    "favicon.ico",
    "filter-style.css",
    "filters-values.xml",
    "filters.xml",
    "helpmap.txt",
    "helpmapBaseUrl.txt",
    "ion-style.css",
    "ion.css",
    "jslr-style.css",
    "localeSpecific.css",
    "logoION.jpg",
    "override.css",
    "popup.css",
    "print.css",
    "readme.txt",
    "searchbutton.png",
    "standalone-style.css",
    "style.css",
    "suggestionFile.xml",
    "titleTableTopION.jpg",
    "tree.css",
    "appendixes.html",
    "index.html",
    "class-summary.html",
    "package-summary.html",
    "package-list.html",
    "charset-codes.html",
    "compilerErrors.html",
    "compilerWarnings.html",
    "conventions.html",
    "deprecated.html",
    "index-list.html",
    "motionXSD.html",
    "mxml-tag-detail.html",
    "mxml-tags.html",
    "runtimeErrors.html",
    "specialTypes.html",
    "TimedTextTags.html"]

staticFolders = ["images"]


def printTraceback():
    '''prints the traceback'''

    # get variables for the method we are about to call
    exc_type, exc_value, exc_traceback = sys.exc_info()

    # print exception
    traceback.print_exception(exc_type, exc_value, exc_traceback)

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
        with open(os.path.join(argString, "index.html"), "r", encoding="utf-8") as f:

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
        # note: you have to use os.path.normpath here or else we get duplicate entries, cause we somehow get 
        # "./String.html" and "String.html", which are the same file, but different paths!
        result = os.path.normpath(urllib.parse.urlunparse(urlList))

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

    # TODO: we should probably do something similar like with formatTwo where we can take multiple arguments 
    # for hiddenId. I dont have any use for it now however.

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
                and [x not in tag.parent.parent["class"] for x in hiddenId])

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

def getTokenAnchorTupleListFromATags(tagList, refType, pageName):
    '''this method adds <a> tags to the list of tuples that we are going to 
    serialize into the tokens.xml file. Here, the a tags are like:

    <a href="#label" class="signatureLink">label</a>

    the href is the anchor, and the text is the name of the property/method/whatever.

    @param tagList - a list of the html tags that we are getting info out of and adding to the tokenList
    @param refType - the reftype for this tag for entry into tokens.xml, see http://kapeli.com/docsets/
    @param pageName - name of the page we are on 
    @return a list of the tuples that we created, of the format (refString, anchor)
    '''

    tokenList = []
    for tag in tagList:

        if tag.name =="a" and isinstance(tag, bs4.element.Tag):

            # convert NavigableString to a str object
            # also get rid of the # infront of the href, cause we don't write it to the tokens.xml file
            tmp = ("//apple_ref/cpp/{}/{}".format(refType, pageName + "." + str(tag.string)), tag["href"].lstrip("#"))
            tokenList.append(tmp)

        else:

            raise ValueError("addATagsToTokenList(): one of the entries in the list was not a tag obj or not a <a> tag! it was: {}".format(tag))

    return tokenList

def getTokenAnchorTupleListFromSpanTags(tagList, refType, pageName, anchorPrefix):
    ''' this method adds <span> tags to the list of tuples that we are going to
    serialize into the tokens.xml file. Here, the tags look like:

    <span class="signatureLink">disabled</span>

    Notice how they don't have an anchor, because they are not <a> tags (duh). these
    actually have anchors further up the html heirarchy, but we don't need to get them
    as they are just <some prefix>:<tag name>, so we just pass in the prefix and we can
    generate the name easily.

    @param tagList - a list of the html tags that we are getting info out of and adding to the tokenList
    @param refType - the reftype for this tag for entry into tokens.xml, see http://kapeli.com/docsets/
    @param anchorPrefix - since span tags don't have the anchor inside them, this is the prefix that we 
        add to the tag's string to make the anchor
    @param pageName - name of the page we are on
    @return a list of the tuples that we created, of the format (refString, anchor)
    '''

    tokenList = []
    for tag in tagList:

        if tag.name =="span" and isinstance(tag, bs4.element.Tag):

            # convert NavigableString to a str object
            # since we dont have a href we need to create the anchor by adding the anchorPrefix + : + the tag's string value
            tmp = ("//apple_ref/cpp/{}/{}".format(refType, pageName + "." + str(tag.string)), "{}:{}".format(anchorPrefix, str(tag.string)))
            tokenList.append(tmp)

        else:

            raise ValueError("addSpanTagsToTokenList(): one of the entries in the list was not a tag obj or not a <span> tag! it was: {}".format(tag))

    return tokenList

def getClassTypeTupleFromClassSignature(soup, pageName):
    '''every class page has a class signature at the top, looking like

    Interface public interface IContentLoader extends IEventDispatcher

    so here we find that line in the html, (the 'title label' to the left) see if it either has 
    "interface" or "class" in it, and then return the correct tuple (appleref, anchor) for the page. 
    Note that the  anchor for regular classes will be the "constructorDetail" anchor, while the interface one
    won't have an anchor, since there really isn't anything useful to anchor to, it will just 
    take them to the page i guess

    @param soup - the bs4 object
    @param pageName - name of the page
    @returns the tuple that we add to the token list'''

    tmp = None
    tmp2 = None
    classType = None

    try:
        # find the <td> tag that has the class signature
        tmp = soup.find(lambda tag: tag.name == "td" 
            and tag.has_attr("class") 
            and "classSignature" in tag["class"])

        # now the type of this class (whether its a package/interface) is the <td> element 
        # that is right before this, so we use previous_sibling
        tmp2 = tmp.previous_sibling


        classType = str(tmp2.string).lower()

    except Exception as e:

        # bail out if there is no previous sibling, here in case some pages are weird and don't have this element!
        # like pages such as "package.html" or "operators.html". we still parse them for properties/methods
        # we just don't return a class/interface token
        return None

    # continue as normal

    # return token string and anchor depending on the class type
    if  classType == "interface":

        return ("//apple_ref/cpp/{}/{}".format("intf", pageName), "")

    elif classType == "class":

        # need to make sure here that we have a #constructionDetail anchor, cause SOME PAGES DON'T 
        # like flash/display/ShaderPrecision.html
        constructorTag = soup.find(lambda tag: tag.name == "a"
            and tag.has_attr("name")
            and tag["name"] == "constructorDetail")

        if constructorTag is not None:

            # return with anchor, there is actually an anchor in the page
            return ("//apple_ref/cpp/{}/{}".format("cl", pageName), "constructorDetail")

        else:

            # return with no anchor
            return ("//apple_ref/cpp/{}/{}".format("cl", pageName), "")
        

    else:

        raise ValueError("unknown class type! {}".format(classType))





def modifyAndSaveHtml(soup, destinationFile, tokenList):
    '''takes a html file from the documentation, and we remove certain elements 
    and modify some attributes to make it so it actually views properly in the 
    dash viewer. This method also inserts the appleref anchor links so dash can 
    use them for the Table of Contents feature.

    @param soup - the bs4 object we are using to modify the html and save it to the new location
    @param destinationFile - where we are saving the modified html
    @param tokenList - the list of tuples, of the form (appleRef, anchor) for the current page
        so that we can add appleref anchor links on the webpage.'''

    pageSoup = soup

    # find the following things and remove them:
    # 1 - div id "filter_panel_float" , the thing that is above the page title (has package/clas filters)
    # 2 - div id splitter # stuff on the left we dont want
    # 3 - div id mainleft # stuff on the left we dont want

    # 1
    filterTag = pageSoup.find(lambda tag: tag.name == "div" 
        and tag.has_attr("id")
        and tag["id"] ==  "filter_panel_float")

    if filterTag:
        filterTag.decompose() # deletes the tag

    # 2
    splitTag = pageSoup.find(lambda tag: tag.name == "div"
        and tag.has_attr("id")
        and tag["id"] == "splitter"
        and tag.has_attr("class")
        and tag["class"] == "splitter")

    if splitTag:
        splitTag.decompose() # deletes the tag

    # 3
    leftTag = pageSoup.find(lambda tag: tag.name == "div"
        and tag.has_attr("class")
        and tag["class"] == "mainleft"
        and tag.has_attr("id")
        and tag["id"] == "toc") # if javascript is on, then it just brings back this element, wtf?

    if leftTag:
        leftTag.decompose() # delete tag

    # now find the  maincontainer div and delete the style attribute cause its set to none by default
    mainTag = pageSoup.find(lambda tag: tag.name == "div"
        and tag.has_attr("id")
        and tag["id"] == "maincontainer"
        and tag.has_attr("style"))

    if mainTag:
        del mainTag["style"] # delete style attribute

    # get rid of the search bar in the top right
    searchTag = pageSoup.find(lambda tag: tag.name == "form"
        and tag.has_attr("class")
        and "searchFormION" in tag["class"]) # i have to say "in" because class is a multi valued attribute

    if searchTag:
        searchTag.decompose() # delete tag


    # make it so all 'inherited' properties/methods are shown by default since we are not going to be able to use JS. 
    # delete this if you want to use js and have the normal arrow showing hide/show inherited stuff
    inheritedTags = pageSoup.find_all(lambda tag: (tag.name == "tr"
        or tag.name == "table") # tables can have this too
        and tag.has_attr("class")
        and [not x.startswith("hide") for x in tag["class"]])

    if inheritedTags:
        for tag in inheritedTags:
            classNameList = tag["class"]
            resultList = []

            # here, since class is a multi valued attribute, we can't just delete the entire "class"
            # attribute, we have to remove the one that starts with "hide", but leaves the rest alone.
            for className in classNameList:

                if not className.startswith("hide"):
                    resultList.append(className)

            tag["class"] = resultList

    # get rid of the "show / hide inherited properties" or whatever links.
    # note that there are 'two' tags with the class "showHideLinks", the one with
    # div tags as children is the one we want. (the other one, with <a> tags, is a link that usually says
    # "click for more information on <something>")
    showHideTags = pageSoup.find_all(lambda tag: tag.name == "div"
        and tag.has_attr("class")
        and "showHideLinks" in tag["class"]
        and delShowHideTagsHelper(tag)) # use helper method

    if showHideTags:
        for iterTag in showHideTags:
            iterTag.decompose() # delete each of the tags that match this.


    # now we iterate through the tokenList, and add appleref anchor links right after the anchor links that 
    # the page already has for all the methods/properties/styles/etc, for dash's table of contents feature
    for iterTuple in tokenList:

        appleRef = iterTuple[0]
        anchorLink = iterTuple[1]

        if anchorLink != "": # don't do this if we don't have an anchor

            # find the anchor link in the webpage
            anchorTag = pageSoup.find(lambda tag: tag.name == "a"
                and tag.has_attr("name")
                and tag["name"] == anchorLink)

            # add new anchor link tag right after the one we found.
            newTag = pageSoup.new_tag("a")
            newTag["name"] = appleRef
            anchorTag.insert_after(newTag)

    # make sure we have folder heirarchy or else we get no such file/directory
    if not os.path.exists(os.path.split(destinationFile)[0]):
        os.makedirs(os.path.split(destinationFile)[0]) # creates up to leaf directory, aka the html file

    # now write the modified soup to the destination dir
    with open(destinationFile, "w", encoding="utf-8") as f:

        f.write(str(pageSoup))


def delShowHideTagsHelper(tag):
    ''' helper method to help us determine if a <div> tag is the correct tag to delete
    when we are getting rid of the "show/hide inherited whatever" tags.

    @param tag - the tag that BS4 gives us when filtering
    @return boolean, whether we want to delete this tag or not.
    '''
    for tag in tag.contents:            
        if tag.name == "a":
            return False
    return True

def trouble(message):
    ''' prints an error message and exits with status 1
    @param message - the error message'''

    print(message + "\n")
    printTraceback()
    sys.exit(1)


def copyAndModifyStaticFilesToDocs(srcFolder, destFolder):
    ''' copies static files to the Documents folder, that don't get
    copied automatically during our script run. Css files, html files,etc.
    For a few CSS files that we need to modify, we modify them here.

    @param srcFolder - folder that we are copying stuff from
    @param destFolder - the folder we are copying stuff too'''

    # copy all of the index files from our htmlPagesToParse list at the top 
    # of the script
    for entry in htmlPagesToParse:

        shutil.copy2(os.path.join(srcFolder, entry), os.path.join(destFolder, entry))


    # copy the static to the documents directory
    for entry in staticFiles:

        # have special cases 
        if entry == "filter-style.css":

            # here we change the css top property to be smaller so we dont have a big gap at the top
            tmpCss = None
            with open(os.path.join(srcFolder, entry), "r", encoding="utf-8") as f:
                tmpCss = f.read()

            # change the top property
            tmpCss = re.sub("top:.*?;", "top:113px", tmpCss) # if the pattern isnt found, string is returned unchanged

            # write modified file to dest directory
            with open(os.path.join(destFolder, entry), "w", encoding="utf-8") as f:
                f.write(tmpCss)

        else:
            # normal file, just copy it to dest directory
            shutil.copy2(os.path.join(srcFolder, entry), os.path.join(destFolder, entry))

    # copy static folders
    for entry in staticFolders:

        shutil.copytree(os.path.join(srcFolder, entry), os.path.join(destFolder, entry))


def makeDocset(args):
    ''' does the work to make the docset
        @param args - the argument parser namespace object
        '''

    if not args.noDocsetutil:
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

    print("Docset being saved to: {}".format(docsetFolder))

    ## Create all the necessary folder hierarchy. 
    os.makedirs(os.path.join(docsetFolder,"Contents", "Resources", "Documents"))
    contentsFolder = os.path.join(docsetFolder, "Contents")

    ## Create Info.plist
    # lazy so we just write it as a string, instead of using bs4
    print("Creating {}".format(os.path.join(contentsFolder, "Info.plist")))
    with open(os.path.join(contentsFolder, "Info.plist"), "w", encoding="utf-8") as info:
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
    print("Creating {}".format(os.path.join(resourcesFolder ,"Nodes.xml")))
    with open(os.path.join(resourcesFolder ,"Nodes.xml"), "w", encoding="utf-8") as nodes:
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

    # var to the  Documents folder inside the .docset file
    documentsFolder = os.path.join(resourcesFolder ,"Documents")

    # copy over static files, images, scripts, pages that don't get transferred automatically
    # and modify them if necessary
    copyAndModifyStaticFilesToDocs(sourceFolder, documentsFolder)

    # dictionary that will hold the pages
    # key is the html files path, and value is a list of 
    # tuple objects, the first value is the strings that will will be of the format //apple_ref/language/type/name
    # that identifies the various classes, properties, styles, etc inside each html file. The second is the 'anchor'
    pages = {}

    print("Figuring out what files we need to parse")
    # get all the pages that we need to parse. uses the htmlPagesToParse list defined at the top
    for htmlFile in htmlPagesToParse:

        # the html files are inside the Documents folder. 
        with open(os.path.join(sourceFolder, htmlFile), "r", encoding="utf-8") as f:

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
    # Skin Part -> property (instp)
    # skin states -> property (instp)
    # effects -> property (instp)
    # Event -> binding (binding)
    # Class -> class (cl)
    # method -> method (clm)
    # protected method -> method (clm)
    # Interface, package -> interface (intf)
    # Style -> property (instp)
    # mobile theme styles -> property (instp)
    # Package -> category (cat)

    counter = 1
    total = len(pages)

    for pageLink, tokenList in pages.items():

        soup = None

        # scrape the page and get the tokens
        # TODO here we have to open the page for the first time, and we open it again when we call
        # modifyAndSaveHtml, maybe i can just give it the soup variable to save it a bit of processing time!
        with open(os.path.join(sourceFolder, pageLink), "r", encoding="utf-8") as f:

            print("Parsing file {}/{}: {}".format(counter, total, pageLink))
            counter += 1

            # make the beautifulsoup object that reprsents the html
            soup = BeautifulSoup(f)

        # name of the page/class, the big "title" thing on the grey bar, like "JSON" or "Top Level"
        # this also seems to have a "non breaking backspace" at the end....strip it off
        className = str(soup.find(lambda tag: tag.name == "convert" 
            and tag.parent is not None
            and tag.parent.has_attr("id")
            and tag.parent["id"] == "subTitle").string).strip().replace(" ", "") # remove excess whitespace

        # NOTE: uncomment if we want to make this use the full qualified classname as the pageName.
        # get the name of the package this class belongs in
        #packageName = str(soup.find(lambda tag: tag.name == "a"
        #    and tag.has_attr("id")
        #    and tag["id"] == "packageName").string).strip()

        # NOTE: uncomment if we want to make this use the full qualified classname as the pageName.
        # page name is the package name + class name
        #pageName = packageName + "." + className
        pageName = className

        # here, we test to see if this is a package html page. 
        if os.path.basename(pageLink) == "package-detail.html":

            # note that the anchor can be either "classSummary" or "interfaceSummary", so since it can 
            # have one or both, then we just don't provide an anchor.
            # add tuple to the list. tuple is of the format (refname, anchor)
            tokenList.append( ("//apple_ref/cpp/cat/{}".format(pageName), "") )

        else:

            # normal page, find props/styles/etc

            # **************************
            # type of page (class or interface)
            # **************************

            # adds the class or interface listing to our tokenList
            # note: we do not try and get the class type for all pages, thats why we have the check
            # to see if there is actually a tuple before we add it to tokenList. If its none then
            # its a weird page that isn't a class/interface (like package.html, operators.html)
            # so we don't add it
            tmpTuple = getClassTypeTupleFromClassSignature(soup, pageName)

            if tmpTuple:

                tokenList.append(tmpTuple)

            # **************************
            # properties
            # **************************

            # get the table tag 
            propertyTableTag = getTableTag("summaryTableProperty", soup)

            if propertyTableTag:
                # get the tag list
                propList = getTagListFormatOne(propertyTableTag, "a", "hideInheritedProperty")

                # add it to tokenlist
                tokenList.extend(getTokenAnchorTupleListFromATags(propList, "instp", pageName))
            
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
                tokenList.extend(getTokenAnchorTupleListFromATags(protPropList, "instp", pageName))


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
                tokenList.extend(getTokenAnchorTupleListFromATags(methodList, "clm", pageName))
                

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
                tokenList.extend(getTokenAnchorTupleListFromATags(protMethodList, "clm", pageName))


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
                tokenList.extend(getTokenAnchorTupleListFromATags(eventList, "binding", pageName))


            # **************************
            # styles
            # **************************

            # get tables tag ( three of them)
            styleTableTag = getTableTag(["summaryTablecommonStyle", "summaryTablesparkStyle", "summaryTablemobileStyle"], soup)

            # make sure we actually have styles
            if styleTableTag:

                # get as list, where we exclude all elements whose class is in our list
                # here get span tags cause classes that have styles as links inherited them and we dont want 
                # inherited stuff
                styleTwoList = getTagListFormatTwo(styleTableTag, "span", ["hideInheritedcommonStyle", "hideInheritedmobileStyle", "hideInheritedsparkStyle"])

                # add to token list. note these are span tags so we need a diff method
                # anchors are in style of "style:SomethingHere"
                tokenList.extend(getTokenAnchorTupleListFromSpanTags(styleTwoList, "instp", pageName, "style"))

            # **************************
            # skin parts
            # **************************

            # get table tag
            skinPartTableTag = getTableTag("summaryTableSkinPart", soup)

            # if we have skin parts:
            if skinPartTableTag:

                # get as list
                # here we only get span tags, cause the classes that have skin parts as links, have inherited the 
                # skin parts from another class and we don't want inherited props
                skinPartList = getTagListFormatTwo(skinPartTableTag, "span", "hideInheritedSkinPart")

                # add to list
                # anchor is in style of "SkinPart:SomethingHere"
                tokenList.extend(getTokenAnchorTupleListFromSpanTags(skinPartList, "instp", pageName, "SkinPart"))

            # **************************
            # skin states
            # **************************

            # get table tag
            skinStateTableTag = getTableTag("summaryTableSkinState", soup)

            # if we have skin states
            if skinStateTableTag:

                # get as list
                # here we only get span tags cause the classes that have skin states as links have inherited the 
                # skin states from another class and we don't want inherited stuff
                skinStateList = getTagListFormatTwo(skinStateTableTag, "span", "hideInheritedSkinState")

                # add to list
                # anchors are of the format "SkinState:SomethingHere"
                tokenList.extend(getTokenAnchorTupleListFromSpanTags(skinStateList, "instp", pageName, "SkinState"))


            # **************************
            # effects
            # **************************

            # get table tag
            effectTableTag = getTableTag("summaryTableEffect", soup)

            # if we have effects
            if effectTableTag:

                # get as list
                # here we only get span tags cause the classes that have effects as links have inherited the 
                # effect from another class and we don't want inherited stuff
                effectList = getTagListFormatTwo(effectTableTag, "span", "hideInheritedEffect")

                # add to list
                # anchors are of the format "effect:SomethingHere"
                tokenList.extend(getTokenAnchorTupleListFromSpanTags(effectList, "instp", pageName, "effect"))

            # **************************
            # constants
            # **************************

            # get table tag
            constTableTag = getTableTag("summaryTableConstant", soup)

            # if we have constants:
            if constTableTag:

                # get as list
                constList = getTagListFormatOne(constTableTag, "a", "hideInheritedConstant")

                # add to list
                tokenList.extend(getTokenAnchorTupleListFromATags(constList, "clconst", pageName))

        # now that we have gotten all of the tokens, we need to modify and save the html to the 
        # Documents folder within the docset we created
        # this is also where we add the anchor links for the Dash TOC (anchor links that have the appleref link 
        modifyAndSaveHtml(soup, os.path.join(documentsFolder, pageLink), tokenList)

    # now create the soup object that will be written to Tokens.xml
    # the format of this file is
    # <Tokens>
    #   <File>
    #       <Token>
    #           <TokenIdentifier>
    #           <Anchor>
    #   ... more <File> tags

    # bs4 object that will represent the xml file we are creating. 
    tokenSoup = BeautifulSoup('''<?xml version="1.0" encoding="UTF-8"?> 
    <Tokens version="1.0"></Tokens>''', "xml") # this requires bs4 beta 9 at least or else the xml declaration is bugged.

    # the tag that are adding <File> tags too
    soupTokensTag = tokenSoup.find("Tokens")

    # go through our pages dictionary
    for pageHref, tokenList in pages.items():

        # the file tag that will contain everything for this page
        fileTag = tokenSoup.new_tag("File", path=pageHref)

        # we seem to only write <file> tags if there are actually any tokens to write.
        for tmpTuple in tokenList:

            # Token tag that will hold the tokenidentifier and anchor tags
            iterToken = tokenSoup.new_tag("Token")

            # create the TokenIdentifier and Anchor tags
            idTag = tokenSoup.new_tag("TokenIdentifier")
            idTag.append(tmpTuple[0]) # the identifier
            iterToken.append(idTag)

            if tmpTuple[1] != "": # don't add an anchor for empty strings as anchors, they don't have one!
                anchorTag = tokenSoup.new_tag("Anchor")
                anchorTag.append(tmpTuple[1]) # the anchor
                iterToken.append(anchorTag)

            # add to file tag
            fileTag.append(iterToken)

        # add file tag to the Tokens tag only if we have tokens in our tokens list
        if len(tokenList) > 0:

            soupTokensTag.append(fileTag)


    # now we write to the tokens.xml file. 
    print("Creating {}".format(os.path.join(resourcesFolder, "Tokens.xml")))
    with open(os.path.join(resourcesFolder, "Tokens.xml"), "w", encoding="utf-8") as f:

        f.write(str(tokenSoup))


    if not args.noDocsetutil:
        # call apple's docset utility
        print("Calling docsetutil")
        resultCode = subprocess.call([docsetutilPath, "index", docsetFolder])


        # Cleanup the xml files as they are not needed anymore
        print("Cleaning up Nodes.xml and Tokens.xml")
        #os.remove(os.path.join(docsetFolder, "Contents", "Resources", "Nodes.xml"))
        #os.remove(os.path.join(docsetFolder, "Contents", "Resources", "Tokens.xml"))

    else:

        print("Creating the token files done. You still need to run 'docsetutil index as3.docset'" +
            " in order  for this to work with dash!")

    print("Done!")

if __name__ == "__main__":
    # if we are being run as a real program

    # the script does NOT seem to work if lxml is not installed
    # bs4 needs lxml or else it wont be able to find elements for 
    # some reason!
    try:
        import lxml
    except ImportError as e:

        trouble("lxml is not installed! the script does not seem to work without lxml, see www.lxml.de. Error: {}".format(e))

    parser = argparse.ArgumentParser(description="create a .docset file for the as3 documentation", 
        epilog="Copyright 2012 Mark Grandi, forked from https://github.com/gpambrozio/PythonScripts")

    parser.add_argument('docPath', help="the directory where the as3 documentation is located", type=verify_docpath)
    
    parser.add_argument('--outputPath', help="the directory to place the resulting .docset. defaults to os.getcwd()", type=verify_outputpath, default=os.getcwd())
    

    parser.add_argument("--noDocsetutil", action="store_true", default=False, help="Whether or not we should attempt to run docsetutil or not.")

    args = parser.parse_args()

    try:
        makeDocset(args)
    except Exception as e:

        trouble("problem making the docset: error was: {}".format(e))
