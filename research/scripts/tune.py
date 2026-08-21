from ultralytics import YOLO

# --- Cấu hình ---
DATA_PATH = '/ssd1/tuannw/batch4/data/config.yaml'

model = YOLO('jameslahm/yolo11x-seg.pt')  # hoặc đường dẫn local


# --- Khai báo không gian tìm kiếm hyperparameter ---
search_space = {
    "lr0": (1e-5, 1e-2),          # Tốc độ học ban đầu
    "momentum": (0.7, 0.99),      # Momentum nếu dùng SGD
    "hsv_s": (0.2, 0.9),          # Bão hoà màu - chống mất chi tiết
    "hsv_v": (0.2, 0.9),          # Độ sáng - chống mất chi tiết
    "hsv_h": (0.0, 0.1),          # Sắc thái màu - chống mất chi tiết
    "mosaic": (0.0, 1.0),          # Sử dụng mosaic augmentation
    "scale": (0.3, 0.7),          # Phóng to/thu nhỏ
    "translate": (0.0, 0.2),      # Dịch chuyển ảnh
    "degrees": (0.0, 15.0),       # Xoay ảnh nhẹ
}

# --- Gọi hàm tune ---
results = model.tune(
    data=DATA_PATH,
    epochs=20,                  # Train mỗi cấu hình trong 20 epoch
    iterations=50,              # Số lần thử (tức là 50 tổ hợp khác nhau)
    optimizer="AdamW",          # Có thể dùng SGD nếu muốn
    space=search_space,         # Không gian tìm kiếm
    plots=True,                 # Vẽ biểu đồ kết quả
    save=True,                  # Lưu log và kết quả
    val=True,                   # Đánh giá val set
    project='yolo-tune',
    name='tune4batch',           # Tên thư mục lưu kết quả
    device='cuda:[3]',            # Chỉ định GPU
    augment=True,              # Bật data augmentation
)

# --- In ra bộ thông số tốt nhất ---
print("\nBest hyperparameters:")
print(results.best_params)
