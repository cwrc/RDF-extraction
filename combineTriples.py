
from rdflib import RDF
from rdflib import Graph, Namespace
import os


def main():
    root = "~/Documents/UoGuelph Projects/CombiningTriples/"
    aPath       = os.path.expanduser(root + "culturalform_triples/")
    gPath       = os.path.expanduser(root + "birthDeathFamily_triples/")
    dPath       = os.path.expanduser(root + "CauseOfDeath_Triples/")
    dtnPath     = os.path.expanduser(root + "CombinedFiles/")

    index = 1
    numTriples = 0
    print(gPath)
    noWork = []
    missing = []
    gurjapCounter  = 0
    # f = open("namesAndTriples6.txt", "w")
    for dirName, subdirlist, files in os.walk(gPath):
        for name in files:
            # print(name)
            # if "dumaal" not in name:
            #     continue

            graph   = Graph()
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
            if os.path.isfile(dFileName) == True:
                # continue
                try:
                    dGraph.parse(dFileName,format="turtle")
                except Exception as e:
                    noWork.append(fileName + "-cod.txt")
                    print("error", e)
            else:
                missing.append(fileName + "-cod.txt")


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
            # break
            # print(len(graph))
            # print("========================================")
            graph.serialize(destination=dtnPath + fileName + '.txt', format='turtle')
            # f.write("%s:%d\n" % (name, len(graph)))
            # print("Al:",len(alGraph),"d:",len(dGraph),"g:",len(gGraph))
            # print("index: ",index,"total triples",len(graph))
            index += 1
            numTriples += len(graph)
            # print("number of triples",numTriples)
            # break
    # f.close()
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