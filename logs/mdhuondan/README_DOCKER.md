# Docker Setup - Quick Start

## ✅ Đã Setup

### Cấu trúc:
```
├── crawler/          # Crawler service (chạy xong exit)
├── api/              # FastAPI service (chạy liên tục)
├── docker-compose.yml
└── .env
```

### Luồng hoạt động:
1. **Crawler** → Fetch data → Lưu DB → Tính formulas → Exit
2. **API** → Query metrics → Trả JSON
3. **Cron** → Trigger crawler 2 lần/ngày

## 🚀 Quick Start

### 1. Setup .env
```bash
cp .env.example .env
# Sửa DB_HOST=db (hoặc localhost nếu dùng DB ngoài)
```

### 2. Chạy services
```bash
# Start API + DB
docker compose up -d api db

# Test crawler
docker compose run --rm crawler --first-page-only
```

### 3. Setup Cron (VPS)
```bash
crontab -e

# Thêm:
0 1,13 * * * cd /srv/revenue-crawler && docker compose run --rm crawler >> /var/log/revenue-crawler.log 2>&1
```

## 📊 API Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Get metrics
curl http://localhost:8000/api/aggregated-metrics?metric_name=rpm_total_net_revenue

# Get fetch logs
curl http://localhost:8000/api/fetch-logs
```

## 🔒 Bảo Mật

- ✅ MySQL không expose public (bỏ port mapping)
- ✅ DB user riêng cho crawler
- ✅ Lock mechanism (crawl_runs table)
- ✅ Logs ra file

Xem chi tiết: `DOCKER_SETUP.md`
