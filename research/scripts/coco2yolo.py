import os
import json


# --- Configuration ---
INPUT_LABELS = "/ssd1/tuannw/batch4/coco_labels/masked.json"
OUTPUT_LABELS = "/ssd1/tuannw/batch4/yolo_labels"

# Map category_id -> YOLO class index
# Sau khi xóa product package chỉ còn top_face và front_face
category_id_map = {
    1: 0,  # top_face
    2: 1   # front_face
}

os.makedirs(OUTPUT_LABELS, exist_ok=True)


def load_coco_data(json_path):
    """Load COCO JSON data from file."""
    with open(json_path, "r") as f:
        return json.load(f)


def build_image_info(coco_data):
    """Build mapping from image_id to (file_name, width, height)."""
    return {
        img["id"]: (img["file_name"], img["width"], img["height"])
        for img in coco_data["images"]
    }


def group_annotations_by_image(coco_data):
    """Group annotations by image ID."""
    anns_per_image = {}
    for ann in coco_data["annotations"]:
        anns_per_image.setdefault(ann["image_id"], []).append(ann)
    return anns_per_image


def convert_bbox(annotation, width, height):
    """Convert bounding box annotation to YOLO format."""
    x, y, w, h = annotation["bbox"]
    x_center = (x + w / 2) / width
    y_center = (y + h / 2) / height
    w_norm = w / width
    h_norm = h / height
    yolo_id = category_id_map.get(annotation["category_id"])
    if yolo_id is None:
        return None
    return f"{yolo_id} {x_center:.6f} {y_center:.6f} {w_norm:.6f} {h_norm:.6f}"


def convert_segmentation(annotation, width, height):
    """Convert segmentation annotation to YOLO polygon format."""
    yolo_id = category_id_map.get(annotation["category_id"])
    if yolo_id is None:
        return None

    seg = []
    if "segmentation" in annotation and isinstance(annotation["segmentation"], list):
        if len(annotation["segmentation"]) > 0:
            seg = annotation["segmentation"][0]  # Take first segmentation polygon

    if not seg:
        # Fallback: use bbox to create rectangle polygon
        x, y, w, h = annotation["bbox"]
        seg = [x, y, x + w, y, x + w, y + h, x, y + h]

    norm_coords = [
        f"{seg[i] / width:.6f}" if i % 2 == 0 else f"{seg[i] / height:.6f}"
        for i in range(len(seg))
    ]
    return f"{yolo_id} " + " ".join(norm_coords)


def process_annotations(image_info, annotations, mode="bbox"):
    """
    Process annotations for one image.
    Returns list of YOLO-formatted strings or None if skipped.
    """
    file_name, width, height = image_info
    lines = []

    for ann in annotations:
        if mode == "bbox":
            line = convert_bbox(ann, width, height)
        elif mode == "seg":
            line = convert_segmentation(ann, width, height)
        else:
            raise ValueError(f"Unknown mode: {mode}")

        if line:
            lines.append(line)

    return lines


def save_yolo_labels(file_name, lines):
    """Save YOLO labels to .txt file."""
    label_file = os.path.splitext(file_name)[0] + ".txt"
    label_path = os.path.join(OUTPUT_LABELS, label_file)

    with open(label_path, "w") as f:
        f.write("\n".join(lines))


def select_mode():
    """Prompt user to choose the conversion mode via console."""
    choice = input("1.bbox | 2.seg : ").strip()

    if choice not in ["1", "2"]:
        print("Exit.")
        exit()

    return "bbox" if choice == "1" else "seg"


def main():
    # Load COCO data
    coco_data = load_coco_data(INPUT_LABELS)

    # Build mappings
    image_id_to_info = build_image_info(coco_data)
    anns_per_image = group_annotations_by_image(coco_data)

    # Prompt user to select mode
    mode = select_mode()
    print(f"Mode: {mode.upper()}")

    # Process each image
    for image_id, annotations in anns_per_image.items():
        image_info = image_id_to_info[image_id]
        lines = process_annotations(image_info, annotations, mode=mode)
        if lines:
            save_yolo_labels(image_info[0], lines)

    print(f"Done: {OUTPUT_LABELS} ({mode})")


if __name__ == "__main__":
    main()