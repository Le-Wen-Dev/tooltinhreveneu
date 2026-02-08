# Quick Test Guide - Local

## 🚀 Cách Nhanh Nhất

### Chạy script tự động:
```bash
./start-local-test.sh
```

Script sẽ:
1. ✅ Tạo .env
2. ✅ Start MySQL container
3. ✅ Import schema tự động
4. ✅ Build và start API
5. ✅ Verify setup

Sau đó test:
```bash
# Test crawler
docker compose -f docker-compose.local.yml run --rm crawler --first-page-only

# Test API
curl http://localhost:8000/health
curl http://localhost:8000/api/fetch-logs
```

## 📋 Test Flow

### 1. Crawler chạy
```bash
docker compose -f docker-compose.local.yml run --rm crawler --first-page-only
```

**Kết quả mong đợi**:
- ✅ Login thành công
- ✅ Fetch được data
- ✅ Lưu vào database
- ✅ Tính formulas tự động

### 2. Verify Data
```bash
# Xem fetch logs
curl http://localhost:8000/api/fetch-logs | python3 -m json.tool

# Xem raw data
curl http://localhost:8000/api/raw-data | python3 -m json.tool

# Xem computed metrics
curl http://localhost:8000/api/computed-metrics | python3 -m json.tool

# Xem aggregated metrics
curl http://localhost:8000/api/aggregated-metrics | python3 -m json.tool
```

### 3. Test API Endpoints
Mở browser: http://localhost:8000/docs

Test các endpoints:
- `GET /health`
- `GET /api/fetch-logs`
- `GET /api/raw-data`
- `GET /api/aggregated-metrics`
- `GET /api/computed-metrics`

## 🔍 Troubleshooting

### MySQL không kết nối được:
```bash
# Check MySQL đang chạy
docker compose -f docker-compose.local.yml ps db

# Check logs
docker compose -f docker-compose.local.yml logs db

# Test connection từ container
docker compose -f docker-compose.local.yml exec api python -c "from crawler.db import engine; engine.connect(); print('OK')"
```

### API không chạy:
```bash
# Check logs
docker compose -f docker-compose.local.yml logs api

# Restart
docker compose -f docker-compose.local.yml restart api
```

### Crawler lỗi:
```bash
# Xem logs
docker compose -f docker-compose.local.yml logs crawler

# Test lại
docker compose -f docker-compose.local.yml run --rm crawler --first-page-only
```

## ✅ Sau Khi Test Thành Công

Nếu flow hoạt động đúng:
1. ✅ Push images lên VPS
2. ✅ Deploy production theo `DEPLOY_TO_VPS.md`
