#!/usr/bin/python3
from bs4 import BeautifulSoup
from Utils import utilities, place, organizations, context
from writer import Writer
import rdflib
logger = utilities.config_logger("writing")


class GeneralRelation(object):
    """docstring for GeneralRelation"""

    def __init__(self, pred, obj):
        super(GeneralRelation, self).__init__()
        self.predicate = pred
        self.object = obj

    def __str__(self):
        string = ""
        string += "Predicate: " + self.predicate + "\n"
        string += "Object: " + self.object + "\n"
        return string

    def to_triple(self, context):
        g = utilities.create_graph()
        g.add((context.uri, self.predicate, self.object))
        return g


def extract_general_info(doc, person, count):
    tag = doc.find("AUTHORSUMMARY")
    general_relations = []
    cwrc = utilities.NS_DICT['cwrc']
    general_relations.append(GeneralRelation(cwrc.profile, rdflib.Literal(utilities.limit_words(tag.text, 35))))

    context_id = person.id + "_WritingContext_" + str(count)
    temp_context = context.Context(context_id, tag, "AUTHORSUMMARY")
    temp_context.link_triples(general_relations)
    person.add_context(temp_context)

    count += 1
    general_relations = []

    # TODO: Need to check mapping with genre ontology
    # Make genre class for mapping 
    # does this apply to person or the ouevre
    tags = tag.find_all("GENERICRANGE")
    genre_tags = []
    for x in tags:
        genre_tags += x.find_all("TGENRE")

    genres = [x["GENRENAME"] for x in genre_tags]
    for x in genres:
        general_relations.append(GeneralRelation(cwrc.genericRangeIncludes, rdflib.Literal(x)))

    print(genres)

    extent = tag.find_all("EXTENTOFOEUVRE")
    for x in extent:
        general_relations.append(GeneralRelation(cwrc.extent, rdflib.Literal(utilities.limit_words(x.text, 35))))

    context_id = person.id + "_WritingContext_" + str(count)
    temp_context = context.Context(context_id, tag, "AUTHORSUMMARY", subject_uri=person.oeuvre_uri)
    temp_context.link_triples(general_relations)
    person.add_context(temp_context)

    events = tag.find("CHRONSTRUCT")
    if events:
        logger.warning("Events found in AUTHORSUMMARY of entry: " + person.id + "\n" + str(events))

    return count


def main():
    file_dict = utilities.parse_args(__file__, "Majority of writing related data")

    entry_num = 1
    uber_graph = utilities.create_graph()

    highest_triples = 0
    least_triples = 0
    smallest_person = None
    largest_person = None
    logger.info("Time started: " + utilities.get_current_time() + "\n")

    for filename in file_dict.keys():
        with open(filename) as f:
            soup = BeautifulSoup(f, 'lxml-xml')

        person_id = filename.split("/")[-1][:6]

        print(person_id)
        print(file_dict[filename])
        print("*" * 55)
        context_count = 1

        person = Writer(person_id, soup)
        extract_general_info(soup, person, context_count)

        # print(person)
        graph = person.to_graph()

        print(person.to_file())
        triple_count = len(graph)

        if triple_count > highest_triples:
            highest_triples = triple_count
            largest_person = filename
        if least_triples == 0 or triple_count < least_triples:
            least_triples = triple_count
            smallest_person = filename

        # triples to files
        temp_path = "extracted_triples/writing_turtle/" + person_id + "_writing.ttl"
        utilities.create_extracted_file(temp_path, person)

        uber_graph += graph
        entry_num += 1

    place.log_mapping_fails()
    organizations.log_mapping()

    logger.info(str(len(uber_graph)) + " total triples created")
    logger.info(str(largest_person) + " produces the most triples(" + str(highest_triples) + ")")
    logger.info(str(smallest_person) + " produces the least triples(" + str(least_triples) + ")")

    logger.info("Time completed: " + utilities.get_current_time())

    temp_path = "extracted_triples/writing_triples.ttl"
    utilities.create_extracted_uberfile(temp_path, uber_graph)


if __name__ == "__main__":
    main()
