# file đầu tiên để viết thuật toán check is_full cho top_face và front_face
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
X_THRESHOLD = 0.1
Y_THRESHOLD = 0.1

# ======================================================
# 3. HÀM TÌM FILE PHÙ HỢP
# ======================================================

def find_file(folder_path):
    """Chọn file tốt nhất trong folder theo thứ tự ưu tiên: 1_(1).txt > 1_(2).txt > ... > 1_.txt"""
    files = os.listdir(folder_path)
    candidates = []

    for file in files:
        full_path = os.path.join(folder_path, file)

        if "1_.txt" in file:
            # Ưu tiên thấp nhất
            candidates.append((10, full_path))
            
        elif "1_(" in file and ")".join(file.split("1_(")[1].split(")")[0:-1]) and file.endswith(".txt"):
            try:
                suffix_part = file.split("1_(")[1]
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
    def find_corners(mask_normalized, img_w=640, img_h=640):
        """
        Lấy 4 điểm đặc biệt từ mask đã chuẩn hóa về [0,1]

        Parameters:
            mask_normalized (np.ndarray): mảng [n_points, 2], tọa độ đã chuẩn hóa về [0,1]
            img_w, img_h: kích thước ảnh gốc để chuyển đổi sang pixel
            
        Returns:
            list: [top_left, top_right, bottom_right, bottom_left] trong miền [0,1]
        """
        # Chuyển về pixel để xử lý
        pts_px = np.array([[x * img_w, y * img_h] for x, y in mask_normalized], dtype=np.int32)

        sums = pts_px[:, 0] + pts_px[:, 1]
        diffs = pts_px[:, 0] - pts_px[:, 1]

        top_left = tuple(pts_px[np.argmin(sums)])
        bottom_right = tuple(pts_px[np.argmax(sums)])
        top_right = tuple(pts_px[np.argmax(diffs)])
        bottom_left = tuple(pts_px[np.argmin(diffs)])

        # Chuyển lại về chuẩn hóa [0,1] trước khi trả về
        return [
            [round(x / img_w, 4), round(y / img_h, 4)] for x, y in [top_left, top_right, bottom_right, bottom_left]
        ]
        #  # Tạo danh sách 4 điểm góc bằng approxPolyDP
        #     points = np.array(coords, dtype=np.float32).reshape(-1, 2)
        #     epsilon = 0.04 * cv2.arcLength(points, True)
        #     approx = cv2.approxPolyDP(points, epsilon, True)
            
            
        #     if len(approx) != 4:
        #         print(f"[WARNING] 4 corners not found {class_id}, getting bbox instead.")
        #         corners = [(min_x, min_y), (max_x, min_y), (min_x, max_y), (max_x, max_y)]
        #     else:
        #         corners = approx.reshape(-1, 2).tolist() 
            
   
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

            # Convert normalized segment to 640x640 pixel mask
            mask_px = np.round(mask * 640).astype(np.int32)
            mask_img = np.zeros((640, 640), dtype=np.uint8)
            cv2.fillPoly(mask_img, [mask_px], 1)

            # Find corners from the mask (using normalized mask as before)
            corners = find_corners(mask)
            # print("Corners:", corners)
            if class_id not in boxes_by_class:
                boxes_by_class[class_id] = []

            boxes_by_class[class_id].append((center_x, y_custom, class_id, corners))
    
    return boxes_by_class


def group_and_sort_boxes(boxes, y_threshold=Y_THRESHOLD):
    if not boxes:
        return []

    # Xác định class_id từ hộp đầu tiên
    class_id = boxes[0][2]  # Lấy class_id từ (x, y, class_id, corners)

    # Chọn threshold dựa trên class_id
    if class_id == 0:
        y_threshold = TOP_Y_THRESHOLD
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

def create_full_boxes(boxes_by_class, x_threshold=X_THRESHOLD, y_threshold=Y_THRESHOLD):
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

            full_boxes.append((avg_x, avg_y, 2, []))
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

    return is_full_top(boxes_by_class)
    # return True, "Front full"




def is_full_top(boxes_by_class, area_threshold=0.9):
    """
    Kiểm tra xem mặt trên có đầy đủ không dựa trên diện tích các top_face.
    
    Thay vì chỉ dùng box trái nhất/phải nhất, giờ dùng tất cả các điểm top_left và bottom_left/right
    để fit đường thẳng và xác định giao điểm chính xác hơn.

    Returns:
        tuple: (is_full_top: bool, reason: str)
    """
    top_list = boxes_by_class.get(0, [])

    # Tính tổng diện tích các top_face
    top_area = 0.0
    all_corners = []

    for box in top_list:
        _, _, _, corners = box
        poly = Polygon(corners)
        top_area += poly.area
        all_corners.append(corners)

    # Gom nhóm các hộp thành hàng theo Y
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
    
    
    def linear_regression_1d(points, threshold=0.05):
        """
        Fit một đường thẳng qua danh sách điểm bằng RANSACRegressor
        
        Parameters:
            points (list): list các tuple (x, y)
            threshold (float): ngưỡng xác định inlier
            
        Returns:
            tuple: (slope, intercept) của phương trình y = slope * x + intercept
        """
        if len(points) < 2:
            return None

        X = np.array([p[0] for p in points]).reshape(-1, 1)
        y = np.array([p[1] for p in points])

        # Dùng RANSAC để fit với khả năng loại bỏ outlier tự động
        model = make_pipeline(PolynomialFeatures(1), RANSACRegressor(estimator=LinearRegression(), residual_threshold=threshold, random_state=42))
        model.fit(X, y)

        coef = model.named_steps['ransacregressor'].estimator_.coef_
        intercept = model.named_steps['ransacregressor'].estimator_.intercept_

        slope = round(coef[1], 4)
        intercept = round(intercept, 4)

        return (slope, intercept)


    def line_intersection(line_params, y_intersect):
        """
        Tìm giao điểm giữa đường thẳng (slope, intercept) và đường y=y_intersect
        
        Parameters:
            line_params (tuple): (slope, intercept)
            y_intersect (float): giá trị y mà bạn muốn tìm giao
            
        Returns:
            tuple: (x, y_intersect)
        """
        slope, intercept = line_params
        if slope == 0:
            return None  # Đường ngang -> vô số nghiệm hoặc không cắt
        
        x_intersect = (y_intersect - intercept) / slope
        return round(x_intersect, 4), round(y_intersect, 4)    
    
    
    # === Thu thập các điểm top_left và bottom_left từ mọi hàng ===
    left_points_tl = []
    left_points_bl = []
    right_points_tr = []
    right_points_br = []

    for row in sorted_top_rows:
        first_box = row[0]  # Hộp đầu tiên của hàng
        corners = first_box[3]  # Danh sách [top_left, top_right, bottom_right, bottom_left]

        # Lấy top_left (corners[0]) và bottom_left (corners[3])
        top_left = corners[0]
        bottom_left = corners[2]  # hoặc corners[3] nếu bottom_left là [3]

        left_points_tl.append(top_left)
        left_points_bl.append(bottom_left)
        
        last_box = row[-1]  # Hộp cuối cùng của hàng
        corners = last_box[3]  # [top_left, top_right, bottom_right, bottom_left]

        # Trích top_right và bottom_right
        top_right = corners[1]
        bottom_right = corners[2]  # hoặc corners[3] nếu bạn coi là bottom_left

        right_points_tr.append(top_right)
        right_points_br.append(bottom_right)

    # === Fit đường thẳng trái (A-B) từ top_left + bottom_left ===
    left_points = left_points_tl + left_points_bl + [[0, y_max]]

    left_XY = np.array([(p[0], p[1]) for p in left_points])
    left_XY = left_XY[np.argsort(left_XY[:, 0])]  # sắp xếp theo x tăng dần
    # print("Left XY:", left_XY)
    # Fit đường thẳng bằng RANSAC (tự loại bỏ outlier)
    left_line = linear_regression_1d(left_XY.tolist())

    # === Fit đường thẳng phải (C-D) từ top_right + bottom_right ===
    right_points = right_points_tr + right_points_br + [[1, y_max]]

    right_XY = np.array([(p[0], p[1]) for p in right_points])
    right_XY = right_XY[np.argsort(right_XY[:, 0])]
    # print("Right XY:", right_XY)
    # Fit đường thẳng bằng RANSAC
    right_line = linear_regression_1d(right_XY.tolist())
    
    # === Tính giao điểm với y_min và y_max ===
    left_top = line_intersection(left_line, y_min)  # Giao với y_min
    left_bot = line_intersection(left_line, y_max)   # Giao với y_max

    right_top = line_intersection(right_line, y_min)   # Giao với y_min
    right_bot = line_intersection(right_line, y_max)   # Giao với y_max

    
    # Áp dụng clip để đảm bảo nằm trong [0,1]
    def clip_point(point):
        """
        Cắt tọa độ điểm (x, y) về khoảng [0, 1]
        
        Parameters:
            point (tuple): (x, y), x và y có thể vượt quá [0, 1]
            
        Returns:
            tuple: (clipped_x, clipped_y)
        """
        if point is None:
            return None
        
        x, y = point
        x_clipped = max(0.0, min(1.0, x))
        y_clipped = max(0.0, min(1.0, y))
        
        return round(x_clipped, 4), round(y_clipped, 4)
    
    
    left_top = clip_point(left_top)
    left_bot = clip_point(left_bot)
    right_top = clip_point(right_top)
    right_bot = clip_point(right_bot)
    
    
    # print(f"left_top (giao y_min): {left_top}")
    # print(f"left_bot (giao y_max): {left_bot}")
    # print(f"right_top (giao y_min): {right_top}")
    # print(f"right_bot (giao y_max): {right_bot}")
    # === Tạo tứ giác ABCD ===
    quad_ABCD = [left_top, left_bot, right_bot, right_top]

    try:
        poly_quad = Polygon(quad_ABCD)
        full_area = poly_quad.area
    except Exception as e:
        return False, f"Invalid polygon"

    # print(f"Full area: {full_area:.4f}")
    # print(f"Total area of top boxes: {top_area:.4f}")
    
    filled_ratio = top_area / full_area if full_area > 0 else 0.0

    if filled_ratio >= area_threshold:
        return True, f"Top full: {filled_ratio:.4f}"
    else:
        return False, f"Top not full: {filled_ratio:.4f}"  
       
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

        log_file.write(
            f"{'Case':<4} | {'Folder':<8} | {'Top':<3} | {'Front':<5} | "
            f"{'Top_Rows':<8} | {'Front_Rows':<10} | {'isFull':<6} | "
            f"{'Expected':<8} | {'Passed':<6} | {'Reason':<20} | {'Ratio':<7} | {'Comment'}" + "\n"
        )
        log_file.write("-" * 160 + "\n")

        failed_file.write(
            f"{'Case':<4} | {'Folder':<8} | {'File':<20} | {'isFull':<6} | {'Expected':<8} | {'Reason'}\n"
        )
        failed_file.write("-" * 120 + "\n")

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

            line = (
                f"{idx + 1:<4} | {folder_name:<8} | {top:<3} | {front:<5} | "
                f"{top_r:<8} | {front_r:<10} | {is_full_str:<6} | "
                f"{expected:<8} | {passed:<6} | {reason:<20} | {ratio:<7} | "
            )
            log_file.write(line + "\n")

            if not is_match:

                failed_line = (
                    f"{idx + 1:<4} | {folder_name:<8} | {os.path.basename(best_file):<20} | "
                    f"{is_full_str:<6} | {expected:<8} | {reason}"
                )
                failed_file.write(failed_line + "\n")

    print(f"Result: {LOG_FILE_PATH}")
    print(f"Failed: {FAILED_CASES_FILE_PATH}")


# ==== CHẠY ====
process_all_folders(ROOT_LABEL_DIR)