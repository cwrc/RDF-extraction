#!/usr/bin/python3
from bs4 import BeautifulSoup
import rdflib
import re
from rdflib import RDF, RDFS, Literal
from Env import env
import islandora_auth as login

# temp function for


def strip_all_whitespace(string):
    return re.sub('[\s+]', '', str(string))


class Biography(object):
    """docstring for Biography"""
    g = rdflib.Graph()

    def __init__(self, id, name, gender):
        super(Biography, self).__init__()
        self.id = id
        self.name = name
        # Check mapping for gender ? --> do it before creating bio obj
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

    def create_cultural_form(self, predicate, reported, value, other_attributes=None):
        self.cf_list.append(CulturalForm(predicate, reported, value, other_attributes))

    def add_event(self, title, event_type, date, other_attributes=None):
        self.event_list.append(Event(title, event_type, date, other_attributes))

    def create_context_triples(self):
        # create mini context graph
        # for x in self.context_list:
        #     x.to_triple(self.id)
        pass

    def create_cf_triples(self):
        # create mini cf graph
        pass

    def to_graph(self):
        # create graph
        # create bio triples
            # Foaf name?
            # hasGender?
        self.create_context_triples()
        self.create_cf_triples()
        # create context triples
        # create cf triples
        # create event triples
        pass

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
        self.text = text
        # holding off till we know how src should work
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
        text = ' '.join(str(self.text).split())
        # text = strip_all_whitespace(str(self.text))
        string += "\ttype: " + self.type + "\n"
        string += "\tmotivation: " + self.motivation + "\n"
        string += "\ttext: \n\t\t{" + text + "}\n"
        if self.subjects:
            string += "\tsubjects:"
            for x in self.subjects:
                string += str(x)
        return string + "\n"

    # def context_count(self,type):
    #     pass


class CulturalForm(object):
    """docstring for CulturalForm
        Notes: mapping is done prior to creation of cf, no need to include class type then
        if no term found then use value as string --> this needs to be logged eventually not just in final triples

    """

    def __init__(self, predicate, reported, value, other_attributes=None):
        super(CulturalForm, self).__init__()
        # self.context_id = context_id
        self.predicate = predicate
        self.reported = reported
        self.value = value

    def to_triple(self, person_uri):
        p = self.predicate + self.reported
        o = self.value
        # figure out if i can just return tuple or triple without creating a whole graph

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


def find_cultural_forms(cf):
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
            else:
                return "?????"
        return None

    def get_reg(tag):
        reg = tag.get("reg")
        if reg:
            return reg
        return None

    def get_class():
        classes = cf.find_all("class")
        for x in classes:
            value = x.get("socialrank")
            if not value:
                value = str(x.text)

            cf_list.append(CulturalForm("hasSocialClass", get_reported(x), get_mapped_term("SocialClass", value)))

    def get_denomination():
        pass

    def get_PA():
        # Create theoretical extra triples for now
        # possible predicates:
        # These will also need inverse if we were to maintain consistency?
        # There's also some
        # These are the levels of political involvement
        # MEMBERSHIP --> INVOLVEMENT --> ACTIVISM
        # low --> med --> high

        # possible that we can change these predicates to some of leveling term
        # Should examine data for any contradictions
        # INVOLVEMENTYES --> hasPoliticalInvolvement
        # ACTIVISMYES --> hasActivistRole
        # MEMBERSHIPYES --> hasMembership
        # Membership can be broader to work for general organizations perhaps? ex. religious organizations
        #

        pas = cf.find_all("politicalaffiliation")
        for x in pas:
            # print(x)
            value = get_reg(x)
            if not value:
                value = "__" + str(x.text) + "__"

            cf_list.append(CulturalForm("hasPoliticalAffiliation", get_reported(x), value))
            # Since according to orlando it is a scale and they overlap
            if x.get("activism") == "ACTIVISTYES":
                cf_list.append(CulturalForm("hasActivistRole", None, value))
            elif x.get("involvement") == "INVOLVEMENTYES":
                cf_list.append(CulturalForm("hasPoliticalInvolvement", None, value))
            elif x.get("membership") == "MEMBERSHIPYES":
                cf_list.append(CulturalForm("hasMembership", None, value))

    def get_language():
        # NEED MAPPING TO LOC CODES
        langs = cf.find_all("language")
        for x in langs:
            value = get_reg(x)
            if not value:
                value = x.text

            # Need real value from mapping
            # What if nested ethnicity tag?

            competence = x.get("competence")
            predicate = ""
            if competence == "MOTHER":
                predicate = "hasNativeLinguisticAbility"
            elif competence == "OTHER":
                predicate = "hasLinguisticAbility"
            else:
                predicate = "hasLinguisticAbility"
            cf_list.append(CulturalForm(predicate, None, value))

    def get_forebear_cfs():
        # This optional attribute attaches to the elements Ethnicity, Geographical Heritage, National Heritage, or Race, Colour,
        # has ten possible values: Father, Mother, Parents, Grandfather, Grandmother, Grandparents, Aunt, Uncle, Other, and Family.
        #
        tags = ["racecolour", "nationalheritage", "geogheritage", "ethnicity"]
        # geogheritage and national

        # for x in tags[:1]:
        temp = cf.find_all("language")
        # for y in temp:
            # print(y)
        # This will have to interact will sparql endpoint to check family related triples
        # sparql query to check if person hasMother/hasFather, and there is a valid uri
        # otherwise create the person and familial relation?
        pass
    def get_other_cfs():
        # go through mapping here or no?
        tags = ["nationality", "sexualidentity"]

    # get_forebear_cfs()
    get_class()
    # get_language()
    # get_PA()
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
    return subjects


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
                temp_context = Context(x + "_context" + str(cf_subelements_count[x]), y.get_text(), x)
                cf_subelements_count[x] += 1
                forms_found += 1

                cf_list = find_cultural_forms(cf)
                temp_context.subjects = get_subjects(cf_list)
                person.add_context(temp_context)
                person.add_cultural_form(cf_list)

        if forms_found == 0:
            temp_context = Context(x + "_context" + str(id), cf.get_text())

            cf_list = find_cultural_forms(cf)
            temp_context.subjects = get_subjects(cf_list)

            person.add_context(temp_context)
            person.add_cultural_form(cf_list)
            id += 1


cf_map = {}


def create_cf_map():
    import csv
    global cf_map
    with open('mapping.csv', newline='') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        for row in reader:
            if row[0] not in cf_map:
                cf_map[row[0]] = []
            temp_row = [x.lower().replace("-", " ") for x in row[2:]]

            cf_map[row[0]].append(list(filter(None, [row[1], *temp_row])))


# Currently getting exact match ignoring case and "-"
# todo:
# Will need add some sort of percentage match for failures
# log unmatched term,
# return literal or uri
def get_mapped_term(rdf_type, value):
    if "http://sparql.cwrc.ca/ontologies/cwrc#" not in rdf_type:
        rdf_type = "http://sparql.cwrc.ca/ontologies/cwrc#" + rdf_type

    term = None
    for x in cf_map[rdf_type]:
        if value.lower().replace("-", " ") in x:
            term = x[0]
            break

    if "http" in str(term):
        term = rdflib.term.URIRef(term)
    elif term:
        term = rdflib.term.Literal(term, datatype=rdflib.namespace.XSD.string)
    else:
        term = rdflib.term.Literal("_" + value.lower() + "_", datatype=rdflib.namespace.XSD.string)
    return term


def main():
    import os
    create_cf_map()
    # get_mapped_term("Gender", "MALE")
    # get_mapped_term("Gender", "transgendered male to female")
    # get_mapped_term("PoliticalAffiliation", "sugar boycotter")
    # get_mapped_term("RaceColour", "mixed-race")
    # get_mapped_term("Ethnicity", "jew")
    # get_mapped_term("Religion", "Buddhist")
    # get_mapped_term("Language", "Russian")
    # get_mapped_term("http://sparql.cwrc.ca/ontologies/cwrc#NationalIdentity", "scot")
    # get_mapped_term("Language", "JEW")
    # exit()

    # data = rdflib.Namespace("http://cwrc.ca/cwrcdata/")
    # cwrc = rdflib.Namespace("http://sparql.cwrc.ca/ontologies/cwrc#")
    # g = rdflib.Graph()

    filelist = [filename for filename in sorted(os.listdir("bio_data")) if filename.endswith(".xml")]

    # for filename in filelist[:200]:
    for filename in filelist:
        with open("bio_data/" + filename) as f:
            soup = BeautifulSoup(f, 'lxml')

        # print(filename)
        test_person = Biography(filename[:-3], get_name(soup), get_mapped_term("Gender", get_sex(soup)))

        create_cf_data(soup, test_person)

        print(test_person)
        print("=" * 75)
        # exit()

    # exit()


# test code for creating triples
def test():
    g = rdflib.Graph()
    namespace_manager = rdflib.namespace.NamespaceManager(g)

    cwrc = rdflib.Namespace("http://sparql.cwrc.ca/ontologies/cwrc#")
    data = rdflib.Namespace("http://cwrc.ca/cwrcdata/")
    namespace_manager.bind('cwrc', cwrc, override=False)
    namespace_manager.bind('cwrcdata', data, override=False)

    data.bob  # = rdflib.term.URIRef(u'http://example.org/people/bob')
    data.eve  # = rdflib.term.URIRef(u'http://example.org/people/eve')

    temp1 = ["name1", "name2", "name3"]

    for x in temp1:
        b = str(data) + x
        g.add((rdflib.term.URIRef(b), cwrc.hasBrother, data.eve))

    # g.add((data.bob, cwrc.potato, data.idk))
    # g.add((data.bob, cwrc.something, data.lol))
    # g.add((data.him, cwrc.brother, data.joe))
    # g.add((data.eve, cwrc.hasReligion, data.hindu))
    temp = g.serialize(format="ttl").decode()
    print(temp)
    # for s, p, o in g.triples((None, None, None)):
    #     print(s, p, o)

    exit()

if __name__ == "__main__":
    # auth = [env.env("USER_NAME"), env.env("PASSWORD")]
    # login.main(auth)
    main()
    # test()
