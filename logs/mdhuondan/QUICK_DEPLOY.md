# Quick Deploy Guide - Tóm Tắt Nhanh

## ✅ Đã Hoàn Thành

### Docker Images:
- ✅ `toolgetdata-crawler:latest` (137MB)
- ✅ `toolgetdata-api:latest` (141MB)
- ✅ Đã save thành: `crawler-image.tar` và `api-image.tar`

## 🚀 Deploy Lên VPS (3 Bước)

### 1. Upload Images
```bash
scp -P 2222 crawler-image.tar api-image.tar docker-compose.yml database_schema_complete.sql tooltinhreveneu@gmail.com@36.50.27.158:/srv/toolgetdata/
```

### 2. SSH và Setup
```bash
ssh tooltinhreveneu@gmail.com@36.50.27.158 -p 2222
cd /srv/toolgetdata

# Load images
docker load -i crawler-image.tar
docker load -i api-image.tar

# Import database (1 lần duy nhất)
mysql -u tooltinhreveneu_1 -p tooltinhreveneu_1 < database_schema_complete.sql

# Tạo .env
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

# Start API
docker compose up -d api

# Test crawler
docker compose run --rm crawler --first-page-only
```

### 3. Setup Cron
```bash
crontab -e
# Thêm:
0 1,13 * * * cd /srv/toolgetdata && docker compose run --rm crawler >> /var/log/revenue-crawler.log 2>&1
```

## ❓ Về MySQL

**KHÔNG CẦN** setup MySQL gì thêm vì:
- ✅ MySQL đã có sẵn trên VPS
- ✅ Database `tooltinhreveneu_1` đã tồn tại
- ✅ Chỉ cần import schema 1 lần: `database_schema_complete.sql`

## 📝 Files Cần Upload

1. `crawler-image.tar` - Crawler image
2. `api-image.tar` - API image
3. `docker-compose.yml` - Docker config
4. `database_schema_complete.sql` - Database schema

## ✅ Sau Khi Deploy

- API: `http://36.50.27.158:8000`
- Health: `curl http://36.50.27.158:8000/health`
- Metrics: `curl http://36.50.27.158:8000/api/aggregated-metrics`

Xem chi tiết: `DEPLOY_TO_VPS.md`
