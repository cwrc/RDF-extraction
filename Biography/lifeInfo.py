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
        if other_attributes:
            self.name = None
            self.uri = name_tag
        else:
            self.name = name_tag.get("STANDARD")
            self.uri = utilities.get_name_uri(name_tag)

        # TODO possibly mapping to get relationship
        self.predicate = utilities.create_cwrc_uri(relationship)

    def to_triple(self, context):
        g = utilities.create_graph()
        g.add((self.uri, RDF.type, utilities.create_cwrc_uri("NaturalPerson")))
        g.add((context.uri, self.predicate, self.uri))
        if self.name:
            g.add((self.uri, RDFS.label, Literal(self.name)))
        return g

    def __str__(self):
        string = "\tURI: " + str(self.uri) + "\n"
        string += "\tname: " + str(self.name) + "\n"
        string += "\tpredicate: " + str(self.predicate) + "\n"
        string += "\tvalue: " + str(self.value) + "\n"

        return string


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


def find_relationships(tag, person, relation):
    predicate_map = {
        "EROTICYES": "eroticRelationship",
        "EROTICPOSSIBLY": "possiblyEroticRelationship",
        "EROTICNO": "nonEroticRelationship",
        None: "intimateRelationship"
    }
    relationships = []
    if relation is None:
        people_found = utilities.get_people(tag)
        if person.uri in people_found:
            people_found.remove(person.uri)
        if len(people_found) == 1:
            logger.info(str(people_found[0]) + "-->" + str(relation) + " of " + person.name)
            relationships.append(Person(people_found[0], predicate_map[relation], True))

    else:
        relationships = find_friends(tag, person, predicate_map[relation])

    return relationships


def extract_relationships(tag_list, context_type, person, list_type="paragraphs"):
    """ Creates the interpersonal relation and ascribes them to the person along
        with the associated contexts and event
    """
    global context_count
    global event_count
    CONTEXT_TYPE = get_context_type("INTIMATERELATIONSHIPS")
    EVENT_TYPE = get_event_type("INTIMATERELATIONSHIPS")

    for tag in tag_list:
        temp_context = None
        relationship_list = None
        context_count += 1
        context_id = person.id + "_" + CONTEXT_TYPE + "_" + str(context_count)
        relationship_list = find_relationships(tag, person, context_type)
        if relationship_list:
            temp_context = Context(context_id, tag, "INTIMATERELATIONSHIPS")
            temp_context.link_triples(relationship_list)
        else:
            temp_context = Context(context_id, tag, "INTIMATERELATIONSHIPS", "identifying")

        if list_type == "events":
            event_count += 1
            event_title = person.name + " - " + "Intimate Relationship Event"
            event_uri = person.id + "_IntimateRelationshipEvent_" + str(event_count)
            temp_event = Event(event_title, event_uri, tag, EVENT_TYPE)
            temp_context.link_event(temp_event)
            person.add_event(temp_event)

        person.add_context(temp_context)


def extract_intimate_relationships_data(bio, person):
    relationship_tags = bio.find_all('INTIMATERELATIONSHIPS')
    global context_count
    global event_count
    context_count = 0
    event_count = 0
    for tag in relationship_tags:
        relation = tag.get("EROTIC")
        paragraphs = tag.find_all("P")
        events = tag.find_all("CHRONSTRUCT")
        extract_relationships(paragraphs, relation, person)
        extract_relationships(events, relation, person, "events")


def find_friends(tag, person, predicate="interpersonalRelationshipWith"):
    friends = []
    names = tag.find_all("NAME")
    for x in names:
        friends.append(Person(x, predicate))
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


def create_family_map(path=None):
    # Create better searching mechanism
    if not path:
        path = '../data/family_mapping.csv'
    with open(path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        for row in reader:
            if row[0] not in FAMILY_MAP:
                FAMILY_MAP[row[0]] = row[1]

FAMILY_MAP = {}
create_family_map()


def extract_family_data(bio, person):
    # TODO: create duplicate contexts implying inverse operations
    # Acquire occupations
    # TODO: Extract family members in a certain orders
    context_count = 1
    event_count = 1
    family_tags = bio.find_all("FAMILY")

    for family_tag in family_tags:
        member_tags = family_tag.find_all("MEMBER")

        for member_tag in member_tags:
            family_members = []
            relation = FAMILY_MAP[member_tag["RELATION"]]
            context_id = person.id + "_FamilyContext_" + str(context_count)
            temp_context = Context(context_id, member_tag, "FAMILY")

            # Finding family member
            people_found = utilities.get_people(member_tag)
            if person.uri in people_found:
                people_found.remove(person.uri)
            if len(people_found) == 1:
                logger.info(str(people_found[0]) + "-->" + relation + " of " + person.name)
                family_members.append(Person(people_found[0], relation, True))

            # Creating family events
            events_tags = member_tag.find_all("CHRONSTRUCT")
            family_events = []
            for x in events_tags:
                event_title = person.name + " - Family Event (" + relation + ")"
                event_uri = person.id + "_FamilyEvent_" + str(event_count)
                family_events.append(Event(event_title, event_uri, x, "FamilyEvent"))
                event_count += 1

            temp_context.link_triples(family_members)
            for x in family_events:
                temp_context.link_event(x)
                person.add_event(x)

            person.add_context(temp_context)
            context_count += 1

        if len(member_tags) == 0:
            context_id = person.id + "_FamilyContext_" + str(context_count)
            temp_context = Context(context_id, family_tag, "FAMILY")
            events_tags = family_tag.find_all("CHRONSTRUCT")
            family_events = []

            for x in events_tags:
                event_title = person.name + " - Family Event"
                event_uri = person.id + "_FamilyEvent_" + str(event_count)
                family_events.append(Event(event_title, event_uri, x, "FamilyEvent"))
                event_count += 1

            person.add_context(temp_context)
            context_count += 1


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
        # bagnen
        extract_family_data(soup, person)
        extract_intimate_relationships_data(soup, person)

        # extract_cohabitants(soup, person)
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
