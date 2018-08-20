import rdflib
import biography
from context import Context
from log import *
"""
Status: ~85%
Events still need to be handled
Possibly add OtherLifeEvent to list
"""
# Will remove logging after triples are verified
log = Log("log/other_contexts/errors")
log.test_name("Other Context extraction Error Logging")
extract_log = Log("log/other_contexts/extraction")
extract_log.test_name("Other Context extraction Test Logging")
turtle_log = Log("log/other_contexts/triples")
turtle_log.test_name("Other Context extracted Triples")


def extract_other_contexts_data(bio, person):
    """
        loops through tags within other_context list and creates
        simple identifying contexts, as no triples are currently being
        extracted from these contexts due to there being no unique subtagging
        TODO: after reviewing contexts/events remove uber_graph
    """
    other_contexts = ["violence", "wealth", "leisureandsociety"]
    # other_contexts = ["chronstruct"]
    # TODO: handle chronproses --> events, still unsure quite of the relationship between a context and event

    uber_graph = rdflib.Graph()
    namespace_manager = rdflib.namespace.NamespaceManager(uber_graph)
    biography.bind_ns(namespace_manager, biography.NS_DICT)

    for context in other_contexts:
        contexts = bio.find_all(context)
        count = 0
        for x in contexts:
            id = person.id + "_" + context + "Context"
            if count > 0:
                id += str(count)

            temp_context = Context(id, x, context, "identifying")

            uber_graph += temp_context.to_triple(person)
            person.add_context(temp_context)

            count += 1

    turtle_log.subtitle("Other contexts for " + person.name)
    turtle_log.subtitle(str(len(uber_graph)) + " triples created")
    turtle_log.msg(uber_graph.serialize(format="ttl").decode(), stdout=False)

    return uber_graph


def main():
    def get_name(bio):
        return (bio.biography.div0.standard.text)

    def get_sex(bio):
        return (bio.biography.get("sex"))

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
    for filename in filelist:
        with open("bio_data/" + filename) as f:
            soup = BeautifulSoup(f, 'lxml')

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

        uber_graph += graph
        entry_num += 1

    turtle_log.subtitle(str(len(uber_graph)) + " triples created")
    turtle_log.msg(uber_graph.serialize(format="ttl").decode(), stdout=False)
    turtle_log.msg("")

if __name__ == "__main__":
    # auth = [env.env("USER_NAME"), env.env("PASSWORD")]
    # login.main(auth)
    # test()
    main()
