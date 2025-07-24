from ultralytics import YOLO
import os
from PIL import Image, ImageDraw
import yaml

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


def process_images_in_folder(folder_path, model_path, output_dir="detected_trees_output_yolo_class", confidence_threshold=0.25):
    """Processes all images in a folder to detect trees and save the results in a different folder."""
    for filename in os.listdir(folder_path):
        if filename.endswith(".jpg") or filename.endswith(".png"):
            image_path = os.path.join(folder_path, filename)
            run_tree_detection_yolo_class(image_path, model_path, output_dir, confidence_threshold)


if __name__ == "__main__":
    folder_path = "data\coordinate_55.0149809,-1.6224566_images"  # Replace <latitude> and <longitude> with actual values
    model_path = "models/tree_detection_street_best.pt"
    output_directory = "detected_trees_output_yolo_class"

    process_images_in_folder(folder_path, model_path, output_directory)
    print("Tree detection in all images completed.")
