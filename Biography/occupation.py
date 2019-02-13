#!/usr/bin/python3


from biography import Biography
from context import Context
from difflib import get_close_matches
from event import Event
from log import Log
from organizations import get_org_uri
from rdflib import Literal
from utilities import *
import rdflib

"""
Status: ~75%
TODO:
 - review unmapped instances
 - revise method of capturing failed mappings to be similar to culturalforms
"""

# temp log library for debugging
# --> to be eventually replaced with proper logging library
log = Log("log/occupation/errors")
log.test_name("occupation extraction Error Logging")
extract_log = Log("log/occupation/extraction")
extract_log.test_name("occupation extraction Test Logging")
turtle_log = Log("log/occupation/triples")
turtle_log.test_name("Location extracted Triples")

uber_graph = rdflib.Graph()
namespace_manager = rdflib.namespace.NamespaceManager(uber_graph)
bind_ns(namespace_manager, NS_DICT)

context_count = 0
event_count = 0


class Occupation(object):
    """docstring for Occupation
    """

    def __init__(self, job_tag, other_attributes="None"):
        super(Occupation, self).__init__()

        self.predicate = self.get_occupation_predicate(job_tag)
        if self.predicate == "hasEmployer":
            self.value = self.get_employer(job_tag)
        elif self.predicate == "hasOccupationIncome":
            self.value = Literal(self.get_value(job_tag))
        else:
            self.value = self.get_mapped_term(self.get_value(job_tag))

        if other_attributes:
            self.uri = other_attributes

        self.uri = create_uri("cwrc", self.predicate)
    """
    TODO figure out if i can just return tuple or triple without creating
    a whole graph
    Evaluate efficency of creating this graph or just returning a tuple and
    have the biography deal with it
    """

    def to_tuple(self, person_uri):
        return ((person_uri, self.uri, self.value))

    def to_triple(self, person):
        g = rdflib.Graph()
        namespace_manager = rdflib.namespace.NamespaceManager(g)
        bind_ns(namespace_manager, NS_DICT)
        g.add((person.uri, self.uri, self.value))
        return g

    def __str__(self):
        string = "\tURI: " + str(self.uri) + "\n"
        string += "\tpredicate: " + str(self.predicate) + "\n"
        string += "\tvalue: " + str(self.value) + "\n"

        return string

    def get_occupation_predicate(self, tag):
        if tag.name == "JOB":
            if self.get_attribute(tag, "FAMILYBUSINESS"):
                return "hasFamilyBasedOccupation"
            else:
                return "hasPaidOccupation"
        if tag.name == "SIGNIFICANTACTIVITY":
            if self.get_attribute(tag, "PHILANTHROPYVOLUNTEER"):
                return "hasVolunteerOccupation"
            else:
                return "hasOccupation"
        if tag.name == "EMPLOYER":
            return "hasEmployer"
        if tag.name == "REMUNERATION":
            return "hasOccupationIncome"

    def get_employer(self, tag):
        employer = tag.find("NAME")
        if employer:
            return get_name_uri(employer)
        employer = tag.find("ORGNAME")
        if employer:
            return get_org_uri(employer)
        return Literal(self.get_value(tag))

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

    def get_mapped_term(self, value):
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
        rdf_type = "http://sparql.cwrc.ca/ontologies/cwrc#Occupation"
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
            term = Literal("_" + value.lower() + "_", datatype=rdflib.namespace.XSD.string)
            map_fail += 1
            possibilites = []
            for x in JOB_MAP.keys():
                if get_close_matches(value.lower(), JOB_MAP[x]):
                    possibilites.append(x)
            if type(term) is Literal:
                update_fails(rdf_type, value)
            else:
                update_fails(rdf_type, value + "->" + str(possibilites) + "?")
        return term


def clean_term(string):
    string = string.lower().replace("-", " ").strip().replace(" ", "")
    return string


def create_job_map():
    import csv
    global JOB_MAP
    with open('occupation_mapping.csv', newline='', encoding="utf8") as csvfile:
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


def find_occupations(tag):
    """Creates a list of occupations given the tag
    """

    occupation_list = []
    jobs_tags = tag.find_all("JOB") + tag.find_all("SIGNIFICANTACTIVITY")
    jobs_tags += tag.find_all("EMPLOYER") + tag.find_all("REMUNERATION")
    for x in jobs_tags:
        occupation_list.append(Occupation(x))

    return occupation_list


def extract_occupations(tag_list, context_type, person, list_type="paragraphs"):
    """ Creates the occupation relation and ascribes them to the person along
        with the associated contexts and event
    """
    global context_count
    global event_count

    for tag in tag_list:
        temp_context = None
        occupation_list = None
        context_count += 1
        context_id = person.id + "_OccupationContext" + str(context_count)
        occupation_list = find_occupations(tag)
        if occupation_list:
            temp_context = Context(context_id, tag, "OccupationContext")
            temp_context.link_triples(occupation_list)
            person.add_occupation(occupation_list)
        else:
            temp_context = Context(context_id, tag, "OccupationContext", "identifying")

        if list_type == "events":
            event_count += 1
            event_title = person.name + " - " + "Occupation Event"
            event_uri = person.id + "_Occupation_Event" + str(event_count)
            temp_event = Event(event_title, event_uri, tag)
            temp_context.link_event(temp_event)
            person.add_event(temp_event)

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
        extract_occupations(paragraphs, "OccupationContext", person)
        extract_occupations(events, "OccupationContext", person, "events")


def main():
    import os
    from bs4 import BeautifulSoup
    import culturalForm

    def get_name(bio):
        return (bio.BIOGRAPHY.DIV0.STANDARD.text)

    def get_sex(bio):
        return (bio.BIOGRAPHY.get("SEX"))

    filelist = [filename for filename in sorted(os.listdir("bio_data")) if filename.endswith(".xml")]
    entry_num = 1

    uber_graph = rdflib.Graph()
    namespace_manager = rdflib.namespace.NamespaceManager(uber_graph)
    bind_ns(namespace_manager, NS_DICT)

    # for filename in filelist[:200]:
    # for filename in filelist[-5:]:
    test_cases = ["shakwi-b.xml", "woolvi-b.xml", "seacma-b.xml", "atwoma-b.xml",
                  "alcolo-b.xml", "bronem-b.xml", "bronch-b.xml", "levyam-b.xml"]
    # for filename in filelist:
    for filename in test_cases:
        with open("bio_data/" + filename) as f:
            soup = BeautifulSoup(f, 'lxml-xml')

        print(filename)
        person = Biography(
            filename[:-6], get_name(soup), culturalForm.get_mapped_term("Gender", get_sex(soup)))

        extract_occupation_data(soup, person)

        graph = person.to_graph()

        extract_log.subtitle("Entry #" + str(entry_num))
        extract_log.msg(str(person))
        extract_log.subtitle(str(len(graph)) + " triples created")
        extract_log.msg(person.to_file(graph))
        extract_log.subtitle("Entry #" + str(entry_num))
        extract_log.msg("\n\n")

        temp_path = "extracted_triples/occupation_turtle/" + filename[:-6] + "_occupation.ttl"
        create_extracted_file(temp_path, person)

        uber_graph += graph
        entry_num += 1

    turtle_log.subtitle(str(len(uber_graph)) + " triples created")
    turtle_log.msg(uber_graph.serialize(format="ttl").decode(), stdout=False)
    turtle_log.msg("")

    print()
    job_fail_dict = fail_dict['http://sparql.cwrc.ca/ontologies/cwrc#Occupation']
    log.msg("Missed Terms: " + str(len(job_fail_dict.keys())))
    count = 0
    for x in job_fail_dict.keys():
        log.msg(x, ":", job_fail_dict[x])
        count += job_fail_dict[x]
    log.msg("Total Terms: " + str(count))


if __name__ == "__main__":
    main()
