from rdflib import RDF, RDFS, Literal
from Utils import utilities
import rdflib

logger = utilities.config_logger("citation")


class Citation(object):
    """docstring for Citation"""

    def __init__(self, bibcit_tag):
        super(Citation, self).__init__()
        self.tag = bibcit_tag
        self.page = bibcit_tag.text
        self.label = bibcit_tag.get("PLACEHOLDER")
        self.citing_entity = bibcit_tag.get("DBREF")
        self.uri = bibcit_tag.get("REF")
        self.entry_id = utilities.get_entry_id(self.tag)
        
        if self.citing_entity:
            if " " in self.citing_entity:
                logger.error(F"In entry: {self.entry_id} - BIBCIT: Space encountered in DBREF attribute: {bibcit_tag}")
                self.citing_entity = self.citing_entity.replace(" ","")


    def to_triple(self, target_uri, source_url=None):
        g = utilities.create_graph()

        if not self.citing_entity:
            logger.warning(F"In entry: {self.entry_id} - BIBCIT: Missing DBREF attribute: {self.tag}")
            return g
        if not self.label:
            logger.warning(F"In entry: {self.entry_id} - BIBCIT: Missing PLACEHOLDER attribute: {self.tag}")
            return g

        uri = None
        citing_uri = None
        if self.uri:
            uri = rdflib.URIRef(self.uri+"_dbref")
            citing_uri = rdflib.URIRef(self.uri)
        else:
            logger.error(F"In entry: {self.entry_id} - BIBCIT: tag missing REF attribute: {self.tag}")

            uri = utilities.create_uri("temp", "dbref_"+self.citing_entity)
            citing_uri = utilities.create_uri("temp", self.citing_entity)
        
        g.add((target_uri, utilities.NS_DICT["crm"].P67_refers_to, uri))

        g.add((uri, RDF.type, utilities.NS_DICT["crm"].E33_Linguistic_Object))
        g.add((uri, RDFS.label, Literal(self.label, lang="en")))
        g.add((uri, utilities.NS_DICT["crm"].P67i_is_referred_to_by, citing_uri))

        if source_url:
            g.add((source_url, RDF.type, utilities.NS_DICT["crmdig"].D1_Digital_Object))
            g.add((source_url, utilities.NS_DICT["crm"].P67_refers_to, citing_uri))
            g.add((source_url, RDFS.label, Literal(source_url.split("/")[-1])))

        return g

    def __str__(self):
        string = "Tag: " + str(self.tag) + "\n"
        string += "Label: " + self.label + "\n"
        string += "Page: " + self.page + "\n"
        string += "Citing entity: " + self.citing_entity + "\n"
        return string
