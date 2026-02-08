#!/bin/bash
# Script test project trên local với MySQL container

echo "=========================================="
echo "TEST PROJECT TRÊN LOCAL (Với MySQL Container)"
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

# Copy .env
if [ -f .env.local.mysql ]; then
    cp .env.local.mysql .env
    echo "✅ Đã copy .env.local.mysql → .env"
else
    echo "⚠️  Tạo file .env mới..."
    cat > .env << EOF
DB_TYPE=mysql
DB_HOST=db
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
echo "1. START MYSQL CONTAINER"
echo "=========================================="
docker compose -f docker-compose.local.yml up -d db

echo ""
echo "⏳ Đợi MySQL khởi động (30 giây)..."
sleep 30

echo ""
echo "=========================================="
echo "2. VERIFY MYSQL"
echo "=========================================="
docker compose -f docker-compose.local.yml exec -T db mysql -u tooltinhreveneu_1 -ptooltinhreveneu@gndhsggkl tooltinhreveneu_1 -e "SHOW TABLES;" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ MySQL đã sẵn sàng và schema đã được import"
else
    echo "⚠️  MySQL đang khởi động, đợi thêm..."
    sleep 10
fi

echo ""
echo "=========================================="
echo "3. BUILD IMAGES"
echo "=========================================="
docker compose -f docker-compose.local.yml build

echo ""
echo "=========================================="
echo "4. START API SERVICE"
echo "=========================================="
docker compose -f docker-compose.local.yml up -d api

echo ""
echo "⏳ Đợi API khởi động (10 giây)..."
sleep 10

echo ""
echo "=========================================="
echo "5. TEST API HEALTH"
echo "=========================================="
HEALTH=$(curl -s http://localhost:8000/health 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "✅ API đang chạy:"
    echo "$HEALTH" | python3 -m json.tool 2>/dev/null || echo "$HEALTH"
else
    echo "❌ API chưa sẵn sàng"
    echo "Check logs: docker compose -f docker-compose.local.yml logs api"
    docker compose -f docker-compose.local.yml logs api | tail -20
fi

echo ""
echo "=========================================="
echo "6. TEST CRAWLER (First Page Only)"
echo "=========================================="
echo "Đang chạy crawler test..."
docker compose -f docker-compose.local.yml run --rm crawler --first-page-only

echo ""
echo "=========================================="
echo "7. TEST API ENDPOINTS"
echo "=========================================="

echo ""
echo "📊 Fetch Logs:"
curl -s http://localhost:8000/api/fetch-logs 2>/dev/null | python3 -m json.tool 2>/dev/null | head -30 || echo "No data"

echo ""
echo "📈 Aggregated Metrics:"
curl -s http://localhost:8000/api/aggregated-metrics 2>/dev/null | python3 -m json.tool 2>/dev/null | head -30 || echo "No data"

echo ""
echo "📋 Raw Data:"
curl -s "http://localhost:8000/api/raw-data?limit=5" 2>/dev/null | python3 -m json.tool 2>/dev/null | head -40 || echo "No data"

echo ""
echo "📐 Formulas:"
curl -s http://localhost:8000/api/formulas 2>/dev/null | python3 -m json.tool 2>/dev/null | head -30 || echo "No data"

echo ""
echo "=========================================="
echo "✅ TEST HOÀN TẤT"
echo "=========================================="
echo ""
echo "API đang chạy tại: http://localhost:8000"
echo "Swagger UI: http://localhost:8000/docs"
echo ""
echo "Để xem logs:"
echo "  docker compose -f docker-compose.local.yml logs api"
echo "  docker compose -f docker-compose.local.yml logs crawler"
echo "  docker compose -f docker-compose.local.yml logs db"
echo ""
echo "Để stop tất cả:"
echo "  docker compose -f docker-compose.local.yml down"
echo ""
echo "Để xóa database volume (reset):"
echo "  docker compose -f docker-compose.local.yml down -v"
