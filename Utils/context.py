import rdflib
from Utils.citation import Citation
from rdflib import RDF, RDFS, Literal
from Utils import utilities, organizations


MAX_WORD_COUNT = 35
logger = utilities.config_logger("context")

# TODO: Move to utilities + review and look for substring matches instead of growing list
GENERIC_NAMES = ["king","King","mother-in-law" , "Queen", "queen", "Prince","husband","wife","partner" ,"father", "daughter","essay", "son","he","she","they","her","him","them", "sisters","the",  "mother", "sibling", "brother", "sister", "friend", "his wife", "her husband","his husband", "her wife", "their husband", "their wife", "lover", "family", "influence", "Her father", "eldest sister", "father's", "future husband", "grandfather", "grandmother", "her blind husband", "her mother", "landlady", "man", "mother ", "one", "organization", "papa", "parents", "second husband", "secretary", "sister-in-law", "son-in-law", "stepfather", "stepmother", "uncle", "university", "a daughter", "a son", "another","aunt", "author", "baby", "brother's", "brother-in-law", "brothers", "cousin", "daughter-in-law", "elder half-sister", "elder sister", "ex-husband", "father-in-law", "female", "fiancé", "first husband", "first wife", "her aunt", "her father", "his father", "his", "husbands", "mayor", "merchant", "nanny", "nephew", "niece", "paternal grandmother", "patron", "playwright", "publisher", "second wife", "servants", "six-month-old son", "sons", "step-father", "step-grandfather", "step-grandmother", "stepson", "widower", "youngest brother"]

"""
Status: ~84%
TODO:
1) revise mechanism for getting closest heading
2) Fix up labelling of contexts possibly
3) replace mapping related fx with a closure
4) clean up imports
"""

def get_organizations(tag):
    """Returns all organization uris within a given tag"""
    return [organizations.get_org_uri(x) for x in tag.find_all("ORGNAME")]

def get_named_entities(tag, author=None, entity_types=None):
    """Extracts the identifying components in a given tag based on specified entity types.
    
    Args:
        tag (str): The tag to extract entities from.
        author (str, optional): The author to use for extracting people. Defaults to None.
        entity_types (list, optional): List of entity types to extract (e.g., 'people', 'places', 'titles', 'textscopes', 'organizations'). Defaults to None.
    
    Returns:
        list: A list of identified subjects based on the specified entity types.
    """
    identified_subjects = []

    # If entity_types is None, set it to extract all types
    if entity_types is None:
        entity_types = ['people', 'places', 'titles', 'textscopes', 'organizations']

    if 'people' in entity_types:
        if author:
            identified_subjects += utilities.get_other_people(tag, author)
        else:
            identified_subjects += utilities.get_people(tag)
    
    if 'places' in entity_types:
        identified_subjects += utilities.get_places(tag)
    
    if 'titles' in entity_types:
        identified_subjects += utilities.get_titles(tag)
    
    if 'textscopes' in entity_types:
        identified_subjects += utilities.get_textscopes(tag)
    
    if 'organizations' in entity_types:
        identified_subjects += get_organizations(tag)
    
    return identified_subjects

def get_heading(tag):
    # TODO: improve heading finding
    # Figure out distance between tag and the two available headings
    # to see which is closest
    heading = tag.find("HEADING")
    if not heading:
        heading = tag.findPrevious("HEADING")
    if not heading:
        heading = tag.findNext("HEADING")
    if not heading:
        logger.error("Unable to find heading for:" + str(tag))
        return None
    return utilities.remove_punctuation(utilities.strip_all_whitespace(heading.text), True)


def create_context_map():
    # TODO: add exception handling
    temp_context_map = {}
    import pandas as pd
    with open('../data/context_mapping.csv', newline='') as csvfile:
        temp_context_map = pd.read_csv(csvfile)

    # Iterate over WRITING_PROPERTIES and add specific fields to temp_context_map
    for index, row in utilities.WRITING_PROPERTIES.iterrows():
        # Extract specific fields from the row
        new_row = {
            'Orlando Tag': row['Orlando Tag'],
            'Context': row['Context Type'],
            'Event': row['Context Type'].replace('Context', 'Event'),
            'Context relationship predicate': row['Generic Property'],
            # Add more fields as needed
            'Mode': None
        }
        # temp_context_map.concat(new_row)
        # pd.concat([temp_context_map, new_row])
        temp_context_map.loc[len(temp_context_map)] = new_row
    
    return temp_context_map



def get_context_map_res(col, tag, mode=False):
    # will need to revise should contexts have the same mode attribute
    if mode:
        index = Context.MAPPING[Context.MAPPING['Mode'] == tag].index[0]
    else:
        index = Context.MAPPING[Context.MAPPING['Orlando Tag'] == tag].index[0]
    return Context.MAPPING[col][index]


def get_context_predicate(tag, mode=None):
    if mode:
        return get_context_map_res("Context relationship predicate", mode, True)
    return get_context_map_res("Context relationship predicate", tag)


def get_event_type(tag, mode=None):
    if mode:
        return get_context_map_res("Event", mode, True)
    return get_context_map_res("Event", tag)


def get_context_type(tag, mode=None):
    if mode:
        return get_context_map_res("Context", mode, True)
    return get_context_map_res("Context", tag)


class Context(object):
    """
    given the id for creating a context, the tag, context_type
    optional argument of motivation: default is describing
    if motivation is describing then
        it will also create the associated identifying contexts
    if only an identifying context is needed
    motivation="identifying" as argument is necessary
    # TODO: Create possible subclass for necessary other motivations or
    + logic depending on complexity

    TODO: Possibly move out this mapping to utilities for less coupling
    TODO: review better way to generate of ID of context
    """
    MAPPING = create_context_map() #TODO: move to utilities

    def __init__(self, id, tag, context_type="CULTURALFORMATION", motivation="describing", mode=None, subject_uri=None, target_uri=None, id_context=None, subject_name=None, other_triples=True):
        super(Context, self).__init__()
        self.citations = []
        self.events = []
        self.heading = None
        self.src = None
        self.triples = []
        self.xpath = None
        self.other_triples = other_triples
        self.id = id
        self.context_focus = subject_uri
        self.identifying_uri = id_context
        self.uri = utilities.create_uri("data", id)
        self.label = subject_name
        self.context_label = ""
        self.context_type = ""

        # allows reuse of target to reduce duplication of target/citations
        if target_uri:
            self.target_uri = target_uri
            self.new_target = False
        else:
            self.target_uri = rdflib.BNode()
            self.new_target = True

        # Creating citations from bibcit tags
        if not self.identifying_uri:
            self.identifying_uri = utilities.create_uri("data", self.id + "_identifying")
            self.xpath = utilities.get_xpath(tag)
            bibcits = tag.find_all("BIBCIT")
            self.citations = [Citation(x) for x in bibcits]

            self.heading = get_heading(tag)
            self.src = "https://orlando.cambridge.org/profiles/"
            if not self.heading:
                self.src = "http://orlando.cambridge.org"

        self.tag = tag
        self.text = tag.get_text()
        self.orlando_tagname = context_type
  
        if mode:
            self.context_type = get_context_type(context_type, mode)
            self.context_predicate = utilities.create_cwrc_uri(get_context_predicate(context_type)) 
        elif isinstance(context_type, list):
            self.context_type = [get_context_type(x) for x in context_type]
            self.context_predicate = [ utilities.create_cwrc_uri(get_context_predicate(x)) for x in context_type ]
            self.context_label = " and ".join([utilities.split_by_casing(x) for x in self.context_type])
            self.context_type = [utilities.create_cwrc_uri(x) for x in self.context_type]
            
            # self.context_predicate = utilities.create_cwrc_uri("c_hasWritingRelationTo")
        elif context_type != "FREESTANDING_EVENT":
            self.context_type = get_context_type(context_type, mode)
            self.context_predicate = utilities.create_cwrc_uri(get_context_predicate(context_type))
        else:
            self.context_type = "UnknownContext"
            self.context_predicate = None

        if self.context_label == "":
            self.context_label = utilities.split_by_casing(self.context_type)
            self.context_type = utilities.create_cwrc_uri(self.context_type)

        self.named_entities = get_named_entities(self.tag,entity_types=["people","titles","organizations"])
        self.identified_places = utilities.get_places(self.tag)

        if self.named_entities and context_type != "FREESTANDING_EVENT":
            motivation = "describing"

        self.motivation = utilities.create_uri("oa", motivation)
        self.uri = utilities.create_uri("data", id)

    def link_triples(self, comp_list):
        """ Adding to list of components to link context to triples
        """

        if type(comp_list) is list:
            self.triples += comp_list
        else:
            self.triples.append(comp_list)

    def link_event(self, event_list):
        if type(event_list) is list:
            self.events += event_list
        else:
            self.events.append(event_list)

    def get_subject(self, component, person):
        subjects = []
        temp_graph = component.to_triple(person)
        subjects += [x for x in temp_graph.objects(None, None)]

        return list(set(subjects))

    def get_subjects(self, comp_list, person):
        """
        Dependent on the other other classes functioning similarly to cf
        May have to make a variant for more complex components of biography
        """
        subjects = []
        for x in comp_list:
            subjects += self.get_subject(x, person)
        return list(set(subjects))

    def get_snippet(self):
        # removing tags that mess up the snippet
        simplified_tag = utilities.remove_unwanted_tags(self.tag)
       
        if not simplified_tag.get_text():
            logger.error(F"Empty tag encountered when creating the context: {self.id} : Within: {self.orlando_tagname} {str(self.tag)}")
            self.text = ""
        else:
            self.text = utilities.limit_to_full_sentences(str(simplified_tag.get_text()), utilities.MAX_WORD_COUNT)
        
        date = simplified_tag.find("DATE")
        
        if not date:
            date = simplified_tag.find("DATERANGE")    
        
        if not date:
            date = simplified_tag.find("DATESTRUCT")    
  
        if date:
            self.text = self.text.replace(date.text, date.text + ": ")
        
        self.text= self.text.replace("\n"," ")
        self.text= self.text.replace(".",". ")
        self.text= self.text.replace("  "," ")

        self.text=self.text.strip()

    def to_triple(self, person=None):

        g = utilities.create_graph()

        if not self.context_focus and person:
            self.context_focus = person.uri

        # Creating target first
        if self.new_target:
            if person:
                source_url = rdflib.term.URIRef(self.src + person.id + "#" + self.heading)
                target_label = person.name + " - " + self.context_label + " excerpt"
            else:
                source_url = rdflib.term.URIRef(self.src + "/events/" + self.id.split("context_")[1])
                target_label = "FE" + " - " + self.context_label + " excerpt"
            g.add((self.target_uri, RDFS.label, Literal(target_label)))
            g.add((self.target_uri, utilities.NS_DICT["oa"].hasSource, source_url))

            # Adding citations
            for x in self.citations:
                g += x.to_triple(self.target_uri, source_url)

            # Creating xpath selector
            xpath_uri = rdflib.BNode()
            xpath_label = target_label.replace(" excerpt", " XPath Selector")
            g.add((self.target_uri, utilities.NS_DICT["oa"].hasSelector, xpath_uri))
            g.add((xpath_uri, RDFS.label, Literal(xpath_label)))
            g.add((xpath_uri, RDF.type, utilities.NS_DICT["oa"].XPathSelector))
            g.add((xpath_uri, RDF.value, Literal(self.xpath)))

            # Creating text quote selector
            self.get_snippet()
            textquote_uri = rdflib.BNode()
            textquote_label = target_label.replace(" excerpt", " TextQuote Selector")
            g.add((xpath_uri, utilities.NS_DICT["oa"].refinedBy, textquote_uri))
            g.add((textquote_uri, RDF.type, utilities.NS_DICT["oa"].TextQuoteSelector))
            g.add((textquote_uri, RDFS.label, Literal(textquote_label)))
            g.add((textquote_uri, utilities.NS_DICT["oa"].exact, Literal(self.text)))

            # Creating identifying context first and always
            if self.label:
                context_label = self.label + " - " + self.context_label + " (identifying)"
            elif person:
                context_label = person.name + " - " + self.context_label + " (identifying)"
            else:
                context_label = self.context_label + " (identifying)"

            if isinstance(self.context_type, list):
                for x in self.context_type:
                    g.add((self.identifying_uri, RDF.type, x))
            else:
                g.add((self.identifying_uri, RDF.type, self.context_type))

            g.add((self.identifying_uri, RDFS.label, Literal(context_label)))
            g.add((self.identifying_uri, utilities.NS_DICT["oa"].hasTarget, self.target_uri))
            g.add((self.identifying_uri, utilities.NS_DICT["oa"].motivatedBy, utilities.NS_DICT["oa"].identifying))

            # Creating spatial context if place is mentioned
            if self.identified_places:
                self.named_entities += self.identified_places
                g.add((self.identifying_uri, RDF.type, utilities.create_cwrc_uri("SpatialContext")))

            # Adding identifying bodies to annotation
            for x in self.named_entities:
                g.add((self.identifying_uri, utilities.NS_DICT["oa"].hasBody, x))
            if person:
                g.add((self.identifying_uri, utilities.NS_DICT["oa"].hasBody, person.uri))

            # Attaching event to context
            for x in self.events:
                g.add((self.identifying_uri, utilities.NS_DICT["cwrc"].hasEvent, x.uri))

        # Creating describing context if applicable
        if self.motivation == utilities.NS_DICT["oa"].describing:
            self.uri = utilities.create_uri("data", self.id + "_describing")
            if self.label:
                context_label = self.label + " - " + self.context_label + " (identifying)"
            else:
                context_label = person.name + " - " + self.context_label + " (describing)"
            
            
            if isinstance(self.context_type, list):
                for x in self.context_type:
                    g.add((self.uri, RDF.type, x))
            else:
                g.add((self.uri, RDF.type, self.context_type))
            
            g.add((self.uri, RDFS.label, Literal(context_label)))
            g.add((self.uri, utilities.NS_DICT["cwrc"].hasIDependencyOn, self.identifying_uri))
            g.add((self.uri, utilities.NS_DICT["oa"].hasTarget, self.target_uri))
            g.add((self.uri, utilities.NS_DICT["oa"].motivatedBy, self.motivation))
            
            if type(self.context_focus) is list:
                for x in self.context_focus:
                    g.add((self.uri, utilities.NS_DICT["cwrc"].contextFocus, x))
            else:
                g.add((self.uri, utilities.NS_DICT["cwrc"].contextFocus, self.context_focus))

            # Adding extracted triples
            temp_graph = utilities.create_graph()
            for x in self.triples:
                temp_graph += x.to_triple(self)
            g += temp_graph

            # Remove person from named entities
            self.named_entities = list(filter(lambda a: a != person.uri, self.named_entities))

            # Removing named entities if appear within triples
            for x in temp_graph.objects(None, None):
                if x in self.named_entities:
                    self.named_entities.remove(x)

            # Adding any named entities with <context>Relationship predicate
            if isinstance(self.context_predicate, list):
                for x in self.context_predicate:
                    for y in self.named_entities:
                        g.add((self.uri, x, y))
            else:
                for x in self.named_entities:
                    g.add((self.uri, self.context_predicate, x))



            if self.identified_places:
                g.add((self.uri, RDF.type, utilities.create_cwrc_uri("SpatialContext")))

        for x in self.tag.find_all("TITLE"):
            uri = utilities.get_title_uri(x)
            uri = rdflib.term.URIRef(uri)
            title_type = x.get("TITLETYPE")
            g.add((uri, RDF.type, utilities.NS_DICT["bf"].Work))

            if title_type:
                g.add((uri, RDF.type, utilities.TITLE_TYPE_MAPPING[title_type]))
            

            
            std_name = utilities.get_value(x)
            g.add((uri, RDFS.label, Literal(std_name)))

        
        for x in self.tag.find_all("NAME"):
            uri = utilities.get_name_uri(x)
            secondary_uris = []
            if not uri:
                logger.warning(F"URI not found for: {x} within entry: {person.id}")
                continue
            else:
                cwrc_uri = x.get("REF")
                if not cwrc_uri:
                    if person:
                        logger.warning(F"URI not found for: {x} within entry: {person.id}")
                    else:
                        logger.warning(F"URI not found for: {x} within: {self.id}")
                else:
                    secondary_uris = utilities.get_person_secondary_uris(cwrc_uri) 
                uri = rdflib.term.URIRef(uri)
            
            g.add((uri, RDF.type,utilities.NS_DICT["cwrc"].NaturalPerson))
            std_name = utilities.get_full_name(x,self.tag)
            g.add((uri, RDFS.label, Literal(std_name,lang="en")))
            altname = x.get_text()
            if altname and std_name != altname and altname not in GENERIC_NAMES:
                g.add((uri, utilities.NS_DICT["skos"].altLabel, Literal(altname,lang="en")))
            
            for y in secondary_uris:
                if y != uri:
                    g.add((uri, utilities.NS_DICT["owl"].sameAs, y))
       
        for x in self.tag.find_all("ORGNAME"):
            uri = organizations.get_org_uri(x)
            secondary_uris = []
            if not uri:
                logger.warning(F"URI not found for: {x} within entry: {person.id}")
                continue
            else:
                cwrc_uri = x.get("REF")
                if not cwrc_uri:
                    if person:
                        logger.warning(F"URI not found for: {x} within entry: {person.id}")
                    else:
                        logger.warning(F"URI not found for: {x} within: {self.id}")
                else:
                    secondary_uris = organizations.get_secondary_uris(cwrc_uri) 
                uri = rdflib.term.URIRef(uri)
            
            g.add((uri, RDF.type,utilities.NS_DICT["org"].Organization))
            std_name = organizations.get_org_name(x)
            g.add((uri, RDFS.label, Literal(std_name,lang="en")))
            altname = x.get_text()
            if altname and std_name != altname and altname not in GENERIC_NAMES:
                g.add((uri, utilities.NS_DICT["skos"].altLabel, Literal(altname,lang="en")))
            
            for y in secondary_uris:
                if y != uri:
                    g.add((uri, utilities.NS_DICT["owl"].sameAs, y))
       


        return g

    def __str__(self):
        string = ""
        string += f"\tcontext_focus: {self.context_focus}\n"
        string += f"\tcontext_label: {self.context_label}\n"
        string += f"\tcontext_predicate: {self.context_predicate}\n"
        string += f"\tcontext_type: {self.context_type}\n"
        string += f"\tevents: {self.events}\n"
        string += f"\theading: {self.heading}\n"
        string += f"\tid: {self.id}\n"
        string += f"\tmotivation: {self.motivation}\n"
        string += f"\torlando_tagname: {self.orlando_tagname}\n"
        string += f"\tsrc: {self.src}\n"
        string += f"\ttag: {self.tag}\n"
        string += f"\ttext: {self.text}\n"
        string += f"\turi: {self.uri}\n"
        string += f"\txpath: {self.xpath}\n\n\n"
        for x in self.citations:
            string += f"\t\t• {x}\n"
        string += "\n\n"
        for x in self.named_entities:
            string += f"\t\t• {x}\n"
        string += "\n\n"
        for x in self.triples:
            string += f"\t\t• {x}\n"

        return f"{string}\n"