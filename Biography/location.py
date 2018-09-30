#!/usr/bin/python3

# from Env import env
# import islandora_auth as login

import rdflib
import biography
from context import Context
from log import Log
from place import Place
from event import Event


"""
Status: ~80%
"""

# temp log library for debugging -->
# to be eventually replaced with proper logging library
log = Log("log/location/errors")
log.test_name("Location extraction Error Logging")
extract_log = Log("log/location/extraction")
extract_log.test_name("Location extraction Test Logging")
turtle_log = Log("log/location/triples")
turtle_log.test_name("Location extracted Triples")

uber_graph = rdflib.Graph()
namespace_manager = rdflib.namespace.NamespaceManager(uber_graph)
biography.bind_ns(namespace_manager, biography.NS_DICT)

location_occurences = {}
location_count = {
    "VISITED": 0,
    "UNKNOWN": 0,
    "TRAVELLED": 0,
    "LIVED": 0,
    "MIGRATED": 0,
    "MOVED": 0,
}

location_event_count = {
    "VISITED": 0,
    "UNKNOWN": 0,
    "TRAVELLED": 0,
    "LIVED": 0,
    "MIGRATED": 0,
    "MOVED": 0,
}


class Location(object):
    """docstring for Location
    """
    location_dict = {
        "VISITED": "visits",
        "UNKNOWN": "relatesSpatiallyTo",
        "TRAVELLED": "travelsTo",
        "LIVED": "inhabits",
        "MIGRATED": "migratesTo",
        "MOVED": "relocatesTo",
    }

    def __init__(self, predicate, place, other_attributes=None):
        super(Location, self).__init__()
        self.predicate = predicate
        self.value = Place(place).uri

        if other_attributes:
            self.uri = other_attributes

        self.uri = biography.create_uri("cwrc", self.predicate)

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


def check_occurence(place_uri):
    global location_occurences
    for x in location_occurences.keys():
        if place_uri in location_occurences[x]:
            return True

    return False


def find_locations(tag, relation):
    """Creates location list given the tag
    """
    global location_occurences
    location_list = []
    location_type = relation
    places = tag.find_all("PLACE")

    if location_type in ["VISITED", "UNKNOWN", "TRAVELLED", "LIVED"]:
        predicate = Location.location_dict[location_type]
        for place in places:
            location_list.append(Location(predicate, place))
    elif location_type == "MOVED":
        if len(places) > 1:
            for place in places:
                if "leaving " + place.text in tag.text or "left " + place.text in tag.text:
                    place_uri = Place(place).uri
                    location_occurences["MOVED"].remove(place_uri)
                    if not check_occurence(place_uri):
                        location_list.append(Location("relatesSpatiallyTo", place))
                    location_occurences["MOVED"].append(place_uri)
                else:
                    location_list.append(Location("relocatesTo", place))

        else:
            for place in places:
                location_list.append(Location("relocatesTo", place))
    elif location_type == "MIGRATED":
        if len(places) == 1:
            location_list.append(Location("migratesTo", places[0]))
        else:
            for place in places:
                # TODO: clean up these if statements
                if "leaving " + place.text in tag.text or "left " + place.text in tag.text or "from " + place.text in tag.text:
                    location_list.append(Location("migratesFrom", place))
                elif "to " + place.text in tag.text or "to the " + place.text in tag.text or "at " + place.text in tag.text:
                    location_list.append(Location("migratesTo", place))

    return location_list


def get_place_occurences(locations):
    """Gets all the places associated with the different placec tags
    """
    location_occurences = {
        "VISITED": [],
        "UNKNOWN": [],
        "TRAVELLED": [],
        "LIVED": [],
        "MIGRATED": [],
        "MOVED": [],
    }

    for location in locations:
        places = location.find_all("PLACE")
        location_occurences[location.get("RELATIONTO")] += ([Place(x).uri for x in places])
    return location_occurences


def extract_locations(tag_list, context_type, person, list_type="paragraphs"):
    """ Creates the location relation and ascribes them to the person along with the associated
        contexts and event
    """
    global location_count
    global location_event_count

    for tag in tag_list:
        temp_context = None
        location_list = None
        context_id = person.id + "_SpatialContext" + "-" + str(Location.location_dict[context_type])
        location_count[context_type] += 1
        context_id += "_" + str(location_count[context_type])

        location_list = find_locations(tag, context_type)
        if location_list:
            temp_context = Context(context_id, tag, "SpatialContext")
            temp_context.link_triples(location_list)
            person.add_location(location_list)
        else:
            temp_context = Context(context_id, tag, "SpatialContext", "identifying")

        if list_type == "events":
            location_event_count[context_type] += 1
            event_title = person.name + " - " + "Spatial (" + Location.location_dict[context_type] + ") Event"
            event_uri = person.id + "_" + \
                Location.location_dict[context_type] + "_Event" + str(location_event_count[context_type])
            temp_event = Event(event_title, event_uri, tag)
            temp_context.link_event(temp_event)
            person.add_event(temp_event)

        person.add_context(temp_context)


def extract_location_data(bio, person):
    locations = bio.find_all("LOCATION")
    global location_occurences
    global location_count
    global location_event_count
    location_occurences = get_place_occurences(locations)
    location_count = {
        "VISITED": 0,
        "UNKNOWN": 0,
        "TRAVELLED": 0,
        "LIVED": 0,
        "MIGRATED": 0,
        "MOVED": 0,
    }
    location_event_count = {
        "VISITED": 0,
        "UNKNOWN": 0,
        "TRAVELLED": 0,
        "LIVED": 0,
        "MIGRATED": 0,
        "MOVED": 0,
    }

    for location in locations:
        location_type = location.get("RELATIONTO")

        paragraphs = location.find_all("P")
        events = location.find_all("CHRONSTRUCT")
        extract_locations(paragraphs, location_type, person)
        extract_locations(events, location_type, person, "events")


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
    test_cases = ["shakwi-b.xml", "woolvi-b.xml", "seacma-b.xml", "atwoma-b.xml",
                  "alcolo-b.xml", "bronem-b.xml", "bronch-b.xml", "levyam-b.xml"]
    # for filename in filelist:
    for filename in test_cases:
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

        file = open("location_turtle/" + filename[:-6] + "_location.ttl", "w", encoding="utf-8")
        file.write("#" + str(len(graph)) + " triples created\n")
        file.write(graph.serialize(format="ttl").decode())
        file.close()

        uber_graph += graph
        entry_num += 1

    turtle_log.subtitle(str(len(uber_graph)) + " triples created")
    turtle_log.msg(uber_graph.serialize(format="ttl").decode(), stdout=False)
    turtle_log.msg("")

    file = open("location.ttl", "w", encoding="utf-8")
    file.write("#" + str(len(uber_graph)) + " triples created\n")
    file.write(uber_graph.serialize(format="ttl").decode())

    file = open("location.rdf", "w", encoding="utf-8")
    file.write("#" + str(len(uber_graph)) + " triples created\n")
    file.write(uber_graph.serialize(format="pretty-xml").decode())


if __name__ == "__main__":
    main()
