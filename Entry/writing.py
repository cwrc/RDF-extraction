import rdflib
from rdflib import Literal
from Utils import utilities
from Utils.context import Context, get_context_type, get_event_type, get_named_entities
from Utils.event import Event
from Utils.organizations import get_org_uri
from culturalForm import get_mapped_term

logger = utilities.config_logger("writing_2")



writing_context_counts = {
    "CharacterizationContext": 0,
    "InfluenceContext": 0,
    "IntertextualityContext": 0,
    "PerformanceContext": 0,
    "ProductionContext": 0,
    "PublishingContext" : 0,
    "ReceptionContext" : 0,
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
            temp_context = Context(context_id, p, entry_based_tags)
            temp_context.link_triples(entry_based_triples)
            person.add_context(temp_context)
            writing_context_counts["WritingContext"] += 1

        if len(work_based_triples) > 0:
            context_id = person.id + "_WritingContext_" + str(writing_context_counts["WritingContext"])
            temp_context = Context(context_id, p, work_based_tags)
            temp_context.link_triples(work_based_triples)
            person.add_context(temp_context)
            writing_context_counts["WritingContext"] += 1
            
        if len(ouvre_based_triples) > 0:
            context_id = person.id + "_WritingContext_" + str(writing_context_counts["WritingContext"])
            temp_context = Context(context_id, p, ouvre_based_tags)
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
    

def main():
    from bs4 import BeautifulSoup
    from biography import Biography

    extraction_mode, file_dict = utilities.parse_args(
        __file__, "Reception", logger)

    uber_graph = utilities.create_graph()

    for filename in file_dict.keys():
        with open(filename) as f:
            soup = BeautifulSoup(f, 'lxml-xml')

        person_id  = soup.find("ENTRY").get("ID")
        if extraction_mode.verbosity > 0:
            print(filename)
            print(file_dict[filename])
            print(person_id)
            print("*" * 55)
        person = Biography(person_id, soup)
        textscope_analysis(soup, person)
        # title_analysis(soup, person)
        continue
        extract_writing_data(soup, person)
        
        graph = person.to_graph()

        utilities.create_individual_triples(
            extraction_mode, person, "reception")
        utilities.manage_mode(extraction_mode, person, graph)

        uber_graph += graph
    
    logger.info("Title Analysis")
    logger.info(f"Matched Titles: {matched_titles}")
    logger.info(f"Unmatched Titles: {unmatched_titles}")
    logger.info(f"Partial Matches: {partial_matches}")
    
    exit()
    logger.info(str(len(uber_graph)) + " triples created")
    if extraction_mode.verbosity > 0:
        print(str(len(uber_graph)) + " total triples created")

    utilities.create_uber_triples(extraction_mode, uber_graph, "reception")
    logger.info("Time completed: " + utilities.get_current_time())


if __name__ == '__main__':
    main()
