import rdflib
import os
import re
import datetime
import urllib
import csv

try:
    from Utils.place import Place, PLACE_MAP
except ModuleNotFoundError as e:
    from . import Place, PLACE_MAP

"""
TODO: Add doctests for:
- strip_all_whitespace
- remove_punctuation
- get_name_uri
- make_standard_uri
- create_uri
- create_cwrc_uri
- get_value
- get_attribute
- get_reg
- get_people
- get_titles
- get_places

TODO: parse required ns from external files
"""
WRITER_MAP = {}
MAX_WORD_COUNT = 35

PERSON_MAP = {}
ORGANIZATION_MAP = {} # Publishers for now but this will be expanded

NS_DICT = {
    "cwrc": rdflib.Namespace("http://id.lincsproject.ca/cwrc/"),
    "occupation": rdflib.Namespace("http://id.lincsproject.ca/occupation/"),
    "ii": rdflib.Namespace("http://id.lincsproject.ca/ii/"),
    "genre": rdflib.Namespace("http://id.lincsproject.ca/genre/"),
    "cwrc_temp": rdflib.Namespace("http://temp.lincsproject.ca/cwrc/"),
    "frbroo": rdflib.Namespace("http://iflastandards.info/ns/fr/frbr/frbroo/"),
    "as": rdflib.Namespace("http://www.w3.org/ns/activitystreams#"),
    "bibo": rdflib.Namespace("http://purl.org/ontology/bibo/"),
    "biro": rdflib.Namespace("http://purl.org/spar/biro/"),
    "bio": rdflib.Namespace("http://purl.org/vocab/bio/0.1/"),
    "bf": rdflib.Namespace("http://id.loc.gov/ontologies/bibframe/"),
    "cc": rdflib.Namespace("http://creativecommons.org/ns#"),
    "cito": rdflib.Namespace("http://purl.org/spar/cito/"),
    "crm": rdflib.Namespace("http://www.cidoc-crm.org/cidoc-crm/"),
    "crmdig": rdflib.Namespace("http://www.ics.forth.gr/isl/CRMdig/"),
    "data": rdflib.Namespace("http://cwrc.ca/cwrcdata/"),
    "dbpedia": rdflib.Namespace("http://dbpedia.org/resource/"),
    "dcterms": rdflib.Namespace("http://purl.org/dc/terms/"),
    "dctypes": rdflib.Namespace("http://purl.org/dc/dcmitype/"),
    "eurovoc": rdflib.Namespace("http://eurovoc.europa.eu/"),
    "foaf": rdflib.Namespace("http://xmlns.com/foaf/0.1/"),
    "geonames": rdflib.Namespace("http://sws.geonames.org/"),
    "gvp": rdflib.Namespace("http://vocab.getty.edu/ontology#"),
    "loc": rdflib.Namespace("http://id.loc.gov/vocabulary/relators/"),
    "oa": rdflib.Namespace("http://www.w3.org/ns/oa#"),
    "org": rdflib.Namespace("http://www.w3.org/ns/org#"),
    "owl": rdflib.Namespace("http://www.w3.org/2002/07/owl#"),
    "prov": rdflib.Namespace("http://www.w3.org/ns/prov#"),
    "prism": rdflib.Namespace("http://prismstandard.org/namespaces/1.2/basic/"),
    "rdf": rdflib.Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#"),
    "rdfs": rdflib.Namespace("http://www.w3.org/2000/01/rdf-schema#"),
    "sem": rdflib.Namespace("http://semanticweb.cs.vu.nl/2009/11/sem/"),
    "schema": rdflib.Namespace("http://schema.org/"),
    "skos": rdflib.Namespace("http://www.w3.org/2004/02/skos/core#"),
    "skosxl": rdflib.Namespace("http://www.w3.org/2008/05/skos-xl#"),
    "time": rdflib.Namespace("http://www.w3.org/2006/time#"),
    "vann": rdflib.Namespace("http://purl.org/vocab/vann/"),
    "voaf": rdflib.Namespace("http://purl.org/vocommons/voaf#"),
    "void": rdflib.Namespace("http://rdfs.org/ns/void#"),
    "vs": rdflib.Namespace("http://www.w3.org/2003/06/sw-vocab-status/ns#")
}

class Extraction(object):
    """docstring for Extraction"""

    def __init__(self, file_dict, name, verbosity=None, format=None, output=None, pause=None, sparql_endpoint=None, logger=None):
        super(Extraction, self).__init__()
        self.file_dict = file_dict
        self.verbosity = verbosity
        self.format = format or "ttl"
        self.output = output
        self.pause = pause

        self.sparql_endpoint = sparql_endpoint

        if logger:
            self.logger = logger
        else:
            self.logger = config_logger2(name, verbosity)

        if self.format in ["rdf", "rdf/xml"]:
            self.format = "pretty-xml"
        elif self.format == "turtle":
            self.format = "ttl"

    def __str__(self):
        string = ""
        string += "file_dict: " + str(self.file_dict) + "\n"
        string += "verbosity: " + str(self.verbosity) + "\n"
        string += "format: " + str(self.format) + "\n"
        string += "output: " + str(self.output) + "\n"
        string += "pause: " + str(self.pause) + "\n"
        string += "sparql_endpoint: " + str(self.sparql_endpoint) + "\n"
        string += "logger: " + str(self.logger) + "\n"
        return string


class GeneralRelation(object):
    """docstring for GeneralRelation"""

    def __init__(self, pred, obj):
        super(GeneralRelation, self).__init__()
        self.predicate = pred
        self.object = obj

    def __str__(self):
        string = ""
        string += "\t\tPredicate: " + str(self.predicate) + "\n"
        string += "\t\tObject: " + str(self.object) + "\n"
        return string

    def to_triple(self, context):
        g = create_graph()
        g.add((context.uri, self.predicate, self.object))
        return g

def get_entry_id(tag):
    return tag.find_parent("ENTRY").get("ID")

def remove_unwanted_tags(tag):
    unwanted_tag_names = ["BIBCITS", "RESPONSIBILITIES", "KEYWORDCLASSES","RESEARCHNOTE"]
    unwanted_tags = []
    for x in unwanted_tag_names:
        unwanted_tags += tag.find_all(x)

    for x in unwanted_tags:
        x.decompose()


def create_writer_map(path=None):
    if not path:
        path = '../data/writers_sex.csv'
    with open(path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        for row in reader:
            if row[0] not in WRITER_MAP:
                WRITER_MAP[row[0]] = {"ID": row[1], "SEX": row[2]}

def create_person_map(path=None):
    if not path:
        path = '../data/people_mapping.csv'
    with open(path) as f:
        csvfile = csv.reader(f)
        for row in csvfile:
            PERSON_MAP[row[0]] = row[1]

def create_org_map(path=None):
    if not path:
        path = '../data/publisher_mapping.csv'
    with open(path) as f:
        csvfile = csv.reader(f)
        for row in csvfile:
            PERSON_MAP[row[0]] = row[1]
    

create_writer_map()
create_person_map()
create_org_map()
    



def get_current_time():
    return datetime.datetime.now().strftime("%d %b %Y %H:%M:%S")


def create_graph():
    """ Returns graph with necessary namespace
    """
    g = rdflib.Graph()
    namespace_manager = rdflib.namespace.NamespaceManager(g)
    bind_ns(namespace_manager, NS_DICT)
    return g


def bind_ns(namespace_manager, ns_dictionary):
    for x in ns_dictionary.keys():
        namespace_manager.bind(x, ns_dictionary[x], override=False)


"""Some string manipulation functions"""


def strip_all_whitespace(string):
    # temp function for condensing the context strings for visibility in testing
    return re.sub('[\s+]', '', str(string))


def split_by_casing(string):
    return " ".join(re.findall('^[a-z]+|[A-Z][^A-Z]*', string))



# TODO: May want to use: urllib.parse.quote_plus(string) to encode string
def remove_punctuation(temp_str, all=False):
    import string
    from unidecode import unidecode
    if all:
        translator = str.maketrans('', '', string.punctuation)
    else:
        translator = str.maketrans('', '', string.punctuation.replace("-", ""))
    temp_str = temp_str.translate(translator)
    temp_str = temp_str.replace(" ", "_")
    # TODO: Need to revise this method to handle titles with weird unicode ex.
    # Public Confessions of a Middle-Aged Woman Aged 55 ¾
    temp_str = temp_str.replace("¾", "3-4")
    temp_str = temp_str.replace("©", "c")
    temp_str = temp_str.replace("Ã", "A")
    return unidecode(temp_str)


def get_entry_stdname(tag):
    """ returns standard name of person's entry given any tag"""
    return tag.find_parent("DIV0").STANDARD.text

def limit_words(string, word_count):
    """Returns a string of a given word count size.

    >>> limit_words("This is a sample string", 2)
    'This is...'

    >>> limit_words("This is a sample string", 10)
    'This is a sample string'

    >>> limit_words("This is a sample string", -1)
    Traceback (most recent call last):
        ...
    AssertionError: Invalid word count!
    """
    assert(word_count > 0), "Invalid word count!"

    text = " ".join(str(string).split())
    words = text.split(" ")
    text = " ".join(words[:word_count])
    if len(words) > word_count:
        text += "..."
    return text


def limit_to_full_sentences(string, max):
    # logger.info("\n" + string)
    string = string.strip()
    if string == "":
        return string
    sentences = string.split(".")
    text = ""
    for x in sentences:
        if text.count(" ") < max:
            text += x.strip()
            if text[-1] != ".":
                text += "."
        else:
            break

    return text.replace(".  .", ". ")


"""
    Series of functions to do with the creation of URI
"""


def get_name_uri(tag):
    """Creates a uri based on the standard attribute of a tag if ref attribute not present"""
    uri = tag.get("REF")
    if not uri:
        try:
            return make_standard_uri(tag.get("STANDARD"))
        except AttributeError:
            if tag.get_text():
                logger.warning(F"Name missing identifier: {tag}")
                return make_standard_uri(tag.get_text())
                
    else:
        if uri in PERSON_MAP:
            uri = PERSON_MAP[uri]
        
        return rdflib.term.URIRef(uri)


def make_standard_uri(std_str, ns="data"):
    """Makes uri based of string, removes punctuation and replaces spaces with an underscore
    v2, leaving hypens
    """
    return create_uri(ns, remove_punctuation(std_str))


def create_uri(prefix, term):
    """prepends the provided namespace uri to the given term"""
    return rdflib.term.URIRef(str(NS_DICT[prefix]) + term)


def create_cwrc_uri(term):
    # TODO deprecate this method in favour of less verbose equivalent above
    """prepends the cwrc namespace uri to the given term"""
    return create_uri("cwrc", term)


def get_value(tag):
    value = get_attribute(tag, "STANDARD")
    if tag.name == "GENDER":
        value = get_attribute(tag, "GENDERIDENTITY")
    if not value:
        value = get_attribute(tag, "REG")
    if not value:
        value = get_attribute(tag, "CURRENTALTERNATIVETERM")
    if not value:
        value = str(tag.text)
        value = ' '.join(value.split())
    
    return value.strip()


def get_attribute(tag, attribute):
    """Extract a specific attribute"""
    value = tag.get(attribute)
    if value:
        return value
    return None


def get_reg(tag):
    return get_attribute(tag, "REG")

def get_other_people(tag, author):
    """returns all people other than author"""
    return list(filter(lambda a: a != author.uri, get_people(tag)))

def get_people(tag):
    """Returns all people within a given tag"""
    return list(set([get_name_uri(x) for x in tag.find_all("NAME")]))


def get_title_uri(tag):
    title = get_value(tag)
    return make_standard_uri(title + " TITLE", ns="data")

def get_titles(tag):
    """Returns all titles within a given tag TODO Mapping"""
    titles = []
    for x in tag.find_all("TITLE"):
        titles.append(get_title_uri(x))
    return titles


def get_places(tag):
    """Returns all places uris within a given tag""" 
    return [Place(x).uri for x in tag.find_all("PLACE") if Place(x).uri != None]


def get_place_strings(tag):
    """Returns all places strings within a given tag"""
    places = []
    for x in tag.find_all("PLACE"):
        places.append(x.text)
    return places


def get_name(entry):
    name = entry.find("STANDARD")
    if name:
        return name.text
    else:
        return entry.find("NAME")["STANDARD"]


def get_readable_name(bio):
    return bio.find("DOCTITLE").text.split(":")[0].strip()


# TODO: Remove call to this function as it's likely no longer needed with new schema
def get_sex(bio):
    tag = bio.contents[-1]
    if tag.name not in ["BIOGRAPHY", "WRITING"]:
        logger.error("Unexpected last tag: " + tag.name)
    else:
        return (tag.get("SEX"))
    return None


def get_persontype(bio):
    return bio.BIOGRAPHY.get("PERSON")


def get_sparql_results(endpoint_url, query):
    from SPARQLWrapper import SPARQLWrapper, JSON
    sparql = SPARQLWrapper(
        endpoint_url, agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11")

    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    # return sparql.query().convert()
    try:
        res = sparql.query().convert()
    except urllib.error.HTTPError as e:
        logger.error(e)
        res = None
    return res


def get_wd_identifier(id):
    """Given orlando identifier, returns corresponding uri of wikidata should it exist
        :param id: orlando id
        :return: corresponding uri of wikidata should it exist, otherwise returns None
    """
    endpoint_url = "https://query.wikidata.org/sparql"

    query = """SELECT ?item ?itemLabel
    WHERE
    {
      ?item wdt:P6745 "%s"
      SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
    }
    LIMIT 10""" % id
    results = get_sparql_results(endpoint_url, query)
    if not results:
        return None
    elif len(results["results"]["bindings"]) > 1:
        logger.info("Multiple wikidata matches found:" + id)
    elif len(results["results"]["bindings"]) < 1:
        logger.info("Entry not found in wikidata: " + id)
    else:
        for result in results["results"]["bindings"]:
            if (result["item"]["type"]) == "uri":
                logger.info(F"Wikidata Identifier found: {id} | {result['item']['value']}")
                return rdflib.term.URIRef(result["item"]["value"])
        # TODO: Validate this against standard name perhaps
        # result["itemLabel"]
    return None


"""
Creating files of extracted triples
"""

def create_uber_triples(mode, graph, script_id):
    fmt = [mode.format]
    if fmt == ["pretty-xml"]:
        fmt = ["rdf"]
    elif fmt == ["all"]:
        fmt = ["ttl", "rdf"]

    for x in fmt:
        temp_path = "extracted_triples/" + script_id + "." + x
        if x == "rdf":
            x = "pretty-xml"

        create_extracted_uberfile(temp_path, graph, x)


def create_individual_triples(mode, person, script_id):
    fmt = [mode.format]
    if fmt == ["pretty-xml"]:
        fmt = ["rdf"]
    elif fmt == ["all"]:
        fmt = ["ttl", "rdf"]

    for x in fmt:
        temp_path = "extracted_triples/" + script_id + "_" + x + "/" + person.id + "_" + script_id + "." + x
        if x == "rdf":
            x = "pretty-xml"
        create_extracted_file(temp_path, person, x)

def create_place_nodes(g):
    for label, uri in PLACE_MAP.items():
        uri = rdflib.URIRef(uri)
        label = label.replace(",",", ")
        g.add((uri, rdflib.RDF.type, NS_DICT["crm"].E53_Place))
        g.add((uri, NS_DICT["crm"].P2_has_type, NS_DICT["cwrc"].MappedPlace))
        g.add((uri, rdflib.SKOS.hiddenLabel, rdflib.Literal(label)))

def create_extracted_file(filepath, person, serialization="ttl"):
    """Create file of extracted triples for particular person
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        if serialization == "ttl":
            f.write("#" + str(len(person.to_graph())) + " triples created\n")
            f.write(person.to_file())
        elif serialization:
            f.write(person.to_file(serialization=serialization))


def create_extracted_uberfile(filepath, graph, serialization="ttl", extra_triples=None):
    """Create file of triples for a particular graph
    """
    create_place_nodes(graph) #TODO: Review if needed?
    
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        if extra_triples:
            g = rdflib.Graph()
            g.parse(extra_triples, format="ttl")
            graph += g
        if serialization == "ttl":
            f.write("#" + str(len(graph)) + " triples created\n")
            f.write("# date extracted: ~" + get_current_time() + "\n")
            f.write(graph.serialize(format="ttl")) #.decode())
        elif serialization:
            f.write(graph.serialize(format=serialization)) #.decode())



def config_logger2(name, verbose=False):
    # Will likely want to convert logging records to be json formatted and based on external file.
    # Add metadata info about time of extraction run and remove asctime
    # TODO: Deprecate this
    import logging
    import os
    if not os.path.exists("log"):
        os.makedirs("log")

    if name != "utilities":
        name += '_extraction'

    name = name.lower()

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler("log/" + name + ".log", mode="w")
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(levelname)s - %(asctime)s {%(module)s.py:%(lineno)d} - %(message)s ')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    if verbose:
        ch = logging.StreamHandler()
        ch.setLevel(logging.ERROR)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    return logger

def config_logger(name, verbose=3):
    # Will likely want to convert logging records to be json formatted and based on external file.
    # Add metadata info about time of extraction run and remove asctime
    import logging
    import os
    if not os.path.exists("log"):
        os.makedirs("log")

    if name != "utilities":
        name += '_extraction'

    name = name.lower()
    logger = logging.getLogger(name)

    logger.setLevel(logging.INFO)
    fh = logging.FileHandler("log/" + name + ".log", mode="w")
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(levelname)s - %(asctime)s {%(module)s.py:%(lineno)d} - %(message)s ')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Handling of stdout logging
    if verbose == 0:
        ch = logging.StreamHandler()
        ch.setLevel(logging.ERROR)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    elif verbose == 1:
        ch = logging.StreamHandler()
        ch.setLevel(logging.WARNING)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    elif verbose > 2:
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    return logger

logger = config_logger("utilities")

def manage_mode(mode, person, graph):
    if mode.verbosity == 3:
        print(person)
    if mode.verbosity >= 2:
        print(person.to_file())
    if mode.verbosity > 0:
        print(str(len(graph)) + " triples created")
        print("\n" * 3)

    if mode.pause:
        res = input("Enter q/quit to exit or any key to continue\n")
        if res in ["q", "quit"]:
            exit()


def get_file_dict(script, args, testcase_data, testcases_available):
    from collections import OrderedDict
    directory = testcase_data['default directory']
    file_ending = testcase_data['file ending']
    filelist = []
    descriptors = []

    if args.random or args.first or args.last:
        filelist = [directory +
                    filename for filename in sorted(os.listdir(directory)) if filename.endswith(file_ending)]
        if args.random:
            import random
            filelist = random.sample(filelist, args.random)
        elif args.first:
            filelist = filelist[:args.first]
        elif args.last:
            filelist = filelist[-args.last:]
        descriptors = ["Testing on " + filename + " from " + directory for filename in filelist]
        print("Running extraction on", args.random, "random Orlando file(s)")
    elif args.file:
        assert args.file.endswith(".xml"), "Not an XML file"
        filelist = [args.file]
        descriptors = ["Testing single file specified: " + args.file]
    elif args.orlando:
        filelist = [args.orlando]
        descriptors = ["Testing single entry specified: " + args.orlando]
        print("Running extraction on " + args.orlando)
    elif args.directory:
        if args.directory[-1] != "/":
            args.directory += "/"
        filenames = [filename for filename in sorted(os.listdir(args.directory)) if filename.endswith(file_ending)]
        filelist = [args.directory + filename for filename in filenames]
        descriptors = ["Testing on " + filename + " from " + args.directory for filename in filenames]
        print("Running extraction on files within" + args.directory)
    elif args.qa:
        filelist = sorted(testcase_data['qa']['testcases'].keys())
        descriptors = [testcase_data['qa']['testcases'][desc] for desc in filelist]
        print("Running extraction on qa cases: ")
        print(*filelist, sep=", ")
    elif "special" in testcase_data and args.s:
        filelist = sorted(testcase_data['special'].keys())
        descriptors = [testcase_data['special'][desc] for desc in filelist]
        print("Running extraction on special cases: ")
        print(*filelist, sep=", ")
    elif "graffles" in testcase_data and args.g:
        filelist = sorted(testcase_data['graffles'].keys())
        descriptors = [testcase_data['graffles'][desc] for desc in filelist]
        print("Running extraction on graffle examples: ")
        print(*filelist, sep=", ")
    elif "ignored files" in testcase_data and args.i:
        filelist = sorted(testcase_data['ignored files'].keys())
        descriptors = [testcase_data['ignored files'][desc] for desc in filelist]
        print("Running extraction on ignored files: ")
        print(*filelist, sep=", ")
    elif testcases_available and args.testcases:
        filelist = sorted(testcase_data[script]['testcases'].keys())
        descriptors = [testcase_data[script]['testcases'][desc] for desc in filelist]
        print("Running extraction on test cases: ")
        print(*filelist, sep=", ")
    else:
        print("Running extraction on default folder: " + directory)
        filelist = [directory +
                    filename for filename in sorted(os.listdir(directory)) if filename.endswith(file_ending)]
        descriptors = ["Testing on " + filename + " from " + directory for filename in filelist]

    # TODO: clean this maybe using any operator
    if script == "freestanding_events.py" and (args.qa or args.testcases):
        filelist = [directory + file + file_ending for file in filelist]
    elif script == "freestanding_events.py":
        pass
    elif args.qa or args.s or args.i or args.g or args.orlando or (testcases_available and args.testcases):
        filelist = [directory + file + file_ending for file in filelist]

    # TODO: Allow script specific testcases to overwrite ignored files, maybe?
    if "ignored files" in testcase_data and not args.s and not args.i and not args.g:
        # Get full filepaths of to be ignored files since it may vary per option chosen
        ignore_files = [x for x in filelist if any(s in x for s in testcase_data["ignored files"].keys())]
        for x in ignore_files:
            index = filelist.index(x)
            del descriptors[index]
            del filelist[index]
    return OrderedDict(zip(filelist, descriptors))

def parse_args(script, info_type, logger=None):
    """
        Parses arguments to particular extraction script and creates dictionary of {files:desc}
        relying on testcase.json for testcases + qa

        ./birthDeath -t returns {testfiles:testcase descriptions}

    """
    import argparse
    import json

    """
        TODO: add options for verbosity of output, types of output
        -o OUTPUTFILE
        -format/ff/fmt [turtle|rdf-xml|all]
        -v verbose logging + print out triples to stdout
        Possible TODO: create extractionmode obj to handle these additional options with 
    """
    testcases_available = False
    with open("testcases.json", 'r') as f:
        testcase_data = json.load(f)
    parser = argparse.ArgumentParser(
        description='Extract the ' + info_type + ' information from selection of orlando xml documents', add_help=True)
    modes = parser.add_mutually_exclusive_group()

    script = script.split("/")[-1]

    if script in testcase_data:
        # TODO: expand test case prints to expose reasons for testing
        help_str = "will run through test case list particular to " + script
        help_str += " Which currently are:" + str(list(testcase_data[script]['testcases']))[1:-1]
        modes.add_argument('-testcases', '-t', action="store_true", help=help_str)
        testcases_available = True
    else:
        print("No particular testcases available, please add to testcases.json")

    if "qa" in testcase_data:
        help_str = "will run through qa test cases that are related to www.github.com/cwrc/testData/tree/master/qa, "
        help_str += "Which currently are:" + str(list(testcase_data['qa']['testcases']))[1:-1]
        modes.add_argument('-qa', action="store_true", help=help_str)

    if "special" in testcase_data:
        help_str = "will run through special cases that are of particular interest atm which currently are: "
        help_str += str(list(testcase_data['special']))[1:-1]
        modes.add_argument('-s', "-special", action="store_true", help=help_str)

    if "graffles" in testcase_data:
        help_str = "will run through cases related to our graffles"
        help_str += str(list(testcase_data['graffles']))[1:-1]
        modes.add_argument('-g', "-graffles", "-graffle", action="store_true", help=help_str)

    if "ignored files" in testcase_data:
        help_str = "will run through files that are currently being ignored which currently include: "
        help_str += str(list(testcase_data['ignored files']))[1:-1]
        modes.add_argument('-i', "-ignored", action="store_true", help=help_str)

    modes.add_argument("-id", "-orlando", "--orlando",
                       help="entry id of a single orlando document to run extraction upon, ex. woolvi")
    modes.add_argument("-f", "-file", "--file", help="single orlando xml document to run extraction upon")
    # modes.add_argument("-id+", "-orlando+", "--orlando+",
                    #    help="entry id of a single orlando document to run extraction upon and the files proceeding, ex. woolvi")
    modes.add_argument("-d", "-directory", "--directory", help="directory of files to run extraction upon")
    modes.add_argument("-r", "-random", "--random", nargs='?', const=1, type=int,
                       help="chooses {RANDOM} random file(s) to run extraction upon")
    modes.add_argument("-l", "-last", "--last", nargs='?', const=1, type=int,
                       help="chooses {last} file(s) to run extraction upon, ex. the last 20 files")
    modes.add_argument("-fi", "-first", "--first", nargs='?', const=1, type=int,
                       help="chooses {first} file(s) to run extraction upon, ex. the first 20 files")

    parser.add_argument("-v", "--verbosity", default=1, type=int, choices=[0, 1, 2, 3],
                        help="increase output verbosity")
    parser.add_argument("-fmt", "--format", default="ttl",
                        choices=["rdf", "rdf/xml", "ttl", "turtle", "json-ld", "nt", "trix", "n3", "all"])
    parser.add_argument("-u", "-update", "--update", "-update-sparqlendpoint",
                        help="url of sparql endpoint to update")

    # NOTE: could make this to pause after ever n entries? #uselessfeature?
    parser.add_argument("-p", "-pause", "--pause", action="store_true",
                        help="pause after every entry to examine output and be prompted to continue/quit")

    # TODO: Add option for only large graph not individual triples

    args = parser.parse_args()
    
    if args.random and args.random < 1:
        parser.error("Minimum file count is 1")

    file_dict = get_file_dict(script, args, testcase_data, testcases_available)

    arguments = Extraction(file_dict, info_type, verbosity=args.verbosity,
                           logger=logger, format=args.format, pause=args.pause)

    return arguments, arguments.file_dict


if __name__ == '__main__':
    import doctest
    doctest.testmod(verbose=True)
