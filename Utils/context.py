import rdflib
from Utils.citation import Citation
from rdflib import RDF, RDFS, Literal
from Utils import utilities, organizations


logger = utilities.config_logger("context")


"""
Status: ~84%
TODO:

1) revise mechanism for getting closest heading
2) Fix up labelling of contexts possibly
3) replace mapping related fx with a closure
4) clean up imports
"""


def get_xpath(element):
    """courtesy: gist.github.com/ergoithz/6cf043e3fdedd1b94fcf
    Generate xpath from BeautifulSoup4 element
    :param element: BeautifulSoup4 element.
    :type element: bs4.element.Tag or bs4.element.NavigableString
    :return: xpath as string
    :rtype: str
    """
    components = []
    child = element if element.name else element.parent
    for parent in child.parents:
        """
        @type parent: bs4.element.Tag
        """
        siblings = parent.find_all(child.name, recursive=False)
        components.append(
            child.name
            if siblings == [child] else
            '%s[%d]' % (child.name, 1 + siblings.index(child))
        )
        child = parent
    components.reverse()
    return '/%s' % '/'.join(components)


def get_named_entities(tag):
    """ extracts the identifying components in a given tag
        to be used for the subjects of the annotation, other than places
    """
    identified_subjects = []

    identified_subjects += utilities.get_people(tag)
    identified_subjects += utilities.get_titles(tag)

    for x in tag.find_all("ORGNAME"):
        identified_subjects.append(organizations.get_org_uri(x))

    return identified_subjects


def get_heading(tag):
    # TODO: improve heading finding
    # Figure out distance between tag and the two available headings
    # to see which is closest
    # Placeholder for now
    heading = tag.find("HEADING")
    heading_text = ""
    
    if not heading:
        heading = tag.findPrevious("HEADING")
    if not heading:
        heading = tag.findNext("HEADING")
    if not heading:
        logger.error("Unable to find heading for:" + str(tag))
        return None

    if heading.parent.name == "DIV1":
        heading_text = "-chapter-"
    else:
        heading_text = "-subchapter-"
    
    heading_text += utilities.remove_punctuation(utilities.strip_all_whitespace(heading.text.lower()),True)
    
    return heading_text


def create_context_map():
    import pandas as pd
    with open('../data/context_mapping.csv', newline='') as csvfile:
        return pd.read_csv(csvfile)


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


def remove_unwanted_tags(tag):
    unwanted_tag_names = ["BIBCITS", "RESPONSIBILITIES", "KEYWORDCLASSES","RESEARCHNOTE"]
    unwanted_tags = []
    for x in unwanted_tag_names:
        unwanted_tags += tag.find_all(x)

    for x in unwanted_tags:
        x.decompose()


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
    MAPPING = create_context_map()

    def __init__(self, id, tag, context_type="CULTURALFORMATION", motivation="describing", mode=None, subject_uri=None, target_uri=None, id_context=None, subject_name=None, other_triples=True,pattern=1):
        super(Context, self).__init__()
        self.citations = []
        self.events = []
        self.activities = []
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
        self.cidoc_pattern=pattern

        # allows reuse of target to reduce duplication of target/citations
        if target_uri:
            self.target_uri = target_uri
            self.new_target = False
        else:
            self.target_uri = self.uri +"_target"
            self.new_target = True

        # Creating citations from bibcit tags
        if not self.identifying_uri:
            self.identifying_uri = utilities.create_uri("data", self.id + "_identifying")
            self.xpath = get_xpath(tag)
            bibcits = tag.find_all("BIBCIT")
            self.citations = [Citation(x) for x in bibcits]

            self.heading = get_heading(tag)
            self.src = "https://orlando.cambridge.org/profiles/"
            if not self.heading:
                self.src = "http://orlando.cambridge.org"

        self.tag = tag
        self.text = tag.get_text()
        self.orlando_tagname = context_type

        # Would be nice to use the ontology and not worry about changing labels
        # logger.info(context_type + " " + str(mode))
        if context_type != "CHRONEVENT":
            self.context_type = get_context_type(context_type, mode)
            self.context_predicate = utilities.create_cwrc_uri(get_context_predicate(context_type))
            self.context_label = utilities.split_by_casing(self.context_type)
        else:
            self.context_type = "Context"
            self.context_predicate = None
            self.context_label = " ".join(self.id.split("_")).title().replace(" Context", ":") + " Context"

        # TODO: Add this logic to the mapping file instead of hardcoding
        if context_type == "OCCUPATION":
            self.context_type = utilities.create_uri("occupation",self.context_type)
        else:
            self.context_type = utilities.create_cwrc_uri(self.context_type)

        self.named_entities = get_named_entities(self.tag)

        self.motivation = utilities.create_uri("oa", motivation)


    def link_triples(self, components):
        """ Adding to list of components to link context to triples
        """

        if type(components) is list:
            self.triples += components
        else:
            self.triples.append(components)

    def link_activity(self, activities):
        if type(activities) is list:
            self.activities += activities
        else:
            self.activities.append(activities)

    def link_event(self, events):
        if type(events) is list:
            self.events += events
        else:
            self.events.append(events)

    def get_subject(self, component, person):
        subjects = []
        temp_graph = component.to_triple(person)
        subjects += [x for x in temp_graph.objects(None, None)]

        return list(set(subjects))

    def get_subjects(self, components, person):
        """
        Dependent on the other other classes functioning similarly to cf
        May have to make a variant for more complex components of biography
        """
        subjects = []
        for x in components:
            subjects += self.get_subject(x, person)
        return list(set(subjects))

    def get_snippet(self):
        # removing tags that mess up the snippet
        remove_unwanted_tags(self.tag)
        if not self.tag.get_text():
            logger.error("Empty tag encountered when creating the context:  " + self.id +
                         ": Within:  " + self.orlando_tagname + " " + str(self.tag))
            self.text = ""
        else:
            self.text = utilities.limit_to_full_sentences(str(self.tag.get_text()), utilities.MAX_WORD_COUNT)
        
        date = self.tag.find("DATE")
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

        if not self.context_focus:
            self.context_focus = None


        # Creating target first - CIDOCified
        if self.new_target:
            target_label = None
            source_url = None

            if person:
                src_uri = f"{self.src}{person.id}#{person.id}{self.heading}"
                source_url = rdflib.term.URIRef(src_uri)
                target_label = person.name + ": " + self.context_label + " Excerpt"

            else:
                source_url = rdflib.term.URIRef(
                    self.src + "#FE" + self.id.split("_")[-1])
                target_label = self.context_label + " Excerpt"
        
            source_url = rdflib.term.URIRef(source_url)

            g.add((self.target_uri, RDF.type,utilities.NS_DICT["oa"].SpecificResource))
            g.add((self.target_uri, RDF.type,
                   utilities.NS_DICT["crm"].E73_Information_Object))
            g.add((self.target_uri, RDFS.label, Literal(target_label, lang="en")))
            g.add((self.target_uri, utilities.NS_DICT["oa"].hasSource, source_url))

            # Adding citations
            for x in self.citations:
                g += x.to_triple(self.target_uri, source_url)

            # Creating xpath selector
            xpath_uri = self.uri +"_xpath_selector"
            xpath_label = target_label.replace(" Excerpt", " XPath Selector")
            g.add((self.target_uri, utilities.NS_DICT["oa"].hasSelector, xpath_uri))
            g.add((xpath_uri, RDFS.label, Literal(xpath_label, lang="en")))
            g.add((xpath_uri, RDF.type, utilities.NS_DICT["oa"].XPathSelector))
            g.add((xpath_uri, RDF.type,
                   utilities.NS_DICT["crm"].E73_Information_Object))
            g.add((xpath_uri, RDF.value, Literal(self.xpath)))

            # Creating text quote selector
            self.get_snippet()
            textquote_uri = self.uri +"_textquote_selector"
            textquote_label = target_label.replace(" Excerpt", " TextQuote Selector")
            g.add((xpath_uri, utilities.NS_DICT["oa"].refinedBy, textquote_uri))
            g.add((textquote_uri, RDF.type, utilities.NS_DICT["oa"].TextQuoteSelector))
            g.add((textquote_uri, RDF.type,
                   utilities.NS_DICT["crm"].E33_Linguistic_Object))
            g.add((textquote_uri, RDFS.label, Literal(textquote_label, lang="en")))
            g.add((textquote_uri, utilities.NS_DICT["oa"].exact, Literal(
                self.text, lang="en")))

        # Creating identifying context first and always
        if person:
            context_label = person.name + ": " + self.context_label + " (identifying)"
        else:
            context_label = self.context_label + " (identifying)"

        identifying_uri = utilities.create_uri("data", self.id + "_identifying")
        g.add((identifying_uri, RDF.type, utilities.NS_DICT["crm"].E33_Linguistic_Object))
        g.add((identifying_uri, RDF.type, utilities.NS_DICT["oa"].Annotation))
        g.add((identifying_uri, utilities.NS_DICT["crm"].P2_has_type, self.context_type))
        g.add((identifying_uri, RDFS.label, Literal(context_label, lang="en")))
        
        g.add((identifying_uri, utilities.NS_DICT["oa"].hasTarget, self.target_uri))
        
        if self.context_focus:
            g.add((identifying_uri, utilities.NS_DICT["crm"].P67_refers_to, self.context_focus))
        
        # Creating spatial context if place is mentioned
        identified_places = utilities.get_places(self.tag)
        if identified_places:
            self.named_entities += identified_places
            g.add((identifying_uri, utilities.NS_DICT["crm"].P2_has_type, utilities.create_cwrc_uri("SpatialContext")))

        # Adding identifying bodies to annotation
        for x in self.named_entities:
            g.add((identifying_uri, utilities.NS_DICT["oa"].hasBody, x))
        
        if not person:
            for x in self.tag.find_all("NAME"):
                entity_uri = utilities.get_name_uri(x)
                g.add((entity_uri,RDFS.label,Literal(utilities.get_value(x))))
                g.add((entity_uri,RDF.type,utilities.NS_DICT["crm"].E21_Person))
            for x in self.tag.find_all("ORG"):
                entity_uri = utilities.get_name_uri(x)
                g.add((entity_uri,RDFS.label,Literal(utilities.get_value(x))))
                g.add((entity_uri,RDF.type,utilities.NS_DICT["crm"].E74_Group))


        if person:
            g.add((identifying_uri, utilities.NS_DICT["oa"].hasBody, person.uri))



        if self.cidoc_pattern not in ["birth","death","occupation", "location", "culturalform","relationships"]:
        # Creating describing context if applicable
            if self.motivation == utilities.NS_DICT["oa"].describing:
                self.uri = utilities.create_uri("data", self.id + "_attributing")
                context_label = person.name + ": " + self.context_label + " (attributing)"
                g.add((self.uri, RDF.type, self.context_type))
                g.add((self.uri, RDFS.label, Literal(context_label, lang="en")))
                g.add((self.uri, utilities.NS_DICT["cwrc"].hasIDependencyOn, identifying_uri))
                g.add((self.uri, utilities.NS_DICT["oa"].hasTarget, self.target_uri))
                g.add((self.uri, utilities.NS_DICT["oa"].motivatedBy, self.motivation))
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
                for x in self.named_entities:
                    g.add((self.uri, self.context_predicate, x))

                if identified_places:
                    g.add((self.uri, RDF.type, utilities.create_cwrc_uri("SpatialContext")))
        else:
                temp_graph = utilities.create_graph()
                for x in self.triples:
                    temp_graph += x.to_triple(self)
                g += temp_graph

        for x in self.activities:
            g.add((identifying_uri,utilities.NS_DICT["crm"].P129_is_about, x.uri))
            g.add((x.uri,utilities.NS_DICT["crm"].P129i_is_subject_of, identifying_uri))

            if x.connection_uri:
                g.add((x.connection_uri,utilities.NS_DICT["crm"].P129i_is_subject_of, identifying_uri))

        return g

    def __str__(self):
        string = ""
        string += "\tcontext_focus: " + str(self.context_focus) + "\n"
        string += "\tcontext_label: " + str(self.context_label) + "\n"
        string += "\tcontext_predicate: " + str(self.context_predicate) + "\n"
        string += "\tcontext_type: " + str(self.context_type) + "\n"
        string += "\tevents: " + str(self.events) + "\n"
        string += "\theading: " + str(self.heading) + "\n"
        string += "\tid: " + str(self.id) + "\n"
        string += "\tmotivation: " + str(self.motivation) + "\n"
        string += "\torlando_tagname: " + str(self.orlando_tagname) + "\n"
        string += "\tsrc: " + str(self.src) + "\n"
        string += "\ttag: " + str(self.tag) + "\n"
        string += "\ttext: " + str(self.text) + "\n"
        string += "\turi: " + str(self.uri) + "\n"
        string += "\txpath: " + str(self.xpath) + "\n"
        string += "\n\n"
        for x in self.citations:
            string += "\t\t" + str(x) + "\n"
        string += "\n\n"
        for x in self.named_entities:
            string += "\t\t" + str(x) + "\n"
        string += "\n\n"
        for x in self.triples:
            string += "\t\t" + str(x) + "\n"

        return string + "\n"
