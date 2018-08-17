#!/usr/bin/python3

from bs4 import BeautifulSoup
from rdflib import RDF, RDFS, Literal
import rdflib
import culturalForm as cf
from biography import bind_ns, NS_DICT, make_standard_uri

uber_graph = rdflib.Graph()
namespace_manager = rdflib.namespace.NamespaceManager(uber_graph)
bind_ns(namespace_manager, NS_DICT)

# this is temporary list to ensure that the orgname standard is within the auth list
org_list = []


class Organization(object):
    """docstring for Organization
    Currently dependent on the org authority list --> org csv

    TODO: if not typed as any of the orgs to be typed as org:FormalOrg
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
        self.uri = rdflib.term.URIRef(str(NS_DICT["cwrc"]) + uri)

    # TODO figure out if i can just return tuple or triple without creating a whole graph
    # Evaluate efficency of creating this graph or just returning a tuple and have the biography deal with it
    def to_tuple(self):
        pass
        # return ((person_uri, self.uri, self.value))

    def to_triple(self):
        g = rdflib.Graph()
        namespace_manager = rdflib.namespace.NamespaceManager(g)
        bind_ns(namespace_manager, NS_DICT)
        g.add((self.uri, NS_DICT["foaf"].name, Literal(self.name)))
        g.add((self.uri, RDFS.label, Literal(self.name)))
        g.add((self.uri, RDF.type, NS_DICT["org"].FormalOrganization))
        for x in self.altlabels:
            g.add((self.uri, NS_DICT["skos"].altLabel, Literal(x)))
        return g

    def __str__(self):
        string = "\tname: " + self.name + "\n"
        string += "\turi: " + str(self.uri) + "\n"
        if self.altlabels:
            string += "\tlabels: \n"
        for x in self.altlabels:
            string += "\t\t" + x + "\n"
        return string


def get_name(bio):
    return (bio.biography.div0.standard.text)


def get_org_uri(tag):
    if tag.get("standard") in org_list:
        name = tag.get("standard")
    elif tag.get("reg") in org_list:
        name = tag.get("reg")
    else:
        name = tag.get("standard")

    return make_standard_uri(name + " ORG", ns="cwrc")


def get_org(tag):
    orgs = tag.find_all("orgname")
    if not orgs:
        if tag.parent.name == "orgname":
            return [tag.parent]

    return orgs


def extract_org_data(bio):
    elements = ["politicalaffiliation", "denomination", "school"]
    global uber_graph
    for element in elements:
        tag = bio.find_all(element)
        for instance in tag:
            org = get_org(instance)
            if org:
                if element == elements[0]:
                    org_type = NS_DICT["cwrc"].PoliticalOrganization
                elif element == elements[1]:
                    org_type = NS_DICT["cwrc"].ReligiousOrganization
                elif element == elements[2]:
                    org_type = NS_DICT["cwrc"].EducationalOrganization

                for x in org:
                    org_uri = get_org_uri(x)
                    uber_graph.add((org_uri, RDF.type, org_type))
                    uber_graph.remove((org_uri, RDF.type, NS_DICT["org"].FormalOrganization))

                    # Adding the hasOrganization relation
                    if org_type == NS_DICT["cwrc"].ReligiousOrganization:
                        mapped_value = cf.get_mapped_term("Religion", cf.get_value(instance))
                        if type(mapped_value) is rdflib.term.URIRef:
                            uber_graph.add((mapped_value, NS_DICT["cwrc"].hasOrganization, org_uri))
                    elif org_type == NS_DICT["cwrc"].PoliticalOrganization:
                        mapped_value = cf.get_mapped_term("PoliticalAffiliation", cf.get_value(instance))
                        if type(mapped_value) is rdflib.term.URIRef:
                            uber_graph.add((mapped_value, NS_DICT["cwrc"].hasOrganization, org_uri))


def create_org_csv():
    import csv
    w = csv.writer(open("orgNames.csv", "w"))
    with open("scrapes/authority/org_auth.xml") as f:
        soup = BeautifulSoup(f, 'lxml')
    items = soup.find_all("authorityitem")
    for x in items:
        std = x.get("standard")
        disp = x.get("display")
        forms = [form.text for form in x.find_all("form")]
        uri = get_org_uri(std)
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
    csv_to_triples()
    # create_org_csv()

    filelist = [filename for filename in sorted(os.listdir("bio_data")) if filename.endswith(".xml")]

    for filename in filelist:
        with open("bio_data/" + filename) as f:
            soup = BeautifulSoup(f, 'lxml')
        extract_org_data(soup)

    file = open("organizations.ttl", "w")
    file.write("#" + str(len(uber_graph)) + " triples created\n")
    file.write(uber_graph.serialize(format="ttl").decode())
    file.close()


if __name__ == "__main__":
    main()
