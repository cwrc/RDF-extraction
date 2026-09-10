import rdflib
from rdflib import RDF, RDFS, Literal
from difflib import get_close_matches

from utils import utilities
from utils.organizations import get_org, get_org_uri
from utils.place import Place
from utils.event import Event
from utils.context import Context

logger = utilities.config_logger("titles")

class Title(object):
    """"docstring for Title
    This class will be used to type a title
    and eventually map to the bibliographic data
    """
    titleType_mapping = { "monographic": "standaloneWork",
    "analytic": "embeddedWork",
    "journal": "periodical",
    "series": "series",
    "unpublished": "unpublished" }



    def __init__(self, name, titleType, genre = None, other_attributes=None):
        super(Title, self).__init__()
        self.label = name
        self.typing = None
        self.genre = []
        # Temp placeholder until reconciled with bibliography
        # Or use blanknode
        self.uri = utilities.make_standard_uri(name + " TITLE", ns="data")
        if titleType in self.titleType_mapping:
            self.typing = self.titleType_mapping[titleType]
        if genre:
            for g in genre:
                if g not in utilities.GENRE_MAPPING:
                    logger.warning(f"Genre {g} not found in GENRE_MAPPING. Please check for typos or add to mapping.")
                else:
                    self.genre.append(utilities.GENRE_MAPPING[g])

            self.genre = genre
    def to_triple(self):
        g = utilities.create_graph()
        if self.typing:
            g.add((self.uri, RDF.type, self.typing))
        g.add((self.uri, RDFS.Label, self.label))

        for genres in self.genre:
            g.add((self.uri, utilities.NS_DICT["genre"]["hasGenre"], genres))

        return g

    def __str__(self) -> str:
        return f"URI: {self.uri}\nTitle: {self.label}\nTyping:{self.typing}\n"
