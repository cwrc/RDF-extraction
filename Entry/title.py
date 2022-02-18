from turtle import title
import rdflib
from rdflib import RDF, RDFS, Literal
from difflib import get_close_matches

from Utils import utilities
from Utils.organizations import get_org, get_org_uri
from Utils.place import Place
from Utils.event import Event
from Utils.context import Context

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

    def __init__(self, name, titleType, other_attributes=None):
        super(Title, self).__init__()
        self.label = name
        self.typing = None
        # Temp placeholder until reconciled with bibliography
        # Or use blanknode
        self.uri = utilities.make_standard_uri(title + " TITLE", ns="cwrc")
        if titleType in self.titleType_mapping: 
            self.typing = self.titleType_mapping[titleType]

    def to_triple(self):
        g = utilities.create_graph()
        g.add((self.uri, RDF.type, self.value))
        g.add((self.uri, RDFS.Label, self.label))
        return g