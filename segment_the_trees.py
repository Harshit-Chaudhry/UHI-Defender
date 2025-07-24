import os
import sys
import yaml
from PIL import Image, ImageDraw
import numpy as np
from segment_anything import sam_model_registry, SamPredictor

def segment_trees_with_sam(image_path, yaml_path, sam_model_type="vit_h", sam_checkpoint="sam_vit_h_870864.pth", output_dir="segmented_trees_output_sam"):
    """
    Segments trees in an image using SAM model, guided by bounding boxes from a YAML file.
    """
    try:
        
        try:
            with open(yaml_path, 'r') as yaml_file:
                tree_detections = yaml.safe_load(yaml_file)
                if not tree_detections:
                    print(f"No tree detections found in YAML file: {yaml_path}")
                    return
        except FileNotFoundError:
            print(f"Error: YAML file not found at: {yaml_path}") 
            return
        except yaml.YAMLError as e:
            print(f"Error parsing YAML file: {e}")
            return


        """  Load SAM Model """
        try:
            sam = sam_model_registry[sam_model_type](checkpoint=sam_checkpoint)
            sam.to('cuda' if torch.cuda.is_available() else 'cpu') # getting GPU 
            predictor = SamPredictor(sam)
        except FileNotFoundError:
            print(f"Error: SAM checkpoint file not found at: {sam_checkpoint}") 
            return
        except Exception as sam_load_exception:
            print(f"Error loading SAM model: {sam_load_exception}")
            return


        
        try:
            image_pil = Image.open(image_path).convert("RGB")
            image_np = np.array(image_pil)
            predictor.set_image(image_np)
        except FileNotFoundError:
            print(f"Error: Image file not found at: {image_path}") 
            return
        except Exception as image_load_exception:
            print(f"Error loading image file: {image_load_exception}")
            return


        output_mask_dir = os.path.join(output_dir, "masks")
        output_segmented_image_dir = os.path.join(output_dir, "segmented_images")
        os.makedirs(output_mask_dir, exist_ok=True)
        os.makedirs(output_segmented_image_dir, exist_ok=True)


        segmented_image_pil = image_pil.copy() 

        for i, detection in enumerate(tree_detections):
            xh, yh, xw, yw = detection['xh'], detection['yh'], detection['xw'], detection['yw']
            input_box = np.array([xh, yh, xw, yw]) 

            masks, _, _ = predictor.predict(
                point_coords=None,
                point_labels=None,
                box=input_box,
                multimask_output=False, 
            )
            mask = masks[0] 


            """  Save Segmentation Mask """
            mask_pil = Image.fromarray(mask) 
            mask_filename = os.path.splitext(os.path.basename(image_path))[0] + f"_tree_mask_{i+1}.png"
            mask_filepath = os.path.join(output_mask_dir, mask_filename)
            mask_pil.save(mask_filepath)
            print(f"  Saved tree mask: {mask_filepath}")


            
            mask_overlay_color = (0, 255, 0, 150)  
            segmented_image_draw = ImageDraw.Draw(segmented_image_pil, 'RGBA')

            
            contours = find_contours(mask, level=0.5, fully_connected='high') 
            for n, contour in enumerate(contours):
                for l in range(0, len(contour), 1): 
                    x_PIL, y_PIL = tuple(np.flip(contour[l], axis=0)) 
                    segmented_image_draw.point((x_PIL, y_PIL), fill=mask_overlay_color) 


        
        segmented_image_filename = os.path.splitext(os.path.basename(image_path))[0] + "_segmented.jpg"
        segmented_image_filepath = os.path.join(output_segmented_image_dir, segmented_image_filename)
        segmented_image_pil.save(segmented_image_filepath)
        print(f"Segmented image saved: {segmented_image_filepath}")


    except Exception as e: 
        print(f"An unexpected error occurred during segmentation: {e}")




if __name__ == "__main__":
    import torch 
    from skimage.measure import find_contours 

    image_path = "data/coordinate_54.975056,-1.591944_images/street_view_0.jpg" 
    yaml_path = "detected_trees_output_yolo_class/street_view_0_tree_detections.yaml" 
    sam_checkpoint = "models/sam_vit_h_4b8939.pth" 
    sam_model_type = "vit_h" 
    
    """
    print(f"Debugging: Image path: {image_path}") 
    print(f"Debugging: YAML path: {yaml_path}")  
    print(f"Debugging: SAM checkpoint path: {sam_checkpoint}") """

    segment_trees_with_sam(image_path, yaml_path, sam_checkpoint=sam_checkpoint, sam_model_type=sam_model_type)
    print("Tree segmentation with SAM completed.")