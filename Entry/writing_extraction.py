#!/usr/bin/python3
from bs4 import BeautifulSoup
from biography import Biography
from Utils import utilities, place, organizations
from Utils.context import Context, get_context_type, get_event_type
from Utils.event import Event
from Utils.organizations import get_org_uri
import intertextuality
import rdflib
logger = utilities.config_logger("writing")



def extract_general_info(doc, person, count):
    tag = doc.find("AUTHORSUMMARY")
    general_relations = []
    cwrc = utilities.NS_DICT['cwrc']
    general_relations.append(utilities.GeneralRelation(cwrc.profile, rdflib.Literal(utilities.limit_words(tag.text))))

    context_id = person.id + "_WritingContext_" + str(count)
    temp_context = Context(context_id, tag, "AUTHORSUMMARY")
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
    genres = [utilities.GENRE_MAPPING[x.lower()] for x in genres if x.lower() in utilities.GENRE_MAPPING ]
    
    for x in genres:
        general_relations.append(utilities.GeneralRelation(cwrc.genericRangeIncludes, rdflib.URIRef(x)))

    extent = tag.find_all("EXTENTOFOEUVRE")
    titles = utilities.get_titles(tag)
    for x in extent:
        general_relations.append(utilities.GeneralRelation(cwrc.extent, rdflib.Literal(utilities.limit_words(x.text, 35))))

    # TODO!: Make Oeuvre into it's own class similar to titles so that more properties can be attached?
    for x in titles:
        general_relations.append(utilities.GeneralRelation(utilities.NS_DICT["bf"].hasPart, x))


    # Reusing above Context's target uri/snippet
    context_id = person.id + "_WritingContext_" + str(count)
    temp_context2 = Context(context_id, tag, "AUTHORSUMMARY", subject_uri=person.oeuvre_uri, target_uri=temp_context.target_uri,id_context=temp_context.identifying_uri)
    temp_context2.link_triples(general_relations)
    person.add_context(temp_context2)

    events = tag.find("CHRONSTRUCT")
    if events:
        logger.warning("Events found in AUTHORSUMMARY of entry: " + person.id + "\n" + str(events))

    return count


def main():
    extraction_mode, file_dict = utilities.parse_args(
        __file__, "Majority of Writing related data", logger)

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

        person = Biography(person_id, soup)
        
        extract_general_info(soup, person, 1)
        intertextuality.extract_intertextuality_data(soup, person)
        intertextuality.extract_influence_data(soup, person)
        intertextuality.extract_response_data(soup,person)
        graph = person.to_graph()
        triple_count = len(graph)

        if triple_count > highest_triples:
            highest_triples = triple_count
            largest_person = filename
        if least_triples == 0 or triple_count < least_triples:
            least_triples = triple_count
            smallest_person = filename

        # triples to files
        utilities.create_individual_triples(
            extraction_mode, person, "writing")
        utilities.manage_mode(extraction_mode, person, graph)

        uber_graph += graph

    place.log_mapping_fails()
    organizations.log_mapping()

    logger.info(str(len(uber_graph)) + " total triples created")
    logger.info(str(largest_person) + " produces the most triples(" + str(highest_triples) + ")")
    logger.info(str(smallest_person) + " produces the least triples(" + str(least_triples) + ")")

    logger.info("Time completed: " + utilities.get_current_time())

    temp_path = "extracted_triples/writing_triples.ttl"
    utilities.create_extracted_uberfile(temp_path, uber_graph,serialization="ttl", extra_triples="../data/additional_triples.ttl")

    
  

if __name__ == "__main__":
    main()
