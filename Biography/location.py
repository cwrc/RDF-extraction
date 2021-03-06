#!/usr/bin/python3


from biography import Biography
from Utils.context import Context
from Utils.event import Event
from Utils.place import Place
from Utils import utilities

"""
Status: ~80%
"""

logger = utilities.config_logger("location")
uber_graph = utilities.create_graph()

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

        self.uri = utilities.create_uri("cwrc", self.predicate)

    def to_tuple(self, person_uri):
        return ((person_uri, self.uri, self.value))

    def to_triple(self, person):
        g = utilities.create_graph()
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
    from bs4 import BeautifulSoup
    import culturalForm

    file_dict = utilities.parse_args(__file__, "Location")

    entry_num = 1

    uber_graph = utilities.create_graph()

    for filename in file_dict.keys():
        with open(filename) as f:
            soup = BeautifulSoup(f, 'lxml-xml')

        person_id = filename.split("/")[-1][:6]

        print(filename)
        print(file_dict[filename])
        print(person_id)
        print("*" * 55)

        person = Biography(person_id, soup, culturalForm.get_mapped_term("Gender", utilities.get_sex(soup)))
        extract_location_data(soup, person)

        graph = person.to_graph()

        temp_path = "extracted_triples/location_turtle/" + person_id + "_location.ttl"
        utilities.create_extracted_file(temp_path, person)

        uber_graph += graph
        entry_num += 1

    print("UberGraph is size:", len(uber_graph))
    temp_path = "extracted_triples/location.ttl"
    utilities.create_extracted_uberfile(temp_path, uber_graph)

    temp_path = "extracted_triples/location.rdf"
    utilities.create_extracted_uberfile(temp_path, uber_graph, "pretty-xml")


if __name__ == "__main__":
    main()
