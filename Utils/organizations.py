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

    def __init__(self, uri, name, altlabels, other_attributes=None, tag=None):
        super(Organization, self).__init__()
        self.name = name
        self.altlabels = altlabels
        if tag:
            self.altlabels = []
            self.uri = self.tag_to_org(tag)
        elif ".xml" in uri:
            self.uri = "https://commons.cwrc.ca/orlando:" + uri.replace(".xml","")
        elif other_attributes:
            self.uri = rdflib.term.URIRef(uri)
        else:
            self.uri = rdflib.term.URIRef(str(utilities.NS_DICT["cwrc"]) + uri)
        
        if self.name in self.altlabels:
            self.altlabels.remove(self.name)
        
    def tag_to_org(self,tag):
        uri = None
        if "STANDARD" in tag.attrs:
            uri = tag.get("STANDARD")
            self.name = uri
        if "REG" in tag.attrs:
            self.altlabels.append(tag.get("REG"))
        if tag.text:
            self.altlabels.append(tag.text)
        
        return utilities.make_standard_uri(self.name + " ORG", ns="cwrc")



    def to_triple(self):
        g = utilities.create_graph()
        g.add((self.uri, RDFS.label, Literal(self.name)))
        g.add((self.uri, RDF.type, utilities.NS_DICT["org"].Organization))
        for x in self.altlabels:
            g.add((self.uri, utilities.NS_DICT["skos"].altLabel, Literal(x)))
        return g

    def __str__(self):
        string = "\tname: " + self.name + "\n"
        string += "\turi: " + str(self.uri) + "\n"
        if self.altlabels:
            string += "\taltlabels: \n"
        for x in self.altlabels:
            string += "\t\t" + x + "\n"
        return string


def get_org_uri(tag):
    global ORG_MAP
    uri = None
    if "REF" in tag.attrs: 
        logger.error(F"In entry: {utilities.get_entry_id(tag)} - ORG tag missing REF attribute: {tag} ")
        uri = rdflib.term.URIRef(tag.get("REF"))
    elif "STANDARD" in tag.attrs:
        name = tag.get("STANDARD")
    elif "REG" in tag.attrs:
        name = tag.get("REG")
    else:
        name = tag.get("STANDARD")
    
    if not uri:
        uri = utilities.make_standard_uri(name + " ORG", ns="cwrc")

    
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
        log_str += "\t\t" + str(new_dict[y]) + ": " + y + "\n"
        count += new_dict[y]
    log_str += "\tTotal Organizations: " + str(count) + "\n\n"

    print(log_str)
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
    org_types = {
        "POLITICALAFFILIATION":utilities.NS_DICT["cwrc"].PoliticalOrganization, 
        "DENOMINATION":utilities.NS_DICT["cwrc"].ReligiousOrganization, 
        "SCHOOL":utilities.NS_DICT["cwrc"].EducationalOrganization
    }

    for org_tag in org_types.keys():
        tag = bio.find_all(org_tag)
        for instance in tag:
            org = get_org(instance)
            if org:
                org_type = org_types[org_tag]

                for x in org:
                    org_uri = get_org_uri(x)
                    
                    if "_ORG" in org_uri:
                        uber_graph += Organization(None,None,None,tag=x).to_triple()

                    uber_graph.add((org_uri, RDF.type, org_type))
                    uber_graph.remove((org_uri, RDF.type, utilities.NS_DICT["org"].Organization))

                    # Adding the hasOrganization relation
                    if org_type == utilities.NS_DICT["cwrc"].ReligiousOrganization:
                        mapped_value = cf.get_mapped_term("Religion", utilities.get_value(instance))
                        if type(mapped_value) is rdflib.term.URIRef:
                            uber_graph.add((mapped_value, utilities.NS_DICT["cwrc"].hasOrganization, org_uri))
                    elif org_type == utilities.NS_DICT["cwrc"].PoliticalOrganization:
                        mapped_value = cf.get_mapped_term("PoliticalAffiliation", utilities.get_value(instance))
                        if type(mapped_value) is rdflib.term.URIRef:
                            uber_graph.add((mapped_value, utilities.NS_DICT["cwrc"].hasOrganization, org_uri))


def create_org_csv_from_auth(path):
    """ Creates orgName.csv based off of authority file using forms as alt labels
    """
    import csv
    w = csv.writer(open("orgNames.csv", "w"))
    with open(path) as f:
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

def create_org_csv():
    import csv
    import os
    w = csv.writer(open("orgNames.csv", "w"))
    filelist = [filename for filename in sorted(os.listdir("../data/organizations_2021_v2")) if filename.endswith(".xml")]
    for filename in filelist:
        with open("../data/organizations_2021_v2/" + filename) as f:
            soup = BeautifulSoup(f, 'lxml-xml')
            uri = "https://commons.cwrc.ca/orlando:"+filename.replace(".xml","")
            label = soup.find("preferredForm").namePart.text
            alt_labels = [x.namePart.text for x in soup.find_all("variant")]
            if label in alt_labels:
                alt_labels.remove(label)
            
            csv_item = [uri, label]
            csv_item += alt_labels
            w.writerow(csv_item)


def csv_to_triples():
    import csv
    global uber_graph
    global org_list
    with open('orgNames.csv', newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            org_list.append(row[1])
            uber_graph += Organization(row[0], row[1], row[2:],other_attributes=True).to_triple()


def main():
    import os
    global uber_graph

    create_org_csv()
    csv_to_triples()
    filelist = [filename for filename in sorted(os.listdir(
        "../data/entry_2021_v2")) if filename.endswith(".xml")]

    for filename in filelist:
        with open("../data/entry_2021_v2/" + filename) as f:
            soup = BeautifulSoup(f, 'lxml-xml')
        extract_org_data(soup)

    file = open("organizations.ttl", "w")
    file.write("#" + str(len(uber_graph)) + " triples created\n")
    file.write(uber_graph.serialize(format="ttl").decode())
    file.close()


if __name__ == "__main__":
    uber_graph = utilities.create_graph()
    main()
