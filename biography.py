import rdflib
from rdflib import RDF  #, RDFS, Literal

CWRC = rdflib.Namespace("http://sparql.cwrc.ca/ontologies/cwrc#")
FOAF = rdflib.Namespace('http://xmlns.com/foaf/0.1/')
DATA = rdflib.Namespace("http://cwrc.ca/cwrcdata/")


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
