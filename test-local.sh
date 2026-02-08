#!/bin/bash
# Script test project trên local

echo "=========================================="
echo "TEST PROJECT TRÊN LOCAL"
echo "=========================================="
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker chưa được cài đặt!"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "❌ Docker chưa chạy! Vui lòng start Docker Desktop"
    exit 1
fi

echo "✅ Docker đang chạy"
echo ""

# Copy .env.local to .env
if [ -f .env.local ]; then
    cp .env.local .env
    echo "✅ Đã copy .env.local → .env"
else
    echo "⚠️  Không tìm thấy .env.local, tạo file .env mới..."
    cat > .env << EOF
DB_TYPE=mysql
DB_HOST=localhost
DB_PORT=3306
DB_NAME=tooltinhreveneu_1
DB_USER=tooltinhreveneu_1
DB_PASSWORD=tooltinhreveneu@gndhsggkl
SCRAPER_USERNAME=maxvaluemedia
SCRAPER_PASSWORD=gliacloud
API_PORT=8000
EOF
fi

echo ""
echo "=========================================="
echo "1. BUILD IMAGES"
echo "=========================================="
docker compose build

echo ""
echo "=========================================="
echo "2. START API SERVICE"
echo "=========================================="
docker compose up -d api

echo ""
echo "⏳ Đợi API khởi động (5 giây)..."
sleep 5

echo ""
echo "=========================================="
echo "3. TEST API HEALTH"
echo "=========================================="
HEALTH=$(curl -s http://localhost:8000/health)
if [ $? -eq 0 ]; then
    echo "✅ API đang chạy:"
    echo "$HEALTH" | python3 -m json.tool 2>/dev/null || echo "$HEALTH"
else
    echo "❌ API chưa sẵn sàng"
    echo "Check logs: docker compose logs api"
fi

echo ""
echo "=========================================="
echo "4. TEST CRAWLER (First Page Only)"
echo "=========================================="
echo "Đang chạy crawler test..."
docker compose run --rm crawler --first-page-only

echo ""
echo "=========================================="
echo "5. TEST API ENDPOINTS"
echo "=========================================="

echo ""
echo "📊 Fetch Logs:"
curl -s http://localhost:8000/api/fetch-logs | python3 -m json.tool 2>/dev/null | head -20

echo ""
echo "📈 Aggregated Metrics:"
curl -s http://localhost:8000/api/aggregated-metrics | python3 -m json.tool 2>/dev/null | head -20

echo ""
echo "📋 Raw Data:"
curl -s "http://localhost:8000/api/raw-data?limit=5" | python3 -m json.tool 2>/dev/null | head -30

echo ""
echo "=========================================="
echo "✅ TEST HOÀN TẤT"
echo "=========================================="
echo ""
echo "API đang chạy tại: http://localhost:8000"
echo "Swagger UI: http://localhost:8000/docs"
echo ""
echo "Để xem logs:"
echo "  docker compose logs api"
echo "  docker compose logs crawler"
echo ""
echo "Để stop:"
echo "  docker compose down"
