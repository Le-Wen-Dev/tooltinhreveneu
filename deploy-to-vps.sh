#!/bin/bash
# Deploy toàn bộ thay đổi lên VPS: build image linux/amd64, save tar, hướng dẫn upload & chạy
# Chạy trong thư mục gốc project: ./deploy-to-vps.sh

set -e
cd "$(dirname "$0")"

# Cấu hình VPS (sửa theo server của bạn)
VPS_USER="${VPS_USER:-root}"
VPS_HOST="${VPS_HOST:-103.37.60.86}"
VPS_PATH="${VPS_PATH:-/srv/toolgetdata}"
SCP_PORT="${SCP_PORT:-22}"
# Domain chạy app (dùng cho BASE_URL trong .env trên VPS)
DOMAIN="${DOMAIN:-beta.gliacloud.online}"

echo "=========================================="
echo "Deploy lên VPS (linux/amd64)"
echo "=========================================="
echo ""

# 1. Build images cho linux/amd64 (tránh exec format error trên VPS x86)
echo "1. Building API image (linux/amd64)..."
docker buildx build --platform linux/amd64 -t toolgetdata-api:latest -f api/Dockerfile . --load

echo ""
echo "2. Building Crawler image (linux/amd64)..."
docker buildx build --platform linux/amd64 -t toolgetdata-crawler:latest -f crawler/Dockerfile . --load

echo ""
echo "3. Saving images to tar..."
docker save toolgetdata-api:latest -o api-image.tar
docker save toolgetdata-crawler:latest -o crawler-image.tar

echo ""
echo "4. Kích thước:"
du -h api-image.tar crawler-image.tar

echo ""
echo "=========================================="
echo "Bước tiếp: upload lên VPS và chạy"
echo "=========================================="
echo ""
echo "A. Upload từ máy bạn (chạy lần lượt):"
echo ""
echo "  scp -P $SCP_PORT api-image.tar crawler-image.tar $VPS_USER@$VPS_HOST:$VPS_PATH/"
echo "  scp -P $SCP_PORT docker-compose.vps.yml $VPS_USER@$VPS_HOST:$VPS_PATH/"
echo "  scp -P $SCP_PORT database_schema_complete.sql migrations_add_users_table.sql seed_users.sql $VPS_USER@$VPS_HOST:$VPS_PATH/"
echo "  scp -P $SCP_PORT run-crawler.sh $VPS_USER@$VPS_HOST:$VPS_PATH/"
echo ""
echo "  # Upload .env (có mật khẩu, cẩn thận):"
echo "  # Trên VPS đảm bảo .env có: BASE_URL=https://$DOMAIN"
echo "  scp -P $SCP_PORT .env $VPS_USER@$VPS_HOST:$VPS_PATH/"
echo ""
echo "B. Trên VPS (ssh vào rồi chạy):"
echo ""
echo "  ssh -p $SCP_PORT $VPS_USER@$VPS_HOST"
echo "  cd $VPS_PATH"
echo ""
echo "  # Đảm bảo .env có BASE_URL=https://$DOMAIN (link API Docs, v.v.)"
echo ""
echo "  # Nếu đổi domain mới: chạy certbot để lấy SSL cho domain đó (Nginx/Caddy trên VPS):"
echo "  #   sudo certbot --nginx -d $DOMAIN   # hoặc certbot --caddy -d $DOMAIN"
echo ""
echo "  # Load images"
echo "  docker load -i api-image.tar"
echo "  docker load -i crawler-image.tar"
echo ""
echo "  # Dừng bản cũ, chạy bản mới"
echo "  docker-compose -f docker-compose.vps.yml down   # hoặc: docker compose -f docker-compose.vps.yml down"
echo "  docker-compose -f docker-compose.vps.yml up -d   # hoặc: docker compose -f docker-compose.vps.yml up -d"
echo ""
echo "  # Nếu DB đã có từ trước, chỉ cần seed user (1 lần):"
echo "  docker-compose -f docker-compose.vps.yml exec -T db mysql -u \${DB_USER} -p\${DB_PASSWORD} \${DB_NAME} < seed_users.sql"
echo "  # Hoặc thay bằng mật khẩu thật:"
echo "  docker-compose -f docker-compose.vps.yml exec -T db mysql -u tooltinhreveneu_1 -p'YOUR_PASSWORD' tooltinhreveneu_1 < seed_users.sql"
echo ""
echo "  # Kiểm tra"
echo "  docker-compose -f docker-compose.vps.yml ps"
echo "  curl http://localhost:8000/health"
echo ""
echo "C. Cron (2 lần/ngày):"
echo "  crontab -e"
echo "  # Thêm: 0 1,13 * * * cd $VPS_PATH && docker-compose -f docker-compose.vps.yml run --rm crawler >> /var/log/revenue-crawler.log 2>&1"
echo ""
echo "Xong. Sửa VPS_USER, VPS_HOST, VPS_PATH, SCP_PORT, DOMAIN ở đầu script nếu cần."
echo ""
