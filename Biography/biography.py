import rdflib
from rdflib import RDF, RDFS, Literal
from Utils import utilities

logger = utilities.config_logger("biography")

# TODO: Move this to utilities?
WIKIDATA_MAP = {}

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
    # possible_phrases = ["biographer ", "biographer, "]
    # historian?
    # This might erronously identify someone as a biographer who a writer shares a relationship with
    # ex. X married biographer Y
    names = doc.find_all("NAME")
    biographers = []
    for x in names:
        parent_text = x.parent.get_text()      
        if "biographer " + x.get_text().lower() in parent_text.lower():
            biographers.append(x)
        elif "critic " + x.get_text().lower() in parent_text.lower():
            biographers.append(x)
        elif "historian " + x.get_text().lower() in parent_text.lower():
            biographers.append(x)
    return list(set(biographers))



def get_parent_context(tag,):
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
        self.url = "http://orlando.cambridge.org/protected/svPeople?formname=r&people_tab=3&person_id=" + id
        self.url = rdflib.term.URIRef(self.url)
        self.name = utilities.get_readable_name(doc)
        self.std_name = utilities.get_name(doc)
        self.uri =  self.document.ENTRY.DIV0.STANDARD.get("REF")
        self.uri = rdflib.term.URIRef(self.uri)

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

        self.family_members = {}
        self.get_all_members()

        self.wd_id = get_wd_identifier(id)
        
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
        g.add((self.uri, RDFS.label, Literal(self.std_name)))
        g.add((self.uri, utilities.NS_DICT["skos"].altLabel, Literal(self.name)))

        g.add((self.uri, utilities.NS_DICT["foaf"].isPrimaryTopicOf, self.url))

        g += self.create_triples(self.context_list)
        g += self.create_triples(self.event_list)

        if self.wd_id:
            g.add((self.uri, utilities.NS_DICT["owl"].sameAs, rdflib.term.URIRef(self.wd_id)))

        return g

    def to_file(self, graph=None, serialization="ttl"):
        if graph:
            return graph.serialize(format=serialization)
        else:
            return self.to_graph().serialize(format=serialization)

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
