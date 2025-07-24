import requests
import yaml
import os

CONFIG_FILE_PATH = "config.yaml"
COORDINATES_FILE_PATH = "coordinates.yaml"

# Load API key from config.yaml
try:
    with open(CONFIG_FILE_PATH, 'r') as config_file:
        config = yaml.safe_load(config_file)
        api_key = config.get('api_key')
except FileNotFoundError:
    print(f"Error: Configuration file '{CONFIG_FILE_PATH}' not found.")
    exit()

if not api_key:
    print("Error: API key not found in configuration file.")
    exit()


def get_coordinates(address, api_key):
    """Fetch coordinates using Google Maps Geocoding API."""
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={api_key}"
    response = requests.get(url)
    data = response.json()

    if data["status"] == "OK":
        lat = data["results"][0]["geometry"]["location"]["lat"]
        lng = data["results"][0]["geometry"]["location"]["lng"]
        return lat, lng
    else:
        print(f"Error: {data['status']}")
        return None, None


def extract_street_name(address):
    """Get the first part of the address as the street name."""
    return address.split(",")[0].strip()


# Ask user if they want to enter an address
choice = input("Do you want to enter an address? (yes/no): ").strip().lower()

if choice == 'yes':
    address = input("Enter address (e.g., 'Ouseburn Road, Newcastle upon Tyne, UK'): ").strip()
    lat, lng = get_coordinates(address, api_key)
elif choice == 'no':
    try:
        lat = float(input("Enter latitude: ").strip())
        lng = float(input("Enter longitude: ").strip())
        address = f"Coordinates entered manually ({lat}, {lng})"
    except ValueError:
        print("Invalid input. Latitude and longitude must be numbers.")
        exit()
else:
    print("Invalid choice. Please enter 'yes' or 'no'.")
    exit()

if lat and lng:
    print(f"Latitude: {lat}, Longitude: {lng}")

    # Load existing coordinates
    if os.path.exists(COORDINATES_FILE_PATH):
        with open(COORDINATES_FILE_PATH, 'r') as file:
            try:
                coordinates_data = yaml.safe_load(file) or {}
            except yaml.YAMLError as e:
                print(f"Error reading YAML: {e}")
                coordinates_data = {}
    else:
        coordinates_data = {}

    # Generate key
    if choice == 'yes':
        street_name = extract_street_name(address)
        existing_aims = [key for key in coordinates_data if key.lower().startswith("aim ")]
        next_number = len(existing_aims) + 1
        aim_key = f"Aim {next_number} {street_name}"
    else:
        aim_key = f"AIM_{lat}_{lng}"

    # Save coordinates
    coordinates_data[aim_key] = {
        'address': address,
        'latitude': lat,
        'longitude': lng
    }

    try:
        with open(COORDINATES_FILE_PATH, 'w') as coordinates_file:
            yaml.dump(coordinates_data, coordinates_file, sort_keys=False)
        print(f"Coordinates saved to '{COORDINATES_FILE_PATH}' as '{aim_key}'")
    except Exception as e:
        print(f"Error saving coordinates: {e}")
else:
    print("Could not retrieve coordinates.")
