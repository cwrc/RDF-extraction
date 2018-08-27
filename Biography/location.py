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
Status: ~55%

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
        self.value = Place(place).uri

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
    return get_attribute(tag, "REG")


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


def extract_location_data(bio, person):
    locations = bio.find_all("LOCATION")

    id = 1
    for location in locations:
        # Create context id
        location_list = []
        location_type = location.get("RELATIONTO")

        location_dict = {
            "VISITED": "visits",
            "UNKNOWN": "relatesSpatiallyTo",
            "TRAVELLED": "travelsTo",
            "LIVED": "inhabits",
            "MIGRATED": "migratesTo",
            "MOVED": "relocatesTo",
        }
        places = location.find_all("PLACE")

        """
        Notes: Lived and Moved have instructions that depend on the presence of locations in
        other tags, may have to seek clarification
        TODO: 
        1) investigate "LIVED" with multiple places and common words preceding and following places
        2) same for moved
        3) Migrated as well

        """

        if len(places) == 0:
            temp_context = Context(person.id + "_SpatialContext_" +
                                   location_dict[location_type] + "_" + str(id), location, "location", "identifying")
            person.add_context(temp_context)
            continue

        elif location_type in ["VISITED", "UNKNOWN", "TRAVELLED"]:
            predicate = location_dict[location_type]
            for place in places:
                location_list.append(Location(predicate, place))
        elif location_type == "LIVED":
            print(len(places))
            if len(places) > 1:
                log.msg(person.id)
                log.msg(str(location))
                log.msg(location_type)
            elif len(places) == 1:
                location_list.append(Location("inhabits", places[0]))

        elif location_type == "MOVED":
            continue
        elif location_type == "MIGRATED":
            continue

        temp_context = Context(person.id + "_SpatialContext_" +
                               location_dict[location_type] + "_" + str(id), location, "location")
        temp_context.link_triples(location_list)
        person.add_location(location_list)
        person.add_context(temp_context)
        id += 1


def main():
    import os
    from bs4 import BeautifulSoup
    import culturalForm

    def get_name(bio):
        return (bio.BIOGRAPHY.DIV0.STANDARD.text)

    def get_sex(bio):
        return (bio.BIOGRAPHY.get("SEX"))

    filelist = [filename for filename in sorted(os.listdir("bio_data")) if filename.endswith(".xml")]
    entry_num = 1

    uber_graph = rdflib.Graph()
    namespace_manager = rdflib.namespace.NamespaceManager(uber_graph)
    biography.bind_ns(namespace_manager, biography.NS_DICT)

    # for filename in filelist[:200]:
    # for filename in filelist[-5:]:
    for filename in filelist:
        with open("bio_data/" + filename) as f:
            soup = BeautifulSoup(f, 'lxml-xml')

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
