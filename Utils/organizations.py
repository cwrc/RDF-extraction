#!/usr/bin/python3

import rdflib
from bs4 import BeautifulSoup
from rdflib import RDF, RDFS, Literal

try:
    from Utils import utilities
except Exception as e:
    import utilities

# this is temporary list to ensure that the orgname standard is within the auth list
org_list = []
ORG_MAP = {}
logger = utilities.config_logger("organizations")


class Organization(object):
    """docstring for Organization
    Currently dependent on the org authority list --> org csv
    1) Going to create each one as an organization as they arise and merge them together in uber graph at the end
    2) Will likely be more efficent to add triples in the graph concurrently and add if they don't already exist.
    And adding triples but I could be wrong in terms of time for querying for each org every time.
    I think by letting the serialization dealing with duplicate triples it might be even
    TODO: test efficency among the two approaches
    """

    def __init__(self, uri, name, altlabels, other_attributes=None):
        super(Organization, self).__init__()
        self.name = name

        self.altlabels = altlabels
        self.uri = rdflib.term.URIRef(str(utilities.NS_DICT["cwrc"]) + uri)
        # self.uri = rdflib.term.URIRef(uri)

    # TODO figure out if i can just return tuple or triple without creating a whole graph
    # Evaluate efficency of creating this graph or just returning a tuple and have the biography deal with it
    def to_tuple(self):
        pass
        # return ((person_uri, self.uri, self.value))

    def to_triple(self):
        g = utilities.create_graph()
        g.add((self.uri, utilities.NS_DICT["foaf"].name, Literal(self.name)))
        g.add((self.uri, RDFS.label, Literal(self.name)))
        g.add((self.uri, RDF.type, utilities.NS_DICT["foaf"].Organization))
        for x in self.altlabels:
            g.add((self.uri, utilities.NS_DICT["skos"].altLabel, Literal(x)))
        return g

    def __str__(self):
        string = "\tname: " + self.name + "\n"
        string += "\turi: " + str(self.uri) + "\n"
        if self.altlabels:
            string += "\tlabels: \n"
        for x in self.altlabels:
            string += "\t\t" + x + "\n"
        return string


def get_org_uri(tag):
    global ORG_MAP
    std_name = tag.get("STANDARD")
    uri = tag.get("REF")
    if uri:
        if uri in utilities.ORGANIZATION_MAP:
            uri = utilities.ORGANIZATION_MAP[uri]
        
        uri = rdflib.term.URIRef(uri)
    
    else:
        if std_name in org_list:
            name = std_name
        elif tag.get("REG") in org_list:
            name = tag.get("REG")
        elif std_name:
            name = std_name
        else:
            logger.warn(F"No standard name or URI: {tag}")
            name = tag.get_text()
        uri = utilities.make_standard_uri(name + " ORG", ns="temp")
    
    if str(uri) in ORG_MAP:
        ORG_MAP[str(uri)] += 1
    else:
        ORG_MAP[str(uri)] = 1

    return uri


def log_mapping(detail=True):
    from collections import OrderedDict
    log_str = "Mentioned Orgnames:\n"
    new_dict = OrderedDict(sorted(ORG_MAP.items(), key=lambda t: t[1], reverse=True))
    count = 0
    for y in new_dict.keys():
        log_str += "\t\t" + str(new_dict[y]) + ": " + y.split("#")[0] + "\n"
        count += new_dict[y]
    log_str += "\tTotal Organizations: " + str(count) + "\n\n"

    logger.info(log_str)


def get_org(tag):
    orgs = tag.find_all("ORGNAME")
    if not orgs:
        if tag.parent.name == "ORGNAME":
            return [tag.parent]

    return orgs


def extract_org_data(bio):
    import culturalForm as cf
    global uber_graph
    elements = ["POLITICALAFFILIATION", "DENOMINATION", "SCHOOL"]
    for element in elements:
        tag = bio.find_all(element)
        for instance in tag:
            org = get_org(instance)
            if org:
                if element == elements[0]:
                    org_type = utilities.NS_DICT["biography"].politicalOrganization
                elif element == elements[1]:
                    org_type = utilities.NS_DICT["biography"].religiousOrganization
                elif element == elements[2]:
                    org_type = utilities.NS_DICT["biography"].educationalOrganization

                for x in org:
                    org_uri = get_org_uri(x)
                    uber_graph.add((org_uri, RDF.type, org_type))
                    uber_graph.remove((org_uri, RDF.type, utilities.NS_DICT["foaf"].Organization))

                    # Adding the hasOrganization relation
                    if org_type == utilities.NS_DICT["biography"].religiousOrganization:
                        mapped_value = cf.get_mapped_term("Religion", utilities.get_value(instance))
                        if type(mapped_value) is rdflib.term.URIRef:
                            uber_graph.add((mapped_value, utilities.NS_DICT["cwrc"].hasOrganization, org_uri))
                    elif org_type == utilities.NS_DICT["biography"].politicalOrganization:
                        mapped_value = cf.get_mapped_term("PoliticalAffiliation", utilities.get_value(instance))
                        if type(mapped_value) is rdflib.term.URIRef:
                            uber_graph.add((mapped_value, utilities.NS_DICT["biography"].hasOrganization, org_uri))


def create_org_csv():
    """ Creates orgName.csv based off of authority file using forms as alt labels
    """
    import csv
    w = csv.writer(open("orgNames.csv", "w"))
    with open("../data/orlando_UTF8ISO8601ExportBuilder_1561501400922003000/authority_xml_orgname/authority_xml_orgname.xml") as f:
        soup = BeautifulSoup(f, 'lxml-xml')
    items = soup.find_all("AUTHORITYITEM")

    for x in items:
        std = x.get("STANDARD")
        disp = x.get("DISPLAY")
        forms = [form.text for form in x.find_all("FORM")]
        uri = get_org_uri(x)
        csv_item = [uri, std]
        if disp:
            csv_item.append(disp)
        if forms:
            csv_item += forms

        w.writerow(csv_item)


def csv_to_triples():
    import csv
    global uber_graph
    global org_list
    with open('orgNames.csv', newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            org_list.append(row[1])
            uber_graph += Organization(row[0], row[1], row[2:]).to_triple()


def main():
    import os
    global uber_graph

    create_org_csv()
    csv_to_triples()
    filelist = [filename for filename in sorted(os.listdir(
        "../data/biography_entries")) if filename.endswith(".xml")]

    for filename in filelist:
        with open("../data/biography_entries/" + filename) as f:
            soup = BeautifulSoup(f, 'lxml-xml')
        extract_org_data(soup)

    file = open("organizations.ttl", "w")
    file.write("#" + str(len(uber_graph)) + " triples created\n")
    file.write(uber_graph.serialize(format="ttl").decode())
    file.close()


if __name__ == "__main__":
    uber_graph = utilities.create_graph()
    main()
