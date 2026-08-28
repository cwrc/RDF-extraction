from bs4 import BeautifulSoup
import csv
import os
import datetime

# Folder containing your XML files
DIRECTORY_PATH = '/Users/alliyyamo/Desktop/orlando-2.0-c-modelling/textbase-pubc/organizations-pubc/'

# Get today's date
today_date = datetime.datetime.now().strftime('%Y-%m-%d')

# Insert today's date into the file path
CSV_FILE_PATH = f'org_data_{today_date}.csv'


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
    "alternate names": "Alternate Names",
    "historic": "Historic Name",
}

headers = ['File', 'ID', 'Project ID', 'Record Creation Date', 'Record Change Date', 'Preferred Name', 'Displayed Name', 'Orlando Standard Name', 'SameAs Wikidata', 'SameAs VIAF', 'SameAs Getty','Alternate Name', "Alternate Names", "Historic Name", "CWRC URI", "Primary URI", "Secondary URI"]

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

    same_as_viaf = list(set(same_as_viaf))
    same_as_wikidata = list(set(same_as_wikidata))
    same_as_getty = list(set(same_as_getty))

    same_as_viaf = sorted(same_as_viaf,key=len)
    same_as_wikidata = sorted(same_as_wikidata,key=len)
    same_as_getty = sorted(same_as_getty,key=len)
    same_as_values = same_as_viaf + same_as_wikidata + same_as_getty

    data['SameAs Wikidata'] = ' | '.join(same_as_wikidata)
    data['SameAs VIAF'] = ' | '.join(same_as_viaf)
    data['SameAs Getty'] = ' | '.join(same_as_getty)

    # Set primary and secondary URIs
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

    return data #[data[header] for header in headers]

# Open the CSV file for writing
with open(CSV_FILE_PATH, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.DictWriter(file, fieldnames=headers)
    writer.writeheader()

    # Process each XML file in the folder
    for filename in sorted(os.listdir(DIRECTORY_PATH)):
        if filename.endswith('.xml'):
            file_path = os.path.join(DIRECTORY_PATH, filename)
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

print(f"Data extracted to {CSV_FILE_PATH}")
