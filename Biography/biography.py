import rdflib
from rdflib import RDF, RDFS, Literal
# from context import Context
# from culturalForm import CulturalForm
# from event import Event

NS_DICT = {
    "as": rdflib.Namespace("http://www.w3.org/ns/activitystreams#"),
    "cwrc": rdflib.Namespace("http://sparql.cwrc.ca/ontologies/cwrc#"),
    "data": rdflib.Namespace("http://cwrc.ca/cwrcdata/"),
    "dctypes": rdflib.Namespace("http://purl.org/dc/dcmitype/"),
    "foaf": rdflib.Namespace('http://xmlns.com/foaf/0.1/'),
    "oa": rdflib.Namespace("http://www.w3.org/ns/oa#"),
    "dcterms": rdflib.Namespace("http://purl.org/dc/terms/"),
    "org": rdflib.Namespace("http://www.w3.org/ns/org#"),
    "skos": rdflib.Namespace("http://www.w3.org/2004/02/skos/core#")
    # "gn": rdflib.Namespace("http://www.geonames.org/ontology#")
}


def bind_ns(namespace_manager, ns_dictionary):
    for x in ns_dictionary.keys():
        namespace_manager.bind(x, ns_dictionary[x], override=False)


def make_standard_uri(std_str, ns="data"):
    """Makes uri based of string, removes punctuation and replaces spaces with an underscore
    v2, leaving hypens
    """
    import string
    translator = str.maketrans('', '', string.punctuation.replace("-", ""))
    temp_str = std_str.translate(translator)
    temp_str = temp_str.replace(" ", "_")
    return rdflib.term.URIRef(str(NS_DICT[ns]) + temp_str)


class Biography(object):
    """docstring for Biography"""

    def __init__(self, id, name, gender):
        super(Biography, self).__init__()
        self.id = id
        # self.uri = rdflib.term.URIRef(str(NS_DICT["data"]) + id)
        self.name = name
        self.uri = make_standard_uri(name)
        self.gender = gender
        self.context_list = []
        self.cf_list = []
        # Hold off on events for now
        self.event_list = []

        self.education_context_list = []
        self.occupations = []
        self.other_contexts = []
        self.organizations = []
        self.other_triples = []

    def add_context(self, context):
        if context is list:
            self.context_list += context
        else:
            self.context_list.append(context)

    def create_context(self, id, text, type="culturalformation"):
        self.context_list.append(Context(id, text, type))

    def add_organization(self, orgname):
        self.organizations += orgname

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

    def add_education_context(self, education_context):
        # self.education_context_list += [education_context]
        if education_context is list:
            self.education_context_list += education_context
        else:
            self.education_context_list.append(education_context)

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
        bind_ns(namespace_manager, NS_DICT)

        g.add((self.uri, RDF.type, NS_DICT["cwrc"].NaturalPerson))
        g.add((self.uri, NS_DICT["foaf"].name, Literal(self.name, datatype=rdflib.namespace.XSD.string)))
        g.add((self.uri, RDFS.label, Literal(self.name, datatype=rdflib.namespace.XSD.string)))
        g.add((self.uri, NS_DICT["cwrc"].hasGender, self.gender))
        g += self.create_triples(self.cf_list)
        g += self.create_triples(self.context_list)
        g += self.create_triples(self.education_context_list)

        # Organization triples
        for x in self.organizations:
            g.add((self.uri, NS_DICT["org"].memberOf, x))

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
