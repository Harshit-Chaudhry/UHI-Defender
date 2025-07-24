import requests
import os
import yaml
from PIL import Image
import io

CONFIG_FILE_PATH = "config.yaml"
COORDINATES_FILE_PATH = "coordinates.yaml"

FOV = 60
PITCH = 0
SIZE = "600x400"


def load_config():
    """Load API key from config.yaml"""
    try:
        with open(CONFIG_FILE_PATH, 'r') as file:
            config = yaml.safe_load(file)
            return config.get("api_key")
    except Exception as e:
        print(f"Error loading config: {e}")
        return None


def load_coordinates():
    """Load all Aim entries from coordinates.yaml"""
    try:
        with open(COORDINATES_FILE_PATH, 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        print(f"Error loading coordinates: {e}")
        return {}


def get_street_view_image(location_str, heading, api_key, output_dir, filename):
    """Download a single Street View image"""
    url = (
        f"https://maps.googleapis.com/maps/api/streetview?size={SIZE}"
        f"&location={location_str}&fov={FOV}&heading={heading}&pitch={PITCH}&key={api_key}"
    )

    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        image = Image.open(io.BytesIO(response.content))
        image_path = os.path.join(output_dir, filename)
        image.save(image_path)
        print(f"Saved: {image_path}")
        return image_path
    except Exception as e:
        print(f"Error downloading image: {e}")
        return None


def download_street_view_set(aim_title, lat, lng, api_key):
    """Download 6 Street View images for a given location"""
    output_dir = os.path.join("data", aim_title.replace(":", "").replace(",", "").replace(" ", "_"))
    os.makedirs(output_dir, exist_ok=True)

    location = f"{lat},{lng}"
    for i in range(6):
        heading = i * FOV
        filename = f"street_view_{i}.jpg"
        get_street_view_image(location, heading, api_key, output_dir, filename)


def main():
    api_key = load_config()
    if not api_key:
        print("API key not found. Exiting.")
        return

    coordinates_data = load_coordinates()
    if not coordinates_data:
        print("No coordinate data found. Exiting.")
        return

    for aim_title, aim_data in coordinates_data.items():
        lat = aim_data.get('latitude')
        lng = aim_data.get('longitude')

        if lat is None or lng is None:
            print(f"Skipping {aim_title}: missing lat/lng")
            continue

        try:
            lat = float(lat)
            lng = float(lng)
        except ValueError:
            print(f"Skipping {aim_title}: invalid lat/lng format")
            continue

        print(f"Downloading images for: {aim_title}")
        download_street_view_set(aim_title, lat, lng, api_key)


if __name__ == "__main__":
    main()
