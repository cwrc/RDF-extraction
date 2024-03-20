from bs4 import BeautifulSoup
import csv
import os

# Folder containing your XML files
DIRECTORY_PATH = '../data/organizations_2024-03-12/'

# CSV file to store the extracted information
CSV_FILE_PATH = 'org_data.csv'

# Extend the headers with separate columns for Wikidata and VIAF URLs

tag_mapping = {
    "projectId": "Project ID",
    "recordCreationDate": "Record Creation Date",
    "recordChangeDate": "Record Change Date",
    "personType": "Person Type",
    "namePart": "Name Part",
    "variantType": "Variant Type",
    "preferredForm": "Preferred Form",
    "displayLabel": "Display Label",
    "sameAs": "Same As",
    "dateSingle": "Date Single",
    "standardDate": "Standard Date",
    "orlandoStandardName": "Orlando Standard Name",
}

headers = ['ID', 'Project ID', 'Record Creation Date', 'Record Change Date', 'Preferred Name', 'Displayed Name', 'Orlando Standard Name', 'SameAs Wikidata', 'SameAs VIAF', 'SameAs Getty','Alternate Name']

def parse_xml_with_bs(file_path):
    """
    Parse an XML file with Beautiful Soup and extract relevant information, including specific name variant types
    and categorizing 'sameAs' URLs into Wikidata and VIAF.
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'lxml-xml')  # Use 'lxml-xml' for parsing XML

    # Initialize a dictionary for all possible columns to handle missing values
    data = {header: '' for header in headers}

    # Extract basic information
    data['Project ID'] = soup.find('projectId').text if soup.find('projectId') else ''
    data['Record Creation Date'] = soup.find('recordCreationDate').text if soup.find('recordCreationDate') else ''
    data['Record Change Date'] = soup.find('recordChangeDate').text if soup.find('recordChangeDate') else ''
    
    data['Preferred Name'] = soup.find('preferredForm').text.strip() if soup.find('preferredForm') else ''
    data['Displayed Name'] = soup.find('displayLabel').text if soup.find('displayLabel') else ''
    data['Preferred Name'] = data['Preferred Name'].replace("\n", " ")

    alternate_names = []
    # Extract variant names
    variants = soup.find_all('variant')
    for variant in variants:
        variant_type = variant.find('variantType').text if variant.find('variantType') else ''
        if variant_type in tag_mapping:  # Check if the variant type is in our headers
            name_part = variant.find('namePart').text if variant.find('namePart') else ''
            data[tag_mapping[variant_type]] = name_part
        elif variant_type == '':
            alternate_names.append(variant.find('namePart').text if variant.find('namePart') else "")
        else:
            print(f"Variant type '{variant_type}' not in headers for file: {file_path} ")

    alternate_names = [x for x in set(alternate_names) if x]
    data['Alternate Name'] = ' | '.join(alternate_names).replace("\n", " ").replace("\t", " ").replace("   ","")

    # Separate 'sameAs' URLs based on source
    same_as_wikidata = []
    same_as_viaf = []
    same_as_getty = []
    
    for same_as in soup.find_all('sameAs'):
        url = same_as.text
        if 'wikidata.org' in url:
            same_as_wikidata.append(url)
        elif 'viaf.org' in url:
            same_as_viaf.append(url)
        elif 'getty.edu' in url:
            same_as_getty.append(url)
    
    same_as_viaf = list(set(same_as_viaf))
    same_as_wikidata = list(set(same_as_wikidata))
    same_as_getty = list(set(same_as_getty))
    
    same_as_viaf.sort()
    same_as_wikidata.sort()
    same_as_getty.sort()
    
    data['SameAs Wikidata'] = ' | '.join(same_as_wikidata)
    data['SameAs VIAF'] = ' | '.join(same_as_viaf)
    data['SameAs Getty'] = ' | '.join(same_as_getty)
    
    
    return data #[data[header] for header in headers]

# Open the CSV file for writing
with open(CSV_FILE_PATH, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.DictWriter(file, fieldnames=headers)
    writer.writeheader()

    # Process each XML file in the folder
    for filename in os.listdir(DIRECTORY_PATH):
        if filename.endswith('.xml'):
            file_path = os.path.join(DIRECTORY_PATH, filename)
            try:
                # print(f"Parsing {filename}")
                row = parse_xml_with_bs(file_path)
                row["ID"] = filename.split('.')[0]  # Replace 'Project ID' with the filename
                
                writer.writerow(row)
            except Exception as e:
                print(f"Error parsing {filename}: {e}")

print(f"Data extracted to {CSV_FILE_PATH}")
