#!/usr/bin/python3

from rdflib import Literal
from utils import utilities
from utils.context import Context, get_context_type, get_event_type
from utils.event import Event

"""
    TODO:
    rename ReligousName once the typo is fixed within the ontology
"""

logger = utilities.config_logger("personname")

NAME_TYPE_MAPPING = {
    "BIRTHNAME": "Birthname",
    "INDEXED": "IndexedName",
    "MARRIED": "MarriedName",
    "NICKNAME": "Nickname",
    "PSEUDONYM": "Pseudonym",
    "RELIGIOUSNAME": "ReligiousName",
    "ROYAL": "RoyalName",
    "SELFCONSTRUCTED": "SelfConstructedName",
    "STYLED": "StyledName",
    "TITLED": "TitledName",
    "STANDARD": "IndexedName",
    "DOCTITLE": "PreferredName",
}

# Names of the entry as a whole, found outside of PERSONNAME
ENTRY_NAME_TAGS = ["STANDARD", "DOCTITLE"]
PERSONNAME_TAGS = [x for x in NAME_TYPE_MAPPING if x not in ENTRY_NAME_TAGS]

# Tags whose text shouldn't be treated as part of a name
NOTE_TAGS = ["SCHOLARNOTE", "RESEARCHNOTE", "BIBCITS", "BIBCIT"]


class Name(object):
    """docstring for Name
        A name of the biographee, all properties are attached to the name entity
        which is only connected to the context via cwrc:name
    """
    ATTRIBUTE_MAP = {
        "ABUSIVE": "AbusiveName",
        "HONORIFIC": "HonorificName",
        "CRYPTIC": "CrypticName",
        "LOCAL": "LocalName",
        "ROMANCE": "RomanceName",
        "LITERARY": "LiteraryName",
        "FAMILIAR": "FamiliarName",
    }
    NAME_PART_MAP = {
        "GIVEN": "Forename",
        "SURNAME": "Surname",
    }

    def __init__(self, name_tag, person_id):
        super(Name, self).__init__()
        self.person_id = person_id

        self.label = get_name_text(name_tag, use_reg=name_tag.name == "BIRTHNAME")
        if name_tag.name == "DOCTITLE":
            self.label = self.label.split(":")[0].strip()

        self.uri = utilities.make_standard_uri(F"{person_id} NameEnt {self.label}")

        self.types = [NAME_TYPE_MAPPING[name_tag.name]]
        for attribute in ["NAMECONNOTATION", "NAMESIGNIFIER", "NAMETYPE"]:
            value = name_tag.get(attribute)
            if value in self.ATTRIBUTE_MAP:
                self.types.append(self.ATTRIBUTE_MAP[value])
            elif value:
                logger.info(F"Unmapped {attribute} value within {person_id}: {value}")

        if name_tag.get("WROTEORPUBLISHEDAS") == "WROTEPUBLISHEDASYES":
            self.types.append("AuthorialName")

        if name_tag.name == "MARRIED" and is_married_surname(name_tag):
            self.types.append("Surname")

        self.index_sources = []
        if name_tag.name == "STANDARD":
            self.index_sources.append("Orlando")
        elif name_tag.get("INDEXSOURCE"):
            self.index_sources.append(name_tag.get("INDEXSOURCE"))

        self.name_parts = []
        for part_tag in name_tag.find_all("GIVEN") + name_tag.find_all("SURNAME"):
            if part_tag.find_parent(NOTE_TAGS):
                continue
            part_label = get_name_text(part_tag, use_reg=True)
            if part_label:
                self.name_parts.append((self.NAME_PART_MAP[part_tag.name], part_label))
            else:
                logger.info(F"Empty {part_tag.name} tag within {person_id}: {self.label}")

    def merge(self, other):
        """Combines the properties of another Name with the same label, ex. from nested tags"""
        self.types += [x for x in other.types if x not in self.types]
        self.index_sources += [x for x in other.index_sources if x not in self.index_sources]
        if not self.name_parts:
            self.name_parts = other.name_parts

    def to_triple(self, context):
        g = utilities.create_graph()
        g.add((context.uri, utilities.create_uri("cwrc", "name"), self.uri))
        g.add((self.uri, utilities.create_uri("rdfs", "label"), Literal(self.label)))
        for x in self.types:
            g.add((self.uri, utilities.create_uri("rdf", "type"), utilities.create_uri("cwrc", x)))

        for x in self.index_sources:
            g.add((self.uri, utilities.create_uri("cwrc", "indexedBy"), Literal(x)))

        for order, (part_type, part_label) in enumerate(self.name_parts, start=1):
            part_uri = utilities.make_standard_uri(F"{self.person_id} NameEnt {self.label} NamePart {order}")
            g.add((self.uri, utilities.create_uri("cwrc", "hasNamePart"), part_uri))
            g.add((part_uri, utilities.create_uri("rdf", "type"), utilities.create_uri("cwrc", part_type)))
            g.add((part_uri, utilities.create_uri("rdfs", "label"), Literal(part_label)))
            g.add((part_uri, utilities.create_uri("cwrc", "hasSortOrder"), Literal(order)))

        return g

    def __str__(self):
        string = f"\tURI: {self.uri}\n"
        string += f"\tlabel: {self.label}\n"
        string += f"\ttypes: {self.types}\n"
        string += f"\tindex sources: {self.index_sources}\n"
        string += f"\tname parts: {self.name_parts}\n"
        return string


def get_name_text(tag, use_reg=False):
    """Returns the whitespace normalized text of a name tag, ignoring any notes or citations within it"""
    if use_reg and tag.get("REG"):
        return " ".join(tag.get("REG").split())
    tag = utilities.remove_tags(NOTE_TAGS, tag)
    return " ".join(tag.get_text().split())


def is_married_surname(tag):
    """Married names are surnames unless titled (ex. Countess of Blessington),
        which are only surnames if explicitly tagged as such
    """
    if not tag.find("TITLED"):
        return True
    return tag.find_parent("SURNAME") is not None or tag.find("SURNAME") is not None


def get_entry_name_tags(doc, person):
    """Returns the STANDARD and DOCTITLE tags of the entry, which are found outside of PERSONNAME"""
    tags = []
    for tagname in ENTRY_NAME_TAGS:
        tag = doc.find(tagname)
        if tag:
            tags.append(tag)
        else:
            logger.warning(F"{tagname} tag not found within {person.id}")
    return tags


def find_names(name_tags, person):
    """Returns the Names of the given tags, merging those with the same label, ex. nested tags"""
    names = {}
    for tag in name_tags:
        if tag.find_parent(NOTE_TAGS):
            continue

        name = Name(tag, person.id)
        if not name.label:
            logger.warning(F"Empty {tag.name} tag within {person.id}: {tag}")
            continue

        if name.label in names:
            names[name.label].merge(name)
        else:
            names[name.label] = name

    return list(names.values())


def extract_person_name_data(doc, person):
    context_count = 1
    event_count = 1
    CONTEXT_TYPE = get_context_type("PERSONNAME")
    EVENT_TYPE = get_event_type("PERSONNAME")

    contexts = doc.find_all("PERSONNAME")
    if len(contexts) > 1:
        logger.info(F"Multiple PERSONNAME tags within: {person.id}")

    for context in contexts:
        name_tags = context.find_all(PERSONNAME_TAGS)
        if context_count == 1:
            name_tags = get_entry_name_tags(doc, person) + name_tags

        context_id = F"{person.id}_{CONTEXT_TYPE}_{context_count}"
        names = find_names(name_tags, person)
        if names:
            temp_context = Context(context_id, context, "PERSONNAME", person=person)
            temp_context.link_triples(names)
        else:
            temp_context = Context(context_id, context, "PERSONNAME", "identifying", person=person)

        person.add_context(temp_context)
        context_count += 1

        for event in context.find_all("CHRONSTRUCT"):
            context_id = F"{person.id}_{CONTEXT_TYPE}_{context_count}"
            temp_context = Context(context_id, event, "PERSONNAME", "identifying", person=person)

            event_title = F"{person.name} - {utilities.split_by_casing(EVENT_TYPE)}"
            event_uri = F"{person.id}_{EVENT_TYPE}_{event_count}"
            temp_event = Event(event_title, event_uri, event, type=EVENT_TYPE)

            temp_context.link_event(temp_event)
            person.add_event(temp_event)
            person.add_context(temp_context)

            context_count += 1
            event_count += 1


def main():
    from bs4 import BeautifulSoup
    from entry.biography import Biography

    extraction_mode, file_dict = utilities.parse_args(__file__, "Personname", logger)

    uber_graph = utilities.create_graph()

    for filename in file_dict.keys():
        with open(filename) as f:
            soup = BeautifulSoup(f, 'lxml-xml')

        person_id = soup.find("ENTRY").get("ID")
        if extraction_mode.verbosity > 0:
            print(filename)
            print(file_dict[filename])
            print(person_id)
            print("*" * 55)

        person = Biography(person_id, soup)
        extract_person_name_data(soup, person)

        graph = person.to_graph()

        utilities.create_individual_triples(extraction_mode, person, "personname")
        utilities.manage_mode(extraction_mode, person, graph)

        uber_graph += graph

    logger.info(str(len(uber_graph)) + " triples created")
    if extraction_mode.verbosity > 0:
        print(str(len(uber_graph)) + " total triples created")

    utilities.create_uber_triples(extraction_mode, uber_graph, "personname")
    logger.info("Time completed: " + utilities.get_current_time())


if __name__ == "__main__":
    main()
