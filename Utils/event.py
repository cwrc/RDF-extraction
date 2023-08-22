import rdflib
from rdflib import RDF, RDFS, Literal, XSD
from Utils.citation import Citation
from Utils import utilities, organizations


logger = utilities.config_logger("event")


def get_actors(tag):
    """ Returns actors within an event (any name/org/title mentioned)"""
    actors = []
    for x in tag.find_all("NAME"):
        actors.append(utilities.get_name_uri(x))
    for x in tag.find_all("ORGNAME"):
        actors.append(organizations.get_org_uri(x))
    for x in tag.find_all("TITLE"):
        title = utilities.get_value(x)
        actors.append(utilities.make_standard_uri(title + " TITLE", ns="cwrc"))

    return actors


def get_event_type(tag):
    """Returns the types of the event"""
    event_types = []
    event_type = tag.get("RELEVANCE")
    if not event_type:
        logger.error("Missing RELEVANCE attribute:" + str(tag))
    else:
        event_types.append(Event.event_type_map[event_type])

    event_type = tag.get("CHRONCOLUMN")
    if not event_type:
        logger.error("Missing CHRONCOLUMN attribute:" + str(tag))
    else:
        event_types.append(Event.event_type_map[event_type])

    return [utilities.create_cwrc_uri(x) for x in event_types]


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
        msg = "Multiple date tags detected:\n\t" + str(tag) + "\n"
        for x in tags:
            msg += "\t" + str(x) + "\n"
        logger.warning(msg)

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

# TODO: apply '-' if calendar is BC also log this date


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
        Must be linked to a context through link_event() method 
            ex. temp_context.link_event(temp_event)
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

    def __init__(self, title, id, tag, type="BiographicalEvent"):
        super(Event, self).__init__()
        self.title = title
        self.tag = tag
        self.uri = utilities.create_uri("data", id)
        self.place = utilities.get_places(tag)
        self.place_str = utilities.get_place_strings(tag)
        self.event_type = get_event_type(tag)
        self.actors = get_actors(tag)

        # Creating citations from bibcit tags
        bibcits = tag.find_all("BIBCIT")
        self.citations = [Citation(x) for x in bibcits]

        # NOTE: Event could possibly have multiple types/non cwrc types? may need to revise
        self.type = utilities.create_cwrc_uri(type)

        # No longer grabing text of title, no word limit now
        # TODO: replace initials with full name of author where applicable
        self.text = str(tag.CHRONPROSE.get_text())

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
                self.predicate = utilities.NS_DICT["sem"].hasTimeStamp
            elif self.precision == "BY":
                self.predicate = utilities.NS_DICT["sem"].hasLatestBeginTimeStamp
            elif self.precision == "AFTER":
                self.predicate = utilities.NS_DICT["sem"].hasEarliestBeginTimeStamp
            elif self.precision is None:
                self.predicate = utilities.NS_DICT["sem"].hasTimeStamp
            else:
                self.predicate = utilities.NS_DICT["sem"].hasTime
            self.date = format_date(self.date)

    def to_triple(self, person=None):
        g = utilities.create_graph()

        # NOTE: Event will always be attached to a context, possibly multiple event to the same context

        # Labelling the event
        text = self.date_tag.text + ": " + self.text
        g.add((self.uri, RDFS.label, Literal(text)))

        # Typing of the event --> events might have multiple types down the line
        g.add((self.uri, RDF.type, self.type))

        for x in self.event_type:
            g.add((self.uri, utilities.NS_DICT["sem"].eventType, x))

        for x in self.citations:
            g += x.to_triple(self.uri)

        # Attaching place via blank node
        for index, place in enumerate(self.place):
            blanknode = rdflib.BNode()
            g.add((self.uri, utilities.NS_DICT["sem"].hasPlace, blanknode))
            g.add((blanknode, RDFS.label, Literal(self.place_str[index])))
            g.add((blanknode, utilities.NS_DICT["cwrc"].hasMappedLocation, place))
            g.add((blanknode, RDF.type, utilities.NS_DICT["cwrc"].MappedPlace))

        # Attaching actors, including the biographee incase they're not mentioned
        if person:
            g.add((self.uri, utilities.NS_DICT["sem"].hasActor, person.uri))

        for x in self.actors:
            g.add((self.uri, utilities.NS_DICT["sem"].hasActor, x))

        # Typing of time and attaching certainty
        g.add((self.uri, utilities.NS_DICT["sem"].timeType, utilities.create_cwrc_uri(self.time_type)))
        if self.time_certainty:
            g.add((self.uri, utilities.NS_DICT["cwrc"].hasTimeCertainty,
                   utilities.create_cwrc_uri(self.time_certainty)))

        # Attaching the time stamp to the event
        if self.predicate:
            g.add((self.uri, self.predicate, self.date))
        else:
            if self.time_type == "PunctiveTime":
                g.add((self.uri, utilities.NS_DICT["sem"].hasEarliestBeginTimeStamp,
                       format_date(self.date.split(":")[0])))
                g.add((self.uri, utilities.NS_DICT["sem"].hasLatestEndTimeStamp,
                       format_date(self.date.split(":")[1])))
            elif self.time_type == "IntervalTime":
                g.add((self.uri, utilities.NS_DICT["sem"].hasBeginTimeStamp, format_date(self.date.split(":")[0])))
                g.add((self.uri, utilities.NS_DICT["sem"].hasEndTimeStamp, format_date(self.date.split(":")[1])))

        if self.date_tag.name == "DATESTRUCT":
            g.add((self.uri, utilities.NS_DICT["sem"].hasTime, Literal(
                ' '.join(str(self.date_tag.get_text()).split()))))

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
