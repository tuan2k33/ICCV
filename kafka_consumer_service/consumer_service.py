import os
import json
import logging
import time
import requests
from kafka import KafkaConsumer
from collections import defaultdict # Import defaultdict để nhóm dễ dàng hơn

# --- Các phần khác của file giữ nguyên ---
# Cấu hình logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Lấy cấu hình từ biến môi trường
KAFKA_BROKER_URL = os.environ.get("KAFKA_BROKER_URL", "localhost:9092")
KAFKA_TOPIC = os.environ.get("KAFKA_TOPIC", "video_copy_events")
PROCESSING_API_URL = os.environ.get("PROCESSING_API_URL", "http://localhost:9999/process-videos/")
UI_API_URL = os.environ.get("UI_API_URL", "http://localhost:8000/api/task")
AI_FOLDER_PATH = os.environ.get("AI_FOLDER_PATH", "/ssd1/inventory_count/")
AI_OUTPUT_SUBPATH = os.environ.get("AI_OUTPUT_SUBPATH", "output/")
AI_OUTPUT_PATH = os.path.join(AI_FOLDER_PATH, AI_OUTPUT_SUBPATH)
KAFKA_GROUP_ID = os.environ.get("KAFKA_GROUP_ID", "video_processing_group")

def connect_to_kafka(broker_url, topic):
    """
    Cố gắng kết nối tới Kafka consumer. Sẽ thử lại nếu thất bại.
    """
    while True:
        try:
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=broker_url.split(','),
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='earliest',
                group_id=KAFKA_GROUP_ID,
                max_poll_interval_ms=7200000, # 2 giờ
            )
            logging.info(f"Successfully connected to Kafka at {broker_url} and joined group '{KAFKA_GROUP_ID}'. Waiting for messages...")
            return consumer
        except Exception as e:
            logging.error(f"Failed to connect to Kafka: {e}. Retrying in 5 seconds...")
            time.sleep(5)

def call_processing_api(video_paths):
    """
    Gọi API xử lý video và trả về kết quả.
    """
    video_input_payload = video_paths[0] if len(video_paths) == 1 else video_paths
    
    payload = {
        "video_input": video_input_payload,
        "output_path": AI_OUTPUT_PATH
    }
    logging.info(f"Calling processing API: {PROCESSING_API_URL} with payload: {json.dumps(payload)}")
    try:
        response = requests.post(PROCESSING_API_URL, json=payload, timeout=3600)
        response.raise_for_status() 
        
        response_data = response.json()
        if "detail" in response_data and "error" in response_data["detail"]:
             logging.error(f"Processing API returned an error: {response_data['detail']['error']}")
             return None
             
        logging.info("Successfully received response from processing API.")
        logging.info(f"Processing API response data: {json.dumps(response_data)}")
        return response_data
    except requests.exceptions.RequestException as e:
        logging.error(f"Error calling processing API: {e}")
        return None

def call_ui_api(rack_name, data):
    """
    Gọi API của giao diện để gửi dữ liệu đã xử lý.
    Gửi rack_name và tenant_id dưới dạng query params,
    và data dưới dạng JSON body.
    """
    query_params = {
        "rack_name": rack_name,
        "tenant_id": 1
    }
    
    logging.info(f"Calling UI API [PUT] for group '{rack_name}' with {len(data)} racks.")
    logging.info(f"UI API URL: {UI_API_URL}")
    logging.info(f"UI API Query Params: {query_params}")
    logging.info(f"UI API JSON Body contains {len(data)} items.")
    
    try:
        response = requests.put(UI_API_URL, params=query_params, json=data, timeout=60)
        
        response.raise_for_status()
        logging.info(f"Successfully sent data for group '{rack_name}' to UI API. Status: {response.status_code}, Response: {response.text}")
        return True
    except requests.exceptions.RequestException as e:
        if e.response is not None:
             logging.error(f"Error calling UI API for group '{rack_name}'. Status: {e.response.status_code}, Response: {e.response.text}")
        else:
             logging.error(f"Error calling UI API for group '{rack_name}': {e}")
        return False

# --- LOGIC MỚI BẮT ĐẦU TỪ ĐÂY ---
def group_and_send_to_ui(processing_result):
    """
    Nhóm kết quả từ API xử lý và gửi đến API của UI.
    """
    # Sử dụng defaultdict để tự động tạo dictionary rỗng cho nhóm mới
    grouped_racks = defaultdict(dict)

    for original_rack_name, rack_data in processing_result.items():
        try:
            parts = original_rack_name.split('-')
            if len(parts) < 2:
                logging.warning(f"Skipping rack with invalid name format: {original_rack_name}")
                continue

            prefix = parts[0]  # Ví dụ: 'BB'
            number_str = parts[1] # Ví dụ: '079'
            
            rack_number = int(number_str)
            parity = "odd" if rack_number % 2 != 0 else "even"
            
            # Tên nhóm, ví dụ: 'BB-odd' hoặc 'BB-even'
            group_name = f"{prefix}-{parity}"
            
            # Thêm rack hiện tại vào nhóm của nó
            # grouped_racks['BB-odd']['BB-079-6'] = rack_data
            grouped_racks[group_name][original_rack_name] = rack_data

        except (ValueError, IndexError) as e:
            logging.warning(f"Could not parse rack name '{original_rack_name}': {e}. Skipping.")
            continue
    
    if not grouped_racks:
        logging.warning("No valid racks found to group and send.")
        return

    logging.info(f"Grouped racks into {len(grouped_racks)} groups: {list(grouped_racks.keys())}")

    for group_name, data in grouped_racks.items():
        call_ui_api(rack_name=group_name, data=data)

def trim_ai_paths(data, ai_folder_path):
    """
    Loại bỏ tiền tố AI_FOLDER_PATH khỏi tất cả các đường dẫn trong dữ liệu trả về.
    """
    trimmed = {}
    for rack_name, rack_data in data.items():
        new_rack_data = {}
        for key, value in rack_data.items():
            if isinstance(value, list):
                # Nếu là danh sách đường dẫn
                new_rack_data[key] = [v.replace(ai_folder_path, '') for v in value]
            elif isinstance(value, str):
                # Nếu là chuỗi (đề phòng có string path)
                new_rack_data[key] = value.replace(ai_folder_path, '')
            else:
                # Giữ nguyên các giá trị khác (số, bool, float, dict,...)
                new_rack_data[key] = value
        trimmed[rack_name] = new_rack_data
    return trimmed

def main():
    logging.info("Starting Kafka consumer service...")
    consumer = connect_to_kafka(KAFKA_BROKER_URL, KAFKA_TOPIC)
    
    for message in consumer:
        try:
            event_data = message.value
            logging.info(f"Received new message: {event_data}")

            if event_data.get('event_type') == 'copy_complete':
                copied_files = event_data.get('copied_files', [])
                if not copied_files:
                    logging.warning("Message received but 'copied_files' is empty. Skipping.")
                    continue
                
                # 1. Gọi API xử lý video
                processing_result = call_processing_api(copied_files)

                # 2. Xử lý kết quả và gọi API của UI
                if processing_result and "message" not in processing_result:
                    processing_result = trim_ai_paths(processing_result, AI_FOLDER_PATH)
                    group_and_send_to_ui(processing_result)
                elif processing_result:
                    logging.warning(f"Processing API returned no rack data: {processing_result}")
                else:
                    logging.error("Failed to get result from processing API. No data to send to UI.")
                    
        except json.JSONDecodeError as e:
            logging.error(f"Could not decode message value: {message.value}. Error: {e}")
        except Exception as e:
            # Thêm traceback để debug lỗi dễ hơn
            logging.error(f"An unexpected error occurred while processing message:", exc_info=True)


if __name__ == "__main__":
    main()