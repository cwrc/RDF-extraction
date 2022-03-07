#!/usr/bin/python3
from bs4 import BeautifulSoup
from Utils import utilities, place, organizations
from biography import Biography
import culturalForm as cf
import location
import birthDeath
import occupation

import other_contexts
import lifeInfo
import education
import personname

"""
This is a possible temporary main script that creates the biography related triples
TODO:add documentation
implement personname
"""

logger = utilities.config_logger("all_bio")


def main():
    extraction_mode, file_dict = utilities.parse_args(
        __file__, "Majority of biography related data", logger)

    uber_graph = utilities.create_graph()

    highest_triples = 0
    least_triples = 0
    smallest_person = None
    largest_person = None
    total_triples = 0
    logger.info("Time started: " + utilities.get_current_time() + "\n")

    for filename in file_dict.keys():
        person_id = filename.split("/")[-1][:6]
        
        with open(filename) as f:
            soup = BeautifulSoup(f, 'lxml-xml')
        


        print(person_id)
        print(file_dict[filename])
        print("*" * 55)
        person = Biography(person_id, soup)
        occupation.extract_occupation_data(soup, person)
        birthDeath.extract_death_data(soup, person)
        birthDeath.extract_birth_data(soup, person)
        location.extract_location_data(soup, person)
        cf.extract_cf_data(soup, person)
        
        # Not yet reviewed
        # other_contexts.extract_other_contexts_data(soup, person)
        # lifeInfo.extract_family_data(soup, person)
        # lifeInfo.extract_intimate_relationships_data(soup, person)
        # lifeInfo.extract_friend_data(soup, person)
        # personname.extract_person_name(soup, person)
        # education.extract_education_data(soup, person)

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
            extraction_mode, person, "biography")
        utilities.manage_mode(extraction_mode, person, graph)

        uber_graph += graph

    place.log_mapping_fails()
    cf.log_mapping_fails()
    occupation.log_mapping_fails()
    organizations.log_mapping()
    total_triples = len(uber_graph)
    avg = total_triples / len(file_dict.keys())
    logger.info(F"{len(file_dict.keys())} files have been converted")
    logger.info(F"{total_triples} total triples created")
    logger.info(F"{largest_person} produces the most triples({highest_triples})")
    logger.info(F"{smallest_person} produces the least triples({least_triples})")
    logger.info(F"{avg} avg amount of triples per file")

    logger.info(F"Time completed: {utilities.get_current_time()}")



    temp_path = "extracted_triples/biography_triples.ttl"
    utilities.create_extracted_uberfile(temp_path, uber_graph,serialization="ttl", extra_triples="../data/additional_triples.ttl")

if __name__ == "__main__":
    main()
