# this file simply holds functions for lifeInfo.py
from bs4 import BeautifulSoup
import sys
import logging
from classes import *
from stringAndMemberFunctions import *
import context
from event import get_date_tag
from place import Place


def extract_birth(xmlString, person):
    # filePath = os.path.expanduser("~/Downloads/laurma-b.xml")
    # getTreeRoot = xml.etree.ElementTree.parse(filePath)
    # treeRoot = getTreeRoot.getroot()
    # treeRoot = xml.etree.ElementTree.fromstring(xmlString)
    # treeRoot = BeautifulSoup(xmlString,'lxml-xml')
    treeRoot = xmlString
    # print(treeRoot.prettify())
    # BIRTH
    birthDate = ""
    birthplace = None
    birthPositions = []
    # print(treeRoot)
    birthTagParent = treeRoot.BIOGRAPHY.DIV0.BIRTH
    print("---------")
    try:
        birthTags = iterList(birthTagParent, ("CHRONSTRUCT"))
        # birthTags = list(birthTagParent.iter("CHRONSTRUCT"))

        if len(birthTags) == 0:
            # print(birthTagParent)
            birthTags = iterList(birthTagParent, ("SHORTPROSE"))
        if len(birthTags) == 0:
            print("no construct in birth found")
            sys.stdin.read(1)
            return

        birthTag = birthTags[0]
    except Exception as e:

        print(birthTagParent, birthTag, e)
        print("Construct from Birth not found")
        sys.stdin.read(1)
        return

    try:
        birthDateTag = get_date_tag(birthTag)
        if birthDateTag:
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
    birthPositionTags = birthTag.find_all('BIRTHPOSITION')
    for positions in birthPositionTags:
        if 'POSITION' in positions.attrs:
            birthPositions.append(positions['POSITION'])
    print("birth positions: {}".format(birthPositions))

    # Get birth place.
    # Where the subject is born
    birthPlaceTags = (birthTag.find_all('PLACE'))
    try:
        if len(birthPlaceTags) > 0:
            birthplace = Place(birthPlaceTags[0]).uri

            print("birth place: {}".format(birthplace))
        else:
            print("no birthPlaceTag")
            # sys.stdin.read(1)

    except AttributeError:
        print("no birth place information for this individual")
        # sys.stdin(1)
    person.birthObj = birthData(person.name, person.id, person.uri, birthDate, birthPositions, birthplace)
    getContextsFrom = tagChildren(birthTagParent)
    birthContexts = []

    id = 1
    for div in getContextsFrom:
        # birthContexts += getContexts(div)
        context_id = person.id + "_BirthContext_" + str(id)
        tempContext = context.Context(context_id, div, 'BIRTH')
        tempContext.link_triples(person.birthObj.birth_list)
        person.context_list.append(tempContext)

    # if "DIV" not in getContextsFrom[0].name:
    #     DIV = Element('DIV')
    #     DIV.insert(0,getContextsFrom[0])
    #
    #     # DIV.append(getContextsFrom)
    #     getContextsFrom = [DIV]
    # birthContexts = getContexts(getContextsFrom)


def extract_death(xmlString, person):
    # filePath = os.path.expanduser("~/Downloads/laurma-b.xml")
    # getTreeRoot = xml.etree.ElementTree.parse(filePath)
    # treeRoot = getTreeRoot.getroot()
    treeRoot = xmlString

    # DEATH
    deathDate = ""
    deathCauses = []
    deathContexts = []
    deathplace = None
    burialplace = None
    # deathTagParent = treeRoot.find("./DIV0/DIV1/DEATH/")
    # deathTagParent = treeRoot.BIOGRAPHY.DIV0.DEATH.find(recursive=False)
    deathTagParent = tagChild(findTag(treeRoot, "BIOGRAPHY DIV0 DIV1 DEATH"))
    # childrenOfDeathTag = tagChildren(deathTagParent)
    # print(deathTagParent.name)

    # DEATH DATE
    firstChronstructTag = ""
    deathDateTag = ""

    try:
        if deathTagParent is None:
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

        # print(deathTagParent.prettify())
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
            print(getChronstructTags)

            deathDateTags = get_date_tag(firstChronstructTag)

            if not deathDateTags:
                print("no date range either")
            else:
                # Found a date tag
                deathDateTag = deathDateTags
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
        deathplace = Place(deathPlaceTags[0]).uri
        # print("death place: {}, {}, {}".format(deathPlaceSettlement, deathPlaceRegion, deathPlaceGeog))

    else:
        allShortprose = firstChronstructTag.find_all('SHORTPROSE')
        # print(allShortprose)
        if len(allShortprose) > 0:
            for shortprose in allShortprose:
                for tags in shortprose.find_all('PLACE'):
                    deathplace = Place(tags).uri
        else:
            # chronstructParent = firstChronstructTag.find('./..')
            place = deathTagParent.find('PLACE')
            if place is None:
                print("no place found")
            if place is not None and len(place) > 0:
                print("found place")
                # deathPlaceSettlement, deathPlaceRegion, deathPlaceGeog = getPlaceTagContent(place)
                deathplace = Place(place).uri

    # place of burial
    # ElemPrint(deathTagParent)
    print(deathTagParent.name)
    burialTags = tagChildren(deathTagParent)
    print(len(burialTags))

    for i in range(0, len(burialTags)):
        if i == len(burialTags) - 1:
            continue
        # print(getOnlyText(burialTags[i+1].find(".//P")))
        if burialTags[i].name == "CHRONSTRUCT" and burialTags[i + 1].name == "SHORTPROSE" and burialTags[i + 1].find("PLACE") is not None:
            paragraph = getOnlyText(burialTags[i + 1].find("P"))

            if "buried" in paragraph or "grave" in paragraph or "interred" in paragraph:
                burialplace = Place(burialTags[i + 1].find("PLACE")).uri

            else:
                print("no buried in the paragraph")

    person.deathObj = deathData(person.name, person.id, person.uri, deathDate,
                                deathCauses, deathplace, deathContexts, burialplace)
    allDivs = allTagsAllChildren(treeRoot.BIOGRAPHY, "DIV0 DIV1 DEATH")
    # for div in allDivs:
    #     deathContexts += getContexts(div)
    id = 1
    for div in allDivs:
        # birthContexts += getContexts(div)
        context_id = person.id + "_DeathContext_" + str(id)
        tempContext = context.Context(context_id, div, 'DEATH')
        tempContext.link_triples(person.deathObj.death_list)
        person.context_list.append(tempContext)
