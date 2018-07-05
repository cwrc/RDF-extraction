import rdflib
from rdflib import RDF, RDFS, Literal
import re
from biography import bind_ns, NS_DICT
from context import Context


def strip_all_whitespace(string):
# temp function for condensing the context strings for visibility in testing
    return re.sub('[\s+]', '', str(string))


class School(object):
    """docstring for School"""

    def __init__(self, type, level, name, relious, place):
        super(School, self).__init__()
        self.type = type
        self.level = level
        self.name = name
        self.relious = relious
        self.place = place


# Make a subclass of Context
class Education(Context):
    """docstring for Education"""
    context_types = ["Institutional", "SelfTaught", "Domestic"]
    # context_map = {"classissue": "SocialClassContext", "raceandethnicity": "RaceEthnicityContext",
    #                "nationalityissue": "NationalityContext", "sexuality": "SexualityContext", "politics": "PoliticalContext",
    #                "religion": "ReligionContext", "culturalformation": "CulturalFormContext"}

    def __init__(self, id, text, type, school, awards, subjects, texts, instructors):
        Context __init__(self, id, text, type="education" + type, motivation="describing"):

        self.school = school
        self.awards = awards
        self.studied_subjects = subjects
        self.texts = texts
        self.instructors = instructors

    def to_triple(self, person_uri):
        g = rdflib.Graph()
        namespace_manager = rdflib.namespace.NamespaceManager(g)
        bind_ns(namespace_manager, NS_DICT)
        g.add((self.uri, RDF.type, self.type))
        g.add((self.uri, NS_DICT["oa"].motivatedBy, self.motivation))

        choix = rdflib.term.URIRef(str(self.uri) + "_annotationbody")
        g.add((choix, RDF.type, NS_DICT["oa"].choice))
        g.add((self.uri, NS_DICT["oa"].hasBody, choix))

        # Source hasn't really been figured out
        # g.add((self.uri, NS_DICT["oa"].hasSource, self.src))

        item_1 = rdflib.term.URIRef(str(self.uri) + "_item1_snippettext")
        g.add((item_1, RDF.type, NS_DICT["dctypes"].text))
        g.add((item_1, NS_DICT["dctypes"].description, rdflib.term.Literal(
            self.text, datatype=rdflib.namespace.XSD.string)))

        item_2 = rdflib.term.URIRef(str(self.uri) + "_item2_snippettag")
        g.add((item_2, RDF.type, NS_DICT["dctypes"].text))
        g.add((item_2, NS_DICT["dctypes"].description, rdflib.term.Literal(
            self.tag, datatype=rdflib.namespace.XSD.string)))

        g.add((choix, NS_DICT["as"].items, item_1))
        g.add((choix, NS_DICT["as"].items, item_2))
        for x in self.subjects:
            g.add((choix, NS_DICT["as"].items, x))
            g.add((self.uri, NS_DICT["dcterms"].subject, x))
        return g

    def __str__(self):
        string = "\tid: " + str(self.id) + "\n"
        # text = strip_all_whitespace(str(self.text))
        string += "\ttype: " + str(self.type) + "\n"
        string += "\tmotivation: " + str(self.motivation) + "\n"
        string += "\ttag: \n\t\t{" + str(self.tag) + "}\n"
        string += "\ttext: \n\t\t{" + str(self.text) + "}\n"
        if self.subjects:
            string += "\tsubjects:\n"
            for x in self.subjects:
                string += "\t\t" + str(x) + "\n"
        return string + "\n"

    # def context_count(self,type):
    #     pass
