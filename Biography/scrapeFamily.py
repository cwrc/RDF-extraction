import requests
import sys, xml.etree.ElementTree, os, logging, csv, datetime
from bs4 import BeautifulSoup
# from Env import env

# from gLoggingInFunctions import *
from stringAndMemberFunctions import *
from classes import *

# from graphOntology import graphMaker
from birthDeath import getBirth, getDeath

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
def childrenCheck(xmlString, person):
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


def childlessnessCheck(xmlString,person):
    root = xmlString.BIOGRAPHY
    childrenTag = root.find_all('CHILDLESSNESS')
    childlessList = []
    # global numtags
    for tag in childrenTag:
        # ElemPrint(tag)
        
        if any(miscarriageWord in getOnlyText(tag) for miscarriageWord in 
            ["miscarriage","miscarriages","miscarried"]):
            childlessList.append(ChildlessStatus("miscarriage"))
        
        elif any(stillbirthWord in getOnlyText(tag) for stillbirthWord in 
            ["stillborn","still birth"]):
            childlessList.append(ChildlessStatus("stillbirth"))
            # one still birth
        
        elif any(abortionWord in getOnlyText(tag) for abortionWord in 
            ["abortion","aborted"]):
            childlessList.append(ChildlessStatus("abortion"))
            # no entries has this

        elif any(birthControlWord in getOnlyText(tag) for birthControlWord in 
            ["contraception"]):
            childlessList.append(ChildlessStatus("birth control"))
            # no entries has this
        
        elif any(veneralDisease in getOnlyText(tag) for veneralDisease in 
            ["syphilis","veneral","VD"]):
            childlessList.append(ChildlessStatus("venereal disease"))
            # 2 entries have this
        
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
def friendsAssociateCheck(xmlString,person):
    # root = xml.etree.ElementTree.fromstring(xmlString)
    root = xmlString.BIOGRAPHY

    tagToFind = allTagsAllChildren(root,"FRIENDSASSOCIATES")

    listToReturn = []

    for instance in tagToFind:
        listToReturn+=getContextsAndNames(instance,person.name)
        # foundNames, names = getAllNames(instance.iter("NAME"), sourcePerson)
        # if len(names) > 1:
        #     print(names)
        # friendContext = getContexts(instance)
        # if foundNames:
        #     # listToReturn += names
        #     listToReturn.append(PeopleAndContext(names, friendContext))
    # return listToReturn
    person.friendsAssociates_list = listToReturn
def cohabitantsCheck(xmlString,person):
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

def intimateRelationshipsCheck(xmlString,person):
    root = xmlString.BIOGRAPHY
    irTag = root.find_all('INTIMATERELATIONSHIPS')
    intimateRelationships = []
    sourcePerson = person.name
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
            # print(getOnlyText(person))
            intmtContextsAndNames = getContextsAndNames(thisPerson,sourcePerson)
            print(intmtContextsAndNames)
            for thisContext in intmtContextsAndNames:
                if len(thisContext.names) >= 1:
                    print("========>",thisContext.names[0])
                    intimateRelationships.append(IntimateRelationships(thisContext.names[0],attr,thisContext.contexts))
                else:
                    intimateRelationships.append(IntimateRelationships("intimate relationship",attr,thisContext.contexts))

            continue
            foundOtherName,otherNames = getNameOfAssociate(thisPerson.iter("NAME"), sourcePerson)
            print(thisPerson.findall("*"))
            intimateContexts += (getContexts(thisPerson))

            if foundOtherName:
                print("relationship with: ", otherNames)
                # for name in otherNames:
                #     personAttrList.append(PersonAttribute(attr,name))
                personAttrList.append(PersonAttribute(attr,otherNames))
            else:
                print("othername not found")
                personAttrList.append(PersonAttribute(attr, "intimate relationship"))
            # for name in person.iter("NAME"):
            #     print(name.attrib["STANDARD"])
            # getch()
    # intimateRelationships = IntimateRelationships(personAttrList,intimateContexts)

    person.intimateRelationships_list = intimateRelationships

# This function obtains family information
# ------ Example ------
# Name:  Grant, Josceline Charles Henry
# Relation:  FATHER
# Jobs: army officer
# SigAct: lost money, currency committee
def getFamilyInfo(xmlString,person):
    global numSigs
    global numAdded

    myRoot2 = xmlString.BIOGRAPHY
    # SOURCENAME = myRoot2.newFindFunc("DIV0 STANDARD").text
    SOURCENAME = findTag(myRoot2,"DIV0 STANDARD").text
    listOfMembers = []
    fams = myRoot2.find_all('FAMILY')
    for familyTag in myRoot2.find_all('FAMILY'):
        
        #--------------------------------- Get husband and wife ---------------------------------
        for familyMember in familyTag.find_all("MEMBER"):
            if familyMember['RELATION'] in ["HUSBAND","WIFE"]:
                if len(familyMember.find_all()) == 1:
                    continue
                else:
                    listOfMembers = getMemberInfo(familyMember,listOfMembers,SOURCENAME)

        #--------------------------------- get children ---------------------------------
        for familyMember in familyTag.find_all("MEMBER"):
            if familyMember['RELATION'] in ["SON","DAUGHTER","STEPSON","STEPDAUGHTER"]:
                if len(familyMember.find_all()) == 1:
                    continue
                else:
                    listOfMembers = getMemberChildInfo(familyMember,listOfMembers,SOURCENAME)
        
        #--------------------------------- get others ---------------------------------
        for familyMember in familyTag.find_all('MEMBER'):
            finds = familyMember.find_all()
            if familyMember['RELATION'] in ["HUSBAND","WIFE","SON","DAUGHTER","STEPSON","STEPDAUGHTER"] or len(iterListAll(familyMember)) == 1:
                continue
            else:
                listOfMembers = getMemberInfo(familyMember,listOfMembers,SOURCENAME)
    
    print("----------- ",SOURCENAME.strip(),"'s Family Members -----------")
    # printMemberInfo(listOfMembers)
    # print("")
    # return rearrangeSourceName(SOURCENAME),listOfMembers
    # return SOURCENAME,listOfMembers
    person.family_list = listOfMembers

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

    
