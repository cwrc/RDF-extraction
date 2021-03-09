import rdflib
from rdflib import RDF, RDFS, Literal
from Utils import utilities


logger = utilities.config_logger("biography")

# TODO: Move this to utilities?
WIKIDATA_MAP = {}
# Also identify biographers

def create_wikidata_map(path=None):
    import csv
    # if searching takes too long
    # Create better searching mechanism
    if not path:
        path = '../data/wikidata_ids.csv'
    with open(path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        for row in reader:
            if row[0] not in WIKIDATA_MAP:
                WIKIDATA_MAP[row[0]] = row[1]


create_wikidata_map()


def get_wd_identifier(id):
    if id not in WIKIDATA_MAP:
        logger.warning("Unable to find wikidata identifier for " + id)
        return None
    elif WIKIDATA_MAP[id] == "None":
        return None
    else:
        return WIKIDATA_MAP[id]


class Biography(object):
    """docstring for Biography"""

    def __init__(self, id, doc):
        super(Biography, self).__init__()
        self.id = id
        self.url = "http://orlando.cambridge.org/protected/svPeople?formname=r&people_tab=3&person_id=" + id
        self.url = rdflib.term.URIRef(self.url)
        self.name = utilities.get_readable_name(doc)
        self.std_name = utilities.get_name(doc)
        self.uri = utilities.make_standard_uri(self.std_name)
        self.document = doc
        
        # TODO: get nickname from file most common acroynm and replace in event/context strings
        self.nickname = None

        self.family_members = {}
        self.wd_id = get_wd_identifier(id)
        self.nationalities = []

        self.context_list = []
        self.event_list = []

        # Gurjap's files
        self.occupations = []
        self.family_member_list = []
        self.friend_list = []
        self.intimate_relationship_list = []
        self.contextCounts = {
            "intimateRelationship": 1,
            "friendsAssociates": 1
        }
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
        g.add((self.uri, utilities.NS_DICT["foaf"].isPrimaryTopicOf, self.url))
        # g.add((self.uri, utilities.NS_DICT["cwrc"].hasGender, person.gender))

        g += self.create_triples(self.context_list)
        g += self.create_triples(self.event_list)

        # g += self.create_triples(self.cohabitants_list)
        # g += self.create_triples(self.family_list)
        # g += self.create_triples(self.friendsAssociates_list)
        # g += self.create_triples(self.intimateRelationships_list)
        # g += self.create_triples(self.childless_list)
        # g += self.create_triples(self.children_list)
        # g += self.create_triples(self.name_list)

        if self.wd_id:
            g.add((self.uri, utilities.NS_DICT["owl"].sameAs, rdflib.term.URIRef(self.wd_id)))

        # g.add((self.uri, RDFS.label, Literal(self.name)))
        # g.remove((self.uri, RDFS.label, Literal(self.std_name)))
        g.add((self.uri, RDFS.label, Literal(self.std_name)))
        g.add((self.uri, utilities.NS_DICT["skos"].altLabel, Literal(self.name)))

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
        string += "std_name:" + str(self.std_name) + "\n"
        string += "url:" + str(self.url) + "\n"
        string += "uri:" + str(self.uri) + "\n"
        string += "wd_id:" + str(self.wd_id) + "\n"
        if self.context_list:
            string += "Contexts: \n"
            for x in self.context_list:
                string += str(x) + "\n"
        if self.event_list:
            string += "Events: \n"
            for x in self.event_list:
                string += str(x) + "\n"
        if self.family_members:
            string += "family: \n"
            for x in self.family_members:
                string += str(x) + "\n"
        
        return string
