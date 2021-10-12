#!/usr/bin/python3
from typing import List
import rdflib
from rdflib import RDF, RDFS, Literal
from Utils import utilities
from Utils.context import Context
from Utils.place import Place
from Utils.event import get_date_tag, Event, format_date
from Utils.activity import Activity 

# TODO
# - once resolved: https://github.com/cwrc/ontology/issues/462
# - handle multiple DEATH/BIRTH tags

logger = utilities.config_logger("birthdeath")
count = 0

def get_birthposition_uris(positions):
    positions_uris = []
    if positions:
        for birth_position in positions:
            if birth_position == "ONLY":
                positions_uris.append(utilities.NS_DICT["cwrc"].onlyChild)
            elif birth_position == "ELDEST":
                positions_uris.append(utilities.NS_DICT["cwrc"].eldestChild)
            elif birth_position == "YOUNGEST":
                positions_uris.append(utilities.NS_DICT["cwrc"].youngestChild)
            elif birth_position == "MIDDLE:":
                positions_uris.append(utilities.NS_DICT["cwrc"].middleChild)
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
    birth_events = []
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
            attributes[utilities.NS_DICT["crm"].P2_has_type] = [utilities.create_uri("cwrc","birthPosition")]
            activity_id = activity_id.replace("1","2")
            birth_position_event = Activity(person, "Birth Related Event", activity_id, birth_tag, activity_type="attribute", attributes=attributes,related_activity=birth_event.uri)
            temp_context.link_activity(birth_position_event)
            person.add_activity(birth_position_event)

        temp_context.link_activity(birth_event)
        person.add_activity(birth_event)

        person.add_context(temp_context)
        context_count += 1

def extract_death_data(bio, person):
    death_events = []
    context_count = 1

    # Multiple death tags --> michael field
    death_tags = bio.find_all("DEATH")
    if len(death_tags) > 1:
        logger.warning("Multiple Death tags found: " +
                       person.name + " - " + person.id)

    for death_tag in death_tags:
        context_id = person.id + "_DeathContext_" + str(context_count)
        temp_context = Context(context_id, death_tag, "DEATH", pattern="death")

        # create a death event
        activity_id = context_id.replace("Context","Event")
        death_event = Activity(person, "Death Event", activity_id, death_tag, activity_type="death")

        # Creating a burial event
        event = death_tag.find("CHRONSTRUCT")
        if event:
            shortprose = event.find_next_sibling("SHORTPROSE")
            if shortprose and any(word in shortprose.text for word in ["buried", "grave", "interred"]):
                burial_tag = shortprose.find('PLACE')
                burial = None
                if burial_tag:
                    burial = [Place(burial_tag).uri]
                if burial:
                    context_count += 1
                    death_event.places = [death_event.places[0]]
                    context_id2 = person.id + "_DeathContext_" + str(context_count)
                    temp_context2 = Context(context_id2, shortprose, "DEATH", pattern="death")
                    activity_id2 = context_id2.replace("Context","Event")
                    burial_event = Activity(person, "Burial Event", activity_id2, shortprose, activity_type="generic")

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

    utilities.create_uber_triples(extraction_mode, uber_graph, "birthDeath")
    

    logger.info("Time completed: " + utilities.get_current_time())

if __name__ == '__main__':
    main()
