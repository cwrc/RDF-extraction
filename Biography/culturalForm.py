#!/usr/bin/python3

from difflib import get_close_matches
from rdflib import RDF, RDFS, Literal
import rdflib

import logging
from Utils import utilities
from Utils.organizations import get_org, get_org_uri
from Utils.place import Place
from Utils.event import Event
from Utils.context import Context, get_event_type, get_context_type

"""
Status: ~90%
Most of cultural forms have been mapped
    TODO: Review missing religions & PAs

Forebear still needs to be handled/attempted with a query
--> load up gurjap's produced graph and query it  for forebear info to test
temp solution until endpoint is active

"""

logger = utilities.config_logger("culturalform")

uber_graph = utilities.create_graph()


class CulturalForm(object):
    """docstring for CulturalForm
        NOTE: mapping is done prior to creation of cf instance,
        no need to include class type then
        using other_attributes to handle extra predicates
        that may come up for cfs
        Ex. Organizations
        other_attributes=utilities.NS_DICT["org"].memberOf
        This being the uri rather the typical cf one
    """

    def __init__(self, predicate, reported, value, other_attributes=None):
        super(CulturalForm, self).__init__()
        self.predicate = predicate
        self.reported = reported
        self.value = value

        if other_attributes:
            self.uri = other_attributes
        elif self.reported:
            self.uri = utilities.create_uri("cwrc", self.predicate + self.reported)
        else:
            self.uri = utilities.create_uri("cwrc", self.predicate)

        self.uri = rdflib.term.URIRef(self.uri)

    def to_tuple(self, person_uri):
        """TODO
            figure out if i can just return tuple or triple
            without creating a whole graph
            Evaluate efficency of creating this graph or
            just returning a tuple and have the biography deal with it
        """
        return ((person_uri, self.uri, self.value))

    def to_triple(self, context):
        g = utilities.create_graph()
        g.add((context.uri, self.uri, self.value))
        return g

    def __str__(self):
        string = "\tURI: " + str(self.uri) + "\n"
        string += "\tpredicate: " + str(self.predicate) + "\n"
        string += "\treported: " + str(self.reported) + "\n"
        string += "\tvalue: " + str(self.value) + "\n"

        return string


def get_reported(tag):
    reported = tag.get("SELF-DEFINED")
    if reported:
        if reported == "SELFYES":
            return "SelfReported"
        elif reported == "SELFNO":
            return "Reported"
        elif reported == "SELFUNKNOWN":
            return None
        else:
            logger.error("self-defined attribute RETURNED UNEXPECTED RESULTS:" + str(tag) + "?????")
    return None


def find_cultural_forms(cf, person):
    cf_list = []

    def get_class():
        classes = cf.find_all("CLASS")
        for x in classes:
            value = x.get("SOCIALRANK")

            if not value or value == "OTHER":
                value = utilities.get_value(x)

            cf_list.append(CulturalForm("socialClass", get_reported(x), get_mapped_term("SocialClass", value)))

    def get_language():
        langs = cf.find_all("LANGUAGE")
        for x in langs:
            value = utilities.get_value(x)

            # What if nested ethnicity tag?
            competence = x.get("COMPETENCE")
            predicate = ""
            if competence == "MOTHER":
                predicate = "nativeLinguisticAbility"
            elif competence == "OTHER":
                predicate = "linguisticAbility"
            else:
                predicate = "linguisticAbility"

            if value == "hindustani":
                cf_list.append(CulturalForm(predicate, None, get_mapped_term("Language", "hindi")))
            cf_list.append(CulturalForm(predicate, None, get_mapped_term("Language", value)))

    def get_other_cfs():
        tags = {"NATIONALITY": ["nationality", "NationalIdentity"],
                "SEXUALIDENTITY": ["sexuality", "Sexuality"]}
        for tag in tags.keys():
            instances = cf.find_all(tag)
            for x in instances:
                value = utilities.get_value(x)
                if tags[tag][1] == "NationalIdentity":
                    if value == "Indian/English":
                        cf_list.append(CulturalForm(tags[tag][0], get_reported(
                            x), get_mapped_term(tags[tag][1], value.split("/")[0], id=person.id)))
                        value = value.split("/")[1]
                    elif value == "Scots-American":
                        cf_list.append(CulturalForm(tags[tag][0], get_reported(
                            x), get_mapped_term(tags[tag][1], value.split("-")[0], id=person.id)))
                        value = value.split("-")[1]

                value = get_mapped_term(tags[tag][1], value, id=person.id)
                cf_list.append(CulturalForm(tags[tag][0], get_reported(x), value))
                if tags[tag][1] == "NationalIdentity":
                    person.nationalities.append(str(value))

    def get_geoheritage(tag):
        places = tag.find_all("PLACE")
        if places:
            place_values = []
            for x in places:
                temp_place = Place(x)
                if type(temp_place.uri) is Literal:
                    value = get_mapped_term("GeographicHeritage", temp_place.address, id=person.id)
                    place_values.append(value)
                else:
                    place_values.append(temp_place.uri)
            return place_values
        else:
            return get_mapped_term("GeographicHeritage", utilities.get_value(tag), id=person.id)

    def get_forebear_cfs():
        # NOTE: This will have to interact will sparql endpoint to check family related triples
        # sparql query to check if person hasMother/hasFather, and there is a valid uri
        # otherwise create the person and familial relation?
        def get_forebear(tag):
            return utilities.get_attribute(tag, "FOREBEAR")
        # This optional attribute attaches to the elements Ethnicity, Geographical Heritage, National Heritage, or Race, Colour,
        # has ten possible values: Father, Mother, Parents, Grandfather, Grandmother, Grandparents, Aunt, Uncle, Other, and Family.

        # We can only make assumptions about the father, mother, parents, will have to create random relative's otherwise
        def existing_forebear(relation):
            # TODO: sparql query to check if relation exists will also need person's uri
            # also check current uber graph?
            return None

        def add_forebear(relation, culturalform):
            family = {
                "FATHER": "father",
                "MOTHER": "mother",
                "GRANDFATHER": "grandFather",
                "GRANDMOTHER": "grandMother",
                "AUNT": "aunt",
                "UNCLE": "uncle"
            }
            # check graph for existing forebear and get their uri
            forebear_uri = existing_forebear(family[relation])
            if not forebear_uri:
                pass
                # create forebear
                # check if uri available
                # foafname
                # type as real person
                # gender
                # person_uri cwrc.relation forebear_uri
                # uber_graph.add()

            # forebear_uri culturalform.predicate culturalform.value
            # Create
            pass

        tags = {"RACECOLOUR": "RaceColour",
                "NATIONALHERITAGE": "NationalHeritage",
                "GEOGHERITAGE": "GeographicHeritage",
                "ETHNICITY": "Ethnicity"}

        for tag in tags.keys():
            instances = cf.find_all(tag)
            for x in instances:
                culturalforms = []

                forebear = get_forebear(x)
                if tag == "GEOGHERITAGE":
                    value = get_geoheritage(x)
                    if type(value) is list:
                        for place in value:
                            culturalforms.append(CulturalForm("" + tags[tag], get_reported(x), place))
                    else:
                        culturalforms.append(CulturalForm("" + tags[tag], get_reported(x), value))

                else:
                    value = utilities.get_value(x)
                    if tag == "NATIONALHERITAGE" and value in ["American-Austrian", "Anglo-Scottish", "Scottish-Irish"]:
                        culturalforms.append(CulturalForm(
                            tags[tag][0].lower() + tags[tag][1:], get_reported(x), get_mapped_term(tags[tag], value.split("-")[0], id=person.id)))
                        culturalforms.append(CulturalForm(
                            tags[tag][0].lower() + tags[tag][1:], get_reported(x), get_mapped_term(tags[tag], value.split("-")[1], id=person.id)))
                    else:
                        culturalforms.append(CulturalForm(
                            tags[tag][0].lower() + tags[tag][1:], get_reported(x), get_mapped_term(tags[tag], value, id=person.id)))

                for culturalform in culturalforms:
                    cf_list.append(culturalform)

                    if not forebear or forebear in ["OTHER", "FAMILY"]:
                        continue

                    if forebear == "PARENTS":
                        add_forebear("MOTHER", culturalform)
                        add_forebear("FATHER", culturalform)

                    # elif forebear == "GRANDPARENTS":
                    #     add_forebear("GRANDMOTHER", culturalform)
                    #     add_forebear("GRANDFATHER", culturalform)
                    # else:
                    #     add_forebear(forebear, culturalform)

    def get_denomination():
        religions = cf.find_all("DENOMINATION")

        for x in religions:
            value = utilities.get_reg(x)
            orgName = get_org(x)

            if not value and orgName:
                for org in orgName:
                    cf_list.append(CulturalForm(None, None, get_org_uri(org),
                                                other_attributes=utilities.NS_DICT["org"].memberOf))
            elif orgName:
                for org in orgName:
                    cf_list.append(CulturalForm(None, None, get_org_uri(org),
                                                other_attributes=utilities.NS_DICT["org"].memberOf))

            value = get_mapped_term("Religion", utilities.get_value(x), True, id=person.id)

            # Checking if religion occurs as a PA if no result as a religion
            if type(value) is Literal:
                value = get_mapped_term("PoliticalAffiliation", utilities.get_value(x), True, id=person.id)
                # logger.warning("Mapping Religion to PA: " + value)
            if type(value) is Literal:
                value = get_mapped_term("Religion", utilities.get_value(x), id=person.id)

            religion = CulturalForm("religion", get_reported(x), value)

            cf_list.append(religion)

    def get_PA():
        pas = cf.find_all("POLITICALAFFILIATION")
        for x in pas:
            value = utilities.get_reg(x)
            orgName = get_org(x)
            if not value and orgName:
                for org in orgName:
                    cf_list.append(CulturalForm(None, None, get_org_uri(org),
                                                other_attributes=utilities.NS_DICT["org"].memberOf))
                value = get_org_uri(org)
            elif orgName:
                for org in orgName:
                    cf_list.append(CulturalForm(None, None, get_org_uri(org),
                                                other_attributes=utilities.NS_DICT["org"].memberOf))
                value = get_mapped_term("PoliticalAffiliation", utilities.get_value(x), id=person.id)
            else:
                value = get_mapped_term("PoliticalAffiliation", utilities.get_value(x), id=person.id)

            gender_issue = False
            if x.get("WOMAN-GENDERISSUE") == "GENDERYES":
                cf_list.append(CulturalForm("genderedPoliticalActivity", get_reported(x), value))
                gender_issue = True

            if x.get("ACTIVISM") == "ACTIVISTYES":
                cf_list.append(CulturalForm("activistInvolvementIn", None, value))
            elif x.get("MEMBERSHIP") == "MEMBERSHIPYES":
                cf_list.append(CulturalForm("politicalMembershipIn", None, value))
            elif x.get("INVOLVEMENT") == "INVOLVEMENTYES":
                cf_list.append(CulturalForm("politicalInvolvementIn", None, value))
            else:
                if not gender_issue:
                    cf_list.append(CulturalForm("politicalAffiliation", get_reported(x), value))

    if cf.name != "POLITICS":
        get_forebear_cfs()
        get_class()
        get_language()
        get_other_cfs()
        get_denomination()
    get_PA()
    return cf_list


def extract_culturalforms(tag_list, context_type, person, list_type="paragraphs", event_count=1):
    """ Creates the cultural forms ascribes them to the person along with the associated
        contexts and event
    """
    global cf_subelements_count
    CONTEXT_TYPE = get_context_type(context_type)
    forms_found = 0
    event_count = event_count
    for tag in tag_list:
        temp_context = None
        cf_list = None
        cf_subelements_count[context_type] += 1
        context_id = person.id + "_" + CONTEXT_TYPE + str(cf_subelements_count[context_type])

        cf_list = find_cultural_forms(tag, person)
        if cf_list:
            temp_context = Context(context_id, tag, context_type)
            temp_context.link_triples(cf_list)
        else:
            temp_context = Context(context_id, tag, context_type, "identifying")

        forms_found += 1

        if list_type == "events":
            event_title = person.name + " - " + CONTEXT_TYPE.split("Context")[0] + " Event"
            event_uri = person.id + "_" + \
                CONTEXT_TYPE.split("Context")[0] + "_Event" + str(event_count)
            temp_event = Event(event_title, event_uri, tag)

            temp_context.link_event(temp_event)
            person.add_event(temp_event)
            event_count += 1

        person.add_context(temp_context)
    return forms_found


cf_subelements_count = {"CLASSISSUE": 0, "RACEANDETHNICITY": 0, "CULTURALFORMATION": 0,
                        "POLITICS": 0, "NATIONALITYISSUE": 0, "SEXUALITY": 0, "RELIGION": 0}


def reset_count(dictionary):
    for x in dictionary.keys():
        dictionary[x] = 0
    return dictionary


def extract_cf_data(bio, person):
    global cf_subelements_count
    cf_subelements_count = reset_count(cf_subelements_count)
    # cf_subelements_count = {"CLASSISSUE": 0, "RACEANDETHNICITY": 0, "POLITICS": 0,
    #                         "NATIONALITYISSUE": 0, "SEXUALITY": 0, "RELIGION": 0, "CULTURALFORMATION": 0}
    cfs = bio.find_all("CULTURALFORMATION")
    cf_subelements = ["CLASSISSUE", "RACEANDETHNICITY", "NATIONALITYISSUE", "SEXUALITY", "RELIGION"]
    id = 1
    for cf in cfs:
        forms_found = 0
        for context_type in cf_subelements:
            contexts = cf.find_all(context_type)
            for context in contexts:
                # Find triples in paragraphs
                paragraphs = context.find_all("P")
                events = context.find_all("CHRONSTRUCT")
                forms_found += extract_culturalforms(paragraphs, context_type, person)
                forms_found += extract_culturalforms(events, context_type, person, "events")

        for x in cf.children:
            if x.name == "DIV2":
                paragraphs = x.find_all("P")
                events = x.find_all("CHRONSTRUCT")
                id += extract_culturalforms(paragraphs, "CULTURALFORMATION", person)
                id += extract_culturalforms(events, "CULTURALFORMATION", person, "events")

    # Going through political contexts
    elements = bio.find_all("POLITICS")
    forms_found = 1
    for element in elements:
        paragraphs = element.find_all("P")
        events = element.find_all("CHRONSTRUCT")
        extract_culturalforms(paragraphs, "POLITICS", person)
        forms_found += extract_culturalforms(events, "POLITICS", person, "events", forms_found)

    # Extracting additional information from writer
    persontype = utilities.get_persontype(bio)
    # TODO: figure out what context to attach this nationality + genre
    # if persontype in ["BRWWRITER", "IBRWRITER"]:
    #     if not any(x in ["GB", "GB-ENG", "GB-NIR", "GB-SCT", "GB-WLS", "IE"] for x in person.nationalities):
    #         person.add_cultural_form(CulturalForm("nationality", None,
    #                                               get_mapped_term("NationalIdentity", "British")))

    print("\n" * 5)


def clean_term(string):
    string = string.lower().replace("-", " ").strip().replace(" ", "")
    if string[-1:] == "s":
        string = string[:-1]
    if string[-3:] in ["ism", "ist", "ing"]:
        string = string[:-3]
    if string[-2:] == "er":
        string = string[:-2]
    return string


def create_cf_map():
    # TODO: Add exception handling for when file cannot be opened/parsed
    import csv
    global CF_MAP
    with open('../data/cf_mapping.csv', newline='') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        for row in reader:
            if row[0] not in CF_MAP:
                CF_MAP[row[0]] = []
            temp_row = [clean_term(x) for x in row[2:]]
            CF_MAP[row[0]].append(list(filter(None, [row[1], *temp_row])))


CF_MAP = {}
create_cf_map()
map_attempt = 0
map_success = 0
map_fail = 0
fail_dict = {}


def update_fails(rdf_type, value):
    global fail_dict
    if rdf_type in fail_dict:
        if value in fail_dict[rdf_type]:
            fail_dict[rdf_type][value] += 1
        else:
            fail_dict[rdf_type][value] = 1
    else:
        fail_dict[rdf_type] = {value: 1}


def get_mapped_term(rdf_type, value, retry=False, id=None):
    """
        Currently getting exact match ignoring case and "-"
        TODO:
        Make csv of unmapped
    """
    global map_attempt
    global map_success
    global map_fail
    if "http://sparql.cwrc.ca/ontologies/cwrc#" not in rdf_type:
        rdf_type = "http://sparql.cwrc.ca/ontologies/cwrc#" + rdf_type
    map_attempt += 1
    term = None
    temp_val = clean_term(value)
    for x in CF_MAP[rdf_type]:
        if temp_val in x:
            term = x[0]
            map_success += 1
            break

    if "http" in str(term):
        term = rdflib.term.URIRef(term)
    elif term:
        term = Literal("ISO-3166-3:" + term, datatype=rdflib.namespace.XSD.string)
    else:
        term = Literal(value, datatype=rdflib.namespace.XSD.string)
        if retry:
            map_attempt -= 1
        else:
            map_fail += 1
            possibilites = []
            for x in CF_MAP[rdf_type]:
                if get_close_matches(value.lower(), x):
                    possibilites.append(x[0])
            log_str = "Unable to find matching " + rdf_type.split("#")[1] + " instance for '" + value + "'"

            if type(term) is Literal:
                update_fails(rdf_type, value)
            else:
                update_fails(rdf_type, value + "->" + str(possibilites) + "?")
                log_str += "Possible matches: " + value + "->" + str(possibilites) + "?"

            if id:
                logger.warning("In entry: " + id + " " + log_str)
            else:
                logger.warning(log_str)
    return term


def log_mapping_fails(detail=True):
    log_str = "\n\n"
    log_str += "Attempts: " + str(map_attempt) + "\n"
    log_str += "Fails: " + str(map_fail) + "\n"
    log_str += "Success: " + str(map_success) + "\n"
    log_str += "\nFailure Details:" + "\n"
    total_unmapped = 0
    for x in fail_dict.keys():
        num = len(fail_dict[x].keys())
        total_unmapped += num
        log_str += "\t" + x.split("#")[1] + ":" + str(num) + "\n"
    log_str += "\nFailed to find " + str(total_unmapped) + " unique terms" + "\n"

    from collections import OrderedDict
    for x in fail_dict.keys():
        log_str += "\t" + x.split("#")[1] + "(" + str(len(fail_dict[x].keys())) + " unique)" + ":" + "\n"

        new_dict = OrderedDict(sorted(fail_dict[x].items(), key=lambda t: t[1], reverse=True))
        count = 0
        for y in new_dict.keys():
            log_str += "\t\t" + str(new_dict[y]) + ": " + y + "\n"
            count += new_dict[y]
        log_str += "\tTotal missed " + x.split("#")[1] + ": " + str(count) + "\n\n"

    logger.info(log_str)


def main():
    import os
    from biography import Biography
    from bs4 import BeautifulSoup

    file_dict = utilities.parse_args(__file__, "CulturalForm")
    entry_num = 1

    global uber_graph

    logger.info("Time started: " + utilities.get_current_time() + "\n")

    for filename in file_dict.keys():
        with open(filename) as f:
            soup = BeautifulSoup(f, 'lxml-xml')

        person_id = filename.split("/")[-1][:6]

        print("Running on:", filename)
        logger.info(file_dict[filename])
        print(file_dict[filename])
        print("*" * 55)

        person = Biography(person_id, soup, get_mapped_term("Gender", utilities.get_sex(soup)))
        extract_cf_data(soup, person)
        person.name = utilities.get_readable_name(soup)
        graph = person.to_graph()

        temp_path = "extracted_triples/cf_turtle/" + person_id + "_cf.ttl"
        utilities.create_extracted_file(temp_path, person)
        temp_path = "extracted_triples/cf_rdf/" + person_id + "_cf.rdf"
        utilities.create_extracted_file(temp_path, person, "pretty-xml")

        uber_graph += graph
        entry_num += 1
        print(person.to_file())

    logger.info(str(len(uber_graph)) + " triples created")

    temp_path = "extracted_triples/culturalForms.ttl"
    utilities.create_extracted_uberfile(temp_path, uber_graph)

    temp_path = "extracted_triples/culturalForms.rdf"
    utilities.create_extracted_uberfile(temp_path, uber_graph, "pretty-xml")

    log_mapping_fails()
    logger.info("Time completed: " + utilities.get_current_time())


if __name__ == "__main__":
    main()
