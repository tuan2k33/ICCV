# Inventory Count AI

Hệ thống kiểm kê hàng hoá tự động từ video. Pipeline nhận video quay dọc dãy kệ, tự động nhận diện từng bin, đọc mã bin, phân loại trạng thái có hàng / trống và đọc product ID.

---

## Luồng AI

```
Video input (List)
     │
     ▼
[1] Tiền xử lý video
     │  Nối list các video input thành 1 video
     ▼
[2] Decode frame 
     │  VideoReader — decord NVDEC, batch decode trên GPU
     ▼
[3] Phân loại frame — Classifier (ResNet50, PyTorch)
     │  Crop 10–40% chiều cao frame (vùng chứa mã bin)
     │  Label: background | carton | code
     ▼
[4] OCR mã bin — PaddleOCR mobile (song song với bước 3)
     │  Det: PP-OCRv5_mobile_det  |  Rec: PP-OCRv5_mobile_rec
     │  Output: mã bin dạng XX-NNN-P (vd: AT-076-3)
     ▼
[5] Xử lý logic (process_csv_raw + get_all_codes)
     │  Lọc, nhóm frame theo mã bin
     │  Chọn frame đại diện: code frame, front frame, top frame
     ▼
[6] Lưu kết quả
     │  Lưu đoạn video ngắn xung quanh mỗi bin
     │  Lưu ảnh code / front / top cho từng bin
     ▼
[7] Inference bổ sung 
     │  ProductIDReader (PaddleOCR server) — đọc product ID 8 chữ số
     │  Classifier check_inner — phân loại bin rỗng / có hàng
     ▼
Output: dict_total.json + ảnh + video clip + CSV + log
```

---

## Cấu trúc output

Mỗi lần chạy sinh ra:

```
outputs/<video_name>_<timestamp>_result/
├── <video_name>_<timestamp>.mp4      # video đã xử lý
├── output_raw.csv                    # kết quả thô (frame-level)
├── output_processed.csv              # kết quả sau lọc (bin-level)
├── dict_total.json                   # tổng hợp: mã bin, product_id, trạng thái rỗng
└── <video_name>_<timestamp>.log

outputs/<bin_code>/                   # ví dụ: outputs/AT-076-3/
├── AT-076-3_code_<ts>.jpg
├── AT-076-3_front_<ts>.jpg
├── AT-076-3_top_<ts>.jpg
└── AT-076-3.mp4
```

