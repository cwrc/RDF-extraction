import biography
import rdflib
import re
from context import Context, get_people, get_places, get_titles
from difflib import get_close_matches
from event import Event
from log import *
from organizations import get_org, get_org_uri
from place import Place
from rdflib import RDF, RDFS, Literal
"""
Status: ~75%
TODO:
Handle name tags with subject tags
TEXT tags
    name within text
    title within text
"""

log = Log("log/education/errors")
log.test_name("Education extraction Error Logging")
extract_log = Log("log/education/extraction")
extract_log.test_name("Education extraction Test Logging")
turtle_log = Log("log/education/triples")
turtle_log.test_name("Education extracted Triples")

CWRC = biography.NS_DICT["cwrc"]
education_count = {
    "INSTITUTIONAL": 0,
    "SELF-TAUGHT": 0,
    "DOMESTIC": 0,
    None: 0,
}
education_event_count = {
    "INSTITUTIONAL": 0,
    "SELF-TAUGHT": 0,
    "DOMESTIC": 0,
    None: 0,
}


def strip_all_whitespace(string):
    # temp function for condensing the context strings for visibility in testing
    return re.sub('[\s+]', '', str(string))


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

    attending_map = {
        CWRC.PrimarySchool: CWRC.attendsPrimarySchool,
        CWRC.SecondarySchool: CWRC.attendsSecondarySchool,
        CWRC.PostSecondarySchool: CWRC.attendsPostSecondarySchool,
    }

    def __init__(self, name, types, level, tag):
        super(School, self).__init__()
        school_org = get_org(tag)
        if school_org:
            self.uri = get_org_uri(school_org[0])
        else:
            self.uri = biography.make_standard_uri(strip_all_whitespace(name) + " EduOrg", "cwrc")

        self.name = name
        self.level = level
        if self.level:
            self.level = School.school_type_map[level]

        self.types = [School.school_type_map[x] for x in types]
        self.instructors = self.get_instructors(tag)
        self.locations = self.get_locations(tag)
        self.studied_subjects = []

    def __str__(self):
        string = "\t\tname: " + str(self.name) + "\n"
        if self.types:
            string += "\t\tTypes:\n"
            for x in self.types:
                string += "\t\t" + str(x) + "\n"
        if self.instructors:
            string += "\t\tInstructors:\n"
            for x in self.instructors:
                string += "\t\t" + str(x) + "\n"
        if self.locations:
            string += "\t\tLocations:\n"
            for x in self.locations:
                string += "\t\t" + str(x) + "\n"
        return string

    def to_tuple(self, person):
        # For future testing
        p = str(NS_DICT["cwrc"]) + self.predicate + self.reported
        o = self.value
        return ((person.uri, rdflib.term.URIRef(p), o))

    def to_triple(self, person):
        g = rdflib.Graph()
        namespace_manager = rdflib.namespace.NamespaceManager(g)
        biography.bind_ns(namespace_manager, biography.NS_DICT)

        g.add((self.uri, biography.NS_DICT["foaf"].name, rdflib.Literal(self.name)))
        g.add((self.uri, RDF.type, CWRC.EducationalOrganization))
        if self.level:
            g.add((person.uri, self.attending_map[self.level], self.uri))
        else:
            g.add((person.uri, CWRC.attends, self.uri))

        for x in self.types:
            g.add((self.uri, RDF.type, x))

        for x in self.instructors:
            g.add((self.uri, CWRC.hasEmployee, x))

        for x in self.locations:
            g.add((self.uri, CWRC.hasLocation, x))

        for x in self.studied_subjects:
            g.add((self.uri, CWRC.teachesEducationalSubject, x))

        return g

    def get_instructors(self, tag):
        instructors = []
        instructor_tags = tag.find_all("INSTRUCTOR")
        for instructor in instructor_tags:
            instructors += get_people(instructor)
        return instructors

    def get_locations(self, tag):
        return get_places(tag)

    def add_studied_subjects(self, subject):
        self.studied_subjects += subject


class EducationalAward(object):
    """docstring for EducationalAward"""
    award_keywords = ["scholarship", "prize","medal", "fellow","fellowship","essay","bursary","exhibition","distinction","honours","studentship"]
    award_map = {
        "scholarship": CWRC.Scholarship,
        "prize": CWRC.EducationalPrize,
        "medal": CWRC.EducationalPrize,
        "fellow": CWRC.Fellowship,
        "fellowship": CWRC.Fellowship,
        "essay": CWRC.EssayAward,
        "bursary": CWRC.Bursary,
        "exhibition": CWRC.Scholarship,
        "distinction": CWRC.Distinction,
        "honours": CWRC.Distinction,
        "studentship": CWRC.Studentship
    }

    def __init__(self, name):
        super(EducationalAward, self).__init__()
        self.name = name
        self.award_type = self.get_award_type(name)
        if not self.award_type:
            self.award_type = [CWRC.EducationalAward]

        text = ' '.join(str(name).split())
        words = text.split(" ")
        text = ' '.join(words[:15])
        self.uri = biography.create_uri("cwrc", strip_all_whitespace(text))

    def get_award_type(self, name):
        types = []
        for x in self.award_keywords:
            if x in name.lower():
                types.append(self.award_map[x])
        return list(set(types))

    def __str__(self):
        string = "\t\tname: " + str(self.name) + "\n"
        string += "\t\turi: " + str(self.uri) + "\n"
        if self.award_type:
            string += "\t\tTypes:\n"
            for x in self.award_type:
                string += "\t\t" + str(x) + "\n"
        return string

    def to_tuple(self, person):
        # For future testing
        p = str(NS_DICT["cwrc"]) + self.predicate + self.reported
        o = self.value
        return ((person.uri, rdflib.term.URIRef(p), o))

    def to_triple(self, person):
        g = rdflib.Graph()
        namespace_manager = rdflib.namespace.NamespaceManager(g)
        biography.bind_ns(namespace_manager, biography.NS_DICT)

        g.add((self.uri, biography.NS_DICT["foaf"].name, rdflib.Literal(self.name)))
        g.add((person.uri, CWRC.hasAward, self.uri))
        for x in self.award_type:
            g.add((self.uri, RDF.type, x))
        return g


class Education(object):
    """docstring for Education"""

    context_types = ["InstitutionalEducationContext", "SelfTaughtEducationContext", "DomesticEducationContext"]
    context_map = {"INSTITUTIONAL": "InstitutionalEducationContext", "SELF-TAUGHT": "SelfTaughtEducationContext",
                   "DOMESTIC": "DomesticEducationContext", None: "EducationContext"}

    def __init__(self):
        super(Education, self).__init__()
        self.schools = []
        self.instructors = []
        self.companions = []
        self.contested_behaviour = []
        self.studied_subjects = []
        self.degrees = []
        self.degree_subjects = []
        self.awards = []

        self.texts = []
        self.edu_texts = []

    def to_triple(self, person):
        g = rdflib.Graph()
        namespace_manager = rdflib.namespace.NamespaceManager(g)
        biography.bind_ns(namespace_manager, biography.NS_DICT)

        for x in self.schools:
            g += x.to_triple(person)

        for x in self.instructors:
            g.add((person.uri, CWRC.hasInstructor, x))

        for x in self.companions:
            g.add((person.uri, CWRC.hasCompanion, x))

        for x in self.contested_behaviour:
            g.add((person.uri, CWRC.hasContestedBehaviour, Literal(x)))

        for x in self.studied_subjects:
            g.add((person.uri, CWRC.studies, x))

        for x in self.edu_texts:
            g.add((x, RDF.type, CWRC.EducationalText))
            g.add((person.uri, CWRC.studies, x))

        for x in self.degrees:
            g.add((person.uri, CWRC.hasCredential, x))

        for x in self.degree_subjects:
            g.add((person.uri, CWRC.hasCredentialSubject, x))

        for x in self.awards:
            g += x.to_triple(person)
        
        # TODO text

        return g

    def __str__(self):
        string = "Education:\n"
        if self.schools:
            string += "\tschools:\n"
            for x in self.schools:
                string += str(x) + "\n"
        if self.instructors:
            string += "\tinstructors:\n"
            for x in self.instructors:
                string += "\t\t" + str(x) + "\n"
        if self.companions:
            string += "\tcompanions:\n"
            for x in self.companions:
                string += "\t\t" + str(x) + "\n"
        if self.contested_behaviour:
            string += "\tcontested behaviour:\n"
            for x in self.contested_behaviour:
                string += "\t\t" + str(x) + "\n"
        if self.awards:
            string += "\tawards:\n"
            for x in self.awards:
                string += "\t\t" + str(x) + "\n"
        if self.studied_subjects:
            string += "\tstudied_subjects:\n"
            for x in self.studied_subjects:
                string += "\t\t" + str(x) + "\n"
        # TODO
        if self.texts:
            string += "\ttexts:\n"
            for x in self.texts:
                string += "\t\t" + str(x) + "\n"

        return string + "\n"

    def add_school(self, schools):
        self.schools += schools

    def add_instructor(self, instructors):
        self.instructors += instructors

    def add_companion(self, companions):
        self.companions += companions

    def add_contested_behaviour(self, behvaviour):
        self.contested_behaviour += behvaviour

    def add_studied_subjects(self, subject):
        self.studied_subjects += subject

    def add_degrees(self, degree):
        self.degrees += degree

    def add_degree_subjects(self, subject):
        self.degree_subjects += subject

    def add_awards(self, award):
        self.awards += award

    def add_edu_texts(self, title):
        self.edu_texts += title


def get_reg(tag):
    return get_attribute(tag, "REG")


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


def get_study_subjects(subj_tags):
    return [get_mapped_term("Subject", get_value(x)) for x in subj_tags]


def get_degrees(subj_tags):
    return [get_mapped_term("Degree", get_value(x)) for x in subj_tags]


def get_awards(award_tags):
    return [EducationalAward(get_value(x)) for x in award_tags]


def get_texts(text_tags):
    return [x for x in text_tags]
    # return [get_value(x) for x in text_tags]


def get_companion(tag):
    companions = []
    companion_tags = tag.find_all("COMPANION")
    for companion in companion_tags:
        companions += get_people(companion)
    return companions


def get_school(school_tags):
    schools = []
    for tag in school_tags:
        name = get_value(tag)
        lvl = get_attribute(tag, "INSTITUTIONLEVEL")

        school_types = [x for x in [lvl, get_attribute(tag, "STUDENTBODY"), get_attribute(
            tag, "RELIGIOUS"), get_attribute(tag, "INSTITUTION")] if x]

        temp_school = School(name, school_types, lvl, tag)
        temp_school.add_studied_subjects(get_study_subjects(tag.find_all("SUBJECT")))

    return schools


def get_contested_behaviour(tag):
    return [limit_words(get_value(x), 20) for x in tag.find_all("CONTESTEDBEHAVIOUR")]


def get_degree_subjects(tag):
    subjects = []
    for x in tag.find_all("DEGREE"):
        subjects += x.find_all("SUBJECT")

    return get_study_subjects(subjects)


def create_education(tag, person):
    temp_education = Education()
    temp_education.add_school(get_school(tag.find_all("SCHOOL")))
    temp_education.add_instructor(School.get_instructors(None, tag))
    temp_education.add_companion(get_companion(tag))
    temp_education.add_contested_behaviour(get_contested_behaviour(tag))
    temp_education.add_degrees(get_degrees(tag.find_all("DEGREE")))
    temp_education.add_studied_subjects(get_study_subjects(tag.find_all("SUBJECT")))
    temp_education.add_degree_subjects(get_degree_subjects(tag))
    temp_education.add_awards(get_awards(tag.find_all("AWARD")))
    # print()

    texts = get_texts(tag.find_all("TEXT"))
    works = []
    titles = []
    for x in texts:
        works += get_people(x)
        titles += get_titles(x)

    # Add mapping of titles
    temp_education.add_edu_texts(titles)
    # temp_education.add_works(work)

    return temp_education


def limit_words(string, word_count):
    text = ' '.join(str(string).split())
    words = text.split(" ")
    text = ' '.join(words[:word_count])
    if len(words) > word_count:
        text += "..."
    return text


def extract_education(tag_list, context_type, person, list_type="paragraphs"):
    """ Creates the location relation and ascribes them to the person along with the associated
        contexts and event
    """
    global education_count
    global education_event_count

    for tag in tag_list:
        temp_context = None
        education_list = None
        education_count[context_type] += 1

        if context_type is None:
            context_id = person.id + "_EducationContext_" + str(education_count[context_type])
        else:
            context_id = person.id + "_" + Education.context_map[context_type] + "_"
            context_id += str(education_count[context_type])

        education_list = create_education(tag, person)
        if len(education_list.to_triple(person)) > 0:
            temp_context = Context(context_id, tag, Education.context_map[context_type])
            temp_context.link_triples(education_list)
            person.add_education(education_list)
        else:
            temp_context = Context(context_id, tag, Education.context_map[context_type], "identifying")

        if list_type == "events":
            education_event_count[context_type] += 1
            event_type = Education.context_map[context_type].split("Context")[0]
            event_title = person.name + " - " + event_type + " Event"
            event_uri = person.id + "_" + event_type + "_Event" + str(education_event_count[context_type])
            temp_event = Event(event_title, event_uri, tag)
            temp_context.link_event(temp_event)
            person.add_event(temp_event)

        person.add_context(temp_context)


def get_subjects(component, person):
    subjects = []
    temp_graph = component.to_triple(person)
    subjects += [x for x in temp_graph.objects(None, None)]

    return list(set(subjects))


def clean_term(string):
    string = string.lower().replace("-", " ").strip().replace(" ", "")
    return string


def create_edu_map():
    import csv
    global EDU_MAP
    with open('education_mapping.csv', newline='') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        for row in reader:
            if row[0] not in EDU_MAP:
                EDU_MAP[row[0]] = []
            temp_row = [clean_term(x) for x in row[2:]]
            EDU_MAP[row[0]].append(list(filter(None, [row[1], *temp_row])))


EDU_MAP = {}
create_edu_map()
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
    map_attempt += 1
    term = None
    temp_val = clean_term(value)
    for x in EDU_MAP[rdf_type]:
        if temp_val in x:
            term = x[0]
            map_success += 1
            break

    if "http" in str(term):
        term = rdflib.term.URIRef(term)
    elif term:
        term = rdflib.term.Literal(term, datatype=rdflib.namespace.XSD.string)
    else:
        term = rdflib.term.Literal("_" + value.lower() + "_", datatype=rdflib.namespace.XSD.string)
        if retry:
            map_attempt -= 1
        else:
            map_fail += 1
            possibilites = []
            for x in EDU_MAP[rdf_type]:
                if get_close_matches(value.lower(), x):
                    possibilites.append(x[0])
            if type(term) is rdflib.term.Literal:
                update_fails(rdf_type, value)
            else:
                update_fails(rdf_type, value + "->" + str(possibilites) + "?")
    return term


def extract_education_data(bio, person):
    global education_count
    global education_event_count
    education_count = {
        "INSTITUTIONAL": 0,
        "SELF-TAUGHT": 0,
        "DOMESTIC": 0,
        None: 0,
    }
    education_event_count = {
        "INSTITUTIONAL": 0,
        "SELF-TAUGHT": 0,
        "DOMESTIC": 0,
        None: 0,
    }

    education_hist = bio.find_all("EDUCATION")

    for education in education_hist:
        mode = education.get("MODE")
        paragraphs = education.find_all("P")
        events = education.find_all("CHRONSTRUCT")

        extract_education(paragraphs, mode, person)
        extract_education(events, mode, person, "events")


def main():
    import os
    from bs4 import BeautifulSoup
    import culturalForm

    def get_name(bio):
        return (bio.BIOGRAPHY.DIV0.STANDARD.text)

    def get_sex(bio):
        return (bio.BIOGRAPHY.get("SEX"))

    filelist = [filename for filename in sorted(os.listdir("bio_data")) if filename.endswith(".xml")]
    entry_num = 1

    uber_graph = rdflib.Graph()
    namespace_manager = rdflib.namespace.NamespaceManager(uber_graph)
    biography.bind_ns(namespace_manager, biography.NS_DICT)

    # for filename in filelist[:200]:
    # for filename in filelist[-5:]:
    test_cases = ["shakwi-b.xml", "woolvi-b.xml", "seacma-b.xml", "atwoma-b.xml",
                  "alcolo-b.xml", "bronem-b.xml", "bronch-b.xml", "levyam-b.xml"]
    test_cases += ["bankis-b.xml", "burnfr-b.xml", "annali-b.xml", "carrdo-b.xml"]
    # for filename in test_cases:
    for filename in filelist:
        with open("bio_data/" + filename) as f:
            soup = BeautifulSoup(f, 'lxml-xml')

        print(filename)
        test_person = biography.Biography(
            filename[:-6], get_name(soup), culturalForm.get_mapped_term("Gender", get_sex(soup)))

        extract_education_data(soup, test_person)
        print()
        graph = test_person.to_graph()

        extract_log.subtitle("Entry #" + str(entry_num))
        extract_log.msg(str(test_person))
        extract_log.subtitle(str(len(graph)) + " triples created")
        extract_log.msg(test_person.to_file(graph))
        extract_log.subtitle("Entry #" + str(entry_num))
        extract_log.msg("\n\n")

        file = open("education_turtle/" + filename[:-6] + "_education.ttl", "w", encoding="utf-8")
        file.write("#" + str(len(graph)) + " triples created\n")
        file.write(graph.serialize(format="ttl").decode())
        file.close()

        uber_graph += graph
        entry_num += 1

    turtle_log.subtitle(str(len(uber_graph)) + " triples created")
    turtle_log.msg(uber_graph.serialize(format="ttl").decode(), stdout=False)
    turtle_log.msg("")


def test():
    exit()

if __name__ == "__main__":
    # auth = [env.env("USER_NAME"), env.env("PASSWORD")]
    # login.main(auth)
    # test()
    main()
