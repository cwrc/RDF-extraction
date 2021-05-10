from typing import Literal
from bs4 import BeautifulSoup
import rdflib
import sys
import os
import datetime
import csv
from rdflib import *
import logging
from fuzzywuzzy import fuzz
import re
import urllib.parse

CONFIG_FILE = "./bibparse.config"
# Count of bf:Agent --> Unique labeled agents
# 35,767 --> 12,266

# Triple Counts:
#  158200 - bib files
#  657830 - mods from https://gitlab.com/calincs/conversion/metadata-conversion/-/tree/master/Original_Datasets/CWRC/BIBLIFO_MODS
# 2240072 - http://sparql.cwrc.ca/db/BibliographyV1 / http://sparql.cwrc.ca/storage/Orlando_Bibliography_Subset_Version_1-01.ttl extracted ~2018
# 2403600 - from March 2021 islandora api
# 2100555 - switching parser to lxml-xml
# 2403655 - Updates to the parsing
# 2428208 - Swap to orlando identifiers 
# 1995756 - Cidoc-ified

# ----------- SETUP LOGGER ------------

logger = logging.getLogger('bibliography_extraction')
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s {Line #%(lineno)d} : %(message)s ')
fh = logging.FileHandler('bibliography_extraction.log')
fh.setFormatter(formatter)
fh.setLevel(logging.INFO)

logger.addHandler(fh)

# ---------- SETUP NAMESPACES ----------

CWRC = rdflib.Namespace("http://sparql.cwrc.ca/ontologies/cwrc#")
BF = rdflib.Namespace("http://id.loc.gov/ontologies/bibframe/")
XML = rdflib.Namespace("http://www.w3.org/XML/1998/namespace")
MARC_REL = rdflib.Namespace("http://id.loc.gov/vocabulary/relators/")
DATA = rdflib.Namespace("http://cwrc.ca/cwrcdata/")
GENRE = rdflib.Namespace("http://sparql.cwrc.ca/ontologies/genre#")
SCHEMA = rdflib.Namespace("http://schema.org/")
FRBROO = rdflib.Namespace("http://iflastandards.info/ns/fr/frbr/frbroo/")
CRM = rdflib.Namespace("http://www.cidoc-crm.org/cidoc-crm/")
CRMPC = rdflib.Namespace("http://www.cidoc-crm.org/cidoc-crm-pc/")

BF_PROPERTIES = {
    "change date": BF.changeDate,
    "variant title":BF.VariantTitle,
    "generation process":BF.GenerationProcess
}

# To reduce duplication of admin agents
ADMIN_AGENTS = {
    "Orlando Document Archive": DATA.Orlando_Document_Archive,
    "CaAEU": DATA.CaAEU,
    "UAB": DATA.UAB,
    "U3G": DATA.U3G,
    "Orlando: Women's Writing in the British Isles from the Beginnings to the Present": DATA.Orlando,
}

# TODO: Use as skos:related terms
# ROLES = {
#     "publisher": URIRef("http://vocab.getty.edu/aat/300025574"),
#     "editor": URIRef("http://vocab.getty.edu/aat/300025526"),
#     "translator": URIRef("http://vocab.getty.edu/aat/300025601"),
#     "compiler": URIRef("http://vocab.getty.edu/aat/300121766"),
#     "adapter": URIRef("http://vocab.getty.edu/aat/300410355"),
#     "illustrator": URIRef("http://vocab.getty.edu/aat/300025123"),
#     "contributor": URIRef("http://vocab.getty.edu/aat/300403974"),
#     "introduction": URIRef("http://vocab.getty.edu/aat/300374882"), # letters of intro: don't know about this one
#     "revised": URIRef("http://vocab.getty.edu/aat/300025526"), # reusued editor
#     "afterword": URIRef("http://vocab.getty.edu/aat/300121766"),
#     "transcriber": URIRef("http://vocab.getty.edu/aat/300440751"),
# }

ROLES = {
    "publisher": MARC_REL.pbl,
    "editor": MARC_REL.edt,
    "translator": MARC_REL.trl,
    "compiler": MARC_REL.com,
    "adapter": MARC_REL.adp,
    "contributor": MARC_REL.ctb,
    "illustrator": MARC_REL.ill,
    "introduction": MARC_REL.win,
    "revised": MARC_REL.edt,
    "afterword": MARC_REL.aft,
    "transcriber":MARC_REL.trc
}

genre_graph = None
genre_map = {}
geoMapper = None
genre_mapping = {}
STRING_MATCH_RATIO = 50

UNIQUE_UNMATCHED_PLACES = set()

# --------- UTILITY FUNCTIONS -------


def remove_punctuation(input_str, all_punctuation=False):
    """
    Removes punctuation as defined by the Extraction doc
    This is primarly used for normalizing person URIs so they relate
    to separately extracted elements
    :param input_str: the
    :param all_punctuation: removes all punctuation within pythons string.punctuation
    otherwise removes only hyphens (-)
    :return: string with punctuation replaced
    """
    import string
    from unidecode import unidecode
    if all:
        translator = str.maketrans('', '', string.punctuation)
    else:
        translator = str.maketrans('', '', string.punctuation.replace("-", ""))
    input_str = input_str.translate(translator)
    input_str = input_str.replace(" ", "_")
    # TODO: Need to revise this method to handle titles with weird unicode ex.
    # Public Confessions of a Middle-Aged Woman Aged 55 ¾
    input_str = input_str.replace("¾", "3-4")
    input_str = input_str.replace("¼", "1-4")
    input_str = input_str.replace("<<", "")
    input_str = input_str.replace(">>", "")
    return unidecode(input_str)


def dateParse(date_string: str):
    # Currently works for single dates need to examine patterns further for 2 days
    # Strip spaces surrounding the date string
    date_string = date_string.strip().rstrip()

    try:
        dt = datetime.datetime.strptime(date_string, "%Y-%m-%d")
        return dt.isoformat(), True
    except ValueError:
        pass
    try:
        dt = datetime.datetime.strptime(date_string, "%Y--")
        return dt.isoformat(), True
    except ValueError:
        pass
    try:
        dt = datetime.datetime.strptime(date_string, "%Y-")
        return dt.isoformat(), True
    except ValueError:
        pass

    try:
        dt = datetime.datetime.strptime(date_string, "%Y")
        return dt.isoformat(), True
    except ValueError:
        pass

    try:
        dt = datetime.datetime.strptime(date_string, "%Y-%m-")
        return dt.isoformat(), True
    except ValueError:
        pass

    try:
        dt = datetime.datetime.strptime(date_string, "%Y-%m")
        return dt.isoformat(), True
    except ValueError:
        pass

    try:
        dt = datetime.datetime.strptime(date_string, "%Y")
        return dt.isoformat(), True
    except ValueError:
        pass

    try:
        dt = datetime.datetime.strptime(date_string, "%Y-%m-%d")
        return dt.isoformat(), True
    except ValueError:
        pass

    try:
        dt = datetime.datetime.strptime(date_string, "%B %Y")
        return dt.isoformat(), True
    except ValueError:
        pass

    try:
        dt = datetime.datetime.strptime(date_string, "%d %B %Y")
        return dt.isoformat(), True
    except ValueError:
        pass

    try:
        dt = datetime.datetime.strptime(date_string, "%Y-%m--")
        return dt.isoformat(), True
    except ValueError:
        pass

    try:
        dt = datetime.datetime.strptime(date_string, "%b %Y")
        return dt.isoformat(), True
    except ValueError:
        pass

    try:
        dt = datetime.datetime.strptime(date_string, "%d %b %Y")
        return dt.isoformat(), True
    except ValueError:
        pass

    return date_string, False

# ----------- MAIN CLASSES ----------


class ParseGeoNamesMapping:

    place_mapper = []

    def __init__(self, filename):
        with open(filename) as f:
            csvfile = csv.reader(f)

            for row in csvfile:
                place_name = row[0].rstrip(',.')
                place_name = place_name.strip()
                url_string = row[1] if 'http://' in row[1] else F"http://{row[1]}"
                self.place_mapper.append(
                    {"placename": place_name, "url": url_string})

    @staticmethod
    def split_place_parts(place):
        place_name_parts = None
        place = place.strip()

        if ';' in place:
            place_name_parts = re.split("\s*;\s*", place)
        elif 'and' in place:
            place_name_parts = re.split('\s*and\s*', place)
        else:
            place_name_parts = [place]

        return place_name_parts

    def get_place(self, place_name):
        """
        Get the Geonames link given a string of a place
        This uses fuzzy string search library
        :param place_name:
        :return:
        """
        place_name = place_name.strip()
        matched_places = []

        place_name_parts = ParseGeoNamesMapping.split_place_parts(place_name)
        for part in place_name_parts:
            selected_item = None

            for place in self.place_mapper:
                ratio = fuzz.ratio(place['placename'], part)

                if ratio >= STRING_MATCH_RATIO:
                    selected_item = place

                    matched_places.append(place['url'])
                    break

            if not selected_item:
                # Log unmatched places
                logger.info(F"Unable to map Place {place_name}")
                UNIQUE_UNMATCHED_PLACES.add(place_name)

        return matched_places


class WritingParse:
    """
    Parses Writing files which are files of the model:
    http://cwrc.ca/schemas/orlando_writing.rng

    and schema type of: http://relaxng.org/ns/structure/1.0

    This specifically is extracting textscopes and searching for DBREFs
    in this context they are being matched with genre.

    """
    matched_documents = None
    soup = None

    def __init__(self, filename, matched_documents):

        with open(filename) as f:
            self.soup = BeautifulSoup(f, 'lxml-xml')

        self.matched_documents = matched_documents

        self.parse_db_refs()

    def parse_db_refs(self):
        """
        Maps all genres within a textscope to the given DBREF
        Used to map to blibiography
        :return: None
        """
        textscopes = self.soup.find_all('TEXTSCOPE')

        for ts in textscopes:
            ts_parent = ts.parent

            if 'DBREF' in ts.attrs:
                db_ref = ts.attrs['DBREF']

                tgenres = ts_parent.find_all('TGENRE')
                genres = []

                for genre in tgenres:
                    if 'GENRENAME' in genre.attrs:
                        name = genre.attrs['GENRENAME']
                        genres.append(name)

                self.matched_documents[db_ref] = genres


class BibliographyParse:
    """
    Class to parse a single bibliography entry

    Designed to migrate MODS XML entries to BIBFRAME RDF entries
    """

    soup = None
    mainURI = ""
    g = None
    id = ""
    relatedItem = False

    # Maps MODS types to BIBFAME types
    type_map = {
        "text": BF.Text,
        "audio": BF.Audio,
        "sound recording": BF.Audio,
        "cartography": BF.Cartography,
        "dataset": BF.Dataset,
        "mixed material": BF.MixedMaterial,
        "moving image": BF.MovingImage,
        "notated movement": BF.NotatedMovement,
        "multimedia": BF.Multimedia,
        "software, multimedia": BF.Multimedia,
        "still image": BF.StillImage,
        "object": BF.Object
    }

    # Maps MODS roles used in orlando to MARC roles
    role_map = {
        "editor": "edt",
        "translator": "trl",
        "compiler": "com",
        "adapter": "adp",
        "contributor": "ctb",
        "illustrator": "ill",
        "introduction": "win",
        "revised": "edt",
        "afterword": "aft",
        "transcriber": "trc"
    }
# Currently not handled: "original, otherFormat, otherVersion"
# See: https://lincs-cfi.slack.com/archives/D016S5Y05K2/p1617723686006600?thread_ts=1617648071.002900&cid=D016S5Y05K2
    related_item_map = {
        "host": FRBROO.R67i_forms_part_of,
        "constituent": FRBROO.R5i_is_component_of,
        "isReferencedBy": CRM.P67i_is_referenced_by,
        # "original": BF.original,
        # "otherFormat": BF.otherPhysicalFormat,
        # "otherVersion": BF.otherEdition,
        "preceding": FRBROO.R1_is_successor_of,
        "references": CRM.P67_refers_to,
        "reviewOf": CRM.P129_is_about,
        "series": FRBROO.R67i_forms_part_of,
        "succeeding": FRBROO.R1i_has_successor
    }

    def __init__(self, filename, graph, resource_name, related_item=False):
        """
        Initializes the parser
        :param filename: the filename to read from
        :param graph: an existing RDFLib graph
        :param resource_name: The name of resource which all sub-resources will be derived from
        :param related_item: if it is a related item i.e. a sub element within the XML
        """
        if type(filename) is str:
            with open(filename) as f:
                self.soup = BeautifulSoup(f, 'lxml-xml')
            self.id = self.soup.find("recordIdentifier", source="Orlando").text
        else:
            self.soup = filename

        self.filename = filename
        self.g = graph

        if ".xml" in resource_name:
            self.id = self.soup.find("recordIdentifier", source="Orlando").text
        else:
            self.id = resource_name.replace(".xml", "")

        if 'data:' in self.id:
            self.mainURI = self.id
        else:
            self.mainURI = F"http://cwrc.ca/cwrcdata/{self.id}"

        self.relatedItem = related_item

    def get_type(self):
        """
        Extracts the type of a persons role given one of the MODS types
        If a type is not mapped then a default of Text from BIBFRAME
        :return: str|URI
        """
        temp = self.soup.find_all("typeOfResource")
        if len(temp) > 1:
            logger.error("Multiple types detected! "+ self.filename)
        
        if self.soup.typeOfResource:
            resource_type = self.soup.typeOfResource.text.lower()

            return self.type_map[resource_type]
        else:
            return BF.Text

    def get_genre(self):
        """
        Extracts the genre and related authority of that genre
        :return: dict
        """
        genres = []
        for genre in self.soup.find_all("genre"):
            if 'authority' in genre.attrs:
                authority = genre['authority']
            else:
                authority = ""
            genres.append( {'genre': genre.text, 'authority': authority})
        
        return genres

    def get_title(self):
        titles = []

        for title in self.soup.find_all('titleInfo'):
            # Leave out relatedItem types
            if title.parent.name == "relatedItem" and not self.relatedItem:
                continue

            if 'usage' in title.attrs:
                usage = title.attrs['usage']
            elif 'type' in title.attrs:
                usage = title.attrs['type']
            else:
                usage = None

            if title.title:
                title_text = title.text
            else:
                title_text = ""

            titles.append({"title": title_text, "usage": usage})

        return titles

    def get_record_content_source(self):
        records = []
        for record in self.soup.find_all('recordContentSource'):
            if 'authority' in record.attrs:
                records.append(
                    {"value": record.text, "authority": record['authority']})
            else:
                records.append({"value": record.text})

        return records

    def get_record_language_catalog(self):
        records = []

        for r in self.soup.find_all("languageTerm"):
            if 'type' in r.attrs and r['type'] == "code":
                records.append(
                    {"language": r.text, "authority": r['authority'], "type": r['type']})
            else:
                records.append({"language": r.text})

        return records

    def get_record_origin(self):
        records = []

        for r in self.soup.find_all('recordOrigin'):
            records.append({"origin": r.text})

        return records

    def get_record_change_date(self):
        records = []

        for r in self.soup.find_all('recordChangeDate'):
            records.append({"date": r.text})

        return records

    def get_records(self):
        records = []
        for r in self.soup.find_all('recordInfo'):
            record = {}
            record['sources'] = []
            for source in r.find_all('recordContentSource'):
                if 'authority' in source:
                    record['sources'].append(
                        {'source': source.text, 'authority': source['authority']})
                else:
                    record['sources'].append(
                        {'source': source.text, 'authority': ""})
            record['id'] = {'id': r.recordidentifier, 'source': r.source}
            record['creationDate'] = {
                'date': r.creationDate.text, 'encoding': r.creationDate['encoding']}
            record['origin'] = {'origin': r.recordOrigin.text}

            records.append(record)
        return records

    def get_names(self):
        names = []

        for np in self.soup.find_all('name'):
            if np.parent.name == "relatedItem" and self.relatedItem == False:
                continue

            if 'type' in np.attrs:
                name_type = np['type']
            else:
                name_type = None

            role = None
            role_terms = np.find_all('roleTerm')
            for role in role_terms:
                if role['type'] == "text":
                    role = role.text

            if 'standard' in np.attrs:
                name = np.attrs['standard']
            elif np.namePart:
                name = np.namePart.get_text()

            names.append({"type": name_type, "role": role, "name": name})

        return names

    def get_places(self):
        origins = []
        if self.soup.originInfo:
            for oi in self.soup.get_all(['originInfo']):
                if oi.parent.name == 'relatedItem' and self.relatedItem == False:
                    continue
                place = oi.place.placeTerm.text
                publisher = oi.publisher.text
                date = oi.dateIssued.text
                date_type = oi.dateIssued['encoding']

                origins.append(
                    {'place': place, 'publisher': publisher, 'date': date, 'date_type': date_type})

        return origins

    def get_languages(self):
        langs = []
        for l in self.soup.find_all('language'):
            for t in l.find_all('languageTerm'):
                if 'authority' in t.attrs and t['authority'] == "iso639-2b":
                    langs.append({'language': t.text, 'type': t['type']})

        return langs

    def get_origins(self):
        origin_infos = []
        for o in self.soup.find_all('originInfo'):
            place = None
            publisher = None
            date = None
            edition = None
            dateOther = None
            if o.parent.name == 'relatedItem' and self.relatedItem == False:
                continue
            if o.publisher:
                publisher = o.publisher.text
            if o.dateIssued:
                date = o.dateIssued.text
            if o.place:
                place = o.place.placeTerm.text
            if o.edition:
                edition = o.edition.text
            if o.dateOther:
                dateOther = o.dateOther.text

            origin_infos.append({"date": date,
                                 "dateOther": dateOther,
                                 "publisher": publisher,
                                 "edition": edition,
                                 "place": place
                                 })
        return origin_infos

    def get_related_items(self):
        """
        Retrieves related works which are converted to beautifulsoup objects and run through a recursive process
        to generate the same triples as the parent
        :return: [BeautifulSoup]
        """
        related_items = self.soup.find_all('relatedItem')
        soups = []
        for item in related_items:
            item_type = "host"
            if 'type' in item.attrs:
                item_type = item.attrs['type']
            try:
                soups.append(
                    {"type": item_type, "soup": BeautifulSoup(F"{item}", 'lxml-xml')})
            except UnicodeError:
                pass

        return soups

    def get_notes(self):
        """
        Retrieves note elements in the xml and to assign to the Work
        :return: [dict] with type and content keys
        """
        note_items = self.soup.find_all('note')

        notes = []
        for note in note_items:
            if 'type' in note.attrs:
                note_type = note.attrs['type']
                # Skip over internal notes
                if note_type == "internal_note":
                    continue
            else:
                note_type = None

            note_content = note.text

            notes.append({"type": note_type, "content": note_content})

        return notes

    def get_parts(self):
        """
        Retrieves the parts of an instance
        From BIBFRAME - It will
            Concatenate values from subelements start, end, total, list to form the rdf:value
        :return: list of rdf values for the part sub-elements
        """
        part_objects = []
        if self.soup.part:
            # Get the values
            parts = self.soup.find_all('part')
            for item in parts:
                if item.parent.name == 'relatedItem' and not self.relatedItem:
                    continue
                if not item.extent:
                    continue
                cur_value = ""
                issue_num = None
                volume_num = None

                if item.extent.start:
                    cur_value += F"{item.extent.start.text}-"
                else:
                    cur_value += "--"

                if item.extent.end:
                    cur_value += F"{item.extent.end.text}"
                else:
                    cur_value += "-"

                if item.extent.total:
                    cur_value += F"{item.extent.total.text}"

                if item.extent.list:
                    cur_value += F"{item.extent.list.text}"

                # Check and go through volume and issue numbers
                if item.detail and 'type' in item.detail.attrs:
                    for detail in item.find_all('detail'):
                        detail_type = detail.attrs['type']

                        value = detail.number.text
                        if detail_type == "volume":
                            volume_num = value
                        elif detail_type == "issue":
                            issue_num = value

                part_objects.append(
                    {"issue": issue_num, "volume": volume_num, "value": cur_value})

        return part_objects

    def build_graph(self, part_type=None):
        g = self.g

        titles = self.get_title()
        resource = g.resource(self.mainURI)
        
        if not part_type:
            resource.add(RDF.type, FRBROO.F1_Work)
        elif part_type == "constituent":
            resource.add(RDF.type, FRBROO.F2_Expression)
        else:
            resource.add(RDF.type, FRBROO.F1_Work)
        
        
        resource.add(CRM.P2_has_type, self.get_type())
        
        for lang in self.get_languages():
            resource.add(CRM.P72_has_language, Literal(lang['language']))


        instance = g.resource(self.mainURI + "_instance")        
        instance.add(RDF.type, FRBROO.F2_Expression)
        instance.add(FRBROO.R3i_realises, resource)

        # CIDOC: Creating titles
        i = 0
        for item in titles:
            if 'usage' in item and item['usage'] is not None:
                title_res = g.resource(F"{self.mainURI}_title_{i}")
                title_res.add(RDF.type, CRM.E35_Title)
                title_res.add(CRM.P190_has_symbolic_content, Literal(item["title"].strip()))


                if item['usage'] == 'alternative':
                    title_res.add(CRM.P2_has_type, BF.VariantTitle)
                else:
                    title_res.add(CRM.P2_has_type, BF.Title)
                    resource.add(RDFS.label,
                                 Literal(item['title'].strip()))

                instance.add(CRM.P102_has_title, title_res)

                i += 1

        
        adminMetaData = g.resource(F"{self.mainURI}_admin_metadata")
        adminMetaData.add(RDF.type, CRM.E13_Attribute_Assignment)

        i = 0
        for r in self.get_record_content_source():
            if r['value'] in ADMIN_AGENTS:
                assigner_agent = g.resource(ADMIN_AGENTS[r["value"]])
            else:           
                assigner_agent = g.resource(F"{self.mainURI}_admin_agent_{i}")

                i += 1
            # Note: Authority value unused, values encountered: "marcorg", "oclcorg"
            assigner_agent.add(RDFS.label, Literal(r['value']))
            assigner_agent.add(RDF.type, CRM.E39_Actor)
            adminMetaData.add(CRM.P14_carried_out_by, assigner_agent)

            
        
        #CIDOC: Creating time-spans for record change
        for r in self.get_record_change_date():
            dateValue, transformed = dateParse(r['date'])
            date_bnode = BNode()
            g.add((date_bnode, RDF.type, CRM["E52_Time-Span"]))
            g.add((date_bnode, CRM.P2_has_type, BF.changeDate))
            if not transformed:
                logger.info(F"MISSING DATE FORMAT: {dateValue} on Document {self.mainURI}")
                g.add((date_bnode, RDFS.label, Literal(dateValue)))
            else:
                g.add((date_bnode, CRM.P82a_begin_of_the_begin, Literal(dateValue, datatype=XSD.datetime)))
                g.add((date_bnode, CRM.P82b_end_of_the_end,Literal(dateValue, datatype=XSD.datetime)))
            adminMetaData.add(CRM["P4_has_time-span"], date_bnode)

        #CIDOC Creating Generation Process
        i = 0
        for r in self.get_record_origin():
            generation_process = g.resource(F"{self.mainURI}_generation_process_{i}")
            generation_process.add(RDF.type, CRM.E29_Design_or_Procedure)
            generation_process.add(CRM.P2_has_type, BF.GenerationProcess)
            generation_process.add(RDFS.comment, Literal(r['origin']))

            adminMetaData.add(
                CRM.P33_used_specific_technique, generation_process)
            i += 1


        # Track this transformation
        cur_date = datetime.datetime.now()
        generation_process = g.resource(DATA.generation_process_cwrc)
        generation_process.add(RDF.type, CRM.E29_Design_or_Procedure)
        generation_process.add(CRM.P2_has_type, BF.GenerationProcess)
        generation_process.add(RDFS.comment,Literal(F"Converted from MODS to BIBFRAME RDF in {cur_date.strftime('%B')} { cur_date.strftime('%Y')} using CWRC's modsBib extraction script"))
        adminMetaData.add(CRM.P33_used_specific_technique, generation_process)

        resource.add(CRM.P140i_was_attributed_by, adminMetaData)

        i = 0
        #CIDOC: Creating publication event
        for o in self.get_origins():
            
            originInfo = g.resource(F"{self.mainURI}_activity_statement_{i}")
            originInfo.add(RDF.type, FRBROO.F28_Expression_Creation)

            j = 0
            for name in self.get_names():                
                # TODO: insert some tests surrounding names
                temp_name = urllib.parse.quote_plus(
                    remove_punctuation(name['name']))
                agent_resource=g.resource(DATA[F"{temp_name}"])
                agent_resource.add(RDFS.label, Literal(name["name"]))
                                
                # TODO: revise these possibly to roles 
                if name['type'] == 'personal':
                    agent_resource.add(RDF.type, CRM.E21_Person)
                else:
                    agent_resource.add(RDF.type, CRM.E39_Actor)
                    
                """             
               if name['type'] == 'personal':
                    agent_resource.add(RDF.type, BF.Person)
                elif name['type'] == 'family':
                    agent_resource.add(RDF.type, BF.Family)
                elif name['type'] == "corporate":
                    agent_resource.add(RDF.type, BF.Organization)
                elif name['type'] == "conference":
                    agent_resource.add(RDF.type, BF.Meeting)
                else:
                    agent_resource.add(RDF.type, BF.Agent)
                """     

                #Attaching role to the event
                if name['role'] in ROLES:
                    agent_bnode = BNode()
                    g.add((agent_bnode, RDF.type, CRMPC.PC14_carried_out_by))
                    g.add((agent_bnode, CRMPC.P02_has_range, agent_resource.identifier))
                    g.add((agent_bnode, URIRef("http://www.cidoc-crm.org/cidoc-crm/P14.1_in_the_role_of"),
                           ROLES[name['role']]))
                    originInfo.add(CRMPC.P01i_is_domain_of, agent_bnode)
                elif name['role'] != None:
                    logger.warning("Role not handled: "+str(name['role']))


                j+=1         
            
            if o['publisher']:
                publisher = g.resource(F"{self.mainURI}_activity_statement_publisher_{i}")
                publisher.add(RDF.type, CRM.E39_Actor)

                publisher_role_bnode = BNode()
                
                g.add((publisher_role_bnode,RDF.type, CRMPC.PC14_carried_out_by))
                g.add((publisher_role_bnode, CRMPC.P02_has_range, publisher.identifier))
                g.add((publisher_role_bnode, CRMPC["P14.1_in_the_role_of"],ROLES["publisher"]))
                originInfo.add(CRMPC.P01i_is_domain_of,publisher_role_bnode)
        
            if o['place']:
                place = g.resource(F"{self.mainURI}_activity_statement_place_{i}")
                place.add(RDF.value, Literal(o['place']))
                place.add(RDF.type, CRM.E53_Place)

                # TODO: review place mapping
                place_map = geoMapper.get_place(o['place'].strip())
                if place_map:
                    for item in place_map:
                        place.add(OWL.sameAs, URIRef(item))

                originInfo.add(CRM.P7_took_place_at, place)

            
            if o['date']:
                dateValue, transformed = dateParse(o['date'])
                date_bnode = BNode()
                g.add((date_bnode, RDF.type, CRM["E52_Time-Span"]))
                if not transformed:
                    logger.info(F"MISSING DATE FORMAT: {dateValue} on Document {self.mainURI}")
                    g.add((date_bnode, RDFS.label,Literal(dateValue)))
                else:
                    g.add((date_bnode, CRM.P82a_begin_of_the_begin, Literal(dateValue, datatype=XSD.datetime)))
                    g.add((date_bnode, CRM.P82b_end_of_the_end,Literal(dateValue, datatype=XSD.datetime)))
                
                originInfo.add(CRM["P4_has_time-span"],date_bnode)

            # CIDOC: Creating a manifestation, given an edition
            if o['edition']:
                instance_manifestion = g.resource(F"{self.mainURI}_instance_manifestation")
                instance_manifestion.add(RDF.type, FRBROO.F3_Manifestation)
                instance_manifestion.add(FRBROO.R4_embodies,resource)
                
                edition_node = BNode()
                instance_manifestion.add(CRM.P1_identified_by, edition_node)
                g.add((edition_node, RDF.type, CRM.E33_E41_Linguistic_Appellation))
                g.add((edition_node, CRM.P190_has_symbolic_content, Literal(o['edition'])))
                
                # TODO: Replace with URI for edition
                g.add((edition_node, CRM.P2_has_type, Literal("edition")))

            resource.add(FRBROO.R19i_was_realised_through, originInfo)
            i += 1

        i = 0
        if not self.relatedItem:
            for part in self.get_related_items():
                bp = BibliographyParse(part['soup'], self.g, "{}_{}_{}".format(
                    self.mainURI.replace("http://cwrc.ca/cwrcdata/", ""), part['type'], i), True)
                bp.build_graph(part_type=part['type'])

                if part['type'] in self.related_item_map:
                    work = g.resource(F"{self.mainURI}_{part['type']}_{i}")
                    if part["type"] == "constituent":
                        work.add(self.related_item_map[part['type']], resource)
                    else:
                        resource.add(self.related_item_map[part['type']], work)
                    i += 1

                    
                else:
                    logger.error(F"Related Item type is unmapped: {part['type']} for {self.mainURI}")

        # CIDOC: Add notes to the instance
        for n in self.get_notes():
            if n['type']:
                # NOTE: unsure what to do about note type
                # values encountered: public_note
                logger.info("NOTE TYPE: " + str(n['type']))
                # note_r.add(BF.nodeType, Literal(n['type']))

            instance.add(CRM["P3_has_note"], Literal(n['content']))

        i = 0
        # CIDOC: creating identifiers for data sources
        instance_manifestion = None
        o = self.get_origins()
        if o:
            if o[0]['edition']:
                instance_manifestion = g.resource(F"{self.mainURI}_instance_manifestation")
        for p in self.get_parts():
            extent_resource = g.resource(F"{self.mainURI}_extent_{i}")
            
            extent_resource.add(RDF.type, CRM.E33_E41_Linguistic_Appellation)
            extent_label = ""

            # NOTE: Possibly revise these URIs with further guidance
            if p['volume']:
                vol_node = BNode()
                extent_resource.add(CRM.P106_is_composed_of, vol_node)
                g.add((vol_node, RDF.type, CRM.E33_E41_Linguistic_Appellation))
                g.add((vol_node, CRM.P190_has_symbolic_content,Literal(p['volume'])))
                g.add((vol_node, CRM.P2_has_type,SCHEMA.volumeNumber))
                
                extent_label += "Volume " + p['volume']
            if p['issue']:
                issue_node = BNode()
                extent_resource.add(CRM.P106_is_composed_of, issue_node)
                g.add((issue_node, RDF.type, CRM.E33_E41_Linguistic_Appellation))
                g.add((issue_node, CRM.P190_has_symbolic_content,Literal(p['issue'])))
                g.add((issue_node, CRM.P2_has_type,SCHEMA.issueNumber))
                
                if p['volume']:
                    extent_label += ", "
                extent_label += "Issue " + p['issue']
            if p['value'] != "":
                page_node = BNode()
                extent_resource.add(CRM.P106_is_composed_of, page_node)
                g.add((page_node, RDF.type, CRM.E33_E41_Linguistic_Appellation))
                g.add((page_node, CRM.P190_has_symbolic_content,Literal(p['value'])))
                g.add((page_node, CRM.P2_has_type, Literal("page numbers")))
                
                if p['volume'] or p['issue']:
                    extent_label += ", "
                extent_label += "Page " + p['value']

            extent_resource.add(RDFS.label, Literal(extent_label))
            # TODO: Clarify if instance needs to be identified by extent:
            instance.add(CRM.P1_identified_by, extent_resource)
            if instance_manifestion:
                instance_manifestion.add(CRM.P1_identified_by, extent_resource)


        genres = self.get_genre()
        for genre in genres:
            if genre["genre"] in genre_mapping:
                uri = URIRef(genre_mapping[genre["genre"]])
                if genre_graph[uri]:
                    resource.add(CRM.P2_has_type, uri)
                else:
                    logger.warning(F"GENRE NOT FOUND: {genre['genre']}")
            else:
                    logger.warning(F"GENRE NOT FOUND: {genre['genre']}")

        # Grabbing genres extracted from Orlando files
        if self.id in genre_map:
            genres = genre_map[self.id]
            for g in genres:
                if g in genre_mapping:            
                    uri = genre_mapping[g]
                else:
                    uri = genre_mapping[g.lower()]
                uri = URIRef(uri)

                if genre_graph[uri]:
                    resource.add(CRM.P2_has_type, uri)
                else:
                    logger.info(F"GENRE NOT FOUND: {g}")

def add_types_to_graph(graph,uri,label):
    term = graph.resource(uri)
    term.add(RDF.type, CRM.E55_Type)
    term.add(RDFS.label, Literal(label))            

if __name__ == "__main__":
    g = Graph()
    g.bind("cwrc", CWRC)
    g.bind("bf", BF)
    g.bind("xml", XML, True)
    g.bind("marcrel", MARC_REL)
    g.bind("data", DATA)
    g.bind("genre", GENRE)
    g.bind("owl", OWL)
    g.bind("schema", SCHEMA)
    g.bind("crm", CRM)
    g.bind("frbroo", FRBROO)
    g.bind("crmpc", CRMPC)

    # Adding declaration of references
    for label, uri in BibliographyParse.type_map.items():
        add_types_to_graph(g,uri,label)

    for label, uri in BF_PROPERTIES.items():
        add_types_to_graph(g,uri,label)

    for label, uri in ROLES.items():
        add_types_to_graph(g,uri,label)


    config_options = {}

    try:
        with open(CONFIG_FILE) as f:
            for line in f:
                variable, value = line.split('=')
                config_options[variable] = r"{0}".format(value.strip())
    except Exception as e:
        print(e)
        print("Missing config file")
        print("Need a file with the following variables: ")
        print("WRITING_FILES=[DIRECTORY OF WRITING FILES]")
        print("GENRE_ONTOLOGY=[PATH TO GENRE ONTOLOGY]")
        print("BIBLIOGRAPHY_FILES=[DIRECTORY OF BILBIOGRAPHY FILES]")
        print("GENRE_CSV=[PATH TO GENRE MAPPING]")

    dirname = config_options['BIBLIOGRAPHY_FILES']
    writing_dir = config_options['WRITING_FILES']
    genre_ontology = config_options['GENRE_ONTOLOGY']
    places = config_options['PLACES_CSV']
    genre_map_file = config_options['GENRE_CSV']

    geoMapper = ParseGeoNamesMapping(places)

    # TODO: Eventually orlando labels should be used as hidden labels or special orlando label
    genre_graph = Graph()
    genre_graph.parse(genre_ontology)

    with open(genre_map_file) as f:
        csvfile = csv.reader(f)
        for row in csvfile:
            genre_mapping[row[0]] = row[1]

    for fname in os.listdir(writing_dir):
        path = os.path.join(writing_dir, fname)
        if os.path.isdir(path):
            continue

        try:
            genreParse = WritingParse(path, genre_map)
        except UnicodeError:
            pass

    # test_filenames = ["d75215cb-d102-4256-9538-c44bfbf490d9.xml","2e3e602e-b82c-441d-81bc-883f834b20c1.xml","13f8e71a-def5-41e4-90a0-6ae1092ae446.xml","16d427db-a8a2-4f33-ac53-9f811672584b.xml","4109f3c5-0508-447b-9f86-ea8052ff3981.xml"]
    # test_filenames = ["64d3c008-8a9d-415b-b52b-91d232c00952.xml",
                    #   "e1b2f98f-1001-4787-a711-464f1527e5a7.xml", "15655c66-8c0b-4493-8f68-8d6cf4998303.xml"]
    # for fname in os.listdir(dirname):
    for fname in test_filenames:

        path = os.path.join(dirname, fname)
        if os.path.isdir(path):
            continue

        if not fname:
            continue
        try:
            mp = BibliographyParse(path, g, fname)
            mp.build_graph()
        except UnicodeError:
            pass

    with open("unmatchedplaces.csv", "w") as f:
        writer = csv.writer(f, delimiter='\t', quoting=csv.QUOTE_MINIMAL)
        for item in UNIQUE_UNMATCHED_PLACES:
            writer.writerow([item])

    fname = "Bibliography"
    output_name = fname.replace(".xml", "")
    formats = {'ttl': 'turtle'}  # 'xml': 'pretty-xml'
    print(len(g))
    for extension, file_format in formats.items():
        g.serialize(destination=F"{output_name}.{extension}", format=file_format)
