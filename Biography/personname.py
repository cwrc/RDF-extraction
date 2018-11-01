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
        "INDEXED": "IndexedName",
        "MARRIED": "MarriedName",
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
    def __init__(self, types, value, personName, uri=None, extraAttributes=None,parentType=None,otherTriples=None):
        self.id = remove_punctuation("NameEnt " + value)
        self.uri = None
        self.predicate = NS_DICT["cwrc"].hasName                         # used for body in the context sections
        self.value = make_standard_uri(personName + " NameEnt " + value) # used for body in context sections
        self.typeLabels = []
        self.personName = Literal(value)
        self.otherTriples = otherTriples
        for thisType in types:
            self.typeLabels.append(create_uri("cwrc", thisType))


        if uri:
            self.uri = uri

        self.hasSpareGraph = False
        self.spareGraph = None

        if "BirthName" in types:
            self.spareGraph = self.makeBirthGraph(givenNameList=extraAttributes.givenNames,surNameList=extraAttributes.surNames)
            self.hasSpareGraph = True
        if parentType and parentType == "Nickname":
            print("hello")
    #         need to create a mini graph that contains all information regarding their name and stuff

    def makeBirthGraph(self,givenNameList,surNameList):
        g = rdflib.Graph()
        namespace_manager = rdflib.namespace.NamespaceManager(g)
        bind_ns(namespace_manager, NS_DICT)
        # thisNameEntity = make_standard_uri(personName + " NameEnt " + self.value)
        thisNameEntity = self.value

        numPart = 1

        for thisName in givenNameList:
            thisNamePart = make_standard_uri(thisName)
            g.add((thisNamePart, NS_DICT["rdf"].type, NS_DICT["rdf"].Forename))
            g.add((thisNamePart, NS_DICT["cwrc"].hasSortOrder, Literal(numPart)))
            g.add((thisNamePart, NS_DICT["rdf"].label, Literal(thisName)))

            g.add((thisNameEntity, NS_DICT["cwrc"].hasNamePart, thisNamePart))
            numPart += 1

        for thisName in surNameList:
            thisNamePart = make_standard_uri(thisName)
            g.add((thisNamePart, NS_DICT["rdf"].type, NS_DICT["rdf"].Surname))
            g.add((thisNamePart, NS_DICT["cwrc"].hasSortOrder, Literal(numPart)))
            g.add((thisNamePart, NS_DICT["rdf"].label, Literal(thisName)))


            g.add((thisNameEntity, NS_DICT["cwrc"].hasNamePart, thisNamePart))
            numPart += 1

        g.add((thisNameEntity, NS_DICT["rdf"].label, self.personName))

        return g

    def to_triple(self, person):
        global g
        g = rdflib.Graph()
        namespace_manager = rdflib.namespace.NamespaceManager(g)
        bind_ns(namespace_manager, NS_DICT)

        # thisNameEntity = make_standard_uri(person.name + " NameEnt " + self.value)
        thisNameEntity = self.value

        for type in self.typeLabels:
            g.add((thisNameEntity, NS_DICT["rdf"].type, type))

        g.add((thisNameEntity, NS_DICT["rdf"].label, self.personName))

        if self.otherTriples is not None:
            for otherTriple in self.otherTriples:
                g.add((thisNameEntity,otherTriple["predicate"],Literal(otherTriple["value"])))

        g.add((person.uri, NS_DICT["cwrc"].hasName, thisNameEntity))

        if self.hasSpareGraph:
            g += self.spareGraph
        return g


# temporary function because i think alliyya already has one but i can't find it
def getTheName(tag,ignore_reg_value=False):
    if "REG" in tag.attrs and ignore_reg_value == False:
        nameRaw = tag["REG"]
        return nameRaw
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


def makePerson(type, tag, existingList,personName=None):
    types = [type]

    # usefull for birthnames as you have to send the given and surname to the PersonName class
    otherAttributes = None
    otherAttrsReqd = False
    otherTriples = None
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
    elif "MarriedName" in types:
        types.append("Surname")
        name_to_send = getTheName(tag,ignore_reg_value=True)
    elif "IndexedName" in types:
        otherTriples = [
            {
                "predicate" : NS_DICT["cwrc"].IndexedBy,
                "value": "Orlando"
            }
        ]
        name_to_send = getTheName(tag, ignore_reg_value=True)
    elif "PreferredName" in types:
        docText = getTheName(tag,ignore_reg_value=True)
        if ":" in docText:
            name_to_send = docText.split(":")[0]
        else:
            name_to_send = docText
    else:
        name_to_send = getTheName(tag,ignore_reg_value=True)

    if any(person.id == remove_punctuation("NameEnt " + name_to_send) for person in existingList) == False:
        if otherAttrsReqd:
            return PersonName(types, name_to_send, personName, extraAttributes=otherAttributes)
        else:
            return PersonName(types, name_to_send, personName,otherTriples=otherTriples)
    else:
        return None
def extract_person_name(xmlString, person):
    root = xmlString.BIOGRAPHY
    personNameList = []
    stdEntry = makePerson("IndexedName",root.find("STANDARD"),personNameList,personName=person.name)
    if stdEntry:
        personNameList.append(stdEntry)

    docTitle = makePerson("PreferredName",root.find("DOCTITLE"),personNameList,personName=person.name)
    if docTitle:
        personNameList.append(docTitle)

    id = 1
    personNameTags = root.find_all("PERSONNAME")
    if personNameTags == None:
        return
    for name in personNameTags:

        for tagname in basic_layout_dict:
            if tagname == "BIRTHNAME":
                for givenName in name.find_all("BIRTHNAME"):
                    newPerson = makePerson("BirthName", (givenName), personNameList,personName=person.name)
                    if newPerson:
                        personNameList.append(newPerson)
            elif tagname == "NICKNAME":
                for nickname in name.find_all("NICKNAME"):
                    newPerson = makePerson("NickName",nickname,personNameList,personName=person.name)
                    if newPerson:
                        personNameList.append(newPerson)
            else:
                for thisTag in name.find_all(tagname):
                    newPerson = makePerson(basic_layout_dict[tagname], thisTag,personNameList,personName=person.name)
                    if newPerson:
                        personNameList.append(newPerson)


    person.name_list = personNameList
    context_id = person.id + "_PersonNameContext" + str(0)
    tempContext = context.Context(context_id,personNameTags[0],"PersonNameContext")
    tempContext.link_triples(person.name_list[1:])
    person.context_list.append(tempContext)

def main():
    import os
    filelist = [filename for filename in sorted(os.listdir("bio_data/")) if filename.endswith(".xml")]

    for filename in ["woolvi-b.xml"]:
    # for filename in ["blesma-b.xml"]:
    # for filename in ["abdyma-b.xml"]:
    # for filename in ["aikejo-b.xml"]:
    # for filename in filelist:
        with open("bio_data/" + filename, encoding="utf-8") as f:
            soup = BeautifulSoup(f, 'lxml-xml')

        print("===========", filename, "=============")
        person = Biography(filename[:-6], get_name(soup), cf.get_mapped_term("Gender", get_sex(soup)))

        extract_person_name(soup, person)

        graph = person.create_triples(person.name_list)
        # graph += person.create_triples(person.context_list)
        namespace_manager = rdflib.namespace.NamespaceManager(graph)
        bind_ns(namespace_manager, NS_DICT)
        print(graph.serialize(format='turtle').decode())
        # exit()


if __name__ == "__main__":
    # auth = [env.env("USER_NAME"), env.env("PASSWORD")]
    # login.main(auth)
    # test()
    main()
