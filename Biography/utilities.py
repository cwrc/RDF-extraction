import rdflib
import os
from place import Place

NS_DICT = {
    "as": rdflib.Namespace("http://www.w3.org/ns/activitystreams#"),
    "bibo": rdflib.Namespace("http://purl.org/ontology/bibo/"),
    "bio": rdflib.Namespace("http://purl.org/vocab/bio/0.1/"),
    "bf": rdflib.Namespace("http://id.loc.gov/ontologies/bibframe/"),
    "cc": rdflib.Namespace("http://creativecommons.org/ns#"),
    "cwrc": rdflib.Namespace("http://sparql.cwrc.ca/ontologies/cwrc#"),
    "data": rdflib.Namespace("http://cwrc.ca/cwrcdata/"),
    "dbpedia": rdflib.Namespace("http://dbpedia.org/resource/"),
    "dcterms": rdflib.Namespace("http://purl.org/dc/terms/"),
    "dctypes": rdflib.Namespace("http://purl.org/dc/dcmitype/"),
    "eurovoc": rdflib.Namespace("http://eurovoc.europa.eu/"),
    "foaf": rdflib.Namespace("http://xmlns.com/foaf/0.1/"),
    "geonames": rdflib.Namespace("http://sws.geonames.org/"),
    "gvp": rdflib.Namespace("http://vocab.getty.edu/ontology#"),
    "loc": rdflib.Namespace("http://id.loc.gov/vocabulary/relators/"),
    "oa": rdflib.Namespace("http://www.w3.org/ns/oa#"),
    "org": rdflib.Namespace("http://www.w3.org/ns/org#"),
    "owl": rdflib.Namespace("http://www.w3.org/2002/07/owl#"),
    "prov": rdflib.Namespace("http://www.w3.org/ns/prov#"),
    "rdf": rdflib.Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#"),
    "rdfs": rdflib.Namespace("http://www.w3.org/2000/01/rdf-schema#"),
    "sem": rdflib.Namespace("http://semanticweb.cs.vu.nl/2009/11/sem/"),
    "schema": rdflib.Namespace("http://schema.org/"),
    "skos": rdflib.Namespace("http://www.w3.org/2004/02/skos/core#"),
    "skosxl": rdflib.Namespace("http://www.w3.org/2008/05/skos-xl#"),
    "time": rdflib.Namespace("http://www.w3.org/2006/time#"),
    "vann": rdflib.Namespace("http://purl.org/vocab/vann/"),
    "voaf": rdflib.Namespace("http://purl.org/vocommons/voaf#"),
    "void": rdflib.Namespace("http://rdfs.org/ns/void#"),
    "vs": rdflib.Namespace("http://www.w3.org/2003/06/sw-vocab-status/ns#")
}


def bind_ns(namespace_manager, ns_dictionary):
    for x in ns_dictionary.keys():
        namespace_manager.bind(x, ns_dictionary[x], override=False)


"""Some string manipulation functions"""


def strip_all_whitespace(string):
    # temp function for condensing the context strings for visibility in testing
    import re
    return re.sub('[\s+]', '', str(string))


def remove_punctuation(temp_str, all=False):
    import string
    if all:
        translator = str.maketrans('', '', string.punctuation)
    else:
        translator = str.maketrans('', '', string.punctuation.replace("-", ""))
    temp_str = temp_str.translate(translator)
    temp_str = temp_str.replace(" ", "_")
    return temp_str


def limit_words(string, word_count):
    """Returns a string of a given word count size"""
    text = ' '.join(str(string).split())
    words = text.split(" ")
    text = ' '.join(words[:word_count])
    if len(words) > word_count:
        text += "..."
    return text


"""
    Series of functions to do with the creation of URI
"""


def get_name_uri(tag):
    """Creates a uri based on the standard attribute of a tag"""
    return make_standard_uri(tag.get("STANDARD"))


def make_standard_uri(std_str, ns="data"):
    """Makes uri based of string, removes punctuation and replaces spaces with an underscore
    v2, leaving hypens
    """
    return create_uri(ns, remove_punctuation(std_str))


def create_uri(prefix, term):
    """prepends the provided namespace uri to the given term"""
    return rdflib.term.URIRef(str(NS_DICT[prefix]) + term)


def create_cwrc_uri(term):
    """prepends the cwrc namespace uri to the given term"""
    return create_uri("cwrc", term)


def get_value(tag):
    value = get_attribute(tag, "STANDARD")
    if not value:
        value = get_attribute(tag, "REG")
    if not value:
        value = get_attribute(tag, "CURRENTALTERNATIVETERM")
    if not value:
        value = str(tag.text)
        value = ' '.join(value.split())
    return value


def get_attribute(tag, attribute):
    value = tag.get(attribute)
    if value:
        return value
    return None


def get_reg(tag):
    return get_attribute(tag, "REG")


def get_people(tag):
    """Returns all people within a given tag"""
    people = []
    for x in tag.find_all("NAME"):
        people.append(get_name_uri(x))
    return people


def get_titles(tag):
    """Returns all titles within a given tag TODO Mapping"""
    titles = []
    for x in tag.find_all("TITLE"):
        title = get_value(x)
        titles.append(make_standard_uri(title + " TITLE", ns="cwrc"))
    return titles


def get_places(tag):
    """Returns all places within a given tag"""
    places = []
    for x in tag.find_all("PLACE"):
        places.append(Place(x).uri)
    return places


def get_name(bio):
    return (bio.BIOGRAPHY.DIV0.STANDARD.text)


def get_sex(bio):
    return (bio.BIOGRAPHY.get("SEX"))


"""
Creating files of extracted triples
"""


def create_extracted_file(filepath, person, serialization=None):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        if serialization:
            f.write(person.to_file(serialization=serialization))
        else:
            f.write("#" + str(len(person.to_graph())) + " triples created\n")
            f.write(person.to_file())


def create_extracted_uberfile(filepath, graph, serialization=None):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        if serialization:
            f.write(graph.serialize(format=serialization).decode())
        else:
            f.write("#" + str(len(graph)) + " triples created\n")
            f.write(graph.serialize(format="ttl").decode())
