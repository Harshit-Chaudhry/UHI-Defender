import os
import sys
import time
import requests
import yaml  

def download_static_map_image(api_key, location, filename, zoom=18, maptype='satellite', size='600x300', markers_list=None, path=None):
    """Downloads a static map image with optional markers and path."""
    url = "https://maps.googleapis.com/maps/api/staticmap"
    params = {
        'center': location,
        'zoom': zoom,
        'size': size,
        'maptype': maptype,
        'key': api_key  
    }

    if markers_list:
        params['markers'] = markers_list

    if path:
        params['path'] = path

    try:
        response = requests.get(url, params=params, stream=True)
        response.raise_for_status()

        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Static map image downloaded successfully: {filename}")
        return True

    except requests.exceptions.RequestException as e:
        print(f"Error downloading static map image: {e}")
        print("Response Content:", response.text)
        return False
try:
    with open("config.yaml", 'r') as config_yaml_file:
        config = yaml.safe_load(config_yaml_file)
        api_key = config.get('api_key')
        output_dir = config.get('satellite_output_directory')

        if not api_key or not output_dir:
            raise ValueError("API key or output_directory not found in config.yaml")

except FileNotFoundError:
    print("Error: config.yaml file not found. Make sure it exists in the same directory as the script.")
    sys.exit(1)
except yaml.YAMLError as e:
    print(f"Error parsing config.yaml: {e}")
    sys.exit(1)
except ValueError as e:
    print(f"Configuration Error in config.yaml: {e}")
    sys.exit(1)

try:
    with open("coordinates.yaml", 'r') as coordinates_yaml_file:
        coordinates_config = yaml.safe_load(coordinates_yaml_file)

        if not coordinates_config:
            raise ValueError("No data found in coordinates.yaml")

        for aim, details in coordinates_config.items():
            latitude = details.get('latitude')
            longitude = details.get('longitude')

            if not latitude or not longitude:
                print(f"Skipping {aim}: Latitude or longitude not found.")
                continue

            location = f"{latitude},{longitude}"
            filename = os.path.join(output_dir, f"{aim.replace(' ', '_').replace(':', '')}.jpg")

            print(f"Downloading satellite image for {aim}...")
            success = download_static_map_image(
                api_key=api_key,
                location=location,
                filename=filename,
                zoom=19,
                maptype="satellite",
                size='600x600'
            )

            if success:
                print(f"Image for {aim} saved as {filename}")
            else:
                print(f"Failed to download image for {aim}")

except FileNotFoundError:
    print("Error: coordinates.yaml file not found. Make sure it exists in the same directory as the script.")
    sys.exit(1)
except yaml.YAMLError as e:
    print(f"Error parsing coordinates.yaml: {e}")
    sys.exit(1)
except ValueError as e:
    print(f"Configuration Error in coordinates.yaml: {e}")
    sys.exit(1)