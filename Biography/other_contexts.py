from Utils import utilities
from Utils.context import Context, get_event_type, get_context_type
from Utils.event import Event
from Utils.activity import Activity 

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
    event_type = "HealthEvent"
    for context in contexts:
        mode = context.get("ISSUE")
        context_type = get_context_type("HEALTH", mode)
        paragraphs = context.find_all("P")
        for paragraph in paragraphs:
            context_id = person.id + "_" + context_type + "_" + str(count)

            temp_context = Context(context_id, paragraph, "HEALTH", "identifying", mode)
            person.add_context(temp_context)
            count += 1

        events = context.find_all("CHRONSTRUCT")
        for event in events:
            context_id = person.id + "_" + context_type + "_" + str(count)
            temp_context = Context(context_id, event, "HEALTH", "identifying", mode)

            activity_id = context_id.replace("Context","Event") + "_"+ str(event_count)
            label = f"{utilities.split_by_casing(event_type)}"
            activity = Activity(person, label, activity_id, event, activity_type="generic")
            activity.event_type.append(utilities.create_cwrc_uri(event_type))
            temp_context.link_activity(activity)
            person.add_activity(activity)


            # event_title = person.name + " - " + context_type.split("Context")[0] + " Event"
            # event_uri = person.id + "_" + context_type.split("Context")[0] + "Event_" + str(event_count)
            # temp_event = Event(event_title, event_uri, event, "HealthEvent")

            # temp_context.link_event(temp_event)
            # person.add_event(temp_event)
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
        event_type = get_event_type(context)
        context_type = get_context_type(context)
        for x in contexts:
            paragraphs = x.find_all("P")
            for paragraph in paragraphs:
                context_id = person.id + "_" + context_type + "_" + str(count)

                temp_context = Context(context_id, paragraph, context, "identifying")
                person.add_context(temp_context)
                count += 1

            events = x.find_all("CHRONSTRUCT")
            for event in events:
                context_id = person.id + "_" + context_type + "_" + str(count)
                temp_context = Context(context_id, event, context, "identifying")

                activity_id = context_id.replace("Context","Event") + "_"+ str(event_count)
                label = f"{utilities.split_by_casing(event_type)}"
                activity = Activity(person, label, activity_id, event, activity_type="generic")
                activity.event_type.append(utilities.create_cwrc_uri(event_type))
                temp_context.link_activity(activity)
                person.add_activity(activity)

                # event_title = person.name + " - " + context_type.split("Context")[0] + " Event"
                # event_uri = person.id + "_" + \
                #     context_type.split("Context")[0] + "Event_" + str(event_count)
                # temp_event = Event(event_title, event_uri, event, type=event_type)

                # temp_context.link_event(temp_event)
                # person.add_event(temp_event)
                person.add_context(temp_context)

                count += 1
                event_count += 1

    extract_health_contexts_data(bio, person)


def main():
    from bs4 import BeautifulSoup
    from biography import Biography

    ext_type = "Violence, Wealth, Leisure and Society, Other Life Event, Health contexts"
    extraction_mode, file_dict = utilities.parse_args(
        __file__, ext_type, logger)

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
        extract_other_contexts_data(soup, person)

        graph = person.to_graph()

        utilities.create_individual_triples(
            extraction_mode, person, "other_contexts")
        utilities.manage_mode(extraction_mode, person, graph)

        uber_graph += graph

    logger.info(str(len(uber_graph)) + " triples created")
    if extraction_mode.verbosity >= 0:
        print(str(len(uber_graph)) + " total triples created")

    utilities.create_uber_triples(extraction_mode, uber_graph, "other_contexts")
    logger.info("Time completed: " + utilities.get_current_time())


if __name__ == "__main__":
    main()
