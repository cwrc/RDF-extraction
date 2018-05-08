import requests
import sys
from Env import env
import xml.etree.ElementTree
import os
import logging

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

# Get birth information about the subject
# ------ Example ------
# birth date:  1873-12-07
# birth positions: ['ELDEST']
# birth place: Gore, Virginia, USA
def getBirth(xmlString):

    # filePath = os.path.expanduser("~/Downloads/laurma-b.xml")
    # getTreeRoot = xml.etree.ElementTree.parse(filePath)
    # treeRoot = getTreeRoot.getroot()
    treeRoot = xml.etree.ElementTree.fromstring(xmlString)

    # BIRTH
    birthDate = ""
    birthPlaceSettlement = ""
    birthPlaceRegion = ""
    birthPlaceGeog = ""
    birthPositions = []

    birthTagParent = treeRoot.find("./DIV0/DIV1/BIRTH")

    try:
        birthTags = list(birthTagParent.iter("CHRONSTRUCT"))
        
        if len(birthTags) == 0:
            print(birthTagParent)
            birthTags = list(birthTagParent.iter("SHORTPROSE"))
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
        birthDateTags = list(birthTag.iter('DATE'))
        if len(birthDateTags) == 0:
            
            # If no 'DATE' tag, try 'DATERANGE' tag
            birthDateTags = list(birthTag.iter('DATERANGE'))
        if len(birthDateTags) == 0:
            
            # If no 'DATERANGE' tag, try 'DATESTRUCT' tag
            birthDateTags = list(birthTag.iter('DATESTRUCT'))

        birthDateTag = birthDateTags[0]

        if 'VALUE' in birthDateTag.attrib:
            birthDate = birthDateTag.attrib['VALUE']
        elif 'CERTAINTY' in birthDateTag.attrib and 'FROM' in birthDateTag.attrib and 'TO' in birthDateTag.attrib:
            # Sometimes the birth date isn't exact so a range is used
            birthDate = birthDateTag.attrib['FROM'] + " to " + birthDateTag.attrib['TO']
        
        print("---------Information about person--------------")
        print("birth date: ", birthDate)
    
    except Exception as e:
        print("&&&& Birth Date error &&&&")
        print("error: ", e)
        sys.stdin.read(1)
        return
    
    # Get birth positions
    # Ex. 'Oldest', 'Youngest'
    birthPositionTags = list(birthTag.iter('BIRTHPOSITION'))
    for positions in birthPositionTags:
        if 'POSITION' in positions.attrib:
            birthPositions.append(positions.attrib['POSITION'])
    print("birth positions: {}".format(birthPositions))
    
    # Get birth place.
    # Where the subject is born
    birthPlaceTags = list(birthTag.iter('PLACE'))
    birthPlaceTag = ""
    try:
        if len(birthPlaceTags) > 0:
            birthPlaceTag = birthPlaceTags[0]
            for tag in birthPlaceTag.iter():
                # Get settlement where they were born
                if tag.tag == "SETTLEMENT":
                    if "REG" in tag.attrib:
                        birthPlaceSettlement = tag.attrib["REG"]
                    elif "CURRENT" in tag.attrib:
                        # Current refers to a place where the name has changed.
                        # i.e. Today it is known as something else but during this
                        # subject's time, the name was different
                        birthPlaceSettlement = tag.attrib["CURRENT"]
                    else:
                        birthPlaceSettlement = tag.text
                # Get region where they were born
                elif tag.tag == "REGION":
                    if "CURRENT" in tag.attrib:
                        birthPlaceRegion = tag.attrib['CURRENT']
                    elif "REG" in tag.attrib:
                        birthPlaceRegion = tag.attrib['REG']
                    else:
                        birthPlaceRegion = tag.text
                # Get country
                elif tag.tag == "GEOG":
                    if "REG" in tag.attrib:
                        birthPlaceGeog = tag.attrib["REG"]
                    elif "CURRENT" in tag.attrib:
                        birthPlaceGeog = tag.attrib["CURRENT"]
                    else:
                        birthPlaceGeog = tag.text
                    
            print("birth place: {}, {}, {}".format(birthPlaceSettlement,birthPlaceRegion,birthPlaceGeog))
        else:
            print("no birthPlaceTag")
            # sys.stdin.read(1)

    except AttributeError:
        print("no birth place information for this individual")
        # sys.stdin(1)

    
def getDeath(xmlString):

    # filePath = os.path.expanduser("~/Downloads/laurma-b.xml")
    # getTreeRoot = xml.etree.ElementTree.parse(filePath)
    # treeRoot = getTreeRoot.getroot()
    treeRoot = xml.etree.ElementTree.fromstring(xmlString)

    # DEATH
    deathDate = ""
    deathPlaceSettlement = ""
    deathPlaceRegion = ""
    deathPlaceGeog = ""
    deathCauses = []

    deathTagParent = treeRoot.find("./DIV0/DIV1/DEATH/")
    
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
        getChronstructTags = list(deathTagParent.iter("CHRONSTRUCT"))
        
        if len(getChronstructTags) == 0:
            # No chronstruct tag found. Look for a shortprose tag
            getChronstructTags = list(deathTagParent.iter("SHORTPROSE"))

        if len(getChronstructTags) == 0:
            # No shortprose tag found either
            print("no SHORTPROSE in death found")
            sys.stdin.read(1)
            return

        if len(getChronstructTags) > 0:
            # A tag is found. Either a chronstruct or a shortprose
            firstChronstructTag = getChronstructTags[0]
            
            # Iterate through date tags
            deathDateTags = list(firstChronstructTag.iter('DATE'))
            
            if len(deathDateTags) == 0:
                # No date tag found, look for a datestruct tag
                print("no date found in construct. trying datestruct")
                deathDateTags = list(firstChronstructTag.iter('DATESTRUCT'))
            if len(deathDateTags) == 0:
                # No datestruct tag found, look for a daterange tag
                print("no datestruct. trying dateRange")
                deathDateTags = list(firstChronstructTag.iter('DATERANGE'))
            if len(deathDateTags) == 0:
                # No daterange tag found either
                print("no date range either")
                # sys.stdin.read(1)
            else:
                # Found a date tag
                deathDateTag = deathDateTags[0]
                if 'VALUE' in deathDateTag.attrib:
                    deathDate = deathDateTag.attrib['VALUE']
                elif 'CERTAINTY' in deathDateTag.attrib and 'FROM' in deathDateTag.attrib and 'TO' in deathDateTag.attrib:
                    deathDate = deathDateTag.attrib['FROM'] + " to " + deathDateTag.attrib['TO']
            
            
            
    
    except (AttributeError) as e:
        print("Death information not found. person probably still alive")
        # print("error: ", e)
        logging.exception(e)
        sys.stdin.read(1)
        return

    except NameError:
        print("Name Error")
        print("error: ", e)
        sys.stdin.read(1)
        return

    print("\ndeath date: ", deathDate)

    # CAUSE OF DEATH
    deathCauseTags = (firstChronstructTag.findall('CHRONPROSE/CAUSE'))
    if len(deathCauseTags) > 0:
        for causes in deathCauseTags:
            if "REG" in causes.attrib:
                deathCauses.append(causes.attrib['REG'])
            else:
                deathCauses.append(causes.text)
        
        print("death causes: {}".format(deathCauses))          

    # PLACE OF DEATH
    deathPlaceTags = (firstChronstructTag.findall('CHRONPROSE/PLACE/'))
    if len(deathPlaceTags) > 0:
        for tag in deathPlaceTags:
            if tag.tag == "SETTLEMENT":
                if "CURRENT" in tag.attrib:
                    deathPlaceSettlement = tag.attrib["CURRENT"]
                elif "REG" in tag.attrib:
                    deathPlaceSettlement = tag.attrib["REG"]
                else:
                    deathPlaceSettlement = tag.text
                
            elif tag.tag == "REGION":
                if "CURRENT" in tag.attrib:
                    deathPlaceRegion = tag.attrib["CURRENT"]
                elif "REG" in tag.attrib:
                    deathPlaceRegion = tag.attrib["REG"]
                else:
                    deathPlaceRegion = tag.text
            elif tag.tag == "GEOG":
                if "CURRENT" in tag.attrib:
                    deathPlaceGeog = tag.attrib["CURRENT"]
                elif "REG" in tag.attrib:
                    deathPlaceGeog = tag.attrib["REG"]
                else:
                    deathPlaceGeog = tag.text
    
        print("death place: {}, {}, {}".format(deathPlaceSettlement,deathPlaceRegion,deathPlaceGeog))

    else:
        allShortprose = firstChronstructTag.findall('SHORTPROSE')
        # print(allShortprose)
        for shortprose in allShortprose:
            for tags in shortprose.iter('PLACE'):
                for placeInfo in tags.iter():
                    if placeInfo.tag == "SETTLEMENT":
                        deathPlaceSettlement = placeInfo.text
                    elif placeInfo.tag == "REGION":
                        try:
                            deathPlaceRegion = placeInfo.attrib['REG']
                        except KeyError:
                            deathPlaceRegion = placeInfo.text
                    elif placeInfo.tag == "GEOG":
                        try:
                            deathPlaceGeog = placeInfo.attrib['REG']
                        except KeyError:
                            deathPlaceGeog = placeInfo.text
                    # fix: some place tags don't have all of the above
                    if deathPlaceSettlement != "" and deathPlaceRegion != "" and deathPlaceGeog != "":
                        print("other death info: {}, {}, {}".format(deathPlaceSettlement,deathPlaceRegion,deathPlaceGeog))
                        deathPlaceSettlement = ""
                        deathPlaceRegion = ""
                        deathPlaceGeog = ""


def printMemberInfo(memberList):
    for mem in memberList:
        mem.samplePrint()

# This function obtains family information
# ------ Example ------
# Name:  Grant, Josceline Charles Henry
# Relation:  FATHER
# Jobs: army officer
# SigAct: lost money, currency committee
def getFamilyInfo(xmlString):

    # filePath = os.path.expanduser("~/Downloads/laurma-b.xml")
    # myRoot = xml.etree.ElementTree.parse(filePath)
    # myRoot2 = myRoot.getroot()
    myRoot2 = xml.etree.ElementTree.fromstring(xmlString)

    SOURCENAME = myRoot2.find("./DIV0/STANDARD").text

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
                        memberName = thisTag.text
                        if "(" in memberName and ")" not in memberName:
                            memberName += ")"
                    else:
                        memberName = thisTag.attrib['STANDARD']
                # Get the family member's job
                elif thisTag.tag == "JOB":
                    try:
                        job=""
                        job = thisTag.attrib['REG']
                        if job != "" and job not in memberJobs:
                            memberJobs.append(job)
                    except KeyError:
                        if job != "" and job not in memberJobs:
                            memberJobs.append(thisTag.text)
                # Get the family member's significant activities
                elif thisTag.tag == "SIGNIFICANTACTIVITY":
                    sigAct = thisTag.text
                    if sigAct != "" and sigAct not in memberSigAct:
                        memberSigAct.append(sigAct)

            # print("......................")
            # print("Name: ",memberName)
            # print("Relation: ",memberRelation)
            # print("Jobs: ",memberJobs)
            # print("sigAct: ", memberSigAct)
            # print("......................")
            # print("----------------------------------")
            
            # if any(mem.memberName == memberName and mem.memberRelation == memberRelation for mem in listOfMembers) == False:
            if memberName != "" and memberRelation != "":
                listOfMembers.append(Family(memberName,memberRelation,memberJobs,memberSigAct))
           
            memberRelation = ""
            memberName = ""
            description = ""
            memberJobs.clear()
            memberSigAct.clear()
    
    print("----------- ",SOURCENAME.strip(),"'s Family Members -----------")
    printMemberInfo(listOfMembers)
    print("")


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
    else:

        # url = "{0}/islandora/rest/v1/object/orlando%3A{1}/datastream/CWRC/?content=true".format('http://beta.cwrc.ca','2ef845b2-3421-460a-9e0f-623cb30d62d1')
        # r2 = session.get('http://beta.cwrc.ca/islandora/rest/v1/object/orlando%3Ab4859cdd-8c58-46e9-bf2a-28bf8090fcbc/datastream/CWRC/?content=true')
        r2 = session.get('http://beta.cwrc.ca/islandora/rest/v1/object/orlando%3Ad9ab7813-1b1d-42c8-98b0-9712398d8990/datastream/CWRC/?content=true')
        if r2.status_code == 200:
            print("got the content")
            # print(r2.pid)
            getFamilyInfo(r2.text)
            getBirth(r2.text)
            getDeath(r2.text)
        else:
            print(r2.text)
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



if __name__ == "__main__":
    # startLogin()

    # getFamilyInfo()
    # getBirth()
    # getDeath()
    mydir = os.path.expanduser("~/Downloads/biography/")
    # print(mydir)
    numBiographiesRead = 0
    printInfo = False
    for dirName, subdirlist, files in os.walk(mydir):
        for name in files:
            # if "cobbfr-b.xml" not in name:
                # continue
            # if "laurma-b" not in name:
            #     continue
            if "cobbfr-b" in name:
                printInfo = True

            if printInfo == True:
                print('\n===========%s=================' % name)
                openFile = open(mydir+name,"r")
                xmlString = openFile.read()
                # numBiographiesRead += 1
                getFamilyInfo(xmlString)
                getBirth(xmlString)
                getDeath(xmlString)
                # if (peopleDone % 25 == 0):
                #     sys.stdin.read(1)
                # numBiographiesRead += 1
            # getchar()
            # print(openFile.read())
        # for file in files:
        #     print(os.path.join(subdir,file))
    print("people looked at", numBiographiesRead)



