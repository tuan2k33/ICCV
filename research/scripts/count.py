import os
import numpy as np
from sklearn.cluster import DBSCAN
import cv2
from shapely.geometry import Polygon
from typing import List, Tuple
# ======================================================
FOLDER_PATH = "/ssd1/tuannw/infer_result/24-05-25/AH - 063"
TOP_Y_THRESHOLD = 0.05
FRONT_Y_THRESHOLD = 0.07
BOX_X_THRESHOLD = 0.1
BOX_Y_THRESHOLD = 0.1
AREA_THRESHOLD = 0.004

os.environ["CUDA_VISIBLE_DEVICES"] = "3"

# === HÀM TÌM FILE TỐT NHẤT TRONG FOLDER ===
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
def group_and_sort_boxes(boxes, y_threshold=BOX_Y_THRESHOLD):
    if not boxes:
        return []

    class_id = boxes[0][0]

    if class_id == 0:
        y_threshold = TOP_Y_THRESHOLD
        y_coords = np.array([[box[2][1]] for box in boxes])
        labels = DBSCAN(eps=y_threshold, min_samples=1).fit(y_coords).labels_

        grouped_rows = {}
        for idx, label in enumerate(labels):
            grouped_rows.setdefault(label, []).append(boxes[idx])

        sorted_rows = []
        for row_boxes in grouped_rows.values():
            row_boxes.sort(key=lambda b: b[2][0])  # Group theo center x
            cy_avg = np.mean([b[2][1] for b in row_boxes])
            sorted_rows.append((cy_avg, row_boxes))

        sorted_rows.sort(key=lambda r: r[0])  # Sort theo center y
        return [r[1] for r in sorted_rows]    
    
    elif class_id == 1:
        y_threshold = FRONT_Y_THRESHOLD
        y_coords = np.array([[box[2][1]] for box in boxes])
        labels = DBSCAN(eps=y_threshold, min_samples=1).fit(y_coords).labels_

        grouped_rows = {}
        for idx, label in enumerate(labels):
            grouped_rows.setdefault(label, []).append(boxes[idx])

        sorted_rows = []
        for row_boxes in grouped_rows.values():
            row_boxes.sort(key=lambda b: b[2][0])  # Group theo center x
            cy_avg = np.mean([b[2][1] for b in row_boxes])
            sorted_rows.append((cy_avg, row_boxes))

        sorted_rows.sort(key=lambda r: r[0])  # Sort theo center y
        return [r[1] for r in sorted_rows]

    y_coords = np.array([[box[2][1]] for box in boxes])
    labels = DBSCAN(eps=y_threshold, min_samples=1).fit(y_coords).labels_

    grouped_rows = {}
    for idx, label in enumerate(labels):
        grouped_rows.setdefault(label, []).append(boxes[idx])

    sorted_rows = []
    for row_boxes in grouped_rows.values():
        row_boxes.sort(key=lambda b: b[2][0])  # Group theo center x
        cy_avg = np.mean([b[2][1] for b in row_boxes])
        sorted_rows.append((cy_avg, row_boxes))

    sorted_rows.sort(key=lambda r: r[0])  # Sort theo center y
    return [r[1] for r in sorted_rows]


def detect_top_layers(top_rows, ratio_threshold=(1.5, 1.9)):
    """
    Phân lớp các hàng top_face thành từng layer dựa trên ratio diện tích.
    
    - Nếu avg_area[row_i+1] / avg_area[row_i] ∈ ratio_threshold → cùng layer
    - Ngược lại → khác layer

    Trả về:
        grouped_layers: List[List[rows]] (các hàng đã gom theo layer)
    """

    n_rows = len(top_rows)
    if n_rows == 0:
        return []

    def avg_area(row):
        return np.mean([b[1] for b in row])

    is_same_layer = []
    for i in range(len(top_rows) - 1):
        area_i = avg_area(top_rows[i])
        area_next = avg_area(top_rows[i + 1])
        if area_i == 0:
            ratio = float('inf')
        else:
            ratio = area_next / area_i

        is_same = ratio_threshold[0] <= ratio <= ratio_threshold[1]
        is_same_layer.append(is_same)

    # # Gom nhóm theo is_same_layer
    # grouped_layers = []
    # current_layer = [top_rows[0]]
    # for i in range(1, len(top_rows)):
    #     if is_same_layer[i - 1]:
    #         current_layer.append(top_rows[i])
    #     else:
    #         grouped_layers.append(current_layer)
    #         current_layer = [top_rows[i]]
    # grouped_layers.append(current_layer)

    # return grouped_layers
    # Gom theo is_same_layer, lưu index
    grouped_layer_indices = []
    current_group = [0]
    for i in range(1, len(top_rows)):
        if is_same_layer[i - 1]:
            current_group.append(i)
        else:
            grouped_layer_indices.append(current_group)
            current_group = [i]
    grouped_layer_indices.append(current_group)

    return grouped_layer_indices

def count_front_layers(boxes_by_class, y_threshold=FRONT_Y_THRESHOLD):
    """
    Dem so hop tren tung hang cua front_view (class_id = 1).

    Tham so
    -------
    boxes_by_class : dict
        Ket qua cua read_yoloseg(...) chua cac front_face (class 1).
    y_threshold : float, mac dinh 0.05
        Khoang cach toi da giua hai center‑y (da chuan hoa 0..1) de coi chung
        mot hang.

    Tra ve
    ------
    List[int]
        [row_0_count, row_1_count, ...] voi row_0 o tren cung (y be nhat).
    """
    # Lay toan bo front_face (class_id = 1)
    front_boxes = boxes_by_class.get(1, [])
    if not front_boxes:
        return []

    # Chuan bi du lieu Y cho DBSCAN
    y_coords = np.array([[b[2][1]] for b in front_boxes], dtype=np.float32)

    # Gom cum theo truc Y
    labels = DBSCAN(eps=y_threshold, min_samples=1).fit(y_coords).labels_

    # Gop theo nhan
    rows = {}
    for idx, lb in enumerate(labels):
        rows.setdefault(lb, []).append(front_boxes[idx])

    # Sap xep cac hang tu tren xuong duoi va lay so dem
    row_stats = []
    for boxes in rows.values():
        cy_mean = np.mean([b[2][1] for b in boxes])
        row_stats.append((cy_mean, len(boxes)))

    row_stats.sort(key=lambda x: x[0])        # y be nhat la tren cung
    return [count for _, count in row_stats]

def vertical_adjacent(
    top_rows: List[List[Tuple]],
    x_thresh: float = 0.05,
    y_thresh: float = 0.05,
    min_matches: int = 2,
):
    """
    Gom cac row top_face thanh cac zone doc theo truc Y.
    
    Args
    ----
    top_rows   : List[List[Box]]
    x_thresh   : nguong sai khac x de coi hai goc trung nhau
    y_thresh   : nguong sai khac y
    min_matches: so cap goc khop toi thieu de xem la lien ke
    
    Returns
    -------
    zones : List[List[int]]
        Moi phan tu la mot zone, chua cac index row
        (tinh tren mang top_rows = top_rows + rotated_rows)
    """
    # --- Gop tat ca row lai de xu ly ---
    
    n_rows   = len(top_rows)
    if n_rows == 0:
        return []
    
    # --- Thu thap top/bot corners cua tung row ---
    bot_corners = []  # list[list[(x,y)]]
    top_corners = []
    for row in top_rows:
        bot_pts, top_pts = [], []
        for _, _, _, corners in row:
            # corners = [top_left, top_right, bottom_right, bottom_left]
            top_pts.extend([corners[0], corners[1]])
            bot_pts.extend([corners[2], corners[3]])
        bot_corners.append(bot_pts)
        top_corners.append(top_pts)
    
    # --- Xay dung ma tran lien ke ---
    adj = {i: set() for i in range(n_rows)}
    for i in range(n_rows):
        for j in range(i + 1, n_rows):
            matches = 0
            for bx, by in bot_corners[i]:
                for tx, ty in top_corners[j]:
                    if abs(bx - tx) <= x_thresh and abs(by - ty) <= y_thresh:
                        matches += 1
                        if matches >= min_matches:
                            adj[i].add(j)
                            adj[j].add(i)
                            break
                if matches >= min_matches:
                    break
    
    # --- Union‑Find de gom zone ---
    parent = list(range(n_rows))
    def find(u):
        while parent[u] != u:
            parent[u] = parent[parent[u]]
            u = parent[u]
        return u
    def union(u, v):
        pu, pv = find(u), find(v)
        if pu != pv:
            parent[pv] = pu
    
    for i, nbrs in adj.items():
        for j in nbrs:
            union(i, j)
    
    zones_dict = {}
    for idx in range(n_rows):
        root = find(idx)
        zones_dict.setdefault(root, []).append(idx)
    
    zones = [sorted(rows) for rows in zones_dict.values()]
    zones.sort(key=lambda z: z[0])  # sap xep theo row tren cung
    
    return zones

def group_front_top_by_layer(boxes_top_view, layer_counts: List[int], min_ratio: float = 0.6):
    """
    Gom các front_face (class 1) từ góc nhìn top_view thành từng tầng theo center_y,
    và bỏ các box có chiều cao quá nhỏ so với median.

    Args:
        boxes_top_view: dict từ read_yoloseg(top_view)
        layer_counts: List[int], số hộp trên từng tầng front_view (từ trên xuống). Ví dụ [5, 4]
        min_ratio: float, nếu h < median * min_ratio thì bỏ qua

    Returns:
        List[List[Box]]: danh sách các layer chứa front_face từ top_view
    """
    front_faces = boxes_top_view.get(1, [])
    if not front_faces:
        return []

    # === Tính median chiều cao ===
    heights = [b[2][3] for b in front_faces]
    if not heights:
        return []

    median_h = np.median(heights)

    # === Lọc các box có h quá nhỏ ===
    filtered = [b for b in front_faces if b[2][3] >= median_h * min_ratio]

    # Sắp xếp theo center_y tăng dần (tầng trên cùng y nhỏ hơn)
    filtered.sort(key=lambda b: b[2][1])

    grouped_layers = []
    start_idx = 0
    for count in layer_counts:
        layer = filtered[start_idx: start_idx + count]
        if len(layer) < count:
            print(f"[WARNING] Not enough front faces for expected count {count}")
        grouped_layers.append(layer)
        start_idx += count

    return grouped_layers

def count_top_above_front(front_layer, top_faces) -> List[int]:
    """
    Với mỗi front trong layer, đếm số top_face nằm trong vùng:
    - x thuộc [fx - 0.5, fx + 0.5]
    - y thuộc [0, fy]
    
    Args:
        front_layer: List[Box], các front_face trong một layer
        top_faces: List[Box], toàn bộ top_face

    Returns:
        List[int]: số top_face phía trên tương ứng với từng front
    """
    
    counts = []
    counted = set()  # Lưu index của các top đã được đếm

    for front in front_layer:
        fx, fy, fw = front[2][0], front[2][1], front[2][2]
        x_min = round(fx - 0.7 * fw, 4)
        x_max = round(fx + 0.7 * fw, 4)
        y_max = fy  # y_min = 0

        count = 0
        for idx, top in enumerate(top_faces):
            if idx in counted:
                continue
            tx, ty = top[2][0], top[2][1]
            if x_min <= tx <= x_max and ty <= y_max:
                count += 1
                counted.add(idx)

        counts.append(count)
    return counts
# ======================================================
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

def miss_front(boxes_by_class):
    """
    Kiểm tra:
    - Các full_box (nếu có) nằm trên một hàng duy nhất (tức là không thiếu hàng)
    - Dựa trên front-face của full_box để tính chiều dài hàng

    Trả về:
        Tuple: (missing: bool, reason: str)
    """
    boxes_with_full_boxes = create_full_boxes(boxes_by_class)
    top_boxes = boxes_with_full_boxes.get(0, [])
    front_boxes = boxes_with_full_boxes.get(1, [])
    full_boxes = boxes_with_full_boxes.get(2, [])

    if not top_boxes or not front_boxes:
        return True, "Missing top/front boxes"

    if full_boxes:
        full_rows= group_and_sort_boxes(full_boxes)
        if len(full_rows) != 1:
            print("full_rows:")
            for idx, row in enumerate(full_rows):
                print(f" Row {idx}:")
                for box in row:
                    print(f"   - center_x = {box[2][0]:.4f}, center_y = {box[2][1]:.4f}, area = {box[1]:.4f}, w = {box[2][2]:.4f}, h = {box[2][3]:.4f}")
            return True, f"{len(full_rows)} rows of full_box"

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
            return True, "Missing box in row"

    # return miss_top(boxes_by_class)
    return False, "!!"

def miss_top(boxes_by_class, top_zone_threshold=0.85):
    """
    Kiểm tra kiện hàng có đầy đủ từ góc nhìn mặt trên (top-face).
    Dựa trên: diện tích top-face / diện tích hình chữ nhật bao quanh full_boxes.

    Returns:
        (missing: bool, reason: str)
    """
    boxes_with_full_boxes = create_full_boxes(boxes_by_class)
    full_boxes = boxes_with_full_boxes.get(2, [])
    top_boxes = boxes_by_class.get(0, [])

    if not top_boxes:
        return True, "Missing top_face"
    if not full_boxes:
        return True, "No full_boxes created"

    # Lấy hộp đầu và cuối trong danh sách full_box đã được gom hàng
    full_rows= group_and_sort_boxes(full_boxes)
    if not full_rows:
        return True, "Cannot group full_boxes"

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

    if filled_ratio >= top_zone_threshold:
        return False, f"Top full {filled_ratio:.4f}"
    else:
        return True, f"Top not full {filled_ratio:.4f}"
 
   
 
   
# === CHỌN FILE ===
top_view, _, front_view = find_file(FOLDER_PATH)
print(f"Selected file: {top_view}, {front_view}")
if top_view is None or front_view is None:
    print("[ERROR] File not found.")
else:
    # === ĐỌC NỘI DUNG FILE ===
    boxes_top_view = read_yoloseg(top_view)
    boxes_front_view = read_yoloseg(front_view)
    

    # === XỬ LÝ TOP FACE (class 0) ===
    top_boxes = boxes_top_view.get(0, [])
    print("\n=== DIỆN TÍCH CÁC HỘP TOP ===")
    for i, box in enumerate(top_boxes):
        print(f"Top box {i:02d}: area = {box[1]:.5f}, center = ({box[2][0]:.4f}, {box[2][1]:.4f})")

    # Gom nhóm
    tops= group_and_sort_boxes(top_boxes)
    top_count = len(top_boxes)
    print("\n=== TOP FACE: NHÓM CHÍNH ===")
    print(f"Tổng số top_face: {top_count}")
    print(f"Số hàng top_face: {len(tops)}")

    for row_idx, row in enumerate(tops):
        print(f" Row {row_idx} count: {len(row)}")
        for b in row:
            print(f"   - center_x = {b[2][0]:.4f}, center_y = {b[2][1]:.4f}, area = {b[1]:.4f}, w = {b[2][2]:.4f}, h = {b[2][3]:.4f}")
    
    print("\n=== TOP LAYER COUNT ===")
    
    layer_counts = count_front_layers(boxes_front_view)
    fronts_topview = boxes_top_view.get(1, [])
    fronts_topview_count = len(fronts_topview)
    print(f"Tổng số front_face: {fronts_topview_count}")
    print(f"Các layer front_view:" , layer_counts)
    
    front_layers_topview = group_front_top_by_layer(boxes_top_view, layer_counts[:3])
    for idx, layer in enumerate(front_layers_topview):
        print(f"\nLayer {idx} (count = {len(layer)})")
        for b in layer:
            print(f" - center_x = {b[2][0]:.4f}, center_y = {b[2][1]:.4f}, w = {b[2][2]:.4f}, h = {b[2][3]:.4f}, area = {b[1]:.4f}")

    # top_layers = detect_top_layers(tops)
    # print(f"Các layer top_face (detect): {top_layers}")
    zones = vertical_adjacent(tops)
    print(f"Các zone top_face (vertical_adjacent): {zones}")
    
    front_layer0 = sorted(front_layers_topview[0], key=lambda b: b[2][0])
    counts_above = count_top_above_front(front_layer0, top_boxes)
    for i, (b, c) in enumerate(zip(front_layer0, counts_above)):
        print(f"[Front {i}] center_x = {b[2][0]:.4f}, center_y = {b[2][1]:.4f}, width = {b[2][2]:.4f} → top_face phía trên = {c}")



    # === KIỂM TRA VÀ IN DEBUG ===
    missing, reason = miss_front(boxes_top_view)
    print("\n=== MISSING CHECK (TOP VIEW) ===")
    print(f"Missing ? {missing}")
    print(f"Reason  : {reason}")


