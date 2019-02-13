#!/usr/bin/python3
# from Env import env
# import islandora_auth as login
from bs4 import BeautifulSoup
import rdflib

from biography import Biography, bind_ns, NS_DICT, get_name, get_sex
from log import *
from utilities import *
import culturalForm as cf
import education
import location
import other_contexts

import occupation
import personname

# gurjap's files
import birthDeath
import lifeInfo
"""
This is a possible temporary main script that creates the biography related triples
TODO:
add documentation
implement personname
"""

# temp log library for debugging --> to be eventually replaced with proper logging library
log = Log("log/biography/errors")
log.test_name("Biography extraction Error Logging")
extract_log = Log("log/biography/extraction")
extract_log.test_name("Biography extraction Test Logging")
turtle_log = Log("log/biography/triples")
turtle_log.test_name("Biography extracted Triples")

uber_graph = rdflib.Graph()
namespace_manager = rdflib.namespace.NamespaceManager(uber_graph)
bind_ns(namespace_manager, NS_DICT)


def main():
    import os
    filelist = [filename for filename in sorted(os.listdir("bio_data/")) if filename.endswith(".xml")]
    filelist.remove("fielmi-b-transformed.xml")

    numTriples = 0
    entry_num = 1
    global uber_graph

    highest_triples = 0
    least_triples = 0
    smallest_person = None
    largest_person = None

    test_cases = ["shakwi-b-transformed.xml", "woolvi-b-transformed.xml", "seacma-b-transformed.xml", "atwoma-b-transformed.xml",
                  "alcolo-b-transformed.xml", "bronem-b-transformed.xml", "bronch-b-transformed.xml", "levyam-b-transformed.xml"]

    test_cases += ["aguigr-b-transformed.xml"]
    # for testing suffrage
    test_cases += ["taylha-b-transformed.xml"]
    # for testing Africanist
    test_cases += ["angema-b-transformed.xml"]

    # for filename in filelist:
    for filename in test_cases:
        with open("bio_data/" + filename, encoding="utf-8") as f:
            soup = BeautifulSoup(f, 'lxml-xml')

        print("===========", filename, "=============")
        person = Biography(filename[:6], get_name(soup), cf.get_mapped_term("Gender", get_sex(soup)))
        cf.extract_cf_data(soup, person)
        other_contexts.extract_other_contexts_data(soup, person)
        location.extract_location_data(soup, person)
        occupation.extract_occupation_data(soup, person)
        education.extract_education_data(soup, person)

        # personname.extract_person_name(soup, person)
        birthDeath.extract_birth(soup, person)
        birthDeath.extract_death(soup, person)
        lifeInfo.extract_cohabitants(soup, person)
        lifeInfo.extract_family(soup, person)
        lifeInfo.extract_friends_associates(soup, person)
        lifeInfo.extract_intimate_relationships(soup, person)
        lifeInfo.extract_childlessness(soup, person)
        lifeInfo.extract_children(soup, person)

        person.name = get_readable_name(soup)

        graph = person.to_graph()
        numTriples += len(graph)

        # print("length: ",len(graph))
        # Logging bits
        extract_log.subtitle("Entry #" + str(entry_num))
        extract_log.msg(str(person))
        extract_log.subtitle(str(len(graph)) + " triples created")
        extract_log.msg(person.to_file(graph))
        extract_log.subtitle("Entry #" + str(entry_num))
        extract_log.msg("\n\n")

        if len(graph) > highest_triples:
            highest_triples = len(graph)
            largest_person = filename
        if least_triples == 0 or len(graph) < least_triples:
            least_triples = len(graph)
            smallest_person = filename

        # triples to files
        temp_path = "extracted_triples/Bio_Triples/" + str(person.id) + ".ttl"
        create_extracted_file(temp_path, person)

        uber_graph += graph
        entry_num += 1

    turtle_log.subtitle(str(len(uber_graph)) + " triples created")
    turtle_log.msg(uber_graph.serialize(format="ttl").decode(), stdout=False)
    turtle_log.msg("")

    temp_path = "extracted_triples/all_triples.ttl"
    create_extracted_uberfile(temp_path, uber_graph)

    extract_log.test_name("Cultural Form mapping results")
    cf.log_mapping_fails(extract_log, log, detail=False)
    extract_log.msg("See CF Error Log for more indepth logging about failures:")

    log.subtitle(str(len(uber_graph)) + " total triples created")
    log.msg(str(largest_person) + " produces the most triples(" + str(highest_triples) + ")")
    log.msg(str(smallest_person) + " produces the least triples(" + str(least_triples) + ")")


if __name__ == "__main__":
    main()
    # auth = [env.env("USER_NAME"), env.env("PASSWORD")]
    # login.main(auth)
    # test()
