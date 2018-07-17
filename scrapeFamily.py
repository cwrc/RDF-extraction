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
def getNameOfAssociate(names,sourcePerson):
    foundName = False
    otherName = ""
    for thisName in names:
        name = thisName.attrib["STANDARD"]
        print("looking at :", name)
        if name != sourcePerson:
            foundName = True
            otherName = name
            break
    return foundName,otherName

def intimateRelationshipsCheck(xmlString):
    root = xml.etree.ElementTree.fromstring(xmlString)
    irTag = root.findall('.//INTIMATERELATIONSHIPS')
    sourcePerson = root.find("./DIV0/STANDARD").text
    intimateRelationshipsList = []

    for tag in irTag:
        attr = ""
        
        if "EROTIC" in tag.attrib:
            attr = tag.attrib["EROTIC"]
            print("attr: ", tag.attrib["EROTIC"])
        else:
            attr = "nonErotic"
        
        for person in tag.iter("DIV2"):
                print("======person======")
                print("source: ", sourcePerson)
                print(getOnlyText(person))
                foundOtherName,otherName = getNameOfAssociate(person.iter("NAME"), sourcePerson)
                if foundOtherName:
                    print("relationship with: ", otherName)
                    intimateRelationshipsList.append(IntimateRelationships(attr,extractSourceName(otherName)))
                else:
                    print("othername not found")
                    intimateRelationshipsList.append(IntimateRelationships(attr,"intimate relationship"))
                # for name in person.iter("NAME"):
                #     print(name.attrib["STANDARD"])
                # getch()
                
    return intimateRelationshipsList
def getMemberName(thisTag):

    memberName = ""

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

    return memberName

def getMemberJobs(thisTag,memberJobs):

    # memberJobs = []

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

    return memberJobs

def getMemberActs(thisTag,memberSigAct):
    
    # memberSigAct = []
    global numSigs
    global numAdded
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

    return memberSigAct
def uniqueMemberCheck(newMember, listOfMembers):
    uniqueMember = True
    if newMember.memberRelation == "MOTHER" or newMember.memberRelation == "FATHER":
        for addedMember in listOfMembers:
            if addedMember.memberRelation == newMember.memberRelation:
                addedMember.memberJobs = list(set(addedMember.memberJobs).union(set(newMember.memberJobs)))
                addedMember.memberSigActs= list(set(newMember.memberSigActs).union(set(newMember.memberSigActs)))
                if addedMember.memberName == "" and newMember.memberName != "":
                    addedMember.memberName = newMember.memberName
                uniqueMember = False
                print("this is not a unique member")
                # getch()
    else:
        for addedMember in listOfMembers:
            # print(newMember.memberName, "(", newMember.memberRelation,")"," vs ", addedMember.memberName,"(", addedMember.memberRelation,")")
            if newMember.memberRelation == addedMember.memberRelation and newMember.memberName == addedMember.memberName:
                addedMember.memberJobs = list(set(addedMember.memberJobs).union(set(newMember.memberJobs)))
                addedMember.memberSigActs= list(set(newMember.memberSigActs).union(set(newMember.memberSigActs)))
                uniqueMember = False
                print("this is not a unique member")
                # getch()

    if newMember.memberRelation != "" and uniqueMember == True:
        print("now adding in the new member")
        listOfMembers.append(newMember)
        # getch()
    else:
        print("memberRelation is blank and unique member is false")
        # getch()
    return listOfMembers

def getMemberInfo(familyMember,listOfMembers,SOURCENAME):
    memberRelation = ""
    memberName = ""
    memberJobs = []
    memberSigAct = []
    memberRelation = familyMember.attrib['RELATION']

    for thisTag in familyMember.iter():
        # Get name of family Member by making sure the name is not of the person about whom the biography is about
        if thisTag.tag == "NAME" and thisTag.attrib['STANDARD'] != SOURCENAME and memberName == "":
            memberName = getMemberName(thisTag)
        
        # Get the family member's job
        elif thisTag.tag == "JOB":
            memberJobs = getMemberJobs(thisTag,memberJobs)
            
        # Get the family member's significant activities
        elif thisTag.tag == "SIGNIFICANTACTIVITY":
            memberSigAct = getMemberActs(thisTag,memberSigAct)

    # taking care of duplicates for parents
    newMember = Family(memberName,memberRelation,memberJobs,memberSigAct)    
    
    return uniqueMemberCheck(newMember,listOfMembers)

def notParentName(personName,parentList):
    print("welcome to not parent home")
    print("parent list: ",len(parentList))
    for parent in parentList:
        print("compare ", personName, " and ", parent.memberName)
        if parent.memberName == personName:
            return False

    print("finished notparentname check")
    # getch()


    return True
def getMemberChildInfo(familyMember,listOfMembers,SOURCENAME):
    memberRelation = familyMember.attrib['RELATION']
    memberName = ""
    memberJobs = []
    memberSigAct = []
    listOfParents = []

    for member in listOfMembers:
        print("memberName: ", member.memberName)
        print("memberRLTN: ", member.memberRelation)
        if member.memberRelation == "WIFE" or member.memberRelation == "HUSBAND":
            listOfParents.append(member)
            print("added parent")
            # getch()

    for thisTag in familyMember.iter():
        # Get name of family Member by making sure the name is not of the person about whom the biography is about
        if thisTag.tag == "NAME" and thisTag.attrib['STANDARD'] != SOURCENAME and memberName == "" and notParentName(thisTag.attrib['STANDARD'],listOfParents):
            memberName = getMemberName(thisTag)
        
        # Get the family member's job
        elif thisTag.tag == "JOB":
            memberJobs = getMemberJobs(thisTag,memberJobs)
    
        # Get the family member's significant activities
        elif thisTag.tag == "SIGNIFICANTACTIVITY":
            memberSigAct = getMemberActs(thisTag,memberSigAct)
            print("added significant activity")

    # taking care of duplicates for parents
    newMember = Family(memberName,memberRelation,memberJobs,memberSigAct)
    # newMember.samplePrint()
    
    return uniqueMemberCheck(newMember,listOfMembers)


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
            # memberRelation = familyMember.attrib['RELATION']
            if familyMember.attrib['RELATION'] in ["HUSBAND","WIFE"]:
                if len(list(familyMember.iter())) == 1:
                    continue
                else:
                    listOfMembers = getMemberInfo(familyMember,listOfMembers,SOURCENAME)

        #--------------------------------- get children ---------------------------------
        for familyMember in familyTag.findall("MEMBER"):
            # memberRelation = familyMember.attrib['RELATION']
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
    printMemberInfo(listOfMembers)
    # print("")
    return extractSourceName(SOURCENAME),listOfMembers
    
def getTripleNum(fileString):
    return fileString.split(':')[1]
def getFileName(fileString):
    return fileString.split(':')[0]
def executeFile(name):
    bioFolder = os.path.expanduser("~/Documents/UoGuelph Projects/biography/")
    # print(bioFolder)
    numBiographiesRead = 0
    printInfo = True
    sourceName = ""
    birthInfo = ""
    deathInfo = ""
    numTriples = 0
    numNamelessPeople = 0
    file = open("namesAndLines.txt_new","w")

    if printInfo == True:
        print('\n===========%s=================' % name)
        # continue
        openFile = open(bioFolder+name,"r")
        xmlString = openFile.read()
        numBiographiesRead += 1
        # friendAssociateList = friendOrAssociateCheck(xmlString)
        intimateRelationshipsList = intimateRelationshipsCheck(xmlString)
        # continue
        childlessList = childlessnessCheck(xmlString)
        childInfo = childrenCheck(xmlString,os.path.expanduser("\""+bioFolder+name+"\""))
        sourceName,familyMembers   = getFamilyInfo(xmlString,os.path.expanduser("\""+bioFolder+name+"\""))
        birthInfo       = getBirth(xmlString)
        deathInfo       = getDeath(xmlString)
        numGraphTripples,numNameless = graphMaker(sourceName,[name[0:-6],familyMembers],birthInfo,deathInfo,childInfo,childlessList,intimateRelationshipsList)
        numTriples += numGraphTripples
        numNamelessPeople += numNameless
        file.write("%s:%d\n" % (name,numGraphTripples))
        # if len(childlessList) > 0:
        #     getch()
    file.close()


def main():
    # with open(os.path.expanduser("~/Documents/differentfiles/namesAndLines_new.txt")) as newFile:
    #     contentNew = newFile.readlines()
    # contentNew = [x.strip() for x in contentNew] 

    # with open(os.path.expanduser("~/Documents/differentfiles/namesAndLines_old.txt")) as oldFile:
    #     contentOld = oldFile.readlines()
    # contentOld = [x.strip() for x in contentOld] 

    # for i in range(0,len(contentOld)):
    #     newTriple = getTripleNum(contentNew[i])
    #     oldTriple = getTripleNum(contentOld[i])
    #     newFile = getFileName(contentNew[i])
    #     oldFile = getFileName(contentOld[i])

    #     if oldTriple > newTriple:
    #         print("%d < %d"%(int(newTriple),int(oldTriple)))
    #         executeFile(newFile)
    #         # getch()

    # print(len(contentNew))
    # print(len(contentOld))
    # return
    bioFolder = os.path.expanduser("~/Documents/UoGuelph Projects/biography/")
    # print(bioFolder)
    numBiographiesRead = 0
    printInfo = True
    sourceName = ""
    birthInfo = ""
    deathInfo = ""
    numTriples = 0
    numNamelessPeople = 0
    file = open("namesAndLines.txt_new","w")

    for dirName, subdirlist, files in os.walk(bioFolder):
        for name in files:
            # if "saviet-b.xml" not in name:
            #     continue
            # if "dempch-b" not in name:
            #     continue
            # os.system("open "+"\""+bioFolder+name+"\"")
            # if "cobbfr-b" in name:
            #     printInfo = True
            if printInfo == True:
                print('\n===========%s=================' % name)
                # continue
                openFile = open(bioFolder+name,"r")
                xmlString = openFile.read()
                numBiographiesRead += 1
                # friendAssociateList = friendOrAssociateCheck(xmlString)
                intimateRelationshipsList = intimateRelationshipsCheck(xmlString)
                # continue
                childlessList = childlessnessCheck(xmlString)
                childInfo = childrenCheck(xmlString,os.path.expanduser("\""+bioFolder+name+"\""))
                sourceName,familyMembers   = getFamilyInfo(xmlString,os.path.expanduser("\""+bioFolder+name+"\""))
                birthInfo       = getBirth(xmlString)
                deathInfo       = getDeath(xmlString)
                numGraphTripples,numNameless = graphMaker(sourceName,[name[0:-6],familyMembers],birthInfo,deathInfo,childInfo,childlessList,intimateRelationshipsList)
                numTriples += numGraphTripples
                numNamelessPeople += numNameless
                file.write("%s:%d\n" % (name,numGraphTripples))
                # if len(childlessList) > 0:
                #     getch()
            # executeFile(name)
    file.close()
          
    print(numSigs, " number of significant activities found")
    print(numAdded, " number of significant activities added")
    print("number of triples: ", numTriples)
    # print("number of biographies: ", numBiographiesRead)
    # print("number of nameless: ", numNamelessPeople)

if __name__ == "__main__":
    
    # startLogin()
    main()
    
