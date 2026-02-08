#!/bin/bash
# Script để save Docker images và hướng dẫn push lên VPS

echo "=========================================="
echo "Save Docker Images để Push lên VPS"
echo "=========================================="
echo ""

# Build images nếu chưa có
echo "1. Building images..."
docker compose build crawler api

# Save images
echo ""
echo "2. Saving images..."
docker save toolgetdata-crawler:latest -o crawler-image.tar
docker save toolgetdata-api:latest -o api-image.tar

echo ""
echo "✅ Images đã được save:"
echo "   - crawler-image.tar"
echo "   - api-image.tar"
echo ""

# Tính kích thước
CRAWLER_SIZE=$(du -h crawler-image.tar 2>/dev/null | cut -f1 || echo "N/A")
API_SIZE=$(du -h api-image.tar 2>/dev/null | cut -f1 || echo "N/A")

echo "Kích thước:"
echo "   - Crawler: $CRAWLER_SIZE"
echo "   - API: $API_SIZE"
echo ""

echo "=========================================="
echo "Hướng dẫn Push lên VPS:"
echo "=========================================="
echo ""
echo "1. Upload images và files lên VPS:"
echo "   scp -P 2222 crawler-image.tar api-image.tar docker-compose.yml database_schema_complete.sql .env.production tooltinhreveneu@gmail.com@36.50.27.158:/srv/toolgetdata/"
echo ""
echo "2. SSH vào VPS:"
echo "   ssh tooltinhreveneu@gmail.com@36.50.27.158 -p 2222"
echo ""
echo "3. Load images trên VPS:"
echo "   cd /srv/toolgetdata"
echo "   docker load -i crawler-image.tar"
echo "   docker load -i api-image.tar"
echo ""
echo "4. Setup .env:"
echo "   cp .env.production .env"
echo ""
echo "5. Start services (MySQL sẽ tự động import schema):"
echo "   docker compose up -d"
echo ""
echo "6. Verify:"
echo "   docker compose ps"
echo "   curl http://localhost:8000/health"
echo ""
echo "7. Test crawler:"
echo "   docker compose run --rm crawler --first-page-only"
echo ""
