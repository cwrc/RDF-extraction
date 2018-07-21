import rdflib
from rdflib import RDF, RDFS, Literal
import re
from biography import bind_ns, NS_DICT
from context import Context
from place import Place
from log import *
"""
Status: ~65%
Basic School class created
    Scheme for coming up with uris need to be in place
    and what to do about conflict properties 
Rough Education context class created
    Triples need to figured out testdata is outdated
    Graffle is also outdated and doesn't include OA
Subject of study mapping still needed

Events need to be created--> bigger issue
TODO: 
Review produced triples
review graffle and testdata with susan
Get status update on subject of study sheet 
Review naming structure with susan

"""

log = Log("log/education/errors")
log.test_name("Education extraction Error Logging")
extract_log = Log("log/education/extraction")
extract_log.test_name("Education extraction Test Logging")
turtle_log = Log("log/education/triples")
turtle_log.test_name("Education extracted Triples")

CWRC = NS_DICT["cwrc"]


def strip_all_whitespace(string):
# temp function for condensing the context strings for visibility in testing
    return re.sub('[\s+]', '', str(string))

# TODO:
"""
Handle places, orgnames, instructors ,subjects within school tag
"""


class School(object):
    """docstring for School"""
#  Institution, Institution Level, Religious, and Student Body
    school_type_map = {
        # Institution Level
        "PRIMARY": CWRC.PrimarySchool,
        "SECONDARY": CWRC.SecondarySchool,
        "POST-SECONDARY": CWRC.PostSecondarySchool,
        # Religion
        # NOTE: idk about secular school as theres no negation attribute
        "RELIGIOUSYES": CWRC.ReligiousSchool,
        # Student body
        "SINGLESEX": CWRC.SingleSexSchool,
        "CO-ED": CWRC.CoEducationalSchool,
        # Institution Type
        "BOARDING": CWRC.BoardingSchool,
        "COMPREHENSIVE": CWRC.ComprehensiveSchool,
        "DAMESCHOOL": CWRC.DameSchool,
        "DAYSCHOOL": CWRC.DaySchool,
        "GRAMMAR": CWRC.GrammarSchool,
        "PREP": CWRC.PrepSchool,
        "PRIVATE": CWRC.PrivateSchool,
        "SECONDARYMODERN": CWRC.SecondaryModernSchool,
        "STATE": CWRC.StateSchool,
        "TRADESCHOOL": CWRC.TradeSchool,
    }

    def __init__(self, name, type, level, religious, std_body):
        super(School, self).__init__()
        self.name = name

        self.level = level
        if self.level:
            self.level = rdflib.term.URIRef(level)

        self.type = type
        if self.type:
            self.type = rdflib.term.URIRef(type)

        self.religious = religious
        if self.religious:
            self.religious = rdflib.term.URIRef(religious)

        self.student_body = std_body
        if self.student_body:
            self.student_body = rdflib.term.URIRef(std_body)

        self.uri = rdflib.term.URIRef(str(NS_DICT["cwrc"]) + strip_all_whitespace(name))
        # self.place = place

    def __str__(self):
        string = "\tname: " + str(self.name) + "\n"
        if self.type:
            string += "\tinstitution type: " + str(self.type) + "\n"
        if self.level:
            string += "\tlevel: " + str(self.level) + "\n"
        if self.religious:
            string += "\treligiousness: " + str(self.religious) + "\n"
        if self.student_body:
            string += "\tstudent body: " + str(self.student_body) + "\n"
        return string

    def to_tuple(self, person_uri):
        # For future testing
        p = str(NS_DICT["cwrc"]) + self.predicate + self.reported
        o = self.value
        return ((person_uri, rdflib.term.URIRef(p), o))

    def to_triple(self, person_uri):

        g = rdflib.Graph()

        g.add((person_uri, CWRC.attends, self.uri))
        g.add((self.uri, NS_DICT["foaf"].name, rdflib.Literal(self.name)))
        g.add((self.uri, RDF.type, CWRC.EducationalOrganization))

        if self.level:
            g.add((self.uri, RDF.type, self.level))
        if self.type:
            g.add((self.uri, RDF.type, self.type))
        if self.religious:
            g.add((self.uri, RDF.type, self.religious))
        if self.student_body:
            g.add((self.uri, RDF.type, self.student_body))
        return g


class Education(Context):
    """a subclass of Context"""
    context_types = ["InstitutionalEducationContext", "SelfTaughtEducationContext", "DomesticEducationContext"]
    context_map = {"INSTITUTIONAL": "InstitutionalEducationContext", "SELF-TAUGHT": "SelfTaughtEducationContext",
                   "DOMESTIC": "DomesticEducationContext", None: "EducationContext"}

    def __init__(self, id, text, mode, schools, awards, subjects, texts, instructors):
        self.mode = self.context_map[mode]
        super().__init__(id, text, self.mode)
        self.schools = schools
        self.awards = awards
        self.studied_subjects = subjects
        self.texts = texts
        self.instructors = instructors

    # NOTE: triples need to be redone as some predicates have not been created or well understood
    def to_triple(self, person_uri):
        g = rdflib.Graph()
        namespace_manager = rdflib.namespace.NamespaceManager(g)
        bind_ns(namespace_manager, NS_DICT)
        g += super().to_triple(person_uri)
        for x in self.schools:
            g += x.to_triple(person_uri)
            g.add((self.uri, CWRC.hasInstitution, x.uri))

        for x in self.studied_subjects:
            # NOTE this is temporary as the uri for the study subjects should be provided before
            subj_uri = str(NS_DICT["cwrc"]) + x
            g.add((self.uri, CWRC.hasSubjectofStudy, rdflib.term.URIRef(strip_all_whitespace(subj_uri))))

        for x in self.awards:
            # NOTE this is temporary as the uri for the study subjects should be provided before
            subj_uri = str(NS_DICT["cwrc"]) + x
            g.add((self.uri, CWRC.hasAward, rdflib.term.URIRef(strip_all_whitespace(subj_uri))))

        for x in self.instructors:
            # NOTE this is temporary as the uri for the study subjects should be provided before
            subj_uri = str(NS_DICT["cwrc"]) + x
            g.add((self.uri, CWRC.hasInstructor, rdflib.term.URIRef(strip_all_whitespace(subj_uri))))

        return g

# TODO
    def __str__(self):
        string = "\tid: " + str(self.id) + "\n"
        # text = strip_all_whitespace(str(self.text))
        string += "\ttype: " + str(self.mode) + "\n"
        string += "\tmotivation: " + str(self.motivation) + "\n"
        string += "\ttag: \n\t\t{" + str(self.tag) + "}\n"
        string += "\ttext: \n\t\t{" + str(self.text) + "}\n"
        if self.subjects:
            string += "\tsubjects:\n"
            for x in self.subjects:
                string += "\t\t" + str(x) + "\n"

        if self.schools:
            string += "\tschools:\n"
            for x in self.schools:
                string += "\t\t" + str(x) + "\n"
        if self.awards:
            string += "\tawards:\n"
            for x in self.awards:
                string += "\t\t" + str(x) + "\n"
        if self.studied_subjects:
            string += "\tstudied_subjects:\n"
            for x in self.studied_subjects:
                string += "\t\t" + str(x) + "\n"
        if self.texts:
            string += "\ttexts:\n"
            for x in self.texts:
                string += "\t\t" + str(x) + "\n"
        if self.instructors:
            string += "\tinstructors:\n"
            for x in self.instructors:
                string += "\t\t" + str(x) + "\n"

        return string + "\n"

    # def context_count(self,type):
    #     pass


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


# TODO: likely merge these into a generic function that will also include mapping
# Some may not work to be generic as they may include a <name> tag
# and a uri for that person will have to be found or created
def get_study_subjects(subj_tags):
    return [get_value(x) for x in subj_tags]


def get_awards(award_tags):
    return [get_value(x) for x in award_tags]


def get_texts(text_tags):
    return [get_value(x) for x in text_tags]


def get_instructors(instructor_tags):
    return [get_value(x) for x in instructor_tags]


def get_school(school_tags):
#  Institution, Institution Level, Religious, and Student Body
    schools = []
    for x in school_tags:
        log.msg(str(x))
        name = get_value(x)
        type = get_attribute(x, "institution")
        if type in School.school_type_map:
            type = School.school_type_map[type]

        lvl = get_attribute(x, "institutionlevel")
        if lvl in School.school_type_map:
            lvl = School.school_type_map[lvl]

        population = get_attribute(x, "studentbody")
        if population in School.school_type_map:
            population = School.school_type_map[population]

        religious = get_attribute(x, "religious")
        if religious in School.school_type_map:
            religious = School.school_type_map[religious]

        schools.append(School(name, type, lvl, religious, population))
    # return School(name, type, level, religious):
    return schools

# def scrape_schools():
#     pass


def extract_education_data(bio, person):
    education_hist = bio.find_all("education")
    modes = []
    count = 1

    uber_graph = rdflib.Graph()
    namespace_manager = rdflib.namespace.NamespaceManager(uber_graph)
    bind_ns(namespace_manager, NS_DICT)

    for education in education_hist:
        # print(education)
        mode = education.get("mode")
        subjects = get_study_subjects(education.find_all("subject"))
        schools = get_school(education.find_all("school"))
        awards = get_awards(education.find_all("award"))
        texts = get_texts(education.find_all("text"))
        instructors = get_instructors(education.find_all("instructor"))
        # print(mode)
        # for x in subjects:
        #     print(x)

        for x in schools:
            log.msg(str(x))
            # print(x)

        if mode in modes:
            count += 1

        id = person.id + "_" + str(Education.context_map[mode])
        if count > 1:
            id += str(count)
        temp_education = Education(id, education, mode, schools, awards, subjects, texts, instructors)
        modes.append(mode)
        uber_graph += temp_education.to_triple(person.uri)
        extract_log.msg(str(temp_education))
        person.add_education_context(temp_education)

    turtle_log.subtitle("Education context for " + person.name)
    turtle_log.subtitle(str(len(uber_graph)) + " triples created")
    turtle_log.msg(uber_graph.serialize(format="ttl").decode(), stdout=False)

    return uber_graph

    print("AYYY")
