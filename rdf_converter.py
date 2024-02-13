import rdflib
import argparse

NS_DICT = {
    "biography":"http://id.lincsproject.ca/biography/",
    "context":"http://id.lincsproject.ca/context/",
    "cwrc":"http://id.lincsproject.ca/cwrc/",
    "event":"http://id.lincsproject.ca/event/",
    "genre":"http://id.lincsproject.ca/genre/",
    "identity":"http://id.lincsproject.ca/identity/",
    "edit":"http://id.lincsproject.ca/edit/",
    "ii":"http://id.lincsproject.ca/ii/",
    "occupation":"http://id.lincsproject.ca/occupation/",
    "persrel":"http://id.lincsproject.ca/persrel/",
    "writing":"http://id.lincsproject.ca/writing/",
    "frbroo":"http://iflastandards.info/ns/fr/frbr/frbroo/",
    "as":"http://www.w3.org/ns/activitystreams#",
    "bibo":"http://purl.org/ontology/bibo/",
    "biro":"http://purl.org/spar/biro/",
    "bio":"http://purl.org/vocab/bio/0.1/",
    "bf":"http://id.loc.gov/ontologies/bibframe/",
    "cc":"http://creativecommons.org/ns#",
    "cito":"http://purl.org/spar/cito/",
    "crm":"http://www.cidoc-crm.org/cidoc-crm/",
    "crmdig":"http://www.ics.forth.gr/isl/CRMdig/",
    "data":"http://cwrc.ca/cwrcdata/",
    "dbpedia":"http://dbpedia.org/resource/",
    "dcterms":"http://purl.org/dc/terms/",
    "dctypes":"http://purl.org/dc/dcmitype/",
    "eurovoc":"http://eurovoc.europa.eu/",
    "foaf":"http://xmlns.com/foaf/0.1/",
    "geonames":"https://sws.geonames.org/",
    "gvp":"http://vocab.getty.edu/ontology#",
    "loc":"http://id.loc.gov/vocabulary/relators/",
    "oa":"http://www.w3.org/ns/oa#",
    "org":"http://www.w3.org/ns/org#",
    "owl":"http://www.w3.org/2002/07/owl#",
    "prov":"http://www.w3.org/ns/prov#",
    "prism":"http://prismstandard.org/namespaces/1.2/basic/",
    "rdf":"http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs":"http://www.w3.org/2000/01/rdf-schema#",
    "sem":"http://semanticweb.cs.vu.nl/2009/11/sem/",
    "schema":"http://schema.org/",
    "skos":"http://www.w3.org/2004/02/skos/core#",
    "skosxl":"http://www.w3.org/2008/05/skos-xl#",
    "time":"http://www.w3.org/2006/time#",
    "vann":"http://purl.org/vocab/vann/",
    "voaf":"http://purl.org/vocommons/voaf#",
    "void":"http://rdfs.org/ns/void#",
    "vs":"http://www.w3.org/2003/06/sw-vocab-status/ns#",
    "cwrc_temp":"http://temp.lincsproject.ca/cwrc/",
    "lincs":"http://id.lincsproject.ca/",
    "temp":"http://temp.lincsproject.ca/",
}

def bind_ns(namespace_manager, ns_dictionary):
    """
    Binds namespaces to the given namespace manager.

    Args:
        namespace_manager (NamespaceManager): The namespace manager to bind the namespaces to.
        ns_dictionary (dict): A dictionary containing the namespaces to bind, where the keys are the prefixes
                              and the values are the URIs.

    Returns:
        None
    """
    for x in ns_dictionary.keys():
        namespace_manager.bind(x, rdflib.Namespace(ns_dictionary[x]), override=False) # TODO: check if override is necessary

def convert_file(file_path, output_file_path=None, base_uri="http://temp.lincsproject.ca/", output_format="turtle"):
    """
    Converts an RDF file to a specified output format and optionally saves it to a file.

    Args:
        file_path (str): The path to the input RDF file.
        output_file_path (str, optional): The path to save the converted RDF file. If not provided, the converted RDF data will be printed to the console. Defaults to None.
        base_uri (str, optional): The base URI for the RDF graph. Defaults to "http://temp.lincsproject.ca/".
        output_format (str, optional): The output format for the converted RDF data. Defaults to "turtle".

    Returns:
        None
    """
    # Create an RDF graph
    g = rdflib.Graph()
    namespace_manager = rdflib.namespace.NamespaceManager(g)
    bind_ns(namespace_manager, NS_DICT)

    # Read input from a file
    try:
        with open(file_path, 'r') as file:
            input_data = file.read()
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        exit(1)
        
    # Parsing input data
    try:
        input_format = rdflib.util.guess_format(file_path)
        if input_format == "json-ld":
            g.parse(data=input_data, format='json-ld', base=base_uri)
        else:
            g.parse(file_path)
    except Exception as e:
        print(f"Error parsing the input file: {e}")
        exit(1)
    
    
    # Serialize the graph to chosen format
    output_format =  rdflib.util.guess_format(output_file_path) if output_file_path else output_format 
    if output_format == "json-ld":
        output_data = g.serialize(format='json-ld', indent=2, auto_compact=True)
    else:
        output_data = g.serialize(format=output_format)
    
    # Save the output to a file or print to the console
    if output_file_path:
        with open(output_file_path, 'w') as file:
            file.write(output_data)
    else:
        print(output_data)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert JSON-LD/RDF/TTL/NT to JSON-LD/RDF/TTL/NT format.")
    parser.add_argument('input_file', type=str, help="Input JSON-LD/RDF/TTL/NT file path.")
    parser.add_argument('-o', '--output_file', type=str, default=None, help="Output file path, the file extension will be used to determine output format. If not provided, output will be printed to stdout.")
    parser.add_argument('-b', '--base_uri', type=str, default="http://temp.lincsproject.ca/", help="Base URI. Optional, defaults to http://temp.lincsproject.ca/")
    parser.add_argument('-f', '--format', type=str, default="turtle", choices=['xml', 'ttl', 'turtle', 'json-ld', 'json', 'jsonld', "ntriples", "nt","nt11"], help="Output format if printing to stdout. Default is 'turtle'.")

    args = parser.parse_args()

    convert_file(args.input_file, args.output_file, args.base_uri, args.format)
