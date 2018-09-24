import rdflib
from rdflib import RDF, RDFS, Literal
import re
import biography
from context import Context, get_people, get_places
from event import Event
from place import Place
from organizations import get_org, get_org_uri
from log import *
"""
Status: ~65%
Basic School class created
    Scheme for coming up with uris need to be in place
    and what to do about conflict properties 
Rough Education context class created

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

        return g

    def get_instructors(self, tag):
        instructors = []
        instructor_tags = tag.find_all("INSTRUCTOR")
        for instructor in instructor_tags:
            instructors += get_people(instructor)
        return instructors

    def get_locations(self, tag):
        return get_places(tag)


class Education(object):
    """docstring for Education"""

    context_types = ["InstitutionalEducationContext", "SelfTaughtEducationContext", "DomesticEducationContext"]
    context_map = {"INSTITUTIONAL": "InstitutionalEducationContext", "SELF-TAUGHT": "SelfTaughtEducationContext",
                   "DOMESTIC": "DomesticEducationContext", None: "EducationContext"}

    def __init__(self):
        super(Education, self).__init__()
        self.schools = []
        self.awards = []
        self.studied_subjects = []
        self.texts = []
        self.instructors = []
        self.companions = []
        self.contested_behaviour = []

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

        # TODO
        for x in self.studied_subjects:
            # NOTE this is temporary as the uri for the study subjects should be provided before
            subj_uri = str(NS_DICT["cwrc"]) + x
            g.add((self.uri, CWRC.hasSubjectofStudy, rdflib.term.URIRef(strip_all_whitespace(subj_uri))))

        for x in self.awards:
            # NOTE this is temporary as the uri for the study subjects should be provided before
            subj_uri = str(NS_DICT["cwrc"]) + x
            g.add((self.uri, CWRC.hasAward, rdflib.term.URIRef(strip_all_whitespace(subj_uri))))

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

        # TODO
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

        return string + "\n"

    def add_school(self, schools):
        self.schools += schools

    def add_instructor(self, instructors):
        self.instructors += instructors

    def add_companion(self, companions):
        self.companions += companions

    def add_contestedBehaviour(self, behvaviour):
        self.contested_behaviour += behvaviour


class Education2(Context):
    """"""
    context_types = ["InstitutionalEducationContext", "SelfTaughtEducationContext", "DomesticEducationContext"]
    context_map = {"INSTITUTIONAL": "InstitutionalEducationContext", "SELF-TAUGHT": "SelfTaughtEducationContext",
                   "DOMESTIC": "DomesticEducationContext", None: "EducationContext"}

    def __init__(self, id, text, mode, schools, awards, subjects, texts, instructors):
        self.mode = self.context_map[mode]
        super().__init__(id, text, self.mode)
        self.schools = schools
        self.awards = awards
        self.studied_subjects = SUBJECTS
        self.texts = texts
        self.instructors = instructors

    # NOTE: triples need to be redone as some predicates have not been created or well understood
    def to_triple(self, person):
        g = rdflib.Graph()
        namespace_manager = rdflib.namespace.NamespaceManager(g)
        bind_ns(namespace_manager, NS_DICT)
        g += super().to_triple(person.uri)
        for x in self.schools:
            g += x.to_triple(person.uri)
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
            for x in self.STUDIED_SUBJECTS:
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


# TODO: likely merge these into a generic function that will also include mapping
# Some may not work to be generic as they may include a <name> tag
# and a uri for that person will have to be found or created
def get_study_subjects(subj_tags):
    return [get_value(x) for x in subj_tags]


def get_awards(award_tags):
    return [get_value(x) for x in award_tags]


def get_texts(text_tags):
    return [get_value(x) for x in text_tags]


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

        schools.append(School(name, school_types, lvl, tag))

    return schools


def get_contested_behaviour(tag):
    return [limit_words(get_value(x), 20) for x in tag.find_all("CONTESTEDBEHAVIOUR")]


def create_education(tag):
    temp_education = Education()
    temp_education.add_school(get_school(tag.find_all("SCHOOL")))
    temp_education.add_instructor(School.get_instructors(None, tag))
    temp_education.add_companion(get_companion(tag))

    temp_education.add_contestedBehaviour(get_contested_behaviour(tag))
    # degrees
    # subject
    # text
    # awards

    # print(temp_education)
    # subjects = get_study_subjects(education.find_all("subject"))
    # awards = get_awards(education.find_all("award"))
    # texts = get_texts(education.find_all("text"))
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
        print("x" * 100)
        print(context_id)

        education_list = create_education(tag)
        if education_list:
            temp_context = Context(context_id, tag, Education.context_map[context_type])
            temp_context.link_triples(education_list)
            person.add_education(education_list)
        else:
            temp_context = Context(context_id, tag, Education.context_map[context_type], "identifying")

        if list_type == "events":
            education_event_count[context_type] += 1
            event_title = person.name + " - " + Education.context_map[context_type] + " Event"
            event_uri = person.id + "_" + \
                Education.context_map[context_type] + "_Event" + str(education_event_count[context_type])
            temp_event = Event(event_title, event_uri, tag)
            temp_context.link_event(temp_event)
            person.add_event(temp_event)

        # print(temp_context)
        # get_subjects(education_list, person)
        # print(temp_context.to_triple(person).serialize(format="ttl").decode())
        person.add_context(temp_context)


def get_subjects(component, person):
    subjects = []
    temp_graph = component.to_triple(person)
    subjects += [x for x in temp_graph.objects(None, None)]

    return list(set(subjects))


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
        print()
        print(mode)
        paragraphs = education.find_all("P")
        events = education.find_all("CHRONSTRUCT")

        extract_education(paragraphs, mode, person)
        extract_education(events, mode, person, "events")
        # print(education)


def extract_education_data2(bio, person):
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
    test_cases += ["bankis-b.xml", "burnfr-b.xml"]
    for filename in test_cases:
    # for filename in filelist:
        with open("bio_data/" + filename) as f:
            soup = BeautifulSoup(f, 'lxml-xml')

        print(filename)
        test_person = biography.Biography(
            filename[:-6], get_name(soup), culturalForm.get_mapped_term("Gender", get_sex(soup)))

        extract_education_data(soup, test_person)
        print()
        graph = test_person.to_graph()

        # extract_log.subtitle("Entry #" + str(entry_num))
        # extract_log.msg(str(test_person))
        # extract_log.subtitle(str(len(graph)) + " triples created")
        extract_log.msg(test_person.to_file(graph))
        # extract_log.subtitle("Entry #" + str(entry_num))
        # extract_log.msg("\n\n")

        # file = open("education_turtle/" + filename[:-6] + "_education.ttl", "w", encoding="utf-8")
        # file.write("#" + str(len(graph)) + " triples created\n")
        # file.write(graph.serialize(format="ttl").decode())
        # file.close()

        # uber_graph += graph
        # entry_num += 1

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
