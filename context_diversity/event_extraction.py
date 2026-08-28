from datetime import datetime
from itertools import combinations
import csv
import os
from bs4 import BeautifulSoup
from rdflib import Literal, XSD
from utils import utilities
from utils.place import Place
import utils.event
from utils.organizations import get_org_uri, get_org_name
from utils.context import get_named_entities

logger = utilities.config_logger("CD-event-extraction")

DATE = datetime.now().strftime("%Y-%m-%d")

EVENT_PATH = "/Users/alliyyamo/Desktop/orlando-2.0-c-modelling/textbase-pubc/events-pubc/"
PEOPLE = []
PLACES = []
ORGS = []

UNMATCHED_PEOPLE = []
EVENT_FILES = os.listdir(EVENT_PATH)
EVENT_FILES.sort()
EVENT_FILES = [x for x in EVENT_FILES if x.endswith(".xml")]


def write_dict_to_csv(data, filename):
    # Determine the maximum length of the lists in the values
    max_list_length = max((len(value) if isinstance(value, list) else 1) for value in data.values())

    # Create the header row
    header = ["Key"] + [f"Value_{i+1}" for i in range(max_list_length)]

    with open(filename, mode='w', newline='', encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(header)  # Write the header

        for key, value in data.items():
            if isinstance(value, list):
                row = [key] + value + [""] * (max_list_length - len(value))  # Pad the row with empty strings
            else:
                row = [key, value] + [""] * (max_list_length - 1)  # Pad the row with empty strings
            writer.writerow(row)

    print(f"Saved {len(data)} rows to {filename}")

def save_rows_to_csv(rows, filename, columns=None):
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    keys = rows[0].keys()
    if columns:
        keys = columns
    with open(filename, 'w', newline='', encoding="utf-8") as output_file:
        dict_writer = csv.DictWriter(output_file, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(rows)
    print(f"Saved {len(rows)} rows to {filename}")


def format_date(date):
    # TODO: apply '-' if calendar is BC also log this date
    """ Formats date to be in usable xsd format
    # https://github.com/RDFLib/rdflib/issues/747
    :/
    Weird issue with using gYearMonth and gYear resulting in filling out the date
    ex. 1891 --> 1891-01-01
    ex. 1891-12 --> 1891-12-01
    Using normalizing fix from https://github.com/RDFLib/rdflib/issues/806
    Not too sure the side effects of this
    """
    if date[-1] == "-":
        date = date.strip("-")

    if len(date) == 10:
        return Literal(date, datatype=XSD.date)
    elif len(date) == 7:
        return Literal(date, datatype=XSD.date)
    elif len(date) == 4:
        return Literal(date, datatype=XSD.date)
    else:
        return Literal(date)

COLUMNS = [
"Context",
"Context Type",
"Event Title",
"ID",
"Event URI",
"Snippet",
"CHRONCOLUMN",
"CHRONCOLUMN1",
"CHRONCOLUMN2",
"CHRONCOLUMN3",
"RELEVANCE",
"RELEVANCE1",
"RELEVANCE2",
"RELEVANCE3",
"Raw Date",
"Date",
"Year",
"Raw Start Date",
"Start Date",
"Start Year",
"End Date",
"Raw End Date",
"End Year",
"Shortprose",
"Entity URI",
"Entity Type"
]
COLUMNS2 = [
"Context",
"Event Title",
"ID",
"Event URI",
"Snippet",
"CHRONCOLUMN",
"CHRONCOLUMN1",
"CHRONCOLUMN2",
"CHRONCOLUMN3",
"RELEVANCE",
"RELEVANCE1",
"RELEVANCE2",
"RELEVANCE3",
"Raw Date",
"Date",
"Year",
"Raw Start Date",
"Start Date",
"Start Year",
"Raw End Date",
"End Date",
"End Year",
"Shortprose",
"Entity 1 URI",
"Entity 1 Type",
"Entity 2 URI",
"Entity 2 Type"
]

def get_diverse_context_type(value):
    """ Returns the context type based on the value provided.
    :param value: The value to determine the context type from.
    :return: The context type as a string.
    """
    if value == "SOCIALCLIMATE":
        return "Social Context"
    elif value == "NATIONALINTERNATIONAL":
        return "Politics Context"
    elif value == "BRITISHWOMENWRITERS":
        return "Production Context"
    elif value == "WRITINGCLIMATE":
        return "Production Context"
    else:
        return "Unknown Context"

def get_event_details(doc, main_id):
    details = {}
    details["Event Title"] = doc.find("DOCTITLE").text
    details["Context"] = "CHRONEVENT"
    details["ID"] = main_id
    details["Event URI"] = utilities.NS_DICT["orlando"][main_id]
    event_tag = doc.find("CHRONSTRUCT")
    details["Snippet"] = utilities.get_snippet(event_tag)
    details["Context Type"] = get_diverse_context_type(event_tag.get("CHRONCOLUMN"))
    details["CHRONCOLUMN"] = event_tag.get("CHRONCOLUMN")
    details["CHRONCOLUMN1"] = event_tag.get("CHRONCOLUMN1")
    details["CHRONCOLUMN2"] = event_tag.get("CHRONCOLUMN2")
    details["CHRONCOLUMN3"] = event_tag.get("CHRONCOLUMN3")
    details["RELEVANCE"] = event_tag.get("RELEVANCE")
    details["RELEVANCE1"] = event_tag.get("RELEVANCE1")
    details["RELEVANCE2"] = event_tag.get("RELEVANCE2")
    details["RELEVANCE3"] = event_tag.get("RELEVANCE3")

    date_tag = utils.event.get_date_tag(event_tag)
    if date_tag.name != "DATERANGE":
        details["Raw Date"] = date_tag.get("VALUE")
        details["Date"] =  str(format_date(date_tag.get("VALUE")))
        details["Year"] =  details["Date"][:4]
        # details["date format"] = get_date_format(details["date"])
    else:
        details["Raw Start Date"] = date_tag.get("FROM")
        details["Start Date"] =  str(format_date(date_tag.get("FROM")))
        details["Start Year"] =  details["Start Date"][:4]

        details["End Date"] =  str(format_date(date_tag.get("TO")))
        details["End Year"] =  details["End Date"][:4]
        details["Raw End Date"] = date_tag.get("TO")


    shortprose_tag = doc.find("SHORTPROSE")
    if shortprose_tag:
        details["Shortprose"] = utilities.get_snippet(shortprose_tag)
    else:
        details["Shortprose"] = None

    return details
    # details["event_type"] = get_event_type(doc)

ENTITIES = {
    "people": {},
    "places": {},
    "organizations": {},
    "titles": {}
}

def get_mappings(doc):
    people = utilities.get_people_names(doc)

    places_tags = doc.find_all("PLACE")
    places = {}
    for place_tag in places_tags:
        place = Place(place_tag)
        places[place.uri] = place.address


    title_tags = doc.find_all("TITLE")
    titles = {}
    for title_tag in title_tags:
        label = utilities.get_value(title_tag)
        uri = utilities.get_title_uri(title_tag)
        titles[uri] = label

    organization_tags = doc.find_all("ORGNAME")
    orgs = {}
    for org_tag in organization_tags:
        uri = get_org_uri(org_tag)
        orgs[uri] = get_org_name(org_tag)

    ENTITIES["people"].update(people)
    ENTITIES["places"].update(places)
    ENTITIES["titles"].update(titles)
    ENTITIES["organizations"].update(orgs)




def get_entity_rows(tag, basic_details=None):
    if basic_details is None:
        basic_details = {}
    rows = []

    people = get_named_entities(tag, entity_types=["people"])
    places = get_named_entities(tag,entity_types=["places"])
    organizations = get_named_entities(tag,entity_types=["organizations"])
    titles = get_named_entities(tag,entity_types=["titles"])

    entity_mappings = [
    (people, "Person"),
    (places, "Place"),
    (organizations, "Organization"),
    (titles, "Title")]

    for entities, entity_type in entity_mappings:
        for entity in entities:
            row = basic_details.copy()
            # row = {}
            row["Entity URI"] = entity
            row["Entity Type"] = entity_type
            rows.append(row)

    # print(rows)
    # input()
    return rows


def get_entity_combos(tag, basic_details=None):

    if basic_details is None:
        basic_details = {}
    rows = []
    combos = []

    people = get_named_entities(tag, entity_types=["people"])
    places = get_named_entities(tag,entity_types=["places"])
    organizations = get_named_entities(tag,entity_types=["organizations"])
    titles = get_named_entities(tag,entity_types=["titles"])

    entity_mappings = [
    (people, "Person"),
    (places, "Place"),
    (organizations, "Organization"),
    (titles, "Title")]

    for entities, entity_type in entity_mappings:
        for entity in entities:
            # row = basic_details.copy()
            row = {}
            row["Entity URI"] = entity
            row["Entity Type"] = entity_type
            rows.append(row)



    for combo in combinations(rows, 2):
        row = basic_details.copy()
        row["Entity 1 URI"] = combo[0]["Entity URI"]
        row["Entity 1 Type"] = combo[0]["Entity Type"]
        row["Entity 2 URI"] = combo[1]["Entity URI"]
        row["Entity 2 Type"] = combo[1]["Entity Type"]

        combos.append(row)

    # input()
    # Extra rows where there is only one entity
    # if len(combos) == 0 and len(rows) == 1:
    #     row = basic_details.copy()
    #     row["Entity 1 URI"] = rows[0]["Entity URI"]
    #     row["Entity 1 Type"] = rows[0]["Entity Type"]
    #     row["Entity 2 URI"] = None
    #     row["Entity 2 Type"] = None

    #     combos.append(row)
    return combos



files_of_interest = ["orlando_f4e7a041-0ce5-4a0c-b683-042748f2213b.xml"]

def main():
    count = 0
    total = len(EVENT_FILES)
    ROWS = []
    COMBOS = []
    # for filename in files_of_interest:
    for filename in EVENT_FILES:
        with open(EVENT_PATH + filename, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, 'lxml-xml')

        count+=1
        main_id = str(filename).replace(".xml", "").replace("orlando_", "")
        print(F"{count}/{total}:")
        print(F"MAIN ID: {main_id}")
        get_mappings(soup.find("CHRONEVENT"))
        # get_roles(soup, main_id)
        event_details = get_event_details(soup, main_id)
        # rows = get_entity_rows(soup.find("CHRONEVENT"), event_details)

        event_tag = soup.find("CHRONEVENT")
        event_tag = utilities.remove_unwanted_tags(event_tag)
        rows = get_entity_rows(event_tag, event_details)
        ROWS += rows
        # COMBOS += get_entity_combos(event_tag, event_details)

        print("=====================================")

    save_rows_to_csv(
        ROWS, f"context_diversity/results/{DATE}/events-to-entities.csv", columns=COLUMNS)
    # save_rows_to_csv(COMBOS, "event-entities-to-entities.csv", columns=COLUMNS2)
    # save_rows_to_csv(PEOPLE, "bib-adhoc_people.csv")
    # save_rows_to_csv(UNMATCHED_PEOPLE, "bib-adhoc_unmatched_people.csv")
    for key, value in ENTITIES.items():
        write_dict_to_csv(
            value, f"context_diversity/results/{DATE}/event_reference_{key}.csv")

if __name__ == "__main__":
    main()
