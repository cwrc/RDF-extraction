#!/usr/bin/python3

from bs4 import BeautifulSoup
from Utils import utilities
from Utils.context import Context
from Utils.event import Event

logger = utilities.config_logger("freestandingevents")

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

    def __init__(self, id, event, context):
        super(Freestanding_Event, self).__init__()
        self.id = id
        self.event = event
        self.context = context
        self.context.link_event(event)

    def to_graph(self):
        g = utilities.create_graph()
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
    file_dict = utilities.parse_args(__file__, "Freestanding Events")
    extraction_mode, file_dict = utilities.parse_args(
        __file__, "Freestanding Events", logger)

    uber_graph = utilities.create_graph()

    for filename in file_dict.keys():
        with open(filename) as f:
            soup = BeautifulSoup(f, 'lxml-xml')

        file_id = filename.split("/")[-1][:-4]

        event_id = "freestanding_event_" + str(file_id)
        context_id = "freestanding_event_context_" + str(file_id)
        logger.info("==========="+file_id+"=============")

        event_title = "Freestanding Event #" + str(file_id)
        events = soup.find_all("CHRONSTRUCT")
        if not events:
            logger.error(event_title)

        event_tag = soup.find_all("CHRONSTRUCT")
        context_tag = soup.find_all("FREESTANDING_EVENT")

        if len(event_tag) > 1:
            logger.warning("Multiple CHRONSTRUCTs found within: " + filename)

        if len(context_tag) > 1:
            logger.warning(
                "Multiple FREESTANDING_EVENTs found within: " + filename)

        context_tag = context_tag[0]
        event_tag = event_tag[0]

        temp_context = Context(context_id, context_tag,
                               "FREESTANDING_EVENT", "identifying")
        temp_event = Event(event_title, event_id, event_tag, "Event")

        freestanding_event = Freestanding_Event(
            file_id, temp_event, temp_context)

        graph = freestanding_event.to_graph()
        uber_graph += graph

        utilities.create_individual_triples(
            extraction_mode, freestanding_event, "freestanding_event")
        utilities.manage_mode(extraction_mode, freestanding_event, graph)

    utilities.create_uber_triples(
        extraction_mode, uber_graph, "freestanding_event")


if __name__ == "__main__":
    main()
