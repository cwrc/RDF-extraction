import rdflib
PLACE_MAP = {}
UNMAPPED_OCCURENCES = {}


def config_logger(name, verbose=False):
    # Will likely want to convert logging records to be json formatted and based on external file.
    import logging

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler("log/" + name + ".log", mode="w")
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(levelname)s - %(asctime)s - %(message)s ')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    if verbose:
        ch = logging.StreamHandler()
        ch.setLevel(logging.ERROR)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    return logger


logger = config_logger("place")


"""
Class/series of functions that deal with mapping place to its respective uri
based on the places.csv

TODO:
1)create log of unmapped places
2)error handling of missing place.csv
3)create a dictionary of places that failed to map with counts
4)review necessity of Place class
"""


def create_place_map(path=None):
    import csv
    # if searching takes too long
    # Create better searching mechanism
    if not path:
        path = '../data/places.csv'
    with open(path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        for row in reader:
            if row[0] not in PLACE_MAP:
                PLACE_MAP[row[0]] = row[1]


def create_place_rdf(path=None):
    import csv
    
    g = utilities.create_graph()

    if not path:
        path = '../data/places.csv'
    with open(path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        for row in reader:
            print(row[0], row[1])
            place = rdflib.URIRef(row[1])
            label = rdflib.Literal(row[0].replace(",", ", "))
            g.add(
                (place, utilities.NS_DICT["rdf"].type, utilities.NS_DICT["crm"].E53_Place))
            g.add((place, utilities.NS_DICT["rdfs"].label, label))
            g.add(
                (place, utilities.NS_DICT["crm"].P2_has_type, utilities.NS_DICT["biography"].MappedPlace))

    with open("places.ttl", "w", encoding="utf-8") as f:
        f.write("#" + str(len(g)) + " triples created\n")
        f.write(g.serialize(format="ttl").decode())


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


def log_mapping_fails():
    log_str = "\nUnique Missed Places: " + str(len(UNMAPPED_OCCURENCES.keys())) + "\n"

    from collections import OrderedDict

    new_dict = OrderedDict(sorted(UNMAPPED_OCCURENCES.items(), key=lambda t: t[1], reverse=True))
    count = 0
    for y in new_dict.keys():
        log_str += "\t" + str(new_dict[y]) + ": " + y + "\n"
        count += new_dict[y]
    log_str += "\tTotal missed places: " + str(count) + "\n\n"

    print(log_str)
    logger.info(log_str)


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
        if self.address == '':
            self.address = place_tag.text

        # TODO: Use PLACENAME as address perhaps
        if self.address in UNMAPPED_OCCURENCES:
            self.uri = None
            UNMAPPED_OCCURENCES[self.address] += 1
        elif self.address in PLACE_MAP:
            self.uri = rdflib.term.URIRef(PLACE_MAP[self.address])
            # TODO: get place string from uri --> extend csv?
        else:
            logger.warning("Unable to find matching place instance for: " +
                           self.address + "(" + str(place_tag) + ")")
            self.uri = None
            UNMAPPED_OCCURENCES[self.address] = 1

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
