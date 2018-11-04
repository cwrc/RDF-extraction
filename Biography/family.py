from utilities import *
import os, csv
# from rdflib import RDF, RDFS, Literal, URIRef, BNode, Graph
# th eline below imports from classes.py which imports from the line above
from stringAndMemberFunctions import *
from biography import *
import culturalForm as cf

def getCwrcTag(familyRelation):
    csvFile = open(os.path.expanduser("relationshipPredicates.csv"), "r")

    cwrcTag = 'CWRC_Tag'
    orlandoTag = 'Orlando_Relation'

    fileContent = csv.DictReader(csvFile)

    for row in fileContent:
        if row[orlandoTag] == familyRelation:
            return row[cwrcTag]
class Family:
    def __init__(self, memName, memRLTN, memJobs, memSigActs):
        if memName == "":
            self.isNoName = True
        else:
            self.isNoName = False
        self.noNameLetter = ''
        self.memberName = memName
        self.memberRelation = memRLTN
        self.memberJobs = list(memJobs)
        self.memberSigActs = list(memSigActs)

    def to_triple(self, person):
        global g
        g = rdflib.Graph()
        namespace_manager = rdflib.namespace.NamespaceManager(g)
        bind_ns(namespace_manager, NS_DICT)
        sourceName = remove_punctuation(person.name)
        memberName = self.memberName
        print("=======", memberName, "=========")
        # FIXME : name rearranement removed to match alliyya's code
        # if ',' in memberName:
        #     splitName = memberName.split(",")
        #     memberName = splitName[1].strip() + " " + splitName[0].strip()
        # memberName = remove_punctuation(memberName)
        memberSource = URIRef(str(NS_DICT["data"]) + remove_punctuation(memberName))
        if self.isNoName:
            if self.noNameLetter == "":
                # print(sourceName, memberName)
                # if self.memberRelation == "UNCLE":
                #     if (source, URIRef(str(NS_DICT["cwrc"]) + "hasUncle"),None) in g:
                #         print("multipleUncles")
                #     print(self.memberRelation)
                memberSource = URIRef(
                    str(NS_DICT["data"]) + sourceName.replace(" ", "_") + "_" + self.memberRelation.lower().title())

            else:
                memberSource = URIRef(str(NS_DICT["data"]) + sourceName.replace(" ",
                                                                                "_") + "_" + self.memberRelation.lower().title() + "_" + self.noNameLetter)

        else:
            g.add((memberSource, NS_DICT["foaf"].name, Literal(memberName)))

        g.add((memberSource, RDF.type, NS_DICT["cwrc"].NaturalPerson))

        for jobs in self.memberJobs:
            if jobs.job == "":
                continue
            if jobs.predicate == "familyOccupation":
                predicate = NS_DICT["cwrc"].hasFamilyBasedOccupation
            else:
                predicate = NS_DICT["cwrc"].hasPaidOccupation

            # FIXME : change jobs to jogs.job in order to make the thing work. right now, it is not functional.

            # if jobs in occupations:
            #     g.add((memberSource, predicate, Literal(occupations[jobs.job].title())))
            # else:
            g.add((memberSource, predicate, Literal(jobs.job.strip().title())))
            # print("added job ", jobs)

        for sigActs in self.memberSigActs:
            if sigActs.job == "":
                continue
            if sigActs.predicate == "volunteerOccupation":
                predicate = NS_DICT["cwrc"].hasVolunteerOccupation
            else:
                predicate = NS_DICT["cwrc"].hasOccupation

            g.add((memberSource, predicate, Literal(sigActs.job.strip().title())))
            # print("added significant ", sigActs)

        cwrcTag = getCwrcTag(self.memberRelation)

        predicate = URIRef(str(NS_DICT["cwrc"]) + cwrcTag)
        # g.add((source,predicate,Literal(memberName)))
        g.add((person.uri, predicate, memberSource))
        return g

    def samplePrint(self):
        print("......................\nName: ", self.memberName, "\nRelation: ", self.memberRelation)
        print("Jobs: ", end="")
        print(*self.memberJobs, sep=", ")
        print("SigAct: ", end="")
        print(*self.memberSigActs, sep=", ")


# This function obtains family information
# ------ Example ------
# Name:  Grant, Josceline Charles Henry
# Relation:  FATHER
# Jobs: army officer
# SigAct: lost money, currency committee
def extract_family(xmlString, person):
    global numSigs
    global numAdded

    myRoot2 = xmlString.BIOGRAPHY
    # SOURCENAME = myRoot2.newFindFunc("DIV0 STANDARD").text
    SOURCENAME = findTag(myRoot2, "DIV0 STANDARD").text
    listOfMembers = []
    fams = myRoot2.find_all('FAMILY')
    for familyTag in myRoot2.find_all('FAMILY'):

        # --------------------------------- Get husband and wife ---------------------------------
        for familyMember in familyTag.find_all("MEMBER"):
            if familyMember['RELATION'] in ["HUSBAND", "WIFE"]:
                if len(familyMember.find_all()) == 1:
                    continue
                else:
                    listOfMembers = getMemberInfo(familyMember, listOfMembers, SOURCENAME)

        # --------------------------------- get children ---------------------------------
        for familyMember in familyTag.find_all("MEMBER"):
            if familyMember['RELATION'] in ["SON", "DAUGHTER", "STEPSON", "STEPDAUGHTER"]:
                if len(familyMember.find_all()) == 1:
                    continue
                else:
                    listOfMembers = getMemberChildInfo(familyMember, listOfMembers, SOURCENAME)

        # --------------------------------- get others ---------------------------------
        for familyMember in familyTag.find_all('MEMBER'):
            finds = familyMember.find_all()
            if familyMember['RELATION'] in ["HUSBAND", "WIFE", "SON", "DAUGHTER", "STEPSON", "STEPDAUGHTER"] or len(
                    iterListAll(familyMember)) == 1:
                continue
            else:
                listOfMembers = getMemberInfo(familyMember, listOfMembers, SOURCENAME)

    print("----------- ", SOURCENAME.strip(), "'s Family Members -----------")
    # printMemberInfo(listOfMembers)
    # print("")
    # return rearrangeSourceName(SOURCENAME),listOfMembers
    # return SOURCENAME,listOfMembers
    person.family_list = listOfMembers

def main():

    filelist = [filename for filename in sorted(os.listdir("bio_data/")) if filename.endswith(".xml")]

    for filename in ["blesma-b.xml"]:
        # for filename in ["blesma-b.xml"]:
        # for filename in ["abdyma-b.xml"]:
        # for filename in ["aikejo-b.xml"]:
        # for filename in filelist:
        with open("bio_data/" + filename, encoding="utf-8") as f:
            soup = BeautifulSoup(f, 'lxml-xml')

        print("===========", filename, "=============")
        person = Biography(filename[:-6], get_name(soup), cf.get_mapped_term("Gender", get_sex(soup)))

        extract_family(soup, person)

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