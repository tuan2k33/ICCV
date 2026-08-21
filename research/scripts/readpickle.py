
from collections import defaultdict
import os
import pickle
from pathlib import Path
from typing import Dict, List, Tuple, Union, Any

import cv2
import numpy as np
from shapely.geometry import Polygon
from sklearn.cluster import DBSCAN
from ultralytics.engine.results import Results  # type: ignore

# =======================================================
# HẰNG SỐ CẤU HÌNH
# =======================================================
TOP_Y_THRESHOLD = 0.05
FRONT_Y_THRESHOLD = 0.05
BOX_X_THRESHOLD = 0.1
BOX_Y_THRESHOLD = 0.1
AREA_THRESHOLD = 0.003

# Đường dẫn đến file pickle chứa kết quả inference
PICKLE_PATH = "/ssd1/tuannw/infer_result/31-05-252/results.pkl"
# =======================================================
# 1. HÀM TIỆN ÍCH CHUNG (TXT + PICKLE)
# =======================================================



def read_yoloseg_from_result(result: Results) -> Dict[int, List[Tuple]]:
    """Chuyển `Results` → boxes_by_class (giống format txt)."""
    boxes_by_class: Dict[int, List] = {}
    if result.masks is None:
        return boxes_by_class
    h, w = result.orig_shape  # (H, W)
    polys = result.masks.xy
    cls_ids = result.boxes.cls.cpu().numpy().astype(int)
    
    def _sort_corners_four_points(pts: np.ndarray) -> List[List[float]]:
        """Sắp xếp 4 điểm => [top_left, top_right, bottom_right, bottom_left]"""
        sorted_by_y = pts[np.argsort(pts[:, 1])]
        top2, bot2 = sorted_by_y[:2], sorted_by_y[2:]
        if top2[0, 0] < top2[1, 0]:
            tl, tr = top2[0], top2[1]
        else:
            tl, tr = top2[1], top2[0]
        if bot2[0, 0] < bot2[1, 0]:
            bl, br = bot2[0], bot2[1]
        else:
            bl, br = bot2[1], bot2[0]
        return [tl.tolist(), tr.tolist(), br.tolist(), bl.tolist()]


    for cls_id, poly_xy in zip(cls_ids, polys):
        pts = poly_xy.astype(np.float32)
        pts[:, 0] /= w
        pts[:, 1] /= h
        hull = cv2.convexHull(pts)
        epsilon = 0.01 * cv2.arcLength(hull, True)
        approx = cv2.approxPolyDP(hull, epsilon, True)
        while len(approx) > 4:
            epsilon *= 1.05
            approx = cv2.approxPolyDP(hull, epsilon, True)
            

        corners = _sort_corners_four_points(approx.reshape(-1, 2))
        corners = [[round(x, 4), round(y, 4)] for x, y in corners]
        tl, tr, br, bl = corners
        width = (np.linalg.norm(np.array(tr) - tl) + np.linalg.norm(np.array(br) - bl)) / 2
        height = (np.linalg.norm(np.array(bl) - tl) + np.linalg.norm(np.array(br) - tr)) / 2
        cx = np.mean([p[0] for p in corners])
        cy = np.mean([p[1] for p in corners])
        xywh = [round(cx, 4), round(cy, 4), round(width, 4), round(height, 4)]
        area = round(Polygon(corners).area, 4) if len(corners) == 4 else 0.0
        boxes_by_class.setdefault(cls_id, []).append((cls_id, area, xywh, corners))
    return boxes_by_class


# =======================================================
# 2. CÁC HÀM XỬ LÝ NHÓM, GHÉP, KIỂM TRA (GIỮ NGUYÊN)
# =======================================================

def group_and_sort_boxes(boxes, y_threshold=BOX_Y_THRESHOLD, area_threshold=AREA_THRESHOLD):
    if not boxes:
        return [], []
    class_id = boxes[0][0]
    if class_id == 0:  # TOP
        wh = np.array([b[2][2] / (b[2][3] if b[2][3] > 0 else 1e-6) for b in boxes])
        med = np.median(wh)
        normal, rare = [], []
        for b, r in zip(boxes, wh):
            if (med >= 1 and r < 1) or (med < 1 and r >= 1):
                rare.append(b)
            else:
                normal.append(b)
        rows = []
        if normal:
            areas = np.array([[b[1]] for b in normal])
            labels = DBSCAN(eps=area_threshold, min_samples=1).fit(areas).labels_
            grouped = {}
            for idx, lb in enumerate(labels):
                grouped.setdefault(lb, []).append(normal[idx])
            for g in grouped.values():
                cys = np.array([b[2][1] for b in g])
                mean_cy = cys.mean()
                keep = [b for b in g if abs(b[2][1] - mean_cy) <= TOP_Y_THRESHOLD]
                if keep:
                    keep.sort(key=lambda b: b[2][0])
                    rows.append(keep)
            rows.sort(key=lambda row: np.mean([b[2][1] for b in row]))
        # rare xử lý đơn giản: trả list rare nhưng không chen hàng.
        return rows, rare
    else:  # FRONT hoặc FULL
        if class_id == 1:
            y_threshold = FRONT_Y_THRESHOLD
        y = np.array([[b[2][1]] for b in boxes])
        labels = DBSCAN(eps=y_threshold, min_samples=1).fit(y).labels_
        grouped = {}
        for idx, lb in enumerate(labels):
            grouped.setdefault(lb, []).append(boxes[idx])
        rows = []
        for g in grouped.values():
            g.sort(key=lambda b: b[2][0])
            rows.append((np.mean([b[2][1] for b in g]), g))
        rows.sort(key=lambda r: r[0])
        return [r[1] for r in rows], []


def create_full_boxes(boxes_by_class, x_threshold=BOX_X_THRESHOLD, y_threshold=BOX_Y_THRESHOLD):
    top = boxes_by_class.get(0, [])
    front = boxes_by_class.get(1, [])
    full, used = [], set()
    for i_f, f in enumerate(front):
        fx, fy, fw, fh = f[2]
        fy_top = fy - fh / 2
        best, best_y = -1, 1e9
        for i_t, t in enumerate(top):
            if i_t in used:
                continue
            tx, ty, _, th = t[2]
            ty_bot = ty + th / 2
            if abs(fx - tx) <= x_threshold and abs(fy_top - ty_bot) <= y_threshold:
                if abs(fy_top - ty_bot) < best_y:
                    best, best_y = i_t, abs(fy_top - ty_bot)
        if best != -1:
            t = top[best]
            used.add(best)
            area = round(t[1] + f[1], 4)
            w_full = fw
            h_full = round(t[2][3] + fh, 4)
            full.append((2, area, [fx, fy, w_full, h_full], [t, f]))
    if full:
        boxes_by_class[2] = full
    elif 2 in boxes_by_class:
        boxes_by_class.pop(2)
    return boxes_by_class

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
        full_rows, _ = group_and_sort_boxes(full_boxes)
        print(f"Full rows: {full_rows}")
        if len(full_rows) != 1:
            return True, ">1 rows of full_box"

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
def miss_top(boxes_by_class, area_threshold=0.85):
    boxes_with_full = create_full_boxes(dict(boxes_by_class))
    full = boxes_with_full.get(2, [])
    top_boxes = boxes_by_class.get(0, [])
    if not top_boxes or not full:
        return True, "Missing top/full boxes"
    rows, _ = group_and_sort_boxes(full)
    if not rows:
        return True, "Cannot group full_boxes"
    first, last = rows[0][0], rows[0][-1]
    quad = [first[3][0], first[3][3], last[3][2], last[3][1]]
    poly = Polygon(quad)
    full_area = poly.area if poly.is_valid else 0.0
    total_top = sum(b[1] for b in top_boxes)
    ratio = total_top / full_area if full_area else 0.0
    return (ratio < area_threshold), f"Top ratio {ratio:.4f}"

# (miss_front giữ nguyên logic cũ nếu cần)

# =======================================================
# 3. CHỌN VIEW TỪ LIST RESULTS (PICKLE)
# =======================================================

def find_views_from_results(image_paths: List[str], path2result: Dict[str, Results]) -> Dict[str, Dict[str, Any]]:
    """
    Gom nhóm ảnh theo kiện hàng từ image_paths, và chọn 3 góc nhìn:
        - front: ảnh có diện tích mặt trước lớn nhất
        - top  : ảnh có diện tích mặt trên lớn nhất (trừ ảnh front)
        - bird : còn lại, ưu tiên ảnh có front lớn nhất; nếu không có thì = top

    Ngoài ra trả về cả các file thừa trong 'others'.

    Returns
    -------
    Dict[kien_hang_name] = {
        "top": str,
        "front": str,
        "bird": str,
        "others": List[str],
    }
    """

    def _compute_areas(res: Results) -> tuple[float, float]:
        """Tính tổng diện tích top-face và front-face trong 1 Results."""
        boxes = read_yoloseg_from_result(res)
        top_area   = sum(Polygon(b[3]).area for b in boxes.get(0, []))
        front_area = sum(Polygon(b[3]).area for b in boxes.get(1, []))
        return top_area, front_area

    # 1. Gom nhóm theo tên kiện
    grouped: Dict[str, List[str]] = defaultdict(list)
    for p in image_paths:
        stem = Path(p).stem         # 'AZ - 003 - 1_(1)'
        pkg  = stem.split("_")[0]   # 'AZ - 003 - 1'
        grouped[pkg].append(p)

    selected: Dict[str, Dict[str, Any]] = {}

    for pkg, paths in grouped.items():
        candidates = []
        for p in paths:
            res = path2result[p]
            top_a, front_a = _compute_areas(res)
            candidates.append({
                "path": p,
                "top":  top_a,
                "front": front_a,
            })

        # ---- 1. Chọn front view ----
        no_top = [c for c in candidates if c["top"] == 0]
        if no_top:
            front = max(no_top, key=lambda c: c["front"])
            candidates.remove(front)
        else:
            front = max(candidates, key=lambda c: c["front"])
            candidates.remove(front)

        # ---- 2. Chọn top view ----
        if candidates:
            top = max(candidates, key=lambda c: c["top"])
            candidates.remove(top)
        else:
            top = front

        # ---- 3. Chọn bird view ----
        if candidates:
            bird = max(candidates, key=lambda c: c["front"])
            candidates.remove(bird)
        else:
            bird = top

        others = [c["path"] for c in candidates]

        selected[pkg] = {
            "top": top["path"],
            "bird": bird["path"],
            "front": front["path"],
            "others": others,
        }

    return selected
# =======================================================
# 4. MAIN TEST – LOAD PICKLE TRONG 1 FOLDER
# =======================================================



with open(PICKLE_PATH, "rb") as f:
    results: List[Results] = pickle.load(f)

path2res = {r.path: r for r in results}
image_paths = list(path2res.keys())

packages = find_views_from_results(image_paths, path2res)

# In kết quả
for pkg, views in packages.items():
    print(f"\n[{pkg}]")
    for k in ['front', 'top', 'bird']:
        print(f"  {k:7} : {views[k]}")
    if views["others"]:
        print("  others  :", [p for p in views["others"]])

    top_path = views.get("top")

    # Lấy lại Results object
    top_res = path2res[top_path]

    # Chỉ lấy boxes của class 0 (top-face)
    boxes_by_class = read_yoloseg_from_result(top_res)
    # Gọi miss_front
    miss, msg = miss_front(boxes_by_class)
    print(f"  Missing : {miss}, {msg}")