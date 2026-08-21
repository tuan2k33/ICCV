import os
import random
import shutil

# Cấu hình
IMAGE_DIR = "/ssd1/tuannw/batch4/masked_images"  # Thư mục chứa ảnh
LABEL_DIR = "/ssd1/tuannw/batch4/yolo_labels"  # Thư mục chứa file label
OUTPUT_DIR = "/ssd1/tuannw/batch4/data"  # Thư mục sẽ chứa train/val/test

SPLITS = {
    # "train": 0.7,
    # "val": 0.2,
    # "test": 0.1
    "train": 0.8,
    "val": 0.2
}

# Lấy danh sách tất cả file label
label_files = [f for f in os.listdir(LABEL_DIR) if f.endswith(".txt")]
random.shuffle(label_files)  # Trộn ngẫu nhiên

# Tính số lượng mỗi tập
n_total = len(label_files)
n_train = int(n_total * SPLITS["train"])
n_val = int(n_total * SPLITS["val"])
n_test = n_total - n_train - n_val

split_files = {
    "train": label_files[:n_train],
    "val": label_files[n_train:n_train+n_val],
    "test": label_files[n_train+n_val:]
}

# Hàm copy file
def copy_file(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.exists(src):
        shutil.copy2(src, dst)

# Tạo thư mục đích và copy files
for split, files in split_files.items():
    for label_file in files:
        # File nhãn
        src_label = os.path.join(LABEL_DIR, label_file)
        dst_label = os.path.join(OUTPUT_DIR, "labels", split, label_file)

        # File ảnh (same name, khác đuôi)
        base_name = os.path.splitext(label_file)[0]
        img_found = False
        for ext in [".jpg", ".png", ".jpeg", ".bmp"]:
            src_img = os.path.join(IMAGE_DIR, base_name + ext)
            if os.path.exists(src_img):
                dst_img = os.path.join(OUTPUT_DIR, "images", split, base_name + ext)
                copy_file(src_img, dst_img)
                img_found = True
                break
        if not img_found:
            print(f"Cannot found image: {label_file}")

        # Copy label
        copy_file(src_label, dst_label)

print("Splitted.")
# cấu trúc file sau khi split
# data/
# ├── config.yaml
# ├── images/
# │   ├── train/
# │   ├── val/
# │   └── test/
# └── labels/
#     ├── train/
#     ├── val/
#     └── test/
