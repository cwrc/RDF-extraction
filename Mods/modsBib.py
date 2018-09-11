from bs4 import BeautifulSoup
import rdflib, sys
import os

from rdflib import *

CWRC = rdflib.Namespace( "http://sparql.cwrc.ca/ontologies/cwrc#")
BF = rdflib.Namespace( "http://id.loc.gov/ontologies/bibframe/")
XML = rdflib.Namespace("http://www.w3.org/XML/1998/namespace")
MARCREL = rdflib.Namespace("http://id.loc.gov/vocabulary/relators/")
DATA = rdflib.Namespace("http://cwrc.ca/cwrcdata/")
GENRE = rdflib.Namespace("http://sparql.cwrc.ca/ontologies/genre#")

genre_graph = None
genre_map = {}

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
    if all_punctuation:
        translator = str.maketrans('', '', string.punctuation)
    else:
        translator = str.maketrans('', '', string.punctuation.replace("-", ""))

    temp_str = input_str.translate(translator)
    temp_str = temp_str.replace(" ", "_")
    return temp_str

# ----------- MAIN CLASSES ----------


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
        self.mainURI = "{}:{}".format("data", self.id)
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
        if self.soup.titleinfo:
            titleinfo = self.soup.titleinfo
            if 'usage' in titleinfo.attrs:
                usage = titleinfo.attrs['usage']
            else:
                usage = None

            if self.soup.titleinfo.title:
                title = self.soup.titleinfo.title.text
            else:
                title = None
        else:
            return {"title": None, "usage": None}

        return {"title": title, "usage": usage}

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
            if 'type' in np.attrs:
                type = np['type']

            else:
                type = None

            role = None
            roleTerms = np.find_all('roleterm')
            for role in roleTerms:
                if role['type'] == "text":
                    role = role.text

            print(type)
            #print(np.namepart.get_text())
            names.append({"type": type, "role": role, "name": np.namepart.get_text()})

        return names

    def get_places(self):
        origins = []
        if self.soup.origininfo:
            for oi in self.soup.get_all(['origininfo']):
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

    def origin_info_place(self):
        places = []
        for o in self.soup.find_all('origininfo'):
            if o.place:
                places.append({"term": o.place.placeterm.text})

        return places

    def origin_info_publisher(self):
        publishers = []
        for o in self.soup.find_all('origininfo'):
            if o.publisher:
                publishers.append({"publisher": o.publisher.text})

        return publishers

    def origin_info_date(self):
        dates = []
        for o in self.soup.find_all("origininfo"):
            if o.dateissued:
                dates.append({"date": o.dateissued.text})

        return dates

    def get_related_items(self):
        related_items = self.soup.find_all('relateditem')
        soups = []
        for item in related_items:
            try:
                print("{}".format(item))
                #sys.exit(0)
                soups.append(BeautifulSoup("{}".format(item), 'lxml'))
            except UnicodeError:
                pass

        return soups

    def get_notes(self):
        note_items = self.soup.find_all('note')

        notes = []
        for note in note_items:
            if 'type' in note.attrs:
                note_type = note.attrs['type']
            else:
                note_type = None

            note_content = note.text

            notes.append({"type": note_type, "content": note_content})

        return notes

    def build_graph(self):
        g = self.g
        i = 0

        title = self.get_title()

        resource = g.resource(self.mainURI)
        resource.add(RDF.type, BF.Work)
        if title['title'] is not None:
            resource.add(RDFS.label, Literal(title['title']))
        resource.add(RDF.type, self.get_type())

        instance = g.resource(self.mainURI + "_instance")
        instance.add(RDF.type, BF.Instance)
        instance.add(BF.instanceOf, resource)

        if 'usage' in title and title['usage'] is not None:
            title_res = g.resource("{}_title".format(self.mainURI))
            title_res.add(RDF.type, BF.Title)
            title_res.add(BF.mainTitle, Literal(title["title"]))
            instance.add(BF.title, title_res)

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
                role_resource.add(BF.source, URIRef("marcrel:{}".format(self.role_map[name['role']])))

            if name['role']:
                role_resource.add(RDFS.label, Literal(name["role"]))
            else:
                role_resource.add(BF.code, Literal("aut"))
                role_resource.add(BF.source, URIRef("marcrel:aut"))
                role_resource.add(RDFS.label, Literal("author"))

            agent_resource.add(OWL.sameAs, URIRef("data:{}".format(remove_punctuation(name['name']))))
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
            adminMetaData.add(BF.changeDate, Literal(r['date']))

        i = 0
        for r in self.get_record_origin():
            generationProcess = g.resource("{}_generation_process_{}".format(self.mainURI, i))
            generationProcess.add(RDF.type, BF.GenerationProcess)
            generationProcess.add(RDF.value, Literal(r['origin']))

            adminMetaData.add(BF.generationProcess, generationProcess)

        i = 0
        for r in self.get_record_language_catalog():
            adminMetaData.add(BF.descriptionLanguage, Literal(r['language']))

        resource.add(BF.adminMetadata, adminMetaData)


        originInfo = g.resource("{}_activity_statement".format(self.mainURI))

        i = 0

        for r in self.origin_info_date():
            publisher = g.resource("{}_activity_statement_publisher_{}".format(self.mainURI, i))
            publisher.add(RDF.type, BF.Publication)
            publisher.add(BF.date, Literal(r['date']))

            originInfo.add(BF.provisionActivity, publisher)
            i += 1

        i = 0
        for r in self.origin_info_place():
            place = g.resource("{}_activity_statement_place_{}".format(self.mainURI, i))
            place.add(RDF.value, Literal(r['term']))
            place.add(RDF.type, BF.Place)

            originInfo.add(BF.place, place)
            i += 0

        i = 0
        for r in self.origin_info_publisher():
            publisher = g.resource("{}_activity_statement_publisher_{}".format(self.mainURI, i))
            publisher.add(RDF.type, BF.Agent)
            publisher.add(RDFS.label, Literal(r['publisher']))

            originInfo.add(BF.agent, publisher)

            i += 0

        i = 0
        if self.relatedItem == False:
            for part in self.get_related_items():
                bp = BibliographyParse(part, self.g, "{}_part_{}".format(self.mainURI, i), True)
                bp.build_graph()

                work = g.resource("{}_part_{}".format(self.mainURI, i))
                resource.add(BF.hasPart, work)
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

        resource.add(BF.provisionActivityStatement, originInfo)


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
                uri = URIRef('http://sparql.cwrc.ca/ontologies/genre#genre{}'.format(gName))

                if genre_graph[uri]:
                    resource.add(GENRE.hasGenre, GENRE[gName.lower()])


if __name__ == "__main__":
    g = Graph()
    g.bind("cwrc", CWRC)
    g.bind("bf", BF)
    g.bind("xml", XML, True)
    g.bind("marcrel", MARCREL)
    g.bind("data", DATA)
    g.bind("genre", GENRE)
    g.bind("owl", OWL)

    dirname = sys.argv[1]

    writing_dir = sys.argv[2]

    genre_ontology = sys.argv[3]

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


    #print(mapped_genres)
    #sys.exit(0)

    for fname in os.listdir(dirname):

        path = os.path.join(dirname, fname)
        if os.path.isdir(path):
            continue

        print(fname)
        try:
            mp = BibliographyParse(path, g, fname)
            mp.build_graph()
        except UnicodeError:
            pass

    fname = "Bibliography"
    output_name = fname.replace(".xml", "")
    file_format = "turtle"
    g.serialize(destination="bibrdf/{}.{}".format(output_name, file_format), format=file_format)
