import requests
# import sys, xml.etree.ElementTree, os, logging, csv, datetime,
# from Env import env
import sys
from gLoggingInFunctions import *
from graphOntology import *
from birthDeath import *

from stringAndMemberFunctions import *

numSigs = 0
numAdded = 0
session = requests.Session()
numtags = 0



class ChildlessStatus:
    def __init__(self, label):
        self.Label = label

class ChildStatus:
    def __init__(self, childType,numChild):
        self.ChildType = childType
        self.NumChildren = numChild

class IntimateRelationships:
    def __init__(self, attrValue, name):
        self.AttrValue  = attrValue;
        self.PersonName = name;




# Get g information about the subject
# ------ Example ------
# birth date:  1873-12-07
# birth positions: ['ELDEST']
# birth place: Gore, Virginia, USA
def getch():
    sys.stdin.read(1)
    # o


# checks if child's name is available in children tag
def childrenCheck(xmlString, sourceFile):
    root = xml.etree.ElementTree.fromstring(xmlString)
    childrenTag = root.findall('.//CHILDREN')
    childType = ""

    for child in childrenTag:
        if "NUMBER" in child.attrib:
            print("contains number of child: ", child.attrib["NUMBER"])
            childType = "numberOfChildren"
            numChild = child.attrib["NUMBER"]
            
            return ChildStatus(childType,numChild)

    # if len(childlessTag) > 0 :
        
        
    # for child in myRoot2.findall(".//MEMBER[@RELATION='MOTHER']"):
    #     print("found MOTHER TAG")
    #     print(child.text)

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
        
        for child in childlessList:
            print(child.Label)

    return childlessList

def friendOrAssociateCheck(xmlString):
    root = xml.etree.ElementTree.fromstring(xmlString)
    fOrAtag = root.findall('.//FRIENDORASSOCIATE')
    for tag in fOrAtag:
        ElemPrint(tag)
        getch()

def intimateRelationshipsCheck(xmlString):
    root = xml.etree.ElementTree.fromstring(xmlString)
    irTag = root.findall('.//INTIMATERELATIONSHIPS')
    sourcePerson = root.find("./DIV0/STANDARD").text
    intimateRelationshipsList = []

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
                foundOtherName,otherName = getNameOfAssociate(person.iter("NAME"), sourcePerson)
                if foundOtherName:
                    print("relationship with: ", otherName)
                    intimateRelationshipsList.append(IntimateRelationships(attr,rearrangeSourceName(otherName)))
                else:
                    print("othername not found")
                    intimateRelationshipsList.append(IntimateRelationships(attr,"intimate relationship"))
                # for name in person.iter("NAME"):
                #     print(name.attrib["STANDARD"])
                # getch()
                
    return intimateRelationshipsList

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
    
    for familyTag in myRoot2.findall('.//FAMILY'):
        
        #--------------------------------- Get husband and wife ---------------------------------
        for familyMember in familyTag.findall("MEMBER"):
            if familyMember.attrib['RELATION'] in ["HUSBAND","WIFE"]:
                if len(list(familyMember.iter())) == 1:
                    continue
                else:
                    listOfMembers = getMemberInfo(familyMember,listOfMembers,SOURCENAME)

        #--------------------------------- get children ---------------------------------
        for familyMember in familyTag.findall("MEMBER"):
            if familyMember.attrib['RELATION'] in ["SON","DAUGHTER","STEPSON","STEPDAUGHTER"]:
                if len(list(familyMember.iter())) == 1:
                    continue
                else:
                    listOfMembers = getMemberChildInfo(familyMember,listOfMembers,SOURCENAME)
        
        #--------------------------------- get others ---------------------------------
        for familyMember in familyTag.findall('MEMBER'):
            if familyMember.attrib['RELATION'] in ["HUSBAND","WIFE","SON","DAUGHTER","STEPSON","STEPDAUGHTER"] or len(list(familyMember.iter())) == 1:
                continue
            else:
                listOfMembers = getMemberInfo(familyMember,listOfMembers,SOURCENAME)
    
    print("----------- ",SOURCENAME.strip(),"'s Family Members -----------")
    # printMemberInfo(listOfMembers)
    # print("")
    return rearrangeSourceName(SOURCENAME),listOfMembers
    
def main():
    bioFolder = os.path.expanduser("~/Documents/UoGuelph Projects/biography/")
    numBiographiesRead = 0
    printInfo = True
    numTriples = 0
    numNamelessPeople = 0

    for dirName, subdirlist, files in os.walk(bioFolder):
        for name in files:
            if "woodel-b.xml" not in name:
                continue

            if printInfo == True:
                print('\n===========%s=================' % name)

                openFile = open(bioFolder+name,"r",encoding="utf-8")
                xmlString = openFile.read()
                numBiographiesRead += 1
                
                intimateRelationshipsList   = intimateRelationshipsCheck(xmlString)
                childlessList               = childlessnessCheck(xmlString)
                childInfo                   = childrenCheck(xmlString,os.path.expanduser("\""+bioFolder+name+"\""))
                sourceName,familyMembers    = getFamilyInfo(xmlString,os.path.expanduser("\""+bioFolder+name+"\""))
                birthInfo                   = getBirth(xmlString)
                deathInfo                   = getDeath(xmlString)
                numGraphTriples,numNameless = graphMaker(sourceName,name[0:-6],familyMembers,birthInfo,deathInfo,childInfo,childlessList,intimateRelationshipsList)
                
                numTriples += numGraphTriples
                numNamelessPeople += numNameless
          
    print(numSigs, " number of significant activities found")
    print(numAdded, " number of significant activities added")
    print("number of triples: ", numTriples)
    print("number of biographies: ", numBiographiesRead)
    print("number of nameless: ", numNamelessPeople)

if __name__ == "__main__":
    # startLogin()
    main()
    
