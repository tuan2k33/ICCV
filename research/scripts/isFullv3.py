# =======================================================
# 1. IMPORT CÁC THƯ VIỆN CẦN THIẾT
# =======================================================

import os
import numpy as np
import cv2
from shapely.geometry import Polygon
from sklearn.cluster import DBSCAN
from sklearn.linear_model import RANSACRegressor, LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline

os.environ["CUDA_VISIBLE_DEVICES"] = "3"
# ======================================================
# 2. ĐƯỜNG DẪN & HẰNG SỐ
# ======================================================

ROOT_LABEL_DIR = "/ssd1/tuannw/infer_result/28-05-25"
EXPECTED_FILE_PATH = os.path.join(ROOT_LABEL_DIR, "expected.txt")
LOG_FILE_PATH = os.path.join(ROOT_LABEL_DIR, "result_log3.txt")
FAILED_CASES_FILE_PATH = os.path.join(ROOT_LABEL_DIR, "failed3.txt")
# Threshold cho từng loại mặt
TOP_Y_THRESHOLD = 0.05
FRONT_Y_THRESHOLD = 0.05
BOX_X_THRESHOLD = 0.1
BOX_Y_THRESHOLD = 0.1
AREA_THRESHOLD = 0.004

# ======================================================
# 3. HÀM TÌM VÀ ĐỌC FILE
# ======================================================

def find_file(folder_path):
    """
    Tìm 3 file tốt nhất theo góc nhìn:
    - front_view: diện tích front-face lớn nhất
    - top_view: diện tích top-face lớn nhất (sau khi loại front_view)
    - bird_view: file còn lại (ưu tiên top-face lớn), nếu không có thì = top_view
    """
    files = [f for f in os.listdir(folder_path) if f.endswith(".txt")]
    candidates = []

    def compute_areas(txt_path):
        try:
            boxes_by_class = read_yoloseg(txt_path)
            top_area = sum(Polygon(box[3]).area for box in boxes_by_class.get(0, []))
            front_area = sum(Polygon(box[3]).area for box in boxes_by_class.get(1, []))
            return top_area, front_area
        except Exception as e:
            print(f"[ERROR] {txt_path}: {e}")
            return 0.0, 0.0

    # Tính diện tích cho từng file
    for file in files:
        full_path = os.path.join(folder_path, file)
        top_area, front_area = compute_areas(full_path)
        candidates.append({
            "path": full_path,
            "file": file,
            "top_area": top_area,
            "front_area": front_area
        })

    if not candidates:
        return None, None, None

    # === 1. Chọn front_view ===
    candidates_with_no_top = [c for c in candidates if c["top_area"] == 0]

    if candidates_with_no_top:
        # Chọn file không có top và có front_area lớn nhất
        candidates_with_no_top.sort(key=lambda x: x["front_area"], reverse=True)
        front_view = candidates_with_no_top[0]
        candidates.remove(front_view)
    else:
        # Nếu không có, chọn file có front_area lớn nhất
        candidates.sort(key=lambda x: x["front_area"], reverse=True)
        front_view = candidates.pop(0)

    # === 2. Chọn top_view ===
    if candidates:
        candidates.sort(key=lambda x: x["top_area"], reverse=True)
        top_view = candidates.pop(0)
    else:
        top_view = front_view

    # === 3. Chọn bird_view ===
    if candidates:
        candidates.sort(key=lambda x: x["front_area"], reverse=True)
        bird_view = candidates[0]
    else:
        bird_view = top_view

    print(f"[{os.path.basename(folder_path)}] Selected: bird_view.")
    print(f" top_view   : {os.path.basename(top_view['path'])}")
    print(f" bird_view  : {os.path.basename(bird_view['path'])}")
    print(f" front_view : {os.path.basename(front_view['path'])}")

    return top_view["path"], bird_view["path"], front_view["path"]


def read_yoloseg(txt_path):
    """
    Đọc file YOLOseg và trích xuất thông tin mỗi mask:
    (class_id, area, [center_x, center_y, width, height], [top_left, top_right, bottom_right, bottom_left])

    Sử dụng convex hull + approxPolyDP để tìm đúng 4 góc.
    width/height được tính lại dựa trên khoảng cách giữa các góc.

    Returns:
        boxes_by_class = {
            class_id: [
                (class_id, area, [cx, cy, w, h], [pt1, pt2, pt3, pt4]),
                ...
            ]
        }
    """

    def sort_corners_four_points(pts):
        """
        Sắp xếp 4 điểm thành [top_left, top_right, bottom_right, bottom_left]
        """
        pts = np.array(pts)
        sorted_by_y = pts[np.argsort(pts[:, 1])]
        top_two = sorted_by_y[:2]
        bottom_two = sorted_by_y[2:]

        if top_two[0][0] < top_two[1][0]:
            top_left, top_right = top_two[0], top_two[1]
        else:
            top_left, top_right = top_two[1], top_two[0]

        if bottom_two[0][0] < bottom_two[1][0]:
            bottom_left, bottom_right = bottom_two[0], bottom_two[1]
        else:
            bottom_left, bottom_right = bottom_two[1], bottom_two[0]

        return [top_left, top_right, bottom_right, bottom_left]

    boxes_by_class = {}

    with open(txt_path, "r") as f:
        for line in f:
            parts = list(map(float, line.strip().split()))
            class_id = int(parts[0])
            coords = parts[1:]

            pts = np.array(coords, dtype=np.float32).reshape(-1, 2)

            # === Thuật toán tìm corners chính xác ===
            hull = cv2.convexHull(pts)
            epsilon = 0.01 * cv2.arcLength(hull, True)
            scale = 1.05
            approx = cv2.approxPolyDP(hull, epsilon, True)

            while len(approx) > 4:
                epsilon *= scale
                approx = cv2.approxPolyDP(hull, epsilon, True)


            corners = sort_corners_four_points(approx.reshape(-1, 2))
            corners = [[round(x, 4), round(y, 4)] for x, y in corners]

            # === Tính lại width/height theo corners ===
            top_left, top_right, bottom_right, bottom_left = corners

            width_top = np.linalg.norm(np.array(top_right) - np.array(top_left))
            width_bottom = np.linalg.norm(np.array(bottom_right) - np.array(bottom_left))
            width = round((width_top + width_bottom) / 2, 4)

            height_left = np.linalg.norm(np.array(bottom_left) - np.array(top_left))
            height_right = np.linalg.norm(np.array(bottom_right) - np.array(top_right))
            height = round((height_left + height_right) / 2, 4)

            # === Tính center theo trung bình 4 điểm ===
            center_x = round(np.mean([pt[0] for pt in corners]), 4)
            center_y = round(np.mean([pt[1] for pt in corners]), 4)
            xywh = [center_x, center_y, width, height]

            # === Tính diện tích polygon ===
            try:
                poly = Polygon(corners)
                area = round(poly.area, 4)
            except Exception:
                area = 0.0

            if class_id not in boxes_by_class:
                boxes_by_class[class_id] = []

            boxes_by_class[class_id].append(
                (class_id, area, xywh, corners)
            )

    return boxes_by_class


# ======================================================
# 4. HÀM GOM NHÓM VÀ SẮP XẾP HÀNG
# ======================================================

def group_and_sort_boxes(boxes, y_threshold=0.1):
    if not boxes:
        return []

    class_id = boxes[0][0]
    if class_id == 0:
        y_threshold = TOP_Y_THRESHOLD
    elif class_id == 1:
        y_threshold = FRONT_Y_THRESHOLD
    # class_id == 2 (full_box) vẫn dùng y_threshold mặc định nếu không đổi

    # Lấy center_y từ box[2][1] (xywh)
    y_coords = np.array([[box[2][1]] for box in boxes])

    # Gom nhóm bằng DBSCAN theo center_y
    clustering = DBSCAN(eps=y_threshold, min_samples=1).fit(y_coords)
    labels = clustering.labels_

    grouped_rows = {}
    for idx, label in enumerate(labels):
        if label not in grouped_rows:
            grouped_rows[label] = []
        grouped_rows[label].append(boxes[idx])

    # Tính trung bình y để sắp xếp hàng (trên xuống dưới)
    sorted_rows = []
    for row_boxes in grouped_rows.values():
        avg_cy = sum(box[2][1] for box in row_boxes) / len(row_boxes)
        sorted_boxes = sorted(row_boxes, key=lambda box: box[2][0])  # sort theo center-x
        sorted_rows.append((avg_cy, sorted_boxes))

    sorted_rows.sort(key=lambda row: row[0])
    return [row[1] for row in sorted_rows]


def create_full_boxes(boxes_by_class, x_threshold=BOX_X_THRESHOLD, y_threshold=BOX_Y_THRESHOLD):
    """
    Ghép top_face + front_face thành full_box (class_id=2), 
    đảm bảo mỗi front_face chỉ ghép với top_face có x_diff nhỏ nhất trong số các top phù hợp.
    """
    top_boxes = boxes_by_class.get(0, [])
    front_boxes = boxes_by_class.get(1, [])

    full_boxes = []
    used_top_indices = set()

    for i_front, front in enumerate(front_boxes):
        _, area_front, xywh_front, _ = front
        fx = xywh_front[0]
        fy = round(xywh_front[1] - xywh_front[3] / 2, 4)

        min_y_diff = float('inf')
        best_match_idx = -1

        for i_top, top in enumerate(top_boxes):
            if i_top in used_top_indices:
                continue

            _, area_top, xywh_top, _ = top
            tx = xywh_top[0]
            ty = round(xywh_top[1] + xywh_top[3] / 2, 4)

            x_diff = abs(fx - tx)
            y_diff = abs(fy - ty)

            if x_diff <= x_threshold and y_diff <= y_threshold:
                if y_diff < min_y_diff:
                    min_y_diff = y_diff
                    best_match_idx = i_top

        if best_match_idx != -1:
            matched_top = top_boxes[best_match_idx]
            _, area_top, xywh_top, _ = matched_top

            avg_x = round((fx + xywh_top[0]) / 2, 4)
            avg_y = round((fy + (xywh_top[1] + xywh_top[3] / 2)) / 2, 4)

            area_full = round(area_top + area_front, 4)
            w_full = xywh_front[2]
            h_full = round(xywh_top[3] + xywh_front[3], 4)

            full_boxes.append((2, area_full, [xywh_front[0], xywh_front[1], w_full, h_full], [matched_top, front]))
            used_top_indices.add(best_match_idx)

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
    - Các full_box (nếu có) nằm trên một hàng duy nhất (tức là không thiếu hàng)
    - Dựa trên front-face của full_box để tính chiều dài hàng

    Trả về:
        Tuple: (is_aligned: bool, reason: str)
    """
    boxes_with_full_boxes = create_full_boxes(boxes_by_class)
    top_boxes = boxes_with_full_boxes.get(0, [])
    front_boxes = boxes_with_full_boxes.get(1, [])
    full_boxes = boxes_with_full_boxes.get(2, [])

    if not top_boxes or not front_boxes:
        return False, "Missing top/front boxes"

    if full_boxes:
        full_rows = group_and_sort_boxes(full_boxes)
        if len(full_rows) != 1:
            return False, ">1 rows of full_box"

        full_row = full_rows[0]
        # Lấy front-face của box đầu tiên
        first_full = full_row[0]
        first_front = first_full[3][1]  # [top, front]
        first_front_corners = first_front[3]
        first_top_left_x = first_front_corners[0][0]

        # Lấy front-face của box cuối cùng
        last_full = full_row[-1]
        last_front = last_full[3][1]
        last_front_corners = last_front[3]
        last_top_right_x = last_front_corners[1][0]

        # Tính chiều dài hàng các hộp
        fullbox_row_length = last_top_right_x - first_top_left_x

        if 1 - fullbox_row_length > BOX_X_THRESHOLD:
            return False, "Missing box in row"

    return is_full_top(boxes_by_class)

def is_full_top(boxes_by_class, area_threshold=0.85):
    """
    Kiểm tra kiện hàng có đầy đủ từ góc nhìn mặt trên (top-face).
    Dựa trên: diện tích top-face / diện tích hình chữ nhật bao quanh full_boxes.

    Returns:
        (is_full: bool, reason: str)
    """
    boxes_with_full_boxes = create_full_boxes(boxes_by_class)
    full_boxes = boxes_with_full_boxes.get(2, [])
    top_boxes = boxes_by_class.get(0, [])

    if not top_boxes:
        return False, "Missing top_face"
    if not full_boxes:
        return False, "No full_boxes created"

    # Lấy hộp đầu và cuối trong danh sách full_box đã được gom hàng
    full_rows = group_and_sort_boxes(full_boxes)
    if not full_rows:
        return False, "Cannot group full_boxes"

    # Dùng hàng đầu tiên
    full_row = full_rows[0]
    first_full = full_row[0]
    last_full = full_row[-1]

    top_face_first = first_full[3][0]
    top_face_last = last_full[3][0]

    # Lấy các điểm cần dùng
    bot_left = top_face_first[3][3]  # bottom_left
    top_left = top_face_first[3][0]  # top_left

    bot_right = top_face_last[3][2]  # bottom_right
    top_right = top_face_last[3][1]  # top_right

    # Fit 2 đường thẳng: trái và phải
    def fit_line(p1, p2):
        x1, y1 = p1
        x2, y2 = p2
        if abs(x1 - x2) < 1e-6:
            return (x1, None)  # đứng
        slope = (y2 - y1) / (x2 - x1)
        intercept = y1 - slope * x1
        return (slope, intercept)

    left_line = fit_line(bot_left, top_left)
    right_line = fit_line(bot_right, top_right)

    # Tính y_min và y_max
    y_min = 0.01
    y_max = min(bot_left[1], bot_right[1])

    # Tính giao điểm với y_min và y_max
    def intersect(line, y_val):
        if line[1] is None:  # đứng
            return (round(line[0], 4), round(y_val, 4))
        slope, intercept = line
        x = (y_val - intercept) / slope
        return (round(x, 4), round(y_val, 4))

    left_top = intersect(left_line, y_min)
    left_bot = intersect(left_line, y_max)
    right_top = intersect(right_line, y_min)
    right_bot = intersect(right_line, y_max)

    # Clip các điểm về trong ảnh [0,1]
    def clip_point(p):
        x, y = p
        return (min(max(x, 0.0), 1.0), min(max(y, 0.0), 1.0))

    quad_ABCD = [
        clip_point(left_top),
        clip_point(right_top),
        clip_point(right_bot),
        clip_point(left_bot)
    ]

    # Tính diện tích vùng bao (ABCD)
    try:
        quad_poly = Polygon(quad_ABCD)
        full_area = quad_poly.area
    except Exception as e:
        return False, f"Invalid polygon: {str(e)}"

    # Tính tổng diện tích top_face
    total_top_area = sum(round(box[1], 4) for box in top_boxes)

    filled_ratio = total_top_area / full_area if full_area > 0 else 0.0

    if filled_ratio >= area_threshold:
        return True, f"Top full {filled_ratio:.4f}"
    else:
        return False, f"Top not full {filled_ratio:.4f}"
 
       
# ======================================================
# 6. HÀM XỬ LÝ TOÀN BỘ FOLDER
# ======================================================

def process_folder(folder_path):
    selected_file, _,  _ = find_file(folder_path)

    top_boxes = []
    front_boxes = []

    if selected_file and os.path.isfile(selected_file):
        boxes_by_class = read_yoloseg(selected_file)
        if 0 in boxes_by_class:
            top_boxes = boxes_by_class[0]
        if 1 in boxes_by_class:
            front_boxes = boxes_by_class[1]


    # Gom nhóm và sắp xếp hàng
    top_sorted_rows = group_and_sort_boxes(top_boxes)
    front_sorted_rows = group_and_sort_boxes(front_boxes)

    
    # Kiểm tra is_full
    is_full = (False, "No data")  # Mặc định
    if top_sorted_rows and front_sorted_rows:
        is_full = is_full_front(boxes_by_class)  # Dùng boxes_by_class

    return is_full, selected_file

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
    failed_cases_info = []

    with open(LOG_FILE_PATH, "w") as log_file, \
         open(FAILED_CASES_FILE_PATH, "w") as failed_file:

        # Ghi header vào log file
        log_file.write(
            f"{'Case':<4} | {'Folder':<8} | {'File':<25} | {'isFull':<6} | "
            f"{'Expected':<8} | {'Passed':<6} | {'Reason':<25} | {'Ratio':<7} | {'Comment'}\n"
        )
        log_file.write("-" * 130 + "\n")

        # Ghi header vào failed.txt theo yêu cầu
        failed_file.write("FAILED                                                 isFull   Expected\n")
        failed_file.write("=" * 100 + "\n")

        for idx, folder_name in enumerate(all_folders):
            folder_path = os.path.join(root_label_dir, folder_name)
            expected = expected_list[idx] if idx < len(expected_list) else "0"

            is_full, selected_file = process_folder(folder_path)
            is_full_str = "1" if is_full[0] else "0"
            reason = is_full[1]
            is_match = is_full_str == expected
            passed = "1" if is_match else "0"

            total_cases += 1
            if is_match:
                passed_cases += 1
            ratio = f"{passed_cases}/{total_cases}"

            # Ghi log chi tiết
            log_line = (
                f"{idx + 1:<4} | {folder_name:<8} | {os.path.basename(selected_file):<25} | {is_full_str:<6} | "
                f"{expected:<8} | {passed:<6} | {reason:<25} | {ratio:<7} | "
            )
            log_file.write(log_line + "\n")

            # Ghi case fail
            if not is_match:
                failed_cases_info.append((idx + 1, folder_path, reason))
                failed_file.write(f"{idx + 1:<4} | {folder_path:<45} | {is_full_str:<6} | {expected:<8} | {reason}\n")

        # Kết thúc failed.txt
        failed_file.write("=" * 100 + "\n")
        failed_file.write(f"failed: {len(failed_cases_info)}\n")
        failed_file.write(f"passed: {passed_cases}\n")
        failed_file.write(f"total: {total_cases}\n")

    # Chỉ in tên file log kết quả
    print(f"Result: {LOG_FILE_PATH}")
    print(f"Failed: {FAILED_CASES_FILE_PATH}")


# ======================================================
# 7. CHẠY TOÀN BỘ
# ======================================================
process_all_folders(ROOT_LABEL_DIR)