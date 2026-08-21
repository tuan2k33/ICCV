import os
import pickle
from ultralytics import YOLO

# --- Cấu hình ---
WEIGHTS_PATH = '/ssd1/tuannw/yolo/4batch2/weights/best.pt'
IMAGES_PATH = '/ssd1/tuannw/output_fix_merged/31-05-25'
OUTPUT_PATH = '/ssd1/tuannw/infer_result'

# Load mô hình
model = YOLO(WEIGHTS_PATH)

# Inference
results = model.predict(
    source=IMAGES_PATH,
    task='segment',
    imgsz=640,
    save=True,             # Lưu ảnh có overlay kết quả
    save_txt=False,        # Không lưu txt
    project=OUTPUT_PATH,
    name='31-05-252',
    iou=0.5,
    conf=0.5,
    agnostic_nms=True,
    device='2'  # Không cần để trong dấu [] với ultralytics
)

# === Lưu kết quả inference ra file pickle ===
with open(os.path.join(OUTPUT_PATH+"/31-05-25/", 'results.pkl'), 'wb') as f:
    pickle.dump(results, f)

print("✅ Saved full YOLO results object to results.pkl")