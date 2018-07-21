import rdflib


class Place(object):
    """docstring for Place"""
    # There may be additional information about places we may have to add
    # if we decide to go a different way than just geonames could also be dependent
    # on how we handle events as well

    def __init__(self, settlement, region, geog, other_attributes=None):
        super(Place, self).__init__()
        # Add somefunction to create uri/ get relevant uri from geonames
        self.uri = str([settlement, region, geo])[1:-1]

    #Hopefully won't have to create triples about a place just provide a uri but  
    def to_triple(self, person_uri):
        # p = self.predicate + self.reported
        # o = self.value
        # figure out if i can just return tuple or triple without creating a whole graph
        pass

    def __str__(self):
        string = "\turi: " + str(self.uri) + "\n"
        return string


# scrape freestanding events
