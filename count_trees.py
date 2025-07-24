from ultralytics import YOLO
import os
from PIL import Image, ImageDraw
import numpy as np

def run_tree_detection_yolo_class(image_path, model_path, output_dir, confidence_threshold=0.20):
    """Detects trees in an image using the YOLO class and saves the output."""
    try:
        model = YOLO(model_path)
        results = model.predict(
            source=image_path,
            conf=confidence_threshold,
            save=False,
            save_txt=False,
            save_conf=True,
        )[0]

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
                        label = f"{class_name}_{confidence:.2f}"
                        draw.rectangle([(x1, y1), (x2, y2)], outline="green", width=2)
                        text_position = (x1, y2 + 15)
                        draw.text(text_position, label, fill="blue")

            if tree_detected_count > 0:
                print(f"Detected {tree_detected_count} trees in {image_path}")
            else:
                print(f"No trees detected in {image_path}")

            output_path = os.path.join(output_dir, os.path.basename(image_path))
            os.makedirs(output_dir, exist_ok=True)
            detected_image.save(output_path)
            print(f"Image with tree detections saved to: {output_path}")

    except Exception as e:
        print(f"Error during tree detection: {e}")


def process_directory(input_dir, model_path, output_dir, confidence_threshold=0.10):
    """Processes all images in the input directory for tree detection."""
    if not os.path.exists(input_dir):
        print(f"Input directory '{input_dir}' does not exist.")
        return

    os.makedirs(output_dir, exist_ok=True)

    for filename in os.listdir(input_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            image_path = os.path.join(input_dir, filename)
            print(f"Processing image: {image_path}")
            run_tree_detection_yolo_class(image_path, model_path, output_dir, confidence_threshold)


if __name__ == "__main__":
    model_path = "models/count_trees_aerial_best.pt"  # Path to your YOLO model
    input_directory = "data/Satellite_images"  # Directory containing satellite images
    output_directory = "count_trees_opt"  # Directory to save processed images
    confidence_threshold = 0.50  # Confidence threshold for tree detection

    process_directory(input_directory, model_path, output_directory, confidence_threshold)
    print("Tree detection for all images in the directory completed.")