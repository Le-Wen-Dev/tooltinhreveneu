# Deploy Lên VPS - Dùng MySQL Container

## ✅ Setup: MySQL Container trong Docker

Không cần MySQL trên VPS, dùng MySQL container trong Docker.

## 🚀 Deploy Steps

### 1. Upload Files Lên VPS

```bash
scp -P 2222 \
  crawler-image.tar \
  api-image.tar \
  docker-compose.yml \
  database_schema_complete.sql \
  .env.production \
  tooltinhreveneu@gmail.com@36.50.27.158:/srv/toolgetdata/
```

### 2. SSH Vào VPS

```bash
ssh tooltinhreveneu@gmail.com@36.50.27.158 -p 2222
cd /srv/toolgetdata
```

### 3. Load Docker Images

```bash
docker load -i crawler-image.tar
docker load -i api-image.tar

# Verify
docker images | grep toolgetdata
```

### 4. Setup .env

```bash
cp .env.production .env

# Hoặc tạo thủ công:
cat > .env << EOF
DB_TYPE=mysql
DB_HOST=db
DB_PORT=3306
DB_NAME=tooltinhreveneu_1
DB_USER=tooltinhreveneu_1
DB_PASSWORD=tooltinhreveneu@gndhsggkl
DB_ROOT_PASSWORD=rootpassword
SCRAPER_USERNAME=maxvaluemedia
SCRAPER_PASSWORD=gliacloud
API_PORT=8000
EOF
```

### 5. Start Services

```bash
# Start tất cả (MySQL + API)
docker compose up -d

# MySQL sẽ tự động:
# - Khởi động
# - Import schema từ database_schema_complete.sql
# - Tạo database và user
```

### 6. Đợi MySQL Khởi Động

```bash
# Đợi 30-40 giây để MySQL import schema
# Check logs:
docker compose logs db | tail -20

# Verify schema đã import:
docker compose exec db mysql -u tooltinhreveneu_1 -ptooltinhreveneu@gndhsggkl tooltinhreveneu_1 -e "SHOW TABLES;"
```

Kết quả mong đợi: 7 tables

### 7. Verify Services

```bash
# Check containers
docker compose ps

# Test API
curl http://localhost:8000/health

# Test crawler
docker compose run --rm crawler --first-page-only
```

### 8. Setup Cron

```bash
crontab -e

# Thêm:
0 1,13 * * * cd /srv/toolgetdata && docker compose run --rm crawler >> /var/log/revenue-crawler.log 2>&1
```

## 📊 Verify Database

```bash
# Connect vào MySQL container
docker compose exec db mysql -u tooltinhreveneu_1 -p tooltinhreveneu_1

# Check tables
SHOW TABLES;

# Check data
SELECT COUNT(*) FROM raw_revenue_data;
SELECT COUNT(*) FROM aggregated_metrics;
```

## 🔄 Backup Database

```bash
# Backup database volume
docker compose exec db mysqldump -u tooltinhreveneu_1 -ptooltinhreveneu@gndhsggkl tooltinhreveneu_1 > backup.sql

# Hoặc backup volume
docker run --rm -v toolgetdata_db_data:/data -v $(pwd):/backup alpine tar czf /backup/db_backup.tar.gz /data
```

## 🔄 Restore Database

```bash
# Restore từ SQL file
docker compose exec -T db mysql -u tooltinhreveneu_1 -ptooltinhreveneu@gndhsggkl tooltinhreveneu_1 < backup.sql
```

## 📝 Lưu Ý

### Database Volume
- Database được lưu trong Docker volume: `toolgetdata_db_data`
- Volume persist ngay cả khi container stop
- Để reset database: `docker compose down -v` (xóa volume)

### Ports
- API: `8000:8000` (expose ra ngoài)
- MySQL: Không expose (chỉ trong Docker network)

### Network
- Tất cả containers trong cùng network: `revenue-network`
- Containers giao tiếp qua service name: `db`, `api`

## ✅ Advantages

- ✅ Không cần setup MySQL trên VPS
- ✅ Database tự động import schema khi khởi động
- ✅ Dễ backup/restore (Docker volume)
- ✅ Isolated, không ảnh hưởng MySQL khác
- ✅ Dễ migrate/update

## 🐛 Troubleshooting

### MySQL không khởi động:
```bash
docker compose logs db
```

### Schema không import:
```bash
# Check file có mount đúng không
docker compose exec db ls -la /docker-entrypoint-initdb.d/

# Import thủ công
docker compose exec -T db mysql -u tooltinhreveneu_1 -ptooltinhreveneu@gndhsggkl tooltinhreveneu_1 < database_schema_complete.sql
```

### Containers không kết nối được DB:
```bash
# Check network
docker network ls
docker network inspect toolgetdata_revenue-network

# Test connection từ API container
docker compose exec api python -c "from crawler.db import engine; engine.connect(); print('OK')"
```

## 🎯 Quick Commands

```bash
# Start all
docker compose up -d

# Stop all
docker compose down

# Stop và xóa database (reset)
docker compose down -v

# View logs
docker compose logs -f

# Restart service
docker compose restart api
```
