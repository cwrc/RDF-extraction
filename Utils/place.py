import rdflib
PLACE_MAP = {}
# TODO remove circular dependence and add find places to this class
# from utilities import *


"""
Class/series of functions that deal with mapping place to its respective uri
based on the places.csv

TODO:
1)create log of unmapped places
2)error handling of missing place.csv
3)review necessity of Place class
"""


def create_place_map(path=None):
    import csv
    # if searching takes too long
    # Create better searching mechanism
    # with open('geoghert_places.csv', newline='') as csvfile:
    if not path:
        path = '../data/places.csv'
    with open(path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        for row in reader:
            if row[0] not in PLACE_MAP:
                PLACE_MAP[row[0]] = row[1]


def get_attribute(tag, attribute):
    value = tag.get(attribute)
    if value:
        return value
    return None


def get_value(tag):
    value = get_attribute(tag, "CURRENT")
    if not value:
        value = get_attribute(tag, "REG")
    if not value:
        value = get_attribute(tag, "CURRENTALTERNATIVETERM")
    if not value:
        value = str(tag.text)
        value = ' '.join(value.split())
    return value


class Place(object):
    """
        Probably will remove this class and just leave the functions for address and uri but for now
        Maybe morph this class into the one for locations
        keeping for now.
    """

    def get_address(self, place_tag):
        # place_
        add_str = ''
        temp = place_tag.find("SETTLEMENT")
        if temp:
            add_str += get_value(temp)
        temp = place_tag.find("REGION")
        if temp:
            add_str += "," + get_value(temp)
        temp = place_tag.find("GEOG")
        if temp:
            add_str += "," + get_value(temp)
        if add_str and add_str[0] == ",":
            add_str = add_str[1:]
        return add_str

    def __init__(self, place_tag, other_attributes=None):
        super(Place, self).__init__()
        self.address = self.get_address(place_tag)

        if self.address in PLACE_MAP:
            self.uri = rdflib.term.URIRef(PLACE_MAP[self.address])
        else:
            self.uri = rdflib.term.Literal(self.address)

    # Hopefully won't have to create triples about a place just provide a uri but
    def to_triple(self, person_uri):
        # p = self.predicate + self.reported
        # o = self.value
        # figure out if i can just return tuple or triple without creating a whole graph
        pass

    def __str__(self):
        string = "\taddress: " + str(self.address) + "\n"
        string += "\turi: " + str(self.uri) + "\n"
        return string


def main():
    print(PLACE_MAP)


if __name__ == "__main__":
    create_place_map("data/places.csv")
    main()
else:
    create_place_map()
