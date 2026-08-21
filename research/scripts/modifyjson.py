import json
import os
import re

# === CẤU HÌNH ===
input_json_path = "/ssd1/tuannw/missing_case.json"  # Đường dẫn file A.json
output_json_path = "/ssd1/tuannw/missing_count.json"  # Đường dẫn file B.json muốn ghi ra
folder_path = "/ssd1/tuannw/infer_result/"  # Đường dẫn gốc của bạn

def convert_a_to_b(input_path, output_path, base_folder):
    with open(input_path, "r") as f:
        data_a = json.load(f)

    result = {}

    for full_path, info in data_a.items():
        # 1. Extract ngày trong [ ]
        match_date = re.search(r"\[(.*?)\]", full_path)
        if not match_date:
            continue
        date_part = match_date.group(1)  # ví dụ: "28-05-25"

        # 2. Extract tên ảnh cuối (ví dụ AU - 020 - 1_.png)
        filename = os.path.basename(full_path)

        # 3. Lấy 8 ký tự đầu tên ảnh: "AU - 020"
        folder_name = filename[:8]

        # 4. Tạo path đầu ra
        final_path = os.path.join(base_folder, date_part, folder_name)

        # 5. Ghi vào kết quả
        result[final_path] = {
            "missing": info.get("missing", False),
            "num_miss": info.get("nums_miss", 0)
        }

    # === SORT THE RESULT BY PATH (ALPHABETICALLY) ===
    sorted_result = dict(sorted(result.items(), key=lambda item: item[0]))

    # Ghi ra file json kết quả (có sort key)
    with open(output_path, "w") as f:
        json.dump(sorted_result, f, indent=4)

    print(f"✅ Đã tạo file: {output_path} với {len(sorted_result)} mục (đã sắp xếp theo path)")

# === GỌI HÀM ===
convert_a_to_b(input_json_path, output_json_path, folder_path)
