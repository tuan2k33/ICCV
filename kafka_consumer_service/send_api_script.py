import os
import json
import logging
import requests
from collections import defaultdict

# --- Cấu hình logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Biến môi trường ---
UI_API_URL = os.environ.get("UI_API_URL", "http://localhost:8000/api/task")

# --- Hàm gọi API UI ---
def call_ui_api(rack_name, data):
    """
    Gọi API của giao diện để gửi dữ liệu đã xử lý.
    """
    query_params = {
        "rack_name": rack_name,
        "tenant_id": 1
    }

    logging.info(f"Calling UI API [PUT] for group '{rack_name}' with {len(data)} racks.")
    logging.info(f"UI API URL: {UI_API_URL}")
    logging.info(f"UI API Query Params: {query_params}")
    logging.info(f"UI API JSON Body contains {len(data)} items.")

    # print(f"Debug: Sending data for group '{rack_name}' to UI API.")
    # print(f"Debug: UI API URL: {UI_API_URL}")
    # print(f"Debug: UI API Query Params: {query_params}")
    # print(f"Debug: UI API JSON Body: {json.dumps(data)[:500]}...")  # Chỉ in một phần để tránh quá dài

    # raise("Debug Exception: Stopping before actual API call.")

    try:
        response = requests.put(UI_API_URL, params=query_params, json=data, timeout=60)
        response.raise_for_status()
        logging.info(f"✅ Sent data for group '{rack_name}' to UI API. Status: {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        if e.response is not None:
            logging.error(f"❌ Error calling UI API for group '{rack_name}'. "
                          f"Status: {e.response.status_code}, Response: {e.response.text}")
        else:
            logging.error(f"❌ Error calling UI API for group '{rack_name}': {e}")
        return False


# --- Hàm xử lý đường dẫn ---
def ensure_output_prefix(data):
    """
    Đảm bảo tất cả các đường dẫn đều có prefix 'output/'.
    Nếu đã có thì giữ nguyên.
    """
    updated = {}
    for rack_name, rack_data in data.items():
        new_rack_data = {}
        for key, value in rack_data.items():
            if key == "product_id":
                new_rack_data[key] = value
                continue
            if isinstance(value, list):
                new_rack_data[key] = [
                    v if v.startswith("output/") else f"output/{v}"
                    for v in value
                ]
            elif isinstance(value, str):
                new_rack_data[key] = value if value.startswith("output/") else f"output/{value}"
            else:
                new_rack_data[key] = value
        updated[rack_name] = new_rack_data
    return updated


# --- Nhóm và gửi lên UI ---
def group_and_send_to_ui(processing_result):
    """
    Nhóm kết quả theo prefix + odd/even và gửi đến UI API.
    """
    grouped_racks = defaultdict(dict)

    for original_rack_name, rack_data in processing_result.items():
        try:
            parts = original_rack_name.split('-')
            if len(parts) < 2:
                logging.warning(f"Skipping invalid rack name: {original_rack_name}")
                continue

            prefix = parts[0]
            number_str = parts[1]
            rack_number = int(number_str)
            parity = "odd" if rack_number % 2 != 0 else "even"
            group_name = f"{prefix}-{parity}"

            grouped_racks[group_name][original_rack_name] = rack_data
        except (ValueError, IndexError) as e:
            logging.warning(f"Could not parse rack name '{original_rack_name}': {e}. Skipping.")
            continue

    if not grouped_racks:
        logging.warning("No valid racks found to send.")
        return

    logging.info(f"📦 Grouped racks into {len(grouped_racks)} groups: {list(grouped_racks.keys())}")

    for group_name, data in grouped_racks.items():
        call_ui_api(rack_name=group_name, data=data)


# --- Main ---
def main():
    import argparse
    parser = argparse.ArgumentParser(description="Send processed video results to UI API from JSON file")
    parser.add_argument("json_path", help="Path to the JSON file containing processed results")
    args = parser.parse_args()

    json_path = args.json_path

    if not os.path.exists(json_path):
        logging.error(f"File not found: {json_path}")
        return

    logging.info(f"📂 Loading processed result file: {json_path}")
    with open(json_path, "r") as f:
        processing_result = json.load(f)

    # Thêm prefix output/ nếu thiếu
    processing_result = ensure_output_prefix(processing_result)

    # Gửi đến UI API
    group_and_send_to_ui(processing_result)


if __name__ == "__main__":
    main()
