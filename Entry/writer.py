import rdflib
from rdflib import RDF, RDFS, Literal
from Utils import utilities


logger = utilities.config_logger("writer")


class Writer(object):
    """docstring for Writer"""

    def __init__(self, id, doc):
        super(Writer, self).__init__()
        self.id = id
        self.url = "http://orlando.cambridge.org/protected/svPeople?formname=r&people_tab=3&person_id=" + id
        self.url = rdflib.term.URIRef(self.url)
        self.name = utilities.get_readable_name(doc)
        self.std_name = utilities.get_name(doc)
        self.uri = utilities.make_standard_uri(self.std_name)
        self.document = doc
        # TODO: get nickname from file most common acroynm and replace in event/context strings
        self.nickname = None
        self.oeuvre_uri = rdflib.term.URIRef(self.uri + "_Oeuvre")

        self.context_list = []
        self.event_list = []

    def add_context(self, context):
        if type(context) is list:
            self.context_list += context
        else:
            self.context_list.append(context)

    def add_event(self, event):
        if type(event) is list:
            self.event_list += event
        else:
            self.event_list.append(event)

    def create_triples(self, e_list):
        g = rdflib.Graph()
        for x in e_list:
            g += x.to_triple(self)
        return g

    def to_graph(self):
        g = utilities.create_graph()

        g.add((self.uri, RDF.type, utilities.NS_DICT["cwrc"].NaturalPerson))
        g.add((self.uri, utilities.NS_DICT["foaf"].isPrimaryTopicOf, self.url))

        g += self.create_triples(self.context_list)
        g += self.create_triples(self.event_list)

        g.add((self.uri, RDFS.label, Literal(self.std_name)))
        g.add((self.uri, utilities.NS_DICT["skos"].altLabel, Literal(self.name)))

        # Adding ouevre
        g.add((self.oeuvre_uri, RDF.type, utilities.NS_DICT["cwrc"].Oeuvre))
        g.add((self.uri, utilities.NS_DICT["bf"].author, self.oeuvre_uri))
        label = self.uri.split("/")[-1].split("_")[0] + "'s"
        g.add((self.oeuvre_uri, RDFS.label, Literal(label + " Oeuvre")))

        return g

    def to_file(self, graph=None, serialization="ttl"):
        if graph:
            return graph.serialize(format=serialization).decode()
        else:
            return self.to_graph().serialize(format=serialization).decode()

    def __str__(self):
        string = "id: " + str(self.id) + "\n"
        string += "name: " + str(self.name) + "\n"
        string += "uri: " + str(self.uri)
        string += "url: " + str(self.url)
        string += "nickname: " + str(self.nickname)
        string += "oeuvre uri: " + str(self.oeuvre_uri)
        string += "std name: " + str(self.std_name)

        if self.context_list:
            string += "Contexts: \n"
            for x in self.context_list:
                string += str(x) + "\n"
        if self.event_list:
            string += "Events: \n"
            for x in self.event_list:
                string += str(x) + "\n"

        return string
