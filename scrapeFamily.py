import requests
# import sys, xml.etree.ElementTree, os, logging, csv, datetime,
# from Env import env
import sys
from gLoggingInFunctions import *
from graphOntology import *
from birthDeath import *

numSigs = 0
numAdded = 0
session = requests.Session()

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
def dateValidate(dateStr):
    try:
        datetime.datetime.strptime(dateStr, '%Y-%m-%d')
        return True
    except ValueError:
        return False
        


def printMemberInfo(memberList):
    for mem in memberList:
        mem.samplePrint()
def extractName(nameStr):
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
        print("something went wrong")
        sys.stdin.read(1)
    if " of " in returnName:
        justName = returnName.split(" of ")
        returnName = justName[0]
    return returnName


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
            
            for thisTag in familyMember.iter():
                
                # Get name of family Member by making sure the name is not of the person about whom the biography is about
                if thisTag.tag == "NAME" and thisTag.attrib['STANDARD'] != SOURCENAME and memberName == "":
                    if ",," in thisTag.attrib['STANDARD']:
                        print("old: ", thisTag.attrib['STANDARD'])
                        memberName = extractName(thisTag.attrib['STANDARD'])
                        print("new: ", memberName)
                        # memberName = thisTag.text
                        # print(memberRelation,"|,, name|",thisTag.attrib['STANDARD'])
                        sys.stdin.read(1)
                        if "(" in memberName and ")" not in memberName:
                            memberName += ")"
                    else:
                        memberName = thisTag.attrib['STANDARD']
                # Get the family member's job
                elif thisTag.tag == "JOB":
                    if 'REG' in thisTag.attrib:
                        memberJobs.append(thisTag.attrib['REG'])
                    else:
                        memberJobs.append(thisTag.text)
                    
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
            # if memberName != "" and memberRelation != "":

            listOfMembers.append(Family(memberName,memberRelation,memberJobs,memberSigAct))
           
            memberRelation = ""
            memberName = ""
            description = ""
            memberJobs.clear()
            memberSigAct.clear()
    
    print("----------- ",SOURCENAME.strip(),"'s Family Members -----------")
    printMemberInfo(listOfMembers)
    # print("")
    return SOURCENAME,listOfMembers
    

if __name__ == "__main__":
    
    # startLogin()

    mydir = os.path.expanduser("~/Google Drive/Term 3 - UoGuelph/biography/")
    # print(mydir)
    numBiographiesRead = 0
    printInfo = True
    sourceName = ""
    birthInfo = ""
    deathInfo = ""
    for dirName, subdirlist, files in os.walk(mydir):
        for name in files:
            if "seacma-b.xml" not in name:
                continue
            # if "laurma-b" not in name:
            #     continue
            # os.system("open "+"\""+mydir+name+"\"")
            # if "cobbfr-b" in name:
            #     printInfo = True

            if printInfo == True:
                print('\n===========%s=================' % name)
                openFile = open(mydir+name,"r")
                xmlString = openFile.read()
                # numBiographiesRead += 1
                sourceName,familyMembers   = getFamilyInfo(xmlString,os.path.expanduser("\""+mydir+name+"\""))
                birthInfo       = getBirth(xmlString)
                deathInfo       = getDeath(xmlString)
                graphMaker(sourceName,[name[0:-6],familyMembers],birthInfo,deathInfo)
    print(numSigs, " number of significant activities found")
    print(numAdded, " number of significant activities added")
