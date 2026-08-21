# Tài liệu dự án: Inventory Count AI

**Phiên bản:** 1.0
**Ngày cập nhật:** 2026-06-08
**Ngôn ngữ:** Python 3.x
**Mục đích:** Hệ thống kiểm kê kho hàng tự động bằng AI

---

## Mục lục

1. [Tổng quan dự án](#1-tổng-quan-dự-án)
2. [Kiến trúc hệ thống](#2-kiến-trúc-hệ-thống)
3. [Cấu trúc thư mục](#3-cấu-trúc-thư-mục)
4. [Tech Stack](#4-tech-stack)
5. [Cài đặt & Khởi chạy](#5-cài-đặt--khởi-chạy)
6. [Cấu hình](#6-cấu-hình)
7. [Pipeline xử lý](#7-pipeline-xử-lý)
8. [Các thành phần AI/ML](#8-các-thành-phần-aiml)
9. [API Reference](#9-api-reference)
10. [Cấu trúc Output](#10-cấu-trúc-output)
11. [Docker Deployment](#11-docker-deployment)
12. [Các lớp & Interface chính](#12-các-lớp--interface-chính)
13. [Sơ đồ luồng xử lý](#13-sơ-đồ-luồng-xử-lý)

---

## 1. Tổng quan dự án

**Inventory Count AI** là hệ thống kiểm kê kho hàng tự động, sử dụng trí tuệ nhân tạo để xử lý video ghi hình các kệ hàng và tự động:

- **Phát hiện và đọc mã thùng hàng** (bin code) định dạng `XX-NNN-P` (ví dụ: `AT-076-3`)
- **Nhận diện mã sản phẩm** (product ID) 8 chữ số trong mỗi thùng
- **Phân loại trạng thái thùng** (đầy / một phần / trống)
- **Trích xuất hình ảnh và video clip** đại diện cho từng thùng hàng


---

## 2. Kiến trúc hệ thống

```
┌─────────────────────────────────────────────────────────┐
│                      Input Layer                        │
│           Video files (MP4, stereo/mono)                │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                  Video Processing                       │
│   FFmpeg concat → GPU Decode (Decord NVDEC)             │
└──────────────┬──────────────────────────┬───────────────┘
               │                          │
┌──────────────▼──────────────┐  ┌────────▼───────────────┐
│  Frame Classifier ResNet50  │  │   PaddleOCR Thread     │
│  3 classes:                 │  │   Bin code Reader      │
│  background/carton/code     │  │   Pattern: XX-NNN-P    │
└──────────────┬──────────────┘  └────────┬───────────────┘
               └────────────┬─────────────┘
                            │
┌───────────────────────────▼─────────────────────────────┐
│               Post-processing Logic                     │
│   CSV filtering → Code grouping → Frame selection       │
└───────────────────────┬─────────────────────────────────┘
                        │
         ┌──────────────┼──────────────┐
         │              │              │
┌────────▼──────┐ ┌─────▼──────┐ ┌─────▼──────────────────┐
│  Save Images  │ │ Save Video │ │  PaddleOCR             │
│  code.jpg     │ │ clips.mp4  │ │  Product ID Reader     │
│  front.jpg    │ │            │ │  Fullness Classifier   │
│  top.jpg      │ │            │ │  ResNet50              │
└────────┬──────┘ └─────┬──────┘ └───┬────────────────────┘
         └──────────────┼────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│                   Output Layer                          │
│         dict_total.json + images + video clips          │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Cấu trúc thư mục

```
inventory-count-ai/
│
├── main.py                          # Pipeline chính, lớp VideoProcessing
├── api_server.py                    # FastAPI server (REST endpoint)
├── run_multi.py                     # Chạy đa tiến trình
│
├── models/                          # Các mô hình AI/ML
│   ├── classifier.py                # ResNet50 phân loại khung hình
│   ├── classifier_check_inner.py    # ResNet50 phân loại độ đầy thùng
│   ├── paddle_apdater.py            # PaddleOCR (mobile) đọc bin code
│   ├── product_id_reader.py         # PaddleOCR (server) đọc product ID
│   └── ocr.py                       # OCR legacy
│
├── utils/                           # Tiện ích
│   ├── process_raw.py               # Lọc và xử lý CSV thô
│   ├── get_frame_position.py        # Logic chọn khung hình & nhóm code
│   ├── save_frame.py                # Lưu hình ảnh và tạo dict_total.json
│   ├── save_vids.py                 # Trích xuất video clip
│   ├── get_pid.py                   # Trích xuất product ID
│   ├── check_inner.py               # Kiểm tra độ đầy thùng
│   ├── video_reader.py              # Đọc video GPU qua Decord
│   ├── reader.py                    # Đọc cấu hình YAML
│   ├── logger.py                    # Logging theo múi giờ VN
│   └── code_split.py                # Tiện ích tách mã
│
├── weights/                         # Trọng số mô hình
│   ├── resnet50_trained.pth
│   ├── resnet50_trained_new_classify_1.pth
│   ├── resnet50_trained_new_classify_2.pth
│   └── official_models/             # Các mô hình PaddleOCR
│       ├── PP-OCRv5_mobile_det/     # Phát hiện bin code (mobile)
│       ├── PP-OCRv5_mobile_rec/     # Nhận dạng bin code (mobile)
│       ├── PP-OCRv5_server_det/     # Phát hiện product ID (server)
│       ├── PP-OCRv5_server_rec/     # Nhận dạng product ID (server)
│       ├── PP-LCNet_x1_0_doc_ori/
│       ├── PP-LCNet_x1_0_textline_ori/
│       └── UVDoc/
│
├── configs/
│   └── config.yaml                  # File cấu hình chính
│
├── outputs/                         # Kết quả xử lý (tự tạo)
├── videos/                          # Video mẫu/kiểm thử
├── test/                            # Dữ liệu kiểm thử
│
├── docker-compose.yml               # Docker production
├── docker-compose.dev.yml           # Docker development
├── docker-compose.test.yml          # Docker test
├── requirements.txt                 # Python dependencies
└── README.md
```

---

## 4. Tech Stack

### AI / ML

| Thư viện | Phiên bản | Mục đích |
|----------|-----------|---------|
| PyTorch | 2.12.0 | Deep learning framework |
| TorchVision | 0.27.0 | ResNet50 models |
| PaddlePaddle (GPU) | 3.3.1 | OCR backend |
| PaddleOCR | 3.6.0 | Text detection & recognition |

### Xử lý Video & Ảnh

| Thư viện | Phiên bản | Mục đích |
|----------|-----------|---------|
| Decord (custom) | N/A | GPU-accelerated video decode (NVDEC) |
| OpenCV | 4.10.0.84 | Image manipulation |
| FFmpeg | System | Video concatenation & segment extraction |

### API & Server

| Thư viện | Phiên bản | Mục đích |
|----------|-----------|---------|
| FastAPI | 0.136.3 | REST API framework |
| Uvicorn | 0.49.0 | ASGI server |
| Pydantic | 2.13.4 | Data validation |

### Data & Utilities

| Thư viện | Phiên bản | Mục đích |
|----------|-----------|---------|
| Pandas | 3.0.3 | DataFrame xử lý CSV |
| NumPy | 2.3.5 | Numerical computing |
| PyYAML | 6.0.2 | Đọc file cấu hình |
| Loguru | 0.7.3 | Advanced logging |

### CUDA Stack

| Thành phần | Phiên bản |
|------------|-----------|
| CUDA | 13.0 |
| cuDNN | 9.20.0.48 |
| NVIDIA NCCL | 2.29.7 |
| TensorRT | 11.0.0 |

---

## 5. Cài đặt & Khởi chạy

### Yêu cầu hệ thống

- GPU NVIDIA với CUDA 13.0+
- Docker với NVIDIA Container Toolkit
- Python 3.x (nếu chạy trực tiếp)

### Chạy bằng Docker (khuyến nghị)

```bash
# Production
docker-compose up -d

# Development
docker-compose -f docker-compose.dev.yml up -d

# Test
docker-compose -f docker-compose.test.yml up -d
```

### Chạy trực tiếp

```bash
# Cài dependencies
pip install -r requirements.txt

# Cài Decord (custom GPU build)
cd /tmp/decord2/python && pip install .

# Chạy pipeline
python main.py \
  --video_input /path/to/video.mp4 \
  --output_path outputs \
  --config configs/config.yaml \
  --mode 1

# Chạy API server
uvicorn api_server:app --host 0.0.0.0 --port 8000

```

### Gọi API

```bash
curl -X POST http://localhost:8000/process-videos/ \
  -H "Content-Type: application/json" \
  -d '{
    "video_input": "/ssd1/path/to/video.mp4",
    "output_path": "outputs"
  }'
```

---

## 6. Cấu hình

### `configs/config.yaml`

```yaml
ocr:
  device: "gpu"                              # Thiết bị xử lý OCR
  det_model: "PP-OCRv5_mobile_det"           # Model phát hiện văn bản
  rec_model: "PP-OCRv5_mobile_rec"           # Model nhận dạng văn bản
  server_det: "weights/official_models/PP-OCRv5_server_det"
  mobile_det: "weights/official_models/PP-OCRv5_mobile_det"
  server_rec: "weights/official_models/PP-OCRv5_server_rec"
  mobile_rec: "weights/official_models/PP-OCRv5_mobile_rec"

classifier:
  model_path: "weights/resnet50_trained.pth"
  model_link: ""                             # URL tải weights nếu chưa có sẵn (tuỳ chọn)

video:
  output_dir: "outputs/"                     # Thư mục lưu kết quả
  raw_csv: "output_raw.csv"                  # CSV kết quả thô
  processed_csv: "output_processed.csv"      # CSV đã xử lý

batch_size: 16          # Batch size cho frame classifier
batch_size_ocr: 16      # Batch size cho OCR
batch_size_pid: 1       # Batch size cho product ID reader
```

### Biến môi trường Docker

| Biến | Mặc định | Mô tả |
|------|----------|-------|
| `NVIDIA_VISIBLE_DEVICES` | `all` | GPU được sử dụng |
| `DECORD_EOF_RETRY_MAX` | `20480` | Số lần retry khi EOF |
| `SSD1` | `/ssd1` | Đường dẫn SSD |
| `HDD1` | `/hdd1` | Đường dẫn HDD |

---

## 7. Pipeline xử lý

Pipeline xử lý gồm các bước tuần tự sau:

### Bước 1: Tiền xử lý video

**Hàm:** `concat_videos()` trong `main.py`

- Nhận danh sách đường dẫn video đầu vào
- Validate định dạng và khả năng đọc
- Ghép nối các video thành một luồng duy nhất bằng FFmpeg
- Tuỳ chọn: Tách video stereo thành kênh trái/phải, sau đó ghép lại

### Bước 2: Giải mã video GPU

**Lớp:** `VideoReader` trong `utils/video_reader.py`

- Sử dụng thư viện Decord với NVDEC (phần cứng GPU)
- Giải mã frame theo batch, trả về PyTorch tensor hình `(N, H, W, 3)`
- Lấy thông tin: số frame, resolution, FPS

### Bước 3: Phân loại khung hình

**Lớp:** `Classifier` trong `models/classifier.py`

- Với mỗi batch frame: cắt vùng ROI (10–40% chiều cao)
- ResNet50 dự đoán 1 trong 3 nhãn:
  - `background`: Khung nền, không có thùng
  - `carton`: Thấy mặt carton nhưng không thấy mã
  - `code`: Nhìn thấy mã thùng (bin code)
- Ghi kết quả vào DataFrame

### Bước 4: OCR song song

**Worker:** `_ocr_worker()` thread trong `main.py`

- Chạy song song với Bước 3 trong thread riêng
- Queue nhận frame được gán nhãn `code`
- `PaddleOCRAdapter` (mobile models) xử lý batch:
  - Phát hiện vùng văn bản (detection)
  - Nhận dạng ký tự (recognition)
  - Trả về: text, confidence score, tọa độ center

### Bước 5: Xuất CSV thô

**File:** `output_raw.csv`

| Cột | Mô tả |
|-----|-------|
| `frame_idx` | Chỉ số frame trong video |
| `label` | Nhãn phân loại: background/carton/code |
| `ocr` | Danh sách văn bản nhận dạng được (JSON) |
| `score` | Confidence score của OCR (JSON) |
| `ocr_center` | Tọa độ tâm văn bản (JSON) |

### Bước 6: Xử lý hậu kỳ CSV

**Hàm:** `process_csv_raw()` trong `utils/process_raw.py`

- Lọc chỉ giữ frame có bin code hợp lệ theo pattern `XX-NNN-P`
  - `XX`: 2 chữ cái (ví dụ `AT`, `BD`)
  - `NNN`: 3 chữ số (ví dụ `076`)
  - `P`: 1 chữ số 1–6 (số vị trí)
- Chọn text có confidence cao nhất và gần tâm nhất
- Xuất `output_processed.csv`

### Bước 7: Logic chọn frame đại diện

**Hàm:** `get_all_codes()` trong `utils/get_frame_position.py`

- Sửa lỗi OCR thường gặp trong prefix mã thùng (`edit_prefix()`)
- Nhóm các frame liên tiếp có cùng bin code (`group_code()`)
- Xác định cột kệ hàng (`get_cols()`)
- Với mỗi bin code, chọn 3 frame đại diện:
  - **code**: Frame nhìn thấy rõ mã thùng nhất
  - **front**: Frame nhìn thẳng mặt trước thùng (để đọc product ID)
  - **top**: Frame nhìn từ trên xuống mặt thùng (để kiểm tra độ đầy)

### Bước 8: Trích xuất và lưu kết quả

**Hàm:** `save_frames_by_metadata()` trong `utils/save_frame.py`

- Lưu 3 ảnh (code/front/top) vào thư mục riêng theo bin code
- Chạy **ProductIDReader** trên ảnh `front`: đọc mã sản phẩm 8 chữ số
- Chạy **Fullness Classifier** trên ảnh `front`: phân loại độ đầy (0/1/2)
- Trích xuất video clip ngắn cho từng thùng
- Tạo file `dict_total.json` tổng hợp kết quả

---

## 8. Các thành phần AI/ML

### 8.1 Frame Classifier (ResNet50)

**File:** `models/classifier.py`

**Mục đích:** Phân loại nhanh từng khung hình video

**Đầu vào:** Batch frame ảnh (sau khi crop ROI 10–40% chiều cao)

**Đầu ra:** Nhãn `background` / `carton` / `code`

**Chi tiết:**
- Kiến trúc: ResNet50 pretrained, thay đầu classifier → 3 classes
- Weights: `weights/resnet50_trained.pth`
- Inference GPU với batch size cấu hình được

---

### 8.2 Bin Code OCR (PaddleOCR Mobile)

**File:** `models/paddle_apdater.py`

**Mục đích:** Đọc mã thùng hàng từ frame được phân loại là `code`

**Đầu vào:** Batch ảnh crop (tối đa 40 ảnh/batch)

**Đầu ra:** List dict gồm `scores`, `texts`, `centers`

**Chi tiết:**
- Models: PP-OCRv5 mobile (nhẹ, nhanh)
- Pattern mã thùng: `XX-NNN-P` (ví dụ `AT-076-3`)
- Hỗ trợ xử lý song song trong thread riêng

---

### 8.3 Product ID Reader (PaddleOCR Server)

**File:** `models/product_id_reader.py`

**Mục đích:** Đọc mã sản phẩm 8 chữ số từ mặt trước thùng

**Đầu vào:** Ảnh `front`, crop vùng 20–80% chiều cao

**Đầu ra:** Mã sản phẩm (string 8 chữ số) + confidence score

**Chi tiết:**
- Models: PP-OCRv5 server (chính xác hơn mobile)
- Pattern validation: đúng 8 chữ số
- Batch processing có thể điều chỉnh

---

### 8.4 Fullness Classifier (ResNet50)

**File:** `models/classifier_check_inner.py`

**Mục đích:** Phân loại trạng thái độ đầy của thùng hàng

**Đầu vào:** Ảnh `front`, crop vùng tâm 30–70%

**Đầu ra:** Nhãn `0` (đầy) / `1` (một phần) / `2` (trống) + confidence

**Chi tiết:**
- Kiến trúc: ResNet50, 3 classes
- Singleton pattern (chỉ tạo một instance)
- Nhận numpy array, torch tensor, hoặc list

---

## 9. API Reference

### POST `/process-videos/`

Xử lý một hoặc nhiều video và trả về kết quả kiểm kê.

**Request Body:**

```json
{
  "video_input": "/path/to/video.mp4",
  "output_path": "outputs"
}
```

| Field | Type | Mô tả |
|-------|------|-------|
| `video_input` | `str` hoặc `list[str]` | Đường dẫn file video (1 hoặc nhiều) |
| `output_path` | `str` | Thư mục lưu kết quả |

**Response thành công (200):**

```json
{
  "AT-076-3": {
    "code": ["/outputs/AT-076-3/AT-076-3_code_20251025.jpg"],
    "front": ["/outputs/AT-076-3/AT-076-3_front_20251025.jpg"],
    "top": ["/outputs/AT-076-3/AT-076-3_top_20251025.jpg"],
    "video": ["/outputs/AT-076-3/AT-076-3.mp4"],
    "product_id": "12345678",
    "score_pid": 0.95,
    "empty": 1,
    "score_empty": 0.87
  },
  "BD-012-2": {
    "code": [...],
    "front": [...],
    "top": [...],
    "video": [...],
    "product_id": "87654321",
    "score_pid": 0.91,
    "empty": 0,
    "score_empty": 0.94
  }
}
```

**Giải thích các trường response:**

| Trường | Kiểu | Mô tả |
|--------|------|-------|
| `code` | `list[str]` | Đường dẫn ảnh nhìn thấy mã thùng |
| `front` | `list[str]` | Đường dẫn ảnh mặt trước thùng |
| `top` | `list[str]` | Đường dẫn ảnh nhìn từ trên |
| `video` | `list[str]` | Đường dẫn video clip thùng hàng |
| `product_id` | `str` | Mã sản phẩm 8 chữ số (hoặc rỗng) |
| `score_pid` | `float` | Confidence đọc product ID (0–1) |
| `empty` | `int` | Trạng thái: `0`=đầy, `1`=một phần, `2`=trống |
| `score_empty` | `float` | Confidence phân loại độ đầy (0–1) |

**Response lỗi (500):**

```json
{
  "error": "Mô tả lỗi",
  "traceback": "Chi tiết traceback"
}
```

**Cổng mặc định:**
- Production: `9998` (map sang `8000` nội bộ)
- Development: `9999`

---

## 10. Cấu trúc Output

### Cấu trúc thư mục kết quả

```
outputs/
├── <video_name>_result/
│   ├── <video_name>.mp4              # Video đã ghép nối
│   ├── output_raw.csv                # Kết quả frame-level thô
│   ├── output_processed.csv          # Kết quả đã lọc bin code
│   ├── dict_total.json               # Tổng hợp tất cả thùng hàng
│   └── <video_name>_result.log       # Log xử lý (múi giờ VN)
│
├── AT-076-3/
│   ├── AT-076-3_code_<timestamp>.jpg   # Ảnh thấy mã thùng
│   ├── AT-076-3_front_<timestamp>.jpg  # Ảnh mặt trước
│   ├── AT-076-3_top_<timestamp>.jpg    # Ảnh từ trên
│   └── AT-076-3.mp4                    # Video clip ngắn
│
├── AT-077-2/
│   └── ... (cấu trúc tương tự)
│
└── ... (một thư mục mỗi bin code)
```

### Định dạng `output_raw.csv`

```csv
frame_idx,label,ocr,score,ocr_center
0,background,[],[],[]
1,background,[],[],[]
42,code,"[\"AT-076-3\"]","[0.97]","[[540,120]]"
43,code,"[\"AT-076-3\"]","[0.95]","[[538,118]]"
100,carton,[],[],[]
```

### Định dạng `output_processed.csv`

Tương tự `output_raw.csv` nhưng chỉ giữ lại frame có bin code hợp lệ.

### Định dạng `dict_total.json`

```json
{
  "AT-076-3": {
    "code": ["/path/to/AT-076-3_code.jpg"],
    "front": ["/path/to/AT-076-3_front.jpg"],
    "top": ["/path/to/AT-076-3_top.jpg"],
    "video": ["/path/to/AT-076-3.mp4"],
    "product_id": "12345678",
    "score_pid": 0.95,
    "empty": 0,
    "score_empty": 0.92
  }
}
```

---

## 11. Docker Deployment

### `docker-compose.yml` — Production

```yaml
services:
  inventory-count-ai:
    image: decord2:20260805
    ports:
      - "9998:8000"           # Cổng public: 9998
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              capabilities: [compute, video]
              count: all       # Dùng tất cả GPU
    volumes:
      - ./:/app
      - /ssd1:/ssd1
      - /hdd1:/hdd1
    shm_size: "16gb"           # Shared memory cho GPU processing
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - DECORD_EOF_RETRY_MAX=20480
    command: uvicorn api_server:app --host 0.0.0.0 --port 8000
```

### `docker-compose.dev.yml` — Development

- Image: `decord2:20260605`
- Port: `9999:8000`
- Cấu hình tương tự production

### `docker-compose.test.yml` — Testing

- Image: `decord2:20260608`
- Đọc biến môi trường từ file `.env`
- Cấu hình GPU/storage linh động qua biến `SSD1`, `HDD1`

---

## 12. Các lớp & Interface chính

### `VideoProcessing` (`main.py`)

Lớp orchestration chính của pipeline.

```python
class VideoProcessing:
    def __init__(self, config_classifier: dict, config_ocr: dict)
    def infer_video(self, config_video: dict) -> tuple[pd.DataFrame, VideoReader]
    def start_ocr_thread(self)
    def stop_ocr_thread(self)
    def reset(self)
    def _ocr_worker(self)   # Thread worker nội bộ
```

---

### `Classifier` (`models/classifier.py`)

```python
class Classifier:
    def __init__(self, w_path: str, width: int = 2160, height: int = 2160)
    def predict(self, images: list) -> list[str]
    def transform_image(self, images: list) -> torch.Tensor
    def set_height_width(self, height: int, width: int)
    def set_angle(self, angle: float)
    def clear_cache(self)
```

---

### `PaddleOCRAdapter` (`models/paddle_apdater.py`)

```python
class PaddleOCRAdapter:
    def __init__(self, config: dict, width: int, height: int, angle: float)
    def predict(self, input: list, text_rec_score_thresh: float) -> list[dict]
    def clear_cache(self)
```

**Cấu trúc phần tử output:**
```python
{
    "scores": [0.97, 0.95],      # Confidence scores
    "texts": ["AT-076-3", ...],  # Văn bản nhận dạng
    "centers": [[540, 120], ...]  # Tọa độ tâm (x, y)
}
```

---

### `ProductIDReader` (`models/product_id_reader.py`)

```python
class ProductIDReader:
    def __init__(self, config: dict, width: int, height: int, angle: float)
    def predict(self, input: list, text_rec_score_thresh: float,
                batch_size: int) -> list[dict]
    def transform_image(self, images: list) -> list
    def clear_cache(self)
```

---

### `VideoReader` (`utils/video_reader.py`)

```python
class VideoReader:
    def __init__(self, path: str, device: str = "cuda")
    def get_batch(self, indices: list[int]) -> torch.Tensor   # (N, H, W, 3)
    def get_shape(self) -> tuple                               # (n_frames, H, W, 3)
    def get_fps(self) -> float
```

---

### Hàm tiện ích chính

| Hàm | File | Mô tả |
|-----|------|-------|
| `process_csv_raw(df)` | `utils/process_raw.py` | Lọc DataFrame theo pattern bin code |
| `get_all_codes(df, vr)` | `utils/get_frame_position.py` | Pipeline logic chọn frame đại diện |
| `save_frames_by_metadata(...)` | `utils/save_frame.py` | Lưu ảnh, chạy AI phụ, tạo dict_total.json |
| `get_pid(frames, reader)` | `utils/get_pid.py` | Đọc product ID từ danh sách frame |
| `check_inner(frames, clf)` | `utils/check_inner.py` | Phân loại độ đầy thùng |
| `concat_videos(paths)` | `main.py` | Ghép nhiều video bằng FFmpeg |

---

## 13. Sơ đồ luồng xử lý

```
Input: video_input (str | list[str])
          │
          ▼
    [concat_videos]
    Validate + ghép video bằng FFmpeg
          │
          ▼
    [VideoReader (Decord GPU)]
    Giải mã video bằng NVDEC
          │
          ▼
    ┌─────────────────────────────┐
    │   Xử lý theo batch frame    │
    │                             │
    │  Frame batch ──► Crop ROI   │
    │                  10-40% H   │
    │         │                   │
    │         ▼                   │
    │  [ResNet50 Classifier]      │    [OCR Thread - song song]
    │  background / carton / code │ ──► Queue code frames
    │         │                   │         │
    │         ▼                   │    [PaddleOCR Mobile]
    │  Ghi vào DataFrame          │    Detect + Recognize
    │                             │    text, score, center
    └─────────────────────────────┘         │
          │                                 │
          ▼                                 │
    [Merge kết quả ◄─────────────────────────┘
     vào DataFrame]
          │
          ▼
    [output_raw.csv]
    frame_idx, label, ocr, score, ocr_center
          │
          ▼
    [process_csv_raw]
    Lọc pattern XX-NNN-P
    Chọn text confidence cao & gần tâm nhất
          │
          ▼
    [output_processed.csv]
          │
          ▼
    [get_all_codes]
    ├─ edit_prefix(): Sửa lỗi OCR prefix
    ├─ group_code(): Nhóm frame liên tiếp
    ├─ get_cols(): Xác định cột kệ hàng
    └─ get_frames(): Chọn code/front/top
          │
          ▼
    [save_videos]
    Trích xuất video clip per bin (FFmpeg)
          │
          ▼
    [save_frames_by_metadata]
    ├─ Lưu 3 ảnh per bin code
    ├─ ProductIDReader → product_id, score_pid
    ├─ FullnessClassifier → empty, score_empty
    └─ Ghi dict_total.json
          │
          ▼
    Output:
    ├─ outputs/<bin_code>/*.jpg (3 ảnh/thùng)
    ├─ outputs/<bin_code>/*.mp4 (video clip)
    ├─ output_raw.csv
    ├─ output_processed.csv
    └─ dict_total.json
```

---

## Ghi chú quan trọng

- **Thư viện Decord:** Phiên bản tùy chỉnh hỗ trợ GPU NVDEC, build từ source trong `/decord/`
- **Tự động tải weights:** Nếu không tìm thấy file weights, hệ thống tự tải từ MinIO server
- **Múi giờ:** Toàn bộ log sử dụng múi giờ Việt Nam (Asia/Ho_Chi_Minh)
- **Định dạng bin code:** `XX-NNN-P` — `XX` là 2 chữ cái, `NNN` là 3 chữ số, `P` là vị trí 1–6
- **Không dùng database:** Tất cả kết quả lưu dưới dạng file (JSON, CSV, ảnh, video)
- **Multi-GPU:** Hỗ trợ đầy đủ nhiều GPU qua biến môi trường NVIDIA
- **Shared memory:** Cần ít nhất 16GB shm_size khi chạy Docker cho GPU processing
