#!/usr/bin/python3
import sys
import logging

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
# TODO once resolved: https://github.com/cwrc/ontology/issues/462

logger = utilities.config_logger("birthdeath")


class Birth:
    def __init__(self, bDate, bPositions, birthplace):
        self.date = bDate
        self.position = []
        self.place = birthplace

        for birth_position in bPositions:
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

    def to_triple(self, person):
        g = utilities.create_graph()
        if self.date:
            g.add((person.uri, utilities.NS_DICT["cwrc"].hasBirthDate, format_date(self.date)))

        for x in self.position:
            g.add((person.uri, utilities.NS_DICT["cwrc"].hasBirthPosition, x))

        if self.place:
            g.add((person.uri, utilities.NS_DICT["cwrc"].hasBirthPlace, self.place))

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

    birthTagParent = xmlString.BIOGRAPHY.DIV0.BIRTH
    if not birthTagParent:
        return

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
            # logger.info(birth_date_tag)
            # TODO: Figure out what to do with daterange
            if birth_date_tag.name == "DATERANGE":
                logger.warning("Daterange:" + str(birth_date_tag))
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
            logger.warning("Multiple Birth positions:" + str(birth_positions))

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
        person.add_birth(tempBirth)
        context_count += 1


# TODO: Still need to update this function
def extract_death(xmlString, person):
    # filePath = os.path.expanduser("~/Downloads/laurma-b.xml")
    # getTreeRoot = xml.etree.ElementTree.parse(filePath)
    # treeRoot = getTreeRoot.getroot()
    treeRoot = xmlString

    # DEATH
    deathDate = ""
    deathCauses = []
    deathContexts = []
    deathplace = None
    burialplace = None
    # deathTagParent = treeRoot.find("./DIV0/DIV1/DEATH/")
    # deathTagParent = treeRoot.BIOGRAPHY.DIV0.DEATH.find(recursive=False)
    deathTagParent = tagChild(findTag(treeRoot, "BIOGRAPHY DIV0 DIV1 DEATH"))
    # childrenOfDeathTag = tagChildren(deathTagParent)
    # print(deathTagParent.name)

    # DEATH DATE
    firstChronstructTag = ""
    deathDateTag = ""

    try:
        if deathTagParent is None:
            # Death tag not found
            deathTagParent = treeRoot.find(".//DEATH/")
            if deathTagParent is not None:
                print("used to be none but found death")
                sys.stdin.read(1)
            else:
                # Still no death tag found
                print("still no death tag found")
                # sys.stdin.read(1)
                return

        # allDeathDivs = treeRoot.BIOGRAPHY.select("DIV0 DIV1 DEATH")
        # allDivs = []
        # for deathTag in allDeathDivs:
        #     allDivs += tagChildren(deathTag)
            # div.find_all(recursive=False)

        # if type(deathContexts) is list:
        #     print(deathContexts)
        #     print("this is a list")
        # getContextsFrom = [deathTagParent]
        # if "DIV" not in getContextsFrom[0].name:
        #     DIV = Element('DIV')
        #     DIV.insert(0, getContextsFrom[0])
        #
        #     # DIV.append(getContextsFrom)
        #     getContextsFrom = [DIV]
        # deathContexts = getContexts(getContextsFrom)

        # deathParagraphs = list(deathTagParent.iter("P"))
        # if deathParagraphs != None and len(deathParagraphs) > 0:
        #     for para in list(deathTagParent.iter("P")):
        #
        #         # gets all text in paragraph. creates element iterator
        #         paraText = para.itertext()
        #         # the paragraph will be saved as a string in variable below
        #         paragraph = ""
        #
        #         for text in paraText:
        #             paragraph = paragraph + " " + text.strip()
        #         paragraph = paragraph.strip()
        #         print(paragraph)
        #         deathContexts.append(paragraph)
                # print(paragraph)
        # print(deathTagParent.contents)

        # print(deathTagParent.prettify())
        getChronstructTags = iterList(deathTagParent, "CHRONSTRUCT")

        if len(getChronstructTags) == 0:
            # No chronstruct tag found. Look for a shortprose tag
            getChronstructTags = (deathTagParent.find_all("SHORTPROSE"))

        if len(getChronstructTags) == 0:
            # No shortprose tag found either
            print("no SHORTPROSE in death found")
            sys.stdin.read(1)
            return

        if len(getChronstructTags) > 0:
            # A tag is found. Either a chronstruct or a shortprose
            firstChronstructTag = getChronstructTags[0]
            print(getChronstructTags)

            deathDateTags = get_date_tag(firstChronstructTag)

            if not deathDateTags:
                print("no date range either")
            else:
                # Found a date tag
                deathDateTag = deathDateTags
                if 'VALUE' in deathDateTag.attrs:
                    deathDate = deathDateTag['VALUE']
                elif 'CERTAINTY' in deathDateTag.attrs and 'FROM' in deathDateTag.attrs and 'TO' in deathDateTag.attrs:
                    deathDate = deathDateTag['FROM'] + " to " + deathDateTag['TO']

    except (AttributeError) as e:
        print("Death information not found. person probably still alive")
        # print("error: ", e)
        logging.exception(e)
        sys.stdin.read(1)
        return

    except NameError as e:
        print("Name Error")
        print("error: ", e)
        sys.stdin.read(1)
        return

    print("\ndeath date: ", deathDate)

    # CAUSE OF DEATH
    deathCauseTags = (firstChronstructTag.select('CHRONPROSE CAUSE'))
    if len(deathCauseTags) > 0:
        for causes in deathCauseTags:
            if "REG" in causes.attrs:
                deathCauses.append(causes['REG'])
            else:
                deathCauses.append(causes.text)

        print("death causes: {}".format(deathCauses))

    # PLACE OF DEATH
    deathPlaceTags = (firstChronstructTag.select('CHRONPROSE PLACE'))
    if len(deathPlaceTags) > 0:
        deathplace = Place(deathPlaceTags[0]).uri
        # print("death place: {}, {}, {}".format(deathPlaceSettlement, deathPlaceRegion, deathPlaceGeog))

    else:
        allShortprose = firstChronstructTag.find_all('SHORTPROSE')
        # print(allShortprose)
        if len(allShortprose) > 0:
            for shortprose in allShortprose:
                for tags in shortprose.find_all('PLACE'):
                    deathplace = Place(tags).uri
        else:
            # chronstructParent = firstChronstructTag.find('./..')
            place = deathTagParent.find('PLACE')
            if place is None:
                print("no place found")
            if place is not None and len(place) > 0:
                print("found place")
                # deathPlaceSettlement, deathPlaceRegion, deathPlaceGeog = getPlaceTagContent(place)
                deathplace = Place(place).uri

    # place of burial
    # ElemPrint(deathTagParent)
    print(deathTagParent.name)
    burialTags = tagChildren(deathTagParent)
    print(len(burialTags))

    for i in range(0, len(burialTags)):
        if i == len(burialTags) - 1:
            continue
        # print(getOnlyText(burialTags[i+1].find(".//P")))
        if burialTags[i].name == "CHRONSTRUCT" and burialTags[i + 1].name == "SHORTPROSE" and burialTags[i + 1].find("PLACE") is not None:
            paragraph = getOnlyText(burialTags[i + 1].find("P"))

            if "buried" in paragraph or "grave" in paragraph or "interred" in paragraph:
                burialplace = Place(burialTags[i + 1].find("PLACE")).uri

            else:
                print("no buried in the paragraph")

    person.deathObj = deathData(person.name, person.id, person.uri, deathDate,
                                deathCauses, deathplace, deathContexts, burialplace)
    allDivs = allTagsAllChildren(treeRoot.BIOGRAPHY, "DIV0 DIV1 DEATH")
    # for div in allDivs:
    #     deathContexts += getContexts(div)
    id = 1
    for div in allDivs:
        # birthContexts += getContexts(div)
        context_id = person.id + "_DeathContext_" + str(id)
        tempContext = context.Context(context_id, div, 'DEATH')
        tempContext.link_triples(person.deathObj.death_list)
        person.context_list.append(tempContext)


def main():
    from bs4 import BeautifulSoup
    import culturalForm
    import rdflib
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
        person.name = utilities.get_readable_name(soup)
        # print(person.to_file())
        # print()

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
