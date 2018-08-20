#!/usr/bin/python3

# from Env import env
# import islandora_auth as login

from difflib import get_close_matches
from rdflib import RDF, RDFS, Literal
import rdflib
import biography
from context import Context
from log import *
from place import Place


"""
Status: ~85%
Most of cultural forms have been mapped
    TODO: Review missing religions & PAs

Forebear still needs to be handled/attempted with a query
--> load up gurjap's produced graph and query it  for forebear info to test
temp solution until endpoint is active

Events need to be created--> bigger issue
Waiting on event modelling and time
"""

# temp log library for debugging --> to be eventually replaced with proper logging library
# from log import *
log = Log("log/location/errors")
log.test_name("Location extraction Error Logging")
extract_log = Log("log/location/extraction")
extract_log.test_name("Location extraction Test Logging")
turtle_log = Log("log/location/triples")
turtle_log.test_name("Location extracted Triples")

uber_graph = rdflib.Graph()
namespace_manager = rdflib.namespace.NamespaceManager(uber_graph)
biography.bind_ns(namespace_manager, biography.NS_DICT)


class Location(object):
    """docstring for Location
    """

    def __init__(self, predicate, place, other_attributes=None):
        super(Location, self).__init__()
        self.predicate = predicate
        temp_place = Place(place)
        if temp_place.uri:
            self.value = rdflib.term.URIRef(temp_place.uri)
        else:
            self.value = Literal(temp_place.address)

        if other_attributes:
            self.uri = other_attributes

        self.uri = str(biography.NS_DICT["cwrc"]) + self.predicate
        self.uri = rdflib.term.URIRef(self.uri)

    # TODO figure out if i can just return tuple or triple without creating a whole graph
    # Evaluate efficency of creating this graph or just returning a tuple and have the biography deal with it
    def to_tuple(self, person_uri):
        return ((person_uri, self.uri, self.value))

    def to_triple(self, person):
        g = rdflib.Graph()
        namespace_manager = rdflib.namespace.NamespaceManager(g)
        biography.bind_ns(namespace_manager, biography.NS_DICT)
        g.add((person.uri, self.uri, self.value))
        return g

    def __str__(self):
        string = "\tURI: " + str(self.uri) + "\n"
        string += "\tpredicate: " + str(self.predicate) + "\n"
        string += "\tvalue: " + str(self.value) + "\n"

        return string


def get_reg(tag):
    return get_attribute(tag, "reg")


def get_attribute(tag, attribute):
    value = tag.get(attribute)
    if value:
        return value
    return None


def get_value(tag):
    value = get_reg(tag)
    if not value:
        value = get_attribute(tag, "CURRENTALTERNATIVETERM")
    if not value:
        value = str(tag.text)
        value = ' '.join(value.split())
    return value


# bare min event scrape
def find_event(type, tag, person):
    event_tag = tag.find_all("chronstruct")
    for x in event_tag:
        # print(type)
        # print(event_tag)
        event_body = ""

        for y in x.find_all("chronprose"):
            event_body += str(y)

        date = None
        for y in x.find_all("date"):
            date = y.text
        person.add_event(event_body, type, date)

    pass


def find_cultural_forms(cf, person):
    cf_list = []

# Also handles politics tag as well


def extract_location_data(bio, person):
    locations = bio.find_all("location")
    cf_subelements = ["classissue", "raceandethnicity", "nationalityissue", "sexuality", "religion"]
    cf_subelements_count = {"classissue": 0, "raceandethnicity": 0,
                            "nationalityissue": 0, "sexuality": 0, "religion": 0}

    id = 1
    for location in locations:
        # Create context id
        location_list = []
        location_type = location.get("relationto")
        log.msg(str(location))
        log.msg(location_type)

        if location_type in ["VISITED", "UNKNOWN"]:
            if location_type == "VISITED":
                predicate = "visits"
            else:
                predicate = "relatesSpatiallyTo"

            places = location.find_all("place")
            for place in places:
                location_list.append(Location(predicate, place))

        elif location_type == "LIVED":
            pass
        elif location_type == "MOVED":
            pass

        elif location_type == "TRAVELLED":
            pass
        elif location_type == "MIGRATED":
            pass

        temp_context = Context(person.id + "_spatial_context" + str(id), location, "location")
        temp_context.link_triples(location_list)
        person.add_location(location_list)
        person.add_context(temp_context)

        id += 1

        # if cf.div2:
        #     temp_context = None
        #     cf_list = None

        #     temp_context = Context(person.id + "_culturalformation" + "_context" + str(id), cf)
        #     cf_list = find_cultural_forms(cf.div2, person)
        #     temp_context.link_triples(cf_list)

        #     person.add_context(temp_context)
        #     person.add_cultural_form(cf_list)
        #     id += 1


def get_name(bio):
    return (bio.biography.div0.standard.text)


def get_sex(bio):
    return (bio.biography.get("sex"))


def log_mapping_fails(main_log, error_log, detail=True):
    main_log.subtitle("Attempts: #" + str(map_attempt))
    main_log.subtitle("Fails: #" + str(map_fail))
    main_log.subtitle("Success: #" + str(map_success))
    main_log.separ()
    print()
    main_log.subtitle("Failure Details:")
    total_unmapped = 0
    for x in fail_dict.keys():
        num = len(fail_dict[x].keys())
        total_unmapped += num
        error_log.subtitle(x.split("#")[1] + ":" + str(num))
    main_log.subtitle("Failed to find " + str(total_unmapped) + " unique terms")

    print()
    error_log.separ("#")
    if not detail:
        log_mapping_fails(extract_log, log)
        return

    from collections import OrderedDict
    for x in fail_dict.keys():
        error_log.msg(x.split("#")[1] + "(" + str(len(fail_dict[x].keys())) + " unique)" + ":")

        new_dict = OrderedDict(sorted(fail_dict[x].items(), key=lambda t: t[1], reverse=True))
        count = 0
        for y in new_dict.keys():
            error_log.msg("\t" + str(new_dict[y]) + ": " + y)
            count += new_dict[y]
        error_log.msg("Total missed " + x.split("#")[1] + ": " + str(count))
        error_log.separ()
        print()


def main():
    import os
    from bs4 import BeautifulSoup
    import culturalForm
    def get_name(bio):
        return (bio.biography.div0.standard.text)

    def get_sex(bio):
        return (bio.biography.get("sex"))

    filelist = [filename for filename in sorted(os.listdir("bio_data")) if filename.endswith(".xml")]
    entry_num = 1

    uber_graph = rdflib.Graph()
    namespace_manager = rdflib.namespace.NamespaceManager(uber_graph)
    biography.bind_ns(namespace_manager, biography.NS_DICT)

    # for filename in filelist[:200]:
    # for filename in filelist[-5:]:
    for filename in filelist:
        with open("bio_data/" + filename) as f:
            soup = BeautifulSoup(f, 'lxml')

        print(filename)
        test_person = biography.Biography(
            filename[:-6], get_name(soup), culturalForm.get_mapped_term("Gender", get_sex(soup)))

        extract_location_data(soup, test_person)

        graph = test_person.to_graph()

        extract_log.subtitle("Entry #" + str(entry_num))
        extract_log.msg(str(test_person))
        extract_log.subtitle(str(len(graph)) + " triples created")
        extract_log.msg(test_person.to_file(graph))
        extract_log.subtitle("Entry #" + str(entry_num))
        extract_log.msg("\n\n")

        uber_graph += graph
        entry_num += 1

    turtle_log.subtitle(str(len(uber_graph)) + " triples created")
    turtle_log.msg(uber_graph.serialize(format="ttl").decode(), stdout=False)
    turtle_log.msg("")


def test():
    exit()

if __name__ == "__main__":
    # auth = [env.env("USER_NAME"), env.env("PASSWORD")]
    # login.main(auth)
    # test()
    main()
