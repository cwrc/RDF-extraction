import rdflib
import os
import re
import datetime
import urllib
import copy
import csv

try:
    from utils.place import Place
except ModuleNotFoundError as e:
    from . import Place

"""
TODO: Add doctests for:
- strip_all_whitespace
- remove_punctuation
- get_name_uri
- make_standard_uri
- create_uri
- create_cwrc_uri
- get_value
- get_reg
- get_people
- get_titles
- get_places

TODO: parse required ns from external files
"""
# TODO Review variables/function names and refactor
WRITER_MAP = {}
MAX_WORD_COUNT = 35
GENRE_MAPPING = {}

TITLE_MAPPING = {}
TITLE_MAPPING_1 = {}
TITLE_MAPPING_2 = {}



PERSON_MAP = {}
ORGANIZATION_MAP = {}
CWRC_URI_MAP = {}
CORE_TAGS = ['RS','ADDRLINE', 'ADDRESS', "SCHOLARNOTE", "RESEARCHNOTE" , "SIC", 'SOCALLED','AREA', 'FOREIGN','SETTLEMENT', 'REGION', 'GEOG', 'ORGNAME',"BIBCIT", "BIBCITS", "QUOTE","NAME", "TITLE", "PLACE", "DATE", "DATERANGE", "DATESTRUCT", "TEXTSCOPE", "TGENRE", "CHRONSTRUCT"]
GENERIC_TITLES = ["Selected Stories","Songs", "Poems on Several Occasions", "Poems on Various Subjects", "Songs", "Selected Stories", "Essays", "Autobiography","A Book", "Collected Short Stories","Collected Stories", "","Poems", "Critical", "Monthly", "Memoirs", "Collected Poems", "Selected Poems", "Works", "Poetry", "Poetry Review", "Analytical", "Journal", "Letters", "Life", "Verses", "The Monthly Packet", "Dictionary", "Miscellaneous Poems", "Standard", "Epilogue", "Library Journal", "Plays by Women", "New Collected Poems"]
GENERIC_NAMES = ["king","King","mother-in-law" , "Queen", "queen", "Prince","husband","wife","partner" ,"father", "daughter","essay", "son","he","she","they","her","him","them", "sisters","the",  "mother", "sibling", "brother", "sister", "friend", "his wife", "her husband","his husband", "her wife", "their husband", "their wife", "lover", "family", "influence", "Her father", "eldest sister", "father's", "future husband", "grandfather", "grandmother", "her blind husband", "her mother", "landlady", "man", "mother ", "one", "organization", "papa", "parents", "second husband", "secretary", "sister-in-law", "son-in-law", "stepfather", "stepmother", "uncle", "university", "a daughter", "a son", "another","aunt", "author", "baby", "brother's", "brother-in-law", "brothers", "cousin", "daughter-in-law", "elder half-sister", "elder sister", "ex-husband", "father-in-law", "female", "fiancé", "first husband", "first wife", "her aunt", "her father", "his father", "his", "husbands", "mayor", "merchant", "nanny", "nephew", "niece", "paternal grandmother", "patron", "playwright", "publisher", "second wife", "servants", "six-month-old son", "sons", "step-father", "step-grandfather", "step-grandmother", "stepson", "widower", "youngest brother"]

WRITING_PROPERTIES = {}






NS_DICT = {
    "as": rdflib.Namespace("http://www.w3.org/ns/activitystreams#"),
    "bf": rdflib.Namespace("http://id.loc.gov/ontologies/bibframe/"),
    "bibo": rdflib.Namespace("http://purl.org/ontology/bibo/"),
    "bio": rdflib.Namespace("http://purl.org/vocab/bio/0.1/"),
    "biro": rdflib.Namespace("http://purl.org/spar/biro/"),
    "cc": rdflib.Namespace("http://creativecommons.org/ns#"),
    "cito": rdflib.Namespace("http://purl.org/spar/cito/"),
    "cwrc": rdflib.Namespace("http://sparql.cwrc.ca/ontologies/cwrc#"),
    "data": rdflib.Namespace("http://cwrc.ca/cwrcdata/"),
    "dbpedia": rdflib.Namespace("http://dbpedia.org/resource/"),
    "dcterms": rdflib.Namespace("http://purl.org/dc/terms/"),
    "dctypes": rdflib.Namespace("http://purl.org/dc/dcmitype/"),
    "eurovoc": rdflib.Namespace("http://eurovoc.europa.eu/"),
    "foaf": rdflib.Namespace("http://xmlns.com/foaf/0.1/"),
    "genre": rdflib.Namespace("http://sparql.cwrc.ca/ontologies/genre#"),
    "geonames": rdflib.Namespace("https://sws.geonames.org/"),
    "gvp": rdflib.Namespace("http://vocab.getty.edu/ontology#"),
    "ii": rdflib.Namespace("http://sparql.cwrc.ca/ontologies/ii#"),
    "loc": rdflib.Namespace("http://id.loc.gov/vocabulary/relators/"),
    "oa": rdflib.Namespace("http://www.w3.org/ns/oa#"),
    "org": rdflib.Namespace("http://www.w3.org/ns/org#"),
    "orlando": rdflib.Namespace("https://commons.cwrc.ca/orlando:"),
    "owl": rdflib.Namespace("http://www.w3.org/2002/07/owl#"),
    "prism": rdflib.Namespace("http://prismstandard.org/namespaces/1.2/basic/"),
    "prov": rdflib.Namespace("http://www.w3.org/ns/prov#"),
    "rdf": rdflib.Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#"),
    "rdfs": rdflib.Namespace("http://www.w3.org/2000/01/rdf-schema#"),
    "schema": rdflib.Namespace("http://schema.org/"),
    "sem": rdflib.Namespace("http://semanticweb.cs.vu.nl/2009/11/sem/"),
    "skos": rdflib.Namespace("http://www.w3.org/2004/02/skos/core#"),
    "skosxl": rdflib.Namespace("http://www.w3.org/2008/05/skos-xl#"),
    "tgn": rdflib.Namespace("http://vocab.getty.edu/tgn/"),
    "time": rdflib.Namespace("http://www.w3.org/2006/time#"),
    "vann": rdflib.Namespace("http://purl.org/vocab/vann/"),
    "voaf": rdflib.Namespace("http://purl.org/vocommons/voaf#"),
    "void": rdflib.Namespace("http://rdfs.org/ns/void#"),
    "vs": rdflib.Namespace("http://www.w3.org/2003/06/sw-vocab-status/ns#"),
}

TITLE_TYPE_MAPPING = { "MONOGRAPHIC": NS_DICT["genre"].standaloneWork,
    "ANALYTIC": NS_DICT["genre"].embeddedWork,
    "JOURNAL": NS_DICT["genre"].periodical,
    "SERIES": NS_DICT["genre"].series,
    "UNPUBLISHED": NS_DICT["genre"].unpublished }


class Extraction(object):
    """docstring for Extraction"""

    def __init__(self, file_dict, name, verbosity=None, format=None, output=None, pause=None, logger=None):
        super(Extraction, self).__init__()
        self.file_dict = file_dict
        self.verbosity = verbosity
        self.format = format or "ttl"
        self.output = output
        self.pause = pause

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

def get_xpath(element):
    """courtesy: gist.github.com/ergoithz/6cf043e3fdedd1b94fcf
    Generate xpath from BeautifulSoup4 element
    :param element: BeautifulSoup4 element.
    :type element: bs4.element.Tag or bs4.element.NavigableString
    :return: xpath as string
    :rtype: str
    """
    components = []
    child = element if element.name else element.parent
    for parent in child.parents:
        """
        @type parent: bs4.element.Tag
        """
        siblings = parent.find_all(child.name, recursive=False)
        components.append(
            child.name
            if siblings == [child] else
            '%s[%d]' % (child.name, 1 + siblings.index(child))
        )
        child = parent
    components.reverse()
    return '/%s' % '/'.join(components)


def remove_unwanted_tags(tag):
    tag_copy = copy.copy(tag)

    unwanted_tag_names = ["BIBCITS", "RESPONSIBILITIES", "KEYWORDCLASSES","RESEARCHNOTE", "SOURCES", "SOURCE", "ORLANDOHEADER", "WORKSCITED", "HEADING"]
    unwanted_tags = []
    for x in unwanted_tag_names:
        unwanted_tags += tag_copy.find_all(x)

    for x in unwanted_tags:
        x.decompose()
    return tag_copy

def remove_tags(tag_names,tag):
    tag_copy = copy.copy(tag)

    unwanted_tags = tag_copy.find_all(tag_names)

    for x in unwanted_tags:
        x.decompose()

    return tag_copy

def get_snippet(tag, no_limit=False):
    text = ""
    # removing tags that mess up the snippet
    simplified_tag = remove_unwanted_tags(tag)

    if not simplified_tag.get_text():
        logger.error(F"Empty tag encountered when creating the snippet from: {tag}")
        text = ""
    elif no_limit:
        text = str(simplified_tag.get_text())
        name = simplified_tag.find("STANDARD")
        if name:
            text = text.replace(name.text, name.text + ": ")
        headings = simplified_tag.find_all("HEADING")
        for x in headings:
            text = text.replace(x.get_text(), F"{x.get_text()} ")
    else:
        text = limit_to_full_sentences(str(simplified_tag.get_text()), MAX_WORD_COUNT)

    date = simplified_tag.find("DATE")

    if not date:
        date = simplified_tag.find("DATERANGE")

    if not date:
        date = simplified_tag.find("DATESTRUCT")

    if date:
        text = text.replace(date.text, date.text + ": ")

    text= text.replace("\n"," ")
    text= text.replace(".",". ")
    text= text.replace("  "," ")
    text= text.replace(". .",".")

    text=text.strip()
    return text


def camel_case(s):
    """Converts a string to camelCase."""
    s = re.sub(r"(_|-)+", " ", s).title().replace(" ", "")
    return s[0].lower() + s[1:]

def create_writer_map(path=None):

    if not path:
        path = 'data/writers_sex.csv'
    with open(path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        for row in reader:
            if row[0] not in WRITER_MAP:
                WRITER_MAP[row[0]] = {"ID": row[1],"NAME": row[2] , "SEX": row[3]}


def create_person_map(path=None):
    if not path:
        path = 'data/full_people_mapping.csv'
    with open(path) as f:
        csv_file = csv.DictReader(f)
        for row in csv_file:
            row["CWRC URI"] = f"{NS_DICT['orlando']}{row['ID']}"
            PERSON_MAP[row["CWRC URI"]] = row
            if row['Primary URI']:
                CWRC_URI_MAP[row['Primary URI']] = row["CWRC URI"]


def create_org_map(path=None):
    if not path:
        path = 'data/organization_mapping.csv'
    with open(path) as f:
        csv_file = csv.DictReader(f)
        for row in csv_file:
            row["CWRC URI"] = f"{NS_DICT['orlando']}{row['ID']}"
            ORGANIZATION_MAP[row["CWRC URI"]] = row
            if row['Primary URI']:
                CWRC_URI_MAP[row['Primary URI']] = row["CWRC URI"]



def create_genre_map(path=None):

    if not path:
        path = "data/genre_mapping.csv"
    with open(path) as f:
        csvfile = csv.reader(f)
        next(csvfile)
        for row in csvfile:
            GENRE_MAPPING[row[0]] = row[1]


def create_title_mappings():
    # TODO: Review more efficient mapping + using fuzzy matching
    mapping_path_1 = "data/title_mapping_lvl1.csv"
    mapping_path_2 = "data/title_mapping_lvl2.csv"

    try:
        with open(mapping_path_1) as f:
            reader = csv.reader(f)
            for row in reader:
                TITLE_MAPPING_1[row[0]] = row[1]
    except FileNotFoundError:
        print(f"File not found: {mapping_path_1}")
    except Exception as e:
        print(f"Error reading {mapping_path_1}: {e}")

    try:
        with open(mapping_path_2) as f:
            reader = csv.reader(f)
            for row in reader:
                TITLE_MAPPING_2[row[0]] = row[1]
    except FileNotFoundError:
        print(f"File not found: {mapping_path_2}")
    except Exception as e:
        print(f"Error reading {mapping_path_2}: {e}")


def create_writing_properties_map():
    import pandas as pd
    global WRITING_PROPERTIES
    with open("data/writing_property_mapping.csv") as f:
        WRITING_PROPERTIES = pd.read_csv(f)


create_writing_properties_map()
create_writer_map()
create_genre_map()
create_title_mappings()
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
    import re
    return re.sub('[\s+]', '', str(string))


def split_by_casing(string, altmode=None):
    return " ".join(re.findall('^[a-z]+|[A-Z][^A-Z]*', string))


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


def limit_words(string, word_count=MAX_WORD_COUNT):
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
    string = string.strip()
    if string == "":
        return string

    if string[0] == ".":
        string = string[1:]

    sentences = string.split(".")
    text = ""
    for x in sentences:
        if text.count(" ") < max:
            text += x.strip()
            try:
                if text[-1] != ".":
                    text += ". "
            except IndexError:
                pass
        else:
            break

    text = text.strip()
    text.replace(".  .", ". ")

    return text


"""
    Series of functions to do with the creation of URI
"""

def get_entry_id(tag):
    return tag.find_parent("ENTRY").get("ID")


def get_name_uri(tag):
    """Creates a uri based on the standard attribute of a tag if ref attribute not present"""
    uri = tag.get("REF")
    if not uri:
        try:
            id = get_entry_id(tag)
            logger.error(F"In entry: {id} - NAME tag missing REF attribute: {tag}")
        except AttributeError:
            logger.error(F"NAME tag missing REF attribute: {tag}")
        std_val = tag.get("STANDARD")

        if not std_val:
            try:
                logger.error(F"In entry: {id} - NAME tag missing STANDARD attribute: {tag}")
            except UnboundLocalError:
                logger.error(F"NAME tag missing STANDARD attribute: {tag}")
            return make_standard_uri(tag.text)
        return make_standard_uri(std_val)
    else:
        if uri in PERSON_MAP:
            new_uri = PERSON_MAP[uri]['Primary URI']
            if new_uri:
                uri = new_uri
        elif uri in ORGANIZATION_MAP:
            new_uri = ORGANIZATION_MAP[uri]['Primary URI']
            if new_uri:
                uri = new_uri

        return rdflib.term.URIRef(uri)


# TODO: make this function handle different entity types
def get_primary_uri(uri, text, entity_type="person"):
    if uri in PERSON_MAP:
        return rdflib.term.URIRef(PERSON_MAP[uri]['Primary URI'])
    elif uri in ORGANIZATION_MAP:
        return rdflib.term.URIRef(ORGANIZATION_MAP[uri]['Primary URI'])
    elif uri and uri != "None":
        return rdflib.term.URIRef(uri)
    else:
        logger.warning(F"{entity_type} not in mapping: {text}")
        return make_standard_uri(text)


def get_entry_standard_name(entry):
    name = entry.find("STANDARD")
    if name:
        return name.text
    else:
        return entry.find("NAME")["STANDARD"]

def get_cwrc_uri(uri):
    if str(uri) in CWRC_URI_MAP:
        return rdflib.term.URIRef(CWRC_URI_MAP[str(uri)])
    logger.warning(F"URI not in mapping: {uri}")
    return None

def get_person_secondary_uris(cwrc_uri):
    if cwrc_uri not in PERSON_MAP:
        logger.warning(F"Person not in published authority list: {cwrc_uri}")
        return []
    secondary_identifier = PERSON_MAP[cwrc_uri]["Secondary URI"]
    secondary_uris = []
    if secondary_identifier != "":
        secondary_uris = secondary_identifier.split(" | ")
    if PERSON_MAP[cwrc_uri]["Primary URI"] != "":
        secondary_uris.append(cwrc_uri)

    secondary_uris = [rdflib.term.URIRef(x) for x in secondary_uris]

    return secondary_uris

def get_full_name(tag_or_uri, doc=None, fallback=None):
# TODO: Leverage standard name to get full name from URI's name tag

    full_name = None
    uri = None
    if type(tag_or_uri) == rdflib.term.URIRef:
        uri = tag_or_uri
    else:
        full_name = tag_or_uri.get_text()
        uri = tag_or_uri.get("REF")

    if uri:
        uri = uri.strip()
    else:
        logger.warning(F"URI not found for {full_name}")
        if full_name in GENERIC_NAMES:
            logger.warning(F"Generic name found: {full_name} from {tag_or_uri}")
            return tag_or_uri.get("STANDARD").strip()
        else:
            return full_name

    if uri in CWRC_URI_MAP:
        uri = str(get_cwrc_uri(uri))

    if uri in PERSON_MAP:
        full_name = PERSON_MAP[uri]['Full Name']
    elif uri in ORGANIZATION_MAP:
        full_name = ORGANIZATION_MAP[uri]['Preferred Name']
    elif doc:
        full_name = doc.find(REF=uri).text
    elif fallback:
        full_name = fallback
        logger.warning(F"URI not in mapping, using fallback: {uri}: {fallback}")
    else:
        logger.warning(F"URI not in mapping: {uri}")

    if not full_name:
        logger.warning(F"Full name missing for {uri}")

    full_name = full_name.strip()

    return full_name



def make_standard_uri(std_str, ns="data"):
    """Makes uri based of string, removes punctuation and replaces spaces with an underscore
    v2, leaving hyphens
    """
    return create_uri(ns, remove_punctuation(std_str))


def create_uri(prefix, term):
    """prepends the provided namespace uri to the given term"""
    return rdflib.term.URIRef(str(NS_DICT[prefix]) + term)


def create_cwrc_uri(term):
    # TODO: Deprecate this and use create_uri instead
    """prepends the cwrc namespace uri to the given term"""
    return create_uri("cwrc", term)


def get_value(tag):
    value = tag.get("STANDARD")
    if not value:
        value = tag.get("REG")
    if not value:
        value = tag.get("CURRENTALTERNATIVETERM")
    if not value:
        value = str(tag.text)
        value = ' '.join(value.split())
    return value

def get_values(tag):
    values = []
    values.append(tag.get("STANDARD"))
    values.append(tag.get("REG"))
    values.append(tag.get("CURRENTALTERNATIVETERM"))
    text = str(tag.text)
    text = ' '.join(text.split())
    values.append(text)

    values = [x for x in values if x]

    return values


def get_reg(tag):
    # TODO: Remove this function and where it's been used.
    return tag.get("REG")

def get_other_people(tag, author):
    """returns all unique people other than author, does not return in order of occurences"""
    return [x for x in get_people(tag) if x != author.uri]
def get_all_other_people(tag, author):
    """returns all people other than author, does return in order of occurences"""
    return [x for x in get_all_people(tag) if x != author.uri]

def get_all_people(tag):
    """Returns all people within a given tag"""
    return [get_name_uri(x) for x in tag.find_all("NAME")]

def get_people(tag):
    """Returns all unique people within a given tag, no order guaranteed due to use of set()"""
    return list(set([get_name_uri(x) for x in tag.find_all("NAME")]))

def get_people_names(tag, exclude=None):
    """Returns all URIs mapped to names from all name tags within a given tag"""
    people = {}
    for x in tag.find_all("NAME"):
        uri = get_name_uri(x)
        # print(tag)
        # print(uri)
        # name = get_value(x)
        name = get_full_name(x)
        if uri == exclude:
            continue
        elif uri in people and name not in people[uri]:
            people[uri].append(name)
        else:
            people[uri]=[name]
    return people

def get_title_uri(tag, person=None):
    title = get_value(tag)
    possible_titles = get_values(tag)

    if not title:
        logger.warning(f"Title tag has no value: {tag}")
        return None

    for x in possible_titles:
        # Check if the title is in the person's text scope map
        if person and x in person.textscope_map:
            uri = person.textscope_map[x].get("REF")
            if uri:
                return rdflib.term.URIRef(uri)
            else:
                logger.warning(f"Textscope has no REF attribute: {person.textscope_map[x]} in {person.id}")



    # Check the title mappings
        if x in TITLE_MAPPING_1:
            return rdflib.URIRef(TITLE_MAPPING_1[x])
        if x in TITLE_MAPPING_2:
            return rdflib.URIRef(TITLE_MAPPING_2[x])

        if person:
            logger.warning(f"Title not in mapping: {x} for {person.id}")
        else:
            logger.warning(f"Title not in mapping: {x}")

    # Create a standard URI if no mapping is found
    return make_standard_uri(title + " TITLE", ns="data")

def get_titles(tag, person=None):
    """Returns all titles within a given tag temporary Mapping"""
    title_tags = tag.find_all("TITLE")

    # Get URIs for all title tags
    titles = [get_title_uri(x, person) for x in title_tags]

    # Filter out None values
    titles = [x for x in titles if x]

    return titles


def get_places(tag, entry_id=None):
    """Returns all places uris within a given tag"""
    return [Place(x,entry_id=entry_id).uri for x in tag.find_all("PLACE")]


def get_place_strings(tag, entry_id=None):
    """Returns all places strings within a given tag"""
    return [x.text for x in tag.find_all("PLACE")]

def get_name(entry):
    name = entry.find("STANDARD")
    if name:
        return name.text
    else:
        return entry.find("NAME")["STANDARD"]

def get_readable_name(bio):
    return bio.find("DOCTITLE").text.split(":")[0]

def get_sex(bio):
    tag = bio.contents[-1]
    if tag.name not in ["BIOGRAPHY", "WRITING","ENTRY"]:
        logger.error("Unexpected last tag: " + tag.name)
    else:
        return (tag.get("SEX"))
    return None


def get_persontype(bio):
    return bio.get("PERSON")


def get_div2(tag):
    # NOTE: Might be easier with recursion
    for parent in tag.parents:
        if parent.name == "DIV2":
            return parent

def get_div(tag):
    # NOTE: Might be easier with recursion
    for parent in tag.parents:
        if "DIV" in parent.name:
            return parent

    return None
def get_textscopes_text(tag):
    tag = get_div2(tag)
    if not tag:
        logger.warning(F"Unable to find DIV2 for {tag}")
        return None
    textscopes = tag.find_all("TEXTSCOPE")
    if textscopes == []:
        logger.info(F"No corresponding textscope: {tag}")
    else:
        textscopes = [x.get("PLACEHOLDER") for x in textscopes ]
    return textscopes

def get_textscopes(tag):
    tag = get_div2(tag)
    textscopes = tag.find_all("TEXTSCOPE")
    if textscopes == [] or textscopes is None:
        logger.info(F"{get_entry_id(tag)}: No corresponding textscope: {tag}")
    else:
        textscopes = [rdflib.term.URIRef(x.get("REF")) for x in textscopes if x.get("REF") ]
    return textscopes

def get_sparql_results(endpoint_url, query):
    from SPARQLWrapper import SPARQLWrapper, JSON
    sparql = SPARQLWrapper(endpoint_url)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    return sparql.query().convert()


def get_wd_identifier(id):
    """Given orlando URI, returns corresponding uri of wikidata should it exist
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

    if len(results["results"]["bindings"]) > 1:
        logger.info("Multiple wikidata matches found:" + id)
    elif len(results["results"]["bindings"]) < 1:
        logger.info("Entry not found in wikidata: " + id)
    else:
        for result in results["results"]["bindings"]:
            if (result["item"]["type"]) == "uri":
                return rdflib.term.URIRef(result["item"]["value"])
        # TODO: Validate this against standard name perhaps
        # result["itemLabel"]
    return None


"""
Creating files of extracted triples
"""


"""
Creating files of extracted triples
"""

def create_uber_triples(mode, graph, script_id, extra_triples=None):
    fmt = [mode.format]
    if fmt == ["pretty-xml"]:
        fmt = ["rdf"]
    elif fmt == ["all"]:
        fmt = ["ttl", "rdf"]

    for x in fmt:
        temp_path = "extracted_triples/" + script_id + "." + x
        if x == "rdf":
            x = "pretty-xml"

        create_extracted_uberfile(temp_path, graph, x, extra_triples=extra_triples)


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

def create_extracted_file(filepath, person, serialization="ttl"):
    """Create file of extracted triples for particular person
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        if serialization == "ttl":
            f.write("#" + str(len(person.to_graph())) + " triples created\n")
            f.write("# date extracted: ~" + get_current_time() + "\n")
            f.write(person.to_file())
        elif serialization:
            f.write(person.to_file(serialization=serialization))


def create_extracted_uberfile(filepath, graph, serialization="ttl", extra_triples=None):
    """Create file of triples for a particular graph
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        if extra_triples:
            g = rdflib.Graph()
            g.parse(extra_triples, format="ttl")
            graph += g
        if serialization == "ttl":
            f.write("#" + str(len(graph)) + " triples created\n")
            f.write("# date extracted: ~" + get_current_time() + "\n")
            f.write(graph.serialize(format="ttl"))
        elif serialization:
            f.write(graph.serialize(format=serialization))


def config_logger(name, verbose=False):
    # Will likely want to convert logging records to be json formatted and based on external file.
    import logging
    import os
    if not os.path.exists(".log"):
        os.makedirs(".log")

    if name != "utilities":
        name += '_extraction'

    name = name.lower()
    logger = logging.getLogger(name)

    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(".log/" + name + ".log", mode="w")
    fh.setLevel(logging.INFO)
    # formatter = logging.Formatter('%(levelname)s - %(asctime)s {%(module)s.py:%(lineno)d} - %(message)s ')
    formatter = logging.Formatter('%(message)s ')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

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
    file_prefix = testcase_data['file prefix'] if 'file prefix' in testcase_data else None
    filelist = []
    descriptors = []
    print(args)

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
        if file_prefix:
            args.orlando = file_prefix + args.orlando
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

        if file_prefix:
            filelist = [file_prefix + x for x in filelist]

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
        if file_prefix:
            filelist = [file_prefix + x for x in filelist]
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
    if "ignored files" in testcase_data and not args.s and not args.i and not args.g and not args.override_ignored:
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
    import os
    import argparse
    import json
    print(script, info_type, logger)
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
    modes.add_argument("-oi", "-override-ignored", "--override-ignored", action="store_true")

    parser.add_argument("-v", "--verbosity", default=1, type=int, choices=[0, 1, 2, 3],
                        help="increase output verbosity")
    parser.add_argument("-fmt", "--format", default="ttl",
                        choices=["rdf", "rdf/xml", "ttl", "turtle", "json-ld", "nt", "trix", "n3", "all"])
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
