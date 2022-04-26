from Utils import utilities, event
from Utils.context import Context, get_context_type, get_event_type
from Utils.event import Event
from Utils.activity import Activity
# from Utils.place import Place
import csv
from bs4 import Tag
import occupation
from rdflib import RDF, RDFS, Literal
from culturalForm import get_mapped_term
import rdflib
numtags = 0

logger = utilities.config_logger("relationships",verbose=0)

class Person(object):
    """docstring for a general Person with a social/familar relation to biographee"""

    def __init__(self, name, relationship, other_attributes=None):
        super(Person, self).__init__()
        if type(name) is rdflib.term.URIRef:
            self.name = None
            self.alt_name = None
            self.uri = name
        elif type(name) is Tag and name.name == "NAME":
            self.name = name.get("STANDARD")
            self.alt_name = name.get_text()
            self.uri = utilities.get_name_uri(name)
        else:
            logger.error("Unexpected type for name parameter:" +
                         str(type(name)) + ": " + str(name))

        if other_attributes:
            logger.info("Other Attributes: " +
                        str(other_attributes) + " is unhandled ")

        self.predicate = utilities.create_cwrc_uri(relationship)

    def to_triple(self, context):
        g = utilities.create_graph()
        g.add((self.uri, RDF.type, utilities.create_cwrc_uri("NaturalPerson")))
        g.add((context.uri, self.predicate, self.uri))
        if self.name:
            g.add((self.uri, RDFS.label, Literal(self.name)))
        if self.alt_name:
            g.add(
                (self.uri, utilities.NS_DICT["skos"].altLabel, Literal(self.alt_name)))

        return g

    def __str__(self):
        string = "\tURI: " + str(self.uri) + "\n"
        string += "\tname: " + str(self.name) + "\n"
        string += "\tpredicate: " + str(self.predicate) + "\n"
        return string

def create_marital_status(tagname):
    return utilities.GeneralRelation(utilities.create_cwrc_uri("maritalStatusChange"), utilities.create_cwrc_uri(tagname.lower()))

def find_marital_status(tag):
    tags = tag.find_all("MARRIAGE", limit=1) + tag.find_all("SEPARATION",
                                                            limit=1) + tag.find_all("DIVORCE", limit=1)
    return [create_marital_status(x.name) for x in tags]

def find_children(tag):
    count = []
    for x in tag.find_all("CHILDREN"):
        if "NUMBER" in x.attrs:
            count.append(x["NUMBER"])

    if count == []:
        return None
    else:
        return count

def find_childlessness(tag):
    tags = tag.find_all("CHILDLESSNESS")
    childlessness_words = {
        "birthControl": ["contraception", "birth control", "family planning"],
        "adoption": ["adopted", "adoption"],
        "childlessness": ["childless", "no children", "no surviving children", "none survived", "no child alive", "did not have any children", "they had none", "decided not to have children"],
        "miscarriage": ["miscarriage", "miscarriages", "miscarried"],
        "stillbirth": ["stillborn", "still birth", "stillbirth"],
        "abortion": ["abortion", "aborted"],
        "venerealDisease":["syphilis", "venereal", "VD"]
    }
    childlessness = []
    for x in tags:
        keyword_found = False
        for reproductiveHistory in childlessness_words.keys():
            if any(word in x.text for word in childlessness_words[reproductiveHistory]):
                keyword_found =True
                childlessness.append(utilities.GeneralRelation(utilities.create_cwrc_uri(
                    "reproductiveHistory"), utilities.create_cwrc_uri(reproductiveHistory)))
                print(reproductiveHistory)

        if not keyword_found:
            childlessness.append(utilities.GeneralRelation(utilities.create_cwrc_uri(
                "unspecifiedReproductiveHistory"), utilities.create_cwrc_uri("unspecifiedReproductiveHistory")))
            input()

    return childlessness


def find_relationships(tag, person, relation):
    predicate_map = {
        "EROTICYES": "eroticRelationship",
        "EROTICPOSSIBLY": "possiblyEroticRelationship",
        "EROTICNO": "nonEroticRelationship",
        None: "intimateRelationship"
    }
    relationships = []
    if relation is None:
        people_found = utilities.get_other_people(tag,person)
        if len(people_found) == 1:
            logger.info(str(people_found[0]) + "-->" + str(relation) + " of " + person.name)
            relationships.append(Person(people_found[0], predicate_map[relation], True))

    else:
        relationships = find_friends(tag, person, predicate_map[relation])

    return relationships

def get_attributes(entities):
    attributes = {}
    for x in entities:
        print(x)
        if x.predicate in attributes:
            attributes[x.predicate].append(x.uri)
        else:
            attributes[x.predicate] = [x.uri]
    return attributes

def extract_relationships(tag_list, context_type, person, list_type="paragraphs"):
    """ Creates the interpersonal relation and ascribes them to the person along
        with the associated contexts and event
    """
    global context_count
    global event_count
    tag_name = "INTIMATERELATIONSHIPS"

    CONTEXT_TYPE = get_context_type(tag_name)
    EVENT_TYPE = get_event_type(tag_name)

    for tag in tag_list:
        temp_context = None
        relationship_list = None
        context_count += 1
        context_id = person.id + "_" + CONTEXT_TYPE + "_" + str(context_count)
        relationship_list = find_relationships(tag, person, context_type)
        attributes = get_attributes(relationship_list)


        if relationship_list:
            temp_context = Context(context_id, tag, tag_name,pattern="relationships")
            event_count = 1
            participants = None
            
            for x in attributes.keys():
                temp_attr = {x:attributes[x]}
       
                activity_id = context_id.replace("Context","Event") + "_"+ str(event_count)
                label = f"Intimate Relationship Event: {utilities.split_by_casing(str(x).split('#')[1]).lower()}"
                activity = Activity(person, label, activity_id, tag, activity_type="generic+", attributes=temp_attr)
                activity.event_type.append(utilities.create_cwrc_uri(get_event_type(tag_name)))
                print(temp_attr)
                print(activity.event_type)

                if participants:
                    activity.participants = participants
                temp_context.link_activity(activity)
                person.add_activity(activity)
                event_count+=1
            
        else:
            temp_context = Context(context_id, tag, tag_name, "identifying")


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
    companion_tags = tag.find_all("LIVESWITH")
    companion_names = [y for x in companion_tags for y in x.find_all("NAME")]

    for x in names:
        if x not in companion_names:
            friends.append(Person(x, predicate))
        else:
            friends.append(Person(x, "cohabitant"))
    
    return list(filter(lambda a: a.uri != person.uri and a.uri not in person.biographers, friends))


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
    if not path:
        path = '../data/family_mapping.csv'
    with open(path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        for row in reader:
            if row[0] not in FAMILY_MAP:
                FAMILY_MAP[row[0]] = {"Predicate": row[1], "MALE": row[2],
                                      "FEMALE": row[3], "NEUTRAL": row[4], "SEX": row[5], "CIDOC":row[6]}


FAMILY_MAP = {}
create_family_map()
symmetric_relations = ["interpersonalRelationshipWith", "cousin", "partner"]

def get_all_members(bio,person):
    member_tags = bio.find_all("MEMBER")
    family_tree = {}
    for x in member_tags:
        peeps = utilities.get_other_people(x,person)
        peeps = [y for y in peeps if y not in person.biographers]
        
        if x["RELATION"] in family_tree:
            family_tree[x["RELATION"]].append(peeps)
        else:
            family_tree[x["RELATION"]] = (peeps)
    person.family_members = family_tree

def extract_family_data(bio, person):
    # TODO: create duplicate contexts implying inverse operations
    """
    TODO: Extract family members in a certain orders
    Parents, siblings, then partners, other relatives
    """
    get_all_members(bio,person)

    context_count = 1
    event_count = 1

    # NOTE: Will need to update this when schema changes, sex will be in culturalform tag
    # <GENDER GENDERIDENTITY="WOMAN"/>

    sex = utilities.get_sex(bio)

    if sex not in ["FEMALE", "MALE"]:
        sex = "NEUTRAL"

    # maybe best approach is to create family tree then go about creating the contexts? 
    get_all_members(bio, person)
    family_tags = bio.find_all("FAMILY")

    for family_tag in family_tags:
        member_tags = family_tag.find_all("MEMBER")
        for member_tag in member_tags:
            family_members = []
            relation = FAMILY_MAP[member_tag["RELATION"]]["Predicate"]
            context_id = person.id + "_FamilyContext_" + str(context_count)
            temp_context = Context(context_id, member_tag, "FAMILY")

            # Finding family member
            people_found = utilities.get_other_people(member_tag,person)
            marital_statuses = find_marital_status(member_tag)
            child_count = find_children(member_tag)
            family_members += find_childlessness(member_tag)

            if child_count:
                for x in child_count:
                    family_members.append(utilities.GeneralRelation(utilities.create_cwrc_uri(
                        "children"), rdflib.term.Literal(int(x), datatype=rdflib.namespace.XSD.int)))

            print(people_found)
            print(len(people_found))
            # Cleaning people found
            if person.uri in people_found:
                people_found.remove(person.uri)
            print(len(people_found))
            for x in people_found:
                if x in person.biographers:
                    people_found.remove(x)

            # Replace with more sopshisticated mapping
            if people_found:
                people_found = [people_found[0]]
            if len(people_found) == 1:
                print(member_tag["RELATION"])
                print(people_found[0])
                print(FAMILY_MAP[member_tag["RELATION"]])
                if str(people_found[0]) in utilities.WRITER_MAP and utilities.WRITER_MAP[str(people_found[0])]["SEX"] != FAMILY_MAP[member_tag["RELATION"]]["SEX"]:
                    # Creating placeholder
                    if relation != "interpersonalRelationshipWith":
                        people_found[0] = person.uri + "_PLACEHOLDER_"+ relation
                elif str(people_found[0]) in utilities.WRITER_MAP:
                    print(utilities.WRITER_MAP[str(people_found[0])])
                    print(utilities.WRITER_MAP[str(people_found[0])]["SEX"])
                    print(person.family_members)
                
                log_str = person.id + "\n"
                print(relation)
                log_str += "\t" + person.uri.split("/")[-1] + " --" + relation + "--> " + \
                    str(people_found[0]).split("/")[-1] + "\n"

                family_members.append(Person(people_found[0], relation))
                if relation in person.family_members:
                    person.family_members[relation].append(people_found[0])
                else:
                    person.family_members[relation] = [people_found[0]]

                # Creating context for relative
                relative_triples = occupation.find_occupations(member_tag)
                cohabitant_tag = member_tag.find("LIVESWITH")
                if cohabitant_tag:
                    relative_triples.append(Person(person.uri, "cohabitant"))

                if relation in symmetric_relations:
                    relative_triples.append(Person(person.uri, relation))
                else:
                    relation = FAMILY_MAP[member_tag["RELATION"]][sex]
                    relative_triples.append(Person(person.uri, relation))
                    logger.warning("Need to invert relation:" + relation)

                log_str += "\t" + str(people_found[0]).split("/")[-1] + " --" + \
                    relation + "--> " + person.uri.split("/")[-1] + "\n"
                logger.info(log_str)

                if marital_statuses:
                    if member_tag["RELATION"] in ["HUSBAND", "WIFE", "PARTNER"]:
                        family_members += marital_statuses
                        relative_triples += marital_statuses
                    else:
                        relative_triples += marital_statuses

                if FAMILY_MAP[member_tag["RELATION"]]["SEX"] in ["FEMALE", "MALE"]:
                    gender = get_mapped_term(
                        "Gender", FAMILY_MAP[member_tag["RELATION"]]["SEX"])
                    relative_triples.append(utilities.GeneralRelation(
                        utilities.create_cwrc_uri("gender"), gender))

                if relative_triples:
                    context_count += 1
                    context_id = person.id + \
                        "_FamilyContext_" + str(context_count)
                    relative_context = Context(context_id, member_tag, "FAMILY",
                                               subject_uri=people_found[0], target_uri=temp_context.target_uri, id_context=temp_context.identifying_uri)
                    relative_context.link_triples(relative_triples)
                    person.add_context(relative_context)


            # Creating family events
            events_tags = member_tag.find_all("CHRONSTRUCT")
            family_events = []
            for x in events_tags:
                event_title = person.name + " - Family Event (" + relation + ")"
                event_uri = person.id + "_FamilyEvent_" + str(event_count)
                family_events.append(event.Event(event_title, event_uri, x, "FamilyEvent"))
                event_count += 1

            temp_context.link_triples(family_members)
            for x in family_events:
                temp_context.link_event(x)
                person.add_event(x)

            person.add_context(temp_context)
            context_count += 1

        if len(member_tags) == 0:
            triples = []
            child_count = find_children(family_tag)
            triples += find_childlessness(family_tag)
            
            if child_count:
                for x in child_count:
                    triples.append(utilities.GeneralRelation(utilities.create_cwrc_uri(
                        "children"), rdflib.term.Literal(int(x), datatype=rdflib.namespace.XSD.int)))
            
            context_id = person.id + "_FamilyContext_" + str(context_count)
            temp_context = Context(context_id, family_tag, "FAMILY")
            temp_context.link_triples(triples)

            events_tags = family_tag.find_all("CHRONSTRUCT")
            family_events = []

            for x in events_tags:
                event_title = person.name + " - Family Event"
                event_uri = person.id + "_FamilyEvent_" + str(event_count)
                family_events.append(event.Event(event_title, event_uri, x, "FamilyEvent"))
                event_count += 1

            person.add_context(temp_context)
            context_count += 1




def main():
    from bs4 import BeautifulSoup
    from biography import Biography
    extraction_mode, file_dict = utilities.parse_args(
        __file__, "relationships", logger)
    print("-" * 200)
    

    uber_graph = utilities.create_graph()

    for filename in file_dict.keys():
        with open(filename) as f:
            soup = BeautifulSoup(f, 'lxml-xml')

        person_id = filename.split("/")[-1][:6]

        print(filename)
        print(file_dict[filename])
        print(person_id)
        print("*" * 55)

        person = Biography(person_id, soup)
        # extract_family_data(soup, person)
        # extract_friend_data(soup, person)
        extract_intimate_relationships_data(soup, person)

        graph = person.to_graph()

        utilities.create_individual_triples(
            extraction_mode, person, "relationships")
        utilities.manage_mode(extraction_mode, person, graph)

        uber_graph += graph

    logger.info(str(len(uber_graph)) + " triples created")
    if extraction_mode.verbosity >= 0:
        print(str(len(uber_graph)) + " total triples created")

    utilities.create_uber_triples(extraction_mode, uber_graph, "relationships")
    logger.info("Time completed: " + utilities.get_current_time())

if __name__ == "__main__":
    main()
