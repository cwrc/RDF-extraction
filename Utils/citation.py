from rdflib import RDF, RDFS, Literal, BNode
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
        #NOTE: Temporarily logging this info for decision about page numbers
        if "," in self.page or "-" in self.page:
            logger.info("\n\t" + str(self.tag) + "\n")

    def to_triple(self, target_uri, source_url=None):
        g = utilities.create_graph()
        uri = BNode()
        g.add((target_uri, utilities.NS_DICT["cito"].cites, uri))

        g.add((uri, RDF.type, utilities.NS_DICT["cito"].Citation))
        g.add((uri, RDFS.label, Literal(self.label)))
        if self.page:
            g.add((uri, utilities.NS_DICT["prism"].startingPage, Literal(self.page)))
            g.add((uri, utilities.NS_DICT["prism"].endingPage, Literal(self.page)))

        citing_uri = utilities.create_cwrc_uri(self.citing_entity)
        g.add((uri, utilities.NS_DICT["cito"].hasCitingEntity, citing_uri))

        if source_url:
            g.add((source_url, utilities.NS_DICT["biro"].references, citing_uri))

        return g

    def __str__(self):
        string = "Tag: " + str(self.tag) + "\n"
        string += "Label: " + self.label + "\n"
        string += "Page: " + self.page + "\n"
        string += "Citing entity: " + self.citing_entity + "\n"
        return string
