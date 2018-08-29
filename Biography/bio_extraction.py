#!/usr/bin/python3
# from Env import env
# import islandora_auth as login
from bs4 import BeautifulSoup
import rdflib

from biography import Biography, bind_ns, NS_DICT
from log import *
import culturalForm as cf
import education
import location
import other_contexts

# gurjap's files
import birthDeath
import scrapeFamily
"""
This is a possible temporary main script that creates the biography related triples
TODO: 
add documentation
implement location
implement education
implement personname
implement occupation

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


def get_name(bio):
    return (bio.BIOGRAPHY.DIV0.STANDARD.text)


def get_sex(bio):
    return (bio.BIOGRAPHY.get("SEX"))


def main():
    import os
    filelist = [filename for filename in sorted(os.listdir("/Users/gurjapsingh/Documents/UoGuelph Projects/biography/")) if filename.endswith(".xml")]
    # filelist.remove("fielmi-b.xml")
    numTriples = 0
    entry_num = 1
    global uber_graph

    highest_triples = 0
    least_triples = 0
    smallest_person = None
    largest_person = None

    # 328686 triples created
    # for filename in filelist[:200]:
    # for filename in filelist[:2]:
    fileo = open("namesAndTriplesNewer.txt","w",encoding="utf-8")

    for filename in filelist:
    # for filename in ["woolvi-b.xml","notlfr-b.xml","atwoma-b.xml","levyam-b.xml"]:
    # for filename in filelist[1365:]:
    # for filename in filelist[:25]:
    # for filename in ["bedfsy-b.xml","blesma-b.xml","butlel-b.xml"]:
    # for filename in ["delama-b.xml"]:
        with open("/Users/gurjapsingh/Documents/UoGuelph Projects/biography/" + filename,encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'lxml-xml')

        print(filename)
        person = Biography(filename[:-6], get_name(soup), cf.get_mapped_term("Gender", get_sex(soup)))

        # education.extract_education_data(soup, person)

        # cf.extract_cf_data(soup, person)
        # other_contexts.extract_health_contexts_data(soup, person)
        birthDeath.getBirth(soup,person)
        birthDeath.getDeath(soup,person)
        scrapeFamily.cohabitantsCheck(soup,person)
        scrapeFamily.getFamilyInfo(soup,person)
        scrapeFamily.friendsAssociateCheck(soup,person)
        scrapeFamily.intimateRelationshipsCheck(soup,person)
        scrapeFamily.childlessnessCheck(soup,person)
        scrapeFamily.childrenCheck(soup,person)
        # location.extract_location_data(soup, person)
        # other_contexts.extract_other_contexts_data(soup, person)

        graph = person.to_graph()
        graph.remove((person.uri,NS_DICT["foaf"].name,None))
        graph.remove((person.uri,NS_DICT["foaf"].isPrimaryTopicOf,None))
        graph.remove((person.uri,NS_DICT["cwrc"].hasGender,None))
        graph.remove((person.uri,NS_DICT["rdfs"].label,None))
        numTriples += len(graph)
        fileo.write("%s:%d,total:%d\n" % (filename, len(graph),numTriples))
        print("length: ",len(graph))
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
        # file = open("culturalform_triples/" + str(person.id) + "-cf.txt", "w")
        # file.write("#" + str(len(graph)) + " triples created\n")
        # file.write(person.to_file(graph))
        # file.close()

        uber_graph += graph
        entry_num += 1
        # exit()
    fileo.close()

    turtle_log.subtitle(str(len(uber_graph)) + " triples created")
    turtle_log.msg(uber_graph.serialize(format="ttl").decode(), stdout=False)
    turtle_log.msg("")

    file = open("all_triples.ttl", "w",encoding="utf-8")
    file.write("#" + str(len(uber_graph)) + " triples created\n")
    file.write(uber_graph.serialize(format="ttl").decode())

    extract_log.test_name("Cultural Form mapping results")
    cf.log_mapping_fails(extract_log, log, detail=False)
    extract_log.msg("See CF Error Log for more indepth logging about failures:")

    print(largest_person, "produces the most triples(" + str(highest_triples) + ")")
    print(smallest_person, "produces the least triples(" + str(least_triples) + ")")
    print(numTriples, "THIS IS THE AMOUNT OF TRIPLES PLEASE WORK PROPERLY")
    exit()


def test():
    exit()

if __name__ == "__main__":
    # auth = [env.env("USER_NAME"), env.env("PASSWORD")]
    # login.main(auth)
    # test()
    main()
