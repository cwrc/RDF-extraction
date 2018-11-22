#!/usr/bin/python3
from bs4 import BeautifulSoup
import sys
import logging
from classes import *
from stringAndMemberFunctions import *

import context
from context import Context
from event import get_date_tag, Event
from place import Place
from utilities import *
# TODO: clean up imports post death

class Birth:
    def __init__(self, bDate, bPositions, birthplace):
        self.date = bDate
        self.position = []
        self.place = birthplace

        for birth_position in bPositions:
            if birth_position == "ONLY":
                self.position.append(NS_DICT["cwrc"].onlyChild)
            elif birth_position == "ELDEST":
                self.position.append(NS_DICT["cwrc"].eldestChild)
            elif birth_position == "YOUNGEST":
                self.position.append(NS_DICT["cwrc"].youngestChild)
            elif birth_position == "MIDDLE:":
                self.position.append(NS_DICT["cwrc"].middleChild)

    def __str__(self):
        string = "\tDate: " + str(self.date) + "\n"
        string += "\tbirthplace: " + str(self.place) + "\n"
        for x in self.position:
            string += "\tbirthposition: " + str(x) + "\n"
        return string

    def to_triple(self, person):
        g = rdflib.Graph()
        namespace_manager = rdflib.namespace.NamespaceManager(g)
        bind_ns(namespace_manager, NS_DICT)
        if self.date:
            g.add((person.uri, NS_DICT["cwrc"].hasBirthDate, format_date(self.date)))

        for x in self.position:
            g.add((person.uri, NS_DICT["cwrc"].hasBirthPosition, x))

        if self.place:
            g.add((person.uri, NS_DICT["cwrc"].hasBirthPlace, self.place))

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
            # TODO: Figure out what to do with daterange
            if birth_date_tag.name == "DATERANGE":
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


def create_testcase_dict():
    test_case_files = []
    test_case_desc = []

    # Normal cases
    test_case_desc += ["chronstruct and chronprose  --> birthdate chronstruct, birthposition chronprose"]
    test_case_files += ["allima-b-transformed.xml"]

    test_case_desc += ["Just a chronstruct w. both birth Position & birthdate"]
    test_case_files += ["adcofl-b-transformed.xml"]

    test_case_desc += ["Just a shortprose with date we'll assume is the birthdate"]
    test_case_files += ["aberfr-b-transformed.xml"]

    test_case_desc += ["birthposition & birthdate in a shortprose, no chronstruct"]
    test_case_files += ["cuthca-b-transformed.xml"]

    # this birthposition was orginally not extracted
    test_case_desc += ["chronstruct(date & place) and shortprose(birthpositions)"]
    test_case_files += ["acklva-b-transformed.xml"]

    # Atypical cases
    test_case_desc += ["chronstruct w. date range"]
    test_case_files += ["askean-b-transformed.xml"]

    test_case_desc += ["Has two dates in shortprose"]
    test_case_files += ["bootfr-b-transformed.xml"]

    test_case_desc += ["Daterange within shortprose"]
    test_case_files += ["butls2-b-transformed.xml"]

    test_case_desc += ["has two events in a birthtag(first birth, second christening)"]
    test_case_files += ["scotsa-b-transformed.xml"]

    return dict(zip(test_case_files, test_case_desc))


def main():
    import os
    import argparse
    from bs4 import BeautifulSoup
    import culturalForm
    from biography import Biography
    """
        TODO: add options for verbosity of output, types of output
        -o OUTPUTFILE
        -format [turtle|rdf-xml|all]

    """
    parser = argparse.ArgumentParser(
        description='Extract the Birth/Death information from selection of orlando xml documents', add_help=True)

    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('-testcases', '-t', action="store_true", help="will run through test case list")
    modes.add_argument('-qa', action="store_true",
                       help="will run through qa test cases that are related to https://github.com/cwrc/testData/tree/master/qa")
    modes.add_argument("-f", "-file", "--file", help="single file to run extraction upon")
    modes.add_argument("-d", "-directory", "--directory", help="directory of files to run extraction upon")
    args = parser.parse_args()

    qa_case_files = ["shakwi-b-transformed.xml", "woolvi-b-transformed.xml", "seacma-b-transformed.xml", "atwoma-b-transformed.xml",
                     "alcolo-b-transformed.xml", "bronem-b-transformed.xml", "bronch-b-transformed.xml", "levyam-b-transformed.xml", "aguigr-b-transformed.xml"]
    test_cases = create_testcase_dict()

    if args.file:
        print("Running extraction on " + args.file)
        filelist = [args.file]
    elif args.directory:
        print("Running extraction on files within" + args.directory)
        if args.directory[-1] != "/":
            args.directory += "/"
        filelist = [args.directory +
                    filename for filename in sorted(os.listdir(args.directory)) if filename.endswith(".xml")]
    elif args.qa:
        print("Running extraction on qa cases: ", sep=None)
        print(*qa_case_files, sep=", ")
        filelist = sorted(["bio_data/" + filename for filename in qa_case_files])
    elif args.testcases:
        print("Running extraction on test cases: ", sep=None)
        print(*test_cases.keys(), sep=", ")
        filelist = sorted(["bio_data/" + filename for filename in test_cases.keys()])
    else:
        filelist = ["bio_data/" +
                    filename for filename in sorted(os.listdir("bio_data")) if filename.endswith(".xml")]

    print("-" * 200)
    entry_num = 1

    uber_graph = rdflib.Graph()
    namespace_manager = rdflib.namespace.NamespaceManager(uber_graph)
    bind_ns(namespace_manager, NS_DICT)

    for filename in filelist:
        with open(filename) as f:
            soup = BeautifulSoup(f, 'lxml-xml')
        person_id = filename.split("/")[-1][:6]

        print(filename)
        print(person_id)
        if args.testcases:
            print(test_cases[filename.split("bio_data/")[1]])
        print("*" * 55)

        person = Biography(person_id, get_name(soup), culturalForm.get_mapped_term("Gender", get_sex(soup)))
        extract_birth_data(soup, person)
        # print(person)
        # print("^" * 200)
        print(person.to_file())
        print()

        temp_path = "extracted_triples/birthdeath_turtle/" + person_id + "_birthdeath.ttl"
        create_extracted_file(temp_path, person)

        uber_graph += person.to_graph()
        entry_num += 1
        print("=" * 55)

    print("UberGraph is size:", len(uber_graph))
    temp_path = "extracted_triples/birthdeath.ttl"
    create_extracted_uberfile(temp_path, uber_graph)

    temp_path = "extracted_triples/birthdeath.rdf"
    create_extracted_uberfile(temp_path, uber_graph, "pretty-xml")


if __name__ == '__main__':
    main()
