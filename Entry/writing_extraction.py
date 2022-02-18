#!/usr/bin/python3
from bs4 import BeautifulSoup
from biography import Biography
from Utils import utilities, place, organizations
from Utils.context import Context, get_context_type, get_event_type
from Utils.event import Event
from Utils.organizations import get_org_uri
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
    for x in genres:
        general_relations.append(utilities.GeneralRelation(cwrc.genericRangeIncludes, rdflib.Literal(x)))

    print(genres)

    extent = tag.find_all("EXTENTOFOEUVRE")
    for x in extent:
        general_relations.append(utilities.GeneralRelation(cwrc.extent, rdflib.Literal(utilities.limit_words(x.text, 35))))

    context_id = person.id + "_WritingContext_" + str(count)
    temp_context = Context(context_id, tag, "AUTHORSUMMARY", subject_uri=person.oeuvre_uri)
    temp_context.link_triples(general_relations)
    person.add_context(temp_context)

    events = tag.find("CHRONSTRUCT")
    if events:
        logger.warning("Events found in AUTHORSUMMARY of entry: " + person.id + "\n" + str(events))

    return count


def main():
    from biography import Biography
    
  

if __name__ == "__main__":
    main()
