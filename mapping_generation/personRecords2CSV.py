import datetime
from bs4 import BeautifulSoup
import csv
import os

# Folder containing your XML files
folder_path = '/Users/alliyyamo/Desktop/orlando-2.0-c-modelling/textbase-pubc/persons-pubc/'

files_of_interest = [
                     "b29f292e-4d7e-4475-9512-7b09ab2b1cec.xml",
"ed8fc2e4-827a-4694-8181-13c0a95e2efa.xml",
"60347188-2616-4ef3-a0b7-09f7a7729107.xml",
"0ba7b2ee-836e-4c5b-84c9-90452c9943ce.xml",
"2ceb5c1c-3948-4fbf-9a42-7b16be9d061d.xml",
"74b6f20d-5716-4828-92cf-4a68d13b374a.xml",
                     ]

# CSV file to store the extracted information

# Get today's date
today_date = datetime.datetime.now().strftime('%Y-%m-%d')

# Insert today's date into the file path
csv_file_path = f'people_data_{today_date}.csv'

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
    "alternate names": "Alternative Name",
    "termsOfAddress": "Terms of Address"
}

headers = ['ID','File', 'Project ID', 'Record Creation Date', 'Record Change Date', 'Person Type', 'Full Name', 'Preferred Name', 'Displayed Name', 'Family Name', 'Given Name', 'Terms of Address',
           'Birth Name', 'Married Name', 'Indexed Name', "Alternative Name", 'Pseudonym', 'Used Form', 'Nickname', 'Religious Name', 'Royal Name',
           'Self Constructed Name', 'Styled Name', 'Titled Name', 'Orlando Standard Name', 'SameAs Wikidata', 'SameAs VIAF', 'SameAs Getty', 'Birth Date', 'Death Date', "CWRC URI", "Primary URI", "Secondary URI"]

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

    used_names = soup.find("preferredForm")


    data['Family Name'] = used_names.find('namePart', {'partType': 'family'}).text if used_names.find('namePart', {'partType': 'family'}) else ''
    data['Given Name'] = used_names.find('namePart', {'partType': 'given'}).text if used_names.find('namePart', {'partType': 'given'}) else ''
    data['Terms of Address'] = soup.find('namePart', {'partType': 'termsOfAddress'}).text if soup.find('namePart', {'partType': 'termsOfAddress'}) else ''

    data['Preferred Name'] = soup.find('preferredForm').text.strip() if soup.find('preferredForm') else ''
    data['Displayed Name'] = soup.find('displayLabel').text if soup.find('displayLabel') else ''
    data['Preferred Name'] = data['Preferred Name'].replace("\n", " ")

    # Setting full name
    if data['Displayed Name'] != '':
        data['Full Name'] = data['Displayed Name']
    elif data['Family Name'] != '' and data['Given Name'] != '':
        data['Full Name'] = f"{data['Given Name']} {data['Family Name']}"
    elif data['Preferred Name'] != '':
        data['Full Name'] = data['Preferred Name']
    else:
        data['Full Name'] = ''


    # Extract variant names
    variants = soup.find_all('variant')
    for variant in variants:
        variant_type = variant.find('variantType').text if variant.find('variantType') else ''
        if variant_type in tag_mapping:  # Check if the variant type is in our headers
            name_part = variant.find('namePart').text if variant.find('namePart') else ''
            data[tag_mapping[variant_type]] = name_part
        else:
            print(f"Variant type '{variant_type}' not in headers within {file_path}")

    # Separate 'sameAs' URLs based on source
    same_as_wikidata = []
    same_as_viaf = []
    same_as_getty = []
    same_as_tags = []
    same_as_values = []
    
    for same_as in soup.find_all('sameAs'):
        url = same_as.text
        if 'wikidata.org' in url:
            same_as_wikidata.append(url)
        elif 'viaf.org' in url:
            same_as_viaf.append(url)
        elif 'getty.edu' in url:
            same_as_getty.append(url)
            
        same_as_tags.append(same_as)

    same_as_viaf = list(set(same_as_viaf))  # Remove duplicates
    same_as_wikidata = list(set(same_as_wikidata))  # Remove duplicates
    same_as_getty = list(set(same_as_getty))  # Remove duplicates

    same_as_viaf = sorted(same_as_viaf,key=len)
    same_as_wikidata = sorted(same_as_wikidata,key=len)
    same_as_getty = sorted(same_as_getty,key=len)
    same_as_values = same_as_viaf + same_as_wikidata + same_as_getty

    data['SameAs Wikidata'] = ' | '.join(same_as_wikidata)
    data['SameAs VIAF'] = ' | '.join(same_as_viaf)
    data['SameAs Getty'] = ' | '.join(same_as_getty)

    for tag in same_as_tags:
        if tag.get("preferred") == "yes":
            data['Primary URI'] = tag.text

    if not data['Primary URI']:
        # Set primary and secondary URIs
        if same_as_viaf:
            data['Primary URI'] = same_as_viaf[0]
        elif same_as_wikidata:
            data['Primary URI'] = same_as_wikidata[0]
        elif same_as_getty:
            data['Primary URI'] = same_as_getty[0]

        else:
            data['Primary URI'] = None
            
    if not data['Secondary URI']:
        if data['Primary URI'] is not None and data['Primary URI'] in same_as_values:
            same_as_values.remove(data['Primary URI'])
        if len(same_as_values) > 1:
            data['Secondary URI'] = same_as_values[0]
        else:
            data['Secondary URI'] = None
    
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
    for filename in sorted(os.listdir(folder_path)):
    # for filename in files_of_interest:
        if filename.endswith('.xml'):
            file_path = os.path.join(folder_path, filename)
            try:
                # print(f"Parsing {filename}")
                row = parse_xml_with_bs(file_path)
                row["File"] = filename.split('.')[0]  # Replace 'Project ID' with the filename
                row["ID"] = filename.split('.')[0].replace("orlando_","")  # Replace 'Project ID' with the filename
                row["CWRC URI"] = f"https://commons.cwrc.ca/orlando:{row['ID']}"
                
                if row["Primary URI"] is None:
                    row["Primary URI"] = row["CWRC URI"]
                
                writer.writerow(row)
            except Exception as e:
                print(f"Error parsing {filename}: {e}")

print(f"Data extracted to {csv_file_path}")
