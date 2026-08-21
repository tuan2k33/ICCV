#!/bin/bash
BASE="$(cd "$(dirname "$0")" && pwd)"
source $BASE/.env
ENV=${1:-test}

case "$ENV" in
  test)
    BACKEND_URL="http://$HOST:8086"
    PATH_DATA=$BASE
    PATH_TEMPLATE=$PATH_TEMPLATE_FILE
    FE_PORT=5174
    ;;
  dev)
    BACKEND_URL="http://$HOST:8080"
    PATH_DATA=/ssd1/inventory_count
    PATH_TEMPLATE=/ssd1/inventory_count/code/ic_be/template.xlsx
    FE_PORT=5173
    ;;
  *)
    echo "Usage: bash $0 [test|dev]"
    exit 1
    ;;
esac

echo ">>> [$ENV] Starting inventory count ($BACKEND_URL)"
echo ""

echo "=== [1/6] Kafka broker ==="
docker compose -f $BASE/docker-compose.kafka.$ENV.yml up -d

echo "=== [2/6] Backend (postgres + api) ==="
PATH_DATA=$PATH_DATA \
PATH_TEMPLATE_FILE=$PATH_TEMPLATE \
docker compose -f $BASE/ic_be/docker-compose.$ENV.yml up -d

echo "=== [3/6] AI module ==="
docker compose -f $BASE/ic_ai/docker-compose.$ENV.yml up -d --remove-orphans

echo "=== [4/6] Kafka consumer ==="
docker compose -f $BASE/kafka_consumer_service/docker-compose.$ENV.yml up -d

echo "=== [5/6] Frontend ==="
BACKEND_URL=$BACKEND_URL \
docker compose -f $BASE/ic_fe/docker-compose.$ENV.yml up -d

echo ""
echo "✓ Xong. Truy cập:"
echo "  Web   : http://$HOST:$FE_PORT  (backend → $BACKEND_URL)"
echo "  API   : $BACKEND_URL/docs"
echo "  Login : admin / Rsc@2025"
echo ""
echo "  VideoCopy (chạy tay):"
echo "    cd $BASE/VideoCopy && conda activate copyvideo && python main.py"
