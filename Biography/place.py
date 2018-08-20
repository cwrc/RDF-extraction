import rdflib
PLACE_MAP = {}

"""
Class/series of functions that deal with mapping place to its respective uri
based on the places.csv

TODO:
1)create log of unmapped places
2)error handling of missing place.csv
3)review necessity of Place class

"""


def create_place_map():
    import csv
    # if searching takes too long
    # Create better searching mechanism
    # with open('geoghert_places.csv', newline='') as csvfile:
    with open('places.csv', newline='') as csvfile:
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
    value = get_attribute(tag, "current")
    if not value:
        value = get_attribute(tag, "reg")
    if not value:
        value = get_attribute(tag, "currentalternativeterm")
    if not value:
        value = str(tag.text)
        value = ' '.join(value.split())
    return value


create_place_map()


class Place(object):
    """
        Probably will remove this class and just leave the functions for address and uri but for now
        Maybe morph this class into the one for locations
        keeping for now.
    """

    def get_address(self, place_tag):
        # place_
        add_str = ''
        temp = place_tag.find("settlement")
        if temp:
            add_str += get_value(temp)
        temp = place_tag.find("region")
        if temp:
            add_str += "," + get_value(temp)
        temp = place_tag.find("geog")
        if temp:
            add_str += "," + get_value(temp)
        if add_str and add_str[0] == ",":
            add_str = add_str[1:]
        return add_str

    def __init__(self, place_tag, other_attributes=None):
        super(Place, self).__init__()
        self.address = self.get_address(place_tag)

        if self.address in PLACE_MAP:
            self.uri = PLACE_MAP[self.address]
        else:
            self.uri = None

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
    main()
