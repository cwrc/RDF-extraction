from bs4 import BeautifulSoup
import rdflib, sys
from rdflib import RDF, RDFS, OWL, XSD
import os, datetime
import csv

import logging
from fuzzywuzzy import fuzz
import re

CONFIG_FILE="./bibparse.config"

# ----------- SETUP LOGGER ------------

logger = logging.getLogger('bibliography_extraction')
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(levelname)s {Line #%(lineno)d} : %(message)s ')
fh = logging.FileHandler('bibliography_extraction.log', mode="w")
fh.setLevel(logging.INFO)
logger.addHandler(fh)
logger.info(
    F"Started extraction: {datetime.datetime.now().strftime('%d %b %Y %H:%M:%S')}")

# ---------- SETUP NAMESPACES ----------


BF = rdflib.Namespace("http://id.loc.gov/ontologies/bibframe/")
CWRC = rdflib.Namespace("http://sparql.cwrc.ca/ontologies/cwrc#")
DATA = rdflib.Namespace("http://cwrc.ca/cwrcdata/")
FRBROO = rdflib.Namespace("http://iflastandards.info/ns/fr/frbr/frbroo/")
GENRE = rdflib.Namespace("http://sparql.cwrc.ca/ontologies/genre#")
MARC_REL = rdflib.Namespace("http://id.loc.gov/vocabulary/relators/")
MARCREL = rdflib.Namespace("http://id.loc.gov/vocabulary/relators/")
SCHEMA = rdflib.Namespace("http://schema.org/")
SKOS = rdflib.Namespace("http://www.w3.org/2004/02/skos/core#")
XML = rdflib.Namespace("http://www.w3.org/XML/1998/namespace")

# To reduce duplication of admin agents
ADMIN_AGENTS = {
    "Orlando Document Archive": DATA.Orlando_Document_Archive,
    "CaAEU": DATA.CaAEU,
    "UAB": DATA.UAB,
    "U3G": DATA.U3G,
    "Orlando: Women's Writing in the British Isles from the Beginnings to the Present": DATA.Orlando,
}

genre_graph = None

genre_map = {} # from writing parsing
genre_mapping = {} # genre mapping from CSV
geoMapper = None
STRING_MATCH_RATIO = 90

UNIQUE_UNMATCHED_PLACES = set()
FORMS = []
MEDIUMS = []
AGENTS = {}



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
    # from unidecode import unidecode
    import urllib.parse
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
    return urllib.parse.quote_plus(input_str)



def dateParse(date_string: str):

    # Strip spaces surrounding the date string
    date_string = date_string.strip().rstrip()

    try:
        dt = datetime.datetime.strptime(date_string, "%Y-%m-%d")
        return dt.isoformat().split("T")[0], True
    except ValueError:
        pass
    try:
        dt = datetime.datetime.strptime(date_string, "%Y--")
        return dt.isoformat().split("T")[0], True
    except ValueError:
        pass
    try:
        dt = datetime.datetime.strptime(date_string, "%Y-")
        return dt.isoformat().split("T")[0], True
    except ValueError:
        pass

    try:
        dt = datetime.datetime.strptime(date_string, "%Y")
        return dt.isoformat().split("T")[0], True
    except ValueError:
        pass

    try:
        dt = datetime.datetime.strptime(date_string, "%Y-%m-")
        return dt.isoformat().split("T")[0], True
    except ValueError:
        pass

    try:
        dt = datetime.datetime.strptime(date_string, "%Y-%m")
        return dt.isoformat().split("T")[0], True
    except ValueError:
        pass

    try:
        dt = datetime.datetime.strptime(date_string, "%Y")
        return dt.isoformat().split("T")[0], True
    except ValueError:
        pass

    try:
        dt = datetime.datetime.strptime(date_string, "%B %Y")
        return dt.isoformat().split("T")[0], True
    except ValueError:
        pass

    try:
        dt = datetime.datetime.strptime(date_string, "%d %B %Y")
        return dt.isoformat().split("T")[0], True
    except ValueError:
        pass

    try:
        dt = datetime.datetime.strptime(date_string, "%Y-%m--")
        return dt.isoformat().split("T")[0], True
    except ValueError:
        pass

    try:
        dt = datetime.datetime.strptime(date_string, "%b %Y")
        return dt.isoformat().split("T")[0], True
    except ValueError:
        pass

    try:
        dt = datetime.datetime.strptime(date_string, "%d %b %Y")
        return dt.isoformat().split("T")[0], True
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
                url_string = row[1] if 'http://' in row[1] else "http://{0}".format(row[1])
                self.place_mapper.append({"placename": place_name, "url": url_string})

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
                logger.warning("Unable to map place: {0}".format(place_name))
                UNIQUE_UNMATCHED_PLACES.add(place_name)

        return matched_places


class WritingParse:
    """
    Parses Writing files which are files of the model:
    http://cwrc.ca/schemas/orlando_writing.rng

    and schema type of: http://relaxng.org/ns/structure/1.0

    This specifically is extracting textscopes and searching for dbrefs
    in this context they are being matched with genre.

    """
    matched_documents = None
    soup = None
    def __init__(self, filename, matched_documents):

        with open(filename,encoding='utf-8') as f:
            self.soup = BeautifulSoup(f, 'lxml-xml')
        

        self.matched_documents = matched_documents

        self.parse_db_refs()

    def parse_db_refs(self):
        """
        Maps all genres within a textscope to the given ref/dbref
        Used to map to bibliography
        :return: None
        """
        textscopes = self.soup.find_all('TEXTSCOPE')

        for ts in textscopes:
            ts_parent = ts.parent
            rec_id = None
            if 'REF' in ts.attrs:
                rec_id = ts.attrs['REF'].split(":")[2]
                
            elif 'DBREF' in ts.attrs:
                rec_id = ts.attrs['DBREF']

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
                logger.error("TEXTSCOPE missing REF & DBREF attribute")
                

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
        "transcriber": "trc",
        "recipient":"rcp",
        "rcp":"rcp"
    }

    related_item_map = {
        "host": BF.partOf,
        "constituent": BF.partOf,
        "isReferencedBy": BF.referencedBy,
        "original": BF.original,
        "otherFormat": BF.otherPhysicalFormat,
        "otherVersion": BF.otherEdition,
        "preceding": BF.precededBy,
        "references": BF.references,
        "reviewOf": BF.review,
        "series": BF.hasSeries,
        "succeeding": BF.succeededBy
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
            with open(filename, 'r',encoding='utf-8') as f:
                self.soup = BeautifulSoup(f, 'lxml-xml')
        else:
            self.soup = filename

        self.filename = filename
        self.mainTitle = None
        self.g = graph
        self.id = resource_name.replace(".xml", "")
        self.old_id = self.id
        #TODO: update this to use cwrc identifiers
        if ".xml" in resource_name:
            self.old_id = self.soup.find("recordIdentifier", source="Orlando")
            if self.old_id:
                self.old_id = self.old_id.text
            else:
                self.old_id = resource_name.replace(".xml", "")
        else:
            self.old_id = resource_name.replace(".xml", "")


        if 'data:' in self.id:
            self.mainURI = self.id
        elif "https://commons.cwrc.ca/orlando:" in self.id:
            self.mainURI = self.id
        else:
            self.mainURI = F"https://commons.cwrc.ca/orlando:{self.id}"
    
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
            # Leave out relateditem types
            if title.parent.name == "relatedItem" and not self.relatedItem:
                continue

            if 'usage' in title.attrs:
                usage = title.attrs['usage']
            elif 'type' in title.attrs:
                usage = title.attrs['type']
            else:
                usage = None

            if title.title:
                title_text = title.text.strip()
            else:
                title_text = ""

            titles.append({"title": title_text, "usage": usage})

        return titles

    def get_record_content_source(self):
        records = []
        for record in self.soup.find_all('recordContentSource'):
            if 'authority' in record.attrs:
                records.append({"value": record.text, "authority": record['authority']})
            else:
                records.append({"value": record.text})

        return records

    def get_record_language_catalog(self):
        records = []

        for r in self.soup.find_all("languageTerm"):
            if 'type' in r.attrs and  r['type'] == "code":
                records.append({"language": r.text, "authority": r['authority'], "type": r['type']})
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
                    record['sources'].append({'source': source.text, 'authority': source['authority']})
                else:
                    record['sources'].append({'source': source.text, 'authority': ""})
            record['id'] = {'id': r.recordIdentifier, 'source': r.source}
            record['creationDate'] = {'date': r.creationDate.text, 'encoding': r.creationDate['encoding']}
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
                else:
                    role = role.text
                    # continue


            if 'standard' in np.attrs:
                name = np.attrs['standard']
            elif np.namePart:
                name = np.namePart.get_text()
            else:
                name = None
                logger.warning(F"No name found: {np}")
                
            alt = None
            if np.displayForm:
                alt = np.displayForm.get_text()

            uri = None
            if "valueURI" in np.attrs:
                uri = np.attrs["valueURI"]

            names.append({"type": name_type, "role": role, "name": name, "uri":uri, "altname":alt})
        return names

    def get_places(self):
        origins = []
        if self.soup.origininfo:
            for oi in self.soup.get_all(['originInfo']):
                if oi.parent.name == 'relatedItem' and self.relatedItem == False:
                    continue
                place = oi.place.placeTerm.text
                publisher = oi.publisher.text
                date = oi.dateIssued.text
                date_type = oi.dateIssued['encoding']

                origins.append({'place': place, 'publisher': publisher, 'date': date, 'date_type': date_type})

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
            publisher_uri = None
            date = None
            edition = None
            dateOther = None
            if o.parent.name == 'relatedItem' and self.relatedItem == False:
                continue
            if o.publisher:
                publisher = o.publisher.text
                if "valueURI" in o.publisher.attrs:
                    publisher_uri = o.publisher["valueURI"]
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
                                 "publisher uri": publisher_uri,
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
            item_type="host"
            if 'type' in item.attrs:
                item_type = item.attrs['type']
            try:
                soups.append({"type": item_type, "soup": BeautifulSoup(F"{item}", 'lxml-xml')})
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

                part_objects.append({"issue": issue_num, "volume": volume_num, "value": cur_value})

        return part_objects


    def get_main_title(self, titles):
        for x in titles:
            if x['usage'] == 'primary':
                self.mainTitle = x['title'].strip().replace("\n"," ").replace("\t"," ")
                return
    
   
    def build_graph(self):
        g = self.g
        i = 0


        titles = self.get_title()
        self.get_main_title(titles)
        resource = g.resource(self.mainURI)
        resource.add(RDF.type, BF.Work)
        instance = g.resource(self.mainURI + "_instance")
        instance.add(RDF.type, BF.Instance)
        instance.add(BF.instanceOf, resource)

        if self.mainTitle is not None:
            resource.add(RDFS.label, rdflib.Literal(self.mainTitle))

        for item in titles:
            if 'usage' in item and item['usage'] is not None:
                title_res = g.resource("{}_title_{}".format(self.mainURI, i))

                title_res.add(BF.mainTitle, rdflib.Literal(item["title"].strip()))
                if item['usage'] == 'alternative':
                    title_res.add(RDF.type, BF.VariantTitle)
                else:
                    title_res.add(RDF.type, BF.Title)
                    resource.add(RDFS.label, rdflib.Literal(item['title'].strip()))
                # Schema.org attributes per spreadsheet for BIBFRAME matching
                title_res.add(RDF.type, SCHEMA.CreativeWork)

                instance.add(BF.title, title_res)

                i += 1

        i = 0

        resource.add(RDF.type, self.get_type())

        for name in self.get_names():
            # contribution_resource = g.resource(self.mainURI + "#contribution_{}".format(i))
            
            agent_resource = None
            if "uri" in name and name["uri"]:
                agent_resource=g.resource(name["uri"])
            else:
                temp_name = remove_punctuation(name['name'])
                agent_resource=g.resource(DATA[F"{temp_name}"])
         

            if name['role'] in self.role_map:
                role = MARCREL[self.role_map[name['role']]]
            elif name['role']:
                role = rdflib.Literal(name["role"])
            else:
                role = MARCREL.aut
            
            if role and "id.loc" in role:
                role = role.split("/")[-1]
                
            
            agent_label = F"{name['name']} in role of {role}"
            uri = None
            if agent_label in AGENTS:
                uri = AGENTS[agent_label]
            else:
                if "orlando" in str(agent_resource.identifier):
                    temp = DATA[f"{agent_resource.identifier.split('orlando:')[1]}_{role}"]                        
                    AGENTS[agent_label] = temp
                    uri = temp
                else:
                    uri = f"{agent_resource.identifier}_{role}"
            
          
            contribution_resource = g.resource(uri)
            contribution_resource.add(RDF.type, BF.Contribution)

      
            
            # agent_resource = g.resource(self.mainURI + "#agent_{}".format(i))
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

            agent_resource.add(RDFS.label, rdflib.Literal(name["name"]))
            # role_resource = g.resource("{}#contribution_{}_role".format(self.mainURI, i))
            # role_resource.add(RDF.type, BF.Role)

            if name['role'] in self.role_map:
                # role_resource.add(BF.code, rdflib.Literal(self.role_map[name['role']]))
                # role_resource.add(BF.source, MARCREL[self.role_map[name['role']]])
                contribution_resource.add(BF.role,MARCREL[self.role_map[name['role']]])
            if name['role']:
                # role_resource.add(RDFS.label, rdflib.Literal(name["role"]))
                contribution_resource.add(BF.role,rdflib.Literal(name["role"]))
            else:
                contribution_resource.add(BF.role,MARCREL.aut)
                # role_resource.add(BF.code, rdflib.Literal("aut"))
                # role_resource.add(BF.source, MARCREL.aut)
                # role_resource.add(RDFS.label, rdflib.Literal("author"))

            contribution_resource.add(BF.agent, agent_resource)
            # bf:role marcrel:aut
            # contribution_resource.add(BF.role, role_resource)

            resource.add(BF.contribution, contribution_resource)

            i += 1

        for lang in self.get_languages():
            resource.add(XML.lang, rdflib.Literal(lang['language']))

        adminMetaData = g.resource("{}_admin_metadata".format(self.mainURI))

        i = 0
        for r in self.get_record_content_source():
            if r['value'] in ADMIN_AGENTS:
                assigner_agent = g.resource(ADMIN_AGENTS[r["value"]])
            else:           
                assigner_agent = g.resource(F"{self.mainURI}_admin_agent_{i}")

                i += 1
            
            assigner_agent.add(RDFS.label, rdflib.Literal(r['value']))
            assigner_agent.add(RDF.type, BF.Agent)



            # if 'authority' in r:
            #     source_agent = g.resource("{}_admin_agent_source_{}".format(self.mainURI, i))
            #     source_agent.add(RDF.type, BF.Source)
            #     source_agent.add(RDF.value, rdflib.Literal(r['authority']))
            #     assigner_agent.add(BF.source, source_agent)

            adminMetaData.add(BF.assigner, assigner_agent)


        for r in self.get_record_change_date():

            dateValue, transformed = dateParse(r['date'])
            if not transformed:
                logger.info("MISSING DATE FORMAT: {} on Document {}".format(dateValue, self.mainURI))
            adminMetaData.add(BF.changeDate, rdflib.Literal(dateValue, datatype=XSD.date))

        i = 0
        for r in self.get_record_origin():
            if r['origin'] == "Record has been transformed into MODS from an XML Orlando record using an XSLT stylesheet. Metadata originally created in Orlando Document Archive's bibliographic database formerly available at nifflheim.arts.ualberta.ca/wwp.":
                generation_process = g.resource(DATA.generation_process_xslt)
                generation_process.add(RDF.type, BF.GenerationProcess)
                generation_process.add(RDF.value, rdflib.Literal(r['origin']))
                generation_process.add(RDFS.comment,rdflib.Literal(r['origin']))
                generation_process.add(RDFS.label, rdflib.Literal(F"generation process of the MODS Record of Orlando bibiliographic records"))

            else:
                generation_process = g.resource("{}_generation_process_{}".format(self.mainURI, i))
                generation_process.add(RDF.type, BF.GenerationProcess)
                generation_process.add(RDF.value, rdflib.Literal(r['origin']))

            adminMetaData.add(BF.generationProcess, generation_process)

        i = 0
        for r in self.get_record_language_catalog():
            if (len(r['language'])) < 5:
                adminMetaData.add(BF.descriptionLanguage, rdflib.URIRef(F"http://id.loc.gov/vocabulary/languages/{r['language']}"))
            else:
                adminMetaData.add(BF.descriptionLanguage, rdflib.Literal(r['language']))



        resource.add(BF.adminMetadata, adminMetaData)


        i = 0

        for o in self.get_origins():
            originInfo = g.resource("{}_activity_statement_{}".format(self.mainURI, i))
            if o['publisher']:
                if o['publisher uri']:
                    publisher = g.resource(o['publisher uri'])
                else:
                    publisher = g.resource(DATA[remove_punctuation(o['publisher'])])
                    publisher = g.resource("{}_activity_statement_publisher_{}".format(self.mainURI, i))
                
                publisher.add(RDF.type, BF.Agent)
                publisher.add(RDFS.label, rdflib.Literal(o['publisher']))
                publisher.add(BF.role, MARCREL.pbl)

                originInfo.add(BF.provisionActivity, publisher)
            if o['place']:
                place = g.resource("{}_activity_statement_place_{}".format(self.mainURI, i))
                place.add(RDF.value, rdflib.Literal(o['place']))
                place.add(RDF.type, BF.Place)

                place_map = geoMapper.get_place(o['place'].strip())

                if place_map:
                    for item in place_map:
                        place.add(OWL.sameAs, rdflib.URIRef(item))

                originInfo.add(BF.place, place)

            if o['date']:
                originInfo.add(RDF.type, BF.Publication)
                dateValue, transformed = dateParse(o['date'])
                if not transformed:
                    logger.info("MISSING DATE FORMAT: {} on Document {}".format(dateValue, self.mainURI))
                originInfo.add(BF.date, rdflib.Literal(dateValue, datatype=XSD.date))

            if o['edition']:
                instance.add(BF.editionStatement, rdflib.Literal(o['edition']))

            i += 1

            resource.add(BF.provisionActivity, originInfo)

        i = 0
        if not self.relatedItem:
            for part in self.get_related_items():
                bp = BibliographyParse(part['soup'], self.g, "{}_{}_{}".format(self.mainURI.replace("http://cwrc.ca/cwrcdata/", ""), part['type'], i), True)
                bp.build_graph()

                work = g.resource("{}_part_{}".format(self.mainURI, i))
                resource.add(self.related_item_map[part['type']], work)
                i += 0

        i = 0

        # Add notes to the instance
        for n in self.get_notes():
            note_r = g.resource("{}_note_{}".format(self.mainURI, i))
            note_r.add(RDF.type, BF.Note)
            note_r.add(RDF.value, rdflib.Literal(n['content']))
            if n['type']:
                note_r.add(BF.nodeType, rdflib.Literal(n['type']))

            i += 0

            instance.add(BF.note, note_r)

        i = 0
        # Add parts to the instance
        for p in self.get_parts():
            extent_resource = g.resource("{}_extent_{}".format(self.mainURI, i))
            extent_resource.add(RDF.type, BF.Extent)
            if p['value'] != "":
                extent_resource.add(RDF.value, rdflib.Literal(p['value']))
            if p['volume']:
                extent_resource.add(SCHEMA.volumeNumber, rdflib.Literal(p['volume']))
            if p['issue']:
                extent_resource.add(SCHEMA.issueNumber, rdflib.Literal(p['issue']))

            instance.add(BF.extent, extent_resource)

        genres = self.get_genre()


        for genre in genres:
            genre["genre"] = genre["genre"].lower()
            if genre["genre"] in genre_mapping:
                uri = rdflib.URIRef(genre_mapping[genre["genre"]])
                if genre_graph[uri]:

                    if uri in FORMS:
                        resource.add(GENRE.hasForm, uri)
                    elif uri in MEDIUMS:
                        resource.add(GENRE.hasMedium, uri)
                    else:
                        resource.add(GENRE.hasGenre, uri)

                else:
                    logger.warning(F"GENRE NOT FOUND: {genre['genre']}")
            else:
                    logger.warning(F"GENRE NOT FOUND: {genre['genre']}")

        if self.id in genre_map:
            genres = genre_map[self.id]
            for genre in genres:
                if genre in genre_mapping:            
                    uri = genre_mapping[genre]
                else:
                    uri = genre_mapping[genre.lower()]
                uri = rdflib.URIRef(uri)

                if genre_graph[uri]:
                    if uri in FORMS:
                        resource.add(GENRE.hasForm, uri)
                    elif uri in MEDIUMS:
                        resource.add(GENRE.hasMedium, uri)
                    else:
                        resource.add(GENRE.hasGenre, uri)
                else:
                    logger.info(F"GENRE NOT FOUND: {genre}")



if __name__ == "__main__":
#     g = rdflib.Graph()
#     g.bind("bf", BF)
#     g.bind("cwrc", CWRC)
#     g.bind("data", DATA)
#     g.bind("frbroo", FRBROO)
#     g.bind("genre", GENRE)
#     g.bind("marcrel", MARC_REL)
#     g.bind("marcrel", MARCREL)
#     g.bind("owl", OWL)
#     g.bind("schema", SCHEMA)
#     g.bind("skos", SKOS)
#     g.bind("xml", XML, True)
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


#     geoMapper = ParseGeoNamesMapping(places)

#     genre_graph = rdflib.Graph()
#     genre_graph.parse(genre_ontology)

#     with open(genre_map_file) as f:
#         csvfile = csv.reader(f)
#         for row in csvfile:
#             genre_mapping[row[0]] = row[1]

#     # Retrieving genre:Forms to determine correct predicate to use
#     res = genre_graph.query("""SELECT ?s WHERE { ?s rdf:type*/rdfs:subClassOf* <http://sparql.cwrc.ca/ontologies/genre#Form>
# . }""")
#     FORMS = [ row.s for row in res]
#     res = genre_graph.query("""SELECT ?s WHERE { ?s rdf:type*/rdfs:subClassOf* <http://sparql.cwrc.ca/ontologies/genre#Medium>
# . }""")
#     MEDIUMS = [ row.s for row in res]


#     for fname in os.listdir(writing_dir):
#         path = os.path.join(writing_dir, fname)
#         if os.path.isdir(path):
#             continue

#         try:
#             genreParse = WritingParse(path, genre_map)
#         except UnicodeError:
#             pass

#     # test_filenames = ["e57c7868-a3b7-460e-9f20-399fab7f894c.xml"]
#     # test_filenames = ["0d0e00bf-3224-4286-8ec4-f389ec6cc7bb.xml"]
#     test_filenames = ["55aff3fb-8ea9-4e95-9e04-0f3e630896e3.xml", "0c133817-f55e-4a8f-a9b4-474566418d9b.xml"]

    count = 1
    total = len(os.listdir(dirname))
    # for fname in test_filenames:
    for fname in os.listdir(dirname):
        # print(F"{count}/{total} files extracted ({fname})")

        path = os.path.join(dirname, fname)
        if os.path.isdir(path):
            continue

        if not fname:
            continue
        with open(path,encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'lxml-xml')
            genres = soup.find_all("genre")
            for x in genres:
                if x.text == "article":
                    # print (x.text)
                    print(soup)
                    print("<!--  Next Record below  -->")
            # input()
        # try:
        #     mp = BibliographyParse(path, g, fname)
        #     mp.build_graph()
        # except UnicodeError:
        #     pass
        count +=1

    exit()

    with open("unmatchedplaces.csv", "w") as f:
        writer = csv.writer(f, delimiter='\t', quoting=csv.QUOTE_MINIMAL)
        for item in UNIQUE_UNMATCHED_PLACES:
            writer.writerow([item])

    fname = "bibliography"
    output_name = fname.replace(".xml", "")
    formats = {'ttl': 'turtle'} # 'xml': 'pretty-xml'
    for extension, file_format in formats.items():
        g.serialize(destination=F"{output_name}.{extension}", format=file_format,encoding="utf-8")

logger.info(F"Finished extraction: {datetime.datetime.now().strftime('%d %b %Y %H:%M:%S')}")