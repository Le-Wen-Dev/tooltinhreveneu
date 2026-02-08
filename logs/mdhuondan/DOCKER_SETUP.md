# Docker Setup Guide

## 📁 Cấu Trúc Project

```
revenue-crawler/
├── crawler/
│   ├── main.py          # Crawler service
│   ├── db.py            # Database models
│   ├── lock.py          # Lock mechanism
│   ├── requirements.txt
│   └── Dockerfile
├── api/
│   ├── main.py          # FastAPI service
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml
├── .env
└── database_schema_complete.sql
```

## 🚀 Setup

### 1. Tạo file .env

```bash
cp .env.example .env
# Sửa thông tin database trong .env
```

### 2. Build và chạy

```bash
# Build images
docker compose build

# Chạy API service (background)
docker compose up -d api db

# Test crawler (manual)
docker compose run --rm crawler

# Hoặc với date cụ thể
docker compose run --rm crawler --date 2026-01-26
```

## ⏱ Cron Job Setup (VPS)

### Tạo cron job

```bash
crontab -e
```

Thêm dòng:

```bash
# Chạy crawler mỗi ngày lúc 1:00 AM và 1:00 PM
0 1,13 * * * cd /srv/revenue-crawler && docker compose run --rm crawler >> /var/log/revenue-crawler.log 2>&1
```

### Hoặc script wrapper

Tạo file `/srv/revenue-crawler/run-crawler.sh`:

```bash
#!/bin/bash
cd /srv/revenue-crawler
docker compose run --rm crawler >> /var/log/revenue-crawler.log 2>&1
```

Chmod:
```bash
chmod +x /srv/revenue-crawler/run-crawler.sh
```

Cron:
```bash
0 1,13 * * * /srv/revenue-crawler/run-crawler.sh
```

## 🔒 Bảo Mật

### 1. MySQL không mở public

Trong `docker-compose.yml`, bỏ port mapping nếu không cần:
```yaml
# Bỏ dòng này nếu không cần access từ ngoài
ports:
  - "3306:3306"
```

### 2. DB user riêng cho crawler

Đã có trong schema:
- User: `tooltinhreveneu_1`
- Chỉ có quyền trên database `tooltinhreveneu_1`

### 3. Log ra file

Logs được lưu vào:
- `/app/logs/crawler.log` (trong container)
- Mount vào `./logs` (host)

### 4. Lock mechanism

Crawler tự động lock để tránh chạy trùng:
- Table: `crawl_runs`
- Check PID để detect stale locks

### 5. Retry logic

Có thể thêm retry trong `crawler/main.py` nếu cần.

## 📊 Workflow

```
1. Cron trigger → docker compose run crawler
2. Crawler fetch data → lưu raw_revenue_data
3. Calculator tính formulas → lưu computed_metrics & aggregated_metrics
4. API query metrics → trả JSON
```

## 🧪 Test

### Test crawler:
```bash
docker compose run --rm crawler --first-page-only
```

### Test API:
```bash
# Start API
docker compose up -d api

# Test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/aggregated-metrics
curl http://localhost:8000/api/fetch-logs
```

### Test database:
```bash
docker compose exec db mysql -u tooltinhreveneu_1 -p tooltinhreveneu_1
```

## 🔄 Update/Deploy

```bash
# Pull code mới
git pull

# Rebuild images
docker compose build

# Restart services
docker compose up -d --force-recreate api

# Crawler tự động dùng image mới khi cron chạy
```

## 📝 Production Checklist

- [ ] `.env` file với credentials đúng
- [ ] Database schema đã import
- [ ] Cron job đã setup
- [ ] Logs directory có quyền write
- [ ] MySQL không expose ra ngoài
- [ ] API có reverse proxy (nginx) nếu cần
- [ ] Backup strategy cho database volume

## 🐛 Troubleshooting

### Crawler không chạy:
```bash
# Check logs
docker compose logs crawler
tail -f /var/log/revenue-crawler.log

# Test manual
docker compose run --rm crawler --first-page-only
```

### API không kết nối DB:
```bash
# Check DB connection
docker compose exec api python -c "from crawler.db import engine; engine.connect()"

# Check logs
docker compose logs api
```

### Lock không release:
```sql
-- Manual cleanup
DELETE FROM crawl_runs WHERE status = 'running' AND completed_at IS NULL;
```
