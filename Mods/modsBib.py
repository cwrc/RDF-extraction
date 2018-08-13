from bs4 import BeautifulSoup
import rdflib, sys

from rdflib import *

CWRC = rdflib.Namespace( "http://sparql.cwrc.ca/ontologies/cwrc#")
BF = rdflib.Namespace( "http://id.loc.gov/ontologies/bibframe/")
XML = rdflib.Namespace("http://www.w3.org/XML/1998/namespace")


class BibliographyParse():

    soup=None
    mainURI = ""
    g=None
    id=""

    type_map = {
        "text": BF.Text,
        "audio": BF.Audio,
        "cartography": BF.Cartography,
        "dataset": BF.Dataset,
        "mixed material": BF.MixedMaterial,
        "moving image": BF.MovingImage,
        "notated movement": BF.NotatedMovement,
        "multimedia": BF.Multimedia,
        "still image": BF.StillImage,
        "object": BF.Object
    }

    def __init__(self, filename, graph):
        with open(filename) as f:
            self.soup = BeautifulSoup(f, 'lxml')

        self.g = graph
        self.id = filename.replace(".xml", "")
        self.mainURI = self.id


    def get_type(self):
        if self.soup.typeofresource:
            resource_type =  self.soup.typeofresource.text.lower()
            return self.type_map[resource_type]
        else:
            return None

    def get_genre(self):
        if self.soup.genre:
            return {'genre': self.soup.genre.text, 'authority': self.soup.genre['authority']}

    def get_title(self):
        title_values = ""
        if self.soup.titleinfo:
            # for item in self.soup.titleinfo:
            #     title_values += item.title
            if self.soup.titleinfo.title:
                return self.soup.titleinfo.title.text
        return ""

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
            print(np['type'])
            print(np.namepart.get_text())
            names.append({"type": np['type'], "name": np.namepart.get_text()})

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
            places.append({"term": o.place.placeterm.text})

        return places

    def origin_info_publisher(self):
        publishers = []
        for o in self.soup.find_all('origininfo'):
            publishers.append({"publisher": o.publisher.text})

        return publishers

    def origin_info_date(self):
        dates = []
        for o in self.soup.find_all("origininfo"):
            dates.append({"date": o.dateissued.text})

        return dates

    def build_graph(self):
        g = self.g
        i = 0

        resource = g.resource(self.mainURI)
        resource.add(RDF.type, BF.Work)
        resource.add(RDFS.label, Literal(self.get_title()))
        resource.add(RDF.type, self.get_type())

        for name in self.get_names():
            contribution_resource = g.resource(self.mainURI + "#contribution_{}".format(i))
            i += 0
            contribution_resource.add(RDF.type, BF.Contribution)
            agent_resource = g.resource(self.mainURI + "#agent_{}".format(i))
            agent_resource.add(RDF.type, BF.Agent)
            agent_resource.add(RDFS.label, Literal(name["name"]))
            agent_resource.add(CWRC.role, URIRef("cwrc:{}".format(name["type"])))

            contribution_resource.add(BF.agent, agent_resource)

            resource.add(BF.contribution, contribution_resource)

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

        resource.add(BF.provisionActivityStatement, originInfo)


        genre = self.get_genre()

        genre_res = g.resource("{}_genre".format(self.mainURI))
        genre_res.add(RDF.type, BF.GenreForm)
        genre_res.add(RDFS.label, Literal(genre['genre']))

        resource.add(BF.genreForm, genre_res)




if __name__ == "__main__":
    g = Graph()
    g.bind("cwrc", CWRC)
    g.bind("bf", BF)
    g.bind("xml", XML, True)

    filename = sys.argv[1]

    mp = BibliographyParse(filename, g)

    mp.build_graph()

    g.serialize(destination="output.txt", format="turtle")
