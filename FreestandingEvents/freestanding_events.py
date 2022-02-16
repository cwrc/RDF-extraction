#!/usr/bin/python3

from bs4 import BeautifulSoup
from Utils import utilities
from Utils.context import Context
from Utils.event import Event
from Utils.activity import Activity

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

    def __init__(self, id, activity, context):
        super(Freestanding_Event, self).__init__()
        self.id = id
        self.activity = activity
        self.context = context
        self.context.link_activity(activity)

    def to_graph(self):
        g = utilities.create_graph()
        g += self.activity.to_triple()
        g += self.context.to_triple()
        return g

    def to_file(self, graph=None, serialization="ttl"):
        if graph:
            return graph.serialize(format=serialization).decode()
        else:
            return self.to_graph().serialize(format=serialization).decode()

    def __str__(self):
        string = "Event:"
        # string += str(self.event)
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
        
        # Creating identifying context
        context_id = "freestanding_event_context_" + str(file_id)
        context_tag = soup.find_all("CHRONEVENT")
        if len(context_tag) > 1:
            logger.warning(
                "Multiple CHRONEVENTs found within: " + filename)

        context_tag = context_tag[0]
        temp_context = Context(context_id, context_tag,
                               "CHRONEVENT", "identifying")

        # Creating activity
        activity_id = F"freestanding_event_{str(file_id)}"
        label = F"Freestanding Event: {str(file_id)}" 
        event_tags = soup.find_all("CHRONSTRUCT")
        if not event_tags:
            logger.error(label)
        elif len(event_tags) > 1:
            logger.warning("Multiple CHRONSTRUCTs found within: " + filename)

        event_tag = event_tags[0]
        activity = Activity(None, label, activity_id, event_tag, activity_type="generic")
        activity.event_type.append(utilities.create_cwrc_uri("Event"))


        # temp_event = Event(event_title, event_id, event_tag, "Event")
        


        freestanding_event = Freestanding_Event(
            file_id, activity, temp_context)

        graph = freestanding_event.to_graph()
        uber_graph += graph

        utilities.create_individual_triples(
            extraction_mode, freestanding_event, "freestanding_event")
        utilities.manage_mode(extraction_mode, freestanding_event, graph)

    utilities.create_uber_triples(
        extraction_mode, uber_graph, "freestanding_event")


if __name__ == "__main__":
    main()
