#!/usr/bin/python3

# from Env import env
# import islandora_auth as login

from difflib import get_close_matches
from rdflib import RDF, RDFS, Literal
import rdflib
import biography
from context import Context
from log import *
from place import Place
from event import Event


"""
Status: ~55%

"""

# temp log library for debugging --> to be eventually replaced with proper logging library
# from log import *
log = Log("log/occupation/errors")
log.test_name("occupation extraction Error Logging")
extract_log = Log("log/occupation/extraction")
extract_log.test_name("occupation extraction Test Logging")
turtle_log = Log("log/occupation/triples")
turtle_log.test_name("Location extracted Triples")

uber_graph = rdflib.Graph()
namespace_manager = rdflib.namespace.NamespaceManager(uber_graph)
biography.bind_ns(namespace_manager, biography.NS_DICT)

context_count = 0
event_count = 0


class Occupation(object):
    """docstring for Occupation
    """

    def __init__(self, predicate, job, other_attributes=None):
        super(Occupation, self).__init__()
        self.predicate = predicate
        self.value = job

        if other_attributes:
            self.uri = other_attributes

        self.uri = biography.create_uri("cwrc", self.predicate)

    # TODO figure out if i can just return tuple or triple without creating a whole graph
    # Evaluate efficency of creating this graph or just returning a tuple and have the biography deal with it
    def to_tuple(self, person_uri):
        return ((person_uri, self.uri, self.value))

    def to_triple(self, person):
        g = rdflib.Graph()
        namespace_manager = rdflib.namespace.NamespaceManager(g)
        biography.bind_ns(namespace_manager, biography.NS_DICT)
        g.add((person.uri, self.uri, self.value))
        return g

    def __str__(self):
        string = "\tURI: " + str(self.uri) + "\n"
        string += "\tpredicate: " + str(self.predicate) + "\n"
        string += "\tvalue: " + str(self.value) + "\n"

        return string


def find_occupations(tag):
    """Creates location list given the tag
    """
    # TODO find alll JOB tags + signAct
    # Translate them to predicates + uris
    occupation_list = None
    return occupation_list


def extract_occupations(tag_list, context_type, person, list_type="paragraphs"):
    """ Creates the location relation and ascribes them to the person along with the associated
        contexts and event
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
            person.add_location(occupation_list)
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
    biography.bind_ns(namespace_manager, biography.NS_DICT)

    # for filename in filelist[:200]:
    # for filename in filelist[-5:]:
    for filename in filelist:
        with open("bio_data/" + filename) as f:
            soup = BeautifulSoup(f, 'lxml-xml')

        print(filename)
        test_person = biography.Biography(
            filename[:-6], get_name(soup), culturalForm.get_mapped_term("Gender", get_sex(soup)))

        extract_occupation_data(soup, test_person)

        graph = test_person.to_graph()

        extract_log.subtitle("Entry #" + str(entry_num))
        extract_log.msg(str(test_person))
        extract_log.subtitle(str(len(graph)) + " triples created")
        extract_log.msg(test_person.to_file(graph))
        extract_log.subtitle("Entry #" + str(entry_num))
        extract_log.msg("\n\n")

        file = open("occupation_turtle/" + filename[:-6] + "_occupation.ttl", "w", encoding="utf-8")
        file.write("#" + str(len(graph)) + " triples created\n")
        file.write(graph.serialize(format="ttl").decode())
        file.close()

        uber_graph += graph
        entry_num += 1

    turtle_log.subtitle(str(len(uber_graph)) + " triples created")
    turtle_log.msg(uber_graph.serialize(format="ttl").decode(), stdout=False)
    turtle_log.msg("")


def test():
    exit()

if __name__ == "__main__":
    # auth = [env.env("USER_NAME"), env.env("PASSWORD")]
    # login.main(auth)
    # test()
    main()
