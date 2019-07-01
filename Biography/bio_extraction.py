#!/usr/bin/python3
from bs4 import BeautifulSoup
import rdflib

from biography import Biography
from log import *
from Utils.utilities import *
from Utils import utilities
import culturalForm as cf
import education
import location
import other_contexts
import occupation

# import personname
# import lifeInfo
import birthDeath

"""
This is a possible temporary main script that creates the biography related triples
TODO:
add documentation
implement personname
"""

logger = utilities.config_logger("biography")


def main():
    file_dict = utilities.parse_args(__file__, "Majority of biography related data")

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
        person = Biography(person_id, soup, cf.get_mapped_term("Gender", utilities.get_sex(soup)))
        cf.extract_cf_data(soup, person)
        other_contexts.extract_other_contexts_data(soup, person)
        occupation.extract_occupation_data(soup, person)
        birthDeath.extract_birth_data(soup, person)
        location.extract_location_data(soup, person)

        # education.extract_education_data(soup, person)
        # personname.extract_person_name(soup, person)
        # birthDeath.extract_death(soup, person)
        # lifeInfo.extract_cohabitants(soup, person)
        # lifeInfo.extract_family(soup, person)
        # lifeInfo.extract_friends_associates(soup, person)
        # lifeInfo.extract_intimate_relationships(soup, person)
        # lifeInfo.extract_childlessness(soup, person)
        # lifeInfo.extract_children(soup, person)

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
        temp_path = "extracted_triples/biography_turtle/" + person_id + "_biography.ttl"
        utilities.create_extracted_file(temp_path, person)

        uber_graph += graph
        entry_num += 1

    temp_path = "extracted_triples/biography_triples.ttl"
    create_extracted_uberfile(temp_path, uber_graph)

    cf.log_mapping_fails()
    logger.info(str(len(uber_graph)) + " total triples created")
    logger.info(str(largest_person) + " produces the most triples(" + str(highest_triples) + ")")
    logger.info(str(smallest_person) + " produces the least triples(" + str(least_triples) + ")")

    logger.info("Time completed: " + utilities.get_current_time())


if __name__ == "__main__":
    main()
