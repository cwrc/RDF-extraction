import requests
import sys, xml.etree.ElementTree, os, logging, csv, datetime
from bs4 import BeautifulSoup
# from Env import env

from gLoggingInFunctions import *
from classes import *

from graphOntology import graphMaker
from birthDeath import getBirth, getDeath
from stringAndMemberFunctions import *

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
def childrenCheck(xmlString, sourceFile):
    root = xml.etree.ElementTree.fromstring(xmlString)
    childrenTag = root.findall('.//CHILDREN')
    childrenList = []

    for child in childrenTag:
        if "NUMBER" in child.attrib:
            print("contains number of child: ", child.attrib["NUMBER"])
            childType = "numberOfChildren"
            numChild = child.attrib["NUMBER"]
            
            childrenList.append(ChildStatus(childType,numChild))

    return childrenList


def childlessnessCheck(xmlString):
    root = xml.etree.ElementTree.fromstring(xmlString)
    childrenTag = root.findall('.//CHILDLESSNESS')
    childlessList = []
    # global numtags
    for tag in childrenTag:
        ElemPrint(tag)
        
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
        


    return childlessList

def friendsAssociateCheck(xmlString,tagName):
    root = xml.etree.ElementTree.fromstring(xmlString)
    sourcePerson = root.find("./DIV0/STANDARD").text

    tagToFind = root.findall(".//FRIENDSASSOCIATES/")

    listToReturn = []

    for instance in tagToFind:
        listToReturn+=getContextsAndNames(instance,sourcePerson)
        # foundNames, names = getAllNames(instance.iter("NAME"), sourcePerson)
        # if len(names) > 1:
        #     print(names)
        # friendContext = getContexts(instance)
        # if foundNames:
        #     # listToReturn += names
        #     listToReturn.append(PeopleAndContext(names, friendContext))
    return listToReturn

def cohabitantsCheck(xmlString,tagName):
    root = xml.etree.ElementTree.fromstring(xmlString)
    sourcePerson = root.find("./DIV0/STANDARD").text

    tagToFind = root.findall(".//" + tagName)

    listToReturn = []

    for instance in tagToFind:
        names = getAllNames(instance.iter("NAME"), sourcePerson)
        if names is not None:
            listToReturn += names

    return listToReturn

def getSexualityContexts(xmlString):
    root = xml.etree.ElementTree.fromstring(xmlString)
    sourcePerson = root.find("./DIV0/STANDARD").text
    tagToFind = root.findall(".//SEXUALITY/")
    print(tagToFind)
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
def intimateRelationshipsCheck(xmlString):
    root = xml.etree.ElementTree.fromstring(xmlString)
    irTag = root.findall('.//INTIMATERELATIONSHIPS')
    sourcePerson = root.find("./DIV0/STANDARD").text
    personAttrList = []
    intimateContexts = []
    intimateRelationships = []
    for tag in irTag:
        attr = ""
        
        if "EROTIC" in tag.attrib:
            attr = tag.attrib["EROTIC"]
            # print("attr: ", tag.attrib["EROTIC"])
        else:
            attr = "nonErotic"
        
        for person in tag.iter("DIV2"):
            print("======person======")
            print("source: ", sourcePerson)
            # print(getOnlyText(person))
            intmtContextsAndNames = getContextsAndNames(person,sourcePerson)
            print(intmtContextsAndNames)
            for thisContext in intmtContextsAndNames:
                if len(thisContext.names) >= 1:
                    intimateRelationships.append(IntimateRelationships(thisContext.names[0],attr,thisContext.contexts))
                else:
                    intimateRelationships.append(IntimateRelationships("intimate relationship",attr,thisContext.contexts))

            continue
            foundOtherName,otherNames = getNameOfAssociate(person.iter("NAME"), sourcePerson)
            print(person.findall("*"))
            intimateContexts += (getContexts(person))

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

    return intimateRelationships

# This function obtains family information
# ------ Example ------
# Name:  Grant, Josceline Charles Henry
# Relation:  FATHER
# Jobs: army officer
# SigAct: lost money, currency committee
def getFamilyInfo(xmlString, sourceFile):
    global numSigs
    global numAdded

    myRoot2 = xml.etree.ElementTree.fromstring(xmlString)
    SOURCENAME = myRoot2.find("./DIV0/STANDARD").text
    listOfMembers = []
    fams = myRoot2.findall('.//FAMILY')
    for familyTag in myRoot2.findall('.//FAMILY'):
        
        #--------------------------------- Get husband and wife ---------------------------------
        for familyMember in familyTag.findall("MEMBER"):
            print(familyMember.attrib["RELATION"])
            if familyMember.attrib['RELATION'] in ["HUSBAND","WIFE"]:
                if len(list(familyMember.iter())) == 1:
                    continue
                else:
                    listOfMembers = getMemberInfo(familyMember,listOfMembers,SOURCENAME)

        #--------------------------------- get children ---------------------------------
        for familyMember in familyTag.findall("MEMBER"):
            print(familyMember.attrib["RELATION"])
            if familyMember.attrib['RELATION'] in ["SON","DAUGHTER","STEPSON","STEPDAUGHTER"]:
                if len(list(familyMember.iter())) == 1:
                    continue
                else:
                    listOfMembers = getMemberChildInfo(familyMember,listOfMembers,SOURCENAME)
        
        #--------------------------------- get others ---------------------------------
        for familyMember in familyTag.findall('MEMBER'):
            print(familyMember.attrib["RELATION"])
            if familyMember.attrib['RELATION'] in ["HUSBAND","WIFE","SON","DAUGHTER","STEPSON","STEPDAUGHTER"] or len(list(familyMember.iter())) == 1:
                continue
            else:
                listOfMembers = getMemberInfo(familyMember,listOfMembers,SOURCENAME)
    
    print("----------- ",SOURCENAME.strip(),"'s Family Members -----------")
    # printMemberInfo(listOfMembers)
    # print("")
    # return rearrangeSourceName(SOURCENAME),listOfMembers
    return SOURCENAME,listOfMembers

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

def main():
    bioFolder = os.path.expanduser("~/Documents/UoGuelph Projects/biography/")
    numBiographiesRead = 0
    printInfo = True
    numTriples = 0
    numNamelessPeople = 0
    occupations = getOccupationDict()
    f = open("namesAndTriples.txt","w")
    cntr = -1
    for dirName, subdirlist, files in os.walk(bioFolder):
        for name in files:
            cntr += 1
            # if cntr == 3:
            #     break
            # if "lee_ve-b.xml" not in name:
            #     continue
            # if "dempch-b.xml" not in name:
            #     continue
            # if "larkph-b.xml" not in name:
            #     continue
            if "fielmi-b.xml" not in name:
                continue
            # if "pounez-b.xml" not in name:
            #     continue

            if printInfo == True:
                print('\n===========%s=================' % name)

                openFile = open(bioFolder+name,"r",encoding="utf-8")
                xmlString = openFile.read()
                numBiographiesRead += 1

                birthInfo                   = getBirth(xmlString)
                deathInfo                   = getDeath(xmlString)
                cohabitantList              = cohabitantsCheck(xmlString, "LIVESWITH")
                sourceName,familyMembers    = getFamilyInfo(xmlString,os.path.expanduser("\""+bioFolder+name+"\""))
                friendAssociateList         = friendsAssociateCheck(xmlString, "FRIENDSASSOCIATES")
                intimateRelationshipsList   = intimateRelationshipsCheck(xmlString)
                childlessList               = childlessnessCheck(xmlString)
                childInfo                   = childrenCheck(xmlString,os.path.expanduser("\""+bioFolder+name+"\""))
                sexualityContext            = getSexualityContexts(xmlString)
                numGraphTriples,numNameless = graphMaker(rearrangeSourceName(sourceName),name[0:-6],sourceName,familyMembers,birthInfo,
                                                         deathInfo,childInfo,childlessList,intimateRelationshipsList,friendAssociateList,
                                                         occupations,cohabitantList,sexualityContext,cntr)
                # if deathInfo != None and deathInfo.deathContexts != None:
                #     f.write("%s:%d\n"%(name,len(deathInfo.deathContexts)))
                # else:
                #     f.write("%s:%d\n" % (name, 0))
                f.write("%s:%d\n" % (name, numGraphTriples))
                numTriples += numGraphTriples
                numNamelessPeople += numNameless
    f.close()
    print(numSigs, " number of significant activities found")
    print(numAdded, " number of significant activities added")
    print("number of triples: ", numTriples)
    print("number of biographies: ", numBiographiesRead)
    print("number of nameless: ", numNamelessPeople)

if __name__ == "__main__":
    # startLogin()
    main()
    
