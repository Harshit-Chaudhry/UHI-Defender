import subprocess
import os
from tree_detection import run_tree_detection_yolo_class  # Import the tree detection function

def run_street_to_coordinate():
    """Runs street_to_coordinate.py script to get coordinates and save to YAML."""
    print("Running street_to_coordinate.py to get coordinates...")
    try:
        subprocess.run(["python", "street_to_coordinate.py"], check=True) # Ensure script is in the same directory or adjust path
        print("street_to_coordinate.py finished successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error running street_to_coordinate.py: {e}")
        exit(1) # Exit main script if street_to_coordinate.py fails

def run_coordinate_to_images():
    """Runs coordinate_to_images.py script to generate panorama images."""
    print("Running coordinate_to_images.py to generate panorama...")
    try:
        subprocess.run(["python", "coordinate_to_images.py"], check=True) # Ensure script is in the same directory or adjust path
        print("coordinate_to_images.py finished successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error running coordinate_to_images.py: {e}")
        exit(1) # Exit main script if coordinate_to_images.py fails

def run_tree_detection():
    """Runs tree detection on the generated panorama images."""
    print("Running tree detection on panorama images...")
    model_path = "models/best.pt"  # Path to your YOLO model
    image_dir = "data/coordinate_54.975056,-1.591944_images" # Assuming images are saved in the 'data' directory
    output_directory = "detected_trees_output_main_integrated" # Output directory for tree detection results

    os.makedirs(output_directory, exist_ok=True) # Create output directory if it doesn't exist

    image_files = [f for f in os.listdir(image_dir) if f.endswith(('.jpg', '.jpeg', '.png'))] # Get image files from data dir

    if not image_files:
        print(f"No images found in '{image_dir}' directory for tree detection.")
        return

    for image_file in image_files:
        image_path = os.path.join(image_dir, image_file)
        print(f"Processing image: {image_path}")
        run_tree_detection_yolo_class(image_path, model_path, output_dir=output_directory) # Run tree detection

    print("Tree detection process finished.")


if __name__ == "__main__":
    print("Starting main script...")
    run_street_to_coordinate() # Run street_to_coordinate.py
    run_coordinate_to_images() # Run coordinate_to_images.py
    run_tree_detection()      # Run tree detection after image generation
    print("Main script finished.")