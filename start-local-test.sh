#!/bin/bash
# Script đơn giản để test local

echo "=========================================="
echo "START LOCAL TEST"
echo "=========================================="
echo ""

# Tạo .env cho MySQL container
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

echo "✅ Đã tạo .env"
echo ""

# Start MySQL
echo "1. Starting MySQL container..."
docker compose -f docker-compose.local.yml up -d db

echo ""
echo "⏳ Đợi MySQL khởi động và import schema (40 giây)..."
sleep 40

# Verify MySQL
echo ""
echo "2. Verifying MySQL..."
docker compose -f docker-compose.local.yml exec -T db mysql -u tooltinhreveneu_1 -ptooltinhreveneu@gndhsggkl tooltinhreveneu_1 -e "SHOW TABLES;" 2>/dev/null

# Build và start API
echo ""
echo "3. Building and starting API..."
docker compose -f docker-compose.local.yml build api crawler
docker compose -f docker-compose.local.yml up -d api

echo ""
echo "⏳ Đợi API khởi động (10 giây)..."
sleep 10

# Test
echo ""
echo "4. Testing API..."
curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null || echo "API chưa sẵn sàng, đợi thêm..."

echo ""
echo "=========================================="
echo "✅ SETUP HOÀN TẤT"
echo "=========================================="
echo ""
echo "Bây giờ bạn có thể:"
echo ""
echo "1. Test Crawler:"
echo "   docker compose -f docker-compose.local.yml run --rm crawler --first-page-only"
echo ""
echo "2. Test API:"
echo "   curl http://localhost:8000/health"
echo "   curl http://localhost:8000/api/fetch-logs"
echo ""
echo "3. Xem Swagger UI:"
echo "   open http://localhost:8000/docs"
echo ""
echo "4. Xem logs:"
echo "   docker compose -f docker-compose.local.yml logs -f api"
echo ""
echo "5. Stop tất cả:"
echo "   docker compose -f docker-compose.local.yml down"
