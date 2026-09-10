#TODO: Note: Current code is non-functional, it was stub taken from another script and needs to be re-written (writing.py)
# SEE: https://github.com/cwrc/RDF-extraction/issues/26 for more details

import rdflib
from rdflib import Literal
from utils import utilities
from utils.context import Context, get_context_type, get_event_type, get_named_entities
from utils.event import Event
from utils.organizations import get_org_uri
from culturalForm import get_mapped_term


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
    from entry.biography import Biography

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
