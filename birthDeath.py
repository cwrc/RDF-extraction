# this file simply holds functions for scrapeFamily.py
import xml.etree.ElementTree

import os
import sys
import logging
import copy
from classes import *
from stringAndMemberFunctions import *



def getBirth(xmlString):

    # filePath = os.path.expanduser("~/Downloads/laurma-b.xml")
    # getTreeRoot = xml.etree.ElementTree.parse(filePath)
    # treeRoot = getTreeRoot.getroot()
    treeRoot = xml.etree.ElementTree.fromstring(xmlString)

    # BIRTH
    birthDate = ""
    birthPlaceSettlement = ""
    birthPlaceRegion = ""
    birthPlaceGeog = ""
    birthPositions = []

    birthTagParent = treeRoot.find("./DIV0/DIV1/BIRTH")

    try:
        birthTags = list(birthTagParent.iter("CHRONSTRUCT"))
        
        if len(birthTags) == 0:
            print(birthTagParent)
            birthTags = list(birthTagParent.iter("SHORTPROSE"))
        if len(birthTags) == 0:
            print("no construct in birth found")
            sys.stdin.read(1)
            return

        birthTag = birthTags[0]
    except Exception as e:

        print(birthTagParent, birthTag,e)
        print("Construct from Birth not found")
        sys.stdin.read(1)
        return

    try:
        # Get birth date
        birthDateTags = list(birthTag.iter('DATE'))
        if len(birthDateTags) == 0:
            
            # If no 'DATE' tag, try 'DATERANGE' tag
            birthDateTags = list(birthTag.iter('DATERANGE'))
        if len(birthDateTags) == 0:
            
            # If no 'DATERANGE' tag, try 'DATESTRUCT' tag
            birthDateTags = list(birthTag.iter('DATESTRUCT'))

        birthDateTag = birthDateTags[0]

        if 'VALUE' in birthDateTag.attrib:
            birthDate = birthDateTag.attrib['VALUE']
        elif 'CERTAINTY' in birthDateTag.attrib and 'FROM' in birthDateTag.attrib and 'TO' in birthDateTag.attrib:
            # Sometimes the birth date isn't exact so a range is used
            birthDate = birthDateTag.attrib['FROM'] + " to " + birthDateTag.attrib['TO']
        
        print("---------Information about person--------------")
        print("birth date: ", birthDate)
    
    except Exception as e:
        print("&&&& Birth Date error &&&&")
        print("error: ", e)
        sys.stdin.read(1)
        return
    
    # Get birth positions
    # Ex. 'Oldest', 'Youngest'
    birthPositionTags = list(birthTag.iter('BIRTHPOSITION'))
    for positions in birthPositionTags:
        if 'POSITION' in positions.attrib:
            birthPositions.append(positions.attrib['POSITION'])
    print("birth positions: {}".format(birthPositions))
    
    # Get birth place.
    # Where the subject is born
    birthPlaceTags = list(birthTag.iter('PLACE'))
    birthPlaceTag = ""
    try:
        if len(birthPlaceTags) > 0:
            birthPlaceTag = birthPlaceTags[0]
            # get settlement, region, geog
            # Current refers to a place where the name has changed.
            # i.e. Today it is known as something else but during this
            # subject's time, the name was different
            birthPlaceSettlement, birthPlaceRegion, birthPlaceGeog = getPlaceTagContent(birthPlaceTag)


            print("birth place: {}, {}, {}".format(birthPlaceSettlement,birthPlaceRegion,birthPlaceGeog))
        else:
            print("no birthPlaceTag")
            # sys.stdin.read(1)

    except AttributeError:
        print("no birth place information for this individual")
        # sys.stdin(1)
    getContextsFrom = birthTagParent.findall("*")
    birthContexts = []
    for div in getContextsFrom:
        birthContexts += getContexts(div)
    # if "DIV" not in getContextsFrom[0].tag:
    #     DIV = Element('DIV')
    #     DIV.insert(0,getContextsFrom[0])
    #
    #     # DIV.append(getContextsFrom)
    #     getContextsFrom = [DIV]
    # birthContexts = getContexts(getContextsFrom)
    return birthData(birthDate, birthPositions, birthPlaceSettlement, birthPlaceRegion, birthPlaceGeog,birthContexts)

    
def getDeath(xmlString):

    # filePath = os.path.expanduser("~/Downloads/laurma-b.xml")
    # getTreeRoot = xml.etree.ElementTree.parse(filePath)
    # treeRoot = getTreeRoot.getroot()
    treeRoot = xml.etree.ElementTree.fromstring(xmlString)

    # DEATH
    deathDate = ""
    deathPlaceSettlement = ""
    deathPlaceRegion = ""
    deathPlaceGeog = ""
    burialPlaceSettlement = ""
    burialPlaceRegion = ""
    burialPlaceGeog = ""
    deathCauses = []
    deathContexts = []

    deathTagParent = treeRoot.find("./DIV0/DIV1/DEATH/")
    
    
    # DEATH DATE
    firstChronstructTag = ""
    deathDateTag = ""
    
    try:
        if deathTagParent == None:
            # Death tag not found
            deathTagParent = treeRoot.find(".//DEATH/")
            if deathTagParent is not None:
                print("used to be none but found death")
                sys.stdin.read(1)
            else:
                # Still no death tag found
                print("still no death tag found")
                # sys.stdin.read(1)
                return

        for div in treeRoot.findall("./DIV0/DIV1/DEATH/"):
            deathContexts += getContexts(div)
        if type(deathContexts) is list:
            print(deathContexts)
            print("this is a list")
        # getContextsFrom = [deathTagParent]
        # if "DIV" not in getContextsFrom[0].tag:
        #     DIV = Element('DIV')
        #     DIV.insert(0, getContextsFrom[0])
        #
        #     # DIV.append(getContextsFrom)
        #     getContextsFrom = [DIV]
        # deathContexts = getContexts(getContextsFrom)

        # deathParagraphs = list(deathTagParent.iter("P"))
        # if deathParagraphs != None and len(deathParagraphs) > 0:
        #     for para in list(deathTagParent.iter("P")):
        #
        #         # gets all text in paragraph. creates element iterator
        #         paraText = para.itertext()
        #         # the paragraph will be saved as a string in variable below
        #         paragraph = ""
        #
        #         for text in paraText:
        #             paragraph = paragraph + " " + text.strip()
        #         paragraph = paragraph.strip()
        #         print(paragraph)
        #         deathContexts.append(paragraph)
                # print(paragraph)
        getChronstructTags = list(deathTagParent.iter("CHRONSTRUCT"))
        
        if len(getChronstructTags) == 0:
            # No chronstruct tag found. Look for a shortprose tag
            getChronstructTags = list(deathTagParent.iter("SHORTPROSE"))

        if len(getChronstructTags) == 0:
            # No shortprose tag found either
            print("no SHORTPROSE in death found")
            sys.stdin.read(1)
            return

        if len(getChronstructTags) > 0:
            # A tag is found. Either a chronstruct or a shortprose
            firstChronstructTag = getChronstructTags[0]
            
            # Iterate through date tags
            deathDateTags = list(firstChronstructTag.iter('DATE'))
            
            if len(deathDateTags) == 0:
                
                # No date tag found, look for a datestruct tag
                print("no date found in construct. trying datestruct")
                deathDateTags = list(firstChronstructTag.iter('DATESTRUCT'))
            if len(deathDateTags) == 0:
                
                # No datestruct tag found, look for a daterange tag
                print("no datestruct. trying dateRange")
                deathDateTags = list(firstChronstructTag.iter('DATERANGE'))
            if len(deathDateTags) == 0:
                
                # No daterange tag found either
                print("no date range either")
                # sys.stdin.read(1)
            else:
                # Found a date tag
                deathDateTag = deathDateTags[0]
                if 'VALUE' in deathDateTag.attrib:
                    deathDate = deathDateTag.attrib['VALUE']
                elif 'CERTAINTY' in deathDateTag.attrib and 'FROM' in deathDateTag.attrib and 'TO' in deathDateTag.attrib:
                    deathDate = deathDateTag.attrib['FROM'] + " to " + deathDateTag.attrib['TO']
            

    except (AttributeError) as e:
        print("Death information not found. person probably still alive")
        # print("error: ", e)
        logging.exception(e)
        sys.stdin.read(1)
        return

    except NameError as e:
        print("Name Error")
        print("error: ", e)
        sys.stdin.read(1)
        return

    print("\ndeath date: ", deathDate)

    # CAUSE OF DEATH
    deathCauseTags = (firstChronstructTag.findall('CHRONPROSE/CAUSE'))
    if len(deathCauseTags) > 0:
        for causes in deathCauseTags:
            if "REG" in causes.attrib:
                deathCauses.append(causes.attrib['REG'])
            else:
                deathCauses.append(causes.text)
        
        print("death causes: {}".format(deathCauses))          

    # PLACE OF DEATH
    deathPlaceTags = (firstChronstructTag.findall('CHRONPROSE/PLACE'))
    if len(deathPlaceTags) > 0:
        deathPlaceSettlement,deathPlaceRegion,deathPlaceGeog = getPlaceTagContent(deathPlaceTags[0])
    
        print("death place: {}, {}, {}".format(deathPlaceSettlement,deathPlaceRegion,deathPlaceGeog))

    else:
        allShortprose = firstChronstructTag.findall('SHORTPROSE')
        # print(allShortprose)
        if len(allShortprose) > 0:
            for shortprose in allShortprose:
                for tags in shortprose.iter('PLACE'):
                    for placeInfo in tags.iter():
                        if placeInfo.tag == "SETTLEMENT":
                            deathPlaceSettlement = placeInfo.text
                        elif placeInfo.tag == "REGION":
                            try:
                                deathPlaceRegion = placeInfo.attrib['REG']
                            except KeyError:
                                deathPlaceRegion = placeInfo.text
                        elif placeInfo.tag == "GEOG":
                            try:
                                deathPlaceGeog = placeInfo.attrib['REG']
                            except KeyError:
                                deathPlaceGeog = placeInfo.text
                        # fix: some place tags don't have all of the above
                        if deathPlaceSettlement != "" and deathPlaceRegion != "" and deathPlaceGeog != "":
                            print("other death info: {}, {}, {}".format(deathPlaceSettlement,deathPlaceRegion,deathPlaceGeog))
                            deathPlaceSettlement = ""
                            deathPlaceRegion = ""
                            deathPlaceGeog = ""
        else:
            # chronstructParent = firstChronstructTag.find('./..')
            place = deathTagParent.find('.//PLACE')
            if place == None:
                print("no place found")
            if place is not None and len(place) > 0:
                print("found place")
                deathPlaceSettlement,deathPlaceRegion,deathPlaceGeog = getPlaceTagContent(place)


    # place of burial
    # ElemPrint(deathTagParent)
    burialTags = deathTagParent.findall("*")
    print(len(burialTags))

    for i in range(0,len(burialTags)):
        if i == len(burialTags)-1:
            continue
        # print(getOnlyText(burialTags[i+1].find(".//P")))
        if burialTags[i].tag == "CHRONSTRUCT" and burialTags[i+1].tag == "SHORTPROSE" and burialTags[i+1].find(".//PLACE") is not None:
            paragraph = getOnlyText(burialTags[i+1].find(".//P"))

            if "buried" in paragraph or "grave" in paragraph or "interred" in paragraph:
                    burialPlaceSettlement,burialPlaceRegion,burialPlaceGeog = getPlaceTagContent(burialTags[i+1].find(".//PLACE"))
                    print(burialPlaceSettlement,burialPlaceRegion,burialPlaceGeog)

            else:
                print("no buried in the paragraph")

    return deathData(deathDate, deathCauses, deathPlaceSettlement, deathPlaceRegion, deathPlaceGeog, deathContexts,burialPlaceSettlement,burialPlaceRegion,burialPlaceGeog)