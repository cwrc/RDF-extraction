import requests
import csv
import os

# Define the API base URL
API_BASE_URL = "https://geonames.lincsproject.ca/geocode?id="

# Input and output file paths
INPUT_FILE = "data/geonames.txt"
OUTPUT_FILE = "data/geonames_extracted.csv"

def fetch_geonames_data(geonames_id):
    """Fetch data from the GeoNames API for a given ID."""
    url = f"{API_BASE_URL}{geonames_id}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch data for ID {geonames_id}: {response.status_code}")
        return None

def extract_properties(geonames_id, api_response):
    """Extract coordinates and relevant properties from the API response."""
    if not api_response or not api_response.get("success"):
        return None

    if len(api_response.get("data", [])) == 0:
        print("No data found in the API response for ID:", geonames_id)
        return None


    data = api_response.get("data", [])[0]
    
    
    
    geometry = data.get("geometry", {})
    properties = data.get("properties", {})

    return {
        "uri": f"https://sws.geonames.org/{properties.get('id')}",
        "id": properties.get("id"),
        "name": properties.get("name"),
        "latitude": geometry.get("coordinates", [None, None])[1],
        "longitude": geometry.get("coordinates", [None, None])[0],
        "admin1": properties.get("admin1"),
        "admin2": properties.get("admin2"),
        "elevation": properties.get("elevation"),
        "featureClass": properties.get("featureClass"),
        "featureCode": properties.get("featureCode"),
        "population": properties.get("population"),
        "timezone": properties.get("timezone"),
        "iso2": properties.get("iso2"),
        "moddate": properties.get("moddate")
    }

def process_geonames_file(input_file, output_file):
    """Process the GeoNames file and extract data for each ID."""
    if not os.path.exists(input_file):
        print(f"Input file {input_file} does not exist.")
        return

    with open(input_file, "r") as infile, open(output_file, "w", newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=[
            "uri","id", "name", "latitude", "longitude", "admin1", "admin2", "elevation",
            "featureClass", "featureCode", "population", "timezone", "iso2", "moddate"
        ])
        writer.writeheader()

        for line in infile:
            geonames_id = line.strip().split("/")[-1]  # Extract the ID from the URL
            # print(f"Processing ID: {geonames_id}...")
            api_response = fetch_geonames_data(geonames_id)
            extracted_data = extract_properties(geonames_id,api_response)

            if extracted_data:
                writer.writerow(extracted_data)

if __name__ == "__main__":
    process_geonames_file(INPUT_FILE, OUTPUT_FILE)
