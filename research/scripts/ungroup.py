import os
import shutil

# Đường dẫn đến folder cha chứa nhiều folder con
INPUT_PATH = '/ssd1/tuannw/24-05-25'

# Thư mục đích để lưu tất cả ảnh
OUTPUT_FOLDER = '/ssd1/tuannw/24-05-25'
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Duyệt qua tất cả các folder con và cháu
for root, dirs, files in os.walk(INPUT_PATH):
    for file in files:
        # Chỉ lấy các file ảnh nếu cần thiết
        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp')):
            src_path = os.path.join(root, file)
            dst_path = os.path.join(OUTPUT_FOLDER, file)

            # Tránh trùng tên bằng cách đổi tên nếu đã tồn tại
            counter = 1
            while os.path.exists(dst_path):
                filename, ext = os.path.splitext(file)
                dst_path = os.path.join(OUTPUT_FOLDER, f"{filename}_{counter}{ext}")
                counter += 1

            print(f"Moved: {src_path} -> {dst_path}")
            shutil.copy(src_path, dst_path)  # hoặc dùng shutil.copy() nếu không xóa file gốc