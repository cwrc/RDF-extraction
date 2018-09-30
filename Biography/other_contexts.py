import rdflib
import biography
from context import Context
from event import Event
from log import *
"""
Status: ~89%
extraction of health context will possibly accompanied by health factors at a later point
only identifying contexts being created
"""
# Will remove logging after triples are verified
log = Log("log/other_contexts/errors")
log.test_name("Other Context extraction Error Logging")
extract_log = Log("log/other_contexts/extraction")
extract_log.test_name("Other Context extraction Test Logging")
turtle_log = Log("log/other_contexts/triples")
turtle_log.test_name("Other Context extracted Triples")


def extract_health_contexts_data(bio, person):
    issue_map = {
        "PHYSICAL": "PhysicalHealthContext",
        "MENTAL": "MentalHealthContext",
        "FEMALEBODY": "WomensHealthContext",
    }
    contexts = bio.find_all("HEALTH")
    count = 1
    event_count = 1
    for context in contexts:
        context_type = context.get("ISSUE")
        if context_type:
            context_type = issue_map[context_type]
        else:
            context_type = "HealthContext"
        paragraphs = context.find_all("P")
        for paragraph in paragraphs:
            context_id = person.id + "_" + context_type + str(count)

            temp_context = Context(context_id, paragraph, context_type, "identifying")
            person.add_context(temp_context)
            count += 1

        events = context.find_all("CHRONSTRUCT")
        for event in events:
            context_id = person.id + "_" + context_type + str(count)
            temp_context = Context(context_id, event, context_type, "identifying")

            event_title = person.name + " - " + context_type.split("Context")[0] + " Event"
            event_uri = person.id + "_" + context_type.split("Context")[0] + "_Event" + str(event_count)
            temp_event = Event(event_title, event_uri, event)

            temp_context.link_event(temp_event)
            person.add_event(temp_event)
            person.add_context(temp_context)

            count += 1
            event_count += 1


def extract_other_contexts_data(bio, person):
    """
        loops through tags within other_context list and creates
        simple identifying contexts, as no triples are currently being
        extracted from these contexts due to there being no unique subtagging
        TODO: after reviewing contexts/events remove uber_graph
    """
    other_contexts = ["VIOLENCE", "WEALTH", "LEISUREANDSOCIETY", "OTHERLIFEEVENT"]

    for context in other_contexts:
        contexts = bio.find_all(context)
        count = 1
        event_count = 1
        for x in contexts:
            paragraphs = x.find_all("P")
            for paragraph in paragraphs:
                context_id = person.id + "_" + Context.context_map[context] + str(count)

                temp_context = Context(context_id, paragraph, context, "identifying")
                person.add_context(temp_context)
                count += 1

            events = x.find_all("CHRONSTRUCT")
            for event in events:
                context_id = person.id + "_" + Context.context_map[context] + str(count)
                temp_context = Context(context_id, event, context, "identifying")

                event_title = person.name + " - " + Context.context_map[context].split("Context")[0] + " Event"
                event_uri = person.id + "_" + \
                    Context.context_map[context].split("Context")[0] + "_Event" + str(event_count)
                temp_event = Event(event_title, event_uri, event)

                temp_context.link_event(temp_event)
                person.add_event(temp_event)
                person.add_context(temp_context)

                count += 1
                event_count += 1

    extract_health_contexts_data(bio, person)


def main():
    def get_name(bio):
        return (bio.BIOGRAPHY.DIV0.STANDARD.text)

    def get_sex(bio):
        return (bio.BIOGRAPHY.get("SEX"))

    import os
    from bs4 import BeautifulSoup
    import culturalForm

    filelist = [filename for filename in sorted(os.listdir("bio_data")) if filename.endswith(".xml")]
    entry_num = 1

    uber_graph = rdflib.Graph()
    namespace_manager = rdflib.namespace.NamespaceManager(uber_graph)
    biography.bind_ns(namespace_manager, biography.NS_DICT)

    # for filename in filelist[:200]:
    # for filename in filelist[-5:]:

    # for filename in filelist:
    # for filename in ["levyam-b.xml", "atwoma-b.xml", "woolvi-b.xml", "clifan-b.xml", "bellfr-b.xml"]:
    for filename in ["woolvi-b.xml"]:
        with open("bio_data/" + filename) as f:
            soup = BeautifulSoup(f, 'lxml-xml')

        print(filename)
        test_person = biography.Biography(
            filename[:-6], get_name(soup), culturalForm.get_mapped_term("Gender", get_sex(soup)))

        extract_other_contexts_data(soup, test_person)

        graph = test_person.to_graph()

        extract_log.subtitle("Entry #" + str(entry_num))
        extract_log.msg(str(test_person))
        extract_log.subtitle(str(len(graph)) + " triples created")
        extract_log.msg(test_person.to_file(graph))
        extract_log.subtitle("Entry #" + str(entry_num))
        extract_log.msg("\n\n")

        file = open("other_contexts_turtle/" + filename[:-6] + "_other_contexts.ttl", "w", encoding="utf-8")
        file.write("#" + str(len(graph)) + " triples created\n")
        file.write(graph.serialize(format="ttl").decode())
        file.close()

        uber_graph += graph
        entry_num += 1

    turtle_log.subtitle(str(len(uber_graph)) + " triples created")
    turtle_log.msg(uber_graph.serialize(format="ttl").decode(), stdout=False)
    turtle_log.msg("")

    file = open("other_contexts.ttl", "w", encoding="utf-8")
    file.write("#" + str(len(uber_graph)) + " triples created\n")
    file.write(uber_graph.serialize(format="ttl").decode())

    file = open("other_contexts.rdf", "w", encoding="utf-8")
    file.write("#" + str(len(uber_graph)) + " triples created\n")
    file.write(uber_graph.serialize(format="pretty-xml").decode())


if __name__ == "__main__":
    # auth = [env.env("USER_NAME"), env.env("PASSWORD")]
    # login.main(auth)
    # test()
    main()
