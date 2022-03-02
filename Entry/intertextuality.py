import rdflib
from rdflib import Literal
from Utils import utilities
from Utils.context import Context, get_context_type, get_event_type
from Utils.event import Event
from Utils.organizations import get_org_uri
from culturalForm import get_mapped_term

logger = utilities.config_logger("intertextuality")

INTERTEXTTYPE_MAPPING = {
    "ALLUSIONACKNOWLEDGED": "explicitAllusion",
    "ALLUSIONUNACKNOWLEDGED": "allusion",
    None: "intertextualRelationship",
    "ADAPTATION-UPDATE": "adaptation",
    # Others are just in lower case
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
def extract_influence_data(doc, person):
    context_count = 0
    event_count = 0

    contexts = doc.find_all("PINFLUENCESHER")
    for context in contexts:
        context_id = F"{person.id}_Influence_{context_count}"
        temp_context = Context(context_id, context, "PINFLUENCESHER")
        extract_subject_influenced(context,person,temp_context)
        person.add_context(temp_context)
        context_count += 1

    contexts = doc.find_all("RSHEINFLUENCED")
    for context in contexts:
        context_id = F"{person.id}_Influence_{context_count}"
        temp_context = Context(context_id, context, "RSHEINFLUENCED")
        extract_influenced_subject(context,person,temp_context)
        person.add_context(temp_context)
        context_count += 1

def extract_influenced_subject(tag, person, context):
    named_entities = []
    named_entities += utilities.get_all_other_people(tag,person)
    named_entities += utilities.get_titles(tag)
    named_entities += utilities.get_places(tag)
    named_entities += [get_org_uri(x) for x in tag.find_all("ORGNAME")]
    influence_triples = [ utilities.GeneralRelation(utilities.create_uri("cwrc","influence"), x) for x in named_entities ]
    context.link_triples(influence_triples)


   
def extract_subject_influenced(tag, person, context):
    named_entities = []
    named_entities += utilities.get_all_other_people(tag,person)
    named_entities += utilities.get_titles(tag)
    named_entities += utilities.get_places(tag)
    named_entities += [get_org_uri(x) for x in tag.find_all("ORGNAME")]
    attribute = tag.get("INFLUENCETYPE")
    if attribute:
        influence_triples = [ utilities.GeneralRelation(utilities.create_uri("cwrc",F"{attribute.lower()}Influence"), x) for x in named_entities ]
    else:
        influence_triples = [ utilities.GeneralRelation(utilities.create_uri("cwrc",F"influenceBy"), x) for x in named_entities ]

    context.link_triples(influence_triples)

def extract_intertextuality_data(doc, person):
    context_count = 0
    event_count = 0

    contexts = doc.find_all("TINTERTEXTUALITY")

    for context in contexts:
        context_id = F"{person.id}_Intertextuality_{context_count}"
        temp_context = Context(context_id, context, "TINTERTEXTUALITY")
        extract_intertextuality(context,person,temp_context)
        context_count += 1
        person.add_context(temp_context)
    

        
        # for e in events:
        #     context_id = F"{person.id}_Intertextuality_{context_count}"
        #     temp_context = Context(context_id, e, "TINTERTEXTUALITY")
        #     extract_intertextuality_data(e,person,temp_context)

        #     event_title = person.name + " - " + "Intertextuality Event"
        #     event_uri = person.id + "_IntertextualityEvent_" + str(event_count)
        #     temp_event = Event(event_title, event_uri, e, "IntertextualityEvent")
        #     temp_context.link_event(temp_event)
        #     person.add_event(temp_event)



def extract_intertextuality(tag, person, context):
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
        people = utilities.get_all_other_people(tag,person)
        entities += people
        if len(people) == 1:
            authorGender = tag.get("GENDEROFAUTHOR")
            author_name = tag.find("NAME").get_text()
            print(author_name)
            gender_triple = utilities.GeneralRelation(utilities.create_uri("cwrc","genderReported"), get_mapped_term("Gender",authorGender))
            context_id =  context.id.replace("_Intertextuality_", "_Intertextuality_CulturalForm_")
            print(context_id)
            g_context = Context(context_id, tag, "GENDER",subject_name=author_name, subject_uri=people[0], target_uri=context.target_uri,id_context=context.identifying_uri )
            g_context.link_triples(gender_triple)
            person.add_context(g_context)



    #NOTE that i'm ignoring: NB: extract ORGNAME and PLACES but use a receptionRelationship to the author or text
    intertextuality_triples = [ utilities.GeneralRelation(utilities.create_uri("cwrc",predicate), x) for x in entities ]


    # print(tag)
    # print(textscopes)
    # print(typing)
    # print(predicate)

    if textscopes:
        context.context_focus = textscopes
    
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
        # extract_intertextuality_data(soup, person)
        extract_influence_data(soup, person)
        
        graph = person.to_graph()

        utilities.create_individual_triples(
            extraction_mode, person, "intertexuality")
        utilities.manage_mode(extraction_mode, person, graph)

        uber_graph += graph

    logger.info(str(len(uber_graph)) + " triples created")
    if extraction_mode.verbosity >= 0:
        print(str(len(uber_graph)) + " total triples created")

    utilities.create_uber_triples(extraction_mode, uber_graph, "intertexuality")
    logger.info("Time completed: " + utilities.get_current_time())


if __name__ == '__main__':
    main()
