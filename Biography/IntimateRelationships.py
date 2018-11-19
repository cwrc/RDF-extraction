from utilities import *
from biography import *
import culturalForm as cf
from stringAndMemberFunctions import *
import context

class IntimateRelationships:
    def __init__(self, Person, attrValue):
        self.PersonName =  Person
        self.AttrValue = attrValue

        self.predicate = None
        self.value = None

        if self.AttrValue == "EROTICYES":
            self.predicate = NS_DICT["cwrc"].hasEroticRelationshipWith
            self.value = make_standard_uri(Person)
        elif self.AttrValue == "EROTICNO":
            self.predicate = NS_DICT["cwrc"].hasNonEroticRelationshipWith
            self.value = make_standard_uri(Person)
        elif self.AttrValue == "EROTICPOSSIBLY":
            self.predicate = NS_DICT["cwrc"].hasPossiblyEroticRelationshipWith
            self.value = make_standard_uri(Person)
        else:
            if self.PersonName.title() != "Intimate Relationship":
                self.predicate = NS_DICT["cwrc"].hasIntimateRelationshipWith
                self.value = make_standard_uri(Person)
            else:
                self.predicate = NS_DICT["cwrc"].hasIntimateRelationshipWith
                self.value = make_standard_uri(Person)

    def to_triple(self,person):
        global g
        g = rdflib.Graph()
        namespace_manager = rdflib.namespace.NamespaceManager(g)
        bind_ns(namespace_manager, NS_DICT)
        g.add((person.uri,self.predicate,self.value))
        # spList = []

        # for relationship in intmtRelationships.Persons:


        # listProperties = {}
        # listProperties["subjectName"] = getStandardUri(person.name)
        # listProperties["unchangedName"]= person.name
        # listProperties["descType"] = NS_DICT["cwrc"].IntimateRelationshipsContext
        # listProperties["subjectsObjects"] = spList
        #
        # person.contextCounts["intimateRelationship"] = addContextsNew(person.id, "hasIntimateRelationshipsContext", self.Context,
        #                                     person.uri, person.contextCounts["intimateRelationship"], listProperties)

        return g
def extract_intimate_relationships(xmlString, person):
    root = xmlString.BIOGRAPHY
    irTag = root.find_all('INTIMATERELATIONSHIPS')
    intimateRelationships = []
    sourcePerson = person.name
    id = 1
    for tag in irTag:
        attr = ""

        if "EROTIC" in tag.attrs:
            attr = tag["EROTIC"]
            # print("attr: ", tag.attrib["EROTIC"])
        else:
            attr = "nonErotic"
        for thisPerson in tag.find_all("DIV2"):
            print("======person======")
            print("source: ", sourcePerson)

            context_id = person.id + "_IntimateRelationshipsContext_" + str(id)
            id += 1
            names = getAllNames(thisPerson.find_all("NAME"),person.name)
            if len(names) >= 1:
                print("========>", names[0])
                thisRelationship = IntimateRelationships(names[0], attr)
            else:
                thisRelationship = IntimateRelationships("intimate relationship", attr)

            tempContext = context.Context(context_id,thisPerson,"INTIMATERELATIONSHIPS")
            tempContext.link_triples([thisRelationship])
            intimateRelationships.append(thisRelationship)
            person.context_list.append(tempContext)
            # for name in person.iter("NAME"):
            #     print(name.attrib["STANDARD"])
            # getch()
    # intimateRelationships = IntimateRelationships(personAttrList,intimateContexts)

    person.intimate_relationship_list = intimateRelationships

def create_testcase_dict():
    return [
        {
            "name": "blesma",
            "description": "easy to compare to the personname approved graffle."
        }
    ]

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Extract the Birth/Death information from selection of orlando xml documents', add_help=True)

    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('-testcases', '-t', action="store_true", help="will run through test case list")
    modes.add_argument('-qa', action="store_true", help="will run through qa test cases that are related to https://github.com/cwrc/testData/tree/master/qa")
    modes.add_argument("-f", "-file", "--file", help="single file to run extraction upon")
    modes.add_argument("-d", "-directory", "--directory", help="directory of files to run extraction upon")
    args = parser.parse_args()

    qa_case_files = ["shakwi-b-transformed.xml", "woolvi-b-transformed.xml", "seacma-b-transformed.xml",
                     "atwoma-b-transformed.xml",
                     "alcolo-b-transformed.xml", "bronem-b-transformed.xml", "bronch-b-transformed.xml",
                     "levyam-b-transformed.xml", "aguigr-b-transformed.xml"]
    test_cases = create_testcase_dict()

    if args.file:
        print("Running extraction on " + args.file)
        filelist = [args.file]
    elif args.directory:
        print("Running extraction on files within" + args.directory)
        if args.directory[-1] != "/":
            args.directory += "/"
        filelist = [args.directory +
                    filename for filename in sorted(os.listdir(args.directory)) if filename.endswith(".xml")]
    elif args.qa:
        filelist = sorted(["bio_data/" + filename for filename in qa_case_files])
    elif args.testcases:
        filelist = ["bio_data/" + filename for filename in test_cases.keys()]
    else:
        filelist = [filename for filename in sorted(os.listdir("bio_data")) if filename.endswith(".xml")]

    # # for filename in ["blesma-b.xml"]:
    # # for filename in ["blesma-b.xml"]:
    # # for filename in ["abdyma-b.xml"]:
    # # for filename in ["aikejo-b.xml"]:
    for filename in filelist:
        print("extract " + filename)
        with open(filename, encoding="utf-8") as f:
            soup = BeautifulSoup(f, 'lxml-xml')

        print("===========", filename, "=============")
        person = Biography(filename[:-6], get_name(soup), cf.get_mapped_term("Gender", get_sex(soup)))

        extract_intimate_relationships(soup, person)

        graph = person.create_triples(person.intimate_relationship_list)
        graph += person.create_triples(person.context_list)
        namespace_manager = rdflib.namespace.NamespaceManager(graph)
        bind_ns(namespace_manager, NS_DICT)
        print(graph.serialize(format='turtle').decode())
        # exit()


if __name__ == "__main__":
    # auth = [env.env("USER_NAME"), env.env("PASSWORD")]
    # login.main(auth)
    # test()
    main()