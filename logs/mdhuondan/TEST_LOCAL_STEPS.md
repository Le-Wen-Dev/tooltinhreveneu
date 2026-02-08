# Test Project Trên Local - Từng Bước

## 🎯 Option 1: Dùng MySQL Container (Dễ nhất)

### Bước 1: Start MySQL Container
```bash
docker compose -f docker-compose.local.yml up -d db
```

Đợi 30 giây để MySQL khởi động và import schema tự động.

### Bước 2: Verify MySQL
```bash
docker compose -f docker-compose.local.yml exec db mysql -u tooltinhreveneu_1 -ptooltinhreveneu@gndhsggkl tooltinhreveneu_1 -e "SHOW TABLES;"
```

Kết quả mong đợi: 7 tables (raw_revenue_data, formulas, computed_metrics, aggregated_metrics, fetch_logs, admin_users, crawl_runs)

### Bước 3: Setup .env
```bash
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
```

### Bước 4: Build và Start API
```bash
docker compose -f docker-compose.local.yml build api
docker compose -f docker-compose.local.yml up -d api
```

### Bước 5: Test API
```bash
# Đợi 10 giây
sleep 10

# Health check
curl http://localhost:8000/health

# Swagger UI
open http://localhost:8000/docs
```

### Bước 6: Test Crawler
```bash
docker compose -f docker-compose.local.yml run --rm crawler --first-page-only
```

### Bước 7: Verify Data
```bash
# Fetch logs
curl http://localhost:8000/api/fetch-logs | python3 -m json.tool

# Raw data
curl http://localhost:8000/api/raw-data | python3 -m json.tool

# Aggregated metrics
curl http://localhost:8000/api/aggregated-metrics | python3 -m json.tool
```

## 🎯 Option 2: Dùng MySQL Local (Nếu đã có MySQL)

### Bước 1: Import Schema
```bash
mysql -u tooltinhreveneu_1 -p tooltinhreveneu_1 < database_schema_complete.sql
```

### Bước 2: Setup .env
```bash
cat > .env << EOF
DB_TYPE=mysql
DB_HOST=host.docker.internal  # macOS/Windows
# Hoặc DB_HOST=172.17.0.1  # Linux
DB_PORT=3306
DB_NAME=tooltinhreveneu_1
DB_USER=tooltinhreveneu_1
DB_PASSWORD=tooltinhreveneu@gndhsggkl
SCRAPER_USERNAME=maxvaluemedia
SCRAPER_PASSWORD=gliacloud
API_PORT=8000
EOF
```

### Bước 3: Build và Start
```bash
docker compose build
docker compose up -d api
```

### Bước 4: Test
```bash
# Test crawler
docker compose run --rm crawler --first-page-only

# Test API
curl http://localhost:8000/health
```

## 🔍 Debug

### Xem logs:
```bash
# API
docker compose -f docker-compose.local.yml logs api

# Crawler
docker compose -f docker-compose.local.yml logs crawler

# MySQL
docker compose -f docker-compose.local.yml logs db
```

### Test database connection:
```bash
docker compose -f docker-compose.local.yml exec api python -c "from crawler.db import engine; engine.connect(); print('✅ Connected')"
```

### Check data:
```bash
docker compose -f docker-compose.local.yml exec db mysql -u tooltinhreveneu_1 -ptooltinhreveneu@gndhsggkl tooltinhreveneu_1 -e "SELECT COUNT(*) FROM raw_revenue_data;"
```

## ✅ Flow Test Checklist

1. [ ] MySQL container chạy được
2. [ ] Schema đã được import
3. [ ] API service chạy được
4. [ ] Crawler fetch được data
5. [ ] Data được lưu vào database
6. [ ] Formulas được tính tự động
7. [ ] API trả về metrics đúng

## 🛑 Stop Services

```bash
# Stop tất cả
docker compose -f docker-compose.local.yml down

# Stop và xóa database volume (reset)
docker compose -f docker-compose.local.yml down -v
```

## 🚀 Sau Khi Test Thành Công

Nếu mọi thứ hoạt động đúng:
1. ✅ Push images lên VPS (đã có: crawler-image.tar, api-image.tar)
2. ✅ Follow `DEPLOY_TO_VPS.md` để deploy production
