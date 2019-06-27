from biography import Biography
from Utils import utilities
from Utils.context import Context, get_event_type, get_context_type
from Utils.event import Event
"""
Status: ~89%
extraction of health context will possibly accompanied by health factors at a later point
only identifying contexts being created
"""
logger = utilities.config_logger("other_contexts")
uber_graph = utilities.create_graph()


def extract_health_contexts_data(bio, person):
    contexts = bio.find_all("HEALTH")
    count = 1
    event_count = 1
    for context in contexts:
        mode = context.get("ISSUE")
        context_type = get_context_type("HEALTH", mode)
        paragraphs = context.find_all("P")
        for paragraph in paragraphs:
            context_id = person.id + "_" + context_type + str(count)

            temp_context = Context(context_id, paragraph, "HEALTH", "identifying", mode)
            person.add_context(temp_context)
            count += 1

        events = context.find_all("CHRONSTRUCT")
        for event in events:
            context_id = person.id + "_" + context_type + str(count)
            temp_context = Context(context_id, event, "HEALTH", "identifying", mode)

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
                context_id = person.id + "_" + get_context_type(context) + str(count)

                temp_context = Context(context_id, paragraph, context, "identifying")
                person.add_context(temp_context)
                count += 1

            events = x.find_all("CHRONSTRUCT")
            for event in events:
                context_id = person.id + "_" + get_context_type(context) + str(count)
                temp_context = Context(context_id, event, context, "identifying")

                event_title = person.name + " - " + get_context_type(context).split("Context")[0] + " Event"
                event_uri = person.id + "_" + \
                    get_context_type(context).split("Context")[0] + "_Event" + str(event_count)
                temp_event = Event(event_title, event_uri, event, type=get_event_type(context))

                temp_context.link_event(temp_event)
                person.add_event(temp_event)
                person.add_context(temp_context)

                count += 1
                event_count += 1

    extract_health_contexts_data(bio, person)


def main():
    from bs4 import BeautifulSoup
    import culturalForm

    ext_type = "Violence, Wealth, Leisure and Society, Other Life Event, Health contexts"
    file_dict = utilities.parse_args(__file__, ext_type)

    entry_num = 1

    uber_graph = utilities.create_graph()

    for filename in file_dict.keys():
        with open(filename) as f:
            soup = BeautifulSoup(f, 'lxml-xml')

        person_id = filename.split("/")[-1][:6]

        print(filename)
        print(file_dict[filename])
        print(person_id)
        print("*" * 55)

        person = Biography(person_id, soup, culturalForm.get_mapped_term("Gender", utilities.get_sex(soup)))
        extract_other_contexts_data(soup, person)

        graph = person.to_graph()

        temp_path = "extracted_triples/other_contexts_turtle/" + person_id + "_other_contexts.ttl"
        utilities.create_extracted_file(temp_path, person)

        print(person.to_file())
        uber_graph += graph
        entry_num += 1

    print("UberGraph is size:", len(uber_graph))
    temp_path = "extracted_triples/other_contexts.ttl"
    utilities.create_extracted_uberfile(temp_path, uber_graph)

    temp_path = "extracted_triples/other_contexts.rdf"
    utilities.create_extracted_uberfile(temp_path, uber_graph, "pretty-xml")


if __name__ == "__main__":
    main()
