from bs4 import BeautifulSoup
import os
from os import listdir
import sys
import csv
import rdflib, sys
from rdflib import *

CWRC = rdflib.Namespace( "http://id.lincsproject.ca/cwrc#")
BF = rdflib.Namespace( "http://id.loc.gov/ontologies/bibframe/")
XML = rdflib.Namespace("http://www.w3.org/XML/1998/namespace")
MARCREL = rdflib.Namespace("http://id.loc.gov/vocabulary/relators/")
DATA = rdflib.Namespace("http://cwrc.ca/cwrcdata/")
GENRE = rdflib.Namespace("http://sparql.cwrc.ca/ontologies/genre#")
SCHEMA = rdflib.Namespace("http://schema.org/")

TYPE_MAPPING = {
    "monographic": "standaloneWork",
    "analytic": "embeddedWork",
    "journal": "periodical",
    "series": "series",
    "unpublished": "unpublished",

}

def csv_matches(csv_file):
    col_map = []
    mapping = {}
    with open(csv_file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            col_map.append(row)
    for item in col_map:
        if 'was_seen' in item:
            continue

        title_value = item['normalized']

        if item['ct_islink'] != "n" and item['ct_islink'] != "" and item['ct_islink'] != "?":
            try:
                row_number = int(item['ct_islink']) - 2 # Minus 2 because we have no header and csv are 1 indexed
            except ValueError:
                continue
            
            
            other_item = col_map[row_number]
            other_title = other_item['normalized']
            title_types = [other_item['titletype'], item['titletype']]
            normalized = [other_item['normalized'], item['normalized']]
            mapping[title_value] = {"title": normalized, "types": title_types}
            mapping[other_title] = {"title": normalized, "types": title_types}

            item['was_seen'] = True
            other_item['was_seen'] = True
        else:
            title_values = [item['normalized']]
            title_types = [item['titletype']]
            mapping[title_value] = {"title": title_values, "types": title_types}

    return mapping


def gen_rdf(mappings, g): 
    for key, value in mappings.items():

        # update the uri with a new value
        title = g.resource(key)
        title.add(RDF.type, BF.Title)
        for label in value['title']:
            title.add(RDFS.label, Literal(label))
        for type_str in value['types']:
            lower_type = type_str.lower()
            try:
                mapped_type = TYPE_MAPPING[lower_type]
            except KeyError:
                continue
            title.add(RDF.type, CWRC[mapped_type])
        




if __name__ == "__main__":

    g = Graph()

    g.bind("cwrc", CWRC)
    g.bind("bf", BF)
    g.bind("xml", XML, True)
    g.bind("marcrel", MARCREL)
    g.bind("data", DATA)
    g.bind("genre", GENRE)
    g.bind("owl", OWL)
    g.bind("schema", SCHEMA)


    if len(sys.argv) < 2:
        sys.exit(str.format("Usage: python {} [un_matched_csv] [files_dir] [bibliograph_dir]", sys.argv[0]))

    filePath = sys.argv[1]

    mappings = csv_matches(filePath)

    gen_rdf(mappings, g)
    output_name="titles_extracted"
    file_format = "pretty-xml"
    extension = "xml"
    g.serialize(destination="{}.{}".format(output_name, extension), format=file_format)