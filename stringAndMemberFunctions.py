from xml.etree import ElementTree
import datetime, sys, copy
from xml.etree.ElementTree import Element
# from scrapeFamily import *
from classes import *


def getch():
    sys.stdin.read(1)



def getContexts(tagParent):
    print(tagParent)
    # tagList = []
    # for tag in tagInput:
    #     if "DIV" not in tag.tag:
    #         DIV = Element('DIV2')
    #         DIV.insert(0, tag)
    #         tagList.append(DIV)
    #     else:
    #         tagList.append(tag)
    # print("taglist: ",tagList)
    returnList = []
    # if "DIV" not in tagParent.tag:
    #     print("what is this",tagParent)
    #     getch()
    # else:
    #     print("proper what is this", tagParent)
    #     getch()
    tags = tagParent.findall("*")
    markedForRemoval = []
    foundChronstruct = False

    if len(tags) == 2:
        if tags[0].tag == "SHORTPROSE" and tags[1].tag == "CHRONSTRUCT":
            tags[0],tags[1] = tags[1],tags[0]

    tags2 = copy.deepcopy(tags)
    for i in range(0, len(tags2)):
        if foundChronstruct == False and tags2[i].tag != "CHRONSTRUCT":
            markedForRemoval.append(i)
        elif tags2[i].tag == "CHRONSTRUCT":
            foundChronstruct = True

    print(tags)
    print(markedForRemoval)

    if len(markedForRemoval) == len(tags):
        print("1. weird thing going on")
        lonePars = tagParent.findall(".//P")
        for par in lonePars:
            returnList.append(getOnlyText(par))
    else:
        i = 0

        while i < len(tags):
            if i in markedForRemoval:
                i += 1
                continue

            if len(tags) > 1:
                if i == len(tags) - 1:
                    i += 1
                    continue

                if tags[i].tag == "CHRONSTRUCT" and tags[i + 1].tag == "SHORTPROSE" and tags[i + 1].find(
                        ".//P") is not None:
                    returnList.append(getOnlyText(tags[i]) + "\n" + getOnlyText(tags[i + 1].find(
                        ".//P")))
                    print("chronstruct with paragraph next")
                    i += 1


            # print("index: ",i)
            # print("isConstruct",deathcnts[i].tag == "CHRONSTRUCT")
            # print("shortprosenext",deathcnts[i+1].tag == "SHORTPROSE")
            # print("paragraph in shortprose", deathcnts[i+1].find(".//P") != None)


                # getch()
            elif len(tags) == 1 and tags[i].tag == "CHRONSTRUCT":
                returnList.append(getOnlyText(tags[i]))
            else:
                print("2. weird thing going on")
                lonePars = tagParent.findall(".//P")
                for par in lonePars:
                    returnList.append(getOnlyText(par))
                print("list of Paragraphs2: ", lonePars)
                # getch()

            i += 1
    if len(returnList) > 0:
        print(returnList)
    return returnList

def getPlaceTagContent(place):
    placeSettlement = ""
    placeRegion     = ""
    placeGeog       = ""

    for tag in place.iter():
        if tag.tag == "SETTLEMENT":
            if "CURRENT" in tag.attrib:
                placeSettlement = tag.attrib["CURRENT"]
            elif "REG" in tag.attrib:
                placeSettlement = tag.attrib["REG"]
            else:
                placeSettlement = tag.text

        elif tag.tag == "REGION":
            if "CURRENT" in tag.attrib:
                placeRegion = tag.attrib["CURRENT"]
            elif "REG" in tag.attrib:
                placeRegion = tag.attrib["REG"]
            else:
                placeRegion = tag.text
        elif tag.tag == "GEOG":
            if "CURRENT" in tag.attrib:
                placeGeog = tag.attrib["CURRENT"]
            elif "REG" in tag.attrib:
                placeGeog = tag.attrib["REG"]
            else:
                placeGeog = tag.text

    return placeSettlement,placeRegion,placeGeog

def getContextDataMultiTag(tag1,tag2,sourcePerson):
    names = getAllNames(tag1.iter("NAME"), sourcePerson) + getAllNames(tag2.iter("NAME"), sourcePerson)
    context = getOnlyText(tag1) + "\n" + getOnlyText(tag2.find(".//P"))

    return PeopleAndContext(names,context)

def getContextData(tag,sourcePerson):
    names = getAllNames(tag.iter("NAME"),sourcePerson)
    context = getOnlyText(tag)

    return PeopleAndContext(names,context)

def getContextsAndNames(tagParent,sourcePerson):
    print(tagParent)
    returnList = []
    tags = tagParent.findall("*")
    markedForRemoval = []
    foundChronstruct = False

    if len(tags) == 2:
        if tags[0].tag == "SHORTPROSE" and tags[1].tag == "CHRONSTRUCT":
            tags[0],tags[1] = tags[1],tags[0]

    tags2 = copy.deepcopy(tags)
    for i in range(0, len(tags2)):
        if foundChronstruct == False and tags2[i].tag != "CHRONSTRUCT":
            markedForRemoval.append(i)
        elif tags2[i].tag == "CHRONSTRUCT":
            foundChronstruct = True

    print("tags: ",tags)
    print("marked for removal: ",markedForRemoval)

    if len(markedForRemoval) == len(tags):
        print("3. No Chronstsruct")
        lonePars = tagParent.findall(".//P")
        for par in lonePars:
            returnList.append(getContextData(par,sourcePerson))
    else:
        i = 0

        while i < len(tags):
            if i in markedForRemoval:
                i += 1
                continue

            if len(tags) > 1:
                if i == len(tags) - 1:
                    i += 1
                    continue

                if tags[i].tag == "CHRONSTRUCT" and tags[i + 1].tag == "SHORTPROSE" and tags[i + 1].find(
                        ".//P") is not None:
                    print("chronstruct with paragraph next")
                    returnList.append(getContextDataMultiTag(tags[i],tags[i+1],sourcePerson))
                    i += 1

            elif len(tags) == 1 and tags[i].tag == "CHRONSTRUCT":
                returnList.append(getContextData(tags[i]),sourcePerson)
                # returnList.append(PeopleAndContext(getAllNames(tags[i].iter("NAME"), sourcePerson),getOnlyText(tags[i])))
            else:
                print("4. weird thing going on")
                lonePars = tagParent.findall(".//P")
                for par in lonePars:
                    returnList.append(getContextData(par, sourcePerson))
                    # returnList.append(PeopleAndContext(getAllNames(par.iter("NAME"), sourcePerson),getOnlyText(par)))
                print("list of Paragraphs2: ", lonePars)

            i += 1
    # if len(returnList) > 0:
    #     print(returnList)
    return returnList

def getStandardUri(std_str):
    import string
    translator = str.maketrans('', '', string.punctuation.replace("-", ""))
    temp_str = std_str.translate(translator)
    temp_str = temp_str.replace(" ", "_")
    return temp_str

# from https://stackoverflow.com/questions/749796/pretty-printing-xml-in-python
# used for printing out elements nicely
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

# used for printing out elemetns
def ElemPrint(elem):
    indenter(elem)
    ElementTree.dump(elem)

# gets the text from a tag. this includes the text of 
# all the subtags
def getOnlyText(tag):
    paraText = tag.itertext()
    paragraph = ""

    for text in paraText:
        paragraph = paragraph.strip() + " " + text.strip()
    paragraph = paragraph.strip()
    
    return paragraph

# makes sure the date
# is in the correct format
def dateValidate(dateStr):
    try:
        datetime.datetime.strptime(dateStr, '%Y-%m-%d')
        return True
    except ValueError:
        return False

# prints member information
# for the list that contains
# family members
def printMemberInfo(memberList):
    for mem in memberList:
        mem.samplePrint()

# extract source name from reg
# values which are in the format
# lastname, firstname
def rearrangeSourceName(nameStr):
    # return nameStr
    # FIXME : commenting out as per Alliyya's code
    # if "," in nameStr:
    #     fullName = nameStr.split(",")
    #     return fullName[1].strip(" ") + " "+ fullName[0].strip(" ")
    # return nameStr
    return getStandardUri(nameStr)

# when titles are in a long format
# this function extracts name
def extractNameFromTitle(nameStr):
    # return nameStr
    # FIXME : commenting out as per Alliyya's code
    return getStandardUri(nameStr)
    # nameSeparation = nameStr.split(",,")
    # returnName = ""
    # if "of" in nameSeparation[-1]:
    #     fullName = nameSeparation[-2].split(",")
    #     # print("returning: ", fullName[-1])
    #     returnName = fullName[-1].strip(" ")
    # elif "," in nameSeparation[0]:
    #     fullName = nameSeparation[0].split(",")
    #     returnName = fullName[1].strip(" ") + " "+ fullName[0].strip(" ")
    #     # print(newName)
    # else:
    #     print(nameStr,"something went wrong")
    #     sys.stdin.read(1)
    # if " of " in returnName:
    #     justName = returnName.split(" of ")
    #     returnName = justName[0]
    # return returnName

# when getting children's names, this makes sure
# we are not getting the parent's name
def notParentName(personName,parentList):
    print("welcome to not parent home")
    print("parent list: ",len(parentList))
    for parent in parentList:
        print("compare ", personName, " and ", parent.memberName)
        if parent.memberName == personName:
            return False
    return True

# get all names in a tag that are not the subject's
def getAllNames(names, sourcePerson):
    otherNames = []
    for thisName in names:
        name = thisName.attrib["STANDARD"]
        # print("looking at :", name)
        if name != sourcePerson:
            otherNames.append(name)

    return otherNames

# get a name of a person by getting the first
# name that is not the source person
def getNameOfAssociate(names,sourcePerson):
    foundName = False
    otherName = ""
    for thisName in names:
        name = thisName.attrib["STANDARD"]
        # print("looking at :", name)
        if name != sourcePerson :
            foundName = True
            otherName = (name)
            break

    return foundName,otherName
def isUniqueSigAct(newAct, pastActs):
    for act in pastActs:
        act = act.job
        if newAct.replace(' ','') == act.replace(' ',''):
            return False
    return True
def getMemberName(thisTag):
    # FIXME : REMOVED CODE TO MATCH ALLIYYA'S CODE
    return thisTag.attrib["STANDARD"]
    # memberName = ""
    #
    # if ",," in thisTag.attrib['STANDARD']:
    #     memberName = extractNameFromTitle(thisTag.attrib['STANDARD'])
    #     # memberName = thisTag.text
    #     # print(memberRelation,"|,, name|",thisTag.attrib['STANDARD'])
    #     # sys.stdin.read(1)
    #     if "(" in memberName and ")" not in memberName:
    #         memberName += ")"
    # else:
    #     memberName = thisTag.attrib['STANDARD']
    #
    # return memberName

def getMemberJobs(thisTag,memberJobs):

    # memberJobs = []
    paidFamilyOccupation = False
    if "FAMILYBUSINESS" in thisTag.attrib:
        # print(thisTag.attrib)
        if thisTag.attrib["FAMILYBUSINESS"] == "FAMILYBUSINESSYES":
            paidFamilyOccupation = True
    # if "HISTORICALTERM" in thisTag.attrib:
    #     print(thisTag.attrib)
    # if "HISTORICALTERMCONTEXTDATE" in thisTag.attrib:
    #     print(thisTag.attrib)
    typeOfOccupation = ""
    if paidFamilyOccupation:
        typeOfOccupation = "familyOccupation"
    else:
        typeOfOccupation = "paidOccupation"

    if 'REG' in thisTag.attrib:
        memberJobs.append(JobSigAct(typeOfOccupation,thisTag.attrib['REG']))

    elif thisTag.text is '':
        memberJobs.append(JobSigAct(typeOfOccupation,thisTag.text))
    else:
        paraText = thisTag.itertext()
        paragraph = ""

        for text in paraText:
            paragraph = paragraph + " " + text.strip()
        paragraph = paragraph.strip()
        memberJobs.append(JobSigAct(typeOfOccupation,paragraph))

    return memberJobs

def getMemberActs(thisTag,memberSigAct):
    
    # memberSigAct = []
    # global numSigs
    # global numAdded
    # numSigs += 1

    philanthropyVolunteer = False

    if "PHILANTHROPYVOLUNTEER" in thisTag.attrib:
        philanthropyVolunteer = True
        print(thisTag.attrib)

    if philanthropyVolunteer:
        typeOfOccupation = "volunteerOccupation"
    else:
        typeOfOccupation = "normalOccupation"

    if "REG" in thisTag.attrib:
        sigAct = thisTag.attrib["REG"]
        if isUniqueSigAct(sigAct,memberSigAct):
            memberSigAct.append(JobSigAct(typeOfOccupation,sigAct))
        # numAdded += 1
    else:
        sigAct = getOnlyText(thisTag)
        if isUniqueSigAct(sigAct, memberSigAct):
            memberSigAct.append(JobSigAct(typeOfOccupation, sigAct))

    return memberSigAct
def incrementLetter(inputLetter):
    return chr(ord(inputLetter) + 1)

def uniqueMemberCheck(newMember, listOfMembers):
    uniqueMember = True
    if newMember.memberRelation == "MOTHER" or newMember.memberRelation == "FATHER":
        for addedMember in listOfMembers:
            if addedMember.memberRelation == newMember.memberRelation:
                addedMember.memberJobs      = list(set(addedMember.memberJobs).union(set(newMember.memberJobs)))
                addedMember.memberSigActs   = list(set(addedMember.memberSigActs).union(set(newMember.memberSigActs)))
                if addedMember.memberName == "" and newMember.memberName != "":
                    addedMember.memberName = newMember.memberName
                uniqueMember = False
                print("this is not a unique member")
                # getch()
    else:
        if newMember.memberName == "":
            noNameList = []
            for member in listOfMembers:
                if member.memberRelation == newMember.memberRelation and member.isNoName == True:
                    linkToMember = member
                    noNameList.append(linkToMember)

            if len(noNameList) == 0:
                newMember.isNoName = True
                newMember.noNameLetter = ''
                newMember.memberName

            elif len(noNameList) == 1:
                newMember.isNoName = True
                newMember.noNameLetter = 'B'
                noNameList[0].noNameLetter = 'A'

            elif len(noNameList) > 1:
                lastMember = noNameList[-1]
                newMember.isNoName = True
                newMember.noNameLetter = incrementLetter(lastMember.noNameLetter)

            # elif len(noNameList) == 1:

        for addedMember in listOfMembers:
            # print(newMember.memberName, "(", newMember.memberRelation,")"," vs ", addedMember.memberName,"(", addedMember.memberRelation,")")
            if newMember.memberRelation == addedMember.memberRelation and newMember.memberName == addedMember.memberName and newMember.noNameLetter == addedMember.noNameLetter:
                addedMember.memberJobs      = list(set(addedMember.memberJobs).union(set(newMember.memberJobs)))
                addedMember.memberSigActs   = list(set(addedMember.memberSigActs).union(set(newMember.memberSigActs)))
                uniqueMember = False
                print("this is not a unique member")
                # getch()


    if newMember.memberRelation != "" and uniqueMember == True:
        # print("now adding in the new member")
        listOfMembers.append(newMember)
        # getch()

    return listOfMembers

def getMemberInfo(familyMember,listOfMembers,SOURCENAME):
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

def getMemberChildInfo(familyMember,listOfMembers,SOURCENAME):
    memberRelation = familyMember.attrib['RELATION']
    memberName = ""
    memberJobs = []
    memberSigAct = []
    listOfParents = []

    for member in listOfMembers:
        # print("memberName: ", member.memberName)
        # print("memberRLTN: ", member.memberRelation)
        if member.memberRelation == "WIFE" or member.memberRelation == "HUSBAND":
            listOfParents.append(member)
            # print("added parent")
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



