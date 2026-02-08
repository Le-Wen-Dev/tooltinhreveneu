# Production Deployment Guide

## ✅ Đã Setup Docker

### Cấu trúc:
- `crawler/` - Crawler service (chạy xong exit)
- `api/` - FastAPI service (chạy liên tục)
- `docker-compose.yml` - Orchestration
- `.env` - Configuration

## 🚀 Deploy trên VPS

### 1. Upload code lên server

```bash
# Từ máy local
scp -P 2222 -r toolgetdata tooltinhreveneu@gmail.com@36.50.27.158:/srv/
```

### 2. SSH vào server

```bash
ssh tooltinhreveneu@gmail.com@36.50.27.158 -p 2222
cd /srv/toolgetdata
```

### 3. Tạo .env

```bash
cp .env.example .env
nano .env
```

Sửa:
```env
DB_HOST=localhost  # Vì MySQL trên cùng server
DB_PORT=3306
DB_NAME=tooltinhreveneu_1
DB_USER=tooltinhreveneu_1
DB_PASSWORD=tooltinhreveneu@gndhsggkl
```

### 4. Import database schema

```bash
mysql -u tooltinhreveneu_1 -p tooltinhreveneu_1 < database_schema_complete.sql
```

### 5. Build Docker images

```bash
docker compose build
```

### 6. Start API service

```bash
docker compose up -d api
```

### 7. Test crawler

```bash
docker compose run --rm crawler --first-page-only
```

### 8. Setup Cron

```bash
crontab -e
```

Thêm:
```bash
# Chạy crawler 2 lần mỗi ngày: 1:00 AM và 1:00 PM
0 1,13 * * * cd /srv/toolgetdata && /srv/toolgetdata/run-crawler.sh
```

Hoặc dùng script wrapper:
```bash
0 1,13 * * * /srv/toolgetdata/run-crawler.sh
```

## 📊 Verify

### Check API:
```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/aggregated-metrics
```

### Check logs:
```bash
tail -f /var/log/revenue-crawler.log
docker compose logs api
```

### Check database:
```bash
mysql -u tooltinhreveneu_1 -p tooltinhreveneu_1 -e "SELECT COUNT(*) FROM raw_revenue_data;"
```

## 🔄 Update

```bash
cd /srv/toolgetdata
git pull  # Nếu dùng git
docker compose build
docker compose up -d --force-recreate api
```

## 🔒 Security Checklist

- [x] MySQL không expose public (localhost only)
- [x] DB user riêng (không phải root)
- [x] Lock mechanism (crawl_runs table)
- [x] Logs ra file
- [ ] API có authentication (nếu cần)
- [ ] Reverse proxy với SSL (nginx)

## 📝 Notes

- **Crawler**: Chạy xong exit, không restart
- **API**: Chạy liên tục, auto restart
- **Cron**: Trigger crawler 2 lần/ngày
- **DB**: Dùng MySQL server có sẵn (không dùng container)
