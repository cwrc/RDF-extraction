import rdflib
from biography import bind_ns, NS_DICT, make_standard_uri, remove_punctuation
from place import Place
from organizations import get_org_uri
from context import get_value

# <CHRONSTRUCT RELEVANCE="COMPREHENSIVE" CHRONCOLUMN="BRITISHWOMENWRITERS" RESP="SIB">
# <DATE VALUE="1874-12-25" CERTAINTY="C">Christmas 1874</DATE>


class Event(object):
    """docstring for CulturalForm"""

    event_type_map = {
        "NATIONALINTERNATIONAL": "PoliticalClimate",
        "BRITISHWOMENWRITERS": "BritishWomenWriters",
        "WRITINGCLIMATE": "LiteraryClimate",
        "SOCIALCLIMATE": "SocialClimate",
        "SELECTIVE": "HistoricSignificance",
        "PERIOD": "PeriodSignificance",
        "DECADE": "DecadeSignficance",
        "COMPREHENSIVE": "IndividualSignificance"
    }

    certainty_map = {
        "CERT": "highCertainty",
        "C": "mediumCertainty",
        "BY": "mediumCertainty",
        "AFTER": "mediumCertainty",
        "ROUGHLYDATED": "lowCertainty",
        "UNKNOWN": "unknownCertainty",
        "FROM": "highCertainty",
        "TO": "mediumCertainty",
        "BOTH": "mediumCertainty",
        "NEITHER": "mediumCertainty",
    }

    def get_actors(tag):
        actors = []
        for x in tag.find_all("NAME"):
            actors.append(make_standard_uri(x.get("STANDARD")))
        for x in tag.find_all("ORGNAME"):
            actors.append(get_org_uri(x))
        for x in tag.find_all("TITLE"):
            title = get_value(x)
            actors.append(make_standard_uri(title + " TITLE", ns="cwrc"))

        return actors

    def get_event_type(tag):
        event_types = []
        event_types.append(Event.event_type_map[tag.get("RELEVANCE")])
        event_types.append(Event.event_type_map[tag.get("CHRONCOLUMN")])
        # event_types += Event.event_type_map[tag.get("CHRONCOLUMN")]
        # return [Event.event_type_map[tag.get("RELEVANCE")],Event.event_type_map[tag.get("CHRONCOLUMN")]]
        return event_types

    def get_time_type(tag):
        """Determine if punctive or interval"""
        if tag.name in ["DATE", "DATESTRUCT"]:
            return "PunctiveTime"
        certainty = tag.get("CERTAINTY")
        if certainty == "ROUGHLYDATED":
            return "PunctiveTime"
        return "IntervalTime"

    def get_time_certainty(tag):
        """Determine time certainty"""
        pass

    def get_date_tag(tag):
        date_structures = ["DATE", "DATESTRUCT", "DATERANGE"]
        children = tag.children
        for x in children:
            if x.name in date_structures:
                return(x)

    def __init__(self, title, tag, other_attributes=None):
        super(Event, self).__init__()
        self.title = title
        # get RELEVANCE CHRONCOLUMN
        self.event_type = Event.get_event_type(tag)
        self.date_tag = Event.get_date_tag(tag)
        self.time_type = Event.get_time_type(self.date_tag)
        self.actors = Event.get_actors(tag)
        # Determine certainty
        # Determine sem predicate to use
        if self.date_tag.name == "DATERANGE":
            pass
        else:
            self.date = self.date_tag.get("VALUE")

        # print(self.date_tag)
        # input()

    def to_triple(self, person_uri):
        # p = self.predicate + self.reported
        # o = self.value
        # figure out if i can just return tuple or triple without creating a whole graph
        pass

    def __str__(self):

        # text = strip_all_whitespace(str(self.title))
        string = "\ttitle: " + self.title + "\n"
        string += "\tevent_type: "
        for x in self.event_type:
            string += x + "\n"
        string += "\tactors: "
        for x in self.actors:
            string += str(x) + "\n"
        string += "\tdate: " + str(self.date) + "\n"
        string += "\ttime_type: " + str(self.time_type) + "\n"
        return string
