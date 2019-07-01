import rdflib
from rdflib import RDF, RDFS, Literal
from Utils import utilities


class Biography(object):
    """docstring for Biography"""

    def __init__(self, id, doc, gender):
        super(Biography, self).__init__()
        self.id = id
        self.url = "http://orlando.cambridge.org/protected/svPeople?formname=r&people_tab=3&person_id=" + id
        self.url = rdflib.term.URIRef(self.url)
        self.name = utilities.get_readable_name(doc)
        self.gender = gender
        self.uri = utilities.make_standard_uri(utilities.get_name(doc))

        # TODO: get nickname from file most common acroynm and replace in event/context strings
        self.nickname = None

        # TODO: Read wikidata identifiers from csv
        self.wd_id = None
        # self.wd_id = utilities.get_wd_identifier(id)

        self.nationalities = []

        self.context_list = []
        self.event_list = []

        self.education_list = []

        # Gurjap's files
        self.occupations = []
        self.family_member_list = []
        self.friend_list = []
        self.intimate_relationship_list = []

        self.contextCounts = {
            "intimateRelationship": 1,
            "friendsAssociates": 1
        }
        self.deathObj = None
        self.cohabitants_list = []
        self.family_list = []
        self.friendsAssociates_list = []
        self.intimateRelationships_list = []
        self.childless_list = []

        self.children_list = []
        self.name_list = []

    def add_context(self, context):
        if type(context) is list:
            self.context_list += context
        else:
            self.context_list.append(context)

    def add_education(self, education):
        if type(education) is list:
            self.education_list += education
        else:
            self.education_list.append(education)

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

    def create_triples2(self, e_list, f_list):
        g = rdflib.Graph()
        for x in e_list:
            g += x.to_triple(self)
        return g

    def to_graph(self):
        g = utilities.create_graph()

        g.add((self.uri, RDF.type, utilities.NS_DICT["cwrc"].NaturalPerson))
        g.add((self.uri, RDFS.label, Literal(self.name, datatype=rdflib.namespace.XSD.string)))
        g.add((self.uri, utilities.NS_DICT["cwrc"].hasGender, self.gender))
        g.add((self.uri, utilities.NS_DICT["foaf"].isPrimaryTopicOf, self.url))

        g += self.create_triples(self.context_list)
        g += self.create_triples(self.event_list)
        g += self.create_triples(self.education_list)

        if self.deathObj is not None:
            g += self.deathObj.to_triples()

        g += self.create_triples(self.cohabitants_list)
        g += self.create_triples(self.family_list)
        g += self.create_triples(self.friendsAssociates_list)
        g += self.create_triples(self.intimateRelationships_list)
        g += self.create_triples(self.childless_list)
        g += self.create_triples(self.children_list)
        g += self.create_triples(self.name_list)

        if self.wd_id:
            g.add((self.uri, utilities.NS_DICT["owl"].sameAs, self.wd_id))

        return g

    def to_file(self, graph=None, serialization="ttl"):
        if graph:
            return graph.serialize(format=serialization).decode()
        else:
            return self.to_graph().serialize(format=serialization).decode()

    def __str__(self):
        # TODO: add occupation + education
        string = "id: " + str(self.id) + "\n"
        string += "name: " + str(self.name) + "\n"
        string += "gender: " + str(self.gender) + "\n"
        if self.context_list:
            string += "Contexts: \n"
            for x in self.context_list:
                string += str(x) + "\n"
        if self.location_list:
            string += "Locations: \n"
            for x in self.location_list:
                string += str(x) + "\n"
        if self.event_list:
            string += "Events: \n"
            for x in self.event_list:
                string += str(x) + "\n"

        return string
