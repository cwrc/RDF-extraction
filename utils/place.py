import rdflib
PLACE_MAP = {}

# TODO create a better methodology for tracking unmapped places 
# to account for get_places() being called multiple times
UNMAPPED_OCCURENCES = {}

UNMAPPED_DETAILED_OCCURENCES = []

def config_logger(name, verbose=3):
    # Will likely want to convert logging records to be json formatted and based on external file.
    # Add metadata info about time of extraction run and remove asctime
    import logging
    import os
    if not os.path.exists("log"):
        os.makedirs("log")

    if name != "utilities":
        name += '_extraction'

    name = name.lower()
    logger = logging.getLogger(name)

    logger.setLevel(logging.INFO)
    fh = logging.FileHandler("log/" + name + ".log", mode="w")
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter(
        '%(levelname)s - %(asctime)s {%(module)s.py:%(lineno)d} - %(message)s ')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Handling of stdout logging
    if verbose == 0:
        ch = logging.StreamHandler()
        ch.setLevel(logging.ERROR)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    elif verbose == 1:
        ch = logging.StreamHandler()
        ch.setLevel(logging.WARNING)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    elif verbose > 2:
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
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
        path = 'data/places.csv'
    with open(path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        for row in reader:
            if row[0] not in PLACE_MAP:
                PLACE_MAP[row[0]] = row[1]



def get_value(tag):
    value = tag.get("CURRENT")
    if not value:
        value = tag.get("REG")
    if not value:
        value = tag.get("CURRENTALTERNATIVETERM")
    if not value:
        value = str(tag.text)
        value = ' '.join(value.split())
    return value

def placejson_to_csv():
    import csv
    import os

    log_dir = 'log'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    csv_filepath = os.path.join(log_dir, 'place_log.csv')
    with open(csv_filepath, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['entry_id', 'tag', 'text', 'address used', 'PLACENAME', 'PLACENAME (REG)', 'PLACENAME (CURRENT)', 'SETTLEMENT', 'SETTLEMENT (REG)', 'SETTLEMENT (CURRENT)', 'REGION', 'REGION (REG)', 'REGION (CURRENT)', 'GEOG', 'GEOG (REG)', 'GEOG (CURRENT)', 'AREA', 'AREA (REG)', 'AREA (CURRENT)', "ADDRESS",'ADDRESS (REG)', 'ADDRESS (CURRENT)']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for place in UNMAPPED_DETAILED_OCCURENCES:
            writer.writerow(place)


def log_mapping_fails():
    log_str = "\nUnique Missed Terms: " + str(len(UNMAPPED_OCCURENCES.keys())) + "\n"

    from collections import OrderedDict

    new_dict = OrderedDict(sorted(UNMAPPED_OCCURENCES.items(), key=lambda t: t[1], reverse=True))
    count = 0
    for y in new_dict.keys():
        log_str += "\t" + str(new_dict[y]) + ": " + y + "\n"
        count += new_dict[y]
    log_str += "\tTotal missed places: " + str(count) + "\n\n"

    placejson_to_csv()
    print(log_str)
    logger.info(log_str)
    
def place_to_json(tag, entry_id, address):
    place_dict = {
        "entry_id": entry_id,
        "tag": str(tag).replace("\n", ""),
        "text": str(tag.text).replace("\n", ""),
        "address used": address,
        "ADDRESS": "",
        "PLACENAME": "",
        "PLACENAME (REG)": "",
        "PLACENAME (CURRENT)": "",
        "SETTLEMENT": "",
        "SETTLEMENT (REG)": "",
        "SETTLEMENT (CURRENT)": "",
        "REGION": "",
        "REGION (REG)": "",
        "REGION (CURRENT)": "",
        "GEOG": "",
        "GEOG (REG)": "",
        "GEOG (CURRENT)": "",
        "AREA": "",
        "AREA (REG)": "",
        "AREA (CURRENT)": "",
    }
    
    subtags = ["ADDRESS","PLACENAME", "SETTLEMENT", "REGION", "GEOG", "AREA"]
    for subtag in subtags:
        subtag_element = tag.find(subtag)
        if subtag_element is not None:
            place_dict[subtag] = subtag_element.text
            place_dict[f"{subtag} (REG)"] = subtag_element.get("REG", "")
            place_dict[f"{subtag} (CURRENT)"] = subtag_element.get("CURRENT", "")
    
    return place_dict
    


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

    def __init__(self, place_tag, other_attributes=None, entry_id=None):
        super(Place, self).__init__()
        self.tag = place_tag
        self.address = self.get_address(place_tag)
        if self.address == '':
            self.address = place_tag.text

        # TODO: Use PLACENAME as address perhaps
        if self.address in UNMAPPED_OCCURENCES:
            self.uri = rdflib.term.Literal(self.address)
            UNMAPPED_DETAILED_OCCURENCES.append(place_to_json(place_tag, entry_id, self.address))
            UNMAPPED_OCCURENCES[self.address] += 1
        elif self.address in PLACE_MAP:
            self.uri = rdflib.term.URIRef(PLACE_MAP[self.address])
            # TODO: get place string from uri --> extend csv?
        else:
            logger.warning(F"Unable to find matching place instance for: {self.address} ({str(place_tag)}) in entry: {entry_id}")
            logger.warning(F"{place_to_json(place_tag, entry_id, self.address)}")
            self.uri = rdflib.term.Literal(self.address)
            UNMAPPED_DETAILED_OCCURENCES.append(place_to_json(place_tag, entry_id, self.address))
            UNMAPPED_OCCURENCES[self.address] = 1

    # Hopefully won't have to create triples about a place just provide a uri but
    def to_triple(self, person_uri):
        # p = self.predicate + self.reported
        # o = self.value
        # figure out if i can just return tuple or triple without creating a whole graph
        pass

    def __str__(self):
        string = f"\taddress: {self.address}\n"
        string += f"\turi: {self.uri}\n"
        return string


def main():
    print(PLACE_MAP)


if __name__ == "__main__":
    create_place_map("data/places.csv")
    main()
else:
    create_place_map()
