# Test Project Trên Local

## 🚀 Quick Start

### Option 1: Dùng Script Tự Động (Khuyên dùng)

```bash
./test-local.sh
```

Script sẽ tự động:
1. Build Docker images
2. Start API service
3. Test crawler (first page only)
4. Test API endpoints

### Option 2: Manual Steps

#### 1. Tạo .env

```bash
cp .env.local .env
# Hoặc tạo thủ công với thông tin MySQL của bạn
```

#### 2. Import Database Schema

**Nếu dùng MySQL local:**
```bash
mysql -u tooltinhreveneu_1 -p tooltinhreveneu_1 < database_schema_complete.sql
```

**Nếu chưa có MySQL local**, có thể dùng MySQL container:
```bash
# Uncomment section db trong docker-compose.yml
# Sau đó:
docker compose up -d db
# Đợi MySQL khởi động (30 giây)
# Import schema vào container
docker compose exec db mysql -u tooltinhreveneu_1 -p tooltinhreveneu_1 < database_schema_complete.sql
```

#### 3. Build Images

```bash
docker compose build
```

#### 4. Start API

```bash
docker compose up -d api
```

#### 5. Test Crawler

```bash
# Test với first page only
docker compose run --rm crawler --first-page-only

# Hoặc test với date cụ thể
docker compose run --rm crawler --date 2026-01-26 --first-page-only
```

#### 6. Test API

```bash
# Health check
curl http://localhost:8000/health

# Fetch logs
curl http://localhost:8000/api/fetch-logs

# Aggregated metrics
curl http://localhost:8000/api/aggregated-metrics

# Raw data
curl http://localhost:8000/api/raw-data?limit=5
```

## 📊 Verify Flow

### 1. Crawler chạy → Lưu data
```bash
docker compose run --rm crawler --first-page-only
```

Kiểm tra:
```bash
# Xem fetch logs
curl http://localhost:8000/api/fetch-logs

# Xem raw data
curl http://localhost:8000/api/raw-data
```

### 2. Formulas được tính tự động
```bash
# Xem computed metrics
curl http://localhost:8000/api/computed-metrics

# Xem aggregated metrics
curl http://localhost:8000/api/aggregated-metrics?metric_name=rpm_total_net_revenue
```

### 3. API trả về metrics
```bash
# Lấy RPM Total Net Revenue
curl http://localhost:8000/api/aggregated-metrics?metric_name=rpm_total_net_revenue

# Lấy RPM per 1000 Players
curl http://localhost:8000/api/computed-metrics?metric_name=rpm_per_1000_players
```

## 🔍 Debug

### Xem logs:
```bash
# API logs
docker compose logs api

# Crawler logs (last run)
docker compose logs crawler

# Follow logs
docker compose logs -f api
```

### Test database connection:
```bash
docker compose run --rm crawler python -c "from crawler.db import engine; engine.connect(); print('✅ DB connected')"
```

### Check database:
```bash
# Nếu dùng MySQL local
mysql -u tooltinhreveneu_1 -p tooltinhreveneu_1 -e "SELECT COUNT(*) FROM raw_revenue_data;"
mysql -u tooltinhreveneu_1 -p tooltinhreveneu_1 -e "SELECT COUNT(*) FROM aggregated_metrics;"
```

## ⚠️ Lưu Ý

### MySQL Connection

Nếu containers không kết nối được đến MySQL local:

**Option 1**: Dùng `network_mode: host` trong docker-compose.yml:
```yaml
services:
  crawler:
    network_mode: host
  api:
    network_mode: host
```

**Option 2**: Dùng `host.docker.internal` (macOS/Windows):
```env
DB_HOST=host.docker.internal
```

**Option 3**: Dùng MySQL container (uncomment trong docker-compose.yml)

## ✅ Checklist Test

- [ ] API service chạy được
- [ ] Crawler fetch được data
- [ ] Data được lưu vào database
- [ ] Formulas được tính tự động
- [ ] API trả về metrics đúng
- [ ] Fetch logs được ghi lại

## 🎯 Sau Khi Test Thành Công

Nếu mọi thứ hoạt động đúng:
1. Push images lên VPS (đã có sẵn: crawler-image.tar, api-image.tar)
2. Follow `DEPLOY_TO_VPS.md` để deploy
