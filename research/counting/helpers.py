import numpy as np
import cv2
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt
from collections import deque
import math
from logics import *

def draw_bboxes(image, positives, negatives, matches, filename):
    """
    Draw bounding boxes and matches on an image.
    - Positives: Green
    - Negatives: Red
    - Matches: Blue lines
    """
    positives = positives.astype(np.uint32)
    negatives = negatives.astype(np.uint32)
    for (x1, y1, x2, y2) in positives:
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)  # Green for positives

    for (x1, y1, x2, y2) in negatives:
        x1, y1, x2, y2 = list(map(lambda x: int(x), [x1, y1, x2, y2]))
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 0, 255), 2)  # Red for negatives

    # Draw matches as blue lines
    for pos_idx, neg_idx in matches.items():
        x1_p, y1_p, x2_p, y2_p = positives[pos_idx]
        x1_n, y1_n, x2_n, y2_n = negatives[neg_idx]

        center_pos = ((x1_p + x2_p) // 2, (y1_p + y2_p) // 2)
        center_neg = ((x1_n + x2_n) // 2, (y1_n + y2_n) // 2)

        cv2.line(image, center_pos, center_neg, (255, 0, 0), 2)  # Blue line for match

    cv2.imwrite(filename, image)


def compute_x_overlap(bbox1, bbox2):
    """Compute x-axis overlap between two bounding boxes."""
    x1_1, _, x2_1, _ = bbox1
    x1_2, _, x2_2, _ = bbox2
    return max(0, min(x2_1, x2_2) - max(x1_1, x1_2))

def compute_y_center(bbox):
    """Compute y-axis center of a bounding box."""
    return (bbox[1] + bbox[3]) / 2

def compute_vertical_gap(pos_bbox, neg_bbox):
    """Compute vertical gap between pos_bbox.y1 and neg_bbox.y2."""
    return abs(pos_bbox[1] - neg_bbox[3])

def find_best_matches(positives, negatives, top_k=3):
    """Find best matches between positive and negative bounding boxes."""
    matches = {}
    for i, pos_bbox in enumerate(positives):
        candidates = []

        for j, neg_bbox in enumerate(negatives):
            x_overlap = compute_x_overlap(pos_bbox, neg_bbox)
            if x_overlap == 0:
                continue  # No overlap in x-axis

            pos_y_center = compute_y_center(pos_bbox)
            neg_y_center = compute_y_center(neg_bbox)

            if neg_y_center >= pos_y_center:
                continue  # Negative must be above positive

            vertical_gap = compute_vertical_gap(pos_bbox, neg_bbox)

            # Store candidate (negative index, x_overlap, vertical_gap)
            candidates.append((j, x_overlap, vertical_gap))

        # Sort by x_overlap (desc) and vertical_gap (asc)
        candidates.sort(key=lambda x: (-x[1], x[2]))

        # Choose the best match among the top-K candidates
        if candidates:
            best_match = min(candidates[:top_k], key=lambda x: x[2])[0]
            matches[i] = best_match  # Map positive[i] -> negative[best_match]

    return matches

def filter_small_bboxes(bboxes, threshold=0.6):
    # Sort bounding boxes by y1 (ascending order)
    bboxes = bboxes[np.argsort(bboxes[:, 1])]
    
    # Compute areas (width * height)
    areas = (bboxes[:, 2] - bboxes[:, 0]) * (bboxes[:, 3] - bboxes[:, 1])
    
    # Get indices of two smallest area boxes
    smallest_indices = np.argsort(areas)[:2]
    
    # Get index of the third smallest area box
    third_index = np.argsort(areas)[2]
    
    # Check condition: if sum of two smallest areas is less than 0.6 * third box area
    if np.sum(areas[smallest_indices]) <  threshold * areas[third_index]:
        bboxes = np.delete(bboxes, smallest_indices, axis=0)
        return bboxes  # Return indices of two smallest area boxes
    
    return bboxes  # If condition is not met, return None

# def convert_bbox_xyxy_to_xywh(bboxes):
#     """
#     Convert bounding boxes from [x1, y1, x2, y2, conf, cls_id] 
#     to [x, y, w, h, conf, cls_id].
    
#     x = x1
#     y = y1
#     w = x2 - x1
#     h = y2 - y1
#     """
#     converted_bboxes = np.copy(bboxes)
#     converted_bboxes[:, 2] = bboxes[:, 2] - bboxes[:, 0]  # width = x2 - x1
#     converted_bboxes[:, 3] = bboxes[:, 3] - bboxes[:, 1]  # height = y2 - y1
#     return converted_bboxes

def convert_bbox_xyxy_to_xywh(bboxes):
    """
    Convert bounding boxes from [x1, y1, x2, y2, conf, cls_id] 
    to [x_center, y_center, w, h, conf, cls_id] using NumPy.

    Args:
        bboxes: np.ndarray of shape (N, 6)

    Returns:
        np.ndarray of shape (N, 6)
    """
    bboxes = np.asarray(bboxes)
    x_center = (bboxes[:, 0] + bboxes[:, 2]) / 2
    y_center = (bboxes[:, 1] + bboxes[:, 3]) / 2
    w = bboxes[:, 2] - bboxes[:, 0]
    h = bboxes[:, 3] - bboxes[:, 1]
    
    converted = np.stack((x_center, y_center, w, h, bboxes[:, 4], bboxes[:, 5]), axis=1)
    return converted


def area(box):
    return (box[2] - box[0]) * (box[3] - box[1])

def is_inside(box_small, box_large, threshold=0.8):
    # Tính giao giữa box_small và box_large
    x1 = max(box_small[0], box_large[0])
    y1 = max(box_small[1], box_large[1])
    x2 = min(box_small[2], box_large[2])
    y2 = min(box_small[3], box_large[3])

    w = max(0, x2 - x1)
    h = max(0, y2 - y1)
    intersection_area = w * h

    small_area = area(box_small)

    if small_area == 0:
        return False

    # Tính tỷ lệ diện tích giao / diện tích box nhỏ
    ratio = intersection_area / small_area

    # Kiểm tra xem box_small có nằm đủ trong box_large không
    return ratio >= threshold

# def remove_nested_boxes(boxes, threshold=0.8):
#     boxes = sorted(boxes, key=lambda x: area(x), reverse=True)  # sắp xếp theo diện tích giảm dần
#     kept_boxes = []

#     for i, box in enumerate(boxes):
#         should_keep = True
#         for kept_box in kept_boxes:
#             if is_inside(box, kept_box, threshold):
#                 should_keep = False
#                 break
#         if should_keep:
#             kept_boxes.append(box)

#     return np.array(kept_boxes)

def compute_iou(boxA, boxB):
    # Tính vùng giao nhau
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    inter_w = max(0, xB - xA)
    inter_h = max(0, yB - yA)
    inter_area = inter_w * inter_h

    # Diện tích của từng box
    areaA = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    areaB = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])

    # Tính IoA theo box nhỏ hơn
    smaller_area = min(areaA, areaB)
    if smaller_area == 0:
        return 0
    ioa = inter_area / smaller_area
    return ioa

def remove_overlapping_boxes(boxes, masks, ioa_thresh=0.5):
    keep_indices = set(range(len(boxes)))

    for i in range(len(boxes)):
        if i not in keep_indices:
            continue
        box_i = boxes[i]
        cls_i = box_i[5]
        area_i = (box_i[2] - box_i[0]) * (box_i[3] - box_i[1])

        for j in range(i + 1, len(boxes)):
            if j not in keep_indices:
                continue
            box_j = boxes[j]
            cls_j = box_j[5]

            if cls_i != cls_j:
                continue

            area_j = (box_j[2] - box_j[0]) * (box_j[3] - box_j[1])
            ioa = compute_iou(box_i, box_j)

            if ioa > ioa_thresh:
                # Xóa box nhỏ hơn
                if area_i < area_j:
                    keep_indices.discard(i)
                    break  # i bị loại, không cần so tiếp
                else:
                    keep_indices.discard(j)

    # Trả về boxes và masks sau khi lọc
    keep_indices = sorted(list(keep_indices))
    boxes_filtered = boxes[keep_indices]
    masks_filtered = [masks[i] for i in keep_indices]
    return boxes_filtered, masks_filtered

def get_x_min_x_max(boxes):
    # Chuyển list sang numpy array nếu cần
    if isinstance(boxes, list):
        boxes = np.array(boxes)
    
    # Giả sử boxes có shape (N, 6) hoặc (1, N, 6), ta reshape về (số_box, 6)
    boxes = boxes.reshape(-1, 6)

    x1s = boxes[:, 0]  # tất cả x1
    x2s = boxes[:, 2]  # tất cả x2

    x_min = float(np.min(x1s))
    x_max = float(np.max(x2s))

    return x_min, x_max

def get_min_width_box(boxes):
    """
    Tìm box có chiều rộng nhỏ nhất (x2 - x1)
    
    :param boxes: list hoặc numpy array chứa các box dạng [x1, y1, x2, y2, ...]
    :return: box có chiều rộng nhỏ nhất
    """
    # Chuyển sang numpy array nếu cần
    if not isinstance(boxes, np.ndarray):
        boxes = np.array(boxes)

    # Giả sử boxes có shape (N, 6) hoặc tương tự
    widths = boxes[:, 2] - boxes[:, 0]  # Tính x2 - x1 cho từng box
    min_index = np.argmin(widths)      # Tìm chỉ số của box có chiều rộng nhỏ nhất

    return boxes[min_index]

def filter_negative_boxes(negative_boxes, n_masks, threshold=0.5):
    mask_with_area = []

    # Step 1: extract convex 4-point polygon and compute area
    for idx, mask in enumerate(n_masks):
        area = cv2.contourArea(mask)
        mask_with_area.append((idx, area))

    # Step 2: sort by area ascending
    mask_with_area.sort(key=lambda x: x[1])
    # Sử dụng median thay cho avg
    areas = [area for _, area in mask_with_area]
    median_area = np.median(areas)

    # Step 3: filter masks
    keep_indices = set(i for i, _ in mask_with_area)
    for i in range(len(mask_with_area) - 1):
        idx_cur, area_cur = mask_with_area[i]
        if area_cur < 0.3 * median_area:
            keep_indices.discard(idx_cur)
            continue
        # _, area_next = mask_with_area[i + 1]
        # # print(area_cur / area_next, area_cur / avg_area)
        # if area_cur < threshold * area_next:
        #     keep_indices.discard(idx_cur)

    # Step 4: return filtered n_masks
    filtered_masks = [n_masks[i] for i in sorted(keep_indices)]
    filtered_boxes = [negative_boxes[i] for i in sorted(keep_indices)]
    remove_masks = [n_masks[i] for i in range(len(negative_boxes)) if i not in sorted(keep_indices)]
    remove_boxes = [negative_boxes[i] for i in range(len(negative_boxes)) if i not in sorted(keep_indices)]
    return filtered_boxes, filtered_masks, remove_boxes, remove_masks, mask_with_area, median_area






def interpolate_boundary(filtered_data, filter_data_masks, target_class_idx=1):
    """
    Nội suy tuyến tính để tạo đường boundary dựa trên class 0,
    loại bỏ các đoạn có góc đi xuống quá 60 độ.

    Args:
        filtered_data: Dữ liệu sau khi lọc.
        filter_data_masks: Mặt nạ tương ứng với filtered_data.
        target_class_idx: Lớp mục tiêu để xác định điểm nằm trên hoặc dưới boundary.

    Returns:
        filtered_data_accept: Dữ liệu sau khi lọc theo boundary.
        filtered_data_ingore: Dữ liệu bị loại bỏ.
        filtered_data_masks_accept: Mặt nạ tương ứng với filtered_data_accept.
        filtered_data_masks_ignore: Mặt nạ tương ứng với filtered_data_ingore.
        bx: Danh sách tọa độ x của boundary.
        by: Danh sách tọa độ y của boundary.
        num_front_face_in_line: Số lượng class 0 gần đường nội suy.
        filtered_data_class_ids_accept: Class ID tương ứng với filtered_data_masks_accept.
    """

    padding = 100

    # Lấy danh sách các điểm class 0
    pos_points = [(x, y, w, h) for x, y, w, h, conf, class_id in filtered_data if class_id == 1 - target_class_idx]
    if not pos_points:
        return filtered_data, None, None, None, None, None, 0, []

    # Sắp xếp theo x
    pos_points = sorted(pos_points, key=lambda x: x[0])

    # Lọc các điểm có đoạn đi xuống quá 60 độ
    filtered_pos_points = [pos_points[0]]
    for i in range(1, len(pos_points)):
        x1, y1, w1, h1 = filtered_pos_points[-1]
        x2, y2, w2, h2 = pos_points[i]
        dx = x2 - x1
        dy = y2 - y1
        if dx > 0:
            angle = np.degrees(np.arctan(dy / dx))
            if angle > -90 and angle < 90:
                filtered_pos_points.append((x2, y2, w2, h2))

    # Tạo boundary points với mỗi pos_point sẽ có thêm điểm đầu (x - w/2, y)
    boundary_points = []
    for x, y, w, h in filtered_pos_points:
        
        # Only append left boundary if it's greater than the previous right boundary
        if (len(boundary_points) == 0) or (x - w / 4 > boundary_points[-1][0]):
            boundary_points.append((x - w / 4, y))

        # Rule for previous right boundary
        if (x < boundary_points[-1][0]):
            boundary_points.pop()
        
        # Always append the x y boundary   
        boundary_points.append((x, y))
        boundary_points.append((x + w / 4, y))
    # Thêm điểm cuối cùng mở rộng bên phải
    # x_last, y_last, w_last, h_last = filtered_pos_points[-1]
    # boundary_points.append((x_last + w_last / 2 + padding, y_last))

    bx, by = zip(*boundary_points)

    x_min_true = min([pt[0] for pt in boundary_points]) - padding
    x_max_true = max([pt[0] for pt in boundary_points]) + padding

    interp_func = interp1d(bx, by, kind="linear", fill_value="extrapolate")

    # Đếm các class đối diện gần đường nội suy
    front_face_in_line = [
        obj for obj in filtered_data
        if obj[5] == 1 - target_class_idx and (
            -50 <= (obj[1] - interp_func(obj[0])) <= 50
            )
    ]
    num_front_face_in_line = len(front_face_in_line)

    # Phân loại dữ liệu
    filtered_data_accept = []
    filtered_data_ingore = []
    filtered_data_masks_accept = []
    filtered_data_masks_ignore = []
    filtered_data_class_ids_accept = []

    for idx, obj in enumerate(filtered_data):
        if obj[5] != target_class_idx or (
            obj[1] <= interp_func(obj[0]) and (x_min_true <= obj[0] <= x_max_true)
        ):
            filtered_data_accept.append(obj)
            filtered_data_masks_accept.append(filter_data_masks[idx])
            filtered_data_class_ids_accept.append(obj[5])
        else:
            filtered_data_ingore.append(obj)
            filtered_data_masks_ignore.append(filter_data_masks[idx])

    return (
        filtered_data_accept,
        filtered_data_ingore,
        filtered_data_masks_accept,
        filtered_data_masks_ignore,
        list(bx),
        list(by),
        num_front_face_in_line,
        filtered_data_class_ids_accept
    )

def plot_filtered_data(
    filtered_data, bx=None, by=None
):
    """
    Vẽ biểu đồ với các điểm đã lọc và đường boundary.

    Args:
        filtered_data: Dữ liệu sau khi lọc.
        bx: Tọa độ x của boundary.
        by: Tọa độ y của boundary.
    """
    plt.figure(figsize=(8, 8))
    ax = plt.gca()

    # Vẽ các điểm class 0 và class 1
    for x, y, w, h, conf, class_id in filtered_data:
        color = "red" if class_id == 0 else "blue"
        plt.scatter(x, y, color=color, label=f"Class {class_id}" if f"Class {class_id}" not in ax.get_legend_handles_labels()[1] else "")
        plt.text(x, y, f"{class_id}", color=color, fontsize=12, bbox=dict(facecolor="white", alpha=0.5))

    # Vẽ đường boundary nếu có
    if bx and by:
        plt.plot(bx, by, "r-", linewidth=2)

    # Thiết lập biểu đồ
    ax.set_xlim(0, 4000)
    ax.set_ylim(0, 4000)
    ax.invert_yaxis()
    plt.xlabel("X Coordinate")
    plt.ylabel("Y Coordinate")
    plt.title("Filtered Object Locations with Closed Red Boundary")
    plt.legend()
    plt.grid(True)
    plt.show()

def check_spacing_between_boxes(boxes, threshold=0.6):
    """
    boxes: list of [x1, y1, x2, y2]
    Return False if any adjacent box pair has spacing > 0.6 * min(box width)
    """
    if len(boxes) < 2:
        return True

    boxes_sorted = sorted(boxes, key=lambda b: b[0])

    # Tính chiều rộng của từng box
    widths = [b[2] - b[0] for b in boxes_sorted]
    min_width = min(widths)

    for i in range(len(boxes_sorted) - 1):
        x2_left = boxes_sorted[i][2]
        x1_right = boxes_sorted[i + 1][0]
        distance = x1_right - x2_left
        # print(distance / min_width)
        if distance > threshold * min_width:
            return False

    return True


def compute_covered_x_distance(boxes):
    """
    Tính tổng khoảng cách trục x được bao phủ bởi các bbox (loại trừ vùng giao).
    
    Args:
        boxes: np.ndarray (N, 6) — mỗi hàng: [x1, y1, x2, y2, conf, class_id]
        
    Returns:
        total_covered: float — tổng chiều dài trục x đã được cover
        x_min: float — nhỏ nhất trong x1
        x_max: float — lớn nhất trong x2
    """
    if len(boxes) == 0:
        return 0, 0, 0

    # Tạo danh sách [x1, x2]
    intervals = [(min(b[0], b[2]), max(b[0], b[2])) for b in boxes]

    # Sắp xếp theo x1
    intervals.sort(key=lambda x: x[0])

    # Gộp các đoạn giao nhau
    merged = []
    start, end = intervals[0]

    for curr_start, curr_end in intervals[1:]:
        if curr_start <= end:  # giao nhau
            end = max(end, curr_end)
        else:
            merged.append((start, end))
            start, end = curr_start, curr_end
    merged.append((start, end))

    # Tổng chiều dài đã cover
    total_covered = sum(e - s for s, e in merged)
    x_min = min(i[0] for i in intervals)
    x_max = max(i[1] for i in intervals)

    return total_covered, x_min, x_max





def extract_bottom_x_range(poly_points):
    """
    Extract x-range [x1, x2] from the two bottom-most points of a polygon.
    """
    pts = np.array(poly_points, dtype=np.float32)
    
    # Get convex 4-point approx
    hull = cv2.convexHull(pts)
    epsilon = 0.01 * cv2.arcLength(hull, True)
    approx = cv2.approxPolyDP(hull, epsilon, True)

    while len(approx) > 4:
        epsilon *= 1.05
        approx = cv2.approxPolyDP(hull, epsilon, True)

    if len(approx) < 4:
        raise Exception("Cannot find 4 point when for bbox.")

    approx = approx.reshape(-1, 2)

    # Get two points with largest y (bottom-most)
    sorted_by_y = sorted(approx, key=lambda p: p[1], reverse=True)
    bottom_pts = sorted_by_y[:2]
    x_coords = [p[0] for p in bottom_pts]
    return min(x_coords), max(x_coords)

def compute_covered_x_distance_from_polygons(polygons):
    """
    Tính tổng khoảng cách trục x được bao phủ bởi các polygon (loại trừ vùng giao).

    Args:
        polygons: list of np.ndarray (N, 4, 2) — 4 điểm của mỗi polygon

    Returns:
        total_covered: float
        x_min: float
        x_max: float
    """
    intervals = []
    for poly in polygons:
        result = extract_bottom_x_range(poly)
        if result is not None:
            intervals.append(result)

    if not intervals:
        return 0, 0, 0

    # Sắp xếp và merge
    intervals.sort(key=lambda x: x[0])
    merged = []
    start, end = intervals[0]
    
    for curr_start, curr_end in intervals[1:]:
        if curr_start <= end:
            end = max(end, curr_end)
        else:
            merged.append((start, end))
            start, end = curr_start, curr_end
    merged.append((start, end))

    total_covered = sum(e - s for s, e in merged)
    x_min = min(i[0] for i in intervals)
    x_max = max(i[1] for i in intervals)

    return total_covered, x_min, x_max


def filter_data_below_front_face(boxes, threshold=0.85):
    """
    Remove class 0 boxes that are under class 1 boxes and horizontally overlap > threshold.

    Args:
        boxes: np.ndarray (N, 6): each row = [xc, yc, w, h, conf, class_id]
        threshold: float: overlap ratio along x to consider

    Returns:
        filtered_boxes: np.ndarray
    """
    boxes = np.array(boxes)
    keep_mask = np.ones(len(boxes), dtype=bool)

    for i, box_A in enumerate(boxes):
        if int(box_A[5]) != 0:
            continue  # only check class 0

        xA, yA, wA, _, _, _ = box_A
        xA1 = xA - wA / 2
        xA2 = xA + wA / 2

        for j, box_B in enumerate(boxes):
            if int(box_B[5]) != 1:
                continue  # only compare with class 1

            xB, yB, wB, _, _, _ = box_B
            xB1 = xB - wB / 2
            xB2 = xB + wB / 2

            # A nằm dưới B
            if yA <= yB:
                continue

            # tính overlap trục x
            x_overlap = max(0, min(xA2, xB2) - max(xA1, xB1))
            min_width = min(wA, wB)

            if min_width > 0 and x_overlap / min_width > threshold:
                keep_mask[i] = False
                break  # không cần xét thêm

    return boxes[keep_mask]




# # Example Usage
# positives = [(100, 200, 300, 400), (50, 150, 250, 350)]
# negatives = [(90, 100, 200, 190), (120, 80, 280, 180), (30, 120, 220, 170), (60, 90, 290, 180)]

# matches = find_best_matches(positives, negatives)
# print(matches)  # Output: {0: best_matching_negative_index, 1: best_matching_negative_index}



def get_center(corners):
    return np.mean(np.array(corners), axis=0)

def euclidean(p1, p2):
    return np.linalg.norm(np.array(p1) - np.array(p2))

def find_all_upper_layers_by_mask(initial_masks, all_masks, threshold=30, min_overlap_ratio=0.3):
    visited_global = set()
    result_all = []
    move_all = []

    def corner_key(corners):
        return tuple(map(tuple, corners))
    initial_masks = sorted(initial_masks, key=lambda m: get_center(m)[0])
    for init_mask in initial_masks:
        queue = deque([init_mask])
        visited_local = set()
        move = []
        local_result = []

        while queue:
            current = queue.popleft()
            key = corner_key(current)
            if key in visited_local or key in visited_global:
                continue

            visited_local.add(key)
            visited_global.add(key)
            local_result.append(current)

            tl, tr, br, bl = current[0], current[1], current[2], current[3]
            center_cur = get_center(current)
            width_cur = np.linalg.norm(np.array(tr) - np.array(tl))
            area_cur = cv2.contourArea(np.array(current, dtype=np.float32))
            
            for candidate in all_masks:
                area_cand = cv2.contourArea(np.array(candidate, dtype=np.float32))
                area_ratio = area_cand / area_cur if area_cur > 0 else 0
                ckey = corner_key(candidate)
                if ckey in visited_local or ckey in visited_global:
                    continue

                ctl, ctr, cbr, cbl = candidate[0], candidate[1], candidate[2], candidate[3]
                center_cand = get_center(candidate)

                # 1. Lan lên trên
                if center_cand[1] < center_cur[1]:
                    up_left = euclidean(tl, cbl)
                    up_right = euclidean(tr, cbr)
                    overlap = min(tr[0], cbr[0]) - max(tl[0], cbl[0])
                    if overlap > min_overlap_ratio * width_cur and abs(center_cur[1] - center_cand[1]) < 400:
                        move.append('up1')
                        queue.append(candidate)
                        continue
                    if (up_left < threshold or up_right < threshold) and abs(center_cur[1] - center_cand[1]) < 400:
                        move.append('up2')
                        queue.append(candidate)
                        continue

                # 2. Lan sang phải
                if center_cand[0] > center_cur[0]:
                    right_top = euclidean(tr, ctl)
                    right_bottom = euclidean(br, cbl)

                    # Chiều cao mặt phải của current (tr → br)
                    cur_right_height = abs(br[1] - tr[1])
                    # Chiều cao mặt trái của candidate (ctl → cbl)
                    cand_left_height = abs(cbl[1] - ctl[1])

                    if right_top < threshold and right_bottom < threshold and 0.8 <= area_ratio <= 1.2:
                        move.append('right1')
                        queue.append(candidate)
                        continue

                    if (right_top < threshold or right_bottom < threshold) and cand_left_height >= 0.5 * cur_right_height and 0.8 <= area_ratio <= 1.2:
                        move.append('right2')
                        queue.append(candidate)
                        continue

                # 3. Lan sang trái
                if center_cand[0] < center_cur[0]:
                    dist_top = euclidean(tl, ctr)
                    dist_bottom = euclidean(bl, cbr)
                    cand_height = abs(cbr[1] - ctr[1])
                    cur_height = abs(bl[1] - tl[1])
                    if dist_top < threshold and dist_bottom < threshold and 0.8 <= area_ratio <= 1.2:
                        move.append('left1')
                        queue.append(candidate)
                        continue
                    if (dist_top < threshold or dist_bottom < threshold) and cand_height >= 0.5 * cur_height and 0.8 <= area_ratio <= 1.2:
                        move.append('left2')
                        queue.append(candidate)
                        continue
                
                # 4. Lan xuống dưới
                if center_cand[1] > center_cur[1]:
                    down_left = euclidean(bl, ctl)
                    down_right = euclidean(br, ctr)
                    cand_top_width = np.linalg.norm(np.array(ctl) - np.array(ctr))
                    cur_bottom_width = np.linalg.norm(np.array(bl) - np.array(br))
                    if down_left < threshold and down_right < threshold:
                        move.append('down1')
                        queue.append(candidate)
                        continue
                    if (down_left < threshold or down_right < threshold) and cand_top_width >= 0.5 * cur_bottom_width:
                        move.append('down2')
                        queue.append(candidate)
                        continue


        if local_result:
            result_all.extend(local_result)
            move_all.append(move)

    print("All directions moved:", move_all)
    return result_all

def fallback_find_corners(pts):
    sums = pts[:, 0] + pts[:, 1]
    diffs = pts[:, 0] - pts[:, 1]
    top_left = pts[np.argmin(sums)]
    bottom_right = pts[np.argmax(sums)]
    top_right = pts[np.argmax(diffs)]
    bottom_left = pts[np.argmin(diffs)]
    return [tuple(top_left), tuple(top_right), tuple(bottom_right), tuple(bottom_left)]

def sort_box_corners_by_position(pts):
    """
    Sắp xếp lại danh sách 4 điểm [x, y] theo thứ tự:
    [top-left, top-right, bottom-right, bottom-left]
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


    return [tuple(top_left), tuple(top_right), tuple(bottom_right), tuple(bottom_left)]

def filter_polygon_outlier_points(pts, dist_thresh=2):
    """
    Lọc các điểm nhiễu trong polygon: nếu hai điểm bất kỳ cách nhau < dist_thresh pixel,
    nhưng index của chúng trong list polygon không liền kề, thì xoá các điểm ở giữa (đoạn ngắn hơn theo vòng tròn).
    """
    pts = np.array(pts)
    n = len(pts)
    keep = np.ones(n, dtype=bool)
    for i in range(n):
        for j in range(i+2, n):
            if (i == 0 and j == n-1):
                continue
            dist = np.linalg.norm(pts[i] - pts[j])
            if dist <= dist_thresh:
                # Xác định hai đoạn: (i+1):j và (j+1):i (theo vòng tròn)
                idx1 = np.arange(i+1, j)
                idx2 = np.concatenate([np.arange(j+1, n), np.arange(0, i)]) if i > 0 else np.arange(j+1, n)
                # Chọn đoạn ngắn hơn
                idx_to_remove = idx1 if len(idx1) <= len(idx2) else idx2
                # Kiểm tra nếu tất cả điểm trong đoạn đều gần 2 đầu mút thì không xoá
                all_near = True
                for k in idx_to_remove:
                    d1 = np.linalg.norm(pts[k] - pts[i])
                    d2 = np.linalg.norm(pts[k] - pts[j])
                    if min(d1, d2) > 2 * dist_thresh:
                        all_near = False
                        break
                if not all_near:
                    keep[idx_to_remove] = False
    return pts[keep]

def find_corners(mask):
    pts = mask.astype(np.int32)
    pts = filter_polygon_outlier_points(pts)
    
    # Tìm convex hull
    hull = cv2.convexHull(pts.reshape(-1, 1, 2))

    # Approximate to polygon
    epsilon = 0.01 * cv2.arcLength(hull, True)
    approx = cv2.approxPolyDP(hull, epsilon, True)

    # Lặp tăng epsilon đến khi còn đúng 4 điểm
    while len(approx) > 4:
        epsilon *= 1.05
        approx = cv2.approxPolyDP(hull, epsilon, True)

    if len(approx) == 4:
        approx = approx.reshape(-1, 2)
        return sort_box_corners_by_position(approx)

    # fallback
    return fallback_find_corners(pts)

def draw_polygons(image, polygons, color=(0, 255, 0), label='Top Match'):
    for idx, poly in enumerate(polygons):
        pts = np.array(poly, np.int32).reshape((-1, 1, 2))
        cv2.polylines(image, [pts], isClosed=True, color=color, thickness=3)

        # Tính trung tâm của polygon
        center = np.mean(np.array(poly), axis=0).astype(int)

        # Ghi nhãn thứ tự lan bên trong box, màu đỏ
        text = f"{idx + 1}"
        cv2.putText(image, text, (center[0], center[1]), cv2.FONT_HERSHEY_SIMPLEX,
                    1.5, (0, 0, 255), thickness=2, lineType=cv2.LINE_AA)

def compute_box_slope(corners):
    corners = np.array(corners)
    p1, p2 = corners[-1], corners[-2]
    A, B = (p1, p2) if p1[0] < p2[0] else (p2, p1)
    dx = B[0] - A[0]
    dy = B[1] - A[1]
    angle_rad = math.atan2(dy, dx)
    angle_deg = math.degrees(angle_rad)
    return A, B, abs(angle_deg)

def compute_extreme_x_distance(inputs):
    """
        Tính khoảng cách giữa x_min nhỏ nhất và x_max lớn nhất.
    Đầu vào có thể là:
      - list các mask (polygon, Nx2)
      - list hoặc np.ndarray các boxes dạng [x1, y1, x2, y2, conf, classid]
    Returns:
        float: abs(x_max - x_min)
        x_min_val (padding) : float — khoảng cách từ cạnh phải của ảnh tới x min
    """
    x_min_val = float('inf')
    x_max_val = float('-inf')

    # Nếu là numpy array và có shape (N, 6) hoặc (N, 4)
    if isinstance(inputs, np.ndarray):
        if inputs.shape[1] >= 4:
            xs_min = inputs[:, 0]
            xs_max = inputs[:, 2]
            x_min_val = float(np.min(xs_min))
            x_max_val = float(np.max(xs_max))
    # Nếu là list các box
    elif isinstance(inputs, list) and len(inputs) > 0 and isinstance(inputs[0], (list, tuple, np.ndarray)) and len(inputs[0]) >= 4:
        xs_min = [box[0] for box in inputs]
        xs_max = [box[2] for box in inputs]
        x_min_val = min(xs_min)
        x_max_val = max(xs_max)
    # Nếu là list các mask (polygon)
    
    else:
        for mask in inputs:
            xs = mask[:, 0]
            x_min = xs.min()
            x_max = xs.max()
            if x_min < x_min_val:
                x_min_val = x_min
            if x_max > x_max_val:
                x_max_val = x_max

    if x_min_val == float('inf') or x_max_val == float('-inf'):
        return None

    pallet_width = abs(x_max_val - x_min_val)
    padding = x_min_val
    
    return pallet_width, padding



def find_top_for_front(front_face_corners, top_face_corners, threshold=50):
    matched_top_faces = []
    matched_front_faces = []

    for front_box in front_face_corners:
        fx1, fy1 = front_box[0]  # top-left
        fx2, fy2 = front_box[1]  # top-right
        front_top_left = (fx1, fy1)
        front_top_right = (fx2, fy2)

        best_top_box = None
        best_dist = float('inf')

        for top_box in top_face_corners:
            tx3, ty3 = top_box[2]  # bottom right
            tx4, ty4 = top_box[3]  # bottom left

            top_bottom_left = (tx4, ty4)
            top_bottom_right = (tx3, ty3)

            left_dist = euclidean(front_top_left, top_bottom_left)
            right_dist = euclidean(front_top_right, top_bottom_right)

            # Chỉ cần một trong hai góc gần là đủ
            if left_dist < threshold or right_dist < threshold:
                min_dist = min(left_dist, right_dist)
                if min_dist < best_dist:
                    best_dist = min_dist
                    best_top_box = top_box

        if best_top_box is not None:
            matched_top_faces.append(best_top_box)
            matched_front_faces.append(front_box)

    return matched_top_faces, matched_front_faces

def get_x_ranges(layer_boxes, pallet_width, padding, min_gap=200):
    """
    Trả về cả các khoảng x của từng box (box_ranges đã merge) và các khoảng gap (gaps) trên trục x.
    box dạng [xmin, ymin, xmax, ymax, conf, id]
    - box_ranges: các đoạn x đã merge (nếu hai box liền kề cách nhau <= 50 pixel thì gộp lại)
    - gaps: các khoảng trống giữa các box_ranges, chỉ lấy gap >= min_gap
    """
    if len(layer_boxes) == 0:
        return [], []
    # Tính x1, x2 cho từng box
    box_ranges = sorted([
        (box[0]+50, box[2]-50) for box in layer_boxes
    ], key=lambda x: x[0])
    
    pallet_range = (padding, pallet_width + padding)

    # Merge các range liền kề (cách nhau <= 100 pixel)
    merged_ranges = []
    for rng in box_ranges:
        if not merged_ranges:
            merged_ranges.append(list(rng))
        else:
            prev = merged_ranges[-1]
            # Nếu hai đoạn liền kề (cách nhau <= 200 pixel), gộp lại
            if rng[0] - prev[1] <= 150:
                prev[1] = max(prev[1], rng[1])
            else:
                merged_ranges.append(list(rng))
    merged_ranges = [tuple(r) for r in merged_ranges]

    # Tìm gaps bằng cách loại merged_ranges khỏi pallet_range
    gaps = []
    last_end = pallet_range[0]
    for rng in merged_ranges:
        if rng[0] - last_end >= min_gap:
            gaps.append((last_end, rng[0]))
        last_end = rng[1]
    if pallet_range[1] - last_end >= min_gap:
        gaps.append((last_end, pallet_range[1]))
        
    # print(f"Layer box_ranges: {merged_ranges}")
    # print(f"Layer gaps: {gaps}")
    return merged_ranges, gaps

def renumber_layers_dict(merged_layers_dict):
    """
    Đánh lại số thứ tự key của merged_layers_dict thành layer_1, layer_2, ...
    Giữ nguyên thứ tự theo vị trí xuất hiện (hoặc bạn có thể sort theo y của box đầu tiên).
    """
    new_dict = {}
    keys = list(merged_layers_dict.keys())
    for i, key in enumerate(keys, 1):
        new_dict[f"layer_{i}"] = merged_layers_dict[key]
    return new_dict

def check_and_merge_layers(layers_boxes, layers_masks, full_ratio=0.8):
    """
    Duyệt qua tất cả các cặp layer thiếu liên tiếp, merge cặp thỏa mãn điều kiện:
    box_range layer này nằm trong gaps layer kia và ngược lại.
    Khi merge xong, cập nhật lại layer đầu (ví dụ 2_3 sẽ cập nhật vào 2), xoá layer sau khỏi danh sách, rồi tiếp tục duyệt các cặp tiếp theo.
    Ngưng khi kết quả không thay đổi nữa.

    Output:
        merged: list các tuple (layer1, layer2) đã merge
        merged_layers_dict: dict, key là layer, value là dict {
            'boxes': list box,
            'masks': list masks tương ứng,
            'missing': bool (True nếu layer thiếu, False nếu đủ),
            'x_range': list các đoạn x đã merge,
            'gaps': list các gap,
            'old_layer': list tên layer gốc
        }
    """
    def boxes_in_gaps(box_ranges, gaps):
        for x1, x2 in box_ranges:
            in_gap = False
            for gap_start, gap_end in gaps:
                if gap_start - 200 <= x1 and x2 <= gap_end + 200:
                    in_gap = True
                    break
                elif (gap_start == x1 and x2 <= gap_end + 500) or (gap_end == x2 and x1 >= gap_start - 500):
                    in_gap = True
                    break
            if not in_gap:
                return False
        return True
    # Xoá các layer trống trước khi duyệt
    layers_boxes = {k: v for k, v in layers_boxes.items() if len(v) > 0}
    layers_masks = {k: v for k, v in layers_masks.items() if k in layers_boxes}
    
    if not layers_boxes:
        return {}
    
    all_boxes = []
    for layer_boxes in layers_boxes.values():
        all_boxes.extend(layer_boxes)
    pallet_width, padding = compute_extreme_x_distance(all_boxes)

    merged_layers_dict = {}
    for layer_name, layer_boxes in layers_boxes.items():
        box_ranges, gaps = get_x_ranges(layer_boxes, pallet_width, padding)
        layer_width = sum(x2 - x1 for x1, x2 in box_ranges) if box_ranges else 0
        missing = layer_width < full_ratio * pallet_width
        merged_layers_dict[layer_name] = {
            'boxes': layer_boxes,
            'masks': layers_masks[layer_name],
            'missing': missing,
            'x_range': box_ranges,
            'gaps': gaps,
            'old_layer': [layer_name]
        }

    changed = True
    while changed:
        changed = False
        # Lấy danh sách các layer thiếu
        not_full_layers = [k for k, v in merged_layers_dict.items() if v['missing']]
        i = 0
        while i < len(not_full_layers) - 1:
            k1, k2 = not_full_layers[i], not_full_layers[i+1]
            boxes1 = merged_layers_dict[k1]['boxes']
            boxes2 = merged_layers_dict[k2]['boxes']
            masks1 = merged_layers_dict[k1]['masks']
            masks2 = merged_layers_dict[k2]['masks']
            box_ranges1, gaps1 = merged_layers_dict[k1]['x_range'], merged_layers_dict[k1]['gaps']
            box_ranges2, gaps2 = merged_layers_dict[k2]['x_range'], merged_layers_dict[k2]['gaps']

            cond1 = boxes_in_gaps(box_ranges1, gaps2)
            cond2 = boxes_in_gaps(box_ranges2, gaps1)
            
            if cond1 or cond2:
                # Merge vào layer đầu (k1), xoá layer sau (k2)
                merged_boxes = boxes1 + boxes2
                merged_masks = masks1 + masks2
                
                box_ranges, gaps = get_x_ranges(merged_boxes, pallet_width, padding)
                missing = True
                old_layer = merged_layers_dict[k1]['old_layer'] + merged_layers_dict[k2]['old_layer']
                
                merged_layers_dict[k1] = {
                    'boxes': merged_boxes,
                    'masks': merged_masks,
                    'missing': missing,
                    'x_range': box_ranges,
                    'gaps': gaps,
                    'old_layer': old_layer
                }
                
                del merged_layers_dict[k2]
                
                changed = True
                # Không cần cập nhật lại not_full_layers, sẽ lấy lại ở vòng while ngoài
                break
            else:
                i += 1
    merged_layers_dict = renumber_layers_dict(merged_layers_dict)
    
    # Tìm layer đầu tiên có missing = False và set missing = False cho các layer trước đó
    layer_keys = sorted(merged_layers_dict.keys(), key=lambda x: int(x.split('_')[1]))
    first_non_missing_idx = None
    
    for i, layer_key in enumerate(layer_keys):
        if not merged_layers_dict[layer_key]['missing']:
            first_non_missing_idx = i
            break
    
    if first_non_missing_idx is not None:
        # Set missing = False cho tất cả layer trước layer đầu tiên có missing = False
        for i in range(first_non_missing_idx):
            layer_key = layer_keys[i]
            if merged_layers_dict[layer_key]['missing']:
                merged_layers_dict[layer_key]['missing'] = False
    
    return merged_layers_dict


def match_layers(front_merged_layers_dict, top_merged_layers_dict):
    """
    Dò các layer từ trên cùng xuống (layer cuối cùng trong dict), chỉ cần cùng số lượng box là coi như match.
    Nếu có layer ở top không map được với front thì trả về False.
    Nếu tìm được hết (chỉ dư layer ở bên front) thì trả về True.

    Args:
        front_merged_layers_dict: dict[str, dict]  # key: layer name, value: dict với 'boxes', ...
        top_merged_layers_dict: dict[str, dict]

    Returns:
        bool
    """
    # Lấy list các layer theo thứ tự từ dưới lên (gốc tọa độ ở trên trái, nên layer trên cùng là cuối cùng)
    front_layers = list(front_merged_layers_dict.values())[::-1]
    top_layers = list(top_merged_layers_dict.values())[::-1]

    # # Dò từng layer từ trên xuống
    # for i, top_info in enumerate(top_layers):
    #     if i >= len(front_layers):
    #         return False  # Không đủ layer front để so sánh
    #     front_info = front_layers[i]
    #     if len(top_info['boxes']) != len(front_info['boxes']):
    #         return False  # Số lượng box không khớp
    # return True  # Nếu tất cả layer top đều match với front (có thể dư layer ở bên front)
    
    # Tạm thời chỉ xét layer trên cùng
    front_info = front_layers[0]
    top_info = top_layers[0]

    return len(front_info['boxes']) == len(top_info['boxes'])


def check_missing_by_area(image: np.array, boxes: np.array, masks: np.array, num_box, top_face_class_idx):
    box_mask_pairs = sorted(zip(boxes, masks), key=lambda x: -x[0][3])
    boxes, masks = zip(*box_mask_pairs)
    boxes = np.array(boxes)
    masks = list(masks)

    negative_indices = np.where(boxes[:, -1] == top_face_class_idx)[0]
    negative_boxes = boxes[negative_indices]
    origin_negative_masks = [masks[i] for i in negative_indices]
    negative_masks = origin_negative_masks[:num_box]
    tmp_boxes = negative_boxes[:num_box]

    box_mask_pairs = sorted(zip(tmp_boxes, negative_masks), key=lambda x: x[0][0])
    tmp_boxes, negative_masks = zip(*box_mask_pairs)

    third_box_idx = np.argmin(negative_boxes[:, 1])
    third_box_poly = origin_negative_masks[third_box_idx]

    output = image.copy()
    four_points = []
    shift_x = 9

    if len(negative_masks) <= 1:
        return True
    
    for idx, points in enumerate(negative_masks):
        approx = points
        if approx is None:
            return True

        cv2.polylines(output, [approx.astype(np.int32)], True, (0, 255, 0), 2)
        if idx in [0, num_box - 1]:
            four_points = draw_line_and_store_points(output, approx, idx, shift_x, four_points)

    # Handle third box and get its line
    approx = third_box_poly
    if approx is not None:
        cv2.polylines(output, [approx.astype(np.int32)], True, (0, 255, 0), 2)
        tmp_list = sorted(approx, key=lambda x: x[1])
        third_start = [int(tmp_list[0][0]), int(tmp_list[0][1])]
        third_end = [int(tmp_list[1][0]), int(tmp_list[1][1])]
        cv2.line(output, third_start, third_end, color=(0, 255, 255), thickness=20)
    else:
        print("Không tìm được 4 điểm cho third_box_poly")
        # raise ValueError("Không tìm được 4 điểm cho third_box_poly")
        return True

    # Get intersections between yellow lines and third box line
    start1, end1, start2, end2 = four_points
    pt1 = line_intersection(start1, end1, third_start, third_end) + np.array([shift_x, shift_x])
    pt2 = line_intersection(start2, end2, third_start, third_end) - np.array([shift_x, shift_x])

    if pt1 is None or pt2 is None:
        raise ValueError("Không tìm được giao điểm với đường nghiêng.")

    y_cut = 30
    # start1, end1, start2, end2 = four_points
    # pt1 = line_intersect_y_full_line(start1, end1, y_cut) + np.array([shift_x, shift_x])
    # pt2 = line_intersect_y_full_line(start2, end2, y_cut) + np.array([shift_x, shift_x])
    # if pt1 is None or pt2 is None:
    #     raise ValueError(f"Không tìm được giao điểm với y = {y_cut}.")

    if pt1[1] < y_cut:
        pt1[1] = y_cut
    if pt2[1] < y_cut:
        pt2[1] = y_cut

    # Calculate angle
    # angle_right = calculate_angle(start1, start2, pt2)
    # angle_left = calculate_angle(start2, start1, pt1)
    # print("Angle left: ", angle_left)
    # print("Angle right: ", angle_right)
    # print(pt2)
    # pt2 = shift_to_left_to_target_deg(start1, start2, pt2, target_angle=47.) - np.array([shift_x, shift_x])
    # print(calculate_angle(start1, start2, pt2))


    top_zones = np.array([start1, start2, pt2, pt1], dtype=np.int32).reshape(-1, 2)
    cv2.polylines(output, [top_zones], True, (0, 255, 0), 2)

    # # Save output image
    # output_path = "output_with_4_lines.jpg"
    # cv2.imwrite(output_path, output)

    gray = cv2.cvtColor(output, cv2.COLOR_BGR2GRAY)
    # gray = 0.2989 * output[..., 0] + 0.5870 * output[..., 1] + 0.1140 * output[..., 2]
    # gray = gray.astype(np.uint8)

    # Assume gray is a 2D grayscale image (H, W)
    # Create a mask of zeros
    mask = np.zeros_like(gray, dtype=np.uint8)

    # Fill polygon area with 1s
    cv2.fillPoly(mask, [top_zones], color=1)

    # Now use the mask to extract pixel values inside the polygon
    masked_pixels = gray[mask == 1]

    # Count pixels with value == 254
    missing_area = np.sum(masked_pixels == 254)
    full_other_area = np.sum(masked_pixels != 254)

    # # Convert BGR to grayscale (manual)
    # gray = 0.2989 * output[..., 0] + 0.5870 * output[..., 1] + 0.1140 * output[..., 2]
    # gray = gray.astype(np.uint8)

    # # Tạo mask của vùng polygon top_zones
    # mask_zone = np.zeros_like(gray, dtype=np.uint8)
    # cv2.fillPoly(mask_zone, [top_zones], color=1)

    # # Tạo mask cho pixel có giá trị 254 nằm trong polygon
    # mask_254_in_zone = np.zeros_like(gray, dtype=np.uint8)
    # mask_254_in_zone[(gray == 254) & (mask_zone == 1)] = 1

    # # Tìm các polygon (contours) trong vùng mask này
    # contours, _ = cv2.findContours(mask_254_in_zone, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # if contours:
    #     # Chọn contour có diện tích lớn nhất
    #     largest_contour = max(contours, key=cv2.contourArea)

    #     # Tạo mask chỉ chứa vùng contour lớn nhất
    #     largest_mask = np.zeros_like(gray, dtype=np.uint8)
    #     cv2.drawContours(largest_mask, [largest_contour], -1, color=1, thickness=-1)

    #     # Đếm số pixel 254 trong vùng contour lớn nhất
    #     missing_area = np.sum((gray == 254) & (largest_mask == 1))
    # else:
    #     missing_area = 0


    # Assume gray is your grayscale image (just used for shape)
    image_shape = gray.shape  # (H, W)

    # areas = []

    # for idx, poly in enumerate(origin_negative_masks):
    #     # Create a blank mask
    #     mask = np.zeros(image_shape, dtype=np.uint8)

    #     # Fill the polygon
    #     poly = poly.astype(np.int32).reshape(-1, 1, 2)
    #     cv2.fillPoly(mask, [poly], color=1)
    #     # cv2.imwrite(f"{idx}.png", mask * 255)

    #     # Area = number of pixels filled
    #     area = np.sum(mask == 1)
    #     # areas.append((area, poly))  # store area with polygon
    #     areas.append(area)

    # # Sort by area ascending
    # areas_sorted = sorted(areas, key=lambda x: x)

    # threshold = 0.75
    is_missing = False
    # # # Example print
    # for i, area in enumerate(areas_sorted):
    #     print(missing_area * 1. / area)
    #     if missing_area * 1. / area > threshold:
    #         is_missing = True
    #         break
    theshold = 0.05
    if missing_area * 1. / full_other_area > theshold:
        is_missing = True
    return is_missing



    