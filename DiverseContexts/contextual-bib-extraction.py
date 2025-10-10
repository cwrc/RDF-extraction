import copy
import rdflib
from rdflib import Literal
import rdflib.term
from utils import utilities
from utils.context import Context, get_context_type, get_event_type, get_named_entities
from utils.event import Event
from utils.organizations import get_org_uri, get_org_name
from culturalForm import get_mapped_term
from utils.place import Place
import csv
import os
logger = utilities.config_logger("adhoc-bib-extraction")
from bs4 import BeautifulSoup


BIB_PATH = "/Users/alliyyamo/Desktop/orlando-2.0-c-modelling/textbase-pubc/bibls-pubc/"

BIB_FILES = os.listdir(BIB_PATH)
BIB_FILES.sort()
bob = BIB_FILES.pop(0)

EVENT_FILES = []

ROLES = [
    "editor",
    "translator",
    "compiler",
    "adapter",
    "contributor",
    "illustrator",
    "introduction",
    "revised",
    "afterword",
    "transcriber",
    "recipient",
    "rcp",
    "transcriber",
    "author",
    "recipient",
]

ROLE_MAP = {
    "rcp": "recipient",
}


ROLES_TO_TITLE = []

PEOPLE = []

# role ={
#     role_name: "",
#     person_uri: "",
#     title: "", 
#     title_uri: ""
# }
def reduce_roles(roles):
    reduced_roles = []
    for role in roles:
        if role in ROLE_MAP:
            reduced_roles.append(ROLE_MAP[role])
        else:
            reduced_roles.append(role.lower())
    
    reduce_roles = list(set(reduced_roles))
    return reduced_roles


def get_name_string(name_tag):
    name_tag_copy = copy.copy(name_tag)
    unwanted_tags = name_tag_copy.find_all("role")
    for unwanted in unwanted_tags:
        unwanted.decompose()
    name = name_tag_copy.text
    return name
        
def get_roles(doc, main_id):
    names = []
    name_tags = doc.find_all("name")
    
    for name_tag in name_tags:
        rows = []
        row = {}
        if name_tag.parent.name == "relatedItem":
            continue
        
        if 'type' in name_tag.attrs:
            name_type = name_tag['type']
        else:
            name_type = None

        original_uri = None
        if "valueURI" in name_tag.attrs:
            original_uri =  rdflib.term.URIRef(name_tag.attrs["valueURI"])




        name = get_name_string(name_tag)
        name = name.strip()
        name = name.replace("\n", " ")
        name = name.replace("  ", " ")
        

        new_uri = utilities.get_primary_uri(original_uri, name)
        print(f"CWRC URI: {original_uri}")
        print(f"New URI: {new_uri}")
        full_name = name
        if original_uri:
            full_name =  utilities.get_full_name(original_uri, fallback=name)
        else:
            print("sad")



        role = None
        role_terms = name_tag.find_all('roleTerm')
        role_terms = reduce_roles([x.text for x in role_terms])
        
        
        if len(role_terms) == 1:
            role = role_terms[0]
        elif len(role_terms) > 1:
            logger.error(f"Multiple roles found for {name_tag.text}")
            print(role_terms)
            # for role in role_terms:
            #     if role['type'] == "text":
            #         role = role.text
            #     else:
            #         role = role.text
            #         # continue
        else:
            role = "author"
            logger.error(f"No role found for {name_tag.text}")
        

        row = {
            "name": name,
            "full_name": full_name,
            "role": role,
            "person_uri": new_uri,
            "title_uri": utilities.NS_DICT["orlando"][main_id]
        }
        print("row:", row)
        logger.info(row)
        person = {"person_uri": new_uri, "full_name": full_name }
    # print(doc)
    # input()
    pass

def main():
    count = 0
    max = len(BIB_FILES)    
    for filename in BIB_FILES:
        with open(BIB_PATH + filename, "r") as f:
            soup = BeautifulSoup(f, 'lxml-xml')
        
        count+=1
        main_id = str(filename).replace(".xml", "").replace("orlando_", "")
        print(F"{count}/{max}:")
        print(F"MAIN ID: {main_id}")
        get_roles(soup, main_id)
        print("=====================================")
    
    pass

if __name__ == "__main__":
    main()
    