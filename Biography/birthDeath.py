#!/usr/bin/python3
import rdflib
from rdflib import RDF, RDFS, Literal
from Utils import utilities
from Utils.context import Context, get_event_type
from Utils.place import Place
from Utils.activity import Activity 
from difflib import get_close_matches

# TODO
# - once resolved: https://github.com/cwrc/ontology/issues/462
# - handle multiple DEATH/BIRTH tags

logger = utilities.config_logger("birthdeath")
BURIAL_KEYWORDS = ["buried", "grave", "interred"]
count = 0
CAUSE_MAP = {}
map_attempt = 0
map_success = 0
map_fail = 0
fail_dict = {}


def clean_term(string):
    string = string.lower().replace("-", " ").strip().replace(" ", "")
    return string

def create_cause_map():
    
    import csv
    global CAUSE_MAP
    with open('../data/COD_mapping.csv', newline='', encoding="utf8") as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            temp_row = [clean_term(x) for x in row[1:]]
            CAUSE_MAP[row[0]] = (list(filter(None, temp_row)))



def get_birthposition_uris(positions):
    positions_uris = []
    if positions:
        for birth_position in positions:
            if birth_position == "ONLY":
                positions_uris.append(utilities.NS_DICT["biography"].onlyChild)
            elif birth_position == "ELDEST":
                positions_uris.append(utilities.NS_DICT["biography"].eldestChild)
            elif birth_position == "YOUNGEST":
                positions_uris.append(utilities.NS_DICT["biography"].youngestChild)
            elif birth_position == "MIDDLE:":
                positions_uris.append(utilities.NS_DICT["biography"].middleChild)
    return positions_uris

def get_attributes(person):
    attributes = {}
    if "FATHER" in person.family_members and len(person.family_members["FATHER"])==1:
        father = person.family_members["FATHER"][0]
        if father:
            attributes[utilities.NS_DICT["crm"].P97_from_father] = [father]

    if "MOTHER" in person.family_members and len(person.family_members["MOTHER"])==1:
        mother = person.family_members["MOTHER"][0]
        if mother:
            attributes[utilities.NS_DICT["crm"].P96_by_mother]= [mother]

    return attributes

def get_birth_position(tag):
    birth_positions = []
    for positions in tag.find_all('BIRTHPOSITION'):
        if 'POSITION' in positions.attrs:
            birth_positions.append(positions['POSITION'])
    birth_positions = list(set(birth_positions))
    if len(birth_positions) > 1:
        logger.info("Multiple Birth positions:" + str(birth_positions))
    return birth_positions

def extract_birth_data(bio, person):
    context_count = 1

    birth_tags = bio.find_all("BIRTH")
    if len(birth_tags) > 1:
        logger.warning("Multiple Birth tags found: " + person.name + person.id)


    for birth_tag in birth_tags:
        context_id = person.id + "_BirthContext_" + str(context_count)
        temp_context = Context(context_id, birth_tag, "BIRTH",pattern="birth")

        # create one
        activity_id = context_id.replace("Context","Event")
        # Get father and mother
        attributes = get_attributes(person)
        birth_event = Activity(person, "Birth Event", activity_id, birth_tag, activity_type="birth", attributes=attributes)

        # retrieving birthposition
        birth_positions = get_birth_position(birth_tag)
        
        # Creating birth position attribution activity if it exists
        if birth_positions:
            birth_positions = get_birthposition_uris(birth_positions)
            attributes = {utilities.NS_DICT["crm"].P141_assigned: birth_positions}
            attributes[utilities.NS_DICT["crm"].P2_has_type] = [utilities.create_uri("biography","birthPosition")]
            activity_id = activity_id.replace("1","2")
            birth_position_event = Activity(person, "Birth Related Event", activity_id, birth_tag, activity_type="attribute", attributes=attributes,related_activity=birth_event.uri)
            birth_position_event.event_type.append(utilities.create_uri("event",get_event_type("BIRTH")))
            temp_context.link_activity(birth_position_event)
            person.add_activity(birth_position_event)

        temp_context.link_activity(birth_event)
        person.add_activity(birth_event)

        person.add_context(temp_context)
        context_count += 1


def get_mapped_term(value, id=None):

    def update_fails(rdf_type, value):
        global fail_dict
        if rdf_type in fail_dict:
            if value in fail_dict[rdf_type]:
                fail_dict[rdf_type][value] += 1
            else:
                fail_dict[rdf_type][value] = 1
        else:
            fail_dict[rdf_type] = {value: 1}
    """
        Currently getting exact match ignoring case and "-" characters
    """
    global map_attempt
    global map_success
    global map_fail
    rdf_type = "http://id.lincsproject.ca/ii/IllnessInjury"
    map_attempt += 1
    term = None
    temp_val = clean_term(value)
    
    for x in CAUSE_MAP.keys():
        if temp_val in CAUSE_MAP[x]:
            term = x
            map_success += 1
            break


    if "http" in str(term):
        term = rdflib.term.URIRef(term)
    elif term:
        term = rdflib.Literal(term, datatype=rdflib.namespace.XSD.string)
    else:
        term = rdflib.Literal(value, datatype=rdflib.namespace.XSD.string)
        map_fail += 1
        possibilities = []
        log_str = "Unable to find matching COD instance for '" + value + "'"

        for x in CAUSE_MAP.keys():
            if get_close_matches(value.lower(), CAUSE_MAP[x]):
                possibilities.append(x)
        if type(term) is rdflib.Literal:
            update_fails(rdf_type, value)
        else:
            update_fails(rdf_type, value + "->" + str(possibilities) + "?")
            log_str += "Possible matches" + value + \
                "->" + str(possibilities) + "?"

        if id:
            logger.warning("In entry: " + id + " " + log_str)
        else:
            logger.warning(log_str)
    return term


def log_mapping_fails(detail=True):
    if 'http://id.lincsproject.ca/ii/IllnessInjury' in fail_dict:
        cod_fail_dict = fail_dict['http://id.lincsproject.ca/ii/IllnessInjury']
        log_str = "\n\n"
        log_str += "Attempts: " + str(map_attempt) + "\n"
        log_str += "Fails: " + str(map_fail) + "\n"
        log_str += "Success: " + str(map_success) + "\n"
        log_str += "\nFailure Details:" + "\n"
        log_str += "\nUnique Missed Terms: " + \
            str(len(cod_fail_dict.keys())) + "\n"

        from collections import OrderedDict

        new_dict = OrderedDict(
            sorted(cod_fail_dict.items(), key=lambda t: t[1], reverse=True))
        count = 0
        for y in new_dict.keys():
            log_str += "\t\t" + str(new_dict[y]) + ": " + y + "\n"
            count += new_dict[y]
        log_str += "\tTotal missed CODs: " + str(count) + "\n\n"

        print(log_str)
        logger.info(log_str)


create_cause_map()


def extract_death_data(bio, person):
    context_count = 1
    
    # Multiple death tags --> Michael Fields
    death_tags = bio.find_all("DEATH")
    if len(death_tags) > 1:
        logger.warning("Multiple Death tags found: " +
                       person.name + " - " + person.id)

    for death_tag in death_tags:
        context_id = person.id + "_DeathContext_" + str(context_count)
        temp_context = Context(context_id, death_tag, "DEATH", pattern="death")
        
        cause_tags = death_tag.find_all("CAUSE")
        causes = [get_mapped_term(utilities.get_value(x),person.id) for x in cause_tags]
        causes = list(filter(None, causes))
        
        # create a death event
        activity_id = context_id.replace("Context","Event")
        death_event = Activity(person, "Death Event", activity_id, death_tag, activity_type="death")

        # Creating a cause of death event if it exists
        if causes:
            attributes = {utilities.NS_DICT["crm"].P141_assigned: causes, utilities.NS_DICT["crm"].P2_has_type: [utilities.create_uri("biography","causeOfDeath")]}
            if (len(causes) > 1):
                logger.warning("Multiple causes of death: " + str(causes))
                attributes[utilities.NS_DICT["crm"].P2_has_type].append(utilities.create_uri("edit","lowQuality"))
            
            cod_activity_id = activity_id + "_COD"
            cod_event = Activity(person, "Cause of Death", cod_activity_id, death_tag, activity_type="attribute", attributes=attributes,related_activity=death_event.uri) 
            
            cod_event.event_type.append(utilities.create_uri("event",get_event_type("DEATH")))
            temp_context.link_activity(cod_event)
            person.add_activity(cod_event)

        # Creating a burial event
        event = death_tag.find("CHRONSTRUCT")
        if event:
            shortprose = event.find_next_sibling("SHORTPROSE")
            if shortprose and any(word in shortprose.text for word in BURIAL_KEYWORDS):
                burial_tag = shortprose.find('PLACE')
                burial = None
                if burial_tag:
                    burial = [Place(burial_tag).uri]
                if burial:
                    context_count += 1
                    if death_event.places:
                        death_event.places = [death_event.places[0]]
                    context_id2 = person.id + "_DeathContext_" + str(context_count)
                    temp_context2 = Context(context_id2, shortprose, "DEATH", pattern="death")
                    activity_id2 = context_id2.replace("Context","Event")
                    burial_event = Activity(person, "Burial Event", activity_id2, shortprose, activity_type="generic")
                    burial_event.event_type.append(utilities.create_uri("event",get_event_type("DEATH")))
                    temp_context2.link_activity(burial_event)
                    person.add_activity(burial_event)
                    person.add_context(temp_context2)
        
        temp_context.link_activity(death_event)
        person.add_activity(death_event)
        person.add_context(temp_context)
        context_count += 1

def main():
    from bs4 import BeautifulSoup
    from biography import Biography

    extraction_mode, file_dict = utilities.parse_args(
        __file__, "BirthDeath", logger)
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
        extract_birth_data(soup, person)
        extract_death_data(soup, person)
        graph = person.to_graph()
        

        utilities.create_individual_triples(
            extraction_mode, person, "birthDeath")
        
        utilities.manage_mode(extraction_mode, person, graph)

        uber_graph += graph

    logger.info(str(len(uber_graph)) + " triples created")
    if extraction_mode.verbosity >= 0:
        print(str(len(uber_graph)) + " total triples created")

    log_mapping_fails()
    utilities.create_uber_triples(extraction_mode, uber_graph, "birthDeath")
    

    logger.info("Time completed: " + utilities.get_current_time())

if __name__ == '__main__':
    main()
