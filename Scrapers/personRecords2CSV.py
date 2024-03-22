from bs4 import BeautifulSoup
import csv
import os

# Folder containing your XML files
folder_path = '../data/person_2024-02-13/'

files_of_interest = [
                     "b29f292e-4d7e-4475-9512-7b09ab2b1cec.xml",
"ed8fc2e4-827a-4694-8181-13c0a95e2efa.xml",
"60347188-2616-4ef3-a0b7-09f7a7729107.xml",
"0ba7b2ee-836e-4c5b-84c9-90452c9943ce.xml",
"2ceb5c1c-3948-4fbf-9a42-7b16be9d061d.xml",
"74b6f20d-5716-4828-92cf-4a68d13b374a.xml",
                     ]

# CSV file to store the extracted information
csv_file_path = 'people_data.csv'

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
    "family": "Family Name",
    "given": "Given Name",
    "nickname": "Nickname",
    "orlandoStandardName": "Orlando Standard Name",
    "pseudonym": "Pseudonym",
    "religiousName": "Religious Name",
    "royalName": "Royal Name",
    "selfConstructedName": "Self Constructed Name",
    "styledName": "Styled Name",
    "titledName": "Titled Name",
    "usedForm": "Used Form",
    "birthName": "Birth Name",
    "marriedName": "Married Name",
    "indexedName": "Indexed Name",
    "termsOfAddress": "Terms of Address"
}

headers = ['ID', 'Project ID', 'Record Creation Date', 'Record Change Date', 'Person Type', 'Preferred Name', 'Displayed Name', 'Family Name', 'Given Name', 'Terms of Address',
           'Birth Name', 'Married Name', 'Indexed Name', 'Pseudonym', 'Used Form', 'Nickname', 'Religious Name', 'Royal Name',
           'Self Constructed Name', 'Styled Name', 'Titled Name', 'Orlando Standard Name', 'SameAs Wikidata', 'SameAs VIAF', 'Birth Date', 'Death Date']

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
    data['Person Type'] = soup.find('personType').text if soup.find('personType') else ''

    data['Family Name'] = soup.find('namePart', {'partType': 'family'}).text if soup.find('namePart', {'partType': 'family'}) else ''
    data['Given Name'] = soup.find('namePart', {'partType': 'given'}).text if soup.find('namePart', {'partType': 'given'}) else ''
    data['Terms of Address'] = soup.find('namePart', {'partType': 'termsOfAddress'}).text if soup.find('namePart', {'partType': 'termsOfAddress'}) else ''

    data['Preferred Name'] = soup.find('preferredForm').text.strip() if soup.find('preferredForm') else ''
    data['Displayed Name'] = soup.find('displayLabel').text if soup.find('displayLabel') else ''
    data['Preferred Name'] = data['Preferred Name'].replace("\n", " ")

    # Extract variant names
    variants = soup.find_all('variant')
    for variant in variants:
        variant_type = variant.find('variantType').text if variant.find('variantType') else ''
        if variant_type in tag_mapping:  # Check if the variant type is in our headers
            name_part = variant.find('namePart').text if variant.find('namePart') else ''
            data[tag_mapping[variant_type]] = name_part
        else:
            print(f"Variant type '{variant_type}' not in headers")

    # Separate 'sameAs' URLs based on source
    same_as_wikidata = []
    same_as_viaf = []
    for same_as in soup.find_all('sameAs'):
        url = same_as.text
        if 'wikidata.org' in url:
            same_as_wikidata.append(url)
        elif 'viaf.org' in url:
            same_as_viaf.append(url)
    
    same_as_viaf = list(set(same_as_viaf))  # Remove duplicates
    same_as_wikidata = list(set(same_as_wikidata))  # Remove duplicates
    
    data['SameAs Wikidata'] = ' | '.join(same_as_wikidata)
    data['SameAs VIAF'] = ' | '.join(same_as_viaf)

    # Extract birth and death dates
    dates = soup.find_all('dateSingle')
    
    for date in dates:
        date_type = date.find('dateType').text if date.find('dateType') else ''
        if date_type == 'birth':
            data['Birth Date'] = date.find('standardDate').text if date.find('standardDate') else ''
        elif date_type == 'death':
            data['Death Date'] = date.find('standardDate').text if date.find('standardDate') else ''
        else:
            print(f"Unknown date type '{date_type}' found in {file_path}")
        
    
    return data #[data[header] for header in headers]

# Open the CSV file for writing
with open(csv_file_path, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.DictWriter(file, fieldnames=headers)
    writer.writeheader()

    # Process each XML file in the folder
    # for filename in os.listdir(folder_path):
    for filename in files_of_interest:
        if filename.endswith('.xml'):
            file_path = os.path.join(folder_path, filename)
            try:
                # print(f"Parsing {filename}")
                row = parse_xml_with_bs(file_path)
                row["ID"] = filename.split('.')[0]  # Replace 'Project ID' with the filename
                
                writer.writerow(row)
            except Exception as e:
                print(f"Error parsing {filename}: {e}")

print(f"Data extracted to {csv_file_path}")
