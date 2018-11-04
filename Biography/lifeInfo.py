import requests
import sys, xml.etree.ElementTree, os, logging, csv, datetime
from bs4 import BeautifulSoup
# from Env import env

# from gLoggingInFunctions import *
from stringAndMemberFunctions import *
from classes import *
import context
# from graphOntology import graphMaker
from birthDeath import extract_birth, extract_death

numSigs = 0
numAdded = 0
session = requests.Session()
numtags = 0


# Get g information about the subject
# ------ Example ------
# birth date:  1873-12-07
# birth positions: ['ELDEST']
# birth place: Gore, Virginia, USA

    # o


# checks if child's name is available in children tag
def extract_children(xmlString, person):
    root = xmlString.BIOGRAPHY
    childrenTag = root.find_all('CHILDREN')
    childrenList = []

    for child in childrenTag:
        if "NUMBER" in child.attrs:
            print("contains number of child: ", child["NUMBER"])
            childType = "numberOfChildren"
            numChild = child["NUMBER"]
            
            childrenList.append(ChildStatus(childType,numChild))

    person.children_list = childrenList


def extract_childlessness(xmlString, person):
    root = xmlString.BIOGRAPHY
    childrenTag = root.find_all('CHILDLESSNESS')
    childlessList = []
    # global numtags
    for tag in childrenTag:
        # ElemPrint(tag)
        
        # if any(miscarriageWord in getOnlyText(tag) for miscarriageWord in
        #     ["miscarriage","miscarriages","miscarried"]):
        #     childlessList.append(ChildlessStatus("miscarriage"))
        #
        # elif any(stillbirthWord in getOnlyText(tag) for stillbirthWord in
        #     ["stillborn","still birth"]):
        #     childlessList.append(ChildlessStatus("stillbirth"))
        #     # one still birth
        #
        # elif any(abortionWord in getOnlyText(tag) for abortionWord in
        #     ["abortion","aborted"]):
        #     childlessList.append(ChildlessStatus("abortion"))
        #     # no entries has this

        if any(birthControlWord in getOnlyText(tag) for birthControlWord in
            ["contraception"]):
            childlessList.append(ChildlessStatus("birth control"))
            # no entries has this
        
        # elif any(veneralDisease in getOnlyText(tag) for veneralDisease in
        #     ["syphilis","veneral","VD"]):
        #     childlessList.append(ChildlessStatus("venereal disease"))
        #     # 2 entries have this

        elif any(adoptionWord in getOnlyText(tag) for adoptionWord in
            ["adopted","adoption"]):
            childlessList.append(ChildlessStatus("adoption"))
            # 8 entries have this
        
        elif any(childlessWord in getOnlyText(tag) for childlessWord in 
            ["childless","no children","no surviving children"]):
            childlessList.append(ChildlessStatus("childlessness"))
            # 131 entries have this

        else:
            childlessList.append(ChildlessStatus("childlessness"))
            # numtags += 1
            # 69 entries
        
        print("------------")
        


    # return childlessList
    person.childless_list = childlessList
def extract_friends_associates(xmlString, person):
    # root = xml.etree.ElementTree.fromstring(xmlString)
    root = xmlString.BIOGRAPHY

    tagToFind = allTagsAllChildren(root,"FRIENDSASSOCIATES")

    listToReturn = []
    id = 1
    for instance in tagToFind:
        context_id = person.id + "_FriendAndAssociatesContext_" + str(id)
        id += 1
        thisInstanceNames = getAllNames(instance.find_all("NAME"), person.name)
        thisInstanceObjs = []

        for name in thisInstanceNames:
            thisInstanceObjs.append(FriendAssociate(name))
        tempContext = context.Context(context_id, instance, "FRIENDSASSOCIATES")
        tempContext.link_triples(thisInstanceObjs)
        person.context_list.append(tempContext)
        listToReturn += thisInstanceObjs

    person.friendsAssociates_list = listToReturn
def extract_cohabitants(xmlString, person):
    # root = xml.etree.ElementTree.fromstring(xmlString)
    root = xmlString.BIOGRAPHY
    sourcePerson = findTag(root,"DIV0 STANDARD").text
    tagToFind = root.find_all("LIVESWITH")

    listToReturn = []

    for instance in tagToFind:
        names = getAllNames(instance.find_all("NAME"), sourcePerson)
        for name in names:
            listToReturn.append(Cohabitant(name))

    person.cohabitants_list =  listToReturn

def getSexualityContexts(xmlString):
    # root = xml.etree.ElementTree.fromstring(xmlString)
    root = xmlString.BIOGRAPHY
    tagToFind = allTagsAllChildren(root,"SEXUALITY")
    # tagToFind = root.find_all("SEXUALITY").find_all(recursive=False)
    listToReturn = []

    for div in tagToFind:
        # print(div.findall("*"))
        sexualityContext = getContexts(div)
        listToReturn += sexualityContext
    print(listToReturn)
#    ================================================
#     root = BeautifulSoup(xmlString,'lxml')
#     print(root)
    return listToReturn

def extract_intimate_relationships(xmlString, person):
    root = xmlString.BIOGRAPHY
    irTag = root.find_all('INTIMATERELATIONSHIPS')
    intimateRelationships = []
    sourcePerson = person.name
    id = 1
    for tag in irTag:
        attr = ""

        if "EROTIC" in tag.attrs:
            attr = tag["EROTIC"]
            # print("attr: ", tag.attrib["EROTIC"])
        else:
            attr = "nonErotic"
        for thisPerson in tag.find_all("DIV2"):
            print("======person======")
            print("source: ", sourcePerson)

            context_id = person.id + "_IntimateRelationshipsContext_" + str(id)
            id += 1
            names = getAllNames(thisPerson.find_all("NAME"),person.name)
            if len(names) >= 1:
                print("========>", names[0])
                thisRelationship = IntimateRelationships(names[0], attr)
            else:
                thisRelationship = IntimateRelationships("intimate relationship", attr)

            tempContext = context.Context(context_id,thisPerson,"INTIMATERELATIONSHIPS")
            tempContext.link_triples([thisRelationship])
            intimateRelationships.append(thisRelationship)
            person.context_list.append(tempContext)
            # for name in person.iter("NAME"):
            #     print(name.attrib["STANDARD"])
            # getch()
    # intimateRelationships = IntimateRelationships(personAttrList,intimateContexts)

    person.intimateRelationships_list = intimateRelationships



def getOccupationDict():
    listToReturn = {}
    with open(os.path.expanduser('~/Documents/UoGuelph Projects/occupation.csv'),encoding='utf8') as csvInput:
        csvReader = csv.reader(csvInput,delimiter=',')

        skipFirst = True
        for row in csvReader:
            if skipFirst:
                skipFirst = False
                continue
            if row[0] == "":
                continue
            # print(row)
            # print("to use: ", row[0])
            for j in range(3,len(row)):
                if row[j] != "":
                    listToReturn[row[j]] = row[0]
                    # print("alternative: ",row[j])
            # break
        # print(len(listToReturn))
    return listToReturn


    
