from rdflib import RDF, RDFS, Literal
from Utils import utilities
import rdflib

logger = utilities.config_logger("citation")


class Citation(object):
    """docstring for Citation"""

    def __init__(self, bibcit_tag):
        super(Citation, self).__init__()
        self.tag = bibcit_tag
        print(self.tag)
        self.page = bibcit_tag.text
        self.label = bibcit_tag.get("PLACEHOLDER")
        self.citing_entity = bibcit_tag.get("DBREF")
        self.uri = bibcit_tag.get("REF")


    def to_triple(self, target_uri, source_url=None):
        g = utilities.create_graph()

        uri = None
        citing_uri = None
        if self.uri:
            uri = rdflib.URIRef(self.uri+"_dbref")
            citing_uri = rdflib.URIRef(self.uri)
        else:
            uri = utilities.create_uri("data", "dbref_"+self.citing_entity)
            citing_uri = utilities.create_uri("data", self.citing_entity)
        
        g.add((target_uri, utilities.NS_DICT["crm"].P67_refers_to, uri))

        g.add((uri, RDF.type, utilities.NS_DICT["crm"].E33_Linguistic_Object))
        g.add((uri, RDFS.label, Literal(self.label)))

        g.add((uri, utilities.NS_DICT["crm"].P67i_is_referred_to_by, citing_uri))

        if source_url:
            g.add((source_url, RDF.type, utilities.NS_DICT["dig"].D1_Digital_Object))
            g.add((source_url, utilities.NS_DICT["crm"].P67_refers_to, citing_uri))

        return g

    def __str__(self):
        string = "Tag: " + str(self.tag) + "\n"
        string += "Label: " + self.label + "\n"
        string += "Page: " + self.page + "\n"
        string += "Citing entity: " + self.citing_entity + "\n"
        return string
