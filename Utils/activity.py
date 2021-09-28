import rdflib
from rdflib import RDF, RDFS, Literal, XSD
from Utils.citation import Citation
from Utils import utilities, organizations

logger = utilities.config_logger("activity")

def get_participants(tag):
    """ Returns participants within an event (any name/org mentioned)"""
    participants = []
    for x in tag.find_all("NAME"):
        participants.append(utilities.make_standard_uri(x.get("STANDARD")))
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
    if date[-1] == "-":
        date = date.strip("-")

    if len(date) in [10,7,4]:
        return Literal(date, datatype=XSD.date)
    else:
        return Literal(date)


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
        "attribute":"E13_Attribute_Assignment"
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
        self.text = self.text.replace(".", ". ").strip()

        

    def __init__(self, person, title, id, tag, activity_type="generic", attributes={}):
        super(Activity, self).__init__()
        self.title = title
        self.tag = tag
        self.id = id
        self.uri = utilities.create_uri("data", id)
        self.places = utilities.get_places(tag)
        

        self.person = person
        # attributes = {predicate:[objects]}
        self.attributes = attributes
        self.activity_type = None
        
        if activity_type.lower() in Activity.activity_map:
            self.activity_type = utilities.NS_DICT["crm"][Activity.activity_map[activity_type.lower()]]            

        self.participants = get_participants(tag)
        if person.uri in self.participants:
            self.participants.remove(person.uri)
        
        self.biographers = []
        for x in self.participants:
            if x in person.biographers:
                self.participants.remove(x)
                self.biographers.append(x)
        
        self.event_type = get_event_type(tag)


        # NOTE: Event could possibly have multiple types/non cwrc types? may need to revise
        # self.type = utilities.create_cwrc_uri(type)

        # TODO: replace initials with full name of author where applicable
        self.get_snippet()
        self.date_tag = get_date_tag(tag)
        self.date_text = None

        # self.text = self.date_tag.text+": " + self.text
        self.precision = None 
        
        if self.date_tag:
            self.date_text = self.date_tag.get_text()
            self.precision = self.certainty_map[self.date_tag.get("CERTAINTY")]
            self.precision = utilities.create_uri("cwrc", self.precision)
            if self.date_tag.name == "DATERANGE":
                print(self.date_tag)
                if self.date_tag.get("FROM") and self.date_tag.get("TO"):
                    self.date = self.date_tag.get("FROM") + ":" + self.date_tag.get("TO")
                else:
                    self.date = self.date_tag.get("FROM")
            else:
                self.date = self.date_tag.get("VALUE")
                self.date = format_date(self.date)
        else: 
            self.date= None

    def to_triple(self, person=None):
        g = utilities.create_graph()
        # Create two activities
        activity = g.resource(self.uri)
        activity_label = self.person.name +": "+  self.title
        connection = None
        if self.activity_type:
            activity.add(RDF.type, self.activity_type)
        else:
            activity.add(RDF.type, utilities.NS_DICT["crm"][self.activity_map["attribute"]])
            connection = g.resource(f"{self.uri}_connection")
            connection.add(RDF.type, utilities.NS_DICT["crm"][self.activity_map["generic"]])
            
            activity.add(utilities.NS_DICT["crm"].P141_assigned,connection)
            activity.add(utilities.NS_DICT["crm"].P140_assigned_attribute_to,self.person.uri)
            connection.add(RDFS.label, Literal(activity_label+" (connection)"))
        
        activity.add(RDFS.label, Literal(activity_label))
        
        if "Birth" in str(self.activity_type):
            activity.add(utilities.NS_DICT["crm"].P98_brought_into_life, self.person.uri)
        elif "Death" in str(self.activity_type):
            activity.add(utilities.NS_DICT["crm"].P100_was_death_of, self.person.uri)

        if self.date:
            time_span = g.resource(self.uri + "_time-span")
            time_span.add(RDFS.label, Literal(activity_label + " time-span"))
            time_span.add(utilities.NS_DICT["crm"]["P82_at_some_time_within"], Literal(self.date_text))
            
            if connection:
                connection.add(utilities.NS_DICT["crm"]["P4_has_time-span"], time_span)
            else:
                activity.add(utilities.NS_DICT["crm"]["P4_has_time-span"], time_span)
            
            time_span.add(RDF.type, utilities.NS_DICT["crm"]["E52_Time-Span"])
            if self.precision:
                time_span.add(utilities.NS_DICT["crm"].P2_has_type, self.precision)

            if ":" in self.date:
                time_span.add(utilities.NS_DICT["crm"]["P82a_begin_of_the_begin"], format_date(self.date.split(":")[0]))
                time_span.add(utilities.NS_DICT["crm"]["P82b_end_of_the_end"], format_date(self.date.split(":")[1]))
            else:
                time_span.add(utilities.NS_DICT["crm"]["P82a_begin_of_the_begin"], format_date(self.date))
                time_span.add(utilities.NS_DICT["crm"]["P82b_end_of_the_end"], format_date(self.date))


        if self.text:
            activity.add(utilities.NS_DICT["crm"].P3_has_note, Literal(self.text))

        for x in self.places:
            activity.add(utilities.NS_DICT["crm"].P7_took_place_at, x)
            
        if "Attribute" not in str(self.activity_type):
            for x in self.event_type:
                activity.add(utilities.NS_DICT["crm"].P2_has_type, x)

        if "Activity" in str(self.activity_type) and self.attributes:
            for pred in self.attributes:
                activity.add(utilities.NS_DICT["crm"].P2_has_type, pred)
                for obj in self.attributes[pred]: 
                    activity.add(utilities.NS_DICT["crm"].P2_has_type, obj)
        elif connection:
            for pred in self.attributes:
                connection.add(utilities.NS_DICT["crm"].P2_has_type, pred)
                if "Self" in pred:
                    connection.add(utilities.NS_DICT["crm"].P14_carried_out_by, self.person.uri)
                for obj in self.attributes[pred]:
                    connection.add(utilities.NS_DICT["crm"].P16_used_specific_object, obj)

        else:
            print(self.attributes)
            for pred in self.attributes:
                for obj in self.attributes[pred]:
                    print(pred, obj)
                    activity.add(pred, obj)
        
        if connection:
            for x in self.participants:
                connection.add(utilities.NS_DICT["crm"].P11_had_participant, x)
        else:            
            for x in self.participants:
                activity.add(utilities.NS_DICT["crm"].P11_had_participant, x)

        if "Activity" in str(self.activity_type):
            activity.add(utilities.NS_DICT["crm"].P14_carried_out_by, self.person.uri)

        return g

