import onnxruntime as ort
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
import os

model_path = 'models/cityscapes_fan_tiny_hybrid_224.onnx'
session = ort.InferenceSession(model_path)

def preprocess_image(image_path):
    img = Image.open(image_path).convert("RGB")
    img = img.resize((224, 224))
    img = np.array(img).astype(np.float32)
    img = img / 255.0
    img = np.transpose(img, (2, 0, 1))
    img = np.expand_dims(img, axis=0)
    return img

def run_inference(session, img):
    input_name = session.get_inputs()[0].name
    output_name = session.get_outputs()[0].name
    result = session.run([output_name], {input_name: img})
    return result[0]

def overlay_tree_segmentation(original_image, mask):
    mask = mask.squeeze()
    tree_class_id = 8
    tree_mask = np.where(mask == tree_class_id, 1, 0)
    tree_mask = Image.fromarray(tree_mask.astype(np.uint8) * 255)
    tree_mask = tree_mask.resize(original_image.size, Image.NEAREST)
    alpha = tree_mask.convert("L").point(lambda p: p * 0.5)
    tree_rgb = Image.new("RGB", original_image.size, (144, 238, 144))
    tree_rgb.putalpha(alpha)
    combined = Image.alpha_composite(original_image.convert("RGBA"), tree_rgb)
    return combined

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
        panorama_path = os.path.join(output_dir, "segmented_panorama.jpg")
        panorama.save(panorama_path)
        print(f"Panorama saved to: {panorama_path}")
    except Exception as e:
        print(f"Error creating panorama: {e}")

input_directory = 'data\coordinate_54.975056,-1.591944_images'
output_directory = 'segmented_trees'
os.makedirs(output_directory, exist_ok=True)

image_paths = []

for filename in os.listdir(input_directory):
    if filename.endswith('.jpg') or filename.endswith('.png'):
        image_path = os.path.join(input_directory, filename)
        original_image = Image.open(image_path).convert("RGB")
        preprocessed_image = preprocess_image(image_path)
        mask = run_inference(session, preprocessed_image)
        result_image = overlay_tree_segmentation(original_image, mask)
        output_path = os.path.join(output_directory, filename.split('.')[0] + '.png')
        result_image.save(output_path)
        image_paths.append(output_path)

create_panorama(image_paths, output_directory)

print("Segmentation completed and saved in the 'segmented_trees' directory.")
