from cgitb import text
import rdflib
from rdflib import Literal
from Utils import utilities
from Utils.context import Context, get_context_type, get_event_type
from Utils.event import Event
from Utils.organizations import get_org_uri
logger = utilities.config_logger("intertextuality")

INTERTEXTTYPE_MAPPING = {
    "ALLUSIONACKNOWLEDGED": "explicitAllusion",
    "ALLUSIONUNACKNOWLEDGED": "allusion",
    None: "intertextualRelationship",
    "ADAPTATION-UPDATE": "adaptation",
    # Others are just in lower case
    # "QUOTATION": "quotation",
    # "MISQUOTATION": "misquotation",
    # "PARODY": "parody",
    # "SATIRE": "satire",
    # "IMITATION": "imitation",
    # "ANSWER": "",

}

ENTITY_TO_EXTRACT_MAP = {
    "prequel": "title",
    "continuation": "title",
}

def get_div2(tag):
    # NOTE: Might be easier with recursion

    for parent in tag.parents:
        if parent.name == "DIV2":
            return parent

    return None
def get_textscopes(tag):
    tag = get_div2(tag)
    textscopes = tag.find_all("TEXTSCOPE")
    if textscopes == []:
        logger.info(F"No corresponding textscope: {tag}")
    else:
        textscopes = [rdflib.term.URIRef(x.get("REF")) for x in textscopes ]
    return textscopes


def extract_relations(doc, person):
    paragraphs = doc.find_all("P")
    events = doc.find_all("CHRONSTRUCT")
    context_count = 0
    event_count = 0


    for p in paragraphs:
        context_id = F"{person.id}_Intertextuality_{context_count}"
        temp_context = Context(context_id, p, "TINTERTEXTUALITY")
        extract_intertextuality_data(p,person,temp_context)
        if temp_context.context_focus and len(temp_context.context_focus) > 1:
            print(temp_context)
            input()
        # if temp_context.context_focus is not None:
        #     input()
        context_count += 1
        person.add_context(temp_context)
    
    # for e in events:
    #     context_id = F"{person.id}_Intertextuality_{context_count}"
    #     extract_intertextuality_data(e,person)
    #     event_count += 1

def extract_intertextuality_data(doc, person, context):
    tags = doc.find_all("TINTERTEXTUALITY")
    for tag in tags:
        textscopes = get_textscopes(tag)
        typing = tag.get("INTERTEXTTYPE")
        predicate = None
        if typing in INTERTEXTTYPE_MAPPING:
            predicate = INTERTEXTTYPE_MAPPING[typing]
        else:
            predicate = typing.lower()

        # Determining what type of entity to extract as object
        entities = utilities.get_titles(tag)
        if predicate not in ["continuation", "prequel"]:
            entities += utilities.get_all_other_people(tag,person)

        intertextuality_triples = [ utilities.GeneralRelation(utilities.create_uri("cwrc",predicate), x) for x in entities ]

        authorGender = tag.get("GENDEROFAUTHOR")

        # print(tag)
        # print(textscopes)
        # print(typing)
        # print(predicate)

        if textscopes:
            context.context_focus = textscopes
            print(context.context_focus)
            # input()

        context.link_triples(intertextuality_triples)




    

def main():
    from bs4 import BeautifulSoup
    from biography import Biography

    extraction_mode, file_dict = utilities.parse_args(
        __file__, "Intertextuality", logger)

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
        extract_relations(soup, person)

        graph = person.to_graph()

        utilities.create_individual_triples(
            extraction_mode, person, "occcupation")
        utilities.manage_mode(extraction_mode, person, graph)

        uber_graph += graph

    logger.info(str(len(uber_graph)) + " triples created")
    if extraction_mode.verbosity >= 0:
        print(str(len(uber_graph)) + " total triples created")

    utilities.create_uber_triples(extraction_mode, uber_graph, "occcupation")
    logger.info("Time completed: " + utilities.get_current_time())


if __name__ == '__main__':
    main()
