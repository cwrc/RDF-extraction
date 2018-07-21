#!/usr/bin/python3
# from Env import env
# import islandora_auth as login
from bs4 import BeautifulSoup
from difflib import get_close_matches
from rdflib import RDF, RDFS, Literal
import rdflib

from biography import Biography, bind_ns, NS_DICT
from context import Context, strip_all_whitespace
from log import *
from event import Event
import culturalForm as cf
import education
import other_contexts

"""
This is a possible temporary main script that creates the biography related triples
TODO: 
add documentation
implement other contexts
implement occupation

"""

# temp log library for debugging --> to be eventually replaced with proper logging library
# from log import *
log = Log("log/biography/errors")
log.test_name("Biography extraction Error Logging")
extract_log = Log("log/biography/extraction")
extract_log.test_name("Biography extraction Test Logging")
turtle_log = Log("log/biography/triples")
turtle_log.test_name("Biography extracted Triples")

uber_graph = rdflib.Graph()
namespace_manager = rdflib.namespace.NamespaceManager(uber_graph)
bind_ns(namespace_manager, NS_DICT)


def get_name(bio):
    return (bio.biography.div0.standard.text)


def get_sex(bio):
    return (bio.biography.get("sex"))


def main():
    import os
    filelist = [filename for filename in sorted(os.listdir("bio_data")) if filename.endswith(".xml")]
    entry_num = 1
    global uber_graph

    # for filename in filelist[:200]:
    # for filename in filelist[:2]:
    # for filename in ["sample-b.xml","atwoma-b.xml"]:
    for filename in filelist:
        with open("bio_data/" + filename) as f:
            soup = BeautifulSoup(f, 'lxml')

        print(filename)
        person = Biography(filename[:-6], get_name(soup), cf.get_mapped_term("Gender", get_sex(soup)))

        cf.extract_cf_data(soup, person)
        # education.extract_education_data(soup, person)
        # other_contexts.extract_other_contexts_data(soup, person)

        graph = person.to_graph()

        # Logging bits
        extract_log.subtitle("Entry #" + str(entry_num))
        extract_log.msg(str(person))
        extract_log.subtitle(str(len(graph)) + " triples created")
        extract_log.msg(person.to_file(graph))
        extract_log.subtitle("Entry #" + str(entry_num))
        extract_log.msg("\n\n")

        # triples to files
        # file = open("culturalform_triples/" + str(person.id) + "-cf.ttl", "w")
        # file.write("#" + str(len(graph)) + " triples created\n")
        # file.write(person.to_file(graph))
        # file.close()

        uber_graph += graph
        entry_num += 1

    turtle_log.subtitle(str(len(uber_graph)) + " triples created")
    turtle_log.msg(uber_graph.serialize(format="ttl").decode(), stdout=False)
    turtle_log.msg("")

    extract_log.test_name("Cultural Form mapping results")
    cf.log_mapping_fails(extract_log, log, detail=False)
    extract_log.msg("See CF Error Log for more indepth logging about failures:")
    exit()


def test():
    exit()

if __name__ == "__main__":
    # auth = [env.env("USER_NAME"), env.env("PASSWORD")]
    # login.main(auth)
    # test()
    main()
