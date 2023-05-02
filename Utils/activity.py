import rdflib
from rdflib import RDF, RDFS, Literal, XSD
from Utils.citation import Citation
from Utils import utilities, organizations
import datetime
logger = utilities.config_logger("activity")

def get_participants(tag):
    """ Returns participants within an event (any name/org mentioned)"""
    participants = []
    for x in tag.find_all("NAME"):
        participants.append(utilities.get_name_uri(x))
    for x in tag.find_all("ORGNAME"):
        participants.append(organizations.get_org_uri(x))
    return participants
    # todo remove bibliographers

def get_event_type(tag):
    """Returns the types of the event"""
    event_types = []
    tag = tag.find("CHRONSTRUCT")
    if tag:
        event_type = tag.get("RELEVANCE")
        if not event_type:
            logger.error("Missing RELEVANCE attribute:" + str(tag))
        else:
            event_types.append(Activity.event_type_map[event_type])

        event_type = tag.get("CHRONCOLUMN")
        if not event_type:
            logger.error("Missing CHRONCOLUMN attribute:" + str(tag))
        else:
            event_types.append(Activity.event_type_map[event_type])


        return [utilities.create_cwrc_uri(x) for x in event_types]
    return []


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


    formatted_date = None

    if date[-1] == "-":
        date = date.strip("-")

    if len(date) == 19:
        formatted_date = Literal(date, datatype=XSD.dateTime)
    elif len(date) in [5, 4]:
        logger.warning("unideal date format: " + date)
        formatted_date = Literal(date, datatype=XSD.gYear)
    elif len(date) == 7:
        logger.warning("unideal date format: " + date)
        formatted_date = Literal(date, datatype=XSD.gYearMonth)
    elif len(date) == 10:
        logger.warning("unideal date format: " + date)
        formatted_date = Literal(date, datatype=XSD.date)
    else:
        logger.warning("Unknown date format: " + date)
        formatted_date = Literal(date)


    return formatted_date


def get_next_month(date):
    # Returns date with next occurring month, ex. 2019-10-1 --> 2019-11-1, or 2012-12-01 --> 2013-01-01,
    # note this only guaranteed to work for date.days <= 28, and may fail for dates later than so.
    return datetime.datetime(date.year+1 if date.month == 12 else date.year, 1 if date.month == 12 else date.month + 1, date.day)


def date_parse(date_string: str, both=True):
    # Strip spaces surrounding the date string
    if not date_string:
        return date_string, False, date_string
    
    date_string = date_string.strip().rstrip()
    end_dt = None

    try:
        dt = datetime.datetime.strptime(date_string, "%Y-%m-%d")
        end_dt = dt + datetime.timedelta(days=1, seconds=-1)
        return dt.isoformat(), True, end_dt.isoformat()
    except ValueError:
        pass
    try:
        dt = datetime.datetime.strptime(date_string, "%Y--")
        end_dt = dt.replace(year=dt.year+1) - datetime.timedelta(seconds=1)
        return dt.isoformat(), True, end_dt.isoformat()
    except ValueError:
        pass
    try:
        dt = datetime.datetime.strptime(date_string, "%Y-")
        end_dt = dt.replace(year=dt.year+1) - datetime.timedelta(seconds=1)
        return dt.isoformat(), True, end_dt.isoformat()
    except ValueError:
        pass

    try:
        dt = datetime.datetime.strptime(date_string, "%Y")
        end_dt = dt.replace(year=dt.year+1) - datetime.timedelta(seconds=1)
        return dt.isoformat(), True, end_dt.isoformat()
    except ValueError:
        pass

    try:
        dt = datetime.datetime.strptime(date_string, "%Y-%m-")
        end_dt = get_next_month(dt) - datetime.timedelta(seconds=1)
        return dt.isoformat(), True, end_dt.isoformat()
    except ValueError:
        pass

    try:
        dt = datetime.datetime.strptime(date_string, "%Y-%m")
        end_dt = get_next_month(dt) - datetime.timedelta(seconds=1)
        return dt.isoformat(), True, end_dt.isoformat()
    except ValueError:
        pass

    try:
        dt = datetime.datetime.strptime(date_string, "%B %Y")
        end_dt = get_next_month(dt) - datetime.timedelta(seconds=1)
        return dt.isoformat(), True, end_dt.isoformat()
    except ValueError:
        pass

    try:
        dt = datetime.datetime.strptime(date_string, "%d %B %Y")
        end_dt = dt + datetime.timedelta(days=1, seconds=-1)
        return dt.isoformat(), True, end_dt.isoformat()
    except ValueError:
        pass

    try:
        dt = datetime.datetime.strptime(date_string, "%Y-%m--")
        end_dt = get_next_month(dt) - datetime.timedelta(seconds=1)
        return dt.isoformat(), True, end_dt.isoformat()
    except ValueError:
        pass

    try:
        dt = datetime.datetime.strptime(date_string, "%b %Y")
        end_dt = get_next_month(dt) - datetime.timedelta(seconds=1)
        return dt.isoformat(), True, end_dt.isoformat()
    except ValueError:
        pass

    try:
        dt = datetime.datetime.strptime(date_string, "%d %b %Y")
        end_dt = dt + datetime.timedelta(days=1, seconds=-1)
        return dt.isoformat(), True, end_dt.isoformat()
    except ValueError:
        pass

    return date_string, False, date_string



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

class Activity(object):
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

    activity_map = {
        "birth": "E67_Birth",
        "death": "E69_Death",
        "generic": "E7_Activity",
        "generic+": "E7_Activity", # assigning  to activity
        "attribute":"E13_Attribute_Assignment" # cultural forms
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
        None: "unknownCertainty",
    }

    def get_snippet(self):
        # removing tags that mess up the snippet
        utilities.remove_unwanted_tags(self.tag)
        self.text = self.tag.get_text()
        if not self.text:
            logger.error("Empty tag encountered when creating the context:  " + self.id +
                         ": Within:  " + self.tag.name + " " + str(self.tag))
            self.text = ""
        else:
            self.text = utilities.limit_to_full_sentences(str(self.text), utilities.MAX_WORD_COUNT)
        
        date = self.tag.find("DATE")
        if not date:
            date = self.tag.find("DATERANGE")    
        
        if date:
            self.text = self.text.replace(date.text, date.text + ": ")
        
        # todo: add smarter method to clean up period spacing.
        self.text = self.text.replace("\n", " ").strip()
        self.text = self.text.replace(".", ". ").strip()

        

    def __init__(self, person, title, id, tag, activity_type="generic", attributes={},related_activity=None):
        super(Activity, self).__init__()
        self.title = title
        self.tag = tag
        self.id = id
        self.uri = utilities.create_uri("data", id)
        self.connection_uri = None

        # TODO: populate this variable with different possibilities similar to the activity map
        self.activity_path = activity_type
        self.activity_type = None
        
        if self.activity_path == "generic+":
            self.uri = utilities.create_uri("data", id+"_Context")
            self.connection_uri = utilities.create_uri("data", id)
        else:
            self.uri = utilities.create_uri("data", id)

        
        self.places = utilities.get_places(tag)
        self.related_activity = related_activity #TODO: Review Usage

        if not person:
            self.person = None
        else:
            self.person = person
        # attributes = {predicate:[objects]}
        self.attributes = attributes
        
        if activity_type.lower() in Activity.activity_map:
            self.activity_type = utilities.NS_DICT["crm"][Activity.activity_map[activity_type.lower()]]            

        self.participants = get_participants(tag)
        self.biographers = []
        
        # Cleaning list of participants
        if self.person:
            if person.uri in self.participants:
                self.participants.remove(person.uri)
            
            for x in self.participants:
                if x in person.biographers:
                    self.participants.remove(x)
                    self.biographers.append(x)
            
        self.event_type = get_event_type(tag)


        # TODO: replace initials with full name of author where applicable
        self.get_snippet()
        self.date_tag = get_date_tag(tag)
        self.date_text = None
        self.start_date = None
        self.end_date = None
        self.date = None
        # self.text = self.date_tag.text+": " + self.text
        self.precision = None 
        
        if self.date_tag:
            self.date_text = self.date_tag.get_text()
            self.precision = self.certainty_map[self.date_tag.get("CERTAINTY")]
            self.precision = utilities.create_uri("cwrc", self.precision)
            if self.date_tag.name == "DATERANGE":
                if self.date_tag.get("FROM") and self.date_tag.get("TO"):
                    self.start_date, status, status = date_parse(self.date_tag.get("FROM"))
                    self.end_date, status, status = date_parse(self.date_tag.get("TO"))
                    self.date = self.date_tag.get("FROM") +" : "+self.date_tag.get("TO")
                else:
                    self.start_date, status, self.end_date = date_parse(self.date_tag.get("FROM"))
                    self.date = self.date_tag.get("FROM")
            else:
                self.date = self.date_tag.get("VALUE")
                if self.date:
                    self.start_date, status, self.end_date = date_parse(self.date)
        else: 
            self.date= None

    def __str__(self):
        string = F"""
title: {self.title}
tag: {self.tag}
id: {self.id}
uri: {self.uri}
places: {self.places}
related_activity: {self.related_activity}
attributes: {self.attributes}
activity_path: {self.activity_path}
activity_type: {self.activity_type}
participants: {self.participants}
biographers: {self.biographers}
event_type: {self.event_type}
date_tag: {self.date_tag}
date_text: {self.date_text}
start_date: {self.start_date}
end_date: {self.end_date}
date: {self.date}
precision: {self.precision}
>\nperson: {self.person}
        """
        return string

    def to_triple(self, person=None):
        g = utilities.create_graph()
        activity = None

        if self.activity_path == "generic+":
            activity = g.resource(self.uri)
        else:
            activity = g.resource(self.uri)


        activity_label = self.title
        if self.person:
            activity_label = self.person.name +": "+  self.title
            
        if self.date:
            if ":" in self.date:
                date_1 = self.date.split(":")[0].strip()[:4]
                date_2 = self.date.split(":")[1].strip()[:4]
                if date_1 == date_2:
                    activity_label = F"{date_1}: {activity_label}"
                else:
                    activity_label = F"{date_1}-{date_2}: {activity_label}"
            else:
                activity_label = F"{self.date[:4]}: {activity_label}"

        connection = None
        if self.activity_type:
            activity.add(RDF.type, self.activity_type)
        else:
            activity.add(RDF.type, utilities.NS_DICT["crm"][self.activity_map["attribute"]])
            connection = g.resource(f"{self.uri}_connection")
            connection.add(RDF.type, utilities.NS_DICT["crm"][self.activity_map["generic"]])
            
            activity.add(utilities.NS_DICT["crm"].P141_assigned,connection)
            activity.add(utilities.NS_DICT["crm"].P140_assigned_attribute_to,self.person.uri)
            connection.add(RDFS.label, Literal(
                activity_label+" (connection)", lang="en"))
            
            if self.event_type:
                event_type = self.event_type[0].replace("Context","Event")
                connection.add(utilities.NS_DICT["crm"].P2_has_type, rdflib.term.URIRef(event_type))

        activity.add(RDFS.label, Literal(activity_label, lang="en"))

        if "Birth" in str(self.activity_type):
            activity.add(utilities.NS_DICT["crm"].P98_brought_into_life, self.person.uri)
        elif "Death" in str(self.activity_type):
            activity.add(utilities.NS_DICT["crm"].P100_was_death_of, self.person.uri)

        if self.date is not None:
            time_span = g.resource(self.uri + "_time-span")
            time_span.add(RDFS.label, Literal(
                activity_label + " time-span", lang="en"))
            time_span.add(utilities.NS_DICT["crm"]["P82_at_some_time_within"], Literal(
                self.date_text, lang="en"))
            
            if connection:
                connection.add(utilities.NS_DICT["crm"]["P4_has_time-span"], time_span)
            else:
                activity.add(utilities.NS_DICT["crm"]["P4_has_time-span"], time_span)
            
            time_span.add(RDF.type, utilities.NS_DICT["crm"]["E52_Time-Span"])
            if self.precision:
                time_span.add(utilities.NS_DICT["crm"].P2_has_type, self.precision)

            time_span.add(utilities.NS_DICT["crm"]["P82a_begin_of_the_begin"], format_date(self.start_date))
            time_span.add(utilities.NS_DICT["crm"]["P82b_end_of_the_end"], format_date(self.end_date))


        if self.text:
            activity.add(utilities.NS_DICT["crm"].P3_has_note, Literal(
                self.text, lang="en"))


        if self.activity_path != "generic+":
            for x in self.places:
                activity.add(utilities.NS_DICT["crm"].P7_took_place_at, x)
            
        if "Attribute" not in str(self.activity_type):
            for x in self.event_type:
                activity.add(utilities.NS_DICT["crm"].P2_has_type, x)


        if self.activity_path == "generic+":            
            # TODO Review this portion of code
            connection = g.resource(f"{self.connection_uri}")
            connection.add(RDFS.label, Literal(activity_label+" (??)"))
            connection.add(RDF.type, utilities.NS_DICT["crm"][self.activity_map["generic"]])
            connection.add(utilities.NS_DICT["crm"].P14_carried_out_by, self.person.uri)
            connection.add(utilities.NS_DICT["crm"].P140i_was_attributed_by,activity)

            for x in self.places:
                connection.add(utilities.NS_DICT["crm"].P7_took_place_at, x)

            activity.add(RDF.type, utilities.NS_DICT["crm"][self.activity_map["attribute"]])
            
            # TODO: REMOVE THIS AFTER TESTING
            if len(self.attributes.keys()) > 1:
                logger.warning(F"Multiple types of attributes: {self.attributes}")
            
            for x in self.attributes.keys():
                activity.add(utilities.NS_DICT["crm"].P141_assigned,x)

                
                # TODO: REMOVE THIS AFTER TESTING, there should only be one participant
                if len(self.attributes[x])>1:
                    logger.warning(F"Multiple participants: {self.attributes[x]}")

                for y in self.attributes[x]:
                   connection.add(utilities.NS_DICT["crm"].P11_had_participant, y)



            
            activity.add(utilities.NS_DICT["crm"].P140_assigned_attribute_to,connection)
            

            if self.event_type:
                event_type = self.event_type[0].replace("Context","Event")
                connection.add(utilities.NS_DICT["crm"].P2_has_type, rdflib.term.URIRef(event_type))
        
        elif "Activity" in str(self.activity_type) and self.attributes:
            for pred in self.attributes:
                activity.add(utilities.NS_DICT["crm"].P2_has_type, pred)
                for obj in self.attributes[pred]:
                    if obj not in self.participants: 
                        activity.add(utilities.NS_DICT["crm"].P2_has_type, obj)
        elif connection:
            for pred in self.attributes:
                if any(term in pred for term in ["genderedPoliticalActivity", "activistInvolvementIn", "politicalMembershipIn"]):
                    connection.add(utilities.NS_DICT["crm"].P2_has_type, pred)
                if "Self" in pred:
                    connection.add(utilities.NS_DICT["crm"].P2_has_type, pred)
                    activity.add(utilities.NS_DICT["crm"].P14_carried_out_by, self.person.uri)
                for obj in self.attributes[pred]:
                    connection.add(utilities.NS_DICT["crm"].P16_used_specific_object, obj)

        else:
            for pred in self.attributes:
                for obj in self.attributes[pred]:
                    activity.add(pred, obj)
        
        if not connection:          
            for x in self.participants:
                activity.add(utilities.NS_DICT["crm"].P11_had_participant, x)

        if self.activity_path == "generic+":
            # Relationship is posed by biographer
            for x in self.biographers:
                activity.add(utilities.NS_DICT["crm"].P14_carried_out_by, x)


        elif self.person and "Activity" in str(self.activity_type):
            activity.add(utilities.NS_DICT["crm"].P14_carried_out_by, self.person.uri)

        #TODO: consult if this property should be a list & review usage
        if self.related_activity:
            activity.add(utilities.NS_DICT["crm"].P140_assigned_attribute_to, self.related_activity)


        return g

