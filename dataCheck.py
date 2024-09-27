import xml.etree.ElementTree as ET
import sys
# Path to the local XML file
file_path = "NDFD_Data.xml"

try:
    # Parse the XML file
    tree = ET.parse(file_path)
    root = tree.getroot()
    print("XML file loaded successfully!")
    sys.exit(200)
except ET.ParseError as e:
    print(f"Error parsing XML: {e}")
    sys.exit(400)
except FileNotFoundError:
    print(f"File not found: {file_path}")
    sys.exit(400)
except Exception as e:
    print(f"An error occurred: {e}")
    sys.exit(400)

