#!/usr/bin/python3
# from Env import env
# import islandora_auth as login
from bs4 import BeautifulSoup
import rdflib

from utilities import *
from context import Context
from event import Event


uber_graph = rdflib.Graph()
namespace_manager = rdflib.namespace.NamespaceManager(uber_graph)
bind_ns(namespace_manager, NS_DICT)

"""
Status: ~75%
Questions pending:
Do freestanding events have a url --> fix link then
What are doing with RS tags
    will we make them actors
What context type should be used
"""


class Freestanding_Event(object):
    """docstring for Freestanding_Event"""

    def __init__(self, event, context):
        super(Freestanding_Event, self).__init__()
        self.event = event
        self.context = context
        self.context.link_event(event)

    def to_graph(self):
        g = rdflib.Graph()
        namespace_manager = rdflib.namespace.NamespaceManager(g)
        bind_ns(namespace_manager, NS_DICT)

        g += self.event.to_triple()
        g += self.context.to_triple()
        return g

    def to_file(self, graph=None, serialization="ttl"):
        if graph:
            return graph.serialize(format=serialization).decode()
        else:
            return self.to_graph().serialize(format=serialization).decode()

    def __str__(self):
        string = "Event:"
        string += str(self.event)
        string += str(self.context)
        return string


def main():
    import os
    filelist = [filename[:-4] for filename in sorted(os.listdir("freeevents_data/")) if filename.endswith(".xml")]
    filelist.sort(key=int)

    entry_num = 1
    global uber_graph

    # for filename in filelist[:1]:
    for filename in filelist:
        with open("freeevents_data/" + str(filename) + ".xml", encoding="utf-8") as f:
            soup = BeautifulSoup(f, 'lxml-xml')

        event_id = "freestanding_event_" + str(filename)
        context_id = "freestanding_event_context_" + str(filename)
        print("===========", filename, "=============")

        event_title = "Freestanding Event #" + str(filename)
        events = soup.find_all("CHRONSTRUCT")
        if not events:
            print(event_title)
            print(events)
            input()
        event_tag = soup.find_all("CHRONSTRUCT")[0]
        context_tag = soup.find_all("FREESTANDING_EVENT")[0]

        temp_context = Context(context_id, context_tag, "Context", "identifying")
        temp_event = Event(event_title, event_id, event_tag)

        freestanding_event = Freestanding_Event(temp_event, temp_context)

        uber_graph += freestanding_event.to_graph()
        entry_num += 1

        temp_path = "extracted_triples/FE_turtle/" + str(filename) + "_FE.ttl"
        create_extracted_file(temp_path, freestanding_event)

    temp_path = "extracted_triples/all_freestandingevents_triples.ttl"
    create_extracted_uberfile(temp_path, uber_graph)


if __name__ == "__main__":
    main()
