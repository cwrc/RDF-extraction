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

logger = utilities.config_logger("relationships")

RELATIONSHIP_LABELS = {
    utilities.create_uri("persrel","interpersonalRelationship"): "interpersonal relationship",
    utilities.create_uri("persrel","cohabitant"): "cohabitation relationship",
    utilities.create_uri("persrel","eroticRelationship"): "erotic relationship",
    utilities.create_uri("persrel","nonEroticRelationship"): "non-erotic relationship",
    utilities.create_uri("persrel","possiblyEroticRelationship"): "possibly erotic relationship",
    utilities.create_uri("persrel","intimateRelationship"): "intimate relationship",
}

class Role(object):
    """docstring for Role"""

    def __init__(self, activity_uri,person_uri, role_uri, other_attributes=None):
        super(Role, self).__init__()
        self.person_uri = person_uri
        cwrc_uri = person_uri if "cwrc" in str(person_uri) else utilities.get_cwrc_uri(person_uri)
        self.name = utilities.get_full_name(cwrc_uri)
        self.role = role_uri
        self.role_label =role_uri.split("/")[-1].lower()
        self.uri = utilities.make_standard_uri(F"""{self.name} as {role_uri.split("/")[-1]}""")
        self.activity_uri = activity_uri

    def to_triple(self, context):
        g = utilities.create_graph()
        
        role_activity = g.resource(self.uri)
        role_activity.add(RDF.type, utilities.NS_DICT["crm"].PC14_carried_out_by)
        role_activity.add(utilities.NS_DICT["crm"]["P14.1_in_the_role_of"], self.role)
        role_activity.add(utilities.NS_DICT["crm"].P02_has_range, self.person_uri)
        role_activity.add(utilities.NS_DICT["crm"].P01_has_domain, self.activity_uri)
        role_activity.add(RDFS.label, Literal(F"{self.name} as {self.role_label}",lang="en"))
        
        
        # g.add((self.name, self.uri, self.role))
        
        
        return g

    def __str__(self):
        string = F""
        string += "person_uri: {self.person_uri}"
        string += "name: {self.name}"
        string += "role: {self.role}"
        string += "role_label: {self.role_label}"
        string += "uri: {self.uri}"
        string += "activity_uri: {self.activity_uri}"

class Person(object):
    """docstring for a general Person with a social/familar relation to biographee"""

    def __init__(self, name, relationship, other_attributes=None):
        super(Person, self).__init__()
        if type(name) is rdflib.term.URIRef:
            self.name = None
            self.alt_name = None
            self.uri = name
        elif type(name) is Tag and name.name == "NAME":
            self.name = utilities.get_full_name(name)
            self.alt_name = name.get_text()
            self.uri = utilities.get_name_uri(name)
        else:
            logger.error("Unexpected type for name parameter:" +
                         str(type(name)) + ": " + str(name))

        if other_attributes:
            logger.info("Other Attributes: " +
                        str(other_attributes) + " is unhandled ")

        self.predicate = utilities.create_uri("persrel",relationship)

    def to_triple(self, context):
        g = utilities.create_graph()
        if self.name:
            g.add((self.uri, RDFS.label, Literal(self.name, lang="en")))
        if self.alt_name:
            g.add(
                (self.uri, utilities.NS_DICT["skos"].altLabel, Literal(self.alt_name, lang="en")))

        return g

    def __str__(self):
        string = F"""
name: {self.name}
alt_name: {self.alt_name}
uri: {self.uri}
predicate: {self.predicate}
        """

        return string

def create_marital_status(tagname):
    return utilities.GeneralRelation(utilities.create_uri("biography","maritalStatusChange"), utilities.create_uri("biography",tagname.lower()))

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
                childlessness.append(utilities.GeneralRelation(utilities.create_uri("biography",
                    "reproductiveHistory"), utilities.create_uri("biography",reproductiveHistory)))
                print(reproductiveHistory)

        if not keyword_found:
            childlessness.append(utilities.GeneralRelation(utilities.create_uri("biography",
                "unspecifiedReproductiveHistory"), utilities.create_uri("biography","unspecifiedReproductiveHistory")))
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
            relationships.append(Person(people_found[0], predicate_map[relation], True))

    else:
        relationships = find_friends(tag, person, predicate_map[relation])

    return relationships

def get_attributes(entities):
    attributes = {}
    for x in entities:
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

        # Sometimes includes cohabitant as well
        attributes = get_attributes(relationship_list)

        # Only extracting intimate relation if there is one name, aiming for precision here
        if relationship_list:
            temp_context = Context(context_id, tag, tag_name,pattern="relationships")
            event_count = 1
            participants = None
            
            for x in attributes.keys():
                if x != utilities.create_uri("persrel","cohabitant") and len(attributes[x])>1:
                    logger.warning(F"{RELATIONSHIP_LABELS[x]}: too many people to extract: {attributes[x]}")
                    continue
                for relationship in attributes[x]:
                    if "temp.lincsproject" in str(relationship):
                        logger.warning(F"NO EXTRACTION: Need to create placeholder for: {relationship}")  
                        continue

                    temp_attr = {x:[]}
                    active_participants = []
                    active_participants.append(relationship)
                    active_participants.append(person.uri)
                    
                    activity_id = context_id.replace("Context","Event") + "_"+ str(event_count)
                    relationship_cwrc_uri = relationship if "cwrc" in str(relationship) else utilities.get_cwrc_uri(relationship)
                    label = f"{RELATIONSHIP_LABELS[x]} with {utilities.get_full_name(relationship_cwrc_uri)}"
                    activity = Activity(person, label, activity_id, tag, activity_type="generic", attributes=temp_attr)

                    activity.participants = []
                    activity.active_participants = active_participants
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


def find_friends(tag, person, predicate="interpersonalRelationship"):
    friends = []
    names = tag.find_all("NAME")
    companion_tags = tag.find_all("LIVESWITH")
    companion_names = [y for x in companion_tags for y in x.find_all("NAME")]

    for x in names:
        if x not in companion_names:
            friends.append(Person(x, predicate))
        else:
            friends.append(Person(x, "cohabitant"))
    
    return list(filter(lambda a: a.uri != person.uri and a.uri not in person.biographers and a.uri not in person.parents, friends))


def extract_friends(tag_list, context_type, person, list_type="paragraphs"):
    """ Creates the interpersonal relation and ascribes them to the person along
        with the associated contexts and event
    """
    global context_count
    global event_count
    tag_name = "FRIENDSASSOCIATES"

    CONTEXT_TYPE = get_context_type(tag_name)
    EVENT_TYPE = get_event_type(tag_name)

    for tag in tag_list:
        temp_context = None
        friend_list = None
        context_count += 1
        context_id = person.id + "_" + CONTEXT_TYPE + "_" + str(context_count)
        friend_list = find_friends(tag, person)
        attributes = get_attributes(friend_list)

        if friend_list:
            temp_context = Context(context_id, tag, tag_name, pattern="relationships")
            event_count = 1
            temp_context.link_triples(friend_list)
            for x in attributes.keys():
                for relationship in attributes[x]:
                    if "temp.lincsproject" in str(relationship):
                        logger.warning(F"NO EXTRACTION: Need to create placeholder for: {relationship}")  
                        continue
                    active_participants = [relationship, person.uri]
                    temp_attr = {x:[]}
                     
                    activity_id = context_id.replace("Context","Event") + "_"+ str(event_count)
                    relationship_cwrc_uri = relationship if "cwrc" in str(relationship) else utilities.get_cwrc_uri(relationship)
                    label = f"{RELATIONSHIP_LABELS[x]} with {utilities.get_full_name(relationship_cwrc_uri)}"
                    
                    activity = Activity(person, label, activity_id, tag, activity_type="generic", attributes=temp_attr)
                    activity.participants = []
                    activity.active_participants = active_participants
                    
                    temp_context.link_activity(activity)
                    person.add_activity(activity)
                    event_count+=1
       
        else:
            temp_context = Context(context_id, tag, tag_name, "identifying")

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
                                      "FEMALE": row[3], "NEUTRAL": row[4], "SEX": row[5], "CIDOC":row[6], "Label":row[7]}


FAMILY_MAP = {}
create_family_map()
symmetric_relations = ["interpersonalRelationship", "cousin", "partner"]

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
    # get_all_members(bio,person)

    context_count = 1
    event_count = 1

    # maybe best approach is to create family tree then go about creating the contexts? 
    # get_all_members(bio, person)
    family_tags = bio.find_all("FAMILY")

    for family_tag in family_tags:
        member_tags = family_tag.find_all("MEMBER")
        for member_tag in member_tags:
            family_members = []
            relation = FAMILY_MAP[member_tag["RELATION"]]["Predicate"]
            context_id = person.id + "_FamilyContext_" + str(context_count)
            temp_context = Context(context_id, member_tag, "FAMILY",pattern="family")

            # Finding family member
            people_found = utilities.get_other_people(member_tag,person)
            # marital_statuses = find_marital_status(member_tag)
            
            # TODO: Need to handle <CHILDREN> & <CHILDLESSNESS> tags
            # child_count = find_children(member_tag)
            # family_members += find_childlessness(member_tag)

            # if child_count:
            #     for x in child_count:
            #         family_members.append(utilities.GeneralRelation(utilities.create_cwrc_uri(
            #             "children"), rdflib.term.Literal(int(x), datatype=rdflib.namespace.XSD.int)))
            
            # Cleaning people found
            if person.uri in people_found:
                people_found.remove(person.uri)
            for x in people_found:
                if x in person.biographers:
                    people_found.remove(x)

            # Replace with more sophisticated mapping
            if people_found:
                people_found = [people_found[0]]
            if len(people_found) == 1:
                relative = people_found[0]
                if "temp.lincsproject" in str(relative):
                    logger.warning(F"NO EXTRACTION: Need to create placeholder for: {relative}")  
                    continue
                
                relative_cwrc_uri = relative if "cwrc" in str(relative) else utilities.get_cwrc_uri(relative)
                activity_id = context_id.replace("Context","Event") + "_"+ str(event_count)
                label = f"""{FAMILY_MAP[member_tag["RELATION"]]["Label"]} with {utilities.get_full_name(relative_cwrc_uri)}"""
                person_role = None
                active_participants = []
                participants = []
                roles = []
                
                activity = Activity(person, label, activity_id, member_tag, activity_type="generic")

                
                if relation == "interpersonalRelationship":
                    active_participants = [relative, person.uri]
                    activity.title = f"""{RELATIONSHIP_LABELS[utilities.create_uri("persrel","interpersonalRelationship")]} with {utilities.get_full_name(relative_cwrc_uri)}"""
                else:
                    # Determining what role to assign to the person depending on their gender (ew but needed for asymmetrical relations)
                    person_gendered_role_type = "NEUTRAL"
                    if len(person.gender) == 1:
                        if "woman" in person.gender[0]:
                            person_gendered_role_type = "FEMALE"
                        elif "man"  in person.gender[0]:
                            person_gendered_role_type = "MALE"
                        else:
                            person_gendered_role_type = "NEUTRAL"
                    person_role = FAMILY_MAP[member_tag["RELATION"]][person_gendered_role_type]
                    roles.append(Role(activity.uri, relative, utilities.create_uri("persrel",relation)))
                    roles.append(Role(activity.uri, person.uri, utilities.create_uri("persrel",person_role)))
                    activity.additional_nodes = roles
                    activity.event_type.append(utilities.create_uri("event", "FamilyEvent"))
                    

        
                activity.participants = participants
                activity.active_participants = active_participants
                
                
                temp_context.link_activity(activity)
                person.add_activity(activity)
                event_count+=1

                log_str = F"\t{person.uri} --{relation} --> {relative}\n"
                family_members.append(Person(relative, relation))
                
                if relation in person.family_members:
                    person.family_members[relation].append(relative)
                else:
                    person.family_members[relation] = [relative]
                # print(log_str)
                
                # TODO: HANDLE OCCUPATIONS of RELATIVES
                # Creating context for relative
                # relative_triples = occupation.find_occupations(member_tag)
                # cohabitant_tag = member_tag.find("LIVESWITH")
                # if cohabitant_tag:
                #     relative_triples.append(Person(person.uri, "cohabitant"))

                # if relation in symmetric_relations:
                #     relative_triples.append(Person(person.uri, relation))
                # else:
                #     relation = FAMILY_MAP[member_tag["RELATION"]][sex]
                #     relative_triples.append(Person(person.uri, relation))
                #     logger.warning("Need to invert relation:" + relation)

                # log_str += "\t" + str(people_found[0]).split("/")[-1] + " --" + \
                #     relation + "--> " + person.uri.split("/")[-1] + "\n"
                # logger.info(log_str)

                # TODO: HANDLE OCCUPATIONS of Marital Statuses
                # if marital_statuses:
                #     if member_tag["RELATION"] in ["HUSBAND", "WIFE", "PARTNER"]:
                #         family_members += marital_statuses
                #         relative_triples += marital_statuses
                #     else:
                #         relative_triples += marital_statuses

                # if FAMILY_MAP[member_tag["RELATION"]]["SEX"] in ["FEMALE", "MALE"]:
                #     gender = get_mapped_term(
                #         "Gender", FAMILY_MAP[member_tag["RELATION"]]["SEX"])
                #     relative_triples.append(utilities.GeneralRelation(
                #         utilities.create_uri("identity","gender"), gender))

                # if relative_triples:
                #     context_count += 1
                #     context_id = person.id + \
                #         "_FamilyContext_" + str(context_count)
                #     relative_context = Context(context_id, member_tag, "FAMILY",
                #                                subject_uri=people_found[0], target_uri=temp_context.target_uri, id_context=temp_context.identifying_uri)
                #     relative_context.link_triples(relative_triples)
                #     person.add_context(relative_context)



            person.add_context(temp_context)
            context_count += 1

        if len(member_tags) == 0:
            triples = []
            # child_count = find_children(family_tag)
            # triples += find_childlessness(family_tag)
            
            # if child_count:
            #     for x in child_count:
            #         triples.append(utilities.GeneralRelation(utilities.create_cwrc_uri(
            #             "children"), rdflib.term.Literal(int(x), datatype=rdflib.namespace.XSD.int)))
            
            context_id = person.id + "_FamilyContext_" + str(context_count)
            temp_context = Context(context_id, family_tag, "FAMILY","identifying")
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
        person = Biography(person_id, soup)
        
        print(F"Full Name\t | entry ID\t | CWRC URI\t | Primary URI")
        print("-" * 100)
        print(F"{person.name}\t| {person_id}\t | {person.cwrc_uri}\t | {person.uri}")
        print("*" * 100)

        extract_family_data(soup, person)
        # extract_intimate_relationships_data(soup, person)
        # # extract_friend_data(soup, person)

        graph = person.to_graph()

        utilities.create_individual_triples(
            extraction_mode, person, "relationships",graph)
        utilities.manage_mode(extraction_mode, person, graph)

        uber_graph += graph

    logger.info(str(len(uber_graph)) + " triples created")
    if extraction_mode.verbosity >= 0:
        print(str(len(uber_graph)) + " total triples created")

    utilities.create_uber_triples(extraction_mode, uber_graph, "relationships")
    logger.info("Time completed: " + utilities.get_current_time())

if __name__ == "__main__":
    main()
