from bs4 import BeautifulSoup
import csv
import datetime
import os

# Folder containing your XML files
folder_path = '/Users/alliyyamo/Desktop/orlando-2.0-c-modelling/textbase-pubc/bibls-pubc/'

files_of_interest = [
                     "20a696c4-292f-4fca-928e-5c0eb8037d09.xml",
                     ]

# Get today's date
today_date = datetime.datetime.now().strftime('%Y-%m-%d')

# Insert today's date into the file path
csv_file_path = f'title_data_{today_date}.csv'


# Extend the headers with separate columns for Wikidata and VIAF URLs

tag_mapping = {
    "ID": "CWRC ID",
    "URI": "URI",
    "primary": "Primary Title",
    "alternative": "Alternative Title",
    "other": "Other Title",
    "recordIdentifier": "Orlando Record Identifier",
    "none": "No Type Title",
    "None": "No Type Title",
    None: "No Type Title"
}

headers = ["CWRC ID",
"URI",
"Primary Title",
"Alternative Title",
"Other Title",
"No Type Title",
"Orlando Record Identifier", "Counts", "Count_primary", "Count_alternative", "Count_other", "Count_none", "Count_all"] 

def title_cleaner(title):
    """
    Clean up the title by removing unwanted characters.
    """
    return title.replace('\n', '').replace('\r', '').replace('\t', '').strip()


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
    data['Orlando Record Identifier'] = soup.find('recordIdentifier').text if soup.find('recordIdentifier') else ''

    # Extract variant names
    titles = soup.find_all('titleInfo')
    title_type_counts = {
        "all": 0,
        "primary": 0,
        "alternative": 0,
        "none": 0,
        "other": 0
    }
    for title in titles:
        if title.parent.name != "mods":
            continue

        title_type = title.get('usage') or title.get('type')    # Default to 'primary' if 'type' attribute is not present

        if title_type is None:
            data[tag_mapping["none"]] = title_cleaner(title.text)
            title_type_counts["none"] += 1
       
        elif title_type in tag_mapping:  # Check if the variant type is in our headers
            data[tag_mapping[title_type]] = title_cleaner(title.text)
            title_type_counts[title_type] += 1

        else:
            print(f"Title type '{title_type}' not in headers")
            print(title)
            input()
        title_type_counts["all"] += 1



    data["Counts"] = str(title_type_counts)
    data["Count_primary"] = title_type_counts["primary"]
    data["Count_alternative"] = title_type_counts["alternative"]
    data["Count_other"] = title_type_counts["other"]
    data["Count_none"] = title_type_counts["none"]
    data["Count_all"] = title_type_counts["all"]
    
    return data #[data[header] for header in headers]

# Open the CSV file for writing
with open(csv_file_path, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.DictWriter(file, fieldnames=headers)
    writer.writeheader()

    # Process each XML file in the folder
    file_list = os.listdir(folder_path)
    file_list.sort()
    # file_list = files_of_interest
    total = len(file_list)
    
    
    for filename in file_list:
    # for filename in files_of_interest:
        if filename.endswith('.xml'):
            print(f"Processing {filename}: ({file_list.index(filename)+1}/{total})")
            file_path = os.path.join(folder_path, filename)
            try:
                # print(f"Parsing {filename}")
                row = parse_xml_with_bs(file_path)
                row["CWRC ID"] = filename.split('.')[0].replace("orlando_","")  # Replace 'Project ID' with the filename
                row["URI"] = f'https://commons.cwrc.ca/orlando:{row["CWRC ID"]}'
                
                writer.writerow(row)
            except Exception as e:
                print(f"Error parsing {filename}: {e}")
                input("You got some explaining to do...")

print(f"Data extracted to {csv_file_path}")
