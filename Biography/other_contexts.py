import rdflib
from rdflib import RDF, RDFS, Literal
import re
from biography import bind_ns, NS_DICT
from context import Context
from place import Place
from log import *
"""
Status: ~22%
"""
i_count = 0

log = Log("log/other_contexts/errors")
log.test_name("Other Context extraction Error Logging")
extract_log = Log("log/other_contexts/extraction")
extract_log.test_name("Other Context extraction Test Logging")
turtle_log = Log("log/other_contexts/triples")
turtle_log.test_name("Other Context extracted Triples")

CWRC = NS_DICT["cwrc"]


def strip_all_whitespace(string):
# temp function for condensing the context strings for visibility in testing
    return re.sub('[\s+]', '', str(string))


def get_reg(tag):
    return get_attribute(tag, "reg")


def get_attribute(tag, attribute):
    value = tag.get(attribute)
    if value:
        return value
    return None


def get_value(tag):
    value = get_reg(tag)
    if not value:
        value = get_attribute(tag, "CURRENTALTERNATIVETERM")
    if not value:
        value = str(tag.text)
        value = ' '.join(value.split())
    return value


def identifying_motivation(tag):
    identifying_tags = ["place", "name", "orgname"]
    for x in identifying_tags:
        if tag.find(x):
            return "identifying"

    return None


def extract_other_contexts_data(bio, person):

    other_contexts = ["violence", "wealth", "leisureandsociety"]
    # other_contexts = ["chronstruct"]
    # TODO: handle health separately as it has different attributes issue
    # Issue, with values Physical, Mental, FemaleBody, and Unspecified
    # TODO: handle chronproses --> events, still unsure quite of the relationship between a context and event
    # TODO: check if place/org/name
    uber_graph = rdflib.Graph()
    namespace_manager = rdflib.namespace.NamespaceManager(uber_graph)
    bind_ns(namespace_manager, NS_DICT)

    for context in other_contexts:
        contexts = bio.find_all(context)
        count = 0
        if contexts:
            log.msg(person.id)
            log.msg(person.name)
        for x in contexts:
            id = person.id + "_" + context + "Context"
            if count > 0:
                id += str(count)

            # if identifying_motivation(x):
            #     log.msg(str(x.prettify()))
                # TODO: create an identifying context
            # else:
            # orgname = x.find_all("orgname")
            # if orgname:
            #     for org in orgname:
            #         orgcount += 1
            #         if get_attribute(org, "standard"):
            #             orgcount_std += 1
            #             log.msg(str(x))
            #             log.msg(str(org))
            temp_context = Context(id, x, context)

            uber_graph += temp_context.to_triple(person.uri)
            person.add_context(temp_context)

            count += 1

    turtle_log.subtitle("Other contexts for " + person.name)
    turtle_log.subtitle(str(len(uber_graph)) + " triples created")
    turtle_log.msg(uber_graph.serialize(format="ttl").decode(), stdout=False)

    return uber_graph

    print("AYYY")
