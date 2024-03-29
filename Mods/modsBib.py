from bs4 import BeautifulSoup
import rdflib
from rdflib import RDF, RDFS, OWL, XSD
import os
import datetime
import csv
import logging
from fuzzywuzzy import fuzz
import re
import urllib.parse

CONFIG_FILE = "./bibparse.config"

# ----------- SETUP LOGGER ------------

logger = logging.getLogger('bibliography_extraction')
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(levelname)s {Line #%(lineno)d} : %(message)s ')
fh = logging.FileHandler('bibliography_extraction.log', mode="w")
fh.setFormatter(formatter)
fh.setLevel(logging.INFO)
logger.addHandler(fh)
logger.info(
    F"Started extraction: {datetime.datetime.now().strftime('%d %b %Y %H:%M:%S')}")

# ---------- SETUP NAMESPACES ----------

EVENT = rdflib.Namespace("http://id.lincsproject.ca/event/")
ORLANDO = rdflib.Namespace("https://commons.cwrc.ca/orlando:")
BF = rdflib.Namespace("http://id.loc.gov/ontologies/bibframe/")
XML = rdflib.Namespace("http://www.w3.org/XML/1998/namespace")
MARC_REL = rdflib.Namespace("http://id.loc.gov/vocabulary/relators/")
DATA = rdflib.Namespace("http://cwrc.ca/cwrcdata/")
TEMP = rdflib.Namespace("http://www.temp.lincsproject.ca/")
# <http://www.temp.lincsproject.ca/> .


LINCS = rdflib.Namespace("http://id.lincsproject.ca/")
GENRE = rdflib.Namespace("http://id.lincsproject.ca/genre/")
SCHEMA = rdflib.Namespace("http://schema.org/")
SKOS = rdflib.Namespace("http://www.w3.org/2004/02/skos/core#")
FRBROO = rdflib.Namespace("http://iflastandards.info/ns/fr/frbr/frbroo/")
CRMPC = rdflib.Namespace("http://www.cidoc-crm.org/cidoc-crm/")
CRM = rdflib.Namespace("http://www.cidoc-crm.org/cidoc-crm/")

GETTY = rdflib.Namespace("https://vocab.getty.edu/aat/")
TGN = rdflib.Namespace("https://vocab.getty.edu/tgn/")
GEONAMES = rdflib.Namespace("https://sws.geonames.org/")

BF_PROPERTIES = {
    "change date": BF.changeDate,
    "variant title": BF.VariantTitle,
    "title": BF.Title,
    "generation process": BF.GenerationProcess
}

# To reduce duplication of admin agents
ADMIN_AGENTS = {
    "Orlando Document Archive": LINCS.z7dHu6axJWK,
    "Canadian Writing Research Collaboratory": LINCS.Ph49VISFM8m,
    "CaAEU": LINCS.zBnrYP48rmJ,
    "UAB": LINCS.zBosqEEBC6a,
    "U3G": LINCS.zBoaS2NkStT,
    "Orlando: Women's Writing in the British Isles from the Beginnings to the Present": LINCS.zBkArbArQww,
}

ROLES = {
    "publisher": MARC_REL.pbl,
    "editor": MARC_REL.edt,
    "translator": MARC_REL.trl,
    "compiler": MARC_REL.com,
    "adapter": MARC_REL.adp,
    "adaptor": MARC_REL.adp,
    "contributor": MARC_REL.ctb,
    "illustrator": MARC_REL.ill,
    "introduction": MARC_REL.win,
    "revised": MARC_REL.edt,
    "afterword": MARC_REL.aft,
    "transcriber": MARC_REL.trc,
    "author": MARC_REL.aut,
    "recipient": MARC_REL.rcp
}

GENRE_GRAPH = None
URI_TO_GENRE_MAPPING = {}  # TITLE URIs to GENRE labels
GEOMAPPER = None
GENRE_MAPPING = {}  # labels to vocab URIs
STRING_MATCH_RATIO = 95

PUBLISHER_MAPPING = {}
PEOPLE_MAPPING = {}

USED_GENRES = []
UNIQUE_UNMATCHED_PLACES = set()
AGENTS = {}

# --------- UTILITY FUNCTIONS -------


def remove_punctuation(input_str, all_punctuation=False):
    """
    Removes punctuation as defined by the Extraction doc
    This is primarily used for normalizing person URIs so they relate
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


def get_next_month(date):
    # Returns date with next occurring month, ex. 2019-10-1 --> 2019-11-1, or 2012-12-01 --> 2013-01-01,
    # note this only guaranteed to work for date.days <= 28, and may fail for dates later than so.
    return datetime.datetime(date.year+1 if date.month == 12 else date.year, 1 if date.month == 12 else date.month + 1, date.day)


def dateParse(date_string: str, both=True):
    # Currently works for single dates need to examine patterns further for 2 days
    # Strip spaces surrounding the date string
    date_string = date_string.strip().rstrip()
    end_dt = None
    
    try:
        dt = datetime.datetime.strptime(date_string, "%Y-%m-%d")
        end_dt = dt + datetime.timedelta(days=1, seconds=-1)
        return dt.isoformat(), True, end_dt.isoformat()
    except ValueError:
        pass
    try:
        dt = datetime.datetime.strptime(date_string, "%Y-%m-%d-")
        end_dt = dt + datetime.timedelta(days=1, seconds=-1)
        return dt.isoformat(), True, end_dt.isoformat()
    except ValueError:
        pass
    try:
        dt = datetime.datetime.strptime(date_string, "%Y--")
        end_dt = dt.replace(year=dt.year+1) - datetime.timedelta(seconds=1)
        return dt.isoformat(), True, end_dt.isoformat()
    except ValueError:
        pass
    try:
        dt = datetime.datetime.strptime(date_string, "%Y-")
        end_dt = dt.replace(year=dt.year+1) - datetime.timedelta(seconds=1)
        return dt.isoformat(), True, end_dt.isoformat()
    except ValueError:
        pass

    try:
        dt = datetime.datetime.strptime(date_string, "%Y")
        end_dt = dt.replace(year=dt.year+1) - datetime.timedelta(seconds=1)
        return dt.isoformat(), True, end_dt.isoformat()
    except ValueError:
        pass

    try:
        dt = datetime.datetime.strptime(date_string, "%Y-%m-")
        end_dt = get_next_month(dt) - datetime.timedelta(seconds=1)
        return dt.isoformat(), True, end_dt.isoformat()
    except ValueError:
        pass

    try:
        dt = datetime.datetime.strptime(date_string, "%Y-%m")
        end_dt = get_next_month(dt) - datetime.timedelta(seconds=1)
        return dt.isoformat(), True, end_dt.isoformat()
    except ValueError:
        pass

    try:
        dt = datetime.datetime.strptime(date_string, "%B %Y")
        end_dt = get_next_month(dt) - datetime.timedelta(seconds=1)
        return dt.isoformat(), True, end_dt.isoformat()
    except ValueError:
        pass

    try:
        dt = datetime.datetime.strptime(date_string, "%d %B %Y")
        end_dt = dt + datetime.timedelta(days=1, seconds=-1)
        return dt.isoformat(), True, end_dt.isoformat()
    except ValueError:
        pass

    try:
        dt = datetime.datetime.strptime(date_string, "%Y-%m--")
        end_dt = get_next_month(dt) - datetime.timedelta(seconds=1)
        return dt.isoformat(), True, end_dt.isoformat()
    except ValueError:
        pass

    try:
        dt = datetime.datetime.strptime(date_string, "%b %Y")
        end_dt = get_next_month(dt) - datetime.timedelta(seconds=1)
        return dt.isoformat(), True, end_dt.isoformat()
    except ValueError:
        pass

    try:
        dt = datetime.datetime.strptime(date_string, "%d %b %Y")
        end_dt = dt + datetime.timedelta(days=1, seconds=-1)
        return dt.isoformat(), True, end_dt.isoformat()
    except ValueError:
        pass

    return date_string, False, date_string

# ----------- MAIN CLASSES ----------


class ParseGeoNamesMapping:

    place_mapper = []

    def __init__(self, filename):
        with open(filename) as f:
            csvfile = csv.reader(f)

            for row in csvfile:
                place_name = row[0].rstrip(',.')
                place_name = place_name.strip()
                url_string = row[1] if 'https://' in row[1] else F"https://{row[1]}"
                self.place_mapper.append(
                    {"placename": place_name, "url": url_string})

    @staticmethod
    def split_place_parts(place):
        place_name_parts = None
        place = place.strip()

        if ';' in place:
            place_name_parts = re.split("\s*;\s*", place)
        elif 'and' in place:
            place_name_parts = re.split('\s* and \s*', place)
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
        mapped_places = {}

        place_name_parts = ParseGeoNamesMapping.split_place_parts(place_name)
        for part in place_name_parts:
            selected_item = None

            for place in self.place_mapper:
                ratio = fuzz.ratio(place['placename'], part)

                if ratio >= STRING_MATCH_RATIO:
                    selected_item = place

                    matched_places.append(place['url'])
                    mapped_places[part] = place['url']
                    break

            if not selected_item:
                # Log unmatched places
                logger.info(F"Unable to map Place {place_name}")
                UNIQUE_UNMATCHED_PLACES.add(place_name)

        return mapped_places


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
        self.filename = filename
        self.parse_db_refs()

    def parse_db_refs(self):
        """
        Maps all genres within a textscope to the given DBREF
        Used to map to bibliography
        :return: None
        """
        textscopes = self.soup.find_all('TEXTSCOPE')

        for ts in textscopes:
            ts_parent = ts.parent
            rec_id = None

            # Using REF attribute over DBREF
            if 'REF' in ts.attrs:
                rec_id = ts.attrs['REF'].split(":")[2]
            elif 'DBREF' in ts.attrs:
                rec_id = ts.attrs['DBREF']

            # Extracting Genres
            if rec_id:
                tgenres = ts_parent.find_all('TGENRE')
                genres = []

                for genre in tgenres:
                    if 'GENRENAME' in genre.attrs:
                        name = genre.attrs['GENRENAME']
                        genres.append(name)

                if rec_id in self.matched_documents:
                    for x in genres:
                        if x not in self.matched_documents[rec_id]:
                            self.matched_documents[rec_id].append(x)
                else:
                    self.matched_documents[rec_id] = list(set(genres))

            else:
                logger.error(F"TEXTSCOPE ({ts}) missing REF & DBREF attribute from {self.filename}")


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

    # Maps MODS types to BIBFRAME types
    type_map = {
        "text": GENRE.TextualMedium,
        "audio": GENRE.AuditoryMedium,
        "sound recording": GENRE.SoundRecordingMedium,
        "cartography": GENRE.CartographicForm,
        "dataset": GENRE.DigitalMedium,
        "mixed material": GENRE.mixedMaterials,
        "moving image": GENRE.MovingMedium,
        "notated movement": GENRE.PerformanceMedium,
        "multimedia": GENRE.multimedia,
        "software, multimedia": GENRE.multimedia,
        "still image": GENRE.StillImageMedium,
        "object": GENRE.threeDimensionalObject
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
        "host": CRM.P148_has_component,
        "constituent": FRBROO.R5i_is_component_of,
        "iconstituent": FRBROO.R5_has_component,
        "isReferencedBy": CRM.P67i_is_referenced_by,
        "preceding": FRBROO.R1_is_logical_successor_of,
        "references": CRM.P67_refers_to,
        "reviewOf": CRM.P129_is_about,
        "series": CRM.P148i_is_component_of,
        "succeeding": FRBROO.R1i_has_successor
        # "original": BF.original,
        # "otherFormat": BF.otherPhysicalFormat,
        # "otherVersion": BF.otherEdition,
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
        else:
            self.soup = filename

        self.filename = filename
        self.g = graph
        self.mainTitle = None
        self.id = resource_name.replace(".xml", "")
        self.old_id = self.id

        # print("===")
        # print(filename, graph, resource_name, related_item)
        # print("===")

        # TODO: update this to use cwrc identifiers
        if ".xml" in resource_name:
            self.old_id = self.soup.find("recordIdentifier", source="Orlando")
            if self.old_id:
                self.old_id = self.old_id.text
            else:
                self.old_id = resource_name.replace(".xml", "")
        else:
            self.old_id = resource_name.replace(".xml", "")

        if 'temp_lincs_temp:' in self.id or "temp.lincsproject" in self.id:  # TODO: Review: What's wrong with this?
            self.mainURI = self.id
            self.placeholderURI = self.id
        elif "https://commons.cwrc.ca/orlando:" in self.id:
            self.mainURI = self.id
            self.placeholderURI = TEMP[F"{self.id.split('orlando:')[1]}"]
        else:  # Level 1 work
            self.mainURI = F"https://commons.cwrc.ca/orlando:{self.id}"
            self.placeholderURI = TEMP[F"{self.id}"]

        self.relatedItem = related_item

    def get_type(self):
        """
        Extracts the type of a persons role given one of the MODS types
        If a type is not mapped then a default of Text from BIBFRAME
        :return: str|URI
        """
        temp = self.soup.find_all("typeOfResource")
        if len(temp) > 1:
            logger.error("Multiple types detected! " + self.filename)

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
            genres.append({'genre': genre.text, 'authority': authority})

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
                title_text = title.text.strip().replace("\n", " ").replace("\t", " ")
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
            record['id'] = {'id': r.recordIdentifier, 'source': r.source}
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
            else:
                name = "None"
                logger.warning(F"No name found: {np}")

            alt = None
            if np.displayForm:
                alt = np.displayForm.get_text()

            uri = None
            if "valueURI" in np.attrs:
                uri = np.attrs["valueURI"]

            names.append({"type": name_type, "role": role,
                          "name": name, "uri": uri, "altname": alt})

        return names

    def get_languages(self):
        langs = []
        for l in self.soup.find_all('language'):
            for t in l.find_all('languageTerm'):
                if 'authority' in t.attrs and t['authority'] == "iso639-2b":
                    label = t.text
                    if label == "eng":
                        label = "English"
                    elif label == "fre":
                        label = "French"
                    elif label == "ger":
                        label = "German"
                    elif label == "lat":
                        label = "Latin"
                    elif label == "spa":
                        label = "Spanish"

                    langs.append(
                        {'language': t.text, 'type': t['type'], 'label': label})

        return langs

    def get_origins(self):
        def get_dates(tag):
            # will return String, start, end_date
            date_string = None
            start_date = None
            end_date = None

            for x in tag.find_all("dateIssued"):
                if x.get("type") == "start":
                    start_date = x.text
                elif x.get("type") == "end":
                    end_date = x.text
                elif x.get("encoding") == "iso8601":
                    date_string = x.text

            return date_string, start_date, end_date

        origin_infos = []
        for o in self.soup.find_all('originInfo'):
            place = None
            publisher = None
            publisher_uri = None
            date = None
            edition = None
            dateOther = None
            start_date = None
            end_date = None
            date_string = None
            if o.parent.name == 'relatedItem' and self.relatedItem == False:
                continue
            if o.publisher:
                publisher = o.publisher.text
                if "valueURI" in o.publisher.attrs:
                    publisher_uri = o.publisher["valueURI"]
            if o.dateIssued:
                date_string, start_date, end_date = get_dates(o)
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
                                 "publisher uri": publisher_uri,
                                 "edition": edition,
                                 "place": place,
                                 "date string": date_string,
                                 "start date": start_date,
                                 "end date": end_date
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

    def get_main_title(self, titles):
        for x in titles:
            if x['usage'] == 'primary':
                self.mainTitle = x['title'].strip().replace(
                    "\n", " ").replace("\t", " ")
                return

    def get_person_id(self, uri):
        person = None
        if uri:
            if uri in PEOPLE_MAPPING:
                person = PEOPLE_MAPPING[uri]
            else:
                person = uri

        return person

    def get_publisher_id(self, origin, index):
        publisher = None
        if origin['publisher uri']:
            if origin['publisher uri'] in PUBLISHER_MAPPING:
                publisher = PUBLISHER_MAPPING[origin['publisher uri']]
            elif origin['publisher'] in PUBLISHER_MAPPING:
                publisher = PUBLISHER_MAPPING[origin['publisher']]
            elif origin['publisher uri'] in PEOPLE_MAPPING:
                publisher = PEOPLE_MAPPING[origin['publisher uri']]
            else:
                publisher = origin['publisher uri']
        else:
            if origin['publisher'] in PUBLISHER_MAPPING:
                publisher = PUBLISHER_MAPPING[origin['publisher']]
            else:
                publisher = F"{self.placeholderURI}_activity_statement_publisher_{index}"
        return publisher

    def build_graph(self, part_type=None):
        g = self.g

        titles = self.get_title()
        self.get_main_title(titles)
        resource = g.resource(self.mainURI)  # The Work

        if not part_type:
            resource.add(RDF.type, FRBROO.F1_Work)
        elif part_type == "constituent":
            resource.add(RDF.type, FRBROO.F2_Expression)
        else:
            resource.add(RDF.type, FRBROO.F1_Work)

        if self.mainTitle is not None:
            resource.add(RDFS.label, rdflib.Literal(self.mainTitle))

        resource.add(CRM.P2_has_type, self.get_type())

        for lang in self.get_languages():
            language_uri = rdflib.URIRef(
                F"http://id.loc.gov/vocabulary/languages/{lang['language']}")
            resource.add(CRM.P72_has_language, language_uri)
            # TODO may want to add this to biography extraction instead
            add_types_to_graph(
                g, language_uri, lang['label'], CRM.E56_Language)

        instance = None
        # The Expression
        instance = g.resource(self.placeholderURI + "_instance")
        instance.add(RDF.type, FRBROO.F2_Expression)
        instance.add(FRBROO.R3i_realises, resource)

        # CIDOC: Creating titles
        i = 0

        for item in titles:
            if 'usage' in item and item['usage'] is not None:
                title_res = g.resource(F"{self.placeholderURI}_title_{i}")
                title_res.add(RDF.type, CRM.E33_E41_Linguistic_Appellation)
                title_res.add(CRM.P190_has_symbolic_content,
                              rdflib.Literal(item["title"].strip()))

                if item['usage'] == 'alternative':
                    title_res.add(RDFS.label, rdflib.Literal(
                        F"Alternate title of {self.mainTitle}", lang="en"))
                    title_res.add(CRM.P2_has_type, GETTY["300417227"])
                else:
                    title_res.add(CRM.P2_has_type, GETTY["300417193"])
                    title_res.add(RDFS.label, rdflib.Literal(
                        F"Title of {self.mainTitle}", lang="en"))

                if instance:
                    instance.add(CRM.P1_is_identified_by, title_res)
                    instance.add(RDFS.label, rdflib.Literal(
                        F"expression of {self.mainTitle}", lang="en"))
                else:
                    resource.add(CRM.P1_is_identified_by, title_res)
                i += 1

        adminMetaData = g.resource(F"{self.placeholderURI}_admin_metadata")
        adminMetaData.add(RDF.type, CRM.E13_Attribute_Assignment)
        adminMetaData.add(RDFS.label, rdflib.Literal(
            (F"administrative metadata {'of the creation of the MODS record for '+ self.mainTitle}") if self.mainTitle else "administrative metadata of MODS record", lang="en"))

        i = 0
        for r in self.get_record_content_source():
            if r['value'] in ADMIN_AGENTS:
                assigner_agent = g.resource(ADMIN_AGENTS[r["value"]])
            else:
                assigner_agent = g.resource(
                    F"{self.placeholderURI}_admin_agent_{i}")

                i += 1
            # Note: Authority value unused, values encountered: "marcorg", "oclcorg"
            assigner_agent.add(
                RDFS.label, rdflib.Literal(r['value'], lang="en"))
            assigner_agent.add(RDF.type, CRM.E39_Actor)
            adminMetaData.add(CRM.P14_carried_out_by, assigner_agent)

        # CIDOC: Creating time-spans for record change (<recordChangeDate>)
        r_count = 1
        for r in self.get_record_change_date():
            start_date, transformed, end_date = dateParse(r['date'])
            time_span = g.resource(
                F"{self.placeholderURI}_time-span_{r_count}")
            time_span.add(RDFS.label, rdflib.Literal(
                F"time-span of modification of MODS record for {self.mainTitle}", lang="en"))
            time_span.add(RDF.type, CRM["E52_Time-Span"])
            time_span.add(CRM["P82_at_some_time_within"],
                          rdflib.Literal(r['date'], lang="en"))
            time_span.add(CRM.P2_has_type, BF.changeDate)
            if not transformed:
                logger.info(
                    F"MISSING DATE FORMAT: {start_date} on Document {self.mainURI}")
            else:

                time_span.add(CRM.P82a_begin_of_the_begin, rdflib.Literal(
                    start_date, datatype=XSD.dateTime))
                time_span.add(CRM.P82b_end_of_the_end, rdflib.Literal(
                    end_date, datatype=XSD.dateTime))

            adminMetaData.add(CRM["P4_has_time-span"], time_span)
            r_count += 1

        # CIDOC Creating Generation Process
        generation_process = g.resource(LINCS.z7kKbF0M7cw)
        generation_process.add(RDF.type, CRM.E29_Design_or_Procedure)
        generation_process.add(CRM.P2_has_type, BF.GenerationProcess)
        generation_process.add(RDFS.comment, rdflib.Literal(
            "Record has been transformed into MODS from an XML Orlando record using an XSLT stylesheet. Metadata originally created in Orlando Document Archive's bibliographic database formerly available at nifflheim.arts.ualberta.ca/wwp.", lang="en"))
        generation_process.add(RDFS.label, rdflib.Literal(
            F"generation process of the MODS Record of Orlando bibiliographic records", lang="en"))
        adminMetaData.add(CRM.P33_used_specific_technique, generation_process)
        resource.add(CRM.P140i_was_attributed_by, adminMetaData)

        i = 0
        # CIDOC: Creating publication event/expression creation
        for o in self.get_origins():

            originInfo = g.resource(
                F"{self.placeholderURI}_activity_statement_{i}")
            originInfo.add(RDF.type, CRM.E65_Creation)
            originInfo.add(CRM.P2_has_type, EVENT.ProductionEvent)
            originInfo.add(CRM.P2_has_type, EVENT.PublishingEvent)

            originInfo.add(RDFS.label, rdflib.Literal(
                F"creation of {self.mainTitle}", lang="en"))
            if instance:
                originInfo.add(CRM.P94_has_created, instance)

            j = 0
            for name in self.get_names():
                # TODO: insert some tests surrounding names

                agent_resource = None
                agent_internal_ID = None  # This will keep the cwrc id for the agent
                if "uri" in name and name["uri"]:
                    agent_resource = self.get_person_id(name["uri"])
                    if agent_resource:
                        agent_resource = g.resource(agent_resource)

                if agent_resource == None:
                    temp_name = urllib.parse.quote_plus(
                        remove_punctuation(name['name']))
                    agent_resource = g.resource(TEMP[F"{temp_name}"])
                    agent_internal_ID = str(TEMP[F"{temp_name}"])
                elif "orlando" in str(agent_resource.identifier):
                    agent_internal_ID = str(agent_resource.identifier)
                else:
                    agent_internal_ID = name["uri"]

                agent_resource.add(RDFS.label, rdflib.Literal(name["name"]))

                # TODO: revise these possibly to roles
                if name['type'] == 'personal':
                    agent_resource.add(RDF.type, CRM.E21_Person)
                else:
                    agent_resource.add(RDF.type, CRM.E39_Actor)

                if "altname" in name and name["altname"]:
                    agent_resource.add(
                        SKOS.altLabel, rdflib.Literal(name["altname"]))

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

                # Attaching role to the event
                if name['role'] in ROLES or name['role'] is None:
                    if name['role'] is None:
                        name['role'] = "author"
                    agent_label = F"{name['name']} in role of {name['role']}"
                    uri = None
                    if agent_label in AGENTS:
                        uri = AGENTS[agent_label]
                    else:
                        if "orlando" in str(agent_internal_ID):
                            temp = TEMP[f"{str(agent_internal_ID).split('orlando:')[1]}_{name['role']}"]
                            AGENTS[agent_label] = temp
                            uri = temp
                        else:
                            uri = f"{str(agent_resource.identifier)}_{name['role']}"
                            AGENTS[agent_label] = rdflib.URIRef(uri)

                    agent = g.resource(uri)
                    agent.add(RDFS.label, rdflib.Literal(
                        agent_label, lang="en"))
                    agent.add(RDF.type, CRMPC.PC14_carried_out_by)
                    agent.add(CRMPC.P02_has_range, agent_resource.identifier)
                    agent.add(rdflib.URIRef("http://www.cidoc-crm.org/cidoc-crm/P14.1_in_the_role_of"),
                              ROLES[name['role']])
                    originInfo.add(CRMPC.P01i_is_domain_of, agent)
                elif name['role'] is None:
                    logger.warning("Role not handled: "+str(name['role']))

                j += 1

            if o['publisher']:
                publisher = g.resource(self.get_publisher_id(o, i))
                o['publisher_id'] = str(publisher.identifier)

                publisher.add(RDF.type, CRM.E39_Actor)
                publisher.add(SKOS.altLabel, rdflib.Literal(
                    F"{o['publisher']}"))
                publisher.add(CRM.P2_has_type, ROLES["publisher"])

                publisher_role = g.resource(
                    F"{self.placeholderURI}_publisher_role_{i}")
                publisher_role.add(RDFS.label, rdflib.Literal(
                    F"{o['publisher']} in the role of publisher", lang="en"))

                publisher_role.add(RDF.type, CRMPC.PC14_carried_out_by)
                publisher_role.add(CRMPC.P02_has_range, publisher.identifier)
                publisher_role.add(
                    CRMPC["P14.1_in_the_role_of"], ROLES["publisher"])

                originInfo.add(CRMPC.P01i_is_domain_of, publisher_role)

            # Adding place of publication
            if o['place']:
                place_map = GEOMAPPER.get_place(o['place'].strip())
                if place_map:
                    for item in place_map:
                        place = g.resource(place_map[item])
                        originInfo.add(CRM.P7_took_place_at, place)
                        place.add(SKOS.altLabel, rdflib.Literal(item))
                        place.add(RDF.type, CRM.E53_Place)

            # Adding date of publication
            if o['date']:
                start_date = None
                transformed = None
                end_date = None
                if o['start date']:
                    start_date, transformed, end_date = dateParse(
                        o['start date'], o)

                if o['end date']:
                    end_date, transformed, dump = dateParse(o['end date'], o)
                    
                time_span = g.resource(F"{self.placeholderURI}_time-span_{i}")
                time_span.add(RDFS.label, rdflib.Literal(
                    (F"time-span {'of the publishing of '+ self.mainTitle}") if self.mainTitle else "creation time-span", lang="en"))
                time_span.add(RDF.type, CRM["E52_Time-Span"])
                time_span.add(CRM["P82_at_some_time_within"],
                              rdflib.Literal(o['date'], lang="en"))
                time_span.add(CRM.P2_has_type, BF.changeDate)
                
                if not transformed:
                    logger.info(
                        F"UNABLE TO PARSE DATE FORMAT: '{o['date']}' on Document {self.mainURI}")
                else:
                    if start_date:
                        time_span.add(CRM.P82a_begin_of_the_begin, rdflib.Literal(
                            start_date, datatype=XSD.dateTime))
                    else:
                        logger.info(
                            F"MISSING START DATE: {start_date} from '{o['date']}' on Document {self.mainURI}")
                    if end_date:
                        time_span.add(CRM.P82b_end_of_the_end, rdflib.Literal(
                            end_date, datatype=XSD.dateTime))
                    else:
                        logger.info(
                            F"MISSING END DATE: {end_date} from '{o['date']}' on Document {self.mainURI}")
                        

                originInfo.add(CRM["P4_has_time-span"], time_span)

            # CIDOC: Creating a linguistic appellation, given an edition
            if o['edition']:
                edition_node = g.resource(F"{self.placeholderURI}_edition")

                instance.add(CRM.P1_is_identified_by, edition_node)
                edition_node.add(RDF.type, CRM.E33_E41_Linguistic_Appellation)
                edition_node.add(CRM.P190_has_symbolic_content,
                                 rdflib.Literal(o['edition']))

                edition_node.add(CRM.P2_has_type, GETTY["300121294"])

            resource.add(CRM.P94i_was_created_by, originInfo)
            i += 1

        i = 0
        if not self.relatedItem:
            for part in self.get_related_items():

                # use placeholder uri for related works
                bp = BibliographyParse(
                    part['soup'], self.g, F"{self.placeholderURI}_{part['type']}_{i}", True)
                bp.build_graph(part_type=part['type'])

                if part['type'] in self.related_item_map:
                    work = g.resource(
                        F"{self.placeholderURI}_{part['type']}_{i}")
                    if bp.mainTitle is None:
                        work.add(RDFS.label, rdflib.Literal(
                            F"{part['type']} of {self.mainTitle}", lang="en"))
                    if part["type"] == "constituent":
                        work.add(self.related_item_map[part['type']], instance)
                        instance.add(
                            self.related_item_map["i"+part['type']], work)
                    else:
                        resource.add(self.related_item_map[part['type']], work)
                    i += 1

                else:
                    logger.error(
                        F"Related Item type is unmapped: {part['type']} for {self.mainURI}")

        # CIDOC: Add notes to the instance
        for n in self.get_notes():
            if n['type']:
                # NOTE: unsure what to do about note type
                # values encountered: public_note
                logger.info("NOTE TYPE: " + str(n['type']))
                # note_r.add(BF.nodeType, rdflib.Literal(n['type']))
            if instance:
                instance.add(CRM["P3_has_note"], rdflib.Literal(n['content']))

        i = 0
        # CIDOC: creating identifiers for data sources

        # TODO: Extent is only connected to instances, what happens to other versions?

        instance_manifestion = None

        o = self.get_origins()

        for p in self.get_parts():
            extent_resource = g.resource(F"{self.placeholderURI}_extent_{i}")

            extent_resource.add(RDF.type, CRM.E33_E41_Linguistic_Appellation)
            extent_label = ""

            # NOTE: Possibly revise these URIs with further guidance
            if p['volume']:
                vol_node = g.resource(
                    F"{self.placeholderURI}_extent_{i}_volume")
                extent_resource.add(CRM.P106_is_composed_of, vol_node)
                vol_node.add(RDF.type, CRM.E33_E41_Linguistic_Appellation)
                vol_node.add(CRM.P190_has_symbolic_content,
                             rdflib.Literal(p['volume']))
                vol_node.add(CRM.P2_has_type, SCHEMA.volumeNumber)
                extent_label += "Volume " + p['volume']

            if p['issue']:
                issue_node = g.resource(
                    F"{self.placeholderURI}_extent_{i}_issue")
                extent_resource.add(CRM.P106_is_composed_of, issue_node)
                issue_node.add(RDF.type, CRM.E33_E41_Linguistic_Appellation)
                issue_node.add(CRM.P190_has_symbolic_content,
                               rdflib.Literal(p['issue']))
                issue_node.add(CRM.P2_has_type, SCHEMA.issueNumber)

                if p['volume']:
                    extent_label += ", "
                extent_label += "Issue " + p['issue']
            if p['value'] != "":
                page_node = g.resource(
                    F"{self.placeholderURI}_extent_{i}_page")
                extent_resource.add(CRM.P106_is_composed_of, page_node)
                page_node.add(RDF.type, CRM.E33_E41_Linguistic_Appellation)
                page_node.add(CRM.P190_has_symbolic_content,
                              rdflib.Literal(p['value']))
                page_node.add(CRM.P2_has_type, rdflib.URIRef(
                    "http://www.wikidata.org/entity/Q11325816"))

                if p['volume'] or p['issue']:
                    extent_label += ", "
                extent_label += "Page " + p['value']

            extent_resource.add(
                RDFS.label, rdflib.Literal(extent_label, lang="en"))

            # TODO: Clarify if instance needs to be identified by extent:
            if instance:
                instance.add(CRM.P1_is_identified_by, extent_resource)

        genres = self.get_genre()
        for genre in genres:
            genre["genre"] = genre["genre"].lower()
            if genre["genre"] in GENRE_MAPPING:
                uri = rdflib.URIRef(GENRE_MAPPING[genre["genre"]])
                if GENRE_GRAPH[uri]:
                    resource.add(CRM.P2_has_type, uri)
                    USED_GENRES.append(uri)
                else:
                    logger.warning(F"GENRE NOT FOUND: {genre['genre']}")
            else:
                logger.warning(F"GENRE NOT FOUND: {genre['genre']}")

        # Grabbing genres extracted from Orlando files
        if self.id in URI_TO_GENRE_MAPPING:
            genres = URI_TO_GENRE_MAPPING[self.id]
            for genre in genres:
                if genre in GENRE_MAPPING:
                    uri = GENRE_MAPPING[genre]
                else:
                    if genre.lower() in GENRE_MAPPING:
                        uri = GENRE_MAPPING[genre.lower()]
                    else:
                        logger.warning(F"GENRE NOT FOUND: {genre}")
                        continue
                uri = rdflib.URIRef(uri)

                if (uri, None, None) in GENRE_GRAPH:
                    resource.add(CRM.P2_has_type, uri)
                    USED_GENRES.append(uri)
                else:
                    logger.info(F"GENRE NOT FOUND: {genre}")


def add_types_to_graph(graph, uri, label, rdf_type=CRM.E55_Type):
    term = graph.resource(uri)
    term.add(RDF.type, rdf_type)
    term.add(RDFS.label, rdflib.Literal(label, lang="en"))


def create_testcases(id):
    if id == "p82a value not formatted":
        return [
            "0b681cee-b42c-4a63-ad65-c0af45b62ce8.xml",
            "1383fa3f-1165-4ff4-b2dd-c95c75fc2c13.xml",
            "02d7c5d7-c35c-4014-937c-7ac3293ca5da.xml",
            "51a0f1ac-a935-4030-af4c-1efa386311e2.xml",
            "5fded5be-698c-44a6-b5d9-dcfc916a3080.xml",
            "586f3760-ca74-4719-86af-f272db0e871a.xml",
            "78c6593a-e40c-4315-8579-e2f626c32097.xml",
            "8e367bab-26fe-4737-a660-1b347512f39d.xml",
            "7a1b0250-e39c-4b23-9e1a-0628875b8ee9.xml",
            "c024cc20-b224-4262-9cf7-7b75fa77d6af.xml",
            "ff1e9376-9e49-4ee7-885c-6c43fd8529fb.xml",
            "ece7a309-06ab-484d-9b6e-327673760d6e.xml",
            "061d2321-dfb5-4f44-942c-9a7e65c21a94.xml",
            "5bed980f-5550-4947-912c-932d2b93d8c4.xml",
            "51ede06d-3b58-49f8-8aed-fa22a68b7155.xml",
            "5cf828b7-c0da-4325-883c-823f77dd9fe0.xml",
            "d9b4b496-aee5-4045-b6d6-b87038ff3b95.xml",
            "d51fb7d2-333f-450e-ab4d-4b0c786f9807.xml",
            "a35fcb83-5f4c-482f-8834-eb8afb8f3500.xml",
        ]
    elif id == "no start/end date":
        return [
            "1f1b99ae-40c8-41a8-9e33-c18be9329999.xml",
            "2d1112bc-5ca3-449b-8a22-dca0063785eb.xml"
            "4e8d76d2-6b8e-4a71-a26e-3844686385ab.xml"
        ]
    elif id == "part of series":
        return ["e6180094-ba76-4020-991d-1e8c68a9d20a.xml",
                "e1b2f98f-1001-4787-a711-464f1527e5a7.xml", "15655c66-8c0b-4493-8f68-8d6cf4998303.xml", "0d0e00bf-3224-4286-8ec4-f389ec6cc7bb.xml",  # VW, the wave
                "005eb7df-fada-4d13-8206-8c30ec309ece.xml", "73bddacf-9be7-49a9-bc6b-05f5928f823d.xml"]
    return None


if __name__ == "__main__":
    g = rdflib.Graph()
    g.bind("event", EVENT)
    g.bind("bf", BF)
    g.bind("xml", XML, True)
    g.bind("marcrel", MARC_REL)
    g.bind("data", DATA)
    g.bind("genre", GENRE)
    g.bind("owl", OWL)
    g.bind("schema", SCHEMA)
    g.bind("crm", CRM)
    g.bind("frbroo", FRBROO)
    g.bind("skos", SKOS)
    g.bind("orlando", ORLANDO)
    g.bind("aat", GETTY)
    g.bind("geonames", GEONAMES)
    g.bind("tgn", TGN)
    g.bind("lincs", LINCS)
    g.bind("temp_lincs_temp", TEMP)

    # Adding declaration of references
    for label, uri in BibliographyParse.type_map.items():
        add_types_to_graph(g, uri, label)

    for label, uri in BF_PROPERTIES.items():
        add_types_to_graph(g, uri, label)

    for label, uri in ROLES.items():
        add_types_to_graph(g, uri, label)

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
        print("GENRE_VOCAB=[PATH TO GENRE VOCAB]")
        print("BIBLIOGRAPHY_FILES=[DIRECTORY OF BILBIOGRAPHY FILES]")
        print("GENRE_CSV=[PATH TO GENRE MAPPING]")
        print("PUBLISHER_CSV=[PATH TO PUBLISHER MAPPING]")
        print("PEOPLE_CSV=[PATH TO PEOPLE MAPPING]")

    dirname = config_options['BIBLIOGRAPHY_FILES']
    writing_dir = config_options['WRITING_FILES']
    genre_ontology = config_options['GENRE_VOCAB']
    places = config_options['PLACES_CSV']
    URI_TO_GENRE_MAPPING_file = config_options['GENRE_CSV']
    publishers_file = config_options['PUBLISHERS_CSV']
    people_file = config_options['PEOPLE_CSV']

    GEOMAPPER = ParseGeoNamesMapping(places)

    # TODO: Eventually orlando labels should be used as hidden labels or special orlando label
    GENRE_GRAPH = rdflib.Graph()
    GENRE_GRAPH.parse(genre_ontology)

    with open(URI_TO_GENRE_MAPPING_file) as f:
        csvfile = csv.reader(f)
        for row in csvfile:
            GENRE_MAPPING[row[0]] = row[1]

    with open(publishers_file) as f:
        csvfile = csv.reader(f)
        for row in csvfile:
            PUBLISHER_MAPPING[row[0]] = row[1]

    with open(people_file) as f:
        csvfile = csv.reader(f)
        for row in csvfile:
            PEOPLE_MAPPING[row[0]] = row[1]

    for fname in os.listdir(writing_dir):
        path = os.path.join(writing_dir, fname)
        if os.path.isdir(path):
            continue

        try:
            genreParse = WritingParse(path, URI_TO_GENRE_MAPPING)
        except UnicodeError:
            pass

    # test_filenames = create_testcases("p82a value not formatted")
    test_filenames = None

    if not test_filenames:
        test_filenames = os.listdir(dirname)

    count = 1
    total = len(test_filenames)
    for fname in test_filenames:
        print(F"{count}/{total} files extracted: {fname}")
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
        count += 1

    # Adding labels for Genres used
    USED_GENRES = list(set(USED_GENRES))
    for genre in USED_GENRES:
        query = """
SELECT ?label
WHERE {
  <%s> rdfs:label ?label .
  FILTER (langMatches(lang(?label), 'en'))
}
""" % genre

        label = [row[0].value for row in GENRE_GRAPH.query(query)][0]
        add_types_to_graph(g, genre, label)

    with open("unmatchedplaces.csv", "w") as f:
        writer = csv.writer(f, delimiter='\t', quoting=csv.QUOTE_MINIMAL)
        for unmatched_place in UNIQUE_UNMATCHED_PLACES:
            writer.writerow([unmatched_place])

    fname = F"bibliography_{datetime.datetime.now().strftime('%Y-%m-%d')}"
    output_name = fname.replace(".xml", "")
    formats = {'ttl': 'turtle'}
    for extension, file_format in formats.items():
        g.serialize(
            destination=F"{output_name}.{extension}", format=file_format)

logger.info(
    F"Finished extraction: {datetime.datetime.now().strftime('%d %b %Y %H:%M:%S')}")
