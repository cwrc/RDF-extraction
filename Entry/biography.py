import rdflib
from rdflib import RDF, RDFS, Literal
from Utils import utilities

logger = utilities.config_logger("biography")

# TODO: Move this to utilities?
WIKIDATA_MAP = {}
ROLE_KEYWORDS = ["biographer","critic", "historian"]

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

def get_possible_biographers(doc):
    # TODO: Review possible additional phrases/sentence structure to id biographers/cr
    # This might erroneously identify someone as a biographer who a writer shares a relationship with
    # ex. X married biographer Y
    names = doc.find_all("NAME")
    biographers = []
    for x in names:
        parent_text = x.parent.get_text().lower()     
        role_text = [f"{role} {x.get_text().lower()}" for role in ROLE_KEYWORDS]

        if any(role in parent_text for role in role_text):
            biographers.append(x)
            
    return list(set(biographers))



def get_parent_context(tag):
    # Might be easier with recursion
    tags = ["HEALTH", "WEALTH", "VIOLENCE", "LEISUREANDSOCIETY", "FRIENDSASSOCIATES", "PERSONNAME", "FAMILY", "INTIMATERELATIONSHIPS", "CULTURALFORMATION",
            "LOCATION", "POLITICS", "OCCUPATION", "OTHERLIFEEVENT", "DEATH", "BIRTH", "EDUCATION"]
    
    for parent in tag.parents:
        if parent.name == "MEMBER":
            if "RELATION" in parent.attrs:
                return parent["RELATION"]

        if parent.name in tags:
            return parent.name

    return None

def get_name_context(doc):
    uri_map = {}
    for x in doc.find_all("NAME"):
        uri = utilities.get_name_uri(x)
        if uri in uri_map:
            uri_map[uri].append(get_parent_context(x))
        else:
            uri_map[uri] = [get_parent_context(x)]
    
    return uri_map
    

class Biography(object):
    """docstring for Biography"""

    def __init__(self, id, doc):
        super(Biography, self).__init__()
        self.id = id
        self.document = doc
        self.old_url = rdflib.term.URIRef("http://orlando.cambridge.org/protected/svPeople?formname=r&people_tab=3&person_id=" + id)
        self.url = rdflib.term.URIRef(F"https://orlando.cambridge.org/profiles/{id}")
        self.name = utilities.get_readable_name(doc)
        self.std_name = utilities.get_name(doc)
        self.uri =  rdflib.term.URIRef(self.document.ENTRY.DIV0.STANDARD.get("REF"))
        self.oeuvre_uri = rdflib.term.URIRef(F"{self.uri}_Oeuvre")
        self.wd_id = get_wd_identifier(id)

        logger.info(F"{self.id}|{self.uri}|{self.std_name}")
        
        # TODO: Review names and people extraction for more precision
        self.biographers = [
            utilities.get_name_uri(x) for x in get_possible_biographers(self.document)]
        self.names_mentioned = utilities.get_people(self.document)
        # uris:Orlando tag
        self.people_contexts = get_name_context(doc)
        
        # uri:role
        self.people_map = {}
        self.people_map[self.uri] = "self"
        for x in self.names_mentioned:
            self.people_map[x] = []
        for x in self.biographers:
            self.people_map[x].append("biographer")

        # TODO: get nickname from file most common acroynm and replace in event/context strings
        self.nickname = None

        self.people_mentioned= utilities.get_people_names(self.document)
        self.family_members = {}
        self.get_all_members()
        
        self.context_list = []
        self.event_list = []



    def get_all_members(self):
        member_tags = self.document.find_all("MEMBER")
        for x in member_tags:
            peeps = utilities.get_other_people(x,self)
            peeps = [y for y in peeps if y not in self.biographers]
            
            if x["RELATION"] in self.family_members:
                self.family_members[x["RELATION"]]+=peeps
            else:
                self.family_members[x["RELATION"]] = peeps

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
        g.add((self.uri, RDFS.label, Literal(self.std_name)))
        g.add((self.uri, utilities.NS_DICT["skos"].altLabel, Literal(self.name)))
        g.add((self.uri, utilities.NS_DICT["foaf"].isPrimaryTopicOf, self.url))

        g += self.create_triples(self.context_list)
        g += self.create_triples(self.event_list)

        if self.wd_id:
            g.add((self.uri, utilities.NS_DICT["owl"].sameAs, rdflib.term.URIRef(self.wd_id)))

        # Adding Ouevre
        g.add((self.oeuvre_uri, RDF.type, utilities.NS_DICT["cwrc"].Oeuvre))
        g.add((self.uri, utilities.NS_DICT["bf"].author, self.oeuvre_uri))
        label = self.std_name.split(", ")[0] + "'s"
        g.add((self.oeuvre_uri, RDFS.label, Literal(label + " Oeuvre")))

        return g

    def to_file(self, graph=None, serialization="ttl"):
        if graph:
            return graph.serialize(format=serialization)
        else:
            return self.to_graph().serialize(format=serialization)

    def __str__(self):
        string = f"id: {self.id}\n"
        string += f"name: {self.name}\n"
        if self.context_list:
            string += "Contexts: \n"
            for x in self.context_list:
                string += f"{x}\n"
        if self.event_list:
            string += "Events: \n"
            for x in self.event_list:
                string += f"{x}\n"

        return string
