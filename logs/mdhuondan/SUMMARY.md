# 📋 Tóm Tắt Dự Án - Revenue Data Crawler & API

## ✅ Đã Hoàn Thành

### 1. **Web Scraper**
- ✅ Login vào `https://gstudio.gliacloud.com` với CSRF token handling
- ✅ Scrape data từ HTML table (pagination support)
- ✅ Parse các fields: channel, slot, time_unit, total_player_impr, total_ad_impr, rpm, net_revenue_usd
- ✅ Test mode: `--first-page-only` để test nhanh

### 2. **Database Schema (MySQL)**
- ✅ 7 tables:
  - `raw_revenue_data`: Dữ liệu thô từ scraper
  - `formulas`: Định nghĩa công thức tính toán
  - `computed_metrics`: Kết quả tính toán theo từng row
  - `aggregated_metrics`: Kết quả tổng hợp theo channel/time_unit
  - `fetch_logs`: Lịch sử fetch data
  - `crawl_runs`: Lock mechanism để tránh chạy trùng
  - `admin_users`: Quản lý admin (cho admin panel)
- ✅ Schema tự động import khi MySQL container khởi động

### 3. **Formula Engine**
- ✅ Tính toán các metrics:
  - `rpm_total_net_revenue`: Tổng Net Revenue (Mobile + Desktop)
  - `rpm_per_1000_players`: (Net Revenue / Total Player Impressions) * 1000
  - `rpm_combined`: (Tổng Net Revenue / Tổng Player Impressions) * 1000
  - `total_net_revenue`: Tổng Net Revenue
- ✅ Focus 100% vào Net Revenue (ignore Gross Revenue)

### 4. **API (FastAPI)**
- ✅ Endpoints:
  - `GET /health`: Health check
  - `GET /api/raw-data`: Lấy raw data (filter: channel, time_unit, fetch_date)
  - `GET /api/computed-metrics`: Lấy computed metrics
  - `GET /api/aggregated-metrics`: Lấy aggregated metrics
  - `GET /api/fetch-logs`: Lịch sử fetch
  - `GET /api/formulas`: Danh sách formulas
  - `POST /api/formulas`: Tạo formula mới
  - `PUT /api/formulas/{id}`: Cập nhật formula
  - `DELETE /api/formulas/{id}`: Xóa formula
  - `POST /api/compute-metrics`: Trigger tính toán lại metrics

### 5. **Admin Panel**
- ✅ Web interface để quản lý formulas
- ✅ CRUD operations cho formulas
- ✅ Access tại: `http://localhost:8000/admin/formulas`

### 6. **Docker Setup**
- ✅ 3 services:
  - `crawler`: Service crawl data (chạy xong exit)
  - `api`: FastAPI service (chạy liên tục)
  - `db`: MySQL 8.0 container (tự động import schema)
- ✅ Docker Compose với health checks
- ✅ Network isolation
- ✅ Volume persistence cho database

### 7. **Data Fetching Logic**
- ✅ Update/Insert: Tự động update nếu record đã tồn tại (dựa trên channel, slot, time_unit, fetch_date)
- ✅ Tự động tính toán metrics sau khi fetch xong
- ✅ Logging vào `fetch_logs` table

### 8. **Concurrency Control**
- ✅ `crawl_runs` table để lock
- ✅ Tránh chạy trùng crawler cho cùng một date

## 🏗️ Cấu Trúc Project

```
toolgetdata/
├── crawler/
│   ├── main.py          # Entry point cho crawler
│   ├── db.py            # Database models
│   ├── lock.py          # Lock mechanism
│   └── Dockerfile
├── api/
│   ├── main.py          # FastAPI app
│   ├── Dockerfile
│   └── ...
├── backend/
│   ├── app.py           # Shared models & logic
│   ├── data_fetcher.py  # Orchestration logic
│   ├── formula_engine.py # Formula calculation
│   ├── scraper.py       # Web scraping
│   ├── admin_panel.py   # Admin panel routes
│   └── templates/       # HTML templates
├── database_schema_complete.sql  # MySQL schema
├── docker-compose.yml   # Docker Compose config
├── .env                 # Environment variables (local)
├── .env.production      # Environment variables (production)
├── start-local-test.sh  # Script test local
└── DEPLOY_VPS_DOCKER_DB.md  # Hướng dẫn deploy
```

## 🚀 Local Testing

```bash
# Start all services
docker compose up -d

# Test crawler (first page only)
docker compose run --rm crawler --first-page-only

# Test API
curl http://localhost:8000/health
curl http://localhost:8000/api/raw-data
```

## 📦 Deploy Lên VPS

### Bước 1: Build & Save Images
```bash
./save-and-push-images.sh
```

### Bước 2: Upload Lên VPS
```bash
scp -P 2222 \
  crawler-image.tar \
  api-image.tar \
  docker-compose.yml \
  database_schema_complete.sql \
  .env.production \
  user@vps:/srv/toolgetdata/
```

### Bước 3: SSH & Deploy
```bash
ssh user@vps -p 2222
cd /srv/toolgetdata

# Load images
docker load -i crawler-image.tar
docker load -i api-image.tar

# Setup .env
cp .env.production .env

# Start services
docker compose up -d

# Verify
curl http://localhost:8000/health
```

### Bước 4: Setup Cron
```bash
crontab -e

# Thêm:
0 1,13 * * * cd /srv/toolgetdata && docker compose run --rm crawler >> /var/log/revenue-crawler.log 2>&1
```

## 🔧 Environment Variables

```bash
# Database (dùng MySQL container)
DB_TYPE=mysql
DB_HOST=db              # Service name trong Docker
DB_PORT=3306
DB_NAME=tooltinhreveneu_1
DB_USER=tooltinhreveneu_1
DB_PASSWORD=your_password
DB_ROOT_PASSWORD=rootpassword

# Scraper
SCRAPER_USERNAME=maxvaluemedia
SCRAPER_PASSWORD=gliacloud

# API
API_PORT=8000
```

## 📊 Database Tables

1. **raw_revenue_data**: Dữ liệu thô từ scraper
2. **formulas**: Công thức tính toán
3. **computed_metrics**: Metrics tính theo row
4. **aggregated_metrics**: Metrics tổng hợp
5. **fetch_logs**: Lịch sử fetch
6. **crawl_runs**: Lock mechanism
7. **admin_users**: Admin users

## 🎯 API Endpoints

### Health
- `GET /health`

### Raw Data
- `GET /api/raw-data?channel=...&time_unit=...&fetch_date=...`

### Metrics
- `GET /api/computed-metrics?metric_name=...`
- `GET /api/aggregated-metrics?formula_name=...&channel=...`

### Formulas
- `GET /api/formulas`
- `POST /api/formulas`
- `PUT /api/formulas/{id}`
- `DELETE /api/formulas/{id}`

### Admin
- `GET /admin/formulas` - List formulas
- `GET /admin/formulas/new` - Create formula
- `GET /admin/formulas/{id}/edit` - Edit formula

## ✅ Advantages của MySQL Container

- ✅ Không cần setup MySQL trên VPS
- ✅ Schema tự động import khi khởi động
- ✅ Database persist trong Docker volume
- ✅ Dễ backup/restore
- ✅ Isolated, không ảnh hưởng MySQL khác
- ✅ Dễ migrate/update

## 🔄 Workflow

1. **Cron trigger** → `docker compose run --rm crawler`
2. **Crawler** → Login → Scrape → Save to DB → Compute metrics
3. **API** → Expose data qua REST endpoints
4. **Admin Panel** → Quản lý formulas

## 📝 Notes

- Crawler chạy xong sẽ exit (không restart)
- API chạy liên tục (restart unless-stopped)
- MySQL container tự động import schema từ `database_schema_complete.sql`
- Database volume: `toolgetdata_db_data` (persist data)

## 🐛 Troubleshooting

### MySQL không import schema:
```bash
docker compose logs db
docker compose exec db ls -la /docker-entrypoint-initdb.d/
```

### Containers không kết nối DB:
```bash
docker network inspect toolgetdata_revenue-network
docker compose exec api python -c "from crawler.db import engine; engine.connect()"
```

### Reset database:
```bash
docker compose down -v  # Xóa volume
docker compose up -d     # Tạo lại và import schema
```
