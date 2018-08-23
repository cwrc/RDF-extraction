import rdflib
import sys

""" Currently parses supplied data file and parses with turtle parser
    Checks for any CWRC ontology uris within datafile
    Then checks if used uri is valid and avaliable within the CWRC ontology
    outputs incorrect uris

    This is super bare bones however would really like to extend it past our ontology
    TODO eventually:
    - validates prefixes are being properly used
    - validate used terms with any uris within the namespace of the datafile
        - Ideally would scrape url from namespace and retrieve rdf file and parse it
        - check uris from that if available
            - probably will have to make a json file of valid paths to rdf/turtle file
    - suggest nearmatches for terms used
"""

NS_DICT = {
    "as": rdflib.Namespace("http://www.w3.org/ns/activitystreams#"),
    "bibo": rdflib.Namespace("http://purl.org/ontology/bibo/"),
    "bio": rdflib.Namespace("http://purl.org/vocab/bio/0.1/"),
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
    "schema": rdflib.Namespace("http://schema.org/"),
    "skos": rdflib.Namespace("http://www.w3.org/2004/02/skos/core#"),
    "skosxl": rdflib.Namespace("http://www.w3.org/2008/05/skos-xl#"),
    "time": rdflib.Namespace("http://www.w3.org/2006/time#"),
    "vann": rdflib.Namespace("http://purl.org/vocab/vann/"),
    "voaf": rdflib.Namespace("http://purl.org/vocommons/voaf#"),
    "void": rdflib.Namespace("http://rdfs.org/ns/void#"),
    "vs": rdflib.Namespace("http://www.w3.org/2003/06/sw-vocab-status/ns#")
}


if (len(sys.argv) != 2):
    print("Insufficent arguments provided")
    print("Expected usage:")
    print(sys.argv[0], " path/file.ttl")
    exit()

# Loading up data file
data_file = sys.argv[1]
data_triples = rdflib.Graph()
data_triples.parse(data_file, format='turtle')
namespace_manager = rdflib.namespace.NamespaceManager(data_triples)
print(len(data_triples), "Triples in provided data file")

# Loading up ontology from repo
ontology = rdflib.Graph()
ontology.parse("https://raw.githubusercontent.com/cwrc/ontology/master/cwrc.rdf", format='xml')
namespace_manager = rdflib.namespace.NamespaceManager(ontology)

cwrc_uri = "http://sparql.cwrc.ca/ontologies/cwrc#"
cwrc_terms = []

# find cwrc predicates and objects within the datafile
for s, p, o in data_triples.triples((None, None, None)):
    if cwrc_uri in str(p):
        cwrc_terms.append(p)
    if cwrc_uri in str(o) and "_ORG" not in str(o) and "_TITLE" not in str(o):
        cwrc_terms.append(o)


cwrc_terms = set(cwrc_terms)
invalid_terms = []
deprecated_terms = []

for x in cwrc_terms:
    if not (x, None, None) in ontology:
        print("Term not found:", x)
        invalid_terms.append(x)
    elif (x, NS_DICT["vs"].term_status, None) in ontology:
        if str(ontology.value(x, NS_DICT["vs"].term_status)) == "deprecated":
            print("Term has been deprecated:", x)
            deprecated_terms.append(x)
    elif (x, NS_DICT["owl"].deprecated, None) in ontology:
        if str(ontology.value(x, NS_DICT["owl"].deprecated)) == "true":
            print("Term has been deprecated:", x)
            deprecated_terms.append(x)


# Displaying summary of results with possible replacement
print("\nResults:")
print("Number of deprecated terms:", len(deprecated_terms))
if deprecated_terms:
    print("\t deprecated term --> possible replacement")

for x in deprecated_terms:
    replacement = ontology.value(x, NS_DICT["dcterms"].isReplacedBy)
    if replacement:
        print("\t", x, "-->", replacement)
    else:
        print("\t", x, "--> No Replacement found!")
print("Number of invalid terms:", len(invalid_terms))
for x in invalid_terms:
    print("\t", x)
