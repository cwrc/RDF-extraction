#!/usr/bin/python3

import rdflib
from bs4 import BeautifulSoup
from rdflib import RDF, RDFS,OWL, Literal

try:
    from Utils import utilities
except Exception as e:
    import utilities

# this is temporary list to ensure that the orgname standard is within the auth list
org_list = []
ORG_COUNT = {}
ORGS_USED = set()
TEMP_ORGS = {}
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
        self.uri = rdflib.term.URIRef(str(utilities.NS_DICT["cwrc_temp"]) + uri)
        # self.uri = rdflib.term.URIRef(uri)

    def to_triple(self):
        g = utilities.create_graph()
        g.add((self.uri, utilities.NS_DICT["foaf"].name, Literal(self.name)))
        g.add((self.uri, RDFS.label, Literal(self.name)))
        g.add((self.uri, RDF.type, utilities.NS_DICT["crm"].E74_Group))
        g.add((self.uri, utilities.NS_DICT["crm"].P2_has_type, utilities.NS_DICT["foaf"].Organization))
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
    global ORG_COUNT
    std_name = tag.get("STANDARD")
    uri = tag.get("REF")
    if uri:
        uri = uri.strip()
        ORGS_USED.add(uri)
        if uri in utilities.ORGANIZATION_MAP:
            if utilities.ORGANIZATION_MAP[uri]["Primary Identifier"] != "":
                uri = utilities.ORGANIZATION_MAP[uri]["Primary Identifier"]
            else:
                uri = utilities.ORGANIZATION_MAP[uri]['CWRC URI']
        else:
            logger.warn(F"Organization not in published authority list: {uri}, {tag}")
        
        uri = rdflib.term.URIRef(uri)
    
    else:
        if std_name:
            name = std_name.strip()
        elif tag.get("REG"):
            name = tag.get("REG").strip()
        else:
            logger.warn(F"No standard name or URI: {tag}")
            name = tag.get_text()
        uri = utilities.make_standard_uri(name + " ORG", ns="temp")
        logger.warn(F"Organization has no REF attribute: {tag}, {uri}")
        ORGS_USED.add(uri)
        TEMP_ORGS[uri] = name
    
    if str(uri) in ORG_COUNT:
        ORG_COUNT[str(uri)] += 1
    else:
        ORG_COUNT[str(uri)] = 1

    return uri


def get_primary_uri(cwrc_uri):
    primary_identifier = utilities.ORGANIZATION_MAP[cwrc_uri]["Primary Identifier"]
    
    if primary_identifier == "":
        return cwrc_uri 
    return primary_identifier

def get_secondary_uris(cwrc_uri):
    secondary_identifier = utilities.ORGANIZATION_MAP[cwrc_uri]["Secondary Identifier"]
    secondary_uris = []
    if secondary_identifier != "":
        secondary_uris = secondary_identifier.split(" | ")
    
    secondary_uris.append(cwrc_uri)
    
    return secondary_uris

def add_organizations():
    g = utilities.create_graph()

    for x in ORGS_USED:
        if x in utilities.ORGANIZATION_MAP:
            primary_identifier = rdflib.term.URIRef(get_primary_uri(x))
            secondary_uris = get_secondary_uris(x)
            g.add((primary_identifier, RDF.type, utilities.NS_DICT["crm"].E74_Group))
            for secondary_uri in secondary_uris:
                g.add((primary_identifier, OWL.sameAs, rdflib.term.URIRef(secondary_uri)))
                
            g.add((primary_identifier, RDFS.label, Literal(utilities.ORGANIZATION_MAP[x]["Preferred Name"])))
            
        elif x in TEMP_ORGS:
            primary_identifier = rdflib.term.URIRef(x)
            g.add((primary_identifier, RDF.type, utilities.NS_DICT["crm"].E74_Group))
            g.add((primary_identifier, RDFS.label, Literal(TEMP_ORGS[x])))
        else:
            primary_identifier = rdflib.term.URIRef(x)
            g.add((primary_identifier, RDF.type, utilities.NS_DICT["crm"].E74_Group))
            
    
    return g        

def log_mapping(detail=True):
    from collections import OrderedDict
    log_str = "Mentioned Orgnames:\n"
    new_dict = OrderedDict(sorted(ORG_COUNT.items(), key=lambda t: t[1], reverse=True))
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
   
    org_type_dict = {
        utilities.NS_DICT["biography"].religiousOrganization: ("Religion", "PoliticalAffiliation"),
        utilities.NS_DICT["biography"].politicalOrganization: ("PoliticalAffiliation", "Religion")
    }
   
    for element in elements:
        tag = bio.find_all(element)
        for instance in tag:
            org = get_org(instance)
            if not org:
                continue
            
            if element == elements[0]:
                org_type = utilities.NS_DICT["biography"].politicalOrganization
            elif element == elements[1]:
                org_type = utilities.NS_DICT["biography"].religiousOrganization
            elif element == elements[2]:
                org_type = utilities.NS_DICT["biography"].educationalOrganization

            # Adding the hasOrganization relation
            for x in org:
                org_uri = get_org_uri(x)
                
                uber_graph.add((org_uri, RDF.type, utilities.NS_DICT["crm"].E74_Group))
                uber_graph.add((org_uri, utilities.NS_DICT["crm"].P2_has_type, org_type))
                uber_graph.remove((org_uri, utilities.NS_DICT["crm"].P2_has_type, utilities.NS_DICT["foaf"].Organization))


                mapped_value = None
                for org_type_key, terms in org_type_dict.items():
                    if org_type == org_type_key:
                        mapped_value = cf.get_mapped_term(terms[0], utilities.get_value(instance))
                        if type(mapped_value) is not rdflib.term.URIRef:
                            mapped_value = cf.get_mapped_term(terms[1], utilities.get_value(instance))

                if type(mapped_value) is rdflib.term.URIRef:
                    uber_graph.add((org_uri, utilities.NS_DICT["crm"].P2_has_type, mapped_value))
                

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

    path = "../data/entry_2023-10-04"
    # create_org_csv()
    # csv_to_triples()
    filelist = [filename for filename in sorted(os.listdir(
        path)) if filename.endswith(".xml")]

    for filename in filelist:
        with open(F"{path}/{filename}") as f:
            soup = BeautifulSoup(f, 'lxml-xml')
        extract_org_data(soup)

    file = open("organizations.ttl", "w")
    file.write("#" + str(len(uber_graph)) + " triples created\n")
    file.write(uber_graph.serialize(format="ttl"))
    file.close()


if __name__ == "__main__":
    uber_graph = utilities.create_graph()
    main()
