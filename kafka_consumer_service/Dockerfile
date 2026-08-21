# Sử dụng một base image Python nhẹ
FROM python:3.9-slim

# Thiết lập thư mục làm việc trong container
WORKDIR /app

# Sao chép file requirements và cài đặt các dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép mã nguồn của ứng dụng
COPY . .

# Lệnh để chạy ứng dụng khi container khởi động
CMD ["python", "consumer_service.py"]