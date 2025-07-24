import requests
import os
from PIL import Image, ImageDraw
import yaml
from ultralytics import YOLO
import io

CONFIG_FILE_PATH = "config.yaml"
COORDINATES_FILE_PATH = "coordinates.yaml"

FOV = 60
PITCH = 0
SIZE = "600x400"

def get_coordinates(address, api_key):
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={api_key}"
    response = requests.get(url)
    data = response.json()

    if data["status"] == "OK":
        latitude = data["results"][0]["geometry"]["location"]["lat"]
        longitude = data["results"][0]["geometry"]["location"]["lng"]
        return latitude, longitude
    else:
        print(f"Error: {data['status']}")
        return None, None

def get_coordinates_from_yaml(yaml_file_path="coordinates.yaml"):
    try:
        with open(yaml_file_path, 'r') as file:
            coordinates_data = yaml.safe_load(file)
    except FileNotFoundError:
        print(f"Error: YAML file '{yaml_file_path}' not found.")
        return None, None
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file '{yaml_file_path}': {e}")
        return None, None

    if coordinates_data and 'Aim 1' in coordinates_data:
        aim_1_data = coordinates_data['Aim 1']
        latitude_str = aim_1_data.get('latitude')
        longitude_str = aim_1_data.get('longitude')

        try:
            latitude = float(latitude_str) if latitude_str is not None else None
            longitude = float(longitude_str) if longitude_str is not None else None
            return latitude, longitude
        except (ValueError, TypeError):
            print(f"Error: Invalid latitude or longitude values in '{yaml_file_path}'.")
            return None, None
    else:
        print(f"Error: 'Aim 1' section or coordinate data not found in '{yaml_file_path}'.")
        return None, None

def get_street_view_image(location_str, heading, api_key, output_dir, filename):
    url = f"https://maps.googleapis.com/maps/api/streetview?size={SIZE}&location={location_str}&fov={FOV}&heading={heading}&pitch={PITCH}&key={api_key}"

    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        image = Image.open(io.BytesIO(response.content))
        image_path = os.path.join(output_dir, filename)
        image.save(image_path)
        print(f"Image saved to: {image_path}")
        return image_path

    except requests.exceptions.RequestException as e:
        print(f"Error downloading image: {e}")
        return None
    except Exception as e:
        print(f"Error processing image: {e}")

def create_panorama(image_paths, output_dir):
    if not image_paths:
        return

    try:
        images = [Image.open(path) for path in image_paths if path]

        height = images[0].height
        widths = [img.width for img in images]
        total_width = sum(widths)

        panorama = Image.new("RGB", (total_width, height))

        x_offset = 0
        for img in images:
            panorama.paste(img, (x_offset, 0))
            x_offset += img.width

        panorama_path = os.path.join(output_dir, "panorama.jpg")
        panorama.save(panorama_path)
        print(f"Panorama saved to: {panorama_path}")

    except Exception as e:
        print(f"Error creating panorama: {e}")

def run_tree_detection_yolo_class(image_path, model_path, output_dir="detected_trees_output_yolo_class", confidence_threshold=0.25):
    """Detects trees in an image using the YOLO class, saves output image and detection coordinates to YAML."""
    try:
        
        model = YOLO(model_path)

        
        results = model.predict(
            source=image_path,
            conf=confidence_threshold,
            save=False,
            save_txt=False,
            save_conf=True,
        )[0]

        tree_detections_data = [] 

        
        if results:
            boxes = results.boxes
            names = model.names

            detected_image = Image.open(image_path).convert("RGB")
            draw = ImageDraw.Draw(detected_image)

            tree_detected_count = 0

            if boxes:
                xyxy = boxes.xyxy.tolist()
                confidences = boxes.conf.tolist()
                class_ids = boxes.cls.int().tolist()

                for i in range(len(xyxy)):
                    x1, y1, x2, y2 = map(int, xyxy[i])
                    confidence = confidences[i]
                    class_id = class_ids[i]
                    class_name = names[class_id]

                    if class_name == 'tree':
                        tree_detected_count += 1
                        label = f"{class_name}Tree_{confidence:.2f}"
                        draw.rectangle([(x1, y1), (x2, y2)], outline="green", width=2)
                        draw.text((x1, y2 + 5), label, fill="blue")

                        
                        tree_data = {
                            "class_name": class_name,
                            "confidence": float(confidence), 
                            "xh": int(x1), 
                            "yh": int(y1),
                            "xw": int(x2),
                            "yw": int(y2),
                        }
                        tree_detections_data.append(tree_data)
                        print(f"  Detected Tree Coordinates (xh, yh, xw, yw): x1={x1}, y1={y1}, x2={x2}, y2={y2}")


            if tree_detected_count > 0:
                print(f"Detected {tree_detected_count} trees in {image_path}")
            else:
                print(f"No trees detected in {image_path}")

            output_path = os.path.join(output_dir, os.path.basename(image_path))
            os.makedirs(output_dir, exist_ok=True)
            detected_image.save(output_path)
            print(f"Image with tree detections saved to: {output_path}")

            
            if tree_detections_data: 
                yaml_filename = os.path.splitext(os.path.basename(image_path))[0] + "_tree_detections.yaml"
                yaml_filepath = os.path.join(output_dir, yaml_filename)
                with open(yaml_filepath, 'w') as yaml_file:
                    yaml.dump(tree_detections_data, yaml_file, indent=2) 
                print(f"Tree detection coordinates saved to YAML: {yaml_filepath}")


    except Exception as e:
        print(f"Error during tree detection: {e}")

if __name__ == "__main__":
    try:
        with open(CONFIG_FILE_PATH, 'r') as config_file:
            config = yaml.safe_load(config_file)
            api_key = config.get('api_key')
    except FileNotFoundError:
        print(f"Error: Configuration file '{CONFIG_FILE_PATH}' not found.")
        api_key = None
        exit()

    if not api_key:
        print("Error: API key not found in configuration file.")
        exit()

    address = input("Enter address like (Ouseburn Road,Newcastle upon Tyne,UK): ")
    lat, lng = get_coordinates(address, api_key)

    if lat and lng:
        print(f"Latitude: {lat}, Longitude: {lng}")

        coordinates_data = {
            'Aim 1': {
                'address': address,
                'latitude': lat,
                'longitude': lng
            }
        }

        try:
            with open(COORDINATES_FILE_PATH, 'w') as coordinates_file:
                yaml.dump(coordinates_data, coordinates_file)
            print(f"Coordinates saved to '{COORDINATES_FILE_PATH}'")

        except Exception as e:
            print(f"Error saving coordinates to '{COORDINATES_FILE_PATH}': {e}")

    else:
        print("Could not retrieve coordinates for the given address.")
        exit()

    use_specific_coordinates = input("Do you want to enter specific coordinates instead of using the given location (yes/no): ").lower()

    if use_specific_coordinates == 'yes' or use_specific_coordinates == 'y':
        while True:
            try:
                lat_input = input("Enter Latitude: ")
                lat = float(lat_input)
                lng_input = input("Enter Longitude: ")
                lng = float(lng_input)
                break
            except ValueError:
                print("Invalid input. Please enter numeric values for latitude and longitude.")

    LOCATION = f"{lat},{lng}"
    OUTPUT_DIR = os.path.join("data", f"coordinate_{LOCATION}_images")

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    image_paths = []
    for i in range(6):
        heading = i * FOV
        filename = f"street_view_{i}.jpg"
        image_path = get_street_view_image(LOCATION, heading, api_key, OUTPUT_DIR, filename)
        image_paths.append(image_path)

    detected_output_dir = "detected_trees_output_yolo_class"
    model_path = "models/tree_detection_street_best.pt"

    for image_path in image_paths:
        run_tree_detection_yolo_class(image_path, model_path, output_dir=detected_output_dir)

    create_panorama(image_paths, detected_output_dir)
