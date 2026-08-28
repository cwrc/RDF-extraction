import csv
import os
from datetime import datetime
import rdflib
from bs4 import BeautifulSoup
from rdflib import Literal, XSD
from entry.biography import Biography
from utils import utilities
from utils.context import Context, get_named_entities
from utils.organizations import get_org_uri, get_org_name
from utils.place import Place
import utils.event

logger = utilities.config_logger("CD-entry-extraction")

DATE = datetime.now().strftime("%Y-%m-%d")
COLUMNS =['Entry ID', 'Context', 'Old Context' ,'Specific Tag', 'Snippet', 'Subject Type', 'Subject SubType', 'Context Tag Type', 'Object', 'Object Type', 'Subject', 'Raw Date', 'Date', 'Raw Start Date', 'Start Date', 'End Date', 'Raw End Date', 'Shortprose' ,"CHRONCOLUMN","CHRONCOLUMN1","CHRONCOLUMN2","CHRONCOLUMN3","RELEVANCE","RELEVANCE1","RELEVANCE2","RELEVANCE3"]

writing_context_counts = {
    "CharacterizationContext": 0,
    "InfluenceContext": 0,
    "IntertextualityContext": 0,
    "PerformanceContext": 0,
    "ProductionContext": 0,
    "PublishingContext" : 0,
    "ReceptionContext" : 0,
    "RecognitionContext": 0,
    "ResponseContext": 0,
    "SettingContext": 0,
    "TextualFeaturesContext": 0,
    "TextualHistoryContext": 0,
    "ThematicContext": 0,
    "WritingConditionsContext": 0,
    "WritingContext": 0,
}



# TODO: Review: Are these actually used/useful?
WRITING_PROPERTIES_GROUPING = utilities.WRITING_PROPERTIES.groupby(["Function Type", "Domain Type"])
SIMPLE_ENTRY_PROPERTIES = utilities.WRITING_PROPERTIES[
        (utilities.WRITING_PROPERTIES['Function Type'] == 'Standard') &
        (utilities.WRITING_PROPERTIES['Domain Type'] == 'Entry Subject')]
SIMPLE_WORK_PROPERTIES = WRITING_PROPERTIES_GROUPING.get_group(('Standard', 'Work'))

def extract_works(tag):
    works = utilities.get_textscopes(tag)
    if len(works) > 0:
        return works

    works = utilities.get_titles(tag)

    return works


def extract_standard_properties(tag, rule):
    triples = []
    property_uri = utilities.NS_DICT["cwrc"][rule["Specific Property"]]

    if (rule["Range Type"] == "String"):
        snippet = utilities.get_snippet(tag)
        if (rule["Specific Property"] == "c_hasCharacterName"):
            snippet = snippet.strip(".")

        triples.append(utilities.GeneralRelation(property_uri, rdflib.Literal(snippet, lang="en")))
    elif (rule["Range Type"] == "Work"):
        works = extract_works(tag)
        for work in works:
            triples.append(utilities.GeneralRelation(property_uri, work))

    elif (rule["Range Type"] == "All Named Entities"):
        for named_entity in get_named_entities(tag):
            triples.append(utilities.GeneralRelation(property_uri, named_entity))

    return triples

def extract_non_standard_properties(tag, rule):
    triples = []

    return triples

def extract_triples(tag,tag_info):
    triples = []

    print(tag_info)

    for index, rule in tag_info.iterrows():
        if rule["Function Type"] == "Standard":
            triples += extract_standard_properties(tag, rule)
        else:
            print("Not Standard")
            logger.warning(f"Custom Function Type not yet handled for {rule['Orlando Tag']}")
            triples += extract_non_standard_properties(tag, rule)
            # triples += extract_standard_entrySubject_triples(tag, rule, person)



    return triples


def extract_writing_data(doc, person):
    global writing_context_counts
    writing_tag = doc.find("WRITING")
    if not writing_tag:
        logger.info(f"{person.id}: No writing tag found")
        return

    paragraphs = writing_tag.find_all("P")
    events = writing_tag.find_all("CHRONSTRUCT")



    # May need to handle multiple different context types
    for p in paragraphs:
        tag_names = list({tag.name for tag in p.descendants if tag.name})
        tag_names = [x for x in tag_names if x not in utilities.CORE_TAGS]

        entry_based_triples = []
        work_based_triples = []
        ouvre_based_triples = []

        for tag_name in tag_names:
            if tag_name not in utilities.WRITING_PROPERTIES["Orlando Tag"].values:
                logger.warning(f"Tag not yet handled: {tag_name}")
                continue

            tags = p.find_all(tag_name)

            tag_metadata = utilities.WRITING_PROPERTIES[utilities.WRITING_PROPERTIES["Orlando Tag"] == tag_name]


            # Get triples for which the subject of the entry is the context focus
            # TODO: we may want to loop through rows of tag_metadata if there are multiple rows with different domain types and same Orlando Tag,
            # but for now we are assuming there is only one domain type
            if tag_metadata["Domain Type"].values[0] == "Entry Subject":
                print("Entry Subject")
                for tag in tags:
                    entry_based_triples += extract_triples(tag, tag_metadata)
            elif tag_metadata["Domain Type"].values[0] == "Work":
                for tag in tags:
                    work_based_triples += extract_triples(tag, tag_metadata)
                print("Work")
            elif tag_metadata["Domain Type"].values[0] == "Work ELSE Entry Subject":
                for tag in tags:
                    works = extract_works(tag)
                    if len(works) > 0:
                        work_based_triples += extract_triples(tag, tag_metadata)
                    else:
                        entry_based_triples += extract_triples(tag, tag_metadata)
                print("Work ELSE Entry Subject")
            elif tag_metadata["Domain Type"].values[0] == "Work ELSE Entry Subject Ouvre":
                for tag in tags:
                    works = extract_works(tag)
                    if len(works) > 0:
                        work_based_triples += extract_triples(tag, tag_metadata)
                    else:
                        ouvre_based_triples += extract_triples(tag, tag_metadata)

                print("Work ELSE Entry Subject Ouvre")
                pass
            else:
                logger.warning(f"Domain Type not yet handled: {tag_metadata['Domain Type'].values[0]}")


            # Get triples for which the work is the context focus
            # if not simple_work_tags.empty:
            #     for tag in tags:
            #         work_based_triples += extract_triples(tag, tag_metadata, person)


            # Get triples for which the context focus is work or then entry subject

            # Get triples for which the context focus is work or then entry subject's ouvre


        # TODO: Count specific properties  to get the list of  orlando tags to be given to the context creation
        entry_based_tags = get_orlando_tags(entry_based_triples)
        work_based_tags = get_orlando_tags(work_based_triples)
        ouvre_based_tags = get_orlando_tags(ouvre_based_triples)


        # TODO Fix how contexts are created here, they should be created based on the type of data extracted
        # Need to handle multiple different context types
        if len(entry_based_triples) > 0:
            context_id = person.id + "_WritingContext_" + str(writing_context_counts["WritingContext"])
            temp_context = Context(context_id, p, entry_based_tags, person=person)
            temp_context.link_triples(entry_based_triples)
            person.add_context(temp_context)
            writing_context_counts["WritingContext"] += 1

        if len(work_based_triples) > 0:
            context_id = person.id + "_WritingContext_" + str(writing_context_counts["WritingContext"])
            temp_context = Context(context_id, p, work_based_tags, person=person)
            temp_context.link_triples(work_based_triples)
            person.add_context(temp_context)
            writing_context_counts["WritingContext"] += 1

        if len(ouvre_based_triples) > 0:
            context_id = person.id + "_WritingContext_" + str(writing_context_counts["WritingContext"])
            temp_context = Context(context_id, p, ouvre_based_tags, person=person)
            temp_context.link_triples(ouvre_based_triples)
            person.add_context(temp_context)
            writing_context_counts["WritingContext"] += 1


def get_orlando_tags(triples):
    predicates = [str(triple.predicate).split("#")[1] for triple in triples]
    filtered_df = utilities.WRITING_PROPERTIES[utilities.WRITING_PROPERTIES['Specific Property'].isin(predicates)]
    orlando_tags = filtered_df['Orlando Tag'].tolist()
    return list(set(orlando_tags))


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


BIOGRAPHY_TAGS = ["BIRTH", "CULTURALFORMATION", "DEATH", "EDUCATION", "FAMILY","FRIENDSASSOCIATES", "HEALTH", "INTIMATERELATIONSHIPS", "LEISUREANDSOCIETY", "LOCATION", "OCCUPATION", "OTHERLIFEEVENT", "POLITICS", "VIOLENCE", "WEALTH"]
WRITING_TAGS = ["PRODUCTION", "RECEPTION",  "TEXTUALFEATURES"]
OTHER_TAGS = ["AUTHORSUMMARY"]

DIVERSITY_CONTEXTS = {
    "Cultural Identity Context": ["CULTURALFORMATION"],
    "Education Context": ["EDUCATION"],
    "Occupation Context": ["OCCUPATION"],
    "Location Context": ["LOCATION"],
    "Politics Context": ["POLITICS"], # National & International Events?)
    "Social Context": ["LEISUREANDSOCIETY", "WEALTH", "FRIENDSASSOCIATES","OTHERLIFEEVENT"],
    "Bodily Context": ["BIRTH", "HEALTH", "DEATH", "VIOLENCE"],
    "Intimate Context": ["INTIMATERELATIONSHIPS", "FAMILY"],
    "Literary Context": ["AUTHORSUMMARY", "RLANDMARKTEXT", "RRECOGNITIONS"],
    "Intertextual Context": ["TINTERTEXTUALITY", "PINFLUENCESHER", "RSHEINFLUENCED", "PLITERARYSCHOOLS", "RFICTIONALIZATION", "PNONBOOKMEDIA"],
    "Adverse Literary Distinction Context": ["RPENALTIES", "RDESTRUCTIONOFWORK", "PNONSURVIVAL"],
    "Production Context": ["PRODUCTION"],  # (+ British Women Writers & Writing Climate Events?)
    "Reception Context": ["RECEPTION"],
    "Textual Features Context": ["TEXTUALFEATURES"],
}

TAGS_OF_INTEREST = DIVERSITY_CONTEXTS["Literary Context"] + DIVERSITY_CONTEXTS["Intertextual Context"] + DIVERSITY_CONTEXTS["Adverse Literary Distinction Context"]

ENTITIES = {
    "people": {},
    "places": {},
    "organizations": {},
    "titles": {}
}

ROWS = []

ROWS_PER_PERSON = {}

def get_diversity_context_label(tag_name):
    """ Returns the label for the diversity context based on the tag name """
    for context, tags in DIVERSITY_CONTEXTS.items():
        if tag_name in tags:
            return context
    return None

def write_dict_to_csv(data, filename):
    # Determine the maximum length of the lists in the values
    max_list_length = max((len(value) if isinstance(value, list) else 1) for value in data.values())

    # Create the header row
    header = ["Key"] + [f"Value_{i+1}" for i in range(max_list_length)]

    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(header)  # Write the header

        for key, value in data.items():
            if isinstance(value, list):
                row = [key] + value + [""] * (max_list_length - len(value))  # Pad the row with empty strings
            else:
                row = [key, value] + [""] * (max_list_length - 1)  # Pad the row with empty strings
            writer.writerow(row)


def get_mappings(doc, person):
    people = utilities.get_people_names(doc)

    places_tags = doc.find_all("PLACE")
    places = {}
    for place_tag in places_tags:
        place = Place(place_tag)
        places[place.uri] = place.address


    title_tags = doc.find_all("TITLE")
    titles = {}
    for title_tag in title_tags:
        label = utilities.get_value(title_tag)
        uri = utilities.get_title_uri(title_tag, person)
        titles[uri] = label

    organization_tags = doc.find_all("ORGNAME")
    orgs = {}
    for org_tag in organization_tags:
        uri = get_org_uri(org_tag)
        orgs[uri] = get_org_name(org_tag)

    ENTITIES["people"].update(people)
    ENTITIES["places"].update(places)
    ENTITIES["titles"].update(titles)
    ENTITIES["organizations"].update(orgs)


def format_date(date):
    # TODO: apply '-' if calendar is BC also log this date
    """ Formats date to be in usable xsd format
    # https://github.com/RDFLib/rdflib/issues/747
    :/
    Weird issue with using gYearMonth and gYear resulting in filling out the date
    ex. 1891 --> 1891-01-01
    ex. 1891-12 --> 1891-12-01
    Using normalizing fix from https://github.com/RDFLib/rdflib/issues/806
    Not too sure the side effects of this
    """

    if not date:
        return Literal("")

    if date[-1] == "-":
        date = date.strip("-")

    if len(date) == 10:
        return Literal(date, datatype=XSD.date)
    elif len(date) == 7:
        return Literal(date, datatype=XSD.date)
    elif len(date) == 4:
        return Literal(date, datatype=XSD.date)
    else:
        return Literal(date)




def get_event_details(doc):
    details = {}

    details["CHRONCOLUMN"] = doc.get("CHRONCOLUMN")
    details["CHRONCOLUMN1"] = doc.get("CHRONCOLUMN1")
    details["CHRONCOLUMN2"] = doc.get("CHRONCOLUMN2")
    details["CHRONCOLUMN3"] = doc.get("CHRONCOLUMN3")
    details["RELEVANCE"] = doc.get("RELEVANCE")
    details["RELEVANCE1"] = doc.get("RELEVANCE1")
    details["RELEVANCE2"] = doc.get("RELEVANCE2")
    details["RELEVANCE3"] = doc.get("RELEVANCE3")

    date_tag = utils.event.get_date_tag(doc)
    if date_tag.name != "DATERANGE":
        details["Raw Date"] = date_tag.get("VALUE")
        details["Date"] =  str(format_date(date_tag.get("VALUE")))
        # details["date format"] = get_date_format(details["date"])
    else:
        details["Raw Start Date"] = date_tag.get("FROM")
        details["Start Date"] =  str(format_date(date_tag.get("FROM")))
        details["End Date"] =  str(format_date(date_tag.get("TO")))
        details["Raw End Date"] = date_tag.get("TO")


    shortprose_tag = doc.find("SHORTPROSE")
    if shortprose_tag:
        details["Shortprose"] = utilities.get_snippet(shortprose_tag)
    else:
        details["Shortprose"] = None

    return details


def get_rows(context, context_label,tag, snippet ,person, subject=None, old_context=None):
    basic_details = {
        "Entry ID": person.id,
        "Context": context_label,
        "Specific Tag": context,
        "Snippet": snippet,
        "Subject Type": "Person",
        "Subject SubType": "Entry Subject",
        "Old Context": old_context
    }

    if not subject or len(subject) == 0:
        # basic_details["Subject"] = person.uri
        subject = [person.uri]
    elif len(subject) == 1:
        basic_details["Subject Type"] = "Title"
        basic_details["Subject SubType"] = "Textscope Text"
        # basic_details["Subject"] = subject[0]
    else :
        logger.warning(f"Multiple subjects found for {person.id} in {context}")
        basic_details["Subject Type"] = "Title"
        basic_details["Subject SubType"] = "Textscope Text"
        #TODO: NEED TO HANDLE MULTIPLE TEXTSCOPES
        # basic_details["Subject"] = subject[0]


    if tag.name == "P":
        basic_details["Context Tag Type"] = "Paragraph"
    elif tag.name == "CHRONSTRUCT":
        basic_details["Context Tag Type"] = "Event"
        basic_details.update(get_event_details(tag))
    else:
        basic_details["Context Tag Type"] = "More Specific Tag"




    rows = []

    for x in subject:
        people = get_named_entities(tag, author=person, entity_types=["people"])
        places = get_named_entities(tag,entity_types=["places"])
        organizations = get_named_entities(tag,entity_types=["organizations"])
        titles = get_named_entities(tag,entity_types=["titles"],author=person)

        entity_mappings = [
        (people, "Person"),
        (places, "Place"),
        (organizations, "Organization"),
        (titles, "Title")]

        for entities, entity_type in entity_mappings:
            for entity in entities:
                row = basic_details.copy()
                row["Object"] = entity
                row["Object Type"] = entity_type
                row["Subject"] = x
                rows.append(row)


    return rows

def extract_adhoc_data(doc, person):
    global ROWS
    person_rows = []
    for bio_tag in BIOGRAPHY_TAGS:
        tags = doc.find_all(bio_tag)
        for tag in tags:
            paragraphs = tag.find_all("P") + tag.find_all("CHRONSTRUCT")
            for p in paragraphs:
                snippet = utilities.get_snippet(p)
                person_rows += get_rows(bio_tag, get_diversity_context_label(bio_tag) ,p, snippet, person,subject=None, old_context=bio_tag)


    for writing_tag in WRITING_TAGS:
        tags = doc.find_all(writing_tag)
        for tag in tags:
            textscopes = utilities.get_textscopes(tag)

            paragraphs = tag.find_all("P") + tag.find_all("CHRONSTRUCT")


            if len(textscopes) > 0:
                for p in paragraphs:
                    specific_tags = p.find_all(TAGS_OF_INTEREST)
                    specific_tag_texts = [x.text for x in specific_tags]
                    snippet = utilities.get_snippet(p)
                    for x in specific_tags:
                        person_rows += get_rows(x.name,get_diversity_context_label(x.name), x, utilities.get_snippet(x), person,subject=textscopes, old_context=writing_tag)

                    for x in specific_tag_texts:
                        snippet = snippet.replace(x, "....")
                    p = utilities.remove_tags(TAGS_OF_INTEREST, p)

                    person_rows += get_rows(writing_tag,get_diversity_context_label(writing_tag), p, snippet, person,subject=textscopes, old_context=writing_tag)
            else:
                for p in paragraphs:
                    snippet = utilities.get_snippet(p)
                    specific_tags = p.find_all(TAGS_OF_INTEREST)
                    specific_tag_texts = [x.text for x in specific_tags]
                    snippet = utilities.get_snippet(p)
                    for x in specific_tags:
                        person_rows += get_rows(x.name,get_diversity_context_label(x.name), x, utilities.get_snippet(x), person,subject=None, old_context=writing_tag)

                    for x in specific_tag_texts:
                        snippet = snippet.replace(x, "....")
                    p = utilities.remove_tags(TAGS_OF_INTEREST, p)

                    person_rows += get_rows(writing_tag,get_diversity_context_label(writing_tag), p,snippet, person,subject=None, old_context=writing_tag)

    # tags = doc.find_all("AUTHORSUMMARY")
    # for tag in tags:
    #     paragraphs = tag.find_all("P")
    #     for p in paragraphs:
    #         snippet = utilities.get_snippet(p)
    #         ROWS += get_rows("AUTHORSUMMARY", "Literary Context", p, snippet ,person,subject=None, old_context="AUTHORSUMMARY")
    ROWS_PER_PERSON[person.id] = len(person_rows)
    ROWS += person_rows



def save_rows_to_csv(rows, filename, columns=None):
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    keys = rows[0].keys()
    if columns:
        keys = columns
    with open(filename, 'w', newline='', encoding="utf-8") as output_file:
        dict_writer = csv.DictWriter(output_file, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(rows)



def extract_author_titles(doc, person):
    # titles = utilities.get_textscopes(doc)
    titles = doc.find_all("TEXTSCOPE")
    for title in titles:
        uri = title.get("REF")
        if not title.get("PLACEHOLDER"):
            logger.warning(f"{person.id}: Textscope has no placeholder text|{title}")
        if not uri:
            logger.warning(f"{person.id}: Textscope has no REF attribute|{title}")
            continue
        ROWS.append({
          "Title URI": uri,
          "Author URI": person.uri,
        })



def main():

    extraction_mode, file_dict = utilities.parse_args(
        __file__, "Reception", logger)

    uber_graph = utilities.create_graph()

    for filename in file_dict.keys():
        with open(filename, encoding="utf-8" ) as f:
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
        extract_adhoc_data(soup, person)
        # extract_author_titles(soup, person)
        get_mappings(soup, person)





    # logger.info("Title Analysis")
    # logger.info(f"Matched Titles: {matched_titles}")
    # logger.info(f"Unmatched Titles: {unmatched_titles}")
    # logger.info(f"Partial Matches: {partial_matches}")
    # logger.info(ENTITIES)
    save_rows_to_csv(
        ROWS, f'context_diversity/results/{DATE}/context-based_relationships.csv', columns=COLUMNS)
    
    # save_rows_to_csv(ROWS, 'adhoc-authors.csv')
    for key, value in ENTITIES.items():
        write_dict_to_csv(
            value, f"context_diversity/results/{DATE}/context-based_reference_{key}.csv")
    # exit()
    logger.info(f"{len(uber_graph)} triples created")
    if extraction_mode.verbosity > 0:
        print(f"{len(uber_graph)} total triples created")



    logger.info(f"Time completed: {utilities.get_current_time()}")


if __name__ == '__main__':
    main()
