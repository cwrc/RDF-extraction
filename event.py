import rdflib


class Event(object):
    """docstring for CulturalForm"""

    def __init__(self, title, event_type, date, other_attributes=None):
        super(Event, self).__init__()
        self.title = title
        self.event_type = event_type
        self.date = date

    def to_triple(self, person_uri):
        # p = self.predicate + self.reported
        # o = self.value
        # figure out if i can just return tuple or triple without creating a whole graph
        pass

    def __str__(self):
        string = "\tevent_type: " + str(self.event_type) + "\n"
        text = strip_all_whitespace(str(self.title))
        string += "\tcontent: " + text + "\n"
        string += "\tdate: " + str(self.date) + "\n"
        return string
