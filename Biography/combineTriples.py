#!/usr/bin/python3
import os
from rdflib import Graph, Namespace, namespace

NS_DICT = {
    "as": Namespace("http://www.w3.org/ns/activitystreams#"),
    "bibo": Namespace("http://purl.org/ontology/bibo/"),
    "bio": Namespace("http://purl.org/vocab/bio/0.1/"),
    "bf": Namespace("http://id.loc.gov/ontologies/bibframe/"),
    "cc": Namespace("http://creativecommons.org/ns#"),
    "cwrc": Namespace("http://id.lincsproject.ca/cwrc#"),
    "data": Namespace("http://cwrc.ca/cwrcdata/"),
    "dbpedia": Namespace("http://dbpedia.org/resource/"),
    "dcterms": Namespace("http://purl.org/dc/terms/"),
    "dctypes": Namespace("http://purl.org/dc/dcmitype/"),
    "eurovoc": Namespace("http://eurovoc.europa.eu/"),
    "foaf": Namespace("http://xmlns.com/foaf/0.1/"),
    "geonames": Namespace("http://sws.geonames.org/"),
    "gvp": Namespace("http://vocab.getty.edu/ontology#"),
    "loc": Namespace("http://id.loc.gov/vocabulary/relators/"),
    "oa": Namespace("http://www.w3.org/ns/oa#"),
    "org": Namespace("http://www.w3.org/ns/org#"),
    "owl": Namespace("http://www.w3.org/2002/07/owl#"),
    "prov": Namespace("http://www.w3.org/ns/prov#"),
    "rdf": Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#"),
    "rdfs": Namespace("http://www.w3.org/2000/01/rdf-schema#"),
    "sem": Namespace("http://semanticweb.cs.vu.nl/2009/11/sem/"),
    "schema": Namespace("http://schema.org/"),
    "skos": Namespace("http://www.w3.org/2004/02/skos/core#"),
    "skosxl": Namespace("http://www.w3.org/2008/05/skos-xl#"),
    "time": Namespace("http://www.w3.org/2006/time#"),
    "vann": Namespace("http://purl.org/vocab/vann/"),
    "voaf": Namespace("http://purl.org/vocommons/voaf#"),
    "void": Namespace("http://rdfs.org/ns/void#"),
    "vs": Namespace("http://www.w3.org/2003/06/sw-vocab-status/ns#")
}


def bind_ns(namespace_manager, ns_dictionary):
    for x in ns_dictionary.keys():
        namespace_manager.bind(x, ns_dictionary[x], override=False)


# root        = "~/Documents/UoGuelph Projects/CombiningTriples/"
drivePath = os.path.expanduser("~/Google Drive/Extraction/")
dtnPath_turtle = os.path.expanduser("CombinedFiles_turtle/")
dtnPath_rdf = os.path.expanduser("CombinedFiles_rdf/")

# aPath       = os.path.expanduser(drivePath + "culturalform_triples/")
# dPath       = os.path.expanduser(drivePath + "CauseOfDeath_Triples/")
dPath = os.path.expanduser("CauseOfDeath_Triples/")
gPath = os.path.expanduser("Bio_Triples/")

gFiles = []
# aFiles = []
dFiles = []


def isFileA(file):
    return file in aFiles


def isFileD(file):
    return file in dFiles


def updateFileLists():
    global gFiles
    global aFiles
    global dFiles

    gFiles = [filename for filename in sorted(os.listdir(gPath)) if filename.endswith(".ttl")]
    # gFiles = [filename for filename in sorted(os.listdir("bio_data/")) if filename.endswith(".xml")]
    dFiles = [filename for filename in sorted(os.listdir(dPath)) if filename.endswith(".txt")]


def main():
    global gFiles
    global dFiles

    updateFileLists()

    index = 1
    numTriples = 0
    print(gPath)
    noWork = []
    missing = []
    gurjapCounter = 0
    megaGraph = Graph()
    megaGraph.parse("organizations.ttl", format="turtle")
    namespace_manager = namespace.NamespaceManager(megaGraph)
    bind_ns(namespace_manager, NS_DICT)
    # f = open("namesAndTriples6.txt", "w")

    for name in gFiles:

        # alGraph = Graph()
        dGraph = Graph()
        gGraph = Graph()

        fileName = name[0:-4]
        # alFileName = aPath + fileName + "-cf.txt"
        gFileName = gPath + name
        dFileName = dPath + fileName + "-cod.txt"
        codExists = False
        # graph.parse(dFileName,format="turtle")

        print(name[0:-4], isFileD(fileName + "-cod.txt"))
        # continue
        # if isFileA(fileName+ "-cf.txt") == False:
        #     continue

        # if(os.path.isfile(dFileName)):
        #     graph.parse(dFileName,format="turtle")
        #     print("got one from deb")
        #     debNum += 1

        # alGraph.parse(alFileName,format="turtle")
        # if os.path.isfile(dFileName) == True:
            # continue
        if isFileD(fileName + "-cod.txt"):
            dGraph.parse(dFileName, format="turtle")
            codExists = True
        # else:
        #     missing.append(fileName + "-cod.txt")

        gGraph.parse(gFileName, format="turtle")
        gurjapCounter += len(gGraph)
        graph = dGraph + gGraph
        namespace_manager = namespace.NamespaceManager(graph)
        bind_ns(namespace_manager, NS_DICT)

        index += 1
        numTriples += len(graph)
        megaGraph += graph
        graph.serialize(destination=dtnPath_turtle + fileName + '.ttl', format='turtle')
        graph.serialize(destination=dtnPath_rdf + fileName + '.rdf', format='pretty-xml')

        # gFiles.remove(name)
        # print(len(aFiles))
        # print(len(aFiles))

        if codExists:
            dFiles.remove(fileName + "-cod.txt")
        # print("number of triples",numTriples)

    # f.close()
    megaGraph.serialize("BIOGRAPHY" + '.ttl', format='turtle')
    megaGraph.serialize("BIOGRAPHY" + '.rdf', format='pretty-xml')

    print("total Triples: ", numTriples)
    print("total Gurjap Triples: ", gurjapCounter)
    print("didnt work ==============")
    for no in noWork:
        print(no)
    print("wasn't there ============")
    for jk in missing:
        print(jk)

if __name__ == '__main__':
    main()
