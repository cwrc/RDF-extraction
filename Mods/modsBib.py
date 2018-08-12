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

    def get_records(self):
        records = []
        for r in self.soup.find_all('recordinfo'):
            record = {}
            record['sources'] = []
            for source in r.get_all(['recordcontentsource']):
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
