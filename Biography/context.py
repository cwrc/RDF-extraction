import rdflib
from rdflib import RDF, RDFS, Literal

from utilities import *
from organizations import get_org_uri

MAX_WORD_COUNT = 35

"""
Status: ~84%
TODO:
1) Revise mechanism for adding triples as a texual body for less list oriented components ex. Death
2) revise mechanism for getting closest heading
3) Fix up labelling of contexts possibly
4) Revise text snippet to grab from where the first triple is extracted
    - however sometime for identifying contexts, names/orgs are identified
        prior to triples extracted
"""


def identifying_motivation(tag):
    """ extracts the identifying components in a given tag
        to be used for the subjects of the annotation
    """
    identified_subjects = []

    identified_subjects += get_places(tag)
    identified_subjects += get_people(tag)
    identified_subjects += get_titles(tag)

    for x in tag.find_all("ORGNAME"):
        identified_subjects.append(get_org_uri(x))

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
        return "Biography"
    return remove_punctuation(strip_all_whitespace(heading.text), True)


class Context(object):
    """
    given the id for creating a context, the tag, context_type
    optional argument of motivation: default is describing
    if motivation is describing then
        it will also create the associated identifying contexts
    if only an identifying context is needed
    motivation="identifying" as argument is necessary
    """
    context_types = ["BiographyContext", "BirthContext", "CulturalFormContext",
                     "DeathContext", "FamilyContext", "FriendsAndAssociatesContext",
                     "GenderContext", "IntimateRelationshipsContext", "LeisureContext",
                     "NationalityContext", "OccupationContext", "PoliticalContext",
                     "RaceEthnicityContext", "ReligionContext", "SexualityContext",
                     "SocialClassContext", "SpatialContext", "ViolenceContext",
                     "WealthContext", "EducationContext", "PersonNameContext",
                     "InstitutionalEducationContext", "SelfTaughtEducationContext", "DomesticEducationContext"]

    context_map = {"CLASSISSUE": "SocialClassContext",
                   "RACEANDETHNICITY": "RaceEthnicityContext",
                   "NATIONALITYISSUE": "NationalityContext",
                   "SEXUALITY": "SexualityContext",
                   "POLITICS": "PoliticalContext",
                   "RELIGION": "ReligionContext",
                   "CULTURALFORMATION": "CulturalFormContext",
                   "LEISUREANDSOCIETY": "LeisureContext",
                   "OCCUPATION": "OccupationContext",
                   "LOCATION": "SpatialContext",
                   "VIOLENCE": "ViolenceContext",
                   "WEALTH": "WealthContext",
                   "OTHERLIFEEVENT": "BiographyContext",
                   "FAMILY": "FamilyContext",
                   "BIRTH": "BirthContext",
                   "DEATH": "DeathContext",
                   "FRIENDSASSOCIATES": "FriendsAndAssociatesContext",
                   "INTIMATERELATIONSHIPS": "IntimateRelationshipsContext",
                   "PERSONNAME": "PersonNameContext"
                   }

    def __init__(self, id, tag, context_type="culturalformation", motivation="describing"):
        super(Context, self).__init__()
        self.id = id
        self.triples = []
        self.event = None

        bibcits = tag.find_all("BIBCITS")
        for x in bibcits:
            x.decompose()
        self.tag = tag
        self.src = "http://orlando.cambridge.org/protected/svPeople?formname=r&people_tab=3&person_id="
        self.heading = get_heading(tag)

        # TODO: Make snippet start where first triple is extracted from
        # Making the text the max amount of words
        self.text = limit_words(str(tag.get_text()), MAX_WORD_COUNT)

        if context_type in self.context_map:
            self.context_type = create_uri("cwrc", self.context_map[context_type])
            self.context_label = self.context_map[context_type].split("Context")[0] + " Context"
        else:
            self.context_type = create_uri("cwrc", context_type)
            self.context_label = context_type.split("Context")[0] + " Context"

        self.motivation = create_uri("oa", motivation)
        self.subjects = []
        if motivation == "identifying":
            self.subjects = identifying_motivation(self.tag)
        self.uri = create_uri("data", id)

    def link_triples(self, comp_list):
        """ Adding to list of components to link context to triples
        """

        if type(comp_list) is list:
            self.triples += comp_list
        else:
            self.triples.append(comp_list)

    def link_event(self, event):
        self.event = event.uri

    def get_subjects2(self, comp_list):
        subjects = []
        for x in comp_list:
            temp_graph = x.to_triple("BOB")
            subjects.append(temp_graph.objects(None, None))

        return list(set(subjects))

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

    def to_triple(self, person):
        # if tag is a describing one create the identifying triples
        g = rdflib.Graph()
        namespace_manager = rdflib.namespace.NamespaceManager(g)
        bind_ns(namespace_manager, NS_DICT)

        # Creating Textual body first
        snippet_uri = rdflib.term.URIRef(str(self.uri) + "_Snippet")
        source_url = rdflib.term.URIRef(self.src + person.id + "#" + self.heading)
        snippet_label = person.name + " - " + self.context_label + " snippet"
        g.add((snippet_uri, RDF.type, NS_DICT["oa"].TextualBody))
        g.add((snippet_uri, RDFS.label, rdflib.term.Literal(snippet_label)))
        g.add((snippet_uri, NS_DICT["oa"].hasSource, source_url))
        g.add((snippet_uri, NS_DICT["dcterms"].description, rdflib.term.Literal(
            self.text, datatype=rdflib.namespace.XSD.string)))

        # Creating identifying context first and always
        context_label = person.name + " - " + self.context_label + " identifying annotation"
        identifying_uri = create_uri("data", self.id + "_identifying")
        g.add((identifying_uri, RDF.type, self.context_type))
        g.add((identifying_uri, RDFS.label, rdflib.term.Literal(context_label)))
        g.add((identifying_uri, NS_DICT["oa"].hasTarget, snippet_uri))
        g.add((identifying_uri, NS_DICT["oa"].motivatedBy, NS_DICT["oa"].identifying))
        self.subjects += identifying_motivation(self.tag)
        if self.triples:
            self.subjects += self.get_subjects(self.triples, person)
        for x in self.subjects:
            g.add((identifying_uri, NS_DICT["oa"].hasBody, x))
        g.add((identifying_uri, NS_DICT["oa"].hasBody, person.uri))

        if self.event:
            g.add((identifying_uri, NS_DICT["cwrc"].hasEvent, self.event))

        # Creating describing context if applicable
        if self.motivation == NS_DICT["oa"].describing:
            self.uri = create_uri("data", self.id + "_describing")
            context_label = person.name + " - " + self.context_label + " describing annotation"
            g.add((self.uri, RDF.type, self.context_type))
            g.add((self.uri, RDFS.label, rdflib.term.Literal(context_label)))
            g.add((self.uri, NS_DICT["cwrc"].hasIDependencyOn, identifying_uri))
            g.add((self.uri, NS_DICT["oa"].hasTarget, person.uri))
            g.add((self.uri, NS_DICT["oa"].hasTarget, snippet_uri))
            g.add((self.uri, NS_DICT["oa"].motivatedBy, self.motivation))

            for x in self.subjects:
                g.add((self.uri, NS_DICT["dcterms"].subject, x))

            for x in self.triples:
                temp_str = x.to_triple(person).serialize(format="ttl").decode().splitlines()
                triple_str_test = [y for y in temp_str if "@prefix" not in y and y != '']
                if len(triple_str_test) == 1:
                    triple_str = x.to_triple(person).serialize(format="ttl").decode().splitlines()[-2]
                    g += self.create_ttl_body(triple_str)
                else:
                    triple_str = "\n".join(triple_str_test)
                    g += self.create_multiple_triples(x.to_triple(person))

            if self.event:
                g.add((self.uri, NS_DICT["cwrc"].hasEvent, self.event))

        # Creating the mentioned people as natural person
        for x in self.tag.find_all("NAME"):
            uri = make_standard_uri(x.get("STANDARD"))
            g.add((uri, RDF.type, NS_DICT["cwrc"].NaturalPerson))
            g.add((uri, RDFS.label, Literal(x.get("STANDARD"), datatype=rdflib.namespace.XSD.string)))
            g.add((uri, NS_DICT["foaf"].name, Literal(x.get("STANDARD"), datatype=rdflib.namespace.XSD.string)))

        return g

    def create_multiple_triples(self, graph):
        """handles multitple triples
        """
        temp_g = rdflib.Graph()
        g = rdflib.Graph()
        namespace_manager = rdflib.namespace.NamespaceManager(temp_g)
        bind_ns(namespace_manager, NS_DICT)
        for x in graph[:]:
            temp_g.add(x)
            triple_str = temp_g.serialize(format="ttl").decode().splitlines()[-2]
            temp_g.remove(x)
            g += self.create_ttl_body(triple_str)

        return g

    def create_ttl_body(self, triple_str):
        g = rdflib.Graph()
        format_str = rdflib.term.Literal("text/turtle", datatype=rdflib.namespace.XSD.string)
        format_uri = create_uri("dcterms", "format")
        triple_str = rdflib.term.Literal(triple_str, datatype=rdflib.namespace.XSD.string)
        temp_body = rdflib.BNode()
        g.add((self.uri, NS_DICT["oa"].hasBody, temp_body))
        g.add((temp_body, RDF.type, NS_DICT["oa"].TextualBody))
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
