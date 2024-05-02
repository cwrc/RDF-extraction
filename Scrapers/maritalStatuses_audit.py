import os
from bs4 import BeautifulSoup
results = {
    "partner": 0,
    "non partner": 0,
}

def check_nested_tags(filename,soup, nested_tags):
    nested = False

    for nested_tag_p in nested_tags:
        elements = soup.find_all(nested_tag_p)
        for tag in elements:
            print(f"{filename} | Found tag: {nested_tag_p}")
            nested_children = []
            for nested_tag_c in nested_tags:
                nested_child = tag.find_all(nested_tag_c)
                if nested_child:
                    nested_children.append(nested_child)
                    print(F"\t\t{filename} | Nested tag found: {nested_tag_c} inside {nested_tag_p}")
                    nested = True

    return nested

def is_child_of_partner(filename, marriage_element):
    parent = marriage_element.find_parent(['MEMBER', 'MARRIAGE'])
    while parent:
        if parent.name == 'MEMBER' and (parent.get('RELATION') == 'HUSBAND' or parent.get('RELATION') == 'WIFE' or parent.get('RELATION') == 'PARTNER'):
            return True
        elif parent.name == 'MEMBER':
            print(f"Found a member {parent.get('RELATION')} in {filename}")
        parent = parent.find_parent(['MEMBER', 'MARRIAGE'])
    return False

def check_parent_tag_for_marriage(filename,soup):
    marriage_elements = soup.find_all('MARRIAGE')

    for marriage_element in marriage_elements:
        if is_child_of_partner(filename,marriage_element):
            print("<MARRIAGE> is a child of <MEMBER RELATION='Partner'> in file:", filename)
            results["partner"] += 1
        else:
            print("<MARRIAGE> is not a child of <MEMBER RELATION='HUSBAND'> in file:", filename)
            results["non partner"] += 1
    

def main(folder_path):
    nested_tags = ['MARRIAGE', 'DIVORCE', 'SEPARATION']
    xml_files = [f for f in os.listdir(folder_path) if f.endswith('.xml')]
    for xml_file in xml_files:
        # print("Checking file:", xml_file)
        with open(os.path.join(folder_path, xml_file), 'r') as f:
            xml_content = f.read()
        soup = BeautifulSoup(xml_content, 'lxml-xml')

        # check_nested_tags(xml_file,soup, nested_tags)
        check_parent_tag_for_marriage(xml_file, soup)
    print(results)





if __name__ == "__main__":
    # folder_path = input("Enter the path to the folder containing XML files: ")
    folder_path = "../data/entry_files/entry_2024-02-05"
    main(folder_path)
