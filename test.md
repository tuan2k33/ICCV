# START — Full Flow (tuannq test env)

| Service | Module | Container (test) | Port test | Port dev |
|---|---|---|---|---|
| Kafka broker | infra | `ic_kafka_test` | 9093 | 9092 |
| BE postgres | AI_IC_BE | `ic_db_test` | 5434 | 5000 |
| BE api | AI_IC_BE | `ic_be_test` | 8086 | 8080 |
| AI module | inventory-count-ai | `ic_ai_test` | 9998 | 9999 |
| Kafka consumer | kafka_consumer_service | `ic_consumer_test` | — | — |
| Frontend | AI_IC | `ic_fe_test` | 5174 | 5173 |
| VideoCopy | VideoCopy | native (conda) | — | — |

---

## Thứ tự khởi động

### 1. Kafka broker
```bash
docker compose -f /ssd1/tuannq/inventory_count/docker-compose.kafka.yml up -d
```
Containers: `ic_zookeeper_test` + `ic_kafka_test` (`:9093`)

### 2. Backend
```bash
PATH_DATA=/ssd1/tuannq/inventory_count \
PATH_TEMPLATE_FILE=/ssd1/tuannq/inventory_count/code/AI_IC_BE/template.xlsx \
docker compose -f /ssd1/tuannq/inventory_count/code/AI_IC_BE/docker-compose.yml up -d
```
Containers: `ic_db_test` (`:5434`) + `ic_be_test` (`:8086`)

### 3. AI module
```bash
docker compose -f /ssd1/tuannq/inventory_count/inventory-count-ai/docker-compose.yml up -d
```
Container: `ic_ai_test` (`:9998`)

### 4. Kafka consumer
```bash
docker compose -f /ssd1/tuannq/inventory_count/kafka_consumer_service/docker-compose.yml up -d
```
Container: `ic_consumer_test` — trỏ AI `:9998`, BE `:8086`

### 5. Frontend
```bash
docker compose -f /ssd1/tuannq/inventory_count/code/AI_IC/docker-compose.yml up -d
```
Container: `ic_fe_test` (`:5174`)

### 6. VideoCopy
```bash
cd /ssd1/tuannq/inventory_count/code/VideoCopy
conda activate copyvideo
python main.py
```
> Kafka target đọc từ `config.json` cùng thư mục (`kafka_servers`, `kafka_topic`)

---

## Truy cập
| | URL | Login |
|---|---|---|
| Web | `http://192.168.0.200:5174` | `admin / Rsc@2025` |
| API docs | `http://192.168.0.200:8086/docs` | — |
