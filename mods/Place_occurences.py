import csv


def clean_file_url(file_url):
    if len(file_url) == 36:
        return  "https://commons.cwrc.ca/orlando:" + file_url
    if "_host_" in file_url:
        return file_url.split("_host_")[0]
    return file_url


# Define the input log file and output CSV file paths
log_file_path = '/Users/alliyyamo/Desktop/test/RDF-extraction/Mods/jan-places.log'
csv_file_path = '/Users/alliyyamo/Desktop/test/RDF-extraction/Mods/Place_occurences.csv'

# Define the CSV headers
csv_headers = ['Place Part', 'Full Place String', 'File/URL', 'Place Breakdown']

# Initialize a list to store the CSV rows
csv_rows = []




# Open and read the log file
with open(log_file_path, 'r') as log_file:
    for line in log_file:
        parts = []
        place_part = ""
        full_place_string = ""
        place_breakdown = ""
        file_id = ""
        file_url = ""
        
        if line.startswith("Unable to map place: "):
            line = line.replace("Unable to map place: ","")
            parts = line.split(" in ")
            
            place_part = parts[0]
            full_place_string = ""

        elif line.startswith("Unable to map part of place: "):
            line = line.replace("Unable to map part of place: ","")
            parts = line.split(" in ")
            places = parts[0].split(" from ")
            
            place_part = places[0]
            full_place_string = places[1].strip()[1:-1]
                        

        print(line)
        place_part = place_part.strip()[1:-1]
        place_breakdown = line.split(" | ")[1]
        place_breakdown = place_breakdown.replace("\n", "")
        place_breakdown = place_breakdown[1:-1]
        
        file_id = parts[1].strip().split(" ")[0]
        file_url = clean_file_url(file_id)
        
        # Append the extracted data as a row in the CSV rows list
        row = [place_part, full_place_string, file_url, place_breakdown]
        print(row)
        csv_rows.append([place_part, full_place_string, file_url, place_breakdown])
        

# Write the CSV rows to the output CSV file
with open(csv_file_path, 'w', newline='') as csv_file:
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(csv_headers)
    csv_writer.writerows(csv_rows)
