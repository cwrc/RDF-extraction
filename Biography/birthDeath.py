# this file simply holds functions for scrapeFamily.py
import xml.etree.ElementTree
from bs4 import BeautifulSoup
import os
import sys
import logging
import copy
from classes import *
from stringAndMemberFunctions import *
import context


def getBirth(xmlString,person):
    # filePath = os.path.expanduser("~/Downloads/laurma-b.xml")
    # getTreeRoot = xml.etree.ElementTree.parse(filePath)
    # treeRoot = getTreeRoot.getroot()
    # treeRoot = xml.etree.ElementTree.fromstring(xmlString)
    # treeRoot = BeautifulSoup(xmlString,'lxml-xml')
    treeRoot = xmlString
    # print(treeRoot.prettify())
    # BIRTH
    birthDate = ""
    birthPlaceSettlement = ""
    birthPlaceRegion = ""
    birthPlaceGeog = ""
    birthPositions = []
    # print(treeRoot)
    birthTagParent = treeRoot.BIOGRAPHY.DIV0.BIRTH
    print("---------")
    try:
        birthTags = iterList(birthTagParent,("CHRONSTRUCT"))
        # birthTags = list(birthTagParent.iter("CHRONSTRUCT"))
        
        if len(birthTags) == 0:
            # print(birthTagParent)
            birthTags = iterList(birthTagParent,("SHORTPROSE"))
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
        birthDateTags = (birthTag.find_all('DATE'))
        if len(birthDateTags) == 0:
            
            # If no 'DATE' tag, try 'DATERANGE' tag
            birthDateTags = (birthTag.find_all('DATERANGE'))
        if len(birthDateTags) == 0:
            
            # If no 'DATERANGE' tag, try 'DATESTRUCT' tag
            birthDateTags = (birthTag.find_all('DATESTRUCT'))

        birthDateTag = birthDateTags[0]

        if 'VALUE' in birthDateTag.attrs:
            birthDate = birthDateTag['VALUE']
        elif 'CERTAINTY' in birthDateTag.attrs and 'FROM' in birthDateTag.attrs and 'TO' in birthDateTag.attrs:
            # Sometimes the birth date isn't exact so a range is used
            birthDate = birthDateTag['FROM'] + " to " + birthDateTag['TO']
        
        print("---------Information about person--------------")
        print("birth date: ", birthDate)
    
    except Exception as e:
        print("&&&& Birth Date error &&&&")
        print("error: ", e)
        sys.stdin.read(1)
        return
    
    # Get birth positions
    # Ex. 'Oldest', 'Youngest'
    birthPositionTags = (birthTag.find_all('BIRTHPOSITION'))
    for positions in birthPositionTags:
        if 'POSITION' in positions.attrs:
            birthPositions.append(positions['POSITION'])
    print("birth positions: {}".format(birthPositions))
    
    # Get birth place.
    # Where the subject is born
    birthPlaceTags = (birthTag.find_all('PLACE'))
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
    person.birth = birthData(person.name,person.id,person.uri,birthDate, birthPositions, birthPlaceSettlement, birthPlaceRegion, birthPlaceGeog)
    getContextsFrom = tagChildren(birthTagParent)
    birthContexts = []

    id = 1
    for div in getContextsFrom:
        # birthContexts += getContexts(div)
        context_id  = person.id + "_BirthContext_" + str(id)
        tempContext = context.Context(context_id,div,'BIRTH')
        # tempContext.link_triples([person.birth])
        person.context_list.append(tempContext)

    # if "DIV" not in getContextsFrom[0].name:
    #     DIV = Element('DIV')
    #     DIV.insert(0,getContextsFrom[0])
    #
    #     # DIV.append(getContextsFrom)
    #     getContextsFrom = [DIV]
    # birthContexts = getContexts(getContextsFrom)

    
def getDeath(xmlString,person):

    # filePath = os.path.expanduser("~/Downloads/laurma-b.xml")
    # getTreeRoot = xml.etree.ElementTree.parse(filePath)
    # treeRoot = getTreeRoot.getroot()
    treeRoot = xmlString

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

    # deathTagParent = treeRoot.find("./DIV0/DIV1/DEATH/")
    # deathTagParent = treeRoot.BIOGRAPHY.DIV0.DEATH.find(recursive=False)
    deathTagParent = tagChild(findTag(treeRoot,"BIOGRAPHY DIV0 DIV1 DEATH"))
    # childrenOfDeathTag = tagChildren(deathTagParent)
    # print(deathTagParent.name)
    
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

        # allDeathDivs = treeRoot.BIOGRAPHY.select("DIV0 DIV1 DEATH")
        # allDivs = []
        # for deathTag in allDeathDivs:
        #     allDivs += tagChildren(deathTag)
            # div.find_all(recursive=False)
        allDivs = allTagsAllChildren(treeRoot.BIOGRAPHY,"DIV0 DIV1 DEATH")
        for div in allDivs:
            deathContexts += getContexts(div)
        # if type(deathContexts) is list:
        #     print(deathContexts)
        #     print("this is a list")
        # getContextsFrom = [deathTagParent]
        # if "DIV" not in getContextsFrom[0].name:
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
        # print(deathTagParent.contents)
        print(deathTagParent.prettify())
        getChronstructTags = iterList(deathTagParent,"CHRONSTRUCT")
        
        if len(getChronstructTags) == 0:
            # No chronstruct tag found. Look for a shortprose tag
            getChronstructTags = (deathTagParent.find_all("SHORTPROSE"))

        if len(getChronstructTags) == 0:
            # No shortprose tag found either
            print("no SHORTPROSE in death found")
            sys.stdin.read(1)
            return

        if len(getChronstructTags) > 0:
            # A tag is found. Either a chronstruct or a shortprose
            firstChronstructTag = getChronstructTags[0]
            
            # Iterate through date tags
            deathDateTags = iterList(firstChronstructTag,'DATE')
            
            if len(deathDateTags) == 0:
                
                # No date tag found, look for a datestruct tag
                print("no date found in construct. trying datestruct")
                deathDateTags = iterList(firstChronstructTag,('DATESTRUCT'))
            if len(deathDateTags) == 0:
                
                # No datestruct tag found, look for a daterange tag
                print("no datestruct. trying dateRange")
                deathDateTags = iterList(firstChronstructTag,('DATERANGE'))
            if len(deathDateTags) == 0:
                
                # No daterange tag found either
                print("no date range either")
                # sys.stdin.read(1)
            else:
                # Found a date tag
                deathDateTag = deathDateTags[0]
                if 'VALUE' in deathDateTag.attrs:
                    deathDate = deathDateTag['VALUE']
                elif 'CERTAINTY' in deathDateTag.attrs and 'FROM' in deathDateTag.attrs and 'TO' in deathDateTag.attrs:
                    deathDate = deathDateTag['FROM'] + " to " + deathDateTag['TO']
            

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
    deathCauseTags = (firstChronstructTag.select('CHRONPROSE CAUSE'))
    if len(deathCauseTags) > 0:
        for causes in deathCauseTags:
            if "REG" in causes.attrs:
                deathCauses.append(causes['REG'])
            else:
                deathCauses.append(causes.text)
        
        print("death causes: {}".format(deathCauses))          

    # PLACE OF DEATH
    deathPlaceTags = (firstChronstructTag.select('CHRONPROSE PLACE'))
    if len(deathPlaceTags) > 0:
        deathPlaceSettlement,deathPlaceRegion,deathPlaceGeog = getPlaceTagContent(deathPlaceTags[0])
    
        print("death place: {}, {}, {}".format(deathPlaceSettlement,deathPlaceRegion,deathPlaceGeog))

    else:
        allShortprose = firstChronstructTag.find_all('SHORTPROSE')
        # print(allShortprose)
        if len(allShortprose) > 0:
            for shortprose in allShortprose:
                for tags in shortprose.find_all('PLACE'):
                    for placeInfo in tags.find_all():
                        if placeInfo.name == "SETTLEMENT":
                            deathPlaceSettlement = placeInfo.text
                        elif placeInfo.name == "REGION":
                            try:
                                deathPlaceRegion = placeInfo['REG']
                            except KeyError:
                                deathPlaceRegion = placeInfo.text
                        elif placeInfo.name == "GEOG":
                            try:
                                deathPlaceGeog = placeInfo['REG']
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
            place = deathTagParent.find('PLACE')
            if place == None:
                print("no place found")
            if place is not None and len(place) > 0:
                print("found place")
                deathPlaceSettlement,deathPlaceRegion,deathPlaceGeog = getPlaceTagContent(place)


    # place of burial
    # ElemPrint(deathTagParent)
    print(deathTagParent.name)
    burialTags = tagChildren(deathTagParent)
    print(len(burialTags))

    for i in range(0,len(burialTags)):
        if i == len(burialTags)-1:
            continue
        # print(getOnlyText(burialTags[i+1].find(".//P")))
        if burialTags[i].name == "CHRONSTRUCT" and burialTags[i+1].name == "SHORTPROSE" and burialTags[i+1].find("PLACE") is not None:
            paragraph = getOnlyText(burialTags[i+1].find("P"))

            if "buried" in paragraph or "grave" in paragraph or "interred" in paragraph:
                    burialPlaceSettlement,burialPlaceRegion,burialPlaceGeog = getPlaceTagContent(burialTags[i+1].find("PLACE"))
                    print(burialPlaceSettlement,burialPlaceRegion,burialPlaceGeog)

            else:
                print("no buried in the paragraph")

    person.death =  deathData(person.name,person.id,person.uri,deathDate, deathCauses, deathPlaceSettlement, deathPlaceRegion, deathPlaceGeog, deathContexts,burialPlaceSettlement,burialPlaceRegion,burialPlaceGeog)