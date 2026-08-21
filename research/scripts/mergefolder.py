import os
import shutil
import sys
folder1= '/ssd1/tuannw/infer_result/24-05-251234/'
folder2= '/ssd1/tuannw/infer_result/24-05-255/'
dst_folder = '/ssd1/tuannw/infer_result/24-05-25/'
def merge_folders(src1, src2, dst):
    if not os.path.isdir(src1) or not os.path.isdir(src2):
        print("Both source folders must exist.")
        return

    os.makedirs(dst, exist_ok=True)

    for src in [src1, src2]:
        for root, dirs, files in os.walk(src):
            rel_path = os.path.relpath(root, src)
            dst_dir = os.path.join(dst, rel_path)
            os.makedirs(dst_dir, exist_ok=True)
            for file in files:
                src_file = os.path.join(root, file)
                dst_file = os.path.join(dst_dir, file)
                if not os.path.exists(dst_file):
                    shutil.copy2(src_file, dst_file)
                else:
                    # If file exists, rename and copy
                    base, ext = os.path.splitext(file)
                    i = 1
                    while True:
                        new_name = f"{base}_copy{i}{ext}"
                        new_dst_file = os.path.join(dst_dir, new_name)
                        if not os.path.exists(new_dst_file):
                            shutil.copy2(src_file, new_dst_file)
                            break
                        i += 1

if __name__ == "__main__":
    merge_folders(folder1, folder2, dst_folder)
