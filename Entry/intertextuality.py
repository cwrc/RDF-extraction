import rdflib
logger = utilities.config_logger("intertextuality")


def main():
    from bs4 import BeautifulSoup
    import culturalForm

    file_dict = utilities.parse_args(__file__, "Occupation")

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
        extract_intertextuality_data(soup, person)

        graph = person.to_graph()

        temp_path = "extracted_triples/intertextuality_turtle/" + person_id + "_intertextuality.ttl"
        utilities.create_extracted_file(temp_path, person)

        print(person.to_file())

        uber_graph += graph
        entry_num += 1

    log_mapping_fails()
    print("UberGraph is size:", len(uber_graph))
    temp_path = "extracted_triples/intertextuality.ttl"
    utilities.create_extracted_uberfile(temp_path, uber_graph)

    temp_path = "extracted_triples/intertextuality.rdf"
    utilities.create_extracted_uberfile(temp_path, uber_graph, "pretty-xml")


if __name__ == '__main__':
    main()
