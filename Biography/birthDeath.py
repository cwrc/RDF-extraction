#!/usr/bin/python3

from Utils import utilities
from Utils.context import Context
from Utils.place import Place
from Utils.event import get_date_tag, Event, format_date

# TODO: clean up imports post death
# Should be matched up to deb's contexts somehow
# otherwise we're looking at duplicate contexts
# two unique id'd contexts but with the same text and different triples
# attached but this might fine if we're distinguishing between
# death context vs cause of death context
# TODO
# - once resolved: https://github.com/cwrc/ontology/issues/462
# - handle multiple DEATH/BIRTH tags


logger = utilities.config_logger("birthdeath")


class Birth:
    def __init__(self, date, positions, birthplace):
        self.date = date
        self.position = []
        self.place = birthplace

        for birth_position in positions:
            if birth_position == "ONLY":
                self.position.append(utilities.NS_DICT["cwrc"].onlyChild)
            elif birth_position == "ELDEST":
                self.position.append(utilities.NS_DICT["cwrc"].eldestChild)
            elif birth_position == "YOUNGEST":
                self.position.append(utilities.NS_DICT["cwrc"].youngestChild)
            elif birth_position == "MIDDLE:":
                self.position.append(utilities.NS_DICT["cwrc"].middleChild)

    def __str__(self):
        string = "\tDate: " + str(self.date) + "\n"
        string += "\tbirthplace: " + str(self.place) + "\n"
        for x in self.position:
            string += "\tbirthposition: " + str(x) + "\n"
        return string

    def to_triple(self, context):
        g = utilities.create_graph()
        if self.date:
            g.add((context.uri, utilities.NS_DICT["cwrc"].birthDate, format_date(self.date)))

        for x in self.position:
            g.add((context.uri, utilities.NS_DICT["cwrc"].birthPosition, x))

        if self.place:
            g.add((context.uri, utilities.NS_DICT["cwrc"].birthPlace, self.place))

        return g


def extract_birth_data(xmlString, person):
    """
    Revised method of extracting birth information
    """
    birth_date = None
    birthplace = None
    birth_events = []
    birth_event = None
    birth_positions = []
    context_count = 1

    date_found = False
    place_found = False

    birthTagParent = xmlString.find_all("BIRTH")
    if len(birthTagParent) > 1:
        logger.warning("Multiple Birth tags found: " + person.name + person.id)

    if not birthTagParent:
        return

    birthTagParent = birthTagParent[0]

    birthTags = birthTagParent.find_all("CHRONSTRUCT")
    birthTags += birthTagParent.find_all("SHORTPROSE")

    for x in birthTags:
        context_id = person.id + "_BirthContext_" + str(context_count)
        temp_context = Context(context_id, x, "BIRTH")

        # creating birth event
        if x.name == "CHRONSTRUCT":
            event_title = person.name + " - Birth Event"
            event_uri = person.id + "_Birth_Event"

            if len(birth_events) > 0:
                # TODO: possibly revise uri as well
                event_title = person.name + " - Birth Related Event"
                event_uri = person.id + "_Birth_Event" + str(len(birth_events) + 1)

            birth_event = Event(event_title, event_uri, x)
            birth_events.append(birth_event)

        # retrieving birthdate
        if not birth_date:
            birth_date_tag = get_date_tag(x)
            # TODO: Figure out what to do with daterange --> issue#462
            if birth_date_tag.name == "DATERANGE":
                logger.info("Birth: Daterange:" + str(birth_date_tag))
                birth_date = birth_date_tag.get("FROM")
            else:
                birth_date = birth_date_tag.get("VALUE")

        # retrieving birthplace
        if not birthplace:
            birthPlaceTags = x.find_all('PLACE')
            if birthPlaceTags:
                birthplace = Place(birthPlaceTags[0]).uri

        # retrieving birthposition
        birthPositionTags = x.find_all('BIRTHPOSITION')
        for positions in birthPositionTags:
            if 'POSITION' in positions.attrs:
                birth_positions.append(positions['POSITION'])
        birth_positions = list(set(birth_positions))
        if len(birth_positions) > 1:
            logger.info("Multiple Birth positions:" + str(birth_positions))

        # creating birth instance
        tempBirth = Birth(None, birth_positions, None)
        if not date_found and birth_date:
            tempBirth.date = birth_date
            date_found = True
        if not place_found and birthplace:
            tempBirth.place = birthplace
            place_found = True

        # adding birth event to person
        if birth_event:
            temp_context.link_event(birth_event)
            person.add_event(birth_event)
            birth_event = None

        # adding context and birth to person
        temp_context.link_triples(tempBirth)
        person.add_context(temp_context)
        # person.add_birth(tempBirth)
        context_count += 1


class Death:
    def __init__(self, date, burialplace, deathplace):
        self.date = date
        self.burial = burialplace
        self.place = deathplace

    def __str__(self):
        string = "\tDate: " + str(self.date) + "\n"
        string += "\tdeathplace: " + str(self.place) + "\n"
        string += "\tburial: " + str(self.burial) + "\n"
        return string

    def to_triple(self, person):
        g = utilities.create_graph()
        if self.date:
            g.add((person.uri, utilities.NS_DICT["cwrc"].hasDeathDate, format_date(self.date)))

        if self.burial:
            g.add((person.uri, utilities.NS_DICT["cwrc"].hasBurialPlace, self.burial))

        if self.place:
            g.add((person.uri, utilities.NS_DICT["cwrc"].hasDeathPlace, self.place))

        return g


def extract_death_data(xmlString, person):
    death_date = None
    deathplace = None
    death_events = []
    death_event = None
    burial = None
    context_count = 1

    date_found = False
    place_found = False

    # Multiple death tags --> michael field
    deathTagParent = xmlString.find_all("DEATH")
    if len(deathTagParent) > 1:
        logger.warning("Multiple Death tags found: " + person.name + " - " + person.id)

    if not deathTagParent:
        return
    deathTagParent = deathTagParent[0]

    deathTags = deathTagParent.find_all("CHRONSTRUCT")
    deathTags += deathTagParent.find_all("SHORTPROSE")

    for x in deathTags:
        context_id = person.id + "_deathContext_" + str(context_count)
        temp_context = Context(context_id, x, "DEATH")

        # creating death event
        if x.name == "CHRONSTRUCT":
            event_title = person.name + " - Death Event"
            event_uri = person.id + "_death_Event"

            if len(death_events) > 0:
                # TODO: possibly revise uri as well
                event_title = person.name + " - Death Related Event"
                event_uri = person.id + "_death_Event" + str(len(death_events) + 1)

            death_event = Event(event_title, event_uri, x)
            death_events.append(death_event)

        # retrieving deathdate
        if not death_date:
            death_date_tag = get_date_tag(x)
            if death_date_tag:
                # TODO: Figure out what to do with daterange --> issue#462
                if death_date_tag.name == "DATERANGE":
                    logger.info("Death: Daterange:" + str(death_date_tag) +
                                " " + person.name + " - " + person.id)
                    death_date = death_date_tag.get("FROM")
                else:
                    death_date = death_date_tag.get("VALUE")

        # retrieving deathplace
        if not deathplace:
            deathPlaceTags = x.find_all('PLACE')
            if deathPlaceTags:
                deathplace = Place(deathPlaceTags[0]).uri

        # potentially retrieving burial place
        if len(death_events) > 0 and x.name == "SHORTPROSE" and burial is None:
            if any(word in x.text for word in ["buried", "grave", "interred"]):
                burialTags = x.find_all('PLACE')
                if burialTags:
                    burial = Place(burialTags[0]).uri

        tempDeath = Death(None, burial, None)
        if not date_found and death_date:
            tempDeath.date = death_date
            date_found = True
        if not place_found and deathplace:
            tempDeath.place = deathplace
            place_found = True

        # adding death event to person
        if death_event:
            temp_context.link_event(death_event)
            person.add_event(death_event)
            death_event = None

        # adding context and birth to person
        temp_context.link_triples(tempDeath)
        person.add_context(temp_context)
        person.add_birth(tempDeath)
        context_count += 1


def main():
    from bs4 import BeautifulSoup
    import culturalForm
    from biography import Biography

    file_dict = utilities.parse_args(__file__, "Birth/Death")
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
        extract_birth_data(soup, person)
        # extract_death_data(soup, person)
        person.name = utilities.get_readable_name(soup)
        print(person.to_file())

        temp_path = "extracted_triples/birthdeath_turtle/" + person_id + "_birthdeath.ttl"
        utilities.create_extracted_file(temp_path, person)

        uber_graph += person.to_graph()
        entry_num += 1
        print("=" * 55)

    print("UberGraph is size:", len(uber_graph))
    temp_path = "extracted_triples/birthdeath.ttl"
    utilities.create_extracted_uberfile(temp_path, uber_graph)

    temp_path = "extracted_triples/birthdeath.rdf"
    utilities.create_extracted_uberfile(temp_path, uber_graph, "pretty-xml")


if __name__ == '__main__':
    main()
