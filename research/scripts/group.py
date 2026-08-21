import os
import shutil
# path
project_root = "/ssd1/tuannw/infer_result/24-05-25"
def group_files_by_prefix(project_root):
    label_dir = os.path.join(project_root, "labels")

    for filename in os.listdir(project_root):
        file_path = os.path.join(project_root, filename)

        if not os.path.isfile(file_path):
            continue

        # Chỉ xử lý ảnh
        if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
            continue

        # Lấy 8 ký tự đầu làm tên folder (VD: 'AZ - 003')
        folder_name = filename[:8]
        dest_folder = os.path.join(project_root, folder_name)
        os.makedirs(dest_folder, exist_ok=True)

        # Di chuyển ảnh
        shutil.move(file_path, os.path.join(dest_folder, filename))
        print(f"Image {filename} moved to {folder_name}/")

        # Tìm label tương ứng
        name_wo_ext = os.path.splitext(filename)[0]
        label_file = name_wo_ext + ".txt"
        label_path = os.path.join(label_dir, label_file)
        if os.path.isfile(label_path):
            shutil.move(label_path, os.path.join(dest_folder, label_file))
            print(f"Label {label_file} moved to {folder_name}/")
        else:
            print(f"Label missing: {filename}")
    os.rmdir(label_dir)


group_files_by_prefix(project_root)
