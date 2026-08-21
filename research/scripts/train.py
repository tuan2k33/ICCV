from ultralytics import YOLO

# Đường dẫn đến file config.yaml
DATA_PATH = '/ssd1/tuannw/batch4/data/config.yaml'

model = YOLO("jameslahm/yolo11x-seg.pt") 

# # # Resume từ checkpoint cuối cùng
# last = YOLO("/ssd1/tuannw/yolo-train/4batch2/weights/last.pt")  # Đường dẫn đến checkpoint cuối cùng
# resume_training = last.train(resume=True)  # Tiếp tục huấn luyện từ checkpoint cuối cùng

# Huấn luyện model với các tham số optimizer và augmentation được chỉ định
results = model.train(
    data=DATA_PATH,        # file cấu hình dataset
    task='segment',        # detect, segment, classify, pose, track
    epochs=50,            # số epoch huấn luyện
    batch=8,               # batch size
    imgsz=640,             # kích thước ảnh đầu vào (tùy chọn)
    workers=1,             # số luồng xử lý song song (tùy chọn)
    project='yolo',        # thư mục lưu kết quả huấn luyện
    name='4batch',         # tên thư mục con để lưu weights và logs
    device='cuda:[2]',     # chỉ định GPU (có thể chỉ định nhiều GPU như '[0,1]' hoặc '-1' để sử dụng GPU rất rỗng)

    # --- Các tham số Optimizer và Learning Rate Schedule ---
    optimizer='AdamW',     # Chỉ định rõ optimizer là AdamW
    lr0=0.003,             # Tốc độ học ban đầu (ví dụ từ log của bạn, hoặc bạn có thể thử giá trị khác)
    lrf=0.01,              # Hệ số tốc độ học cuối cùng (0.01 là mặc định phổ biến)
    momentum=0.9,          # Tham số momentum (ví dụ từ log của bạn)
    weight_decay=0.0005,   # Tham số weight decay (ví dụ từ log của bạn)
    warmup_epochs=3.0,     # Số epoch warmup (giá trị mặc định hoặc bạn có thể tinh chỉnh)
    warmup_momentum=0.8,   # Momentum trong giai đoạn warmup (giá trị mặc định hoặc bạn có thể tinh chỉnh)

    # --- Các tham số Loss Function Weights ---
    box=0.1,               # Trọng số cho bounding box loss (giá trị mặc định hoặc tinh chỉnh)
    cls=0.5,               # Trọng số cho classification loss (giá trị mặc định hoặc tinh chỉnh)

    # --- Các tham số Data Augmentation ---
    augment=True,          # Bật data augmentation
    hsv_h=0.02,            # Thay đổi sắc thái (hue)
    hsv_s=0.7,             # Thay đổi độ bão hòa (saturation) - TĂNG LÊN CHO VẤN ĐỀ LOÁ SÁNG
    hsv_v=0.7,             # Thay đổi độ sáng (value/brightness) - TĂNG LÊN CHO VẤN ĐỀ LOÁ SÁNG
    degrees=0.0,           # Xoay ảnh (thường để 0 nếu đối tượng không xoay)
    translate=0.1,         # Dịch chuyển ảnh
    scale=0.5,             # Thay đổi tỷ lệ ảnh
    shear=0.0,             # Biến dạng cắt (thường để 0)
    perspective=0.0,       # Biến đổi phối cảnh (thường để 0)
    flipud=0.0,            # Lật ảnh theo chiều dọc (0.0 nếu không cần)
    fliplr=0.5,            # Lật ảnh theo chiều ngang (0.5 là mặc định)
    mosaic=1.0,            # Xác suất sử dụng mosaic (1.0 là mặc định)
    mixup=0.2,             # Xác suất sử dụng mixup - TĂNG LÊN CHO VẤN ĐỀ MỜ/LOÁ SÁNG
    copy_paste=0.1,        # Xác suất sử dụng copy-paste (quan trọng cho segmentation)
)