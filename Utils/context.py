import rdflib
from rdflib import RDF, RDFS, Literal

from Utils import utilities, organizations

MAX_WORD_COUNT = 35

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
    if not heading:
        heading = tag.findPrevious("HEADING")
    if not heading:
        heading = tag.findNext("HEADING")
    if not heading:
        logger.error("Unable to find heading for:" + str(tag))
        return None
    return utilities.remove_punctuation(utilities.strip_all_whitespace(heading.text), True)


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
    unwanted_tag_names = ["BIBCITS", "RESPONSIBILITIES", "KEYWORDCLASSES"]
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

    def __init__(self, id, tag, context_type="CULTURALFORMATION", motivation="describing", mode=None):
        super(Context, self).__init__()
        self.id = id
        self.triples = []
        self.event = None
        self.xpath = get_xpath(tag)

        remove_unwanted_tags(tag)
        self.tag = tag

        self.heading = get_heading(tag)
        self.src = "http://orlando.cambridge.org/protected/svPeople?formname=r&people_tab=3&person_id="
        if not self.heading:
            self.src = "http://orlando.cambridge.org"

        # Making the text the max amount of words
        if not tag.get_text():
            logger.error("Empty tag encountered when creating the context:  " + id + ": " + str(tag))
            self.text = ""
        else:
            self.text = utilities.limit_to_full_sentences(str(tag.get_text()), MAX_WORD_COUNT)

        # Would be nice to use the ontology and not worry about changing labels
        logger.info(context_type + " " + str(mode))
        self.context_type = get_context_type(context_type, mode)
        self.context_label = utilities.split_by_casing(self.context_type)
        self.context_type = utilities.create_cwrc_uri(self.context_type)

        self.named_entities = get_named_entities(self.tag)
        self.context_predicate = utilities.create_cwrc_uri(get_context_predicate(context_type))

        if self.named_entities:
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

    def link_event(self, event):
        self.event = event.uri

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

    def to_triple(self, person=None):
        # if tag is a describing None create the identifying triples
        g = utilities.create_graph()

        # Creating target first
        target_uri = rdflib.BNode()
        if person:
            source_url = rdflib.term.URIRef(self.src + person.id + "#" + self.heading)
            target_label = person.name + " - " + self.context_label + " target"
        else:
            source_url = rdflib.term.URIRef(self.src + "#FE")
            target_label = "FE" + " - " + self.context_label + " target"

        g.add((target_uri, RDFS.label, rdflib.term.Literal(target_label)))
        g.add((target_uri, utilities.NS_DICT["oa"].hasSource, source_url))

        # Creating xpath selector
        xpath_uri = rdflib.BNode()
        xpath_label = target_label.replace(" target", " XPath Selector")
        g.add((target_uri, utilities.NS_DICT["oa"].hasSelector, xpath_uri))
        g.add((xpath_uri, RDFS.label, rdflib.term.Literal(xpath_label)))
        g.add((xpath_uri, RDF.type, utilities.NS_DICT["oa"].XPathSelector))
        g.add((xpath_uri, RDF.value, rdflib.term.Literal(self.xpath)))

        # Creating text quote selector
        textquote_uri = rdflib.BNode()
        textquote_label = target_label.replace(" target", " TextQuote Selector")
        g.add((xpath_uri, utilities.NS_DICT["oa"].refinedBy, textquote_uri))
        g.add((textquote_uri, RDF.type, utilities.NS_DICT["oa"].TextQuoteSelector))
        g.add((textquote_uri, RDFS.label, rdflib.term.Literal(textquote_label)))
        g.add((textquote_uri, utilities.NS_DICT["oa"].exact, rdflib.term.Literal(self.text)))

        # Creating identifying context first and always
        if person:
            context_label = person.name + " - " + self.context_label + " (identifying)"
        else:
            context_label = self.context_label + " (identifying)"

        identifying_uri = utilities.create_uri("data", self.id + "_identifying")
        g.add((identifying_uri, RDF.type, self.context_type))
        g.add((identifying_uri, RDFS.label, rdflib.term.Literal(context_label)))
        g.add((identifying_uri, utilities.NS_DICT["oa"].hasTarget, target_uri))
        g.add((identifying_uri, utilities.NS_DICT["oa"].motivatedBy, utilities.NS_DICT["oa"].identifying))

        identified_places = utilities.get_places(self.tag)
        if identified_places:
            self.named_entities += identified_places
            g.add((identifying_uri, RDF.type, utilities.create_cwrc_uri("SpatialContext")))

        for x in self.named_entities:
            g.add((identifying_uri, utilities.NS_DICT["oa"].hasBody, x))

        if person:
            g.add((identifying_uri, utilities.NS_DICT["oa"].hasBody, person.uri))

        if self.event:
            g.add((identifying_uri, utilities.NS_DICT["cwrc"].hasEvent, self.event))

        # Creating describing context if applicable
        if self.motivation == utilities.NS_DICT["oa"].describing:
            self.uri = utilities.create_uri("data", self.id + "_describing")
            context_label = person.name + " - " + self.context_label + " (describing)"
            g.add((self.uri, RDF.type, self.context_type))
            g.add((self.uri, RDFS.label, rdflib.term.Literal(context_label)))
            g.add((self.uri, utilities.NS_DICT["cwrc"].hasIDependencyOn, identifying_uri))
            g.add((self.uri, utilities.NS_DICT["cwrc"].contextFocus, person.uri))
            g.add((self.uri, utilities.NS_DICT["oa"].hasTarget, target_uri))
            g.add((self.uri, utilities.NS_DICT["oa"].motivatedBy, self.motivation))

            if self.event:
                g.add((self.uri, utilities.NS_DICT["cwrc"].hasEvent, self.event))

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

        # Creating the mentioned people as natural person
        for x in self.tag.find_all("NAME"):
            uri = utilities.make_standard_uri(x.get("STANDARD"))
            g.add((uri, RDF.type, utilities.NS_DICT["cwrc"].NaturalPerson))
            g.add((uri, RDFS.label, Literal(x.get("STANDARD"), datatype=rdflib.namespace.XSD.string)))

        return g

# TODO: Remove these functions
    def create_multiple_triples(self, graph):
        """handles multitple triples
        """
        temp_g = utilities.create_graph()
        g = rdflib.Graph()
        for x in graph[:]:
            temp_g.add(x)
            triple_str = temp_g.serialize(format="ttl").decode().splitlines()[-2]
            temp_g.remove(x)
            g += self.create_ttl_body(triple_str)

        return g

    def create_ttl_body(self, triple_str):
        g = rdflib.Graph()
        format_str = rdflib.term.Literal("text/turtle", datatype=rdflib.namespace.XSD.string)
        format_uri = utilities.create_uri("dcterms", "format")
        triple_str = rdflib.term.Literal(triple_str, datatype=rdflib.namespace.XSD.string)
        temp_body = rdflib.BNode()
        g.add((self.uri, utilities.NS_DICT["oa"].hasBody, temp_body))
        g.add((temp_body, RDF.type, utilities.NS_DICT["oa"].TextualBody))
        g.add((temp_body, RDF.value, triple_str))
        g.add((temp_body, format_uri, format_str))
        return g

    def __str__(self):
        string = "\tid: " + str(self.id) + "\n"
        # text = strip_all_whitespace(str(self.text))
        string += "\ttype: " + str(self.context_type) + "\n"
        string += "\tmotivation: " + str(self.motivation) + "\n"
        string += "\theading: " + str(self.heading) + "\n"
        string += "\ttag: \n\t\t{" + str(self.tag) + "}\n"
        string += "\ttext: \n\t\t{" + str(self.text) + "}\n"
        if self.subjects:
            string += "\tsubjects:\n"
            for x in self.subjects:
                string += "\t\t" + str(x) + "\n"
        return string + "\n"
