import rdflib
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS

# Define the namespaces
CWRC = rdflib.Namespace("http://id.lincsproject.ca/cwrc/")
GENRE = rdflib.Namespace("http://id.lincsproject.ca/genre/")
II = rdflib.Namespace("http://id.lincsproject.ca/ii/")
OCC = rdflib.Namespace("http://id.lincsproject.ca/occupation/")

PREFIXES = ["cwrc", "genre", "ii", "occupation"]

data_label = "biography"
# Load the two turtle files into a graph
data_graph = Graph()
data_graph.parse("extracted_triples/biography_triples.ttl", format="turtle")
# data_graph.parse("../Mods/bibliography_01-05-2023.ttl", format="turtle")
# data_graph.parse("extracted_triples/biography_ttl/woolvi_biography.ttl", format="turtle")

vocab_graph = Graph()
vocab_graph.parse("/Users/alliyya/Desktop/vocabularies/genre.ttl", format="turtle")
vocab_graph.parse("/Users/alliyya/Desktop/vocabularies/occupation.ttl", format="turtle")
vocab_graph.parse("/Users/alliyya/Desktop/vocabularies/ii.ttl", format="turtle")
vocab_graph.parse("/Users/alliyya/Desktop/vocabularies/cwrc.ttl", format="turtle")


output_graph = Graph()

def check_namespace(entity, namespaces):
    for namespace in namespaces:
        if entity.startswith(namespace):
            return True
    return False

def get_unique_uris(graph, namespaces):
    print(namespaces)
    namespaces = [str(x) for x in namespaces]
    unique_uris = set()
    for s, p, o in graph:
        if check_namespace(s,namespaces):
            unique_uris.add(s)
        if check_namespace(o,namespaces):
            unique_uris.add(o)
    
    return unique_uris

# Function to look up English labels for URIs in the first graph from the second graph
def lookup_labels(graph1, graph2, namespaces):
    unique_uris = get_unique_uris(graph1, namespaces)
    for uri in unique_uris:
        english_label = None
        for s, p, o in graph2.triples((uri, RDFS.label, None)):
            if o.language == 'en':
                english_label = o
                break

        if english_label:
            output_graph.add((uri, RDFS.label, english_label))
        else:
            print(f"Warning: No English label found for URI {uri}")

# Call the lookup_labels function with the cwrc and genre namespaces
lookup_labels(data_graph, vocab_graph, [CWRC, GENRE, II, OCC])

# Serialize the output graph to a turtle file
with open(F"{data_label}_output_labels.ttl", "w") as f:
    f.write(output_graph.serialize(format="turtle"))