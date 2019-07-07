from classes import *
from stringAndMemberFunctions import *
from Utils import utilities
from Utils.context import Context, get_context_type, get_event_type
from Utils.event import get_date_tag, Event, format_date
from Utils.place import Place
import csv
import os
from occupation import Occupation
from rdflib import RDF, RDFS, Literal
numtags = 0

logger = utilities.config_logger("relationships")


class Person(object):
    """docstring for a general Person with a social/familar relation to biographee"""

    def __init__(self, name_tag, relationship, other_attributes=None):
        super(Person, self).__init__()
        self.name = name_tag.get("STANDARD")
        self.uri = utilities.get_name_uri(name_tag)
        # TODO possibly mapping to get relationship
        self.predicate = utilities.create_cwrc_uri(relationship)

    def to_triple(self, context):
        g = utilities.create_graph()
        g.add((self.uri, RDFS.label, Literal(self.name)))
        g.add((self.uri, RDF.type, utilities.create_cwrc_uri("NaturalPerson")))
        g.add((context.uri, self.predicate, self.uri))
        return g

    def __str__(self):
        string = "\tURI: " + str(self.uri) + "\n"
        string += "\tname: " + str(self.name) + "\n"
        string += "\tpredicate: " + str(self.predicate) + "\n"
        string += "\tvalue: " + str(self.value) + "\n"

        return string


# Get g information about the subject
# ------ Example ------
# birth date:  1873-12-07
# birth positions: ['ELDEST']
# birth place: Gore, Virginia, USA


# checks if child's name is available in children tag
def extract_children(xmlString, person):
    root = xmlString.BIOGRAPHY
    childrenTag = root.find_all('CHILDREN')
    childrenList = []

    for child in childrenTag:
        if "NUMBER" in child.attrs:
            print("contains number of child: ", child["NUMBER"])
            childType = "numberOfChildren"
            numChild = child["NUMBER"]

            childrenList.append(ChildStatus(childType, numChild))

    person.children_list = childrenList


def extract_childlessness(xmlString, person):
    root = xmlString.BIOGRAPHY
    childrenTag = root.find_all('CHILDLESSNESS')
    childlessList = []
    # global numtags
    for tag in childrenTag:
        # ElemPrint(tag)

        # if any(miscarriageWord in getOnlyText(tag) for miscarriageWord in
        #     ["miscarriage","miscarriages","miscarried"]):
        #     childlessList.append(ChildlessStatus("miscarriage"))
        #
        # elif any(stillbirthWord in getOnlyText(tag) for stillbirthWord in
        #     ["stillborn","still birth"]):
        #     childlessList.append(ChildlessStatus("stillbirth"))
        #     # one still birth
        #
        # elif any(abortionWord in getOnlyText(tag) for abortionWord in
        #     ["abortion","aborted"]):
        #     childlessList.append(ChildlessStatus("abortion"))
        #     # no entries has this

        if any(birthControlWord in getOnlyText(tag) for birthControlWord in
               ["contraception"]):
            childlessList.append(ChildlessStatus("birth control"))
            # no entries has this

        # elif any(veneralDisease in getOnlyText(tag) for veneralDisease in
        #     ["syphilis","veneral","VD"]):
        #     childlessList.append(ChildlessStatus("venereal disease"))
        #     # 2 entries have this

        elif any(adoptionWord in getOnlyText(tag) for adoptionWord in
                 ["adopted", "adoption"]):
            childlessList.append(ChildlessStatus("adoption"))
            # 8 entries have this

        elif any(childlessWord in getOnlyText(tag) for childlessWord in
                 ["childless", "no children", "no surviving children"]):
            childlessList.append(ChildlessStatus("childlessness"))
            # 131 entries have this

        else:
            childlessList.append(ChildlessStatus("childlessness"))
            # numtags += 1
            # 69 entries

        print("------------")

    # return childlessList
    person.childless_list = childlessList


def extract_cohabitants(xmlString, person):
    root = xmlString.BIOGRAPHY
    sourcePerson = findTag(root, "DIV0 STANDARD").text
    tagToFind = root.find_all("LIVESWITH")

    listToReturn = []

    for instance in tagToFind:
        names = getAllNames(instance.find_all("NAME"), sourcePerson)
        for name in names:
            listToReturn.append(Cohabitant(name))

    person.cohabitants_list = listToReturn


def getSexualityContexts(xmlString):
    root = xmlString.BIOGRAPHY
    tagToFind = allTagsAllChildren(root, "SEXUALITY")
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


def extract_intimate_relationships(xmlString, person):
    root = xmlString.BIOGRAPHY
    irTag = root.find_all('INTIMATERELATIONSHIPS')
    intimateRelationships = []
    sourcePerson = person.name
    id = 1
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

            context_id = person.id + "_IntimateRelationshipsContext_" + str(id)
            id += 1
            names = getAllNames(thisPerson.find_all("NAME"), person.name)
            if len(names) >= 1:
                print("========>", names[0])
                thisRelationship = IntimateRelationships(names[0], attr)
            else:
                thisRelationship = IntimateRelationships("intimate relationship", attr)

            tempContext = Context(context_id, thisPerson, "INTIMATERELATIONSHIPS")
            tempContext.link_triples([thisRelationship])
            intimateRelationships.append(thisRelationship)
            person.context_list.append(tempContext)
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


def extract_family(xmlString, person):

    myRoot2 = xmlString.BIOGRAPHY
    # SOURCENAME = myRoot2.newFindFunc("DIV0 STANDARD").text
    SOURCENAME = findTag(myRoot2, "DIV0 STANDARD").text
    listOfMembers = []
    fams = myRoot2.find_all('FAMILY')
    for familyTag in myRoot2.find_all('FAMILY'):

        #--------------------------------- Get husband and wife ---------------------------------
        for familyMember in familyTag.find_all("MEMBER"):
            if familyMember['RELATION'] in ["HUSBAND", "WIFE"]:
                if len(familyMember.find_all()) == 1:
                    continue
                else:
                    listOfMembers = getMemberInfo(familyMember, listOfMembers, SOURCENAME)

        #--------------------------------- get children ---------------------------------
        for familyMember in familyTag.find_all("MEMBER"):
            if familyMember['RELATION'] in ["SON", "DAUGHTER", "STEPSON", "STEPDAUGHTER"]:
                if len(familyMember.find_all()) == 1:
                    continue
                else:
                    listOfMembers = getMemberChildInfo(familyMember, listOfMembers, SOURCENAME)

        #--------------------------------- get others ---------------------------------
        for familyMember in familyTag.find_all('MEMBER'):
            finds = familyMember.find_all()
            if familyMember['RELATION'] in ["HUSBAND", "WIFE", "SON", "DAUGHTER", "STEPSON", "STEPDAUGHTER"] or len(iterListAll(familyMember)) == 1:
                continue
            else:
                listOfMembers = getMemberInfo(familyMember, listOfMembers, SOURCENAME)

    print("----------- ", SOURCENAME.strip(), "'s Family Members -----------")
    # printMemberInfo(listOfMembers)
    # print("")
    # return rearrangeSourceName(SOURCENAME),listOfMembers
    # return SOURCENAME,listOfMembers
    person.family_list = listOfMembers


def find_friends(tag, person):
    friends = []
    names = tag.find_all("NAME")
    for x in names:
        friends.append(Person(x, "interpersonalRelationshipWith"))
    return list(filter(lambda a: a.uri != person.uri, friends))


def extract_friends(tag_list, context_type, person, list_type="paragraphs"):
    """ Creates the interpersonal relation and ascribes them to the person along
        with the associated contexts and event
    """
    global context_count
    global event_count
    CONTEXT_TYPE = get_context_type("FRIENDSASSOCIATES")
    EVENT_TYPE = get_event_type("FRIENDSASSOCIATES")

    for tag in tag_list:
        temp_context = None
        friend_list = None
        context_count += 1
        context_id = person.id + "_" + CONTEXT_TYPE + "_" + str(context_count)
        friend_list = find_friends(tag, person)
        if friend_list:
            temp_context = Context(context_id, tag, "FRIENDSASSOCIATES")
            temp_context.link_triples(friend_list)
        else:
            temp_context = Context(context_id, tag, "FRIENDSASSOCIATES", "identifying")

        if list_type == "events":
            event_count += 1
            event_title = person.name + " - " + "Friends and Associates Event"
            event_uri = person.id + "_FriendsAndAssociatesEvent_" + str(event_count)
            temp_event = Event(event_title, event_uri, tag, EVENT_TYPE)
            temp_context.link_event(temp_event)
            person.add_event(temp_event)

        person.add_context(temp_context)


def extract_friend_data(bio, person):
    friends = bio.find_all("FRIENDSASSOCIATES")
    global context_count
    global event_count
    context_count = 0
    event_count = 0
    for friend in friends:
        paragraphs = friend.find_all("P")
        events = friend.find_all("CHRONSTRUCT")
        extract_friends(paragraphs, "FRIENDSASSOCIATES", person)
        extract_friends(events, "FRIENDSASSOCIATES", person, "events")


def extract_family_data(bio, person):
    family_members = []
    # for tag in bio.find_all('FAMILY'):
        # for member in tag.find_all("MEMBER"):
    # Find all husband wife tags
    # children
    # other members


def main():
    from bs4 import BeautifulSoup
    import culturalForm
    from biography import Biography
    file_dict = utilities.parse_args(__file__, "family/friends")
    print("-" * 200)
    entry_num = 1

    uber_graph = utilities.create_graph()

    for filename in file_dict.keys():
        with open(filename) as f:
            soup = BeautifulSoup(f, 'lxml-xml')

        person_id = filename.split("/")[-1][:6]

        print(filename)
        print(file_dict[filename])
        print(person_id)
        print("*" * 55)

        person = Biography(person_id, soup, culturalForm.get_mapped_term("Gender", utilities.get_sex(soup)))
        extract_friend_data(soup, person)
        # extract_cohabitants(soup, person)
        # extract_family(soup, person)
        # extract_friends_associates(soup, person)
        # extract_intimate_relationships(soup, person)
        # extract_childlessness(soup, person)
        # extract_children(soup, person)

        person.name = utilities.get_readable_name(soup)
        print(person.to_file())

        temp_path = "extracted_triples/relationships_turtle/" + person_id + "_relationships.ttl"
        utilities.create_extracted_file(temp_path, person)

        uber_graph += person.to_graph()
        entry_num += 1
        print("=" * 55)

    print("UberGraph is size:", len(uber_graph))
    temp_path = "extracted_triples/relationships.ttl"
    utilities.create_extracted_uberfile(temp_path, uber_graph)

    temp_path = "extracted_triples/relationships.rdf"
    utilities.create_extracted_uberfile(temp_path, uber_graph, "pretty-xml")

if __name__ == "__main__":
    main()
