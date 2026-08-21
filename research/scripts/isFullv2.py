import os
import numpy as np
import cv2
from shapely.geometry import Polygon
from sklearn.cluster import DBSCAN
from sklearn.linear_model import RANSACRegressor, LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline
# ======================================================
# 2. ĐƯỜNG DẪN & HẰNG SỐ
# ======================================================

ROOT_LABEL_DIR = "/ssd1/tuannw/infer_result/30-05-25"
EXPECTED_FILE_PATH = os.path.join(ROOT_LABEL_DIR, "expected.txt")
LOG_FILE_PATH = os.path.join(ROOT_LABEL_DIR, "result_log3.txt")
FAILED_CASES_FILE_PATH = os.path.join(ROOT_LABEL_DIR, "failed3.txt")
# Threshold cho từng loại mặt
TOP_Y_THRESHOLD = 0.05
FRONT_Y_THRESHOLD = 0.05
BOX_X_THRESHOLD = 0.1
BOX_Y_THRESHOLD = 0.1

# ======================================================
# 3. HÀM TÌM FILE PHÙ HỢP
# ======================================================

def find_file(folder_path):
    """Chọn file tốt nhất trong folder theo thứ tự ưu tiên: 1_(1).txt > 1_(2).txt > ... > 1_.txt"""
    files = os.listdir(folder_path)
    candidates = []

    for file in files:
        full_path = os.path.join(folder_path, file)

        if "1_.txt" in file or "1.txt" in file or "1 _.txt" in file:
            # Ưu tiên thấp nhất
            candidates.append((0, full_path))

        elif "(" in file and ")".join(file.split("(")[1].split(")")[0:-1]) and file.endswith(".txt"):
            try:
                suffix_part = file.split("(")[1]
                index_str = suffix_part.split(")")[0]
                index = int(index_str)
                candidates.append((index, full_path))
            except Exception:
                continue

    if not candidates:
        return None

    candidates.sort(key=lambda x: x[0])
    selected_file = candidates[0][1]
    print(f"[{os.path.basename(folder_path)}] Selected: {os.path.basename(selected_file)}")
    return selected_file



def read_yoloseg(txt_path):
    """
    Đọc file YOLOseg và tính toán center x/y.
    Trả về dict theo class_id với mỗi phần tử là:
        (center_x, center_y, class_id, corners[top_left, top_right, bottom_right, bottom_left])

    Parameters:
        txt_path (str): Đường dẫn tới file .txt annotation theo định dạng YOLO-seg

    Returns:
        boxes_by_class = {
            0: [(cx, cy, 0, [pt1, pt2, pt3, pt4]), ...],
            1: [(cx, cy, 1, [pt1, pt2, pt3, pt4]), ...]
        }
    """
    boxes_by_class = {}
    
   
    with open(txt_path, "r") as f:
        for line in f:
            parts = list(map(float, line.strip().split()))
            class_id = int(parts[0])
            coords = parts[1:]

            x_coords = coords[0::2]
            y_coords = coords[1::2]
            min_x, max_x = min(x_coords), max(x_coords)
            min_y, max_y = min(y_coords), max(y_coords)

            center_x = round((min_x + max_x) / 2, 4)
            center_y = round((min_y + max_y) / 2, 4)
            if class_id == 0:
                y_custom = max_y
            elif class_id == 1:
                y_custom = min_y
            else:
                y_custom = center_y
            y_custom = round(y_custom, 4)
            
            mask = np.array(coords).reshape(-1, 2).astype(np.float32)


            def find_corners(mask_normalized):
                """
                Lấy 4 điểm đặc biệt từ mask đã chuẩn hóa về [0,1]

                Parameters:
                    mask_normalized (np.ndarray): mảng [n_points, 2], tọa độ đã chuẩn hóa về [0,1]
                    
                Returns:
                    list: [top_left, top_right, bottom_right, bottom_left] trong miền [0,1]
                """
                # Chuyển thành numpy array nếu chưa là
                pts = np.array(mask_normalized, dtype=np.float32)

                # Tính tổng và hiệu giữa x và y
                sums = pts[:, 0] + pts[:, 1]   # x + y → tìm top_left và bottom_right
                diffs = pts[:, 0] - pts[:, 1]  # x - y → tìm top_right và bottom_left

                # === Trích 4 điểm cực trị ===
                top_left_idx = np.argmin(sums)      # x+y nhỏ nhất → gần top-left
                bottom_right_idx = np.argmax(sums)  # x+y lớn nhất → gần bottom-right
                top_right_idx = np.argmax(diffs)     # x−y lớn nhất → gần top-right
                bottom_left_idx = np.argmin(diffs)   # x−y nhỏ nhất → gần bottom-left

                # Kiểm tra nếu các điểm trùng nhau
                corner_indices = [top_left_idx, top_right_idx, bottom_right_idx, bottom_left_idx]
                unique_indices = set(corner_indices)

                if len(unique_indices) < 3:
                    print("[WARNING] Có ít hơn 3 điểm khác biệt từ sum/diff")

                # === Trả về thứ tự chuẩn ===
                return [
                    list(pts[top_left_idx]),
                    list(pts[top_right_idx]),
                    list(pts[bottom_right_idx]),
                    list(pts[bottom_left_idx])
                ]
            corners = find_corners(mask)
            # print("Corners:", corners)
            if class_id not in boxes_by_class:
                boxes_by_class[class_id] = []

            boxes_by_class[class_id].append((center_x, y_custom, class_id, corners))
    
    return boxes_by_class


def group_and_sort_boxes(boxes, y_threshold=0.1):
    if not boxes:
        return []

    # Xác định class_id từ hộp đầu tiên
    class_id = boxes[0][2]  # Lấy class_id từ (x, y, class_id, corners)

    # Chọn threshold dựa trên class_id
    if class_id == 0:
        # Sort boxes by y (ascending)
        boxes_sorted = sorted(boxes, key=lambda box: box[1])
        n = len(boxes_sorted)
        used = set()
        rows = []
        idxs = list(range(n - 1, -1, -1))  # from last to first
        threshold = TOP_Y_THRESHOLD * 2  # Start with 200%
        while idxs:
            idx = idxs[0]
            if idx in used:
                idxs.pop(0)
                continue
            row = [boxes_sorted[idx]]
            used.add(idx)
            base_y = boxes_sorted[idx][1]
            to_remove = [0]
            for i in range(1, len(idxs)):
                j = idxs[i]
                if j in used:
                    to_remove.append(i)
                    continue
                if abs(boxes_sorted[j][1] - base_y) <= threshold:
                    row.append(boxes_sorted[j])
                    used.add(j)
                    to_remove.append(i)
            # Remove used indices from idxs
            for i in reversed(to_remove):
                idxs.pop(i)
            rows.append(row)
            threshold *= 0.8  # Decrease threshold by 20% for next row
        # Reverse rows to return from first row to last row
        rows = rows[::-1]
        # Sort boxes in each row by x
        sorted_rows = [sorted(row, key=lambda box: box[0]) for row in rows]
        return sorted_rows
    elif class_id == 1:
        y_threshold = FRONT_Y_THRESHOLD
    

    # Lấy tọa độ Y từ boxes
    y_coords = np.array([[y] for x, y, cls, cnr in boxes])

    # Gom nhóm bằng DBSCAN
    clustering = DBSCAN(eps=y_threshold, min_samples=1).fit(y_coords)
    labels = clustering.labels_

    grouped_rows = {}
    for idx, label in enumerate(labels):
        if label not in grouped_rows:
            grouped_rows[label] = []
        grouped_rows[label].append(boxes[idx])

    # Sắp xếp các hộp trong hàng theo trục x (trái -> phải)
    sorted_rows = []
    for row_id, boxes_in_row in grouped_rows.items():
        avg_cy = sum(box[1] for box in boxes_in_row) / len(boxes_in_row)
        sorted_boxes = sorted(boxes_in_row, key=lambda box: box[0])
        sorted_rows.append((avg_cy, sorted_boxes))

    # Sắp xếp các hàng theo vị trí trung bình Y (trên xuống dưới)
    sorted_rows.sort(key=lambda x: x[0])

    return [row[1] for row in sorted_rows]

def create_full_boxes(boxes_by_class, x_threshold=BOX_X_THRESHOLD, y_threshold=BOX_Y_THRESHOLD):
    """
    Tự động ghép top_face + front_face thành full_box (class_id=2)
    
    Parameters:
        boxes_by_class (dict): dict chứa các box theo class_id
        x_threshold (float): ngưỡng cho là cùng hàng ngang
        y_threshold (float): ngưỡng cho là cùng hàng dọc
        
    Returns:
        dict: boxes_by_class đã thêm class 2 nếu có
    """
    top_boxes = boxes_by_class.get(0, [])
    front_boxes = boxes_by_class.get(1, [])

    full_boxes = []
    used_front_indices = set()

    for top in top_boxes:
        tx, ty, _, _ = top
        min_diff = float('inf')
        best_match_idx = -1

        for i, front in enumerate(front_boxes):
            if i in used_front_indices:
                continue

            fx, fy, _, _ = front
            x_diff = abs(tx - fx)
            y_diff = abs(ty - fy)

            if x_diff <= x_threshold and y_diff <= y_threshold:
                if x_diff < min_diff:
                    min_diff = x_diff
                    best_match_idx = i

        if best_match_idx != -1:
            matched_front = front_boxes[best_match_idx]
            fx, fy, _, _ = matched_front

            avg_x = round((tx + fx) / 2, 4)
            avg_y = round((ty + fy) / 2, 4)

            # Append with [matched top face, matched front face]
            full_boxes.append((avg_x, avg_y, 2, [top, matched_front]))
            used_front_indices.add(best_match_idx)

    # Cập nhật boxes_by_class tại chỗ
    if full_boxes:
        boxes_by_class[2] = full_boxes
    else:
        boxes_by_class.pop(2, None)

    return boxes_by_class


# ======================================================
# 5. HÀM KIỂM TRA is_full
# ======================================================

def is_full_front(boxes_by_class):
    """
    Kiểm tra:
    - Các full_box (nếu có) nằm trên một hàng duy nhất

    Trả về:
        Tuple: (is_aligned: bool, reason: str)
    """

    # Lấy các box cần thiết từ boxes_by_class
    boxes_with_full_boxes = create_full_boxes(boxes_by_class)
    top_boxes = boxes_with_full_boxes.get(0, [])
    front_boxes = boxes_with_full_boxes.get(1, [])
    full_boxes = boxes_with_full_boxes.get(2, [])

    # Chỉ lấy hàng đầu tiên của mỗi loại (giả sử đã được sắp xếp)
    if not top_boxes or not front_boxes:
        return False, "Missing top/front boxes"
       
    if full_boxes:
        full_rows = group_and_sort_boxes(full_boxes)
        if len(full_rows) != 1:
            return False, ">1 rows of full_box"
        # Lấy hàng duy nhất của full_box
        full_row = full_rows[0]

        # Lấy top left corner của front-face của box đầu tiên
        first_full = full_row[0]
        first_front = first_full[3][1]  # [top, front], lấy front
        first_front_corners = first_front[3]
        first_top_left_x = first_front_corners[0][0]

        # Lấy top right corner của front-face của box cuối cùng
        last_full = full_row[-1]
        last_front = last_full[3][1] # [top, front], lấy front
        last_front_corners = last_front[3]
        last_top_right_x = last_front_corners[1][0]

        fullbox_row_length = last_top_right_x - first_top_left_x
        if 1 - fullbox_row_length > BOX_X_THRESHOLD:
            return False, "Missing box"

    # return is_full_top(boxes_by_class)
    return True, "Front full"




def is_full_top(boxes_by_class, area_threshold=0.85):
    """
    Kiểm tra xem mặt trên có đầy đủ không dựa trên diện tích các top_face.
    
    Trả về:
        Tuple: (is_aligned: bool, reason: str)
    """
    top_list = boxes_by_class.get(0, [])
    if not top_list:
        return False, "Missing top_face"

    # Gom nhóm các hàng theo Y
    sorted_top_rows = group_and_sort_boxes(top_list)
    if not sorted_top_rows:
        return False, "No rows found for top_face"

     # === Xác định y_min và y_max ===
    last_row = sorted_top_rows[-1]
    y_max = round(np.mean([box[1] for box in last_row]), 4)
    first_row = sorted_top_rows[0]
    # Lấy tất cả các điểm top_left và top_right của các box trong hàng đầu tiên
    top_corners = []
    for box in first_row:
        corners = box[3]
        top_left = corners[0]
        top_right = corners[1]
        top_corners.extend([top_left, top_right])
    y_min = round(np.mean([pt[1] for pt in top_corners]), 4)
    
    
    def trace_top_left_upwards(sorted_top_rows):
        """
        Truy ngược lên các hàng để tìm top_left có y nhỏ nhất
        
        Parameters:
            sorted_top_rows (list): danh sách các hàng đã gom nhóm
            
        Returns:
            tuple: (x, y) của bot_left ban đầu và top_left cuối cùng có y_min
        """
        if not sorted_top_rows or len(sorted_top_rows) < 2:
            return None, None

        # Lấy hàng cuối cùng làm điểm bắt đầu
        last_row = sorted_top_rows[-1]
        current_box = last_row[0]  # Hộp đầu tiên trong hàng cuối
        corners = current_box[3]
        bot_left = corners[3]  # bottom_left
        top_left = corners[0]   # top_left

        # print(f"[INFO] Bắt đầu từ hàng cuối cùng: {bot_left}, {top_left}")

        # Duyệt ngược lại các hàng (từ dưới lên)
        for i in range(len(sorted_top_rows) - 2, -1, -1):
            prev_row = sorted_top_rows[i]
            for box in prev_row:
                prev_corners = box[3]
                prev_bot_left = prev_corners[3]
                prev_top_left = prev_corners[0]

                # Tính khoảng cách giữa bot_left hiện tại và bot_left của hàng trên
                threshold = 0.15
                distance = abs(bot_left[0] - prev_bot_left[0])
                if distance < threshold:  # Nếu gần nhau -> nối thành chuỗi
                    top_left = prev_bot_left
                    # print(f"[INFO] Thay top_left bằng {prev_top_left} từ hàng {i}")
                else:
                    threshold *= 2

        return bot_left, top_left
    # === Truy ngược tìm top_left tối ưu ===
    bot_left, top_left = trace_top_left_upwards(sorted_top_rows)
    if bot_left is None or top_left is None:
        return False, "Cannot find left edge points"


    def trace_top_right_upwards(sorted_top_rows):
        """
        Truy ngược lên các hàng để tìm top_right có y nhỏ nhất
        
        Parameters:
            sorted_top_rows (list): danh sách các hàng đã được sắp xếp
            
        Returns:
            tuple: (x, y) của bot_right ban đầu và top_right cuối cùng có y_min
        """
        if not sorted_top_rows or len(sorted_top_rows) < 1:
            return None, None

        # Lấy hàng cuối cùng → bắt đầu truy ngược từ đây
        last_row = sorted_top_rows[-1]
        last_box_in_last_row = last_row[-1]  # Hộp cuối cùng trong hàng cuối
        corners = last_box_in_last_row[3]

        bot_right = corners[2]  # bottom_right
        top_right = corners[1]  # top_right

        # print(f"[INFO] Bắt đầu từ hàng cuối cùng: {bot_right}, {top_right}")

        # Duyệt ngược lại các hàng
        for i in range(len(sorted_top_rows) - 2, -1, -1):
            prev_row = sorted_top_rows[i]
            if not prev_row:
                continue

            last_prev_box = prev_row[-1]  # Hộp cuối cùng trong hàng phía trên
            prev_corners = last_prev_box[3]
            prev_bot_right = prev_corners[2]  # bottom_right của hàng trên

            # Tính khoảng cách x giữa bot_right hiện tại và bot_right của hàng trên
            distance = abs(bot_right[0] - prev_bot_right[0])
            threshold = 0.15  # Ngưỡng khoảng cách
            if distance < threshold:  # Nếu gần nhau
                top_right = prev_bot_right  # Thay bằng top_right của hàng trên
                # print(f"[INFO] Cập nhật top_right thành {top_right} từ hàng {i}")
            else:
                threshold *= 2  # Tăng ngưỡng nếu không nối được

        return bot_right, top_right
    # === Truy ngược tìm top_right tối ưu ===
    bot_right, top_right = trace_top_right_upwards(sorted_top_rows)
    if bot_right is None or top_right is None:
        return False, "Cannot find right edge points"

    # === Fit 2 đường thẳng trái và phải ===
    def fit_line(p1, p2):
        """Fit đường thẳng qua 2 điểm"""
        x1, y1 = p1
        x2, y2 = p2
        if abs(x1 - x2) < 1e-6:
            return (x1, None)  # Đường thẳng đứng
        slope = (y2 - y1) / (x2 - x1)
        intercept = y1 - slope * x1
        return (slope, intercept)

    left_line = fit_line(bot_left, top_left)
    right_line = fit_line(bot_right, top_right)

    # === Tính giao điểm với y_min và y_max ===
    def intersect(line_params, y_val):
        if line_params[1] is None:  # Đường thẳng đứng
            return (round(line_params[0], 4), round(y_val, 4))
        slope, intercept = line_params
        x = (y_val - intercept) / slope
        return (round(x, 4), round(y_val, 4))

    left_top = intersect(left_line, y_min)
    left_bot = intersect(left_line, y_max)
    right_top = intersect(right_line, y_min)
    right_bot = intersect(right_line, y_max)

    # === Clip về miền [0, 1] nếu vượt quá giới hạn ===
    def clip_point(point):
        if point is None:
            return None
        x, y = point
        x = max(0.0, min(1.0, x))
        y = max(0.0, min(1.0, y))
        return (x, y)

    left_top = clip_point(left_top)
    left_bot = clip_point(left_bot)
    right_top = clip_point(right_top)
    right_bot = clip_point(right_bot)


    # === Tạo tứ giác ABCD ===
    quad_ABCD = [left_top, right_top, right_bot, left_bot]

    # === Tính tổng diện tích các top_face ===
    total_area = 0.0
    for box in top_list:
        _, _, _, corners = box
        poly = Polygon(corners)
        total_area += poly.area

    # === Tính diện tích tứ giác ABCD ===
    try:
        quad_poly = Polygon(quad_ABCD)
        full_area = quad_poly.area
    except Exception as e:
        return False, f"Invalid polygon: {str(e)}"

    filled_ratio = total_area / full_area if full_area > 0 else 0.0

    if filled_ratio >= area_threshold:
        return True, f"Top full {filled_ratio:.4f}"
    else:
        return False, f"Top not full {filled_ratio:.4f}"     
 
       
# ======================================================
# 6. HÀM MAIN - XỬ LÝ TOÀN BỘ FOLDER
# ======================================================

def process_folder(folder_path):
    best_file = find_file(folder_path)

    top_boxes = []
    front_boxes = []

    if best_file and os.path.isfile(best_file):
        boxes_by_class = read_yoloseg(best_file)
        if 0 in boxes_by_class:
            top_boxes = boxes_by_class[0]
        if 1 in boxes_by_class:
            front_boxes = boxes_by_class[1]


    # Gom nhóm và sắp xếp hàng
    top_sorted_rows = group_and_sort_boxes(top_boxes)
    front_sorted_rows = group_and_sort_boxes(front_boxes)

    # Đếm số lượng
    top_count = len(top_boxes)
    front_count = len(front_boxes)
    top_rows = len(top_sorted_rows)
    front_rows = len(front_sorted_rows)

    # Kiểm tra is_full
    is_full = (False, "No data")  # Mặc định
    if top_sorted_rows and front_sorted_rows:
        is_full = is_full_front(boxes_by_class)  # Dùng boxes_by_class

    return top_count, front_count, top_rows, front_rows, is_full, best_file

def process_all_folders(root_label_dir):
    all_folders = sorted([
        f for f in os.listdir(root_label_dir)
        if os.path.isdir(os.path.join(root_label_dir, f))
    ])

    expected_list = ["0"] * len(all_folders)

    if os.path.exists(EXPECTED_FILE_PATH):
        with open(EXPECTED_FILE_PATH, "r") as f:
            expected_list = [line.strip() for line in f.readlines()]
            if len(expected_list) != len(all_folders):
                print("Length mismatch! Skipping expected.")
                expected_list = ["0"] * len(all_folders)

    total_cases = 0
    passed_cases = 0

    with open(LOG_FILE_PATH, "w") as log_file, \
         open(FAILED_CASES_FILE_PATH, "w") as failed_file:

        # log_file.write(
        #     f"{'Case':<4} | {'Folder':<8} | {'Top':<3} | {'Front':<5} | "
        #     f"{'Top_Rows':<8} | {'Front_Rows':<10} | {'isFull':<6} | "
        #     f"{'Expected':<8} | {'Passed':<6} | {'Reason':<20} | {'Ratio':<7} | {'Comment'}" + "\n"
        # )
        log_file.write(
            f"{'Case':<4} | {'Folder':<8} | {'isFull':<6} | "
            f"{'Expected':<8} | {'Passed':<6} | {'Reason':<20} | {'Ratio':<7} | {'Comment'}" + "\n"
        )
        log_file.write("-" * 130 + "\n")

        failed_file.write(
            f"{'Case':<4} | {'Folder':<8} | {'File':<20} | {'isFull':<6} | {'Expected':<8} | {'Reason':<20} | {'Comment'}\n"
        )
        failed_file.write("-" * 130 + "\n")

        for idx, folder_name in enumerate(all_folders):
            folder_path = os.path.join(root_label_dir, folder_name)
            expected = expected_list[idx] if idx < len(expected_list) else "0"

            top, front, top_r, front_r, is_full, best_file = process_folder(folder_path)
            is_full_str = "1" if is_full[0] else "0"
            reason = is_full[1]
            is_match = is_full_str == expected
            passed = "1" if is_match else "0"

            total_cases += 1
            if is_match:
                passed_cases += 1
            ratio = f"{passed_cases}/{total_cases}"

            # line = (
            #     f"{idx + 1:<4} | {folder_name:<8} | {top:<3} | {front:<5} | "
            #     f"{top_r:<8} | {front_r:<10} | {is_full_str:<6} | "
            #     f"{expected:<8} | {passed:<6} | {reason:<20} | {ratio:<7} | "
            # )
            line = (
                f"{idx + 1:<4} | {folder_name:<8} | {is_full_str:<6} | "
                f"{expected:<8} | {passed:<6} | {reason:<20} | {ratio:<7} | "
            )
            log_file.write(line + "\n")

            if not is_match:

                failed_line = (
                    f"{idx + 1:<4} | {folder_name:<8} | {os.path.basename(best_file):<20} | "
                    f"{is_full_str:<6} | {expected:<8} | {reason:<20} | "
                )
                failed_file.write(failed_line + "\n")

    print(f"Result: {LOG_FILE_PATH}")
    print(f"Failed: {FAILED_CASES_FILE_PATH}")


# ==== CHẠY ====
process_all_folders(ROOT_LABEL_DIR)