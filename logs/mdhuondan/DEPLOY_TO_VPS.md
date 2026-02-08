# Hướng Dẫn Deploy Lên VPS

## ✅ Images Đã Build Xong

- `toolgetdata-crawler:latest`
- `toolgetdata-api:latest`

## 🚀 Bước 1: Save Images (Đã làm xong)

```bash
./save-and-push-images.sh
```

Images sẽ được save thành:
- `crawler-image.tar`
- `api-image.tar`

## 📤 Bước 2: Upload Images Lên VPS

```bash
# Upload images
scp -P 2222 crawler-image.tar api-image.tar tooltinhreveneu@gmail.com@36.50.27.158:/srv/toolgetdata/

# Upload code và config
scp -P 2222 -r docker-compose.yml database_schema_complete.sql tooltinhreveneu@gmail.com@36.50.27.158:/srv/toolgetdata/
```

## 🔧 Bước 3: Setup Trên VPS

### SSH vào VPS:
```bash
ssh tooltinhreveneu@gmail.com@36.50.27.158 -p 2222
cd /srv/toolgetdata
```

### Load Images:
```bash
docker load -i crawler-image.tar
docker load -i api-image.tar

# Verify
docker images | grep toolgetdata
```

### Import Database Schema:
```bash
mysql -u tooltinhreveneu_1 -p tooltinhreveneu_1 < database_schema_complete.sql
# Password: tooltinhreveneu@gndhsggkl
```

### Tạo .env:
```bash
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
```

### Tạo logs directory:
```bash
mkdir -p logs
chmod 755 logs
```

## 🎯 Bước 4: Chạy Services

### Start API:
```bash
docker compose up -d api
```

### Test Crawler:
```bash
docker compose run --rm crawler --first-page-only
```

### Verify API:
```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/aggregated-metrics
```

## ⏱ Bước 5: Setup Cron

```bash
crontab -e
```

Thêm:
```bash
# Chạy crawler 2 lần mỗi ngày: 1:00 AM và 1:00 PM
0 1,13 * * * cd /srv/toolgetdata && docker compose run --rm crawler >> /var/log/revenue-crawler.log 2>&1
```

## ✅ Checklist

- [ ] Images đã upload lên VPS
- [ ] Images đã load vào Docker
- [ ] Database schema đã import
- [ ] File .env đã tạo
- [ ] API service đã chạy
- [ ] Crawler test thành công
- [ ] Cron job đã setup

## 🔄 Update Sau Này

Khi có code mới:

1. **Build lại images** (trên máy local):
   ```bash
   docker compose build
   ./save-and-push-images.sh
   ```

2. **Upload lên VPS**:
   ```bash
   scp -P 2222 crawler-image.tar api-image.tar tooltinhreveneu@gmail.com@36.50.27.158:/srv/toolgetdata/
   ```

3. **Load và restart** (trên VPS):
   ```bash
   docker load -i crawler-image.tar
   docker load -i api-image.tar
   docker compose up -d --force-recreate api
   ```

## 📝 Về MySQL

**KHÔNG CẦN** setup MySQL container vì:
- ✅ MySQL đã có sẵn trên VPS
- ✅ Database `tooltinhreveneu_1` đã tồn tại
- ✅ Chỉ cần import schema 1 lần

Xem chi tiết: `MYSQL_INFO.md`
