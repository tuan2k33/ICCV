import os
import json
import cv2
import copy
import numpy as np


# --- CONFIGURATION ---
INPUT_IMAGES = "/ssd1/tuannw/batch4/im"
INPUT_LABELS = "/ssd1/tuannw/batch4/coco_labels/merged4.json"

OUTPUT_IMAGES = "/ssd1/tuannw/batch4/masked_images"
OUTPUT_LABELS = "/ssd1/tuannw/batch4/coco_labels/masked.json"

os.makedirs(OUTPUT_IMAGES, exist_ok=True)

REMOVE_CATEGORY_NAME = "product package"


def load_coco_data(json_path):
    """Load COCO JSON data and build mapping dicts."""
    with open(json_path, "r") as f:
        coco_data = json.load(f)

    image_id_to_info = {img["id"]: img for img in coco_data["images"]}
    category_id_to_name = {cat["id"]: cat["name"] for cat in coco_data["categories"]}
    return coco_data, image_id_to_info, category_id_to_name


def find_remove_category_id(category_id_to_name):
    """Find the ID of the category to remove."""
    for cat_id, name in category_id_to_name.items():
        if name.lower() == REMOVE_CATEGORY_NAME.lower():
            return cat_id
    print(f"Category '{REMOVE_CATEGORY_NAME}' not found.")
    return None


def group_annotations_by_image(coco_data):
    """Group annotations by image ID."""
    anns_per_image = {}
    for ann in coco_data["annotations"]:
        img_id = ann["image_id"]
        anns_per_image.setdefault(img_id, []).append(ann)
    return anns_per_image


def update_categories(coco_data, remove_cat_id):
    """Remove the specified category and reassign new IDs."""
    old_categories = coco_data["categories"]
    new_categories = [cat for cat in old_categories if cat["id"] != remove_cat_id]

    old_to_new_cat_id = {}
    for cat in new_categories:
        old_id = cat["id"]
        new_id = old_id - 1 if old_id > remove_cat_id else old_id
        old_to_new_cat_id[old_id] = new_id
        cat["id"] = new_id

    return new_categories, old_to_new_cat_id


def process_single_image(
    img_id,
    image_id_to_info,
    anns_per_image,
    remove_cat_id,
    old_to_new_cat_id,
    next_image_id,
    next_ann_id,
):
    """Process one image: crop, mask, save, and update annotations."""
    img_info = image_id_to_info[img_id]
    img_path = os.path.join(INPUT_IMAGES, img_info["file_name"])
    image = cv2.imread(img_path)
    if image is None:
        print(f"Error reading image: {img_path}")
        return None, [], [], next_image_id, next_ann_id

    h_img, w_img = image.shape[:2]
    anns = anns_per_image[img_id]

    # Find all boxes of the target category
    target_anns = [ann for ann in anns if ann["category_id"] == remove_cat_id]
    if not target_anns:
        return None, [], [], next_image_id, next_ann_id

    # Determine crop region
    xs, ys = [], []
    for ann in target_anns:
        x, y, w, h = ann["bbox"]
        xs.extend([x, x + w])
        ys.extend([y, y + h])
        if "segmentation" in ann and isinstance(ann["segmentation"], list):
            for seg in ann["segmentation"]:
                xs.extend(seg[::2])
                ys.extend(seg[1::2])

    crop_x1 = max(0, int(min(xs)))
    crop_y1 = max(0, int(min(ys)))
    crop_x2 = min(w_img, int(max(xs)))
    crop_y2 = min(h_img, int(max(ys)))
    crop_w = crop_x2 - crop_x1
    crop_h = crop_y2 - crop_y1

    # Crop and mask
    cropped = image[crop_y1:crop_y2, crop_x1:crop_x2]
    mask = np.zeros((crop_h, crop_w), dtype=np.uint8)

    for ann in target_anns:
        if "segmentation" in ann and isinstance(ann["segmentation"], list):
            for seg in ann["segmentation"]:
                pts = np.array([[x - crop_x1, y - crop_y1] for x, y in zip(seg[::2], seg[1::2])], np.int32)
                cv2.fillPoly(mask, [pts], 255)
        else:
            x, y, w, h = ann["bbox"]
            cv2.rectangle(mask, (int(x - crop_x1), int(y - crop_y1)),
                          (int(x + w - crop_x1), int(y + h - crop_y1)), 255, -1)

    white_bg = np.ones_like(cropped, dtype=np.uint8) * 255
    masked_image = np.where(mask[:, :, None] == 255, cropped, white_bg)

    # Save masked image
    new_filename = f"{os.path.splitext(img_info['file_name'])[0]}.jpg"
    out_path = os.path.join(OUTPUT_IMAGES, new_filename)
    cv2.imwrite(out_path, masked_image)

    # Create new image info
    new_img = {
        "id": next_image_id,
        "file_name": new_filename,
        "width": crop_w,
        "height": crop_h
    }

    # Process remaining annotations
    new_anns = []
    for ann in anns:
        if ann["category_id"] == remove_cat_id:
            continue

        new_ann = copy.deepcopy(ann)
        new_ann["id"] = next_ann_id
        new_ann["image_id"] = next_image_id
        new_ann["category_id"] = old_to_new_cat_id[ann["category_id"]]

        x, y, w, h = ann["bbox"]
        new_ann["bbox"] = [x - crop_x1, y - crop_y1, w, h]

        if "segmentation" in new_ann and isinstance(new_ann["segmentation"], list):
            new_segmentation = []
            for seg in new_ann["segmentation"]:
                new_seg = [coord - crop_x1 if i % 2 == 0 else coord - crop_y1 for i, coord in enumerate(seg)]
                new_segmentation.append(new_seg)
            new_ann["segmentation"] = new_segmentation

        new_anns.append(new_ann)
        next_ann_id += 1

    next_image_id += 1
    return new_img, new_anns, masked_image, next_image_id, next_ann_id


def main():
    """Main entry point."""
    coco_data, image_id_to_info, category_id_to_name = load_coco_data(INPUT_LABELS)
    remove_cat_id = find_remove_category_id(category_id_to_name)

    if remove_cat_id is None:
        return

    anns_per_image = group_annotations_by_image(coco_data)
    new_categories, old_to_new_cat_id = update_categories(coco_data, remove_cat_id)

    new_images = []
    new_annotations = []

    next_image_id = 1
    next_ann_id = 1

    for img_id in sorted(anns_per_image.keys()):
        print(f"Processing image ID: {img_id}")
        new_img, new_anns, _, next_image_id, next_ann_id = process_single_image(
            img_id=img_id,
            image_id_to_info=image_id_to_info,
            anns_per_image=anns_per_image,
            remove_cat_id=remove_cat_id,
            old_to_new_cat_id=old_to_new_cat_id,
            next_image_id=next_image_id,
            next_ann_id=next_ann_id,
        )

        if new_img:
            new_images.append(new_img)
            new_annotations.extend(new_anns)
        else:
            print(f"{img_id} Nothing to do.")

    final_coco = {
        "images": new_images,
        "annotations": new_annotations,
        "categories": new_categories
    }

    with open(OUTPUT_LABELS, "w") as f:
        json.dump(final_coco, f, indent=2)

    print(f"Output images: {OUTPUT_IMAGES}")
    print(f"Output labels: {OUTPUT_LABELS}")


if __name__ == "__main__":
    main()