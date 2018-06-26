import rdflib
from rdflib import RDF, RDFS, Literal
import re

CWRC = rdflib.Namespace("http://sparql.cwrc.ca/ontologies/cwrc#")
DATA = rdflib.Namespace("http://cwrc.ca/cwrcdata/")
OA = rdflib.Namespace("http://www.w3.org/ns/oa#")
AS = rdflib.Namespace("http://www.w3.org/ns/activitystreams#")
DCTYPES = rdflib.Namespace("http://purl.org/dc/dcmitype/")
DCTERMS = rdflib.Namespace("http://purl.org/dc/terms/")


def strip_all_whitespace(string):
# temp function for condensing the context strings in visibility
    return re.sub('[\s+]', '', str(string))


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

        # holding off till we know how src should work may have to do how we're grabbing entries from islandora api
        # self.src = src
        self.type = rdflib.term.URIRef(str(CWRC) + self.context_map[type])
        self.motivation = rdflib.term.URIRef(str(OA) + motivation)
        self.subjects = []
        self.uri = rdflib.term.URIRef(str(DATA) + id)

    def to_triple(self, person_uri):
        g = rdflib.Graph()
        namespace_manager = rdflib.namespace.NamespaceManager(g)

        g.add((self.uri, RDF.type, self.type))
        g.add((self.uri, OA.motivatedBy, self.motivation))

        choix = rdflib.term.URIRef(str(self.uri) + "_choice")
        g.add((choix, RDF.type, OA.choice))
        g.add((self.uri, OA.hasBody, choix))
        # Source hasn't really been figured out
        # g.add((self.uri, OA.hasSource, self.src))

        item_1 = rdflib.term.URIRef(str(self.uri) + "_item1")
        g.add((item_1, RDF.type, DCTYPES.text))
        g.add((item_1, DCTYPES.description, rdflib.term.Literal(self.text, datatype=rdflib.namespace.XSD.string)))

        item_2 = rdflib.term.URIRef(str(self.uri) + "_item2")
        g.add((item_2, RDF.type, DCTYPES.text))
        g.add((item_2, DCTYPES.description, rdflib.term.Literal(self.tag, datatype=rdflib.namespace.XSD.string)))

        g.add((choix, AS.items, item_1))
        g.add((choix, AS.items, item_2))
        for x in self.subjects:
            g.add((choix, AS.items, x))
            g.add((self.uri, DCTERMS.subject, x))
        return g

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
