import os
import json
import cv2
import numpy as np
from collections import defaultdict


# --- Configuration ---
IMAGE_DIR = "/ssd1/tuannw/batch2/masked_images"
LABEL_DIR = "/ssd1/tuannw/batch2/coco_labels/masked.json"
OUTPUT_DIR = "/ssd1/tuannw/batch2/masked_annotated_images"

os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_coco_data(annotation_path):
    """Load COCO JSON data from file."""
    with open(annotation_path, "r") as f:
        return json.load(f)


def build_lookup_dicts(coco_data):
    """Build lookup dictionaries for image info and category names."""
    image_id_to_info = {img["id"]: img for img in coco_data["images"]}
    category_id_to_name = {cat["id"]: cat["name"] for cat in coco_data["categories"]}
    return image_id_to_info, category_id_to_name


def generate_category_colors(category_names):
    """Generate distinct BGR colors for each category using HSV color space."""
    category_name_to_color = {}
    for i, name in enumerate(sorted(set(category_names))):
        hue = int(180 * i / len(category_names))  # Spread out hues
        hsv_color = np.uint8([[[hue, 255, 255]]])
        bgr_color = cv2.cvtColor(hsv_color, cv2.COLOR_HSV2BGR)[0][0]
        category_name_to_color[name] = tuple(int(c) for c in bgr_color)
    return category_name_to_color


def group_annotations_by_image(coco_data):
    """Group annotations by image ID."""
    anns_per_image = defaultdict(list)
    for ann in coco_data["annotations"]:
        anns_per_image[ann["image_id"]].append(ann)
    return anns_per_image


def annotate_image(image_path, image_info, annotations, category_id_to_name, category_name_to_color):
    """Draw annotations on the image and save the result."""
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error reading image: {image_path}")
        return

    for ann in annotations:
        category_name = category_id_to_name.get(ann["category_id"], "unknown")
        color = category_name_to_color.get(category_name, (0, 0, 255))

        segmentations = ann.get("segmentation", [])
        for seg in segmentations:
            pts = np.array(seg, dtype=np.int32).reshape((-1, 1, 2))
            if len(pts) < 2:
                continue
            cv2.polylines(image, [pts], isClosed=True, color=color, thickness=2)

            # Label text near the first point of the polygon
            cv2.putText(
                image,
                category_name,
                tuple(pts[0][0]),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                color,
                2
            )

    # Save output image
    out_path = os.path.join(OUTPUT_DIR, image_info["file_name"])
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    cv2.imwrite(out_path, image)
    print(f"Saved annotated image: {out_path}")


def main():
    """Main function to run the annotation visualization pipeline."""
    # Load data
    coco_data = load_coco_data(LABEL_DIR)

    # Build lookups
    image_id_to_info, category_id_to_name = build_lookup_dicts(coco_data)
    category_names = list(category_id_to_name.values())

    # Generate colors
    category_name_to_color = generate_category_colors(category_names)

    # Group annotations
    anns_per_image = group_annotations_by_image(coco_data)

    # Annotate each image
    for image_id, image_info in image_id_to_info.items():
        print(f"Processing image ID: {image_id}")
        image_path = os.path.join(IMAGE_DIR, image_info["file_name"])
        annotations = anns_per_image[image_id]
        annotate_image(image_path, image_info, annotations, category_id_to_name, category_name_to_color)


if __name__ == "__main__":
    main()