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
"""

if (len(sys.argv) != 2):
    print("Insufficent arguments provided")
    print("Expected usage:")
    print(sys.argv[1], " path/file.ttl")
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
    if cwrc_uri in str(o) and "_ORG" not in str(o):
        cwrc_terms.append(o)

cwrc_terms = set(cwrc_terms)
for x in cwrc_terms:
    if not (x, None, None) in ontology:
        print("Term not found: ", x)
