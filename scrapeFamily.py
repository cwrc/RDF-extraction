import requests
# import sys, xml.etree.ElementTree, os, logging, csv, datetime,
# from Env import env
import sys
from gLoggingInFunctions import *
from graphOntology import *
from birthDeath import *
from xml.etree import ElementTree

numSigs = 0
numAdded = 0
session = requests.Session()
numtags = 0

# from https://stackoverflow.com/questions/749796/pretty-printing-xml-in-python
def indenter(elem, level=0):
    i = "\n" + level*"  "
    j = "\n" + (level-1)*"  "
    
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for subelem in elem:
            indenter(subelem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = j
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = j

def ElemPrint(elem):
    indenter(elem)
    ElementTree.dump(elem)

def getOnlyText(tag):
    paraText = tag.itertext()
    paragraph = ""

    for text in paraText:
        paragraph = paragraph + " " + text.strip()
    paragraph = paragraph.strip()
    
    return paragraph

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

class Family:
    def __init__(self, memName, memRLTN,memJobs,memSigActs):
        self.memberName = memName
        self.memberRelation = memRLTN
        self.memberJobs = list(memJobs)
        self.memberSigActs = list(memSigActs)

    def samplePrint(self):
        print("......................\nName: ",self.memberName,"\nRelation: ",self.memberRelation)
        print("Jobs: ",end="")
        print(*self.memberJobs,sep=", ")
        print("SigAct: ",end="")
        print(*self.memberSigActs,sep=", ")


# Get g information about the subject
# ------ Example ------
# birth date:  1873-12-07
# birth positions: ['ELDEST']
# birth place: Gore, Virginia, USA
def getch():
    sys.stdin.read(1)
def dateValidate(dateStr):
    try:
        datetime.datetime.strptime(dateStr, '%Y-%m-%d')
        return True
    except ValueError:
        return False
        


def printMemberInfo(memberList):
    for mem in memberList:
        mem.samplePrint()

def extractSourceName(nameStr):
    if "," in nameStr:
        fullName = nameStr.split(",")
        return fullName[1].strip(" ") + " "+ fullName[0].strip(" ")
    return nameStr
def extractNameFromTitle(nameStr):
    nameSeparation = nameStr.split(",,")
    returnName = ""
    if "of" in nameSeparation[-1]:
        fullName = nameSeparation[-2].split(",")
        # print("returning: ", fullName[-1])
        returnName = fullName[-1].strip(" ")
    elif "," in nameSeparation[0]:
        fullName = nameSeparation[0].split(",")
        returnName = fullName[1].strip(" ") + " "+ fullName[0].strip(" ")
        # print(newName)
    else:
        print(nameStr,"something went wrong")
        sys.stdin.read(1)
    if " of " in returnName:
        justName = returnName.split(" of ")
        returnName = justName[0]
    return returnName

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
    global numtags
    for tag in childrenTag:
        ElemPrint(tag)
        
        if any(miscarriageWord in getOnlyText(tag) for miscarriageWord in 
            ["miscarriage","miscarriages","miscarried"]):
            # print("this person had a miscarriage")
            childlessList.append(ChildlessStatus("miscarriage"))
            # getch()
        
        elif any(stillbirthWord in getOnlyText(tag) for stillbirthWord in 
            ["stillborn","still birth"]):
            # print("this person experienced a stillbirth")
            childlessList.append(ChildlessStatus("stillbirth"))
            # getch()
            # one still birth
        
        elif any(abortionWord in getOnlyText(tag) for abortionWord in 
            ["abortion","aborted"]):
            # print("this person experienced an abortion")
            childlessList.append(ChildlessStatus("abortion"))

            # getch()
            # no entries has this
        elif any(birthControlWord in getOnlyText(tag) for birthControlWord in 
            ["contraception"]):
            # print("this person used contraception")
            childlessList.append(ChildlessStatus("birth control"))

            # getch()
            # no entries has this
        
        elif any(veneralDisease in getOnlyText(tag) for veneralDisease in 
            ["syphilis","veneral","VD"]):
            # print("this person experienced a veneral")
            childlessList.append(ChildlessStatus("venereal disease"))

            # getch()
            # 2 entries have this
        
        elif any(adoptionWord in getOnlyText(tag) for adoptionWord in 
            ["adopted","adoption"]):
            # print("this person experienced an adoption")
            childlessList.append(ChildlessStatus("adoption"))

            # getch()
            # 8 entries have this
        
        elif any(childlessWord in getOnlyText(tag) for childlessWord in 
            ["childless","no children","no surviving children"]):
            # print("this person is childless")
            childlessList.append(ChildlessStatus("childlessness"))

            # getch()
            # 131 entries have this
            # numtags += 1
        else:
            # print("this person is childless (else statement)")
            childlessList.append(ChildlessStatus("childlessness"))

            # getch()
            numtags += 1
            # 69 entries
        
        print("------------")
        
        for child in childlessList:
            print(child.Label)

    print("number of tags: ", numtags)
    return childlessList
        # print(getOnlyText(tag))
        # getch()

def friendOrAssociateCheck(xmlString):
    root = xml.etree.ElementTree.fromstring(xmlString)
    fOrAtag = root.findall('.//FRIENDORASSOCIATE')
    for tag in fOrAtag:
        ElemPrint(tag)
        getch()

def intimateRelationshipsCheck(xmlString):
    root = xml.etree.ElementTree.fromstring(xmlString)
    irTag = root.findall('.//INTIMATERELATIONSHIPS')
    for tag in irTag:
        if "EROTIC" in tag.attrib:
            attr = tag.attrib["EROTIC"]
            print("attr: ", tag.attrib["EROTIC"])
            # ElemPrint(tag)
            for person in tag.iter("DIV2"):
                print("======person======")
                print(getOnlyText(person))
                for name in person.iter("NAME"):
                    print(name.attrib["STANDARD"])
                getch()
                

        # ElemPrint(tag)
        else:
            # hasIntimateRelationship
            print("intimate relationship attribute")
            # ElemPrint(tag)
            # getch()

# This function obtains family information
# ------ Example ------
# Name:  Grant, Josceline Charles Henry
# Relation:  FATHER
# Jobs: army officer
# SigAct: lost money, currency committee
def getFamilyInfo(xmlString, sourceFile):
    global numSigs
    global numAdded
    # filePath = os.path.expanduser("~/Downloads/laurma-b.xml")
    # myRoot = xml.etree.ElementTree.parse(filePath)
    # myRoot2 = myRoot.getroot()
    myRoot2 = xml.etree.ElementTree.fromstring(xmlString)

    SOURCENAME = myRoot2.find("./DIV0/STANDARD").text
    for child in myRoot2.findall('.//CHILDREN'):
        print("found child")

    # sigi = myRoot2.find("./DIV0/DIV1/FAMILY/MEMBER/DIV2/SHORTPROSE/P/SIGNIFICANTACTIVITY")
    
    # print(' '.join(sigi.itertext()))
    # print(sigi.itertext()' '.join())
    # return
    listOfMembers = []
    memberRelation = ""
    memberName = ""
    memberJobs = []
    memberSigAct = []
    
    for familyTag in myRoot2.findall('.//FAMILY'):
        # print(familyTag.tag)
        for familyMember in familyTag.findall('MEMBER'):
            if "RELATION" in familyMember.attrib:
                memberRelation = familyMember.attrib['RELATION']

            if len(list(familyMember.iter())) == 1:
                continue
            for thisTag in familyMember.iter():
                
                # Get name of family Member by making sure the name is not of the person about whom the biography is about
                if thisTag.tag == "NAME" and thisTag.attrib['STANDARD'] != SOURCENAME and memberName == "":
                    if ",," in thisTag.attrib['STANDARD']:
                        print("old: ", thisTag.attrib['STANDARD'])
                        memberName = extractNameFromTitle(thisTag.attrib['STANDARD'])
                        print("new: ", memberName)
                        # memberName = thisTag.text
                        # print(memberRelation,"|,, name|",thisTag.attrib['STANDARD'])
                        # sys.stdin.read(1)
                        if "(" in memberName and ")" not in memberName:
                            memberName += ")"
                    else:
                        memberName = thisTag.attrib['STANDARD']
                
                # Get the family member's job
                elif thisTag.tag == "JOB":
                    if 'REG' in thisTag.attrib:
                        memberJobs.append(thisTag.attrib['REG'])
                    elif thisTag.text is '':
                        memberJobs.append(thisTag.text)
                    else:
                        paraText = thisTag.itertext()
                        paragraph = ""

                        for text in paraText:
                            paragraph = paragraph + " " + text.strip()
                        paragraph = paragraph.strip()
                        memberJobs.append(paragraph)
                    
                # Get the family member's significant activities
                elif thisTag.tag == "SIGNIFICANTACTIVITY":
                    numSigs += 1
                    if "REG" in thisTag.attrib:
                        sigAct = thisTag.attrib["REG"]
                        memberSigAct.append(sigAct)
                        numAdded += 1
                    else:
                        sigAct = thisTag.text
                        print(sigAct)

                        if sigAct == None or sigAct == "":
                           sigAct = ' '.join(thisTag.itertext())

                           print(sigAct)
                           if sigAct != "" and sigAct not in memberSigAct:
                               memberSigAct.append(sigAct)
                               numAdded += 1
                               print(sigAct)
                               print("2. number of sigActs added: ",numAdded)
                               # sys.stdin.read(1)
                           else:
                               print("1.significant activity not added")
                               # sys.stdin.read(1)
                        else:
                            memberSigAct.append(sigAct)
                            numAdded += 1
                            # print(sigAct)
                            # print("2.significant activity not added")

                            # sys.stdin.read(1)

                           # print("no significant Acts in the sigact")
                           # response = input("open file? ")
                           # if response == "y" or response == "Y":
                           #     print(sourceFile)
                           #     os.system("open "+sourceFile)
                           #     sys.stdin.read(1)

            # print("......................")
            # print("Name: ",memberName)
            # print("Relation: ",memberRelation)
            # print("Jobs: ",memberJobs)
            # print("sigAct: ", memberSigAct)
            # print("......................")
            # print("----------------------------------")
            
            # if any(mem.memberName == memberName and mem.memberRelation == memberRelation for mem in listOfMembers) == False:
            # if memberName != "" and 

            # taking care of duplicates for parents
            newMember = Family(memberName,memberRelation,memberJobs,memberSigAct)

            uniqueMember = True
            if newMember.memberRelation == "MOTHER" or newMember.memberRelation == "FATHER":
                for addedMember in listOfMembers:
                    if addedMember.memberRelation == newMember.memberRelation:
                        addedMember.memberJobs = list(set(addedMember.memberJobs).union(set(newMember.memberJobs)))
                        addedMember.memberSigActs= list(set(newMember.memberSigActs).union(set(newMember.memberSigActs)))
                        if addedMember.memberName == "" and newMember.memberName != "":
                            addedMember.memberName = memberName
                        uniqueMember = False
            else:
                for addedMember in listOfMembers:
                    # print(newMember.memberName, "(", newMember.memberRelation,")"," vs ", addedMember.memberName,"(", addedMember.memberRelation,")")
                    if newMember.memberRelation == addedMember.memberRelation and newMember.memberName == addedMember.memberName:
                        addedMember.memberJobs = list(set(addedMember.memberJobs).union(set(newMember.memberJobs)))
                        addedMember.memberSigActs= list(set(newMember.memberSigActs).union(set(newMember.memberSigActs)))
                        uniqueMember = False

            if memberRelation != "" and uniqueMember == True:
                listOfMembers.append(newMember)
           
            memberRelation = ""
            memberName = ""
            description = ""
            memberJobs.clear()
            memberSigAct.clear()
    
    print("----------- ",SOURCENAME.strip(),"'s Family Members -----------")
    printMemberInfo(listOfMembers)
    # print("")
    return extractSourceName(SOURCENAME),listOfMembers
    

if __name__ == "__main__":
    
    # startLogin()

    bioFolder = os.path.expanduser("~/Documents/UoGuelph Projects/biography/")
    # print(bioFolder)
    numBiographiesRead = 0
    printInfo = True
    sourceName = ""
    birthInfo = ""
    deathInfo = ""
    numTriples = 0
    numNamelessPeople = 0
    for dirName, subdirlist, files in os.walk(bioFolder):
        for name in files:
            # if "dempch-b.xml" not in name:
            #     continue
            if "larkph-b" not in name:
                continue
            # os.system("open "+"\""+bioFolder+name+"\"")
            # if "cobbfr-b" in name:
            #     printInfo = True

            if printInfo == True:
                print('\n===========%s=================' % name)
                openFile = open(bioFolder+name,"r")
                xmlString = openFile.read()
                numBiographiesRead += 1
                # friendAssociateList = friendOrAssociateCheck(xmlString)
                intimateRelationshipsList = intimateRelationshipsCheck(xmlString)
                continue
                childlessList = childlessnessCheck(xmlString)
                childInfo = childrenCheck(xmlString,os.path.expanduser("\""+bioFolder+name+"\""))
                sourceName,familyMembers   = getFamilyInfo(xmlString,os.path.expanduser("\""+bioFolder+name+"\""))
                birthInfo       = getBirth(xmlString)
                deathInfo       = getDeath(xmlString)
                numGraphTripples,numNameless = graphMaker(sourceName,[name[0:-6],familyMembers],birthInfo,deathInfo,childInfo,childlessList)
                numTriples += numGraphTripples
                numNamelessPeople += numNameless
                if len(childlessList) > 0:
                    getch()
    print(numSigs, " number of significant activities found")
    print(numAdded, " number of significant activities added")
    print("number of triples: ", numTriples)
    print("number of biographies: ", numBiographiesRead)
    print("number of nameless: ", numNamelessPeople)
