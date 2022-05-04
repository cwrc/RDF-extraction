from rdflib import RDF, RDFS, Literal, BNode
import rdflib
from Utils import utilities

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

        uri = None

        if self.uri:
            uri = rdflib.URIRef(self.uri+"_dbref")
            citing_uri = rdflib.URIRef(self.uri)
        else:
            logger.error(F"In entry: {self.entry_id} - BIBCIT: tag missing REF attribute: {self.tag}")

            uri = utilities.create_uri("data", "dbref_"+self.citing_entity)
            citing_uri = utilities.create_uri("data", self.citing_entity)

        if not self.citing_entity:
            logger.warning(F"In entry: {self.entry_id} - BIBCIT: Missing DBREF attribute: {self.tag}")
            return g
        if not self.label:
            logger.warning(F"In entry: {self.entry_id} - BIBCIT: Missing PLACEHOLDER attribute: {self.tag}")
            return g


        g.add((target_uri, utilities.NS_DICT["cito"].cites, uri))
        g.add((uri, RDF.type, utilities.NS_DICT["cito"].Citation))
        g.add((uri, RDFS.label, Literal(self.label)))

        if self.page:
            g.add((uri, utilities.NS_DICT["prism"].startingPage, Literal(self.page)))
            g.add((uri, utilities.NS_DICT["prism"].endingPage, Literal(self.page)))

        g.add((uri, utilities.NS_DICT["cito"].hasCitingEntity, citing_uri))

        if source_url:
            g.add((source_url, utilities.NS_DICT["biro"].references, citing_uri))

        return g

    def __str__(self):
        string = F"Tag: {self.tag}\n"
        string += F"Label: {self.label}\n"
        string += F"Page: {self.page}\n"
        string += F"Citing entity: {self.citing_entity}\n"
        return string