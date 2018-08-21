
from rdflib import RDF
from rdflib import Graph, Namespace
import os


def main():
    root        = "~/Documents/UoGuelph Projects/CombiningTriples/"
    drivePath    = os.path.expanduser("~/Google Drive/Extraction/")
    dtnPath     = os.path.expanduser(root + "CombinedFiles/")

    aPath       = os.path.expanduser(drivePath + "culturalform_triples/")
    dPath       = os.path.expanduser(drivePath + "CauseOfDeath_Triples/")
    gPath       = os.path.expanduser(root + "birthDeathFamily_triples/")


    index = 1
    numTriples = 0
    print(gPath)
    noWork = []
    missing = []
    gurjapCounter  = 0
    megaGraph = Graph()
    # f = open("namesAndTriples6.txt", "w")
    for dirName, subdirlist, files in os.walk(gPath):
        for name in files:
            # print(name)
            # if "dumaal" not in name:
            #     continue

            alGraph = Graph()
            dGraph  = Graph()
            gGraph  = Graph()

            fileName = name[0:-4]
            alFileName = aPath + fileName + "-cf.txt"
            gFileName = gPath + name
            dFileName = dPath + fileName + "-cod.txt"
            # graph.parse(dFileName,format="turtle")

            print(name[0:-4],os.path.isfile(alFileName),os.path.isfile(dFileName))

            if(os.path.isfile(alFileName)) == False:
                continue

            # if(os.path.isfile(dFileName)):
            #     graph.parse(dFileName,format="turtle")
            #     print("got one from deb")
            #     debNum += 1

            alGraph.parse(alFileName,format="turtle")
            # if os.path.isfile(dFileName) == True:
                # continue
            try:
                dGraph.parse(dFileName,format="turtle")
            except Exception as e:
                noWork.append(fileName + "-cod.txt")
                print("error", e)
            # else:
            #     missing.append(fileName + "-cod.txt")


            gGraph.parse(gFileName,format="turtle")
            gurjapCounter += len(gGraph)
            graph = alGraph + dGraph + gGraph
            cwrcNamespace   = Namespace('http://sparql.cwrc.ca/ontologies/cwrc#')
            oa              = Namespace('http://www.w3.org/ns/oa#')
            data            = Namespace('http://cwrc.ca/cwrcdata/')
            foaf            = Namespace('http://xmlns.com/foaf/0.1/')
            graph.bind('cwrc', cwrcNamespace)
            graph.bind('oa', oa)
            graph.bind('data', data)
            graph.bind('foaf', foaf)
            # print(graph.serialize(format='turtle').decode())

            # f.write("%s:%d\n" % (name, len(graph)))
            # print("Al:",len(alGraph),"d:",len(dGraph),"g:",len(gGraph))
            # print("index: ",index,"total triples",len(graph))

            index += 1
            numTriples += len(graph)
            megaGraph += graph
            # graph.serialize(destination=dtnPath + fileName + '.txt', format='turtle')
            # print("number of triples",numTriples)

    # f.close()
    megaGraph.serialize(destination=drivePath + "SUPER_MEGA_GRAPH" + '.txt', format='turtle')

    print("total Triples: ",numTriples)
    print("total Gurjap Triples: ", gurjapCounter)
    print("didnt work ==============")
    for no in noWork:
        print(no)
    print("wasn't there ============")
    for jk in missing:
        print(jk)

if __name__ == '__main__':
    main()