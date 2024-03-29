from time import clock_getres
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
        self.old_url = rdflib.term.URIRef(F"http://orlando.cambridge.org/protected/svPeople?formname=r&people_tab=3&person_id={id}")
        self.url = rdflib.term.URIRef(F"https://orlando.cambridge.org/profiles/{id}")
        self.name = utilities.get_readable_name(doc)
        self.std_name = utilities.get_name(doc)
        self.cwrc_uri = self.document.ENTRY.DIV0.STANDARD.get("REF")

        if self.cwrc_uri in utilities.PERSON_MAP:
            self.uri = utilities.PERSON_MAP[self.cwrc_uri]
        else:
            self.uri = self.cwrc_uri

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

        self.parents = []
        self.possible_family_members = {}
        self.get_all_members()
        self.family_members = {}
        self.get_family_members()

        self.wd_id = get_wd_identifier(id)
        self.context_list = []
        self.event_list = []
        self.activity_list = []
        self.organizations = []
        self.name_list = []

    def get_family_members(self):
        # Assuming mother and father are the first names mentioned in context
        if "MOTHER" in self.possible_family_members and len(self.possible_family_members["MOTHER"]) > 0:
            self.family_members["MOTHER"] = self.possible_family_members["MOTHER"][0]
            self.parents.append(self.family_members["MOTHER"])
        if "FATHER" in self.possible_family_members and len(self.possible_family_members["FATHER"]) > 0:
            self.family_members["FATHER"] = self.possible_family_members["FATHER"][0]
            self.parents.append(self.family_members["FATHER"])

        ignore_members = [self.family_members.get(
            "MOTHER"), self.family_members.get("FATHER")]
        
        # Copying rest of possible family members in family members
        for relation, members in self.possible_family_members.items():
            if relation not in ["MOTHER", "FATHER"]:
                # Removing mother/father URIs from other members
                members = [x for x in members if x not in ignore_members ]
                self.family_members[relation] = members
        
                
    def get_all_members(self):
        member_tags = self.document.find_all("MEMBER")
        for x in member_tags:
            peeps = utilities.get_other_people(x,self, unique=False)
            peeps = [y for y in peeps if y not in self.biographers]
            
            if x["RELATION"] in self.possible_family_members:
                self.possible_family_members[x["RELATION"]]+=peeps
            else:
                self.possible_family_members[x["RELATION"]] = peeps
        
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

    def add_activity(self, activity):
        if type(activity) is list:
            self.activity_list += activity
        else:
            self.activity_list.append(activity)

    def add_organization(self, organization):
        if type(organization) is list:
            self.organizations += organization
        else:
            self.organizations.append(organization)

    def create_triples(self, e_list):
        g = rdflib.Graph()
        for x in e_list:
            g += x.to_triple(self)
        return g

    def to_graph(self):
        g = utilities.create_graph()

        g.add((self.uri, RDF.type, utilities.NS_DICT["crm"].E21_Person))
        g.add(
            (self.uri, utilities.NS_DICT["crm"].P129i_is_subject_of, self.url))
        

        g += self.create_triples(self.context_list)
        g += self.create_triples(self.event_list)
        g += self.create_triples(self.activity_list)

        for x in self.organizations:
            g.add((x, utilities.NS_DICT["crm"].P107_has_current_or_former_member, self.uri))
            g.add((self.uri, utilities.NS_DICT["crm"].P107i_is_current_or_former_member_of,x ))

        if self.wd_id and self.wd_id != str(self.uri):
            g.add((self.uri, utilities.NS_DICT["owl"].sameAs, rdflib.term.URIRef(self.wd_id)))

        g.add((self.uri, RDFS.label, Literal(self.std_name)))
        g.add((self.uri, utilities.NS_DICT["skos"].prefLabel, Literal(self.name)))

 
        if str(self.uri) !=  self.cwrc_uri:
            g.add((self.uri, utilities.NS_DICT["owl"].sameAs, rdflib.term.URIRef(self.cwrc_uri)))
            
 

        return g

    def to_file(self, graph=None, serialization="ttl"):
        if graph:
            return graph.serialize(format=serialization)#.decode()
        else:
            return self.to_graph().serialize(format=serialization)#.decode()

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
