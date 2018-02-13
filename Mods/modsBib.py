from bs4 import BeautifulSoup


class ModsParser():

    soup=None

    def __init__(self, filename):
        with open(filename) as f:
            self.soup = BeautifulSoup(f, 'lxml')

    def get_type(self):
        if self.soup.typeofresource:
            return self.soup.typeofresource.text

    def get_genre(self):
        if self.soup.genre:
            return {'genre': self.soup.genre.text, 'authority': self.soup.genre['authority']}

    def get_title(self):
        if self.soup.titleinfo:
            if self.soup.titleinfo.title:
                return self.soup.titleinfo.title.text
        return ""

    def get_records(self):
        records = []
        for r in self.soup.get_all(['recordinfo']):
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
        for np in self.soup.get_all(['namepart']):
            return {np['type']: np.text}

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
        for l in self.soup.get_all(['language']):
            for t in l.get_all('languageterm'):
                langs.append({'language': t.text, 'type': t['type']})

        return langs
