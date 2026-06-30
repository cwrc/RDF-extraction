import rdflib
from rdflib import Literal
from utils import utilities
from utils.context import Context, get_context_type, get_event_type, get_named_entities
from utils.event import Event
from utils.organizations import get_org_uri

logger = utilities.config_logger("writing_2")



writing_context_counts = {
    "CharacterizationContext": 0,
    "InfluenceContext": 0,
    "IntertextualityContext": 0,
    "PerformanceContext": 0,
    "ProductionContext": 0,
    "PublishingContext" : 0,
    "ReceptionContext": 0,
    "RecognitionContext": 0,
    "ResponseContext": 0,
    "SettingContext": 0,
    "TextualFeaturesContext": 0,
    "TextualHistoryContext": 0,
    "ThematicContext": 0,
    "WritingConditionsContext": 0,
    "WritingContext": 0,
}

# Mapping for PMODEOFPUBLICATION PUBLICATIONMODE values to URIs
PUBLICATION_MODE_MAPPING = {
"SELF-PUBLICATION": "selfPublication",
"PRIVATELYPRINTED": "privatelyPrinted",
"LIMITEDEDITION": "limitedEdition",
"PIRATED": "pirated",
"SUBSCRIPTION": "subscription"
}



# TODO: Review: Are these actually used/useful?
WRITING_PROPERTIES_GROUPING = utilities.WRITING_PROPERTIES.groupby(["Function Type", "Domain Type"])
SIMPLE_ENTRY_PROPERTIES = utilities.WRITING_PROPERTIES[
        (utilities.WRITING_PROPERTIES['Function Type'] == 'Standard') &
        (utilities.WRITING_PROPERTIES['Domain Type'] == 'Entry Subject')]
SIMPLE_WORK_PROPERTIES = WRITING_PROPERTIES_GROUPING.get_group(('Standard', 'Work'))

def extract_works(tag):
    """ Extract works associated with the given tag
    tag: BeautifulSoup tag to be processed
    """
    works = utilities.get_textscopes(tag)
    # if len(works) > 0:
    #     return works

    # TODO: Review: Is this needed?
    # works = utilities.get_titles(tag)

    return works


def extract_standard_properties(tag, rule):
    """ Extract standard properties based on the provided rule
    tag: BeautifulSoup tag to be processed
    rule: Series containing metadata for the tag"""

    triples = []
    property_uri = utilities.NS_DICT["cwrc"][rule["Specific Property"]]
    
    if rule["Predicate Type"] == "Attributes":
        attribute = tag.get(rule["Attribute Type"])
        if not attribute or attribute != rule["Attribute Value"]:
            return triples
            
    

    if (rule["Range Type"] == "String"):
        snippet = utilities.get_snippet(tag)
        if (rule["Specific Property"] in ["c_hasCharacterName", "c_hasThemeOrTopic"]):
            snippet = snippet.strip(".")

        triples.append(utilities.GeneralRelation(property_uri, rdflib.Literal(snippet, lang="en")))
    elif (rule["Range Type"] == "Work"):
        works = extract_works(tag)
        for work in works:
            triples.append(utilities.GeneralRelation(property_uri, work))

    elif (rule["Range Type"] == "All Named Entities"):
        for named_entity in get_named_entities(tag):
            triples.append(utilities.GeneralRelation(property_uri, named_entity))
    elif (rule["Range Type"] == "People & Organizations"):
        entities = get_named_entities(tag,entity_types=["organizations", "people"])
        for entity in entities:
            triples.append(utilities.GeneralRelation(property_uri, entity))
    elif (rule["Range Type"] == "Places"):
        entities = get_named_entities(tag,entity_types=["places"])
        for entity in entities:
            triples.append(utilities.GeneralRelation(property_uri, entity))
    else:
        logger.warning(f"Range Type not yet handled: {rule['Range Type']} for {rule['Orlando Tag']}")
        print(f"Range Type not yet handled: {rule['Range Type']} for {rule['Orlando Tag']}")
        # input()
        # triples.append(utilities.GeneralRelation(property_uri, Literal("RANGE TYPE NOT HANDLED")))



    return triples

def extract_non_standard_properties(tag, rule):
    """ Placeholder for custom extraction functions for non-standard properties
    tag: BeautifulSoup tag to be processed
    rule: Series containing metadata for the tag
    """
    triples = []
    property_uri = utilities.NS_DICT["cwrc"][rule["Specific Property"]]
    # print(f"Custom extraction needed for {rule['Orlando Tag']} with property {property_uri}")
    logger.warning(f"Custom extraction needed for {rule['Orlando Tag']} with property {property_uri}")
    # print(tag)
    # print(rule)

    if tag.name == "TMOTIF":
        motif_name = tag.get("MOTIFNAME")
        if motif_name:
            motif_name = utilities.camel_case(motif_name)
            motif_uri = utilities.make_standard_uri(motif_name + "Motif", ns="cwrc")
            triples.append(utilities.GeneralRelation(property_uri, motif_uri))
        else:
            logger.warning(f"TMOTIF tag without MOTIFNAME attribute: {tag}")
    elif tag.name == "PMODEOFPUBLICATION":
        mode = tag.get("PUBLICATIONMODE")
        if mode:
            mode_uri = utilities.make_standard_uri(PUBLICATION_MODE_MAPPING.get(mode), ns="cwrc")
            triples.append(utilities.GeneralRelation(property_uri, mode_uri))



    return triples

def extract_triples(tag,tag_info):
    """ Extract triples from a given tag based on the provided tag information
    tag: BeautifulSoup tag to be processed
    tag_info: DataFrame containing metadata for the tag

    """

    triples = []

    # print(tag_info)

    for index, rule in tag_info.iterrows():
        if rule["Function Type"] == "Standard":
            triples += extract_standard_properties(tag, rule)
        else:
            logger.warning(f"Custom Function Type not yet handled for {rule['Orlando Tag']}")
            triples += extract_non_standard_properties(tag, rule)
            continue
            # triples += extract_standard_entrySubject_triples(tag, rule, person)



    return triples



def process_tags_by_domain_type(tags, tag_metadata, works, entry_based_triples, work_based_triples, ouvre_based_triples):
    """ Process tags based on their domain type and extract triples accordingly

    tags: List of BeautifulSoup tags to be processed
    tag_metadata: DataFrame containing metadata for the tags
    works: List of works associated with the context
    entry_based_triples: List to store triples related to the entry subject
    work_based_triples: List to store triples related to works
    ouvre_based_triples: List to store triples related to the oeuvre
    """



    for domain_type in tag_metadata["Domain Type"].values:
        for tag in tags:
            print(f"Processing tag: {tag.name} with domain type: {domain_type}")
            if domain_type == "Entry Subject":
                entry_based_triples += extract_triples(tag, tag_metadata)
            elif domain_type == "Work":
                if len(works) > 0:
                    work_based_triples += extract_triples(tag, tag_metadata)
            elif domain_type == "Work ELSE Entry Subject":
                if len(works) > 0:
                    work_based_triples += extract_triples(tag, tag_metadata)
                else:
                    entry_based_triples += extract_triples(tag, tag_metadata)
            elif domain_type == "Work ELSE Entry Subject Ouvre":
                if tag.name == "TTHEMETOPIC":
                    parent = tag.find_parent("AUTHORSUMMARY")
                    if parent:
                        ouvre_based_triples += extract_triples(tag, tag_metadata)
                        continue

                if len(works) > 0:
                    work_based_triples += extract_triples(tag, tag_metadata)
                else:
                    ouvre_based_triples += extract_triples(tag, tag_metadata)
            else:
                logger.warning(f"Domain Type not yet handled: {domain_type}")
                # input()

def extract_writing_data(doc, person):
    """ Extract writing-related data from the document and add it to the person object
    doc: BeautifulSoup object representing the XML document
    person: Biography object representing the person being processed
    """

    global writing_context_counts
    writing_tag = doc.find("WRITING")
    if not writing_tag:
        logger.info(f"{person.id}: No writing tag found")
        return

    paragraphs = writing_tag.find_all("P")
    events = writing_tag.find_all("CHRONSTRUCT")

    context_tags = paragraphs + events

    # May need to handle multiple different context types
    for context_tag in context_tags:
        tag_names = list({tag.name for tag in context_tag.descendants if tag.name})
        tag_names = [x for x in tag_names if x not in utilities.CORE_TAGS]

        entry_based_triples = []
        work_based_triples = []
        ouvre_based_triples = []

        works = extract_works(context_tag)

        for tag_name in tag_names:
            if tag_name not in utilities.WRITING_PROPERTIES["Orlando Tag"].values:
                logger.warning(f"Tag not yet handled: {tag_name}")
                continue

            tags = context_tag.find_all(tag_name)
            tag_metadata = utilities.WRITING_PROPERTIES[utilities.WRITING_PROPERTIES["Orlando Tag"] == tag_name]

            process_tags_by_domain_type(tags, tag_metadata, works, entry_based_triples, work_based_triples, ouvre_based_triples)

        # TODO: Count specific properties  to get the list of  orlando tags to be given to the context creation
        # Getting tags by expected domain type
        entry_based_tags = get_orlando_tags(entry_based_triples)
        work_based_tags = get_orlando_tags(work_based_triples)
        ouvre_based_tags = get_orlando_tags(ouvre_based_triples)

        create_and_link_context(person, context_tag, entry_based_triples, entry_based_tags, person.uri, "WritingContext")
        create_and_link_context(person, context_tag, work_based_triples, work_based_tags, works, "WritingContext")
        create_and_link_context(person, context_tag, ouvre_based_triples, ouvre_based_tags, person.oeuvre_uri, "WritingContext")

def get_orlando_tags(triples):
    """ Get a list of unique orlando tags from the given triples
    triples: List of GeneralRelation objects representing the triples to be analyzed
    """
    predicates = [str(triple.predicate).split("#")[1] for triple in triples]
    filtered_df = utilities.WRITING_PROPERTIES[utilities.WRITING_PROPERTIES['Specific Property'].isin(predicates)]
    orlando_tags = filtered_df['Orlando Tag'].tolist()
    return list(set(orlando_tags))

def create_and_link_context(person, context_tag, triples, tags, context_focus, context_type):
    """ Create a context of the given type, link the triples to it, and add it to the person

    person: Biography object representing the person being processed
    context_tag: BeautifulSoup tag representing the context (paragraph or event)
    triples: List of GeneralRelation objects representing the triples to be linked to the context
    tags: List of orlando tags that were used to generate the triples
    context_focus: URI or Literal representing the focus of the context (person, work, or oeuvre)
    context_type: String representing the type of context (e.g., "WritingContext")
    """

    if len(triples) > 0:
        context_id = f"{person.id}_{context_type}_{writing_context_counts[context_type]}"
        temp_context = Context(context_id, context_tag, tags, person=person)
        temp_context.context_focus = context_focus

        # To avoid self-referential triples
        triples = [x for x in triples if x.object not in temp_context.context_focus and x.object != context_focus]

        temp_context.link_triples(triples)
        person.add_context(temp_context)
        writing_context_counts[context_type] += 1

all_textscopes_texts = []
all_textscopes_map = []

matched_titles = {}
unmatched_titles = {}
partial_matches = {}

match_counts = {}


def check_authorship(title, title_map, person):
    title_previous_sibling = title_map[title].previous_sibling

    if not title_previous_sibling or not title_previous_sibling.previous_sibling:
        return False

    if "'s " in title_previous_sibling and title_previous_sibling.previous_sibling.name == "NAME":
        name_tag = title_previous_sibling.previous_sibling
        if name_tag.get("STANDARD") == person.std_name:
            return True
        else:
            return False

    return True

def textscope_analysis(soup, person):
    textscopes = soup.find_all("TEXTSCOPE")
    for textscope in textscopes:
        if not textscope.get("PLACEHOLDER"):
            logger.warning(f"{person.id}: Textscope has no placeholder text|{textscope}")
        if not textscope.get("REF"):
            logger.warning(f"{person.id}: Textscope has no REF attribute|{textscope}")


def title_analysis(soup, person):
    titles = soup.find_all("TITLE")
    textscopes = soup.find_all("TEXTSCOPE")


    title_texts = [title.text.strip() for title in titles]
    title_texts = list(title_texts)
    title_map = dict(zip(title_texts, titles))

    # filter out textscopes that have no placeholder text
    textscopes = [textscope for textscope in textscopes if textscope.get("PLACEHOLDER")]

    textscope_strings = [textscope.get("PLACEHOLDER") for textscope in textscopes]


    textscope_strings = [ ", ".join(x.split(", ")[1:-1]) for x in textscope_strings]

    # print("\033[91m title_strings: \033[00m", title_texts)
    # print("\033[91m textscope_strings: \033[00m", textscope_strings)
    # print("\033[91m clean_textscope_strings: \033[00m", clean_textscope_strings)
    temp_matched_titles = {}
    temp_unmatched_titles = {}
    temp_partial_matches = {}


    textscope_map = dict(zip(textscope_strings, textscopes))

    for title in title_texts:
        found_match = False
        for textscope_string in textscope_strings:
            if title == textscope_string:
                if title in utilities.GENERIC_TITLES:
                    continue
                if check_authorship(title, title_map, person):
                    matched_titles[title] = textscope_map[textscope_string]
                    temp_matched_titles[title] = textscope_map[textscope_string]
                    found_match = True
                    logger.info(f"MATCHING|{title}|{textscope_map[textscope_string].get('REF')}")
                # elif

                if title in unmatched_titles:
                    del unmatched_titles[title]
                break
            elif title in textscope_string:
                partial_matches[title] = textscope_map[textscope_string]
                temp_partial_matches[title] = textscope_map[textscope_string]

        if not found_match:
            unmatched_titles[title] = title_map[title]
            temp_unmatched_titles[title] = title_map[title]

    # print("\033[91m title_texts: \033[00m", title_texts

    print("\033[91m title_texts: \033[00m", title_texts)
    print("\033[91m textscope_strings: \033[00m", textscope_strings)
    print("\033[91m title_map: \033[00m", title_map)
    print("\033[91m textscope_map: \033[00m", textscope_map)
    print("\033[91m matched_titles: \033[00m", temp_matched_titles)
    print("\033[91m unmatched_titles: \033[00m", temp_unmatched_titles)
    print("\033[91m partial_matches: \033[00m", temp_partial_matches)
    counts = {
        "matched_titles": len(temp_matched_titles),
        "unmatched_titles": len(temp_unmatched_titles),
        "partial_matches": len(temp_partial_matches),
    }
    print("\033[91m counts: \033[00m", counts)

    logger.info(f"{person.id}: {counts}")

    match_counts[person.id] = counts


def title_check(doc, person):
    titles = doc.find_all("TITLE")

    for title in titles:
        uri = utilities.get_title_uri(title, person)
        title_label = utilities.get_value(title)
        if not uri:
            logger.warning(f"FAIL|{person.id}|Title has no value|{title}|{title_label}")
        elif "cwrcdata" in uri:
            logger.warning(f"FAIL|{person.id}|Title has no URI, using placeholder|{title}|{title_label}|{uri}")
        else:
            logger.info(f"SUCCESS|{person.id}|Title has URI|{title}|{title_label}|{uri}")

def main():
    from bs4 import BeautifulSoup
    from entry.biography import Biography

    extraction_mode, file_dict = utilities.parse_args(
        __file__, "Reception", logger)

    uber_graph = utilities.create_graph()

    for filename in file_dict.keys():
        with open(filename, encoding="utf-8") as f:
            soup = BeautifulSoup(f, 'lxml-xml')

        person_id  = soup.find("ENTRY").get("ID")
        if extraction_mode.verbosity > 0:
            print(filename)
            print(file_dict[filename])
            print(person_id)
            print("*" * 55)
        person = Biography(person_id, soup)
        # textscope_analysis(soup, person)
        # title_check(soup, person)
        # title_analysis(soup, person)


        extract_writing_data(soup, person)


        graph = person.to_graph()

        utilities.create_individual_triples(
            extraction_mode, person, "Writing")
        utilities.manage_mode(extraction_mode, person, graph)

        uber_graph += graph

    logger.info("Title Analysis")
    logger.info(f"Matched Titles: {matched_titles}")
    logger.info(f"Unmatched Titles: {unmatched_titles}")
    logger.info(f"Partial Matches: {partial_matches}")

    logger.info(f"{uber_graph} triples created")
    if extraction_mode.verbosity > 0:
        print(str(len(uber_graph)) + " total triples created")

    utilities.create_uber_triples(extraction_mode, uber_graph, "writing")
    logger.info(f"Time completed:  {utilities.get_current_time()}")


if __name__ == '__main__':
    main()
