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
        birthDateTags = list(birthTag.iter('DATE'))
        if len(birthDateTags) == 0:
            birthDateTags = list(birthTag.iter('DATERANGE'))
        if len(birthDateTags) == 0:
            print("still nothing found")
            birthDateTags = list(birthTag.iter('DATESTRUCT'))

        birthDateTag = birthDateTags[0]

        if 'VALUE' in birthDateTag.attrib:
            birthDate = birthDateTag.attrib['VALUE']
        elif 'CERTAINTY' in birthDateTag.attrib:
            birthDate = birthDateTag.attrib['FROM'] + " to " + birthDateTag.attrib['TO']
        print("---------Information about person--------------")
        print("birth date: ", birthDate)
    
    except Exception as e:
        print("&&&& Birth Date error &&&&")
        print("error: ", e)
        sys.stdin.read(1)
        return
    
    birthPositionTags = list(birthTag.iter('BIRTHPOSITION'))
    for positions in birthPositionTags:
        if 'POSITION' in positions.attrib:
            birthPositions.append(positions.attrib['POSITION'])
    print("birth positions: {}".format(birthPositions))
    
    birthPlaceTags = list(birthTag.iter('PLACE'))
    birthPlaceTag = ""
    try:
        if len(birthPlaceTags) > 0:
            birthPlaceTag = birthPlaceTags[0]
            for tag in birthPlaceTag.iter():
                if tag.tag == "SETTLEMENT":
                    birthPlaceSettlement = tag.text
                elif tag.tag == "REGION":
                    birthPlaceRegion = tag.text
                elif tag.tag == "GEOG":
                    try:
                        birthPlaceGeog = tag.attrib['REG']
                    except KeyError:
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
        getChronstructTags = list(deathTagParent.iter("CHRONSTRUCT"))
        
        if len(getChronstructTags) == 0:
            getChronstructTags = list(deathTagParent.iter("SHORTPROSE"))

        if len(getChronstructTags) == 0:
            print("no CHRONSTRUCT in death found")
            sys.stdin.read(1)
            return

        if len(getChronstructTags) > 0
            firstChronstructTag = getChronstructTags[0]
            deathDateTag = list(firstChronstructTag.iter('DATE'))
            if deathDateTag == None:
                print("no date found in construct")
                deathDateTag = firstChronstructTag.find('DATESTRUCT')
            if deathDateTag == None:
                print("still none")
            deathDate = deathDateTag.attrib['VALUE']
    except (AttributeError) as e:
        print("Death information not found. person probably still alive")
        print("error: ", e)
        # sys.stdin.read(1)
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
            try:
                thisCause = causes.attrib['REG']
                if thisCause is not None:
                    deathCauses.append(thisCause)
            except KeyError:
                deathCauses.append(causes.text)
        print("death causes: {}".format(deathCauses))          

    # PLACE OF DEATH
    deathPlaceTags = (firstChronstructTag.findall('CHRONPROSE/PLACE/'))
    if len(deathPlaceTags) > 0:
        for tag in deathPlaceTags:
            if tag.tag == "SETTLEMENT":
                deathPlaceSettlement = tag.text
            elif tag.tag == "REGION":
                try:
                    deathPlaceRegion = tag.attrib['REG']
                except KeyError:
                    deathPlaceRegion = tag.text
            elif tag.tag == "GEOG":
                try:
                    deathPlaceGeog = tag.attrib['REG']
                except KeyError:
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
            memberRelation = familyMember.attrib['RELATION']
            for thisTag in familyMember.iter():
                # print(thisTag)
                if thisTag.tag == "NAME" and thisTag.attrib['STANDARD'] != SOURCENAME and memberName == "":
                    memberName = thisTag.attrib['STANDARD']
                elif thisTag.tag == "JOB":
                    try:
                        job=""
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
        # print("==========================================================")
    
    # print("\n\n+++++++++++++++++++++++++++++")
    # print("Listed Below are members extracted from the biography that are known to be related to %s\n+++++++++++++++++++++++++++++" %SOURCENAME)
    print("----------- ",SOURCENAME.strip(),"'s Family Members -----------")
    printMemberInfo(listOfMembers)
    print("")

    # getBirthAndDeath(myRoot2)


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
    peopleDone = 0
    for dirName, subdirlist, files in os.walk(mydir):
        for name in files:
            # if "ruskjo-b" not in name:
            #     continue
            # if "laurma-b" not in name:
            #     continue
            print('\n===========%s=================' % name)
            openFile = open(mydir+name,"r")
            xmlString = openFile.read()
            peopleDone += 1
            # getFamilyInfo(xmlString)
            getBirth(xmlString)
            getDeath(xmlString)
            # getchar()
            # print(openFile.read())
        # for file in files:
        #     print(os.path.join(subdir,file))
    # print("people looked at", peopleDone)



