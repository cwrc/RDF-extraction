#!/usr/bin/python3


import rdflib

from difflib import get_close_matches
from rdflib import Literal
from Utils import utilities
from Utils.context import Context, get_context_type, get_event_type
from Utils.event import Event
from Utils.organizations import get_org_uri
from Utils.activity import Activity 

"""
Status: ~75%
TODO:
 - review unmapped instances
 - revise method of capturing failed mappings to be similar to culturalforms
 - update predicate for employer/employment
"""
logger = utilities.config_logger("occupation")
uber_graph = utilities.create_graph()


context_count = 0
event_count = 0


class IncomeStatement(object):
    
    def __init__(self, tag, label, id):
        super(IncomeStatement, self).__init__()
        self.tag = tag
        self.value = tag.text
        self.label = label
        self.id = id
        self.uri = utilities.create_uri("temp", self.id)   

    def to_triple(self, context):
        g = utilities.create_graph()
        g.add((self.uri, utilities.NS_DICT["rdf"].type, utilities.NS_DICT["crm"].E54_Dimension))
        g.add((self.uri, utilities.NS_DICT["rdfs"].label, rdflib.Literal(self.label,lang="en")))
        g.add((self.uri, utilities.NS_DICT["rdf"].value, rdflib.Literal(self.value)))
        return g
    
    def __str__(self):
        string = f"\tURI: {self.uri}\n"
        string += f"\tlabel: {self.label}\n"
        string += f"\tvalue: {self.value}\n"
        string += f"\ttag: {self.tag}\n"
        string += f"\tid: {self.id}\n"

        return string
    
class Occupation(object):
    """docstring for Occupation
    """

    def __init__(self, job_tag, predicate=None, other_attributes=None,id=None):
        super(Occupation, self).__init__()
        if predicate:
            self.predicate = predicate
            self.value = self.get_mapped_term(job_tag)
        else:
            self.predicate = self.get_occupation_predicate(job_tag)
            self.value = self.get_mapped_term(self.get_value(job_tag), id=id)

        if other_attributes:
            self.uri = other_attributes

        self.uri = utilities.create_uri("occupation", self.predicate)
    """
    TODO figure out if i can just return tuple or triple without creating
    a whole graph
    Evaluate efficiency of creating this graph or just returning a tuple and
    have the biography deal with it
    """

    def to_triple(self, context):
        g = utilities.create_graph()
        g.add((context.uri, self.uri, self.value))
        return g

    def __str__(self):
        string = "\tURI: " + str(self.uri) + "\n"
        string += "\tpredicate: " + str(self.predicate) + "\n"
        string += "\tvalue: " + str(self.value) + "\n"

        return string

    def get_occupation_predicate(self, tag):
        if tag.name == "JOB":
            if self.get_attribute(tag, "FAMILYBUSINESS"):
                return "familyBasedOccupation"
            else:
                return "paidOccupation"
        if tag.name == "SIGNIFICANTACTIVITY":
            if self.get_attribute(tag, "PHILANTHROPYVOLUNTEER"):
                return "volunteerOccupation"
            else:
                return "Occupation"
        if tag.name == "EMPLOYER":
            return "employment"
        if tag.name == "REMUNERATION":
            return "occupationIncome"


    def get_attribute(self, tag, attribute):
        value = tag.get(attribute)
        if value:
            return value
        return None

    def get_value(self, tag):
        value = self.get_attribute(tag, "REG")
        if not value:
            value = self.get_attribute(tag, "CURRENTALTERNATIVETERM")
        if not value:
            value = str(tag.text)
            value = ' '.join(value.split())
        return value

    def get_mapped_term(self, value, id=None):
        if value == "Counsellor":
            return Literal(value)

        def clean_term(string):
            string = string.lower().replace("-", " ").strip().replace(" ", "")
            return string

        def update_fails(rdf_type, value):
            global fail_dict
            if rdf_type in fail_dict:
                if value in fail_dict[rdf_type]:
                    fail_dict[rdf_type][value] += 1
                else:
                    fail_dict[rdf_type][value] = 1
            else:
                fail_dict[rdf_type] = {value: 1}
        """
            Currently getting exact match ignoring case and "-"
            TODO:
            Make csv of unmapped
        """
        global map_attempt
        global map_success
        global map_fail
        rdf_type = "http://id.lincsproject.ca/occupation/Occupation"
        map_attempt += 1
        term = None
        temp_val = clean_term(value)
        for x in JOB_MAP.keys():
            if temp_val in JOB_MAP[x]:
                term = x
                map_success += 1
                break

        if "http" in str(term):
            term = rdflib.term.URIRef(term)
        elif term:
            term = Literal(term, datatype=rdflib.namespace.XSD.string)
        else:
            term = Literal(value, datatype=rdflib.namespace.XSD.string)
            map_fail += 1
            possibilites = []
            log_str = "Unable to find matching occupation instance for '" + value + "'"

            for x in JOB_MAP.keys():
                if get_close_matches(value.lower(), JOB_MAP[x]):
                    possibilites.append(x)
            if type(term) is Literal:
                update_fails(rdf_type, value)
            else:
                update_fails(rdf_type, value + "->" + str(possibilites) + "?")
                log_str += "Possible matches" + value + "->" + str(possibilites) + "?"

            if id:
                logger.warning("In entry: " + id + " " + log_str)
            else:
                logger.warning(log_str)
        return term


def clean_term(string):
    string = string.lower().replace("-", " ").strip().replace(" ", "")
    return string


def create_job_map():
    import csv
    global JOB_MAP
    with open('../data/occupation_mapping.csv', newline='', encoding="utf8") as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        for row in reader:
            temp_row = [clean_term(x) for x in row[1:]]
            JOB_MAP[row[0]] = (list(filter(None, temp_row)))


JOB_MAP = {}
create_job_map()
map_attempt = 0
map_success = 0
map_fail = 0
fail_dict = {}


def log_mapping_fails(detail=True):
    if 'http://id.lincsproject.ca/occupation/Occupation' in fail_dict:
        job_fail_dict = fail_dict['http://id.lincsproject.ca/occupation/Occupation']
        log_str = "\n\n"
        log_str += "Attempts: " + str(map_attempt) + "\n"
        log_str += "Fails: " + str(map_fail) + "\n"
        log_str += "Success: " + str(map_success) + "\n"
        log_str += "\nFailure Details:" + "\n"
        log_str += "\nUnique Missed Terms: " + str(len(job_fail_dict.keys())) + "\n"

        from collections import OrderedDict

        new_dict = OrderedDict(sorted(job_fail_dict.items(), key=lambda t: t[1], reverse=True))
        count = 0
        for y in new_dict.keys():
            log_str += "\t\t" + str(new_dict[y]) + ": " + y + "\n"
            count += new_dict[y]
        log_str += "\tTotal missed occupation: " + str(count) + "\n\n"

        logger.info(log_str)


def find_occupations(tag, id=None):
    """Creates a list of occupations given the tag
    """

    jobs_tags = tag.find_all("JOB") + tag.find_all("SIGNIFICANTACTIVITY")
    return [Occupation(x, id=id) for x in jobs_tags]

def get_attributes(occupations):
    attributes = {}
    for x in occupations:
        if x.uri in attributes:
            attributes[x.uri].append(x.value)
        else:
            attributes[x.uri] = [x.value]
    return attributes


def get_employer(tag):
    employer = tag.find("NAME")
    if employer:
        return utilities.get_name_uri(employer)
    employer = tag.find("ORGNAME")
    if employer:
        return get_org_uri(employer)
    
    # Note some employers are not in the name or orgname tag
    logger.info(F"Unable to find employer for: {tag}")    
    return None

def extract_occupations(tag_list, context_type, person, list_type="paragraphs"):
    """ Creates the occupation relation and ascribes them to the person along
        with the associated contexts and event
    """
    global context_count
    global event_count
    tag_name = "OCCUPATION"
    CONTEXT_TYPE = get_context_type(tag_name)

    for tag in tag_list:
        temp_context = None
        occupation_list = None
        context_count += 1
        context_id = person.id + "_" + CONTEXT_TYPE + "_" + str(context_count)
        occupation_list = find_occupations(tag, id=person.id)
        attributes = get_attributes(occupation_list)
  
        # Creating identifying context if no occupation is found
        if not occupation_list:
            temp_context = Context(context_id, tag, tag_name, "identifying")
            person.add_context(temp_context)
            continue


        # Creating context for occupation
        temp_context = Context(context_id, tag, tag_name, pattern="occupation")
        event_count = 1 # reset event count for each context, contexts may have multiple events
        related_activities = []

        # Adding employer as participant if there is one 
        employer_tags = tag.find_all("EMPLOYER")
        employers = [ get_employer(x) for x in employer_tags ]
        employers = list(filter(None, employers))
        


        for x in attributes.keys():
            temp_attr = {x:attributes[x]}
            
            # Splitting occupations into multiple events if there are multiple occupations
            for job in temp_attr[x]:
                single_occupation = {x:[job]}            
                activity_id = context_id.replace("Context","Event") + "_"+ str(event_count)
                label = f"Occupation Event: {utilities.split_by_casing(str(x).split('/')[-1]).lower()}"
                
                activity = Activity(person, label, activity_id, tag, activity_type="generic", attributes=single_occupation)
                activity.event_type.append(utilities.create_uri("event",get_event_type(tag_name)))

                if employers:
                    activity.participants = employers
                
                temp_context.link_activity(activity)
                person.add_activity(activity)
                event_count+=1
                related_activities.append(activity.uri)
            
        remuneration_tags = tag.find_all("REMUNERATION")
        income_statement_label = F"{person.name}: Occupation Remuneration Amount"
        income_statements = [ IncomeStatement(x, income_statement_label, context_id+"_remuneration_amount") for x in remuneration_tags ]
        income_event = None
        if income_statements:
            print(*income_statements, sep="\n")
            activity_id = F"{context_id}_remuneration"
            temp_attr = {utilities.NS_DICT["crm"].P141_assigned : [ x.uri for x in income_statements ]}
            temp_attr[utilities.NS_DICT["crm"].P2_has_type] = [utilities.create_uri("biography","occupationIncome")]
            income_event = Activity(person, "Occupation Remuneration Event", activity_id, tag, activity_type="attribute", attributes=temp_attr, related_activity=related_activities, additional_nodes=income_statements)
            temp_context.link_activity(income_event)
            person.add_activity(income_event)
        
        person.add_context(temp_context)


def extract_occupation_data(bio, person):
    occupations = bio.find_all("OCCUPATION")
    global context_count
    global event_count
    context_count = 0
    event_count = 0
    for occupation in occupations:
        paragraphs = occupation.find_all("P")
        events = occupation.find_all("CHRONSTRUCT")
        extract_occupations(paragraphs, "OCCUPATION", person)
        extract_occupations(events, "OCCUPATION", person, "events")


def main():
    from bs4 import BeautifulSoup
    from biography import Biography

    extraction_mode, file_dict = utilities.parse_args(
        __file__, "Occupation", logger)

    uber_graph = utilities.create_graph()

    for filename in file_dict.keys():
        with open(filename) as f:
            soup = BeautifulSoup(f, 'lxml-xml')

        person_id = filename.split("/")[-1][:6]

        print(filename)
        print(file_dict[filename])
        print(person_id)
        print("*" * 55)

        person = Biography(person_id, soup)
        extract_occupation_data(soup, person)

        graph = person.to_graph()

        utilities.create_individual_triples(
            extraction_mode, person, "occcupation")
        utilities.manage_mode(extraction_mode, person, graph)

        uber_graph += graph

    log_mapping_fails()
    logger.info(str(len(uber_graph)) + " triples created")
    if extraction_mode.verbosity >= 0:
        print(str(len(uber_graph)) + " total triples created")

    utilities.create_uber_triples(extraction_mode, uber_graph, "occcupation")
    logger.info("Time completed: " + utilities.get_current_time())


if __name__ == "__main__":
    main()
