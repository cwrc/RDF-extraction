#!/usr/bin/python3

from difflib import get_close_matches
from rdflib import RDF, RDFS, Literal
import rdflib

from log import Log

from utilities import *
from organizations import get_org, get_org_uri

from biography import Biography
from context import Context
from event import Event
from place import Place


"""
Status: ~90%
Most of cultural forms have been mapped
    TODO: Review missing religions & PAs

Forebear still needs to be handled/attempted with a query
--> load up gurjap's produced graph and query it  for forebear info to test
temp solution until endpoint is active

"""

# temp log library for debugging
# to be eventually replaced with proper logging library
log = Log("log/cf/errors")
log.test_name("CF extraction Error Logging")
extract_log = Log("log/cf/extraction")
extract_log.test_name("CF extraction Test Logging")
turtle_log = Log("log/cf/triples")
turtle_log.test_name("CF extracted Triples")

uber_graph = rdflib.Graph()
namespace_manager = rdflib.namespace.NamespaceManager(uber_graph)
bind_ns(namespace_manager, NS_DICT)


class CulturalForm(object):
    """docstring for CulturalForm
        NOTE: mapping is done prior to creation of cf,
        no need to include class type then
        using other_attributes to handle extra predicates
        that may come up for cfs
        Ex. Organizations
        other_attributes=NS_DICT["org"].memberOf
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
            self.uri = create_uri("cwrc", self.predicate + self.reported)
        else:
            self.uri = create_uri("cwrc", self.predicate)

        self.uri = rdflib.term.URIRef(self.uri)

    def to_tuple(self, person_uri):
        """TODO
            figure out if i can just return tuple or triple
            without creating a whole graph
            Evaluate efficency of creating this graph or
            just returning a tuple and have the biography deal with it
        """
        return ((person_uri, self.uri, self.value))

    def to_triple(self, person):
        g = rdflib.Graph()
        namespace_manager = rdflib.namespace.NamespaceManager(g)
        bind_ns(namespace_manager, NS_DICT)
        g.add((person.uri, self.uri, self.value))
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
            log.msg("self-defined attribute RETURNED UNEXPECTED RESULTS:" + str(tag) + "?????")
    return None


def find_cultural_forms(cf, person):
    cf_list = []

    def get_class():
        classes = cf.find_all("CLASS")
        for x in classes:
            value = x.get("SOCIALRANK")

            if not value or value == "OTHER":
                value = get_value(x)

            cf_list.append(CulturalForm("hasSocialClass", get_reported(x), get_mapped_term("SocialClass", value)))

    def get_language():
        langs = cf.find_all("LANGUAGE")
        for x in langs:
            value = get_value(x)

            # What if nested ethnicity tag?
            competence = x.get("COMPETENCE")
            predicate = ""
            if competence == "MOTHER":
                predicate = "hasNativeLinguisticAbility"
            elif competence == "OTHER":
                predicate = "hasLinguisticAbility"
            else:
                predicate = "hasLinguisticAbility"

            if value == "hindustani":
                cf_list.append(CulturalForm(predicate, None, get_mapped_term("Language", "hindi")))
            cf_list.append(CulturalForm(predicate, None, get_mapped_term("Language", value)))

    def get_other_cfs():
        tags = {"NATIONALITY": ["hasNationality", "NationalIdentity"],
                "SEXUALIDENTITY": ["hasSexuality", "Sexuality"]}
        for tag in tags.keys():
            instances = cf.find_all(tag)
            for x in instances:
                value = get_value(x)
                if tags[tag][1] == "NationalIdentity":
                    if value == "Indian/English":
                        cf_list.append(CulturalForm(tags[tag][0], get_reported(
                            x), get_mapped_term(tags[tag][1], value.split("/")[0])))
                        value = value.split("/")[1]
                    elif value == "Scots-American":
                        cf_list.append(CulturalForm(tags[tag][0], get_reported(
                            x), get_mapped_term(tags[tag][1], value.split("-")[0])))
                        value = value.split("-")[1]

                cf_list.append(CulturalForm(tags[tag][0], get_reported(x), get_mapped_term(tags[tag][1], value)))

    def get_geoheritage(tag):
        places = tag.find_all("PLACE")
        if places:
            place_values = []
            for x in places:
                temp_place = Place(x)
                if type(temp_place.uri) is Literal:
                    value = get_mapped_term("GeographicHeritage", temp_place.address)
                    place_values.append(value)
                else:
                    place_values.append(temp_place.uri)
            return place_values
        else:
            return get_mapped_term("GeographicHeritage", get_value(tag))

    def get_forebear_cfs():
        # NOTE: This will have to interact will sparql endpoint to check family related triples
        # sparql query to check if person hasMother/hasFather, and there is a valid uri
        # otherwise create the person and familial relation?
        def get_forebear(tag):
            return get_attribute(tag, "FOREBEAR")
        # This optional attribute attaches to the elements Ethnicity, Geographical Heritage, National Heritage, or Race, Colour,
        # has ten possible values: Father, Mother, Parents, Grandfather, Grandmother, Grandparents, Aunt, Uncle, Other, and Family.

        # We can only make assumptions about the father, mother, parents, will have to create random relative's otherwise
        def existing_forebear(relation):
            # TODO: sparql query to check if relation exists will also need person's uri
            # also check current uber graph?
            return None

        def add_forebear(relation, culturalform):
            family = {
                "FATHER": "hasFather",
                "MOTHER": "hasMother",
                "GRANDFATHER": "hasGrandFather",
                "GRANDMOTHER": "hasGrandMother",
                "AUNT": "hasAunt",
                "UNCLE": "hasUncle"
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
                            culturalforms.append(CulturalForm("has" + tags[tag], get_reported(x), place))
                    else:
                        culturalforms.append(CulturalForm("has" + tags[tag], get_reported(x), value))

                else:
                    value = get_value(x)
                    if tag == "NATIONALHERITAGE" and value in ["American-Austrian", "Anglo-Scottish", "Scottish-Irish"]:
                        culturalforms.append(CulturalForm(
                            "has" + tags[tag], get_reported(x), get_mapped_term(tags[tag], value.split("-")[0])))
                        culturalforms.append(CulturalForm(
                            "has" + tags[tag], get_reported(x), get_mapped_term(tags[tag], value.split("-")[1])))
                    else:
                        culturalforms.append(CulturalForm(
                            "has" + tags[tag], get_reported(x), get_mapped_term(tags[tag], value)))

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
            value = get_reg(x)
            orgName = get_org(x)

            if not value and orgName:
                for org in orgName:
                    cf_list.append(CulturalForm(None, None, get_org_uri(org),
                                                other_attributes=NS_DICT["org"].memberOf))
            elif orgName:
                for org in orgName:
                    cf_list.append(CulturalForm(None, None, get_org_uri(org),
                                                other_attributes=NS_DICT["org"].memberOf))

            value = get_mapped_term("Religion", get_value(x), True)

            # Checking if religion occurs as a PA if no result as a religion
            if type(value) is Literal:
                value = get_mapped_term("PoliticalAffiliation", get_value(x), True)
                log.msg((value))
            if type(value) is Literal:
                value = get_mapped_term("Religion", get_value(x))

            religion = CulturalForm("hasReligion", get_reported(x), value)

            cf_list.append(religion)

    def get_PA():
        pas = cf.find_all("POLITICALAFFILIATION")
        for x in pas:
            value = get_reg(x)
            orgName = get_org(x)
            if not value and orgName:
                for org in orgName:
                    cf_list.append(CulturalForm(None, None, get_org_uri(org),
                                                other_attributes=NS_DICT["org"].memberOf))
                value = get_org_uri(org)
            elif orgName:
                for org in orgName:
                    cf_list.append(CulturalForm(None, None, get_org_uri(org),
                                                other_attributes=NS_DICT["org"].memberOf))
                value = get_mapped_term("PoliticalAffiliation", get_value(x))
            else:
                value = get_mapped_term("PoliticalAffiliation", get_value(x))

            gender_issue = False
            if x.get("WOMAN-GENDERISSUE") == "GENDERYES":
                cf_list.append(CulturalForm("hasGenderedPoliticalActivity", get_reported(x), value))
                gender_issue = True

            if x.get("ACTIVISM") == "ACTIVISTYES":
                cf_list.append(CulturalForm("hasActivistInvolvementIn", None, value))
            elif x.get("MEMBERSHIP") == "MEMBERSHIPYES":
                cf_list.append(CulturalForm("hasPoliticalMembershipIn", None, value))
            elif x.get("INVOLVEMENT") == "INVOLVEMENTYES":
                cf_list.append(CulturalForm("hasPoliticalInvolvementIn", None, value))
            else:
                if not gender_issue:
                    cf_list.append(CulturalForm("hasPoliticalAffiliation", get_reported(x), value))

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

    forms_found = 0
    event_count = event_count
    for tag in tag_list:
        temp_context = None
        cf_list = None
        cf_subelements_count[context_type] += 1
        context_id = person.id + "_" + \
            Context.context_map[context_type] + str(cf_subelements_count[context_type])

        cf_list = find_cultural_forms(tag, person)
        if cf_list:
            temp_context = Context(context_id, tag, context_type)
            temp_context.link_triples(cf_list)
            person.add_cultural_form(cf_list)
        else:
            temp_context = Context(context_id, tag, context_type, "identifying")

        forms_found += 1

        if list_type == "events":
            event_title = person.name + " - " + Context.context_map[context_type].split("Context")[0] + " Event"
            event_uri = person.id + "_" + \
                Context.context_map[context_type].split("Context")[0] + "_Event" + str(event_count)
            temp_event = Event(event_title, event_uri, tag)

            temp_context.link_event(temp_event)
            person.add_event(temp_event)
            event_count += 1

        person.add_context(temp_context)
    return forms_found


cf_subelements_count = {"CLASSISSUE": 0, "RACEANDETHNICITY": 0, "CULTURALFORMATION": 0,
                        "POLITICS": 0, "NATIONALITYISSUE": 0, "SEXUALITY": 0, "RELIGION": 0}


def extract_cf_data(bio, person):
    global cf_subelements_count
    cf_subelements_count = {"CLASSISSUE": 0, "RACEANDETHNICITY": 0, "POLITICS": 0,
                            "NATIONALITYISSUE": 0, "SEXUALITY": 0, "RELIGION": 0, "CULTURALFORMATION": 0}
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

    elements = bio.find_all("POLITICS")
    forms_found = 1
    for element in elements:
        paragraphs = element.find_all("P")
        events = element.find_all("CHRONSTRUCT")
        extract_culturalforms(paragraphs, "POLITICS", person)
        forms_found += extract_culturalforms(events, "POLITICS", person, "events", forms_found)


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
    import csv
    global CF_MAP
    with open('cf_mapping.csv', newline='') as csvfile:
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


def get_mapped_term(rdf_type, value, retry=False):
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
        term = Literal(term, datatype=rdflib.namespace.XSD.string)
    else:
        term = Literal("_" + value.lower() + "_", datatype=rdflib.namespace.XSD.string)
        if retry:
            map_attempt -= 1
        else:
            map_fail += 1
            possibilites = []
            for x in CF_MAP[rdf_type]:
                if get_close_matches(value.lower(), x):
                    possibilites.append(x[0])
            if type(term) is Literal:
                update_fails(rdf_type, value)
            else:
                update_fails(rdf_type, value + "->" + str(possibilites) + "?")
    return term


def log_mapping_fails(main_log, error_log, detail=True):
    main_log.subtitle("Attempts: #" + str(map_attempt))
    main_log.subtitle("Fails: #" + str(map_fail))
    main_log.subtitle("Success: #" + str(map_success))
    main_log.separ()
    print()
    main_log.subtitle("Failure Details:")
    total_unmapped = 0
    for x in fail_dict.keys():
        num = len(fail_dict[x].keys())
        total_unmapped += num
        error_log.subtitle(x.split("#")[1] + ":" + str(num))
    main_log.subtitle("Failed to find " + str(total_unmapped) + " unique terms")

    print()
    error_log.separ("#")
    if not detail:
        log_mapping_fails(extract_log, log)
        return

    from collections import OrderedDict
    for x in fail_dict.keys():
        error_log.msg(x.split("#")[1] + "(" + str(len(fail_dict[x].keys())) + " unique)" + ":")

        new_dict = OrderedDict(sorted(fail_dict[x].items(), key=lambda t: t[1], reverse=True))
        count = 0
        for y in new_dict.keys():
            error_log.msg("\t" + str(new_dict[y]) + ": " + y)
            count += new_dict[y]
        error_log.msg("Total missed " + x.split("#")[1] + ": " + str(count))
        error_log.separ()
        print()


def main():
    import os
    from bs4 import BeautifulSoup
    create_cf_map()

    filelist = [filename for filename in sorted(os.listdir("bio_data")) if filename.endswith(".xml")]
    entry_num = 1

    # for filename in filelist[:200]:
    # for filename in filelist[-5:]:
    global uber_graph
    test_cases = ["shakwi-b.xml", "woolvi-b.xml", "seacma-b.xml", "atwoma-b.xml",
                  "alcolo-b.xml", "bronem-b.xml", "bronch-b.xml", "levyam-b.xml"]
    # for filename in filelist:
    for filename in test_cases:
        with open("bio_data/" + filename) as f:
            soup = BeautifulSoup(f, 'lxml-xml')

        print(filename)
        person = Biography(filename[:-6], get_name(soup), get_mapped_term("Gender", get_sex(soup)))

        extract_cf_data(soup, person)

        graph = person.to_graph()

        extract_log.subtitle("Entry #" + str(entry_num))
        extract_log.msg(str(person))
        extract_log.subtitle(str(len(graph)) + " triples created")
        extract_log.msg(person.to_file(graph))
        extract_log.subtitle("Entry #" + str(entry_num))
        extract_log.msg("\n\n")

        temp_path = "extracted_triples/cf_turtle/" + filename[:-6] + "_cf.ttl"
        create_extracted_file(temp_path, person)
        temp_path = "extracted_triples/cf_rdf/" + filename[:-6] + "_cf.rdf"
        create_extracted_file(temp_path, person, "pretty-xml")

        uber_graph += graph
        entry_num += 1

    turtle_log.subtitle(str(len(uber_graph)) + " triples created")
    turtle_log.msg(uber_graph.serialize(format="ttl").decode(), stdout=False)
    turtle_log.msg("")

    temp_path = "extracted_triples/culturalForms.ttl"
    create_extracted_uberfile(temp_path, uber_graph)

    temp_path = "extracted_triples/culturalForms.rdf"
    create_extracted_uberfile(temp_path, uber_graph, "pretty-xml")

    log_mapping_fails(extract_log, log)


if __name__ == "__main__":
    main()
