
from rdflib import RDF
from rdflib import Graph
import os


def main():
    root = "~/Documents/UoGuelph Projects/CombiningTriples/"
    aPath       = os.path.expanduser(root + "culturalform_triples/")
    gPath       = os.path.expanduser(root + "birthDeathFamily_triples/")
    dPath       = os.path.expanduser(root + "dTriples/")
    dtnPath     = os.path.expanduser(root + "CombinedFiles/")

    index = 1
    numTriples = 0
    print(gPath)
    for dirName, subdirlist, files in os.walk(gPath):
        for name in files:
            print(name)
            # if "levyam" not in name:
            #     continue

            graph = Graph()
            fileName = name[0:-4]
            alFileName = aPath + fileName + "-cf.txt"
            gFileName = gPath + name
            # dFileName = dPath + fileName + "-cod.txt"
            # graph.parse(dFileName,format="turtle")

            print(name[0:-4],os.path.isfile(alFileName),alFileName)

            if(os.path.isfile(alFileName)) == False:
                continue
            # if(os.path.isfile(dFileName)):
            #     graph.parse(dFileName,format="turtle")
            #     print("got one from deb")
            #     debNum += 1

            graph.parse(alFileName,format="turtle")
            # graph.parse(dFileName,format="turtle")

            graph.parse(gFileName,format="turtle")
            # print(graph.serialize(format='turtle').decode())
            # break
            # print(len(graph))
            # print("========================================")
            graph.serialize(destination=dtnPath + fileName + '.txt', format='turtle')

            print(index)
            index += 1
            numTriples += len(graph)
            # break
    print("total Triples: ",numTriples)

if __name__ == '__main__':
    main()