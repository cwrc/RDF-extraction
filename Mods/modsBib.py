from bs4 import BeautifulSoup
import rdflib, sys
import os, datetime
import csv
from rdflib import *
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

CWRC = rdflib.Namespace( "http://sparql.cwrc.ca/ontologies/cwrc#")
BF = rdflib.Namespace( "http://id.loc.gov/ontologies/bibframe/")
XML = rdflib.Namespace("http://www.w3.org/XML/1998/namespace")
MARCREL = rdflib.Namespace("http://id.loc.gov/vocabulary/relators/")
DATA = rdflib.Namespace("http://cwrc.ca/cwrcdata/")
GENRE = rdflib.Namespace("http://sparql.cwrc.ca/ontologies/genre#")
SCHEMA = rdflib.Namespace("http://schema.org/")

genre_graph = None
genre_map = {}
geoMapper = None
STRING_MATCH_RATIO = 80

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
        print(place_name_parts)
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
                logger.info("Unable to map Place {0}".format(place_name))
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

        with open(filename) as f:
            self.soup = BeautifulSoup(f, 'lxml')

        self.matched_documents = matched_documents

        self.parse_db_refs()

    def parse_db_refs(self):
        """
        Maps all genres within a textscope to the given dbref
        Used to map to blibiography
        :return: None
        """
        textscopes = self.soup.find_all('textscope')

        for ts in textscopes:
            ts_parent = ts.parent

            if 'dbref' in ts.attrs:
                db_ref = ts.attrs['dbref']

                tgenres = ts_parent.find_all('tgenre')
                genres = []

                for genre in tgenres:
                    if 'genrename' in genre.attrs:
                        name = genre.attrs['genrename']
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
            with open(filename) as f:
                self.soup = BeautifulSoup(f, 'lxml')
        else:
            self.soup = filename

        self.g = graph
        self.id = resource_name.replace(".xml", "")
        if 'data:' in self.id:
            self.mainURI = self.id
        else:
            self.mainURI = "{}{}".format("http://cwrc.ca/cwrcdata/", self.id)
            
        self.relatedItem = related_item

    def get_type(self):
        """
        Extracts the type of a persons role given one of the MODS types
        If a type is not mapped then a default of Text from BIBFRAME
        :return: str|URI
        """
        if self.soup.typeofresource:
            resource_type = self.soup.typeofresource.text.lower()

            return self.type_map[resource_type]
        else:
            return BF.Text

    def get_genre(self):
        """
        Extracts the genre and related authority of that genre
        :return: dict
        """
        if self.soup.genre:
            if 'authority' in self.soup.genre:
                authority = self.soup.genre['authority']
            else:
                authority = ""
            return {'genre': self.soup.genre.text, 'authority': authority}

    def get_title(self):
        titles = []


        for title in self.soup.find_all('titleinfo'):
            # Leave out relateditem types
            if title.parent.name == "relateditem" and not self.relatedItem:
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
        for record in self.soup.find_all('recordcontentsource'):
            if 'authority' in record.attrs:
                records.append({"value": record.text, "authority": record['authority']})
            else:
                records.append({"value": record.text})

        return records

    def get_record_language_catalog(self):
        records = []

        for r in self.soup.find_all("languageterm"):
            if 'type' in r.attrs and  r['type'] == "code":
                records.append({"language": r.text, "authority": r['authority'], "type": r['type']})
            else:
                records.append({"language": r.text})

        return records

    def get_record_origin(self):
        records = []

        for r in self.soup.find_all('recordorigin'):
            records.append({"origin": r.text})

        return records

    def get_record_change_date(self):
        records = []

        for r in self.soup.find_all('recordchangedate'):
            records.append({"date": r.text})

        return records

    def get_records(self):
        records = []
        for r in self.soup.find_all('recordinfo'):
            record = {}
            record['sources'] = []
            for source in r.find_all('recordcontentsource'):
                if 'authority' in source:
                    record['sources'].append({'source': source.text, 'authority': source['authority']})
                else:
                    record['sources'].append({'source': source.text, 'authority': ""})
            record['id'] = {'id': r.recordidentifier, 'source': r.source}
            record['creationdate'] = {'date': r.creationdate.text, 'encoding': r.creationdate['encoding']}
            record['origin'] = {'origin': r.recordorigin.text}

            records.append(record)
        return records

    def get_names(self):
        names = []

        for np in self.soup.find_all('name'):
            if np.parent.name == "relateditem" and self.relatedItem == False:
                continue

            if 'type' in np.attrs:
                name_type = np['type']
            else:
                name_type = None

            role = None
            role_terms = np.find_all('roleterm')
            for role in role_terms:
                if role['type'] == "text":
                    role = role.text

            if 'standard' in np.attrs:
                name = np.attrs['standard']
            elif np.namepart:
                name = np.namepart.get_text()



            names.append({"type": name_type, "role": role, "name": name})

        return names

    def get_places(self):
        origins = []
        if self.soup.origininfo:
            for oi in self.soup.get_all(['origininfo']):
                if oi.parent.name == 'relateditem' and self.relatedItem == False:
                    continue
                place = oi.place.placeterm.text
                publisher = oi.publisher.text
                date = oi.dateissued.text
                date_type = oi.dateissued['encoding']

                origins.append({'place': place, 'publisher': publisher, 'date': date, 'date_type': date_type})

        return origins

    def get_languages(self):
        langs = []
        for l in self.soup.find_all('language'):
            for t in l.find_all('languageterm'):
                if 'authority' in t.attrs and t['authority'] == "iso639-2b":
                    langs.append({'language': t.text, 'type': t['type']})

        return langs

    def get_origins(self):
        origin_infos = []
        for o in self.soup.find_all('origininfo'):
            place = None
            publisher = None
            date = None
            edition = None
            dateOther = None
            if o.parent.name == 'relateditem' and self.relatedItem == False:
                continue
            if o.publisher:
                publisher = o.publisher.text
            if o.dateissued:
                date = o.dateissued.text
            if o.place:
                place = o.place.placeterm.text
            if o.edition:
                edition = o.edition.text
            if o.dateother:
                dateOther = o.dateother.text

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
        related_items = self.soup.find_all('relateditem')
        soups = []
        for item in related_items:
            item_type="host"
            if 'type' in item.attrs:
                item_type = item.attrs['type']
            try:
                print("{}".format(item))
                soups.append({"type": item_type, "soup": BeautifulSoup("{}".format(item), 'lxml')})
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
                if item.parent.name == 'relateditem' and not self.relatedItem:
                    continue
                if not item.extent:
                    continue
                cur_value = ""
                issue_num = None
                volume_num = None

                if item.extent.start:
                    cur_value += "{}-".format(item.extent.start.text)
                else:
                    cur_value += "--"

                if item.extent.end:
                    cur_value += "{}".format(item.extent.end.text)
                else:
                    cur_value += "-"

                if item.extent.total:
                    cur_value += "{}".format(item.extent.total.text)

                if item.extent.list:
                    cur_value += "{}".format(item.extent.total.text)

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


    def build_graph(self):
        g = self.g
        i = 0

        titles = self.get_title()
        resource = g.resource(self.mainURI)
        resource.add(RDF.type, BF.Work)

        instance = g.resource(self.mainURI + "_instance")
        instance.add(RDF.type, BF.Instance)
        instance.add(BF.instanceOf, resource)

        for item in titles:
            print(item)
            if 'usage' in item and item['usage'] is not None:
                print("Usage")
                title_res = g.resource("{}_title_{}".format(self.mainURI, i))

                title_res.add(BF.mainTitle, Literal(item["title"].strip()))

                if item['usage'] == 'alternative':
                    title_res.add(RDF.type, BF.VariantTitle)
                else:
                    title_res.add(RDF.type, BF.Title)
                    resource.add(RDFS.label, Literal(item['title'].strip()))
                # Schema.org attributes per spreadsheet for BIBFRAME matching
                title_res.add(RDF.type, SCHEMA.CreativeWork)
                title_res.add(SCHEMA.name, Literal(item['title'].strip()))

                instance.add(BF.title, title_res)

                i += 1

        i = 0

        resource.add(RDF.type, self.get_type())

        for name in self.get_names():
            contribution_resource = g.resource(self.mainURI + "#contribution_{}".format(i))

            contribution_resource.add(RDF.type, BF.Contribution)
            agent_resource = g.resource(self.mainURI + "#agent_{}".format(i))
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

            agent_resource.add(RDFS.label, Literal(name["name"]))
            role_resource = g.resource("{}#contribution_{}_role".format(self.mainURI, i))
            role_resource.add(RDF.type, BF.Role)

            if name['role'] in self.role_map:
                role_resource.add(BF.code, Literal(self.role_map[name['role']]))
                role_resource.add(BF.source, MARCREL[self.role_map[name['role']]])

            if name['role']:
                role_resource.add(RDFS.label, Literal(name["role"]))
            else:
                role_resource.add(BF.code, Literal("aut"))
                role_resource.add(BF.source, MARCREL.aut)
                role_resource.add(RDFS.label, Literal("author"))

            agent_resource.add(OWL.sameAs, URIRef("http://cwrc.ca/cwrcdata/{}".format(remove_punctuation(name['name']))))
            contribution_resource.add(BF.agent, agent_resource)
            contribution_resource.add(BF.role, role_resource)
            resource.add(BF.contribution, contribution_resource)

            i += 1

        for lang in self.get_languages():
            resource.add(XML.lang, Literal(lang['language']))

        adminMetaData = g.resource("{}_admin_metatdata".format(self.mainURI))

        i = 0
        for r in self.get_record_content_source():
            assigner_agent = g.resource("{}_admin_agent_{}".format(self.mainURI, i))
            assigner_agent.add(RDF.type, BF.Agent)
            assigner_agent.add(RDFS.label, Literal(r['value']))

            if 'authority' in r:
                source_agent = g.resource("{}_admin_agent_source_{}".format(self.mainURI, i))
                source_agent.add(RDF.type, BF.Source)
                source_agent.add(RDF.value, Literal(r['authority']))
                assigner_agent.add(BF.source, source_agent)

            adminMetaData.add(BF.assigner, assigner_agent)

            i += 1

        for r in self.get_record_change_date():

            dateValue, transformed = dateParse(r['date'])
            if not transformed:
                logger.info("MISSING DATE FORMAT: {} on Document {}".format(dateValue, self.mainURI))
            adminMetaData.add(BF.changeDate, Literal(dateValue, datatype=XSD.date))

        i = 0
        for r in self.get_record_origin():
            generationProcess = g.resource("{}_generation_process_{}".format(self.mainURI, i))
            generationProcess.add(RDF.type, BF.GenerationProcess)
            generationProcess.add(RDF.value, Literal(r['origin']))

            adminMetaData.add(BF.generationProcess, generationProcess)

        i = 0
        for r in self.get_record_language_catalog():
            adminMetaData.add(BF.descriptionLanguage, Literal(r['language']))

        # Track this transformation
        cur_date = datetime.datetime.now()
        generation_process = g.resource("{}_generation_process_cwrc".format(self.mainURI))
        generation_process.add(RDF.type, BF.GenerationProcess)
        generation_process.add(RDF.value,
                               Literal("Converted from MODS to BIBFRAME RDF in" +
                                       " {} {} using CWRC's modsBib extraction script".format(cur_date.strftime("%B"),
                                                                                              cur_date.strftime("%Y"))))
        adminMetaData.add(BF.generationProcess, generation_process)

        resource.add(BF.adminMetadata, adminMetaData)


        i = 0

        for o in self.get_origins():
            originInfo = g.resource("{}_activity_statement_{}".format(self.mainURI, i))
            if o['publisher']:
                publisher = g.resource("{}_activity_statement_publisher_{}".format(self.mainURI, i))
                publisher.add(RDF.type, BF.Agent)
                publisher.add(RDFS.label, Literal(o['publisher']))

                originInfo.add(BF.provisionActivity, publisher)
            if o['place']:
                place = g.resource("{}_activity_statement_place_{}".format(self.mainURI, i))
                place.add(RDF.value, Literal(o['place']))
                place.add(RDF.type, BF.Place)
                place.add(RDF.type, SCHEMA.Place)

                place_map = geoMapper.get_place(o['place'].strip())

                if place_map:
                    for item in place_map:
                        place.add(OWL.sameAs, URIRef(item))

                originInfo.add(BF.place, place)

            if o['date']:
                originInfo.add(RDF.type, BF.Publication)
                dateValue, transformed = dateParse(o['date'])
                if not transformed:
                    logger.info("MISSING DATE FORMAT: {} on Document {}".format(dateValue, self.mainURI))
                originInfo.add(BF.date, Literal(dateValue, datatype=XSD.date))

            if o['edition']:
                instance.add(BF.editionStatement, Literal(o['edition']))

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
            note_r.add(RDF.value, Literal(n['content']))
            if n['type']:
                note_r.add(BF.nodeType, Literal(n['type']))

            i += 0

            instance.add(BF.note, note_r)

        i = 0
        # Add parts to the instance
        for p in self.get_parts():
            extent_resource = g.resource("{}_extent_{}".format(self.mainURI, i))
            extent_resource.add(RDF.type, BF.Extent)
            if p['value'] != "":
                extent_resource.add(RDF.value, Literal(p['value']))
            if p['volume']:
                extent_resource.add(SCHEMA.volumeNumber, Literal(p['volume']))
            if p['issue']:
                extent_resource.add(SCHEMA.issueNumber, Literal(p['issue']))

            instance.add(BF.extent, extent_resource)

        genre = self.get_genre()

        if genre:
            genre_res = g.resource("{}_genre".format(self.mainURI))
            genre_res.add(RDF.type, BF.GenreForm)
            genre_res.add(RDFS.label, Literal(genre['genre']))

            resource.add(BF.genreForm, genre_res)

        if self.id in genre_map:
            genres = genre_map[self.id]
            for g in genres:
                gName = g.lower().title()
                uri = URIRef('http://sparql.cwrc.ca/ontologies/genre#{}'.format(gName))

                if genre_graph[uri]:
                    resource.add(GENRE.hasGenre, GENRE[gName.lower()])
                else:
                    logger.info("GENRE NOT FOUND: {0}".format(gName))


if __name__ == "__main__":
    g = Graph()
    g.bind("cwrc", CWRC)
    g.bind("bf", BF)
    g.bind("xml", XML, True)
    g.bind("marcrel", MARCREL)
    g.bind("data", DATA)
    g.bind("genre", GENRE)
    g.bind("owl", OWL)
    g.bind("schema", SCHEMA)

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

    dirname = config_options['BIBLIOGRAPHY_FILES']
    writing_dir = config_options['WRITING_FILES']
    genre_ontology = config_options['GENRE_ONTOLOGY']
    places = config_options['PLACES_CSV']

    geoMapper = ParseGeoNamesMapping(places)

    genre_graph = Graph()

    genre_graph.parse(genre_ontology)

    for fname in os.listdir(writing_dir):
        path = os.path.join(writing_dir, fname)
        if os.path.isdir(path):
            continue

        try:
            genreParse = WritingParse(path, genre_map)
        except UnicodeError:
            pass

    for fname in os.listdir(dirname):

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
    formats = {'ttl': 'turtle'} # 'xml': 'pretty-xml'
    for extension, file_format in formats.items():
        g.serialize(destination="bibrdf/{}.{}".format(output_name, extension), format=file_format)
