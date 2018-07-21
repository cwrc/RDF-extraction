import rdflib
from rdflib import RDF, RDFS, Literal
import re
from biography import bind_ns, NS_DICT

"""
Status: ~75%
OA has been implemented (primaryily describing)
However identifying contexts may need more handling
TODO: Review triples related to identifying contexts
"""


def strip_all_whitespace(string):
# temp function for condensing the context strings for visibility in testing
    return re.sub('[\s+]', '', str(string))

MAX_WORD_COUNT = 35


class Context(object):
    """docstring for Context"""
    context_types = ["GenderContext", "PoliticalContext", "SocialClassContext",
                     "SexualityContext", "RaceEthnicityContext", "ReligionContext", "NationalityContext"]
    context_map = {"classissue": "SocialClassContext", "raceandethnicity": "RaceEthnicityContext",
                   "nationalityissue": "NationalityContext", "sexuality": "SexualityContext", "politics": "PoliticalContext",
                   "religion": "ReligionContext", "culturalformation": "CulturalFormContext"}

    def __init__(self, id, text, context_type="culturalformation", motivation="describing"):
        super(Context, self).__init__()
        self.id = id

        self.tag = text
        # Will possibly have to clean up citations sans ()
        self.text = ' '.join(str(text.get_text()).split())
        words = self.text.split(" ")
        self.text = ' '.join(words[:MAX_WORD_COUNT])
        if len(words) > MAX_WORD_COUNT:
            self.text += "..."

        # NOTE: holding off till we know how src should work may have to do how we're grabbing entries from islandora api
        # self.src = src
        if context_type in self.context_map:
            self.context_type = rdflib.term.URIRef(str(NS_DICT["cwrc"]) + self.context_map[context_type])
        else:
            self.context_type = rdflib.term.URIRef(str(NS_DICT["cwrc"]) + context_type)

        self.motivation = rdflib.term.URIRef(str(NS_DICT["oa"]) + motivation)
        self.subjects = []
        self.uri = rdflib.term.URIRef(str(NS_DICT["data"]) + id)

    def to_triple(self, person_uri):
        g = rdflib.Graph()
        namespace_manager = rdflib.namespace.NamespaceManager(g)
        bind_ns(namespace_manager, NS_DICT)
        g.add((self.uri, RDF.type, self.context_type))
        g.add((self.uri, NS_DICT["oa"].motivatedBy, self.motivation))
        g.add((self.uri, NS_DICT["oa"].hasTarget, person_uri))

        choix = rdflib.term.URIRef(str(self.uri) + "_annotationbody")
        g.add((choix, RDF.type, NS_DICT["oa"].choice))
        g.add((self.uri, NS_DICT["oa"].hasBody, choix))

        # Source hasn't really been figured out
        # g.add((self.uri, NS_DICT["oa"].hasSource, self.src))

        item_1 = rdflib.term.URIRef(str(self.uri) + "_item1_snippettext")
        g.add((item_1, RDF.type, NS_DICT["dctypes"].text))
        g.add((item_1, NS_DICT["dctypes"].description, rdflib.term.Literal(
            self.text, datatype=rdflib.namespace.XSD.string)))

        # item_2 = rdflib.term.URIRef(str(self.uri) + "_item2_snippettag")
        # g.add((item_2, RDF.type, NS_DICT["dctypes"].text))
        # g.add((item_2, NS_DICT["dctypes"].description, rdflib.term.Literal(
        #     self.tag, datatype=rdflib.namespace.XSD.string)))

        g.add((choix, NS_DICT["as"].items, item_1))
        # g.add((choix, NS_DICT["as"].items, item_2))
        for x in self.subjects:
            g.add((choix, NS_DICT["as"].items, x))
            g.add((self.uri, NS_DICT["dcterms"].subject, x))
        return g

    def __str__(self):
        string = "\tid: " + str(self.id) + "\n"
        # text = strip_all_whitespace(str(self.text))
        string += "\ttype: " + str(self.context_type) + "\n"
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
