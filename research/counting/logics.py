import cv2
import numpy as np


import math

def calculate_angle(A, B, C):
    """
    Calculate angle ABC (in degrees) between 3 points A, B, C
    """
    # Convert to vectors
    BA = (A[0] - B[0], A[1] - B[1])
    BC = (C[0] - B[0], C[1] - B[1])

    # Dot product and magnitude
    dot_product = BA[0]*BC[0] + BA[1]*BC[1]
    mag_BA = math.hypot(BA[0], BA[1])
    mag_BC = math.hypot(BC[0], BC[1])

    if mag_BA == 0 or mag_BC == 0:
        return None  # Avoid division by zero

    # Angle in radians
    angle_rad = math.acos(dot_product / (mag_BA * mag_BC))

    # Convert to degrees
    angle_deg = math.degrees(angle_rad)
    return angle_deg

def shift_to_left_to_target_deg(A, B, C, target_angle=60.):
    angle = calculate_angle(A, B, C)
    new_C = list(C)

    if angle is None:
        return C  # can't compute

    # Only shift if angle > 60
    while angle > target_angle:
        new_C[0] -= 1  # move C left by 1 pixel
        angle = calculate_angle(A, B, new_C)
        if new_C[0] < 0:  # avoid going off image
            break

    return tuple(new_C)

def extract_convex_4_points(poly_points, debug=False):
    pts = poly_points.astype(np.float32)
    hull = cv2.convexHull(pts)
    epsilon = 0.01 * cv2.arcLength(hull, True)
    approx = cv2.approxPolyDP(hull, epsilon, True)

    while len(approx) > 4:
        epsilon *= 1.05
        approx = cv2.approxPolyDP(hull, epsilon, True)

    if len(approx) == 4:
        return approx.reshape(-1, 2)
    if debug:
        print(f"Could not find 4-point approximation, found {len(approx)} points")
    return None


def draw_line_and_store_points(output, approx, idx, shift_x, four_points):
    approx = sorted(approx, key=lambda p: p[0])
    if idx == 0:
        line_pts = sorted(approx[:2], key=lambda x: -x[1])
        shift = shift_x
    else:
        line_pts = sorted(approx[2:], key=lambda x: -x[1])
        shift = -shift_x

    start_point = [int(x) for x in line_pts[0]]
    end_point = [int(x) + shift for x in line_pts[1]]

    four_points.extend([start_point, end_point])
    cv2.line(output, start_point, end_point, color=(0, 255, 255), thickness=20)
    return four_points


def line_intersection(p1, p2, p3, p4):
    """
    Tính giao điểm của hai đường thẳng (p1-p2) và (p3-p4)
    """
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4

    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if denom == 0:
        return None  # song song

    px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / denom
    py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / denom

    return (int(px), int(py))


def fill_mask_and_count(gray, polygon, value=1):
    mask = np.zeros_like(gray, dtype=np.uint8)
    cv2.fillPoly(mask, [polygon], color=value)
    masked_pixels = gray[mask == value]
    return masked_pixels

def line_intersect_y_full_line(p1, p2, y_cut):
    x1, y1 = p1
    x2, y2 = p2

    # Nếu đường ngang → hoặc vô số giao hoặc không có giao
    if y1 == y2:
        return None

    # Tính t cho phương trình đường thẳng
    t = (y_cut - y1) / (y2 - y1)

    # Dùng t để nội suy x
    x = x1 + t * (x2 - x1)
    return (int(x), int(y_cut))

