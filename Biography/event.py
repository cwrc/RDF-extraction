import rdflib
from rdflib import RDF, RDFS, Literal, XSD

from utilities import *
from organizations import get_org_uri

# Leaving this independent of contexts incase we should want to vary events vs contexts
MAX_WORD_COUNT = 35


def get_actors(tag):
    """ Returns actors within an event (any name/org/title mentioned)"""
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
    """Returns the types of the event"""
    event_types = []
    event_types.append(Event.event_type_map[tag.get("RELEVANCE")])
    event_types.append(Event.event_type_map[tag.get("CHRONCOLUMN")])
    return [create_cwrc_uri(x) for x in event_types]


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
    certainty = tag.get("CERTAINTY")
    if certainty:
        return Event.certainty_map[certainty]
    if tag.name == "DATERANGE":
        certainty = tag.get("EXACT")
        if certainty:
            return Event.certainty_map[certainty]

    return None


def get_indirect_date_tag(tag):
    tags = tag.find_all("DATE") + tag.find_all("DATESTRUCT") + tag.find_all("DATERANGE")
    if len(tags) > 1:
        print("Multiple date tags detected:")
        print(*tags, sep="\n")
        print()
        # input()
    if tags:
        return tags[0]
    return None


def get_date_tag(tag):
    """Will retrieve that existing date related tag that is a child of the given tag """
    date_structures = ["DATE", "DATESTRUCT", "DATERANGE"]
    children = tag.children
    for x in children:
        if x.name in date_structures:
            return(x)
    return get_indirect_date_tag(tag)

# TODO: apply '-' if calendar is BC
# 
def format_date(date):
    """ Formats date to be in usable xsd format
    # https://github.com/RDFLib/rdflib/issues/747
    :/
    Weird issue with using gYearMonth and gYear resulting in filling out the date
    ex. 1891 --> 1891-01-01
    ex. 1891-12 --> 1891-12-01
    Using normalizing fix from https://github.com/RDFLib/rdflib/issues/806
    Not too sure the side effects of this
    """
    if date[-1] == "-":
        date = date.strip("-")

    if len(date) == 10:
        return Literal(date, datatype=XSD.date)
    elif len(date) == 7:
        return Literal(date, datatype=XSD.gYearMonth, normalize=False)
    elif len(date) == 4:
        return Literal(date, datatype=XSD.gYear, normalize=False)
    else:
        return Literal(date)


class Event(object):
    """docstring for Event
        Given an id, name, chronstruct tag, it will create an event based on the SEM model and our associated predicates (cwrc:hasEvent)
        Must be linked to a context through temp_context.link_event(temp_event)
    """

    event_type_map = {
        "NATIONALINTERNATIONAL": "PoliticalClimate",
        "BRITISHWOMENWRITERS": "BritishWomenLiteraryClimate",
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

    def __init__(self, title, id, tag, other_attributes=None):
        super(Event, self).__init__()
        self.title = title
        self.tag = tag
        self.uri = create_uri("data", id)
        self.place = get_places(tag)
        self.event_type = get_event_type(tag)
        self.actors = get_actors(tag)

        self.text = limit_words(str(tag.CHRONPROSE.get_text()), MAX_WORD_COUNT)

        self.date_tag = get_date_tag(tag)
        self.time_type = get_time_type(self.date_tag)
        self.precision = self.date_tag.get("CERTAINTY")
        self.time_certainty = get_time_certainty(self.date_tag)

        # Determine sem predicate to use
        if self.date_tag.name == "DATERANGE":
            self.date = self.date_tag.get("FROM") + ":" + self.date_tag.get("TO")
            self.predicate = None
        else:
            self.date = self.date_tag.get("VALUE")
            if self.precision == "CERT":
                self.predicate = NS_DICT["sem"].hasTimeStamp
            elif self.precision == "BY":
                self.predicate = NS_DICT["sem"].hasLatestBeginTimeStamp
            elif self.precision == "AFTER":
                self.predicate = NS_DICT["sem"].hasEarliestBeginTimeStamp
            elif self.precision is None:
                self.predicate = NS_DICT["sem"].hasTimeStamp
            else:
                self.predicate = NS_DICT["sem"].hasTime
            self.date = format_date(self.date)

    def to_triple(self, person=None):
        g = rdflib.Graph()
        namespace_manager = rdflib.namespace.NamespaceManager(g)
        bind_ns(namespace_manager, NS_DICT)

        # attaching event to person, context will need link event fx
        if person:
            g.add((person.uri, NS_DICT["cwrc"].hasEvent, self.uri))
        # Not sure if inverse is necessary atm
        # g.add((self.uri, NS_DICT["cwrc"].eventOf, person.uri))
        # g.add((person.uri, NS_DICT["sem"].actorType, NS_DICT["cwrc"].NaturalPerson))

        # Labelling the event
        g.add((self.uri, RDFS.label, Literal(self.title)))
        text = self.date_tag.text + ": " + self.text
        g.add((self.uri, NS_DICT["dcterms"].description, Literal(text)))

        # Typing of the event
        g.add((self.uri, RDF.type, NS_DICT["sem"].Event))
        for x in self.event_type:
            g.add((self.uri, NS_DICT["sem"].eventType, x))

        # Attaching place
        for x in self.place:
            g.add((self.uri, NS_DICT["sem"].hasPlace, x))

        # Attaching actors, including the biographee incase they're not mentioned
        if person:
            g.add((self.uri, NS_DICT["sem"].hasActor, person.uri))

        for x in self.actors:
            g.add((self.uri, NS_DICT["sem"].hasActor, x))

        # Typing of time and attaching certainty
        g.add((self.uri, NS_DICT["sem"].timeType, create_cwrc_uri(self.time_type)))
        if self.time_certainty:
            g.add((self.uri, NS_DICT["cwrc"].hasTimeCertainty, create_cwrc_uri(self.time_certainty)))

        # Attaching the time stamp to the event
        if self.predicate:
            g.add((self.uri, self.predicate, self.date))
        else:
            if self.time_type == "PunctiveTime":
                g.add((self.uri, NS_DICT["sem"].hasEarliestBeginTimeStamp, format_date(self.date.split(":")[0])))
                g.add((self.uri, NS_DICT["sem"].hasLatestEndTimeStamp, format_date(self.date.split(":")[1])))
            elif self.time_type == "IntervalTime":
                g.add((self.uri, NS_DICT["sem"].hasBeginTimeStamp, format_date(self.date.split(":")[0])))
                g.add((self.uri, NS_DICT["sem"].hasEndTimeStamp, format_date(self.date.split(":")[1])))

        if self.date_tag.name == "DATESTRUCT":
            g.add((self.uri, NS_DICT["sem"].hasTime, Literal(' '.join(str(self.date_tag.get_text()).split()))))

        return g

    def __str__(self):
        string = "\ttitle: " + self.title + "\n"
        string += "\tevent_type: "
        for x in self.event_type:
            string += str(x) + "\n"
        string += "\tactors: "
        for x in self.actors:
            string += str(x) + "\n"
        string += "\tplaces: "
        for x in self.place:
            string += str(x) + "\n"
        string += "\tdatetag: " + str(self.date_tag) + "\n"
        string += "\tdate: " + str(self.date) + "\n"
        string += "\ttime_type: " + str(self.time_type) + "\n"
        string += "\ttime_certainty: " + str(self.time_certainty) + "\n"
        string += "\tpredicate: " + str(self.predicate) + "\n"
        string += "\tEvent tag:\n " + str(self.tag.prettify()) + "\n"
        return string
