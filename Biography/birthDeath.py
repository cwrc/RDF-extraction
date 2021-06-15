#!/usr/bin/python3
from typing import List
import rdflib
from rdflib import RDF, RDFS, Literal
from Utils import utilities
from Utils.context import Context
from Utils.place import Place
from Utils.event import get_date_tag, Event, format_date

# TODO
# - once resolved: https://github.com/cwrc/ontology/issues/462
# - handle multiple DEATH/BIRTH tags

logger = utilities.config_logger("birthdeath")


class Birth:
    def __init__(self, date, positions, birthplace, date_certainty=False):
        self.label = ""
        self.date = date
        self.position = []
        self.place = birthplace
        self.date_certainty = date_certainty
        self.person = None
        self.note = None

    def __str__(self):
        string = "\tDate: " + str(self.date) + "\n"
        string += "\tbirthplace: " + str(self.place) + "\n"
        for x in self.position:
            string += "\tbirthposition: " + str(x) + "\n"
        string += "\tdate certainty: " + str(self.date_certainty) + "\n"
        return string

    def update_birthposition_uris(self):
        positions = []
        if self.position:
            for birth_position in self.position:
                if birth_position == "ONLY":
                    positions.append(utilities.NS_DICT["cwrc"].onlyChild)
                elif birth_position == "ELDEST":
                    positions.append(utilities.NS_DICT["cwrc"].eldestChild)
                elif birth_position == "YOUNGEST":
                    positions.append(utilities.NS_DICT["cwrc"].youngestChild)
                elif birth_position == "MIDDLE:":
                    positions.append(utilities.NS_DICT["cwrc"].middleChild)
        self.position = positions

    def to_triple(self, context):
        g = utilities.create_graph()
        birth_event = utilities.create_uri("data", context.id.replace("Context","Event"))
        
        g.add((birth_event,RDF.type, utilities.NS_DICT["crm"].E67_Birth ))
        g.add((birth_event,RDFS.label, Literal(self.label) ))
        g.add((birth_event,utilities.NS_DICT["crm"].P98_brought_into_life, context.context_focus))

        # Get father and mother
        if "FATHER" in self.person.family_members and len(self.person.family_members["FATHER"])==1:
            father = self.person.family_members["FATHER"][0]
            if len(father) == 1:
                father = father[0]
                if father:
                    g.add((birth_event,utilities.NS_DICT["crm"].P97_from_father,father ))

        if "MOTHER" in self.person.family_members and len(self.person.family_members["MOTHER"])==1:
            mother = self.person.family_members["MOTHER"][0]
            if len(mother) == 1:
                mother = mother[0]
                if mother:
                    g.add((birth_event,utilities.NS_DICT["crm"].P96_by_mother, mother))

        if self.date:
            time_span = rdflib.BNode()
            g.add((birth_event, utilities.NS_DICT["crm"]["P4_has_time-span"], time_span))
            g.add((time_span, utilities.NS_DICT["crm"]["P82a_begin_of_the_begin"], format_date(self.date)))
            g.add((time_span, utilities.NS_DICT["crm"]["P82b_end_of_the_end"], format_date(self.date))) 

        if self.note:
            g.add((birth_event,utilities.NS_DICT["crm"].P3_has_note, Literal(self.note)))

        if self.place:
            g.add((birth_event,utilities.NS_DICT["crm"].P7_took_place_at, self.place))

        birth_context = utilities.create_uri("data", context.id + "_identifying")
        g.add((birth_event,utilities.NS_DICT["crm"].P129i_is_subject_of, birth_context))
        

        return g


def extract_birth_data(bio, person):
    birth_events = []
    birth_positions = []
    context_count = 1

    birth_tags = bio.find_all("BIRTH")
    if len(birth_tags) > 1:
        logger.warning("Multiple Birth tags found: " + person.name + person.id)

    birth = Birth(None, None, None)
    birth.person = person

    for birth_tag in birth_tags:
        context_id = person.id + "_BirthContext_" + str(context_count)
        temp_context = Context(context_id, birth_tag, "BIRTH",pattern="birth")

        # creating Birth event
        event_tags = birth_tag.find_all("CHRONSTRUCT")
        for x in event_tags:
            birth.label = person.name + " - Birth Event"
            event_uri = person.id + "_BirthEvent_1"

            if len(birth_events) > 0:
                # TODO: possibly revise uri as well
                logger.info(
                    "Multiple Birth events encountered within entry: " + person.id)
                event_title = person.name + " - Birth Related Event"
                event_uri = person.id + "_BirthEvent_" + \
                    str(len(birth_events) + 1)

            temp = Event(birth.label, event_uri, x, "BirthEvent")
            birth.note = temp.text
            # birth_events.append()

        # retrieving birthdate
        if not birth.date:
            birth_date_tag = get_date_tag(birth_tag)

            if birth_date_tag:
                if birth_date_tag.get("CERTAINTY") == "CERT":
                    birth.date_certainty = True

                # Taking earliest date of date range for birth
                if birth_date_tag.name == "DATERANGE":
                    if birth.date_certainty:
                        logger.warning(
                            "DATERANGE is certain?: " + str(birth_date_tag))
                    birth.date = birth_date_tag.get("FROM")
                else:
                    birth.date = birth_date_tag.get("VALUE")

        # retrieving birthplace
        if not birth.place:
            birthPlaceTags = birth_tag.find('PLACE')
            if birthPlaceTags:
                birth.place = Place(birthPlaceTags).uri

        # retrieving birthposition
        birthPositionTags = birth_tag.find_all('BIRTHPOSITION')
        for positions in birthPositionTags:
            if 'POSITION' in positions.attrs:
                birth_positions.append(positions['POSITION'])
        birth.position = list(set(birth_positions))
        if len(birth_positions) > 1:
            logger.info("Multiple Birth positions:" + str(birth_positions))

        # adding birth event to person
        # for x in birth_events:
        #     temp_context.link_event(x)
        #     person.add_event(x)

        # adding context and birth to person
        temp_context.link_triples(birth)
        person.add_context(temp_context)
        context_count += 1


class Death:
    def __init__(self, date, burialplace, deathplace, date_certainty=False):
        self.date = date
        self.burial = burialplace
        self.place = deathplace
        self.date_certainty = date_certainty
        self.label = ""
        self.person = None
        self.note = ""

    def __str__(self):
        string = "\tDate: " + str(self.date) + "\n"
        string += "\tdeathplace: " + str(self.place) + "\n"
        string += "\tburial: " + str(self.burial) + "\n"
        string += "\tdate certainty: " + str(self.date_certainty) + "\n"
        return string

    def to_triple(self, context):
        g = utilities.create_graph()
        death_event = utilities.create_uri("data", context.id.replace("Context","Event"))
        
        g.add((death_event,RDF.type, utilities.NS_DICT["crm"].E69_Death ))
        g.add((death_event,RDFS.label, Literal(self.label) ))
        g.add((death_event,utilities.NS_DICT["crm"].P100_was_death_of, context.context_focus))
        
        if self.date:
            time_span = rdflib.BNode()
            g.add((death_event, utilities.NS_DICT["crm"]["P4_has_time-span"], time_span))
            g.add((time_span, utilities.NS_DICT["crm"]["P82a_begin_of_the_begin"], format_date(self.date)))
            g.add((time_span, utilities.NS_DICT["crm"]["P82b_end_of_the_end"], format_date(self.date))) 

        if self.note:
            g.add((death_event,utilities.NS_DICT["crm"].P3_has_note, Literal(self.note)))

        if self.place:
            g.add((death_event,utilities.NS_DICT["crm"].P7_took_place_at, self.place))

        death_context = utilities.create_uri("data", context.id + "_identifying")
        g.add((death_event,utilities.NS_DICT["crm"].P129i_is_subject_of, death_context))
        g.add((death_context,utilities.NS_DICT["crm"].P129_is_about,death_event ))
        


        cod_context = utilities.create_uri("data", context.id + "_attributing")
        g.add((death_event,utilities.NS_DICT["crm"].P140i_was_attributed_by, cod_context))
            

        # if self.burial:
        #     g.add(
        #         (context.uri, utilities.NS_DICT["cwrc"].burialPlace, self.burial))

        if self.place:
            g.add(
                (context.uri, utilities.NS_DICT["cwrc"].deathPlace, self.place))

        return g


def extract_death_data(bio, person):
    death_events = []
    context_count = 1

    # Multiple death tags --> michael field
    death_tags = bio.find_all("DEATH")
    if len(death_tags) > 1:
        logger.warning("Multiple Death tags found: " +
                       person.name + " - " + person.id)

    death = Death(None, None, None)
    for death_tag in death_tags:
        context_id = person.id + "_DeathContext_" + str(context_count)
        temp_context = Context(context_id, death_tag, "DEATH", pattern="death")

        # creating death events
        events_tags = death_tag.find_all("CHRONSTRUCT")
        for x in events_tags:
            death.label = person.name + " - Death Event"
            event_uri = person.id + "_DeathEvent_1"

            if len(death_events) > 0:
                # TODO: possibly revise uri as well
                logger.info(
                    "Multiple Death events encountered within entry: " + person.id)
                event_title = person.name + " - Death Related Event"
                event_uri = person.id + "_DeathEvent_" + \
                    str(len(death_events) + 1)
            temp = Event(death.label, event_uri, x, "DeathEvent")
            death_events.append(temp)
            if len(death_events) == 1:
                death.note = death_events[0].text

            # Get shortprose after event
            if not death.burial:
                shortprose = x.find_next_sibling("SHORTPROSE")
                if shortprose and any(word in shortprose.text for word in ["buried", "grave", "interred"]):
                    burial_tag = shortprose.find('PLACE')
                    if burial_tag:
                        death.burial = Place(burial_tag).uri

        if not death.date:
            death_date_tag = get_date_tag(death_tag)
            if death_date_tag:
                if death_date_tag.get("CERTAINTY") == "CERT":
                    death.date_certainty = True

                if death_date_tag:
                    # Using TO value from daterange
                    if death_date_tag.name == "DATERANGE":
                        if death.date_certainty:
                            logger.warning("DATERANGE is certain " + " - " +
                                           person.id + " : " + str(death_date_tag))
                        death.date = death_date_tag.get("TO")
                    else:
                        death.date = death_date_tag.get("VALUE")

        # retrieving deathplace
        if not death.place:
            deathPlaceTag = death_tag.find('PLACE')
            if deathPlaceTag:
                death.place = Place(deathPlaceTag).uri

        # for x in death_events:
        #     temp_context.link_event(x)
        #     person.add_event(x)

        # adding context and birth to person
        temp_context.link_triples(death)
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
