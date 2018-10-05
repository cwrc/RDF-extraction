#!/usr/bin/python3
import biography
from bs4 import BeautifulSoup
import rdflib
from rdflib import URIRef

from biography import *
import culturalForm as cf
import context

basic_layout_dict = {
        "NICKNAME": {
            "ABUSIVE": "AbusiveName",
            "HONORIFIC": "HonorificName",
            "CRYPTIC": "CrypticName",
            "LOCAL": "LocalName",
            "ROMANCE": "RomanceName",
            "LITERARY": "LiteraryName",
            "FAMILIAR": "FamiliarName",
        },
        "PSEUDONYM": "pseudonym",
        "BIRTHNAME": "BirthName",
        # "PROFESSIONALTITLE": None,
        # "INDEXED": None,
        "MARRIED": "Married",
        "RELIGIOUS": "religiousName",
        "ROYAL": "royalName",
        "SELFCONSTRUCTED": "selfConstructedName",
        "STYLED": "styledName",
        "TITLE": "titledName"
    }
class BirthName:

    def __init__(self, gvnNames, srNames, personName):
        self.givenNames = gvnNames
        self.surNames = srNames
        self.personName = personName


class PersonName:
    def __init__(self, types, value, uri=None, extraAttributes=None,parentType=None):
        self.uri = None
        self.value = value
        self.typeLabels = []
        self.graph = None

        for thisType in types:
            self.typeLabels.append(create_uri("cwrc", thisType))

        self.personName = Literal(value)

        if uri:
            self.uri = uri

        self.hasSpareGraph = False
        self.spareGraph = None

        if "BirthName" in types:
            self.spareGraph = self.makeBirthGraph(givenNameList=extraAttributes.givenNames,surNameList=extraAttributes.surNames,
                                                  personName=extraAttributes.personName)
            self.hasSpareGraph = True
        if parentType and parentType == "Nickname":
            print("hello")
    #         need to create a mini graph that contains all information regarding their name and stuff

    def makeBirthGraph(self,givenNameList,surNameList,personName):
        g = rdflib.Graph()
        namespace_manager = rdflib.namespace.NamespaceManager(g)
        bind_ns(namespace_manager, NS_DICT)
        thisNameEntity = make_standard_uri(personName + " NameEnt " + self.value)

        numPart = 1

        for thisName in givenNameList:
            thisNamePart = make_standard_uri(thisName)
            g.add((thisNamePart, NS_DICT["rdf"].type, NS_DICT["rdf"].Forename))
            g.add((thisNamePart, NS_DICT["cwrc"].hasSortOrder, Literal(numPart)))

            g.add((thisNameEntity, NS_DICT["cwrc"].hasNamePart, thisNamePart))
            numPart += 1

        for thisName in surNameList:
            thisNamePart = make_standard_uri(thisName)
            g.add((thisNamePart, NS_DICT["rdf"].type, NS_DICT["rdf"].Surname))
            g.add((thisNamePart, NS_DICT["cwrc"].hasSortOrder, Literal(numPart)))

            g.add((thisNameEntity, NS_DICT["cwrc"].hasNamePart, thisNamePart))
            numPart += 1

        g.add((thisNameEntity, NS_DICT["rdf"].label, self.personName))

        return g

    def to_triple(self, person):
        global g
        g = rdflib.Graph()
        namespace_manager = rdflib.namespace.NamespaceManager(g)
        bind_ns(namespace_manager, NS_DICT)

        thisNameEntity = make_standard_uri(person.name + " NameEnt " + self.value)

        for type in self.typeLabels:
            g.add((thisNameEntity, NS_DICT["rdf"].type, type))

        g.add((thisNameEntity, NS_DICT["rdf"].label, self.personName))

        g.add((person.uri, NS_DICT["cwrc"].hasName, thisNameEntity))

        if self.hasSpareGraph:
            g += self.spareGraph
        return g


# temporary function because i think alliyya already has one but i can't find it
def getTheName(tag,ignore_reg_value=False):
    if "REG" in tag.attrs and ignore_reg_value == False:
        nameRaw = tag["REG"]
        return tag["REG"]
    else:
        # print(tag.find_all(text=True, recursive=False))
        # print(tag.text)
        return tag.text.replace("\n", " ").strip()


def getGivenAndSurNames(tag):
    allGivenNames = []
    allSurNames = []

    for gName in tag.find_all("GIVEN"):
        allGivenNames.append(getTheName(gName))

    for sName in tag.find_all("SURNAME"):
        allSurNames.append(getTheName(sName))

    return allGivenNames, allSurNames


def makePerson(type, tag, personName=None,parentType=None):
    types = [type]

    # usefull for birthnames as you have to send the given and surname to the PersonName class
    otherAttributes = None
    otherAttrsReqd = False
    name_to_send = ""

    if "WROTEORPUBLISHEDAS" in tag.attrs:
        types.append("AuthorialName")

    if "BirthName" in types:
        givenNames, surNames = getGivenAndSurNames(tag)
        otherAttrsReqd = True
        otherAttributes = BirthName(givenNames, surNames, personName)
        name_to_send = getTheName(tag)
    elif "NickName" in types:
        name_type_dict = basic_layout_dict["NICKNAME"]
        if "NAMECONNOTATION" in tag.attrs:
            property = tag["NAMECONNOTATION"]
            print("name connotation ", property)
            if property in name_type_dict:
                types.append(name_type_dict[property])
                name_to_send = getTheName(tag)

        elif "NAMESIGNIFIER" in tag.attrs:
            property = tag["NAMESIGNIFIER"]
            print("name signifier ", property)
            if property in name_type_dict:
                types.append(name_type_dict[property])
                name_to_send = getTheName(tag)

        elif "NAMETYPE" in tag.attrs:
            property = tag["NAMETYPE"]
            print("name type ", property)
            if property in name_type_dict:
                types.append(name_type_dict[property])
                name_to_send = getTheName(tag)
    elif "Married" in types:
        types.append("Surname")
        name_to_send = getTheName(tag,ignore_reg_value=True)
        # fixme: other class
        #     else:
        # else:
        #     personNameList.append(makePerson("Nickname", "nickname"))
    else:
        name_to_send = getTheName(tag,ignore_reg_value=True)
    if otherAttrsReqd:
        return PersonName(types, name_to_send, extraAttributes=otherAttributes)
    else:
        return PersonName(types, name_to_send)

def extract_person_name2(xmlString,person):
    root = xmlString.BIOGRAPHY
    personNameList = []

    # Subelement : type

    id = 1
    for name in root.find_all("PERSONNAME"):

        for tagname in basic_layout_dict:
            if tagname == "BIRTHNAME":
                for givenName in name.find_all("BIRTHNAME"):
                    personNameList.append(makePerson("BirthName", (givenName), personName=person.name))
            elif tagname == "NICKNAME":
                for nickname in name.find_all("NICKNAME"):
                    personNameList.append(makePerson("NickName",nickname))
            else:
                for thisTag in name.find_all(tagname):
                    personNameList.append(makePerson(basic_layout_dict[tagname], thisTag))

    person.name_list = personNameList

def extract_person_name(xmlString, person):
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
                    personNameList.append(makePerson(name_type_dict[property], nickName))

            elif "NAMESIGNIFIER" in nickName.attrs:
                property = nickName["NAMESIGNIFIER"]
                print("name signifier ", property)
                if property in name_type_dict:
                    personNameList.append(makePerson(name_type_dict[property], nickName))

            elif "NAMETYPE" in nickName.attrs:
                property = nickName["NAMETYPE"]
                print("name type ", property)
                if property in name_type_dict:
                    personNameList.append(makePerson(name_type_dict[property], nickName))

            #     fixme: other class
            #     else:
            # else:
            #     personNameList.append(makePerson("Nickname", "nickname"))

            # print(nickName.name)
        for pseudoNym in name.find_all("PSEUDONYM"):
            personNameList.append(makePerson("pseudonym", pseudoNym))

        for givenName in name.find_all("BIRTHNAME"):
            personNameList.append(makePerson("BirthName", (givenName), personName=person.name))

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
        with open("bio_data/" + filename, encoding="utf-8") as f:
            soup = BeautifulSoup(f, 'lxml-xml')

        print("===========", filename, "=============")
        person = Biography(filename[:-6], get_name(soup), cf.get_mapped_term("Gender", get_sex(soup)))
        # education.extract_education_data(soup, person)
        # cf.extract_cf_data(soup, person)
        # person.context_list.clear()
        # other_contexts.extract_health_contexts_data(soup, person)

        # extract_person_name(soup, person)
        extract_person_name2(soup,person)

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
