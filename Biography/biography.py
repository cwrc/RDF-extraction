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

        self.nationalities = []

        self.context_list = []
        self.event_list = []

        self.cf_list = []
        self.location_list = []
        self.education_list = []
        self.occupation_list = []
        self.birth_list = []

        self.occupations = []
        self.family_member_list = []
        self.friend_list = []
        self.intimate_relationship_list = []

        # Gurjap's files

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

    def add_birth(self, birth):
        if type(birth) is list:
            self.birth_list += birth
        else:
            self.birth_list.append(birth)

    def add_cultural_form(self, culturalform):
        if type(culturalform) is list:
            self.cf_list += culturalform
        else:
            self.cf_list.append(culturalform)

    def add_location(self, location):
        if type(location) is list:
            self.location_list += location
        else:
            self.location_list.append(location)

    def add_occupation(self, occupation):
        if type(occupation) is list:
            self.occupation_list += occupation
        else:
            self.occupation_list.append(occupation)

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
        g.add((self.uri, utilities.NS_DICT["foaf"].name, Literal(self.name, datatype=rdflib.namespace.XSD.string)))
        g.add((self.uri, RDFS.label, Literal(self.name, datatype=rdflib.namespace.XSD.string)))
        g.add((self.uri, utilities.NS_DICT["cwrc"].hasGender, self.gender))
        g.add((self.uri, utilities.NS_DICT["foaf"].isPrimaryTopicOf, self.url))

        g += self.create_triples(self.cf_list)
        g += self.create_triples(self.context_list)
        g += self.create_triples(self.location_list)
        g += self.create_triples(self.event_list)
        g += self.create_triples(self.education_list)
        g += self.create_triples(self.occupation_list)
        g += self.create_triples(self.birth_list)

        if self.deathObj is not None:
            g += self.deathObj.to_triples()

        g += self.create_triples(self.cohabitants_list)
        g += self.create_triples(self.family_list)
        g += self.create_triples(self.friendsAssociates_list)
        g += self.create_triples(self.intimateRelationships_list)
        g += self.create_triples(self.childless_list)
        g += self.create_triples(self.children_list)
        g += self.create_triples(self.name_list)

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
        if self.cf_list:
            string += "CulturalForms: \n"
            for x in self.cf_list:
                string += str(x) + "\n"
        if self.birth_list:
            string += "Births: \n"
            for x in self.birth_list:
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
