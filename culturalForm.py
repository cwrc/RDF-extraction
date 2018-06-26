#!/usr/bin/python3
from bs4 import BeautifulSoup
import rdflib
import re
from rdflib import RDF, RDFS, Literal
from Env import env
import islandora_auth as login
from difflib import get_close_matches
# temp log library for debugging --> to be eventually replaced with proper logging library
from log import *
log = Log("log/cf/errors")
log.test_name("CF extraction Error Logging")
extract_log = Log("log/cf/extraction")
extract_log.test_name("CF extraction Test Logging")
turtle_log = Log("log/cf/triples")
turtle_log.test_name("CF extracted Triples")


CWRC = rdflib.Namespace("http://sparql.cwrc.ca/ontologies/cwrc#")
FOAF = rdflib.Namespace('http://xmlns.com/foaf/0.1/')
DATA = rdflib.Namespace("http://cwrc.ca/cwrcdata/")

uber_graph = rdflib.Graph()
namespace_manager = rdflib.namespace.NamespaceManager(uber_graph)
namespace_manager.bind('cwrc', CWRC, override=False)
namespace_manager.bind('foaf', FOAF, override=False)
namespace_manager.bind('cwrcdata', DATA, override=False)


def strip_all_whitespace(string):
# temp function for condensing the context strings in visibility
    return re.sub('[\s+]', '', str(string))


class Biography(object):
    """docstring for Biography"""

    def __init__(self, id, name, gender):
        super(Biography, self).__init__()
        self.id = id
        self.uri = rdflib.term.URIRef(str(DATA) + id)
        self.name = name
        self.gender = gender
        self.context_list = []
        self.cf_list = []
        # Hold off on events for now
        self.event_list = []

    def add_context(self, context):
        if context is list:
            self.context_list += context
        else:
            self.context_list.append(context)

    def create_context(self, id, text, type="culturalformation"):
        self.context_list.append(Context(id, text, type))

    def add_cultural_form(self, culturalform):
        self.cf_list += culturalform
        # if culturalform is list:
            # self.cf_list += culturalform
            # self.cf_list.extend(culturalform)
        #     pass
        # else:
        #     self.cf_list.append(culturalform)

    def create_cultural_form(self, predicate, reported, value, other_attributes=None):
        self.cf_list.append(CulturalForm(predicate, reported, value, other_attributes))

    def add_event(self, title, event_type, date, other_attributes=None):
        self.event_list.append(Event(title, event_type, date, other_attributes))

    def create_triples(self, e_list):
        g = rdflib.Graph()
        for x in e_list:
            g += x.to_triple(self.uri)
        return g

    def to_graph(self):
        g = rdflib.Graph()
        namespace_manager = rdflib.namespace.NamespaceManager(g)
        namespace_manager.bind('cwrc', CWRC, override=False)
        namespace_manager.bind('foaf', FOAF, override=False)
        namespace_manager.bind('cwrcdata', DATA, override=False)
        g.add((self.uri, RDF.type, CWRC.NaturalPerson))
        g.add((self.uri, FOAF.name, rdflib.Literal(self.name)))
        g.add((self.uri, CWRC.hasGender, self.gender))
        g += self.create_triples(self.cf_list)
        # g += self.create_triples(self.context_list)
        # g += self.create_triples(self.event_list)
        global uber_graph
        uber_graph += g
        return g

    def to_file(self, graph, serialization="ttl"):
        return graph.serialize(format=serialization).decode()

    def __str__(self):
        string = "id: " + str(self.id) + "\n"
        string += "name: " + self.name + "\n"
        string += "gender: " + str(self.gender) + "\n"
        if self.context_list:
            string += "Contexts: \n"
            for x in self.context_list:
                string += str(x) + "\n"
        if self.cf_list:
            string += "CulturalForms: \n"
            for x in self.cf_list:
                string += str(x) + "\n"
        if self.event_list:
            string += "Events: \n"
            for x in self.event_list:
                string += str(x) + "\n"

        return string


class Context(object):
    """docstring for Context"""
    context_types = ["GenderContext", "PoliticalContext", "SocialClassContext",
                     "SexualityContext", "RaceEthnicityContext", "ReligionContext", "NationalityContext"]
    context_map = {"classissue": "SocialClassContext", "raceandethnicity": "RaceEthnicityContext",
                   "nationalityissue": "NationalityContext", "sexuality": "SexualityContext",
                   "religion": "ReligionContext", "culturalformation": "CulturalFormContext"}

    def __init__(self, id, text, type="culturalformation", motivation="describing"):
        super(Context, self).__init__()
        self.id = id

        self.tag = text
        # Will possibly have to clean up citations sans ()
        self.text = ' '.join(str(text.get_text()).split())

        # holding off till we know how src should work may have to how we're grabbing entries from islandora api
        # self.src = src
        self.type = self.context_map[type]
        self.motivation = motivation
        self.subjects = []

    def to_triple(self, person_uri):
        # Pending OA stuff
        # type context as type
        # loop through subjects for dc subject
        # create hasbody
        # create dctypes:text
        # hasbody's object a oa:choice will have items identical to subjects plus
        pass

    def __str__(self):
        string = "\tid: " + str(self.id) + "\n"
        # text = strip_all_whitespace(str(self.text))
        string += "\ttype: " + self.type + "\n"
        string += "\tmotivation: " + self.motivation + "\n"
        string += "\ttag: \n\t\t{" + str(self.tag) + "}\n"
        string += "\ttext: \n\t\t{" + self.text + "}\n"
        if self.subjects:
            string += "\tsubjects:\n"
            for x in self.subjects:
                string += "\t\t" + str(x) + "\n"
        return string + "\n"

    # def context_count(self,type):
    #     pass


class CulturalForm(object):
    """docstring for CulturalForm
        Notes: mapping is done prior to creation of cf, no need to include class type then
    """

    def __init__(self, predicate, reported, value, other_attributes=None):
        super(CulturalForm, self).__init__()
        # self.context_id = context_id
        self.predicate = predicate
        self.reported = reported
        self.value = value

    # figure out if i can just return tuple or triple without creating a whole graph
    # Evaluate efficency of creating this graph or just returning a tuple and have the biography deal with it
    def to_tuple(self, person_uri):
        # For future testing
        p = str(CWRC) + self.predicate + self.reported
        o = self.value
        return ((person_uri, rdflib.term.URIRef(p), o))

    def to_triple(self, person_uri):
        if self.reported:
            p = str(CWRC) + self.predicate + self.reported
        else:
            p = str(CWRC) + self.predicate

        # o = str(CWRC) + self.value
        o = self.value
        g = rdflib.Graph()
        g.add((person_uri, rdflib.term.URIRef(p), o))
        return g

    def __str__(self):
        string = "\tpredicate: " + self.predicate + "\n"
        string += "\treported: " + str(self.reported) + "\n"
        string += "\tvalue: " + str(self.value) + "\n"
        return string


class Event(object):
    """docstring for CulturalForm"""

    def __init__(self, title, event_type, date, other_attributes=None):
        super(Event, self).__init__()
        self.title = title
        self.event_type = event_type
        self.date = date

    def to_triple(self, person_uri):
        # p = self.predicate + self.reported
        # o = self.value
        # figure out if i can just return tuple or triple without creating a whole graph
        pass

    def __str__(self):
        string = "\tevent_type: " + str(self.event_type) + "\n"
        text = strip_all_whitespace(str(self.title))
        string += "\tcontent: " + text + "\n"
        string += "\tdate: " + str(self.date) + "\n"
        return string

# 3


def get_name(bio):
    return (bio.biography.div0.standard.text)


def get_sex(bio):
    return (bio.biography.get("sex"))


def extract_contexts(bio):
    pass


def get_uri(value):
    pass


def find_cultural_forms(cf, person_uri):
    cf_list = []

    def get_reported(tag):
        reported = tag.get("self-defined")
        if reported:
            if reported == "SELFYES":
                return "SelfReported"
            elif reported == "SELFNO":
                return "Reported"
            elif reported == "SELFUNKNOWN":
                return "Reported"
                log.title(str(tag))
            else:
                return "?????"
        return None

    def get_reg(tag):
        return get_attribute(tag, "reg")

    def get_attribute(tag, attribute):
        value = tag.get(attribute)
        if value:
            return value
        return None

    def get_value(tag):
        value = get_reg(tag)
        if not value:
            value = get_attribute(tag, "CURRENTALTERNATIVETERM")
        if not value:
            value = str(tag.text)
            value = ' '.join(value.split())
        return value

    def get_class():
        classes = cf.find_all("class")
        for x in classes:
            value = x.get("socialrank")

            if not value or value == "OTHER":
                value = get_value(x)

            cf_list.append(CulturalForm("hasSocialClass", get_reported(x), get_mapped_term("SocialClass", value)))

    def get_language():
        langs = cf.find_all("language")
        for x in langs:
            value = get_value(x)

            # What if nested ethnicity tag?
            competence = x.get("competence")
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
        tags = {"nationality": ["hasNationality", "NationalIdentity"],
                "sexualidentity": ["hasSexuality", "Sexuality"]}
        for tag in tags.keys():
            instances = cf.find_all(tag)
            for x in instances:
                value = get_value(x)
                if tags[tag][1] == "NationalIdentity" and value in ["Indian/English", "scots american"]:
                    cf_list.append(CulturalForm(tags[tag][0], get_reported(
                        x), get_mapped_term(tags[tag][1], value.split("/")[0])))
                    value = value.split("/")[1]

                cf_list.append(CulturalForm(tags[tag][0], get_reported(x), get_mapped_term(tags[tag][1], value)))

    def get_geoheritage(tag):
        # will require more detailed scrape and parsing of place info + mapping to geonames, may need to split into a separate script pending
        log.separ()
        log.msg(strip_all_whitespace(str(tag)))
        value = get_value(tag)
        if value and len(value) < 50:
            log.msg("\t" + value)
        settlement = tag.find_all("settlement")
        region = tag.find_all("region")
        geog = tag.find_all("geog")
        log.msg("\t\tsettlement: " + str([get_value(x) for x in settlement]))
        log.msg("\t\tregion: " + str([get_value(x) for x in region]))
        log.msg("\t\tgeog: " + str([get_value(x) for x in geog]))

        return "None"

    def get_forebear_cfs():
        # This will have to interact will sparql endpoint to check family related triples
        # sparql query to check if person hasMother/hasFather, and there is a valid uri
        # otherwise create the person and familial relation?
        def get_forebear(tag):
            return get_attribute(tag, "FOREBEAR")
        # This optional attribute attaches to the elements Ethnicity, Geographical Heritage, National Heritage, or Race, Colour,
        # has ten possible values: Father, Mother, Parents, Grandfather, Grandmother, Grandparents, Aunt, Uncle, Other, and Family.

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

        tags = {"racecolour": "RaceColour",
                "nationalheritage": "NationalHeritage",
                "geogheritage": "GeographicHeritage",
                "ethnicity": "Ethnicity"}

        for tag in tags.keys():
            instances = cf.find_all(tag)
            for x in instances:
                forebear = get_forebear(x)

                if tag == "geogheritage":
                    value = get_geoheritage(x)
                else:
                    value = get_value(x)

                culturalforms = []
                if tag == "nationalheritage" and value in ["American-Austrian", "Anglo-Scottish", "Scottish-Irish"]:
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

                    elif forebear == "GRANDPARENTS":
                        add_forebear("GRANDMOTHER", culturalform)
                        add_forebear("GRANDFATHER", culturalform)
                    else:
                        add_forebear(forebear, culturalform)

        pass

    def get_denomination():
        religions = cf.find_all("denomination")
        for x in religions:
            value = get_mapped_term("Religion", get_value(x))
            cf_list.append(CulturalForm("hasReligion", get_reported(x), value))

    def get_PA():
        # Create theoretical extra triples for now
        # possible predicates:
        # These will also need inverse if we were to maintain consistency?
        # MEMBERSHIP --> INVOLVEMENT --> ACTIVISM
        # low --> med --> high
        # possible that we can change these predicates to some of leveling term
        # INVOLVEMENTYES --> hasPoliticalInvolvement
        # ACTIVISMYES --> hasActivistRole
        # MEMBERSHIPYES --> hasMembership
        # Membership can be broader to work for general organizations perhaps? ex. religious organizations
        pas = cf.find_all("politicalaffiliation")
        for x in pas:
            value = get_mapped_term("PoliticalAffiliation", get_value(x))

            cf_list.append(CulturalForm("hasPoliticalAffiliation", get_reported(x), value))
            # Since according to orlando it is a scale and they overlap
            if x.get("activism") == "ACTIVISTYES":
                cf_list.append(CulturalForm("hasActivistRole", None, value))
            elif x.get("involvement") == "INVOLVEMENTYES":
                cf_list.append(CulturalForm("hasPoliticalInvolvement", None, value))
            elif x.get("membership") == "MEMBERSHIPYES":
                cf_list.append(CulturalForm("hasMembership", None, value))

    get_class()
    get_language()
    get_other_cfs()
    get_PA()
    get_denomination()
    get_forebear_cfs()
    return cf_list


# bare min event scrape
def find_event(type, tag, person):
    event_tag = tag.find_all("chronstruct")
    for x in event_tag:
        # print(type)
        # print(event_tag)
        event_body = ""

        for y in x.find_all("chronprose"):
            event_body += str(y)

        date = None
        for y in x.find_all("date"):
            date = y.text
        person.add_event(event_body, type, date)

    pass


def get_subjects(cf_list):
    subjects = []
    for x in cf_list:
        subjects.append(x.value)
    return list(set(subjects))


def create_cf_data(bio, person):
    cfs = bio.find_all("culturalformation")
    cf_subelements = ["classissue", "raceandethnicity", "nationalityissue", "sexuality", "religion"]
    cf_subelements_count = {"classissue": 1, "raceandethnicity": 1,
                            "nationalityissue": 1, "sexuality": 1, "religion": 1}

    id = 1
# TODO clean up naming in this function
    for cf in cfs:
        forms_found = 0
        for x in cf_subelements:
            # find_event(x, cf, person)

            temp = cf.find_all(x)
            for y in temp:
                temp_context = None
                cf_list = None
                temp_context = Context(x + "_context" + str(cf_subelements_count[x]), y, x)
                cf_subelements_count[x] += 1
                forms_found += 1

                cf_list = find_cultural_forms(y, person.uri)
                if cf_list:
                    temp_context.subjects = get_subjects(cf_list)
                    person.add_cultural_form(cf_list)
                person.add_context(temp_context)

        if forms_found == 0:
            temp_context = None
            cf_list = None
            temp_context = Context(x + "_context" + str(id), cf)

            cf_list = find_cultural_forms(cf, person.uri)
            temp_context.subjects = get_subjects(cf_list)

            person.add_context(temp_context)
            person.add_cultural_form(cf_list)
            id += 1


cf_map = {}


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
    global cf_map
    with open('cf_mapping.csv', newline='') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        for row in reader:
            if row[0] not in cf_map:
                cf_map[row[0]] = []
            temp_row = [clean_term(x) for x in row[2:]]
            cf_map[row[0]].append(list(filter(None, [row[1], *temp_row])))


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


# Currently getting exact match ignoring case and "-"
# TODO:
# Will need add some sort of percentage match for failures
# log unmatched term,
# return literal or uri
# Make csv of unmapped
# Make stats report of sucessfulness/failure of mappings
def get_mapped_term(rdf_type, value):
    global map_attempt
    global map_success
    global map_fail
    if "http://sparql.cwrc.ca/ontologies/cwrc#" not in rdf_type:
        rdf_type = "http://sparql.cwrc.ca/ontologies/cwrc#" + rdf_type
    map_attempt += 1
    term = None
    for x in cf_map[rdf_type]:
        # if get_close_matches(value.lower(), x):
        #     term = x[0]
        #     map_success += 1
        #     break
        if clean_term(value) in x:
            term = x[0]
            map_success += 1
            break

    if "http" in str(term):
        term = rdflib.term.URIRef(term)
    elif term:
        term = rdflib.term.Literal(term, datatype=rdflib.namespace.XSD.string)
    else:
        term = rdflib.term.Literal("_" + value.lower() + "_", datatype=rdflib.namespace.XSD.string)
        map_fail += 1
        possibilites = []
        for x in cf_map[rdf_type]:
            if get_close_matches(value.lower(), x):
                possibilites.append(x[0])
        if type(term) is rdflib.term.Literal:
            update_fails(rdf_type, value)
        else:
            update_fails(rdf_type, value + "->" + str(possibilites) + "?")
    return term


def main():
    import os
    create_cf_map()

    filelist = [filename for filename in sorted(os.listdir("bio_data")) if filename.endswith(".xml")]
    entry_num = 1

    # for filename in filelist[:200]:
    # for filename in filelist[-5:]:
    for filename in filelist:
        with open("bio_data/" + filename) as f:
            soup = BeautifulSoup(f, 'lxml')

        # print(filename)
        test_person = Biography(filename[:-4], get_name(soup), get_mapped_term("Gender", get_sex(soup)))

        create_cf_data(soup, test_person)

        # print("=" * 50, "Entry #", entry_num, "=" * 50)
        # print(test_person)
        # print("=" * 50, "Entry #", entry_num, "=" * 50)
        # print("\n\n")

        extract_log.subtitle("Entry #" + str(entry_num))
        extract_log.msg(str(test_person))
        extract_log.subtitle("Entry #" + str(entry_num))
        extract_log.msg("\n\n")
        graph = test_person.to_graph()
        extract_log.subtitle(str(len(graph)) + " triples created")
        extract_log.msg(test_person.to_file(graph))

        entry_num += 1

    turtle_log.subtitle(str(len(uber_graph)) + " triples created")
    turtle_log.msg(uber_graph.serialize(format="ttl").decode(), stdout=False)
    turtle_log.msg("")

    extract_log.subtitle("Attempts: #" + str(map_attempt))
    extract_log.subtitle("Fails: #" + str(map_fail))
    extract_log.subtitle("Success: #" + str(map_success))
    extract_log.separ()
    print()
    extract_log.subtitle("Failure Details:")
    total_unmapped = 0
    for x in fail_dict.keys():
        num = len(fail_dict[x].keys())
        total_unmapped += num
        log.subtitle(x.split("#")[1] + ":" + str(num))
    extract_log.subtitle("Failed to find " + str(total_unmapped) + " unique terms")

    print()
    log.separ("#")
    from collections import OrderedDict
    for x in fail_dict.keys():
        log.msg(x.split("#")[1] + "(" + str(len(fail_dict[x].keys())) + ")" + ":")

        new_dict = OrderedDict(sorted(fail_dict[x].items(), key=lambda t: t[1], reverse=True))
        for y in new_dict.keys():
            log.msg("\t" + str(new_dict[y]) + ": " + y)
        log.separ()
        print()


def test():
    print(clean_term("Dissenter"))
    print()
    print(clean_term("Dissenting"))
    print()
    print(clean_term("Dissenters"))
    print()
    print(clean_term("DISSENTERS"))
    print()
    print(clean_term("dissent"))
    print()
    exit()

if __name__ == "__main__":
    # auth = [env.env("USER_NAME"), env.env("PASSWORD")]
    # login.main(auth)
    # test()
    main()
