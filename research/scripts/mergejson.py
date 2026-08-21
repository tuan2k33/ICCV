import json


def merge_coco_json(json1_path, json2_path, output_path):
    with open(json1_path, 'r') as f1, open(json2_path, 'r') as f2:
        data1 = json.load(f1)
        data2 = json.load(f2)

    # Tạo ID mới để tránh trùng lặp
    max_image_id = max([img["id"] for img in data1["images"]], default=0)
    max_annot_id = max([ann["id"] for ann in data1["annotations"]], default=0)

    # Offset image_id và annotation_id trong file2
    image_id_mapping = {}
    for img in data2["images"]:
        old_id = img["id"]
        max_image_id += 1
        img["id"] = max_image_id
        image_id_mapping[old_id] = max_image_id
        data1["images"].append(img)

    for ann in data2["annotations"]:
        max_annot_id += 1
        ann["id"] = max_annot_id
        ann["image_id"] = image_id_mapping[ann["image_id"]]
        data1["annotations"].append(ann)

    # Hợp nhất categories nếu cần (giả sử 2 file có cùng categories)
    # Nếu không giống nhau, cần thêm xử lý map lại category_id

    with open(output_path, 'w') as out_file:
        json.dump(data1, out_file, indent=2)

    print(f"Merged successfully to {output_path}")

# --------- DÙNG ---------
merge_coco_json(
    json1_path='/ssd1/tuannw/batch4/coco_labels/merged3.json',
    json2_path='/ssd1/tuannw/batch4/coco_labels/instances_default.json',
    output_path='/ssd1/tuannw/batch4/coco_labels/merged4.json'
)
