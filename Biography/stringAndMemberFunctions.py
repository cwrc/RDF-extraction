import datetime
import sys
import copy
# from scrapeFamily import *
from classes import *
from bs4 import BeautifulSoup
from place import Place


def getch():
    sys.stdin.read(1)

# used for getting divs
# equivalent of something like ".//FRIENDSASSOCIATES/"
# that would get all the divs in all of the friends tags


def allTagsAllChildren(base, tagToGet):
    if base == None:
        return None
    childrenToReturn = []
    allTags = base.select(tagToGet)
    for tag in allTags:
        childrenToReturn += tag.find_all(recursive=False)

    return childrenToReturn

# find tag that lets you specify a certain path


def findTag(base, tagPath):
    if base == None:
        return None
    instances = base.select(tagPath)
    if len(instances) == 0:
        return None
    else:
        return instances[0]

# get all the children tags


def tagChildren(base):
    if base == None:
        return None
    return base.find_all(recursive=False)

# get first child


def tagChild(base):
    if base == None:
        return None
    return base.find(recursive=False)

# iterate a certain tag in a list
# equivalent to elementtree's
# something.iter("something else")


def iterList(base, tagToGet):
    if base == None:
        return None
    returnList = []
    if base.name == tagToGet:
        # in elementtree, if the base is same as tag to get in the .iter() function. the base is also returned
        returnList.append(base)
    returnList += base.find_all(tagToGet)
    return returnList

# iterate all children and sub children, including the base tag itself

def iterListAll(base):
    if base == None:
        return None
    returnList = []
    returnList.append(base)
    returnList += base.find_all()
    return returnList


# gets the text from a tag. this includes the text of
# all the subtags


def getOnlyText(tag):
    unformattedText = tag.get_text()
    paraText = unformattedText.split()

    paragraph = ""
    for text in paraText:
        text = text.strip()
        if text[0] != ",":
            text = " " + text
        paragraph = paragraph.strip() + text
    paragraph = paragraph.strip()

    return paragraph


# when getting children's names, this makes sure
# we are not getting the parent's name


def notParentName(personName, parentList):
    print("welcome to not parent home")
    print("parent list: ", len(parentList))
    for parent in parentList:
        print("compare ", personName, " and ", parent.memberName)
        if parent.memberName == personName:
            return False
    return True

# get all names in a tag that are not the subject's


def getAllNames(names, sourcePerson):
    otherNames = []
    for thisName in names:
        name = thisName["STANDARD"]
        # print("looking at :", name)
        if name != sourcePerson:
            otherNames.append(name)

    return otherNames

# get a name of a person by getting the first
# name that is not the source person


def getNameOfAssociate(names, sourcePerson):
    foundName = False
    otherName = ""
    for thisName in names:
        name = thisName["STANDARD"]
        # print("looking at :", name)
        if name != sourcePerson:
            foundName = True
            otherName = (name)
            break

    return foundName, otherName




