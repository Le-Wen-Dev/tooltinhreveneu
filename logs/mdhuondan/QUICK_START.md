# Quick Start Guide

## Chạy local

### Cách 1: Docker (khuyên dùng)

Cần có Docker Desktop. Trong thư mục project:

```bash
# Tạo .env nếu chưa có (DB_HOST=db, DB_PASSWORD=..., DB_USER=..., DB_NAME=...)
docker compose up -d --build
```

Sau đó mở: **http://localhost:8000** (trang chủ, login, admin).

- **Vì sao 2 container?** Cần **api** (web + API) và **db** (MySQL). **crawler** không chạy nền — chỉ chạy khi gọi: `docker compose run --rm crawler --first-page-only`.
- Schema DB tự import lần đầu. Nếu dùng user có sẵn (không qua Setup), chạy seed 1 lần:
  ```bash
  # Thay YOUR_DB_PASSWORD bằng mật khẩu DB trong .env
  docker compose exec -T db mysql -u tooltinhreveneu_1 -pYOUR_DB_PASSWORD tooltinhreveneu_1 < seed_users.sql
  ```
  Rồi login: **admin** / **Admin@!321** (admin) hoặc **maxvaluemedia** / **Maxvalue@2026** (khách).

### Cách 2: Không Docker (Python trực tiếp)

1. **MySQL** đang chạy (local hoặc remote). Tạo DB và import schema:
   ```bash
   mysql -u USER -p DB_NAME < database_schema_complete.sql
   # Nếu đã có DB nhưng chưa có bảng users:
   mysql -u USER -p DB_NAME < migrations_add_users_table.sql
   ```

2. **Tạo `.env`** ở thư mục gốc project, ví dụ:
   ```
   DB_HOST=localhost
   DB_PORT=3306
   DB_NAME=tooltinhreveneu_1
   DB_USER=tooltinhreveneu_1
   DB_PASSWORD=your_password
   ```

3. **(Tuỳ chọn)** Tạo sẵn 2 user để chỉ login, không qua Setup:
   ```bash
   mysql -u USER -p DB_NAME < seed_users.sql
   ```
   Sau đó login: **admin** / **Admin@!321** hoặc **maxvaluemedia** / **Maxvalue@2026**.

4. **Cài dependency và chạy API** (từ thư mục gốc project):
   ```bash
   pip install -r api/requirements.txt
   uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
   ```

Mở: **http://localhost:8000**.

---

## Cào 2 lần mỗi ngày & lưu hết

- **Mỗi lần cào lưu hết:** Khi chạy crawler **không** có `--first-page-only`, tool cào **tất cả trang** theo ngày, rồi **lưu/ghi đè** từng dòng vào DB (raw_revenue_data). Cùng ngày chạy lại sẽ cập nhật, không tạo bản ghi trùng.
- **Đảm bảo cào 2 lần mỗi ngày:** Cấu hình **cron** trên server (VPS) để chạy crawler 2 lần (ví dụ 1:00 và 13:00). **Không** dùng `--first-page-only` để mỗi lần cào full và lưu hết.

**Ví dụ cron (Docker):**

```bash
crontab -e
# Thêm dòng (thay /path/to/toolgetdata bằng đường dẫn thực tế):
0 1,13 * * * cd /path/to/toolgetdata && docker compose run --rm crawler >> /var/log/revenue-crawler.log 2>&1
```

- `0 1,13 * * *` = mỗi ngày lúc 1:00 và 13:00.
- Chạy `docker compose run --rm crawler` **không** truyền `--first-page-only` → cào full, lưu hết raw cho ngày (mặc định là **hôm qua**).

**Trigger thủ công (Admin):** Trong Dashboard bấm **Trigger Crawl (Manual)** → dùng full crawl (không test first page), raw + processed đều được cập nhật.

---

## ✅ Test Crawl - Thành Công!

Hệ thống đã được test và hoạt động tốt:
- ✅ Đăng nhập thành công
- ✅ Lấy được 6 dòng dữ liệu từ trang đầu tiên
- ✅ Dữ liệu đã được lưu vào `test_data.json`

## 🚀 Chạy Test Crawl

```bash
# Test crawl trang đầu tiên
python3 test_crawl.py
```

Kết quả sẽ được lưu vào `test_data.json`.

## 📊 Dữ Liệu Mẫu

Dữ liệu đã lấy được bao gồm:
- **channel**: maxvaluemedia_spotpariz
- **slot**: spotpariz_desktop, spotpariz_mobile, etc.
- **time unit**: 2026/01
- **total player impr**: Số lượng player impressions
- **total ad impr**: Số lượng ad impressions
- **rpm**: Revenue per mille
- **gross revenue (usd)**: Tổng doanh thu
- **net revenue (usd)**: Doanh thu ròng (focus chính)

## 🔧 Sửa Lỗi Login

Đã cập nhật hàm `login()` trong `scraper.py` để:
- Sử dụng đúng URL login: `/ad-sharing/login/`
- Lấy CSRF token từ form
- Xử lý field `next` cho redirect
- Kiểm tra đăng nhập thành công chính xác hơn

## 📝 Next Steps

1. **Test với Backend**:
   ```bash
   # Fetch và lưu vào database
   python3 backend/data_fetcher.py --first-page-only
   ```

2. **Chạy API Server**:
   ```bash
   cd backend
   uvicorn app:app --reload
   ```

3. **Truy cập Admin Panel**:
   - Mở: `http://localhost:8000/admin`
   - Quản lý formulas

4. **Test API**:
   - Swagger UI: `http://localhost:8000/docs`
   - Test endpoints

## 📚 Documentation

- `SETUP_GUIDE.md` - Hướng dẫn setup chi tiết
- `DEPLOYMENT_REQUIREMENTS.md` - Yêu cầu deployment
- `README_BACKEND.md` - Tổng quan hệ thống

## ⚠️ Lưu Ý

- Các cảnh báo linter về `requests` và `bs4` là bình thường (chưa cài packages)
- Cần cài dependencies: `pip install -r requirements.txt`
- Cần setup database trước khi chạy backend
