import re
import sys

# Regular expression pattern to match POINT values
pattern = r'POINT\(([-\d.]+) ([-\d.]+)\)'

# Function to swap the values in POINT notation
def swap_point_values(match):
    return f'POINT({match.group(2)} {match.group(1)})'


# Check if the input file argument is provided
if len(sys.argv) < 2:
    print("Please provide the path to the input file as an argument.")
    sys.exit(1)

# Read input text from the file
file_path = sys.argv[1]
with open(file_path, 'r') as file:
    input_text = file.read()

# Perform the swap using regex substitution
output_text = re.sub(pattern, swap_point_values, input_text)

# Print the updated text
print(output_text)
