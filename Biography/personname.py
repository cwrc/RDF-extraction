#!/usr/bin/python3
import biography
from bs4 import BeautifulSoup
import rdflib
from rdflib import URIRef

from biography import *
import culturalForm as cf
import context

class BirthName:
    def __init__(self,gvnNames,srNames,personName):
        self.givenNames = gvnNames
        self.surNames = srNames
        self.personName = personName

class PersonName:
    def __init__(self, types,value, uri=None,extraAttributes=None):
        self.uri = None
        self.value = value
        self.typeLabels = []

        for thisType in types:
            self.typeLabels.append(create_uri("cwrc",thisType))

        self.personName = Literal(value)

        if uri:
            self.uri = uri

        self.hasSpareGraph = False
        self.spareGraph = None

        if "BirthName" in types:
            print("hello")
            givenNameList = extraAttributes.givenNames
            surNameList = extraAttributes.surNames

            g = rdflib.Graph()
            namespace_manager = rdflib.namespace.NamespaceManager(g)
            bind_ns(namespace_manager, NS_DICT)
            thisNameEntity = make_standard_uri(extraAttributes.personName + " NameEnt " + self.value)

            numPart = 1
            # if len(givenNameList) > 1:
            for thisName in givenNameList:
                thisNamePart = make_standard_uri(thisName)
                g.add((thisNamePart,NS_DICT["rdf"].type,NS_DICT["rdf"].Forename))
                g.add((thisNamePart,NS_DICT["cwrc"].hasSortOrder,Literal(numPart)))

                g.add((thisNameEntity,NS_DICT["cwrc"].hasNamePart, thisNamePart))
                numPart += 1
            # else:
            #     g.add((thisNameEntity, NS_DICT["cwrc"].hasNamePart, Literal(givenNameList[0])))

            # if len(surNameList) > 1:

            for thisName in surNameList:
                thisNamePart = make_standard_uri(thisName)
                g.add((thisNamePart, NS_DICT["rdf"].type, NS_DICT["rdf"].Surname))
                g.add((thisNamePart, NS_DICT["cwrc"].hasSortOrder, Literal(numPart)))

                g.add((thisNameEntity, NS_DICT["cwrc"].hasNamePart, thisNamePart))
                numPart += 1
            # else:
            #     g.add((thisNameEntity, NS_DICT["cwrc"].hasNamePart, Literal(surNameList[0])))


            g.add((thisNameEntity, NS_DICT["rdf"].label, self.personName))

            self.spareGraph = g
            self.hasSpareGraph = True
    #         need to create a mini graph that contains all information regarding their name and stuff



    def to_triple(self,person):
        global g
        g = rdflib.Graph()
        namespace_manager = rdflib.namespace.NamespaceManager(g)
        bind_ns(namespace_manager, NS_DICT)

        thisNameEntity = make_standard_uri(person.name + " NameEnt " + self.value)

        for type in self.typeLabels:
            g.add((thisNameEntity,NS_DICT["rdf"].type, type))

        g.add((thisNameEntity,NS_DICT["rdf"].label, self.personName))

        g.add((person.uri, NS_DICT["cwrc"].hasName,thisNameEntity))

        if self.hasSpareGraph:
            g += self.spareGraph
        return g

# temporary function because i think alliyya already has one but i can't find it
def getTheName(tag):
    if "REG" in tag.attrs:
        nameRaw = tag["REG"]
        return tag["REG"]
    else:
        # print(tag.find_all(text=True, recursive=False))
        # print(tag.text)
        return tag.text.replace("\n"," ").strip()
def getGivenAndSurNames(tag):
    allGivenNames = []
    allSurNames = []

    for gName in tag.find_all("GIVEN"):
        allGivenNames.append(getTheName(gName))

    for sName in tag.find_all("SURNAME"):
        allSurNames.append(getTheName(sName))

    return allGivenNames,allSurNames

def makePerson(type,tag,personName=None):
    types = [type]

    otherAttributes = None
    otherAttrsReqd = False

    if "WROTEORPUBLISHEDAS" in tag.attrs:
        types.append("AuthorialName")

    if "BirthName" in types:
        givenNames,surNames = getGivenAndSurNames(tag)
        otherAttrsReqd = True
        otherAttributes = BirthName(givenNames,surNames,personName)

    if otherAttrsReqd:
        return PersonName(types,getTheName(tag),extraAttributes=otherAttributes)
    else:
        return PersonName(types,getTheName(tag))

def extract_person_name(xmlString,person):
    root = xmlString.BIOGRAPHY
    personNameList = []
    name_type_dict = {
        "ABUSIVE": "AbusiveName",
        "HONORIFIC": "HonorificName",
        "CRYPTIC": "CrypticName",
        "LOCAL": "LocalName",
        "ROMANCE": "RomanceName",
        "LITERARY": "LiteraryName",
        "FAMILIAR": "FamiliarName",
    }
    # Subelement : type
    basic_layout_dict = {
        "RELIGIOUS": "religiousName",
        "ROYAL": "royalName",
        "SELFCONSTRUCTED": "selfConstructedName",
        "STYLED": "styledName",
        "TITLE": "titledName"
    }
    id = 1
    for name in root.find_all("PERSONNAME"):
        # context_id = person.id + "_PersonNameContext_" + str(id)
        # tempContext = context.Context(context_id, name, 'PERSONNAME')
        # tempContext.link_triples(person.deathObj.death_list)
        # person.context_list.append(tempContext)

        for nickName in name.find_all("NICKNAME"):
            if "NAMECONNOTATION" in nickName.attrs:
                property = nickName["NAMECONNOTATION"]
                print("name connotation ", property)
                if property in name_type_dict:
                    personNameList.append(makePerson(name_type_dict[property], (nickName)))

            elif "NAMESIGNIFIER" in nickName.attrs:
                property = nickName["NAMESIGNIFIER"]
                print("name signifier ", property)
                if property in name_type_dict:
                    personNameList.append(makePerson(name_type_dict[property], (nickName)))

            elif "NAMETYPE" in nickName.attrs:
                property = nickName["NAMETYPE"]
                print("name type ", property)
                if property in name_type_dict:
                    personNameList.append(makePerson(name_type_dict[property], (nickName)))

            #     fixme: other class
            #     else:
            # else:
            #     personNameList.append(makePerson("Nickname", "nickname"))

            # print(nickName.name)
        for pseudoNym in name.find_all("PSEUDONYM"):
            personNameList.append(makePerson("pseudonym", pseudoNym))

        for givenName in name.find_all("BIRTHNAME"):
            personNameList.append(makePerson("BirthName", (givenName),personName=person.name))

        # doing nothing for now as according to the personname spread sheet
        # for surName in name.find_all("PROFESSIONLTITLE"):
        #     personNameList.append(makePerson("Surname", (surName)))

        # for surName in name.find_all("INDEXED"):
        #     personNameList.append(makePerson("Surname", (surName)))

        # for surName in name.find_all("MARRIED"):
        #     personNameList.append(makePerson("Surname", (surName)))


    person.name_list = personNameList
def main():
    import os
    filelist = [filename for filename in sorted(os.listdir("bio_data/")) if filename.endswith(".xml")]

    # for filename in ["abdyma-b.xml","woolvi-b.xml", "blaccl-b.xml"]:
    # for filename in ["blesma-b.xml"]:
    for filename in ["abdyma-b.xml"]:
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

        # graph = person.to_graph()
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