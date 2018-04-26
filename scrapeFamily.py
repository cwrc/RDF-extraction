import requests
import sys
from Env import env
import xml.etree.ElementTree
import os

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


def startLogin():
    default_user = "NONE"
    default_password = "NONE"
    if len(sys.argv) > 2:
        default_user = sys.argv[1]
        default_password = sys.argv[2]
    argv = [env.env("USER_NAME", default_user), env.env("PASSWORD", default_password)]
    main(argv)

def login(auth):
    print(auth)
    response = session.post('http://beta.cwrc.ca/rest/user/login', auth)
    print(response)
    if response.status_code != 200:
        raise ValueError('Invalid response')
    # print("this is where you would log in")


def usage():
    print("%s [username] [password]" % sys.argv[0])


def main(argv):            
    # Store the session for future requests.
    login({"username": argv[0], "password": argv[1]})


def get_file_description(uuid):
    res = session.get('http://beta.cwrc.ca/islandora/rest/v1/object/' + uuid);
    return res.text

def get_file_with_format(uuid, format):
    res = session.get('http://beta.cwrc.ca/islandora/rest/v1/object/' + uuid + '/datastream/' + format)
    return res.text

def getFamilyInfo():

    filePath = os.path.expanduser("~/Downloads/laurma-b.xml")
    myRoot = xml.etree.ElementTree.parse(filePath)
    myRoot2 = myRoot.getroot()

    SOURCENAME = myRoot2.find("./DIV0/STANDARD").text

    listOfMembers = []
    memberRelation = ""
    memberName = ""
    memberJobs = []
    memberSigAct = []
    
    for familyTag in myRoot2.findall('.//FAMILY'):
        print(familyTag.tag)
        for familyMember in familyTag.findall('MEMBER'):
            memberRelation = familyMember.attrib['RELATION']
            for thisTag in familyMember.iter():
                print(thisTag)
                if thisTag.tag == "NAME" and thisTag.attrib['STANDARD'] != SOURCENAME and memberName == "":
                    memberName = thisTag.attrib['STANDARD']
                elif thisTag.tag == "JOB":
                    try:
                        job = thisTag.attrib['REG']
                        if job != "" and job not in memberJobs:
                            memberJobs.append(job)
                    except KeyError:
                        if job != "" and job not in memberJobs:
                            memberJobs.append(thisTag.text)
                elif thisTag.tag == "SIGNIFICANTACTIVITY":
                    sigAct = thisTag.text
                    if sigAct != "" and sigAct not in memberSigAct:
                        memberSigAct.append(sigAct)

            print("......................")
            print("Name: ",memberName)
            print("Relation: ",memberRelation)
            print("Jobs: ",memberJobs)
            print("sigAct: ", memberSigAct)
            print("......................")
            print("----------------------------------")
            
            # if any(mem.memberName == memberName and mem.memberRelation == memberRelation for mem in listOfMembers) == False:
            if memberName != "" and memberRelation != "":
                listOfMembers.append(Family(memberName,memberRelation,memberJobs,memberSigAct))
           
            memberRelation = ""
            memberName = ""
            description = ""
            memberJobs.clear()
            memberSigAct.clear()
        print("==========================================================")
    
    print("\n\n++++++++++++++++++++++++++++++++++\nListed Below are members extracted from the biography that are known to be related to ML\n++++++++++++++++++++++++++++++++++")
    printMemberInfo(listOfMembers)
    print("")

    # getBirthAndDeath(myRoot2)

def getBirth():

    filePath = os.path.expanduser("~/Downloads/laurma-b.xml")
    getTreeRoot = xml.etree.ElementTree.parse(filePath)
    treeRoot = getTreeRoot.getroot()

    # BIRTH
    birthDate = ""
    birthPlaceSettlement = ""
    birthPlaceRegion = ""
    birthPlaceGeog = ""
    birthPositions = []

    birthTagParent = treeRoot.findall("./DIV0/DIV1")
    birthTag = birthTagParent[1].find('BIRTH/DIV2/CHRONSTRUCT')
    
    if birthTag == None:
        print("Birth information not found")
        return

    birthDateTag = list(birthTag.iter('DATE'))[0]
    birthDate = birthDateTag.attrib['VALUE']
    
    birthPositionTags = list(birthTag.iter('BIRTHPOSITION'))
    for positions in birthPositionTags:
        birthPositions.append(positions.attrib['POSITION'])

    birthPlaceTag = list(birthTag.iter('PLACE'))[0]

    for tag in birthPlaceTag.iter():
        if tag.tag == "SETTLEMENT":
            birthPlaceSettlement = tag.text
        elif tag.tag == "REGION":
            birthPlaceRegion = tag.text
        elif tag.tag == "GEOG":
            birthPlaceGeog = tag.attrib['REG']

    print("---------Information about person--------------")
    print("birth date: ", birthDate)
    print("birth place: {}, {}, {}".format(birthPlaceSettlement,birthPlaceRegion,birthPlaceGeog))
    print("birth positions: {}".format(birthPositions))


def getDeath():

    filePath = os.path.expanduser("~/Downloads/laurma-b.xml")
    getTreeRoot = xml.etree.ElementTree.parse(filePath)
    treeRoot = getTreeRoot.getroot()

    # DEATH
    deathDate = ""
    deathPlaceSettlement = ""
    deathPlaceRegion = ""
    deathPlaceGeog = ""
    deathCauses = []

    deathTagParent = treeRoot.find("./DIV0/DIV1/DEATH/DIV2/CHRONSTRUCT")
    deathDateTag = ""
    
    try:
        deathDateTag = list(deathTagParent.iter('DATE'))[0]
    except (AttributeError,NameError):
        print("Death information not found")
        return
    
    deathDate = deathDateTag.attrib['VALUE']

    deathCauseTags = list(deathTagParent.iter('CAUSE'))
    for causes in deathCauseTags:
        try:
            thisCause = causes.attrib['REG']
            if thisCause is not None:
                deathCauses.append(thisCause)
        except KeyError:
            deathCauses.append(causes.text)            

    deathPlaceTag = list(deathTagParent.iter('PLACE'))[0]

    for tag in deathPlaceTag.iter():
        if tag.tag == "SETTLEMENT":
            deathPlaceSettlement = tag.text
        elif tag.tag == "REGION":
            deathPlaceRegion = tag.text
        elif tag.tag == "GEOG":
            deathPlaceGeog = tag.attrib['REG']


    print("\ndeath date: ", deathDate)
    print("death place: {}, {}, {}".format(deathPlaceSettlement,deathPlaceRegion,deathPlaceGeog))
    print("death causes: {}".format(deathCauses))


def printMemberInfo(memberList):
    for mem in memberList:
        mem.samplePrint()

if __name__ == "__main__":
    # startLogin()
    # getFamilyInfo()
    getBirth()
    getDeath()

