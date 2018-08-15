#!/usr/bin/python3

# from Env import env
# import islandora_auth as login

from bs4 import BeautifulSoup
from rdflib import RDF, RDFS, Literal
import rdflib

from biography import bind_ns, NS_DICT, make_standard_uri

uber_graph = rdflib.Graph()
namespace_manager = rdflib.namespace.NamespaceManager(uber_graph)
bind_ns(namespace_manager, NS_DICT)


class Organization(object):
    """docstring for Organization
    Currently dependent on the org authority list --> org csv

    TODO: if not typed as any of the orgs to be typed as org:FormalOrg
    investigate instance of "Abbey School" in dataset but not authority file
    1) Going to create each one as an organization as they arise and merge them together in uber graph at the end
    2) Will likely be more efficent to add triples in the graph concurrently and add if they don't already exist.
    And adding triples but I could be wrong in terms of time for querying for each org every time.
    I think by letting the serialization dealing with duplicate triples it might be even
    TODO: test efficency among the two approaches
    """
    def get_altnames(orgName):
        std = orgName.get("standard")
        reg = orgName.get("reg")
        altnames = []
        if reg and reg != std:
            altnames.append(reg)
        free = orgName.text()
        if free and free != std and free != reg:
            altnames.append(free)
        return altnames

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
        for x in self.altlabels:
            g.add((self.uri, NS_DICT["skos"].altLabel, Literal(x, lang='en')))
        return g

    def __str__(self):
        string = "\tname: " + self.name + "\n"
        string += "\turi: " + str(self.uri) + "\n"
        if self.altlabels:
            string += "\tlabels: \n"
        for x in self.altlabels:
            string += "\t\t" + x + "\n"
        return string


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
                    org_type = NS_DICT["cwrc"].PoliticalOrganization                # get element
                elif element == elements[1]:
                    org_type = NS_DICT["cwrc"].ReligiousOrganization
                elif element == elements[2]:
                    org_type = NS_DICT["cwrc"].EducationalOrganization

                for x in org:
                    uber_graph.add((get_org_uri(x.get("standard")), RDF.type, org_type))


def get_name(bio):
    return (bio.biography.div0.standard.text)


def get_org_uri(std_name):
    return make_standard_uri(std_name + " ORG", ns="cwrc")


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
    with open('orgNames.csv', newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            uber_graph += Organization(row[0], row[1], row[2:]).to_triple()


def main():
    import os
    global uber_graph
    csv_to_triples()
    # # create_org_csv()

    filelist = [filename for filename in sorted(os.listdir("bio_data")) if filename.endswith(".xml")]

    for filename in filelist:
        with open("bio_data/" + filename) as f:
            soup = BeautifulSoup(f, 'lxml')
        extract_org_data(soup)

    file = open("organizations.ttl", "w")
    file.write("#" + str(len(uber_graph)) + " triples created\n")
    file.write(uber_graph.serialize(format="ttl").decode())
    file.close()


def test():
    exit()

if __name__ == "__main__":
    # auth = [env.env("USER_NAME"), env.env("PASSWORD")]
    # login.main(auth)
    # test()
    main()
