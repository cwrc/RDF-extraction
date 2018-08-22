import rdflib
from rdflib import RDF, RDFS, Literal
import re
from biography import bind_ns, NS_DICT, make_standard_uri, remove_punctuation
from place import Place
from organizations import get_org_uri

MAX_WORD_COUNT = 35

"""
Status: ~80%
TODO: 
1) Review triples related to identifying contexts
2) revise mechanism for getting closest heading
3) Fix up labelling of contexts possibly
4) Revise text snippet to grab from where the first triple is extracted
    - however sometime for identifying contexts, names/orgs are identified
        prior to triples extracted
"""


def get_attribute(tag, attribute):
    value = tag.get(attribute)
    if value:
        return value
    return None


def get_value(tag):
    value = get_attribute(tag, "standard")
    if not value:
        value = get_attribute(tag, "reg")
    if not value:
        value = get_attribute(tag, "currentalternativeterm")
    if not value:
        value = str(tag.text)
        value = ' '.join(value.split())
    return value


def strip_all_whitespace(string):
# temp function for condensing the context strings for visibility in testing
    return re.sub('[\s+]', '', str(string))


def identifying_motivation(tag):
    identified_subjects = []
    for x in tag.find_all("place"):
        temp_place = Place(x)
        if temp_place.uri:
            identified_subjects.append(rdflib.term.URIRef(temp_place.uri))
        else:
            identified_subjects.append(Literal(temp_place.address))
    for x in tag.find_all("name"):
        identified_subjects.append(make_standard_uri(x.get("standard")))
    for x in tag.find_all("orgname"):
        identified_subjects.append(get_org_uri(x))
    for x in tag.find_all("title"):
        title = get_value(x)
        identified_subjects.append(make_standard_uri(title + " TITLE", ns="cwrc"))

    return identified_subjects


def get_heading(tag):
    # TODO: improve heading finding
    # Figure out distance between tag and the two available headings to see which is closest
    # Placeholder for now
    heading = tag.find("heading")
    if not heading:
        heading = tag.findPrevious("heading")
    if not heading:
        heading = tag.findNext("heading")
    if not heading:
        return "Biography"
    return remove_punctuation(strip_all_whitespace(heading.text), True)


class Context(object):
    """docstring for Context"""
    context_types = ["GenderContext", "PoliticalContext", "SocialClassContext",
                     "SexualityContext", "RaceEthnicityContext", "ReligionContext", "NationalityContext"]
    context_map = {"classissue": "SocialClassContext", "raceandethnicity": "RaceEthnicityContext",
                   "nationalityissue": "NationalityContext", "sexuality": "SexualityContext",
                   "politics": "PoliticalContext", "religion": "ReligionContext",
                   "culturalformation": "CulturalFormContext", "leisureandsociety": "LeisureContext",
                   "occupation": "OccupationContext", "location": "SpatialContext",
                   "violence": "ViolenceContext", "wealth": "WealthContext"}

    def __init__(self, id, tag, context_type="culturalformation", motivation="describing"):
        super(Context, self).__init__()
        self.id = id
        self.triples = []

        self.tag = tag
        self.src = "http://orlando.cambridge.org/protected/svPeople?formname=r&people_tab=3&person_id="
        self.heading = get_heading(tag)

        # rdfs:label "Atwood Education Context 1" ;
        # self.label = " "

        # Making the text the max amount of words
        # TODO: Make snippet start where first triple is extracted from
        self.text = ' '.join(str(tag.get_text()).split())
        words = self.text.split(" ")
        self.text = ' '.join(words[:MAX_WORD_COUNT])
        if len(words) > MAX_WORD_COUNT:
            self.text += "..."

        if context_type in self.context_map:
            self.context_type = rdflib.term.URIRef(str(NS_DICT["cwrc"]) + self.context_map[context_type])
            self.context_label = self.context_map[context_type]
        else:
            self.context_label = context_type
            self.context_type = rdflib.term.URIRef(str(NS_DICT["cwrc"]) + context_type)

        self.motivation = rdflib.term.URIRef(str(NS_DICT["oa"]) + motivation)
        self.subjects = []
        if motivation == "identifying":
            self.subjects = identifying_motivation(self.tag)
        self.uri = rdflib.term.URIRef(str(NS_DICT["data"]) + id)

    def link_triples(self, comp_list):
        """ Adding to list of components to link context to triples
        """
        self.triples += comp_list

    def get_subjects(self, comp_list):
        """
        Dependent on the other other classes functioning similarly to cf
        May have to make a variant for more complex components of biography
        """
        subjects = []
        for x in comp_list:
            subjects.append(x.value)
        return list(set(subjects))

    def to_triple(self, person):
        # if tag is a describing one create the identifying triples
        g = rdflib.Graph()
        namespace_manager = rdflib.namespace.NamespaceManager(g)
        bind_ns(namespace_manager, NS_DICT)

        # Creating Textual body first
        snippet_uri = rdflib.term.URIRef(str(self.uri) + "_Snippet")
        source_url = rdflib.term.URIRef(self.src + person.id + "#" + self.heading)
        snippet_label = person.name + " " + self.context_label + " snippet"
        g.add((snippet_uri, RDF.type, NS_DICT["oa"].TextualBody))
        g.add((snippet_uri, RDFS.label, rdflib.term.Literal(snippet_label)))
        g.add((snippet_uri, NS_DICT["oa"].hasSource, source_url))
        g.add((snippet_uri, NS_DICT["dctypes"].description, rdflib.term.Literal(
            self.text, datatype=rdflib.namespace.XSD.string)))

        # Creating identifying context first and always
        context_label = person.name + " " + self.context_label + " identifying annotation"
        identifying_uri = rdflib.term.URIRef(str(NS_DICT["data"]) + self.id + "_identifying")
        g.add((identifying_uri, RDF.type, self.context_type))
        g.add((identifying_uri, RDFS.label, rdflib.term.Literal(context_label)))
        g.add((identifying_uri, NS_DICT["oa"].hasTarget, snippet_uri))
        g.add((identifying_uri, NS_DICT["oa"].motivatedBy, NS_DICT["oa"].identifying))
        self.subjects += identifying_motivation(self.tag)
        if self.triples:
            self.subjects += self.get_subjects(self.triples)
        for x in self.subjects:
            g.add((identifying_uri, NS_DICT["oa"].hasBody, x))

        # Creating describing context if applicable
        if self.motivation == NS_DICT["oa"].describing:
            self.uri = rdflib.term.URIRef(str(NS_DICT["data"]) + self.id + "_describing")
            context_label = person.name + " " + self.context_label + " describing annotation"
            g.add((self.uri, RDF.type, self.context_type))
            g.add((self.uri, RDFS.label, rdflib.term.Literal(context_label)))
            g.add((self.uri, NS_DICT["cwrc"].hasIDependencyOn, identifying_uri))
            g.add((self.uri, NS_DICT["oa"].hasTarget, person.uri))
            g.add((self.uri, NS_DICT["oa"].hasTarget, snippet_uri))
            g.add((self.uri, NS_DICT["oa"].motivatedBy, self.motivation))

            for x in self.subjects:
                g.add((self.uri, NS_DICT["dcterms"].subject, x))

            format_str = rdflib.term.Literal("text/turtle", datatype=rdflib.namespace.XSD.string)
            format_uri = rdflib.term.URIRef(str(NS_DICT["dcterms"]) + "format")
            for x in self.triples:
                triple_str = x.to_triple(person).serialize(format="ttl").decode().splitlines()[-2]
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
