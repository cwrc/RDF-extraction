#!/usr/bin/python3
import biography
from bs4 import BeautifulSoup
import rdflib
from rdflib import URIRef

from biography import *
import culturalForm as cf

class PersonName:
    def __init__(self, type,value, uri=None):
        self.uri = None
        self.value = value
        self.typeLabel = create_uri("cwrc",type)
        self.personName = Literal(value)

        if uri:
            self.uri = uri


    def to_triple(self,person):
        global g
        g = rdflib.Graph()
        namespace_manager = rdflib.namespace.NamespaceManager(g)
        bind_ns(namespace_manager, NS_DICT)

        thisNameEntity = make_standard_uri(person.name + " NameEnt " + self.value)

        g.add((thisNameEntity,NS_DICT["rdf"].type, self.typeLabel))
        g.add((thisNameEntity,NS_DICT["rdf"].label, self.personName))

        g.add((person.uri, NS_DICT["cwrc"].hasName,thisNameEntity))
        return g

# temporary function because i think alliyya already has one but i can't find it
def getTheName(tag):
    if "REG" in tag.attrs:
        return tag["REG"]
    else:
        return tag.text
def extract_person_name(xmlString,person):
    root = xmlString.BIOGRAPHY
    personNameList = []
    for name in root.find_all("PERSONNAME"):
        for nickName in name.find_all("NICKNAME"):
            if "NAMECONNOTATION" in nickName.attrs:
                print("name connotation ", nickName["NAMECONNOTATION"])

                property = nickName["NAMECONNOTATION"]
                if property == "ABUSIVE":
                    personNameList.append(PersonName("AbusiveName",getTheName(nickName)))
                elif property == "HONORIFIC":
                    personNameList.append(PersonName("HonorificName",getTheName(nickName)))


            elif "NAMESIGNIFIER" in nickName.attrs:
                print("name signifier ", nickName["NAMESIGNIFIER"])

                property = nickName["NAMESIGNIFIER"]
                if property == "CRYPTIC":
                    personNameList.append(PersonName("CrypticName", getTheName(nickName)))
                elif property == "LOCAL":
                    personNameList.append(PersonName("LocalName", getTheName(nickName)))
                elif property == "ROMANCE":
                    personNameList.append(PersonName("RomanceName", getTheName(nickName)))

            elif "NAMETYPE" in nickName.attrs:
                property = nickName["NAMETYPE"]
                if property == "LITERARY":
                    personNameList.append(PersonName("LiteraryName", getTheName(nickName)))
                elif property == "FAMILIAR":
                    print(nickName)
                    personNameList.append(PersonName("FamiliarName", getTheName(nickName)))
            #     fixme: other class
            #     else:
            # else:
            #     personNameList.append(PersonName("Nickname", "nickname"))

            # print(nickName.name)
    person.name_list = personNameList
def main():
    import os
    filelist = [filename for filename in sorted(os.listdir("bio_data/")) if filename.endswith(".xml")]

    for filename in ["woolvi-b.xml", "blaccl-b.xml"]:
    # for filename in filelist:
        with open("bio_data/" + filename,encoding="utf-8") as f:
            soup = BeautifulSoup(f, 'lxml-xml')

        print("===========",filename,"=============")
        person = Biography(filename[:-6], get_name(soup), cf.get_mapped_term("Gender", get_sex(soup)))
        # education.extract_education_data(soup, person)
        # cf.extract_cf_data(soup, person)
        # person.context_list.clear()
        # other_contexts.extract_health_contexts_data(soup, person)
        extract_person_name(soup,person)

        graph = person.create_triples(person.name_list)
        namespace_manager = rdflib.namespace.NamespaceManager(graph)
        bind_ns(namespace_manager, NS_DICT)
        print(graph.serialize(format='turtle').decode())
        # exit()

if __name__ == "__main__":
    # auth = [env.env("USER_NAME"), env.env("PASSWORD")]
    # login.main(auth)
    # test()
    main()