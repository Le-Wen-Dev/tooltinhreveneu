# Hướng Dẫn Import Database

## 📁 File Schema

**File**: `database_schema_complete.sql`

File này chứa:
- ✅ Tất cả 6 tables (raw_revenue_data, formulas, computed_metrics, aggregated_metrics, fetch_logs, admin_users)
- ✅ Tất cả indexes và foreign keys
- ✅ Initial data (4 formulas mặc định)
- ✅ Comments và hướng dẫn

## 🚀 Cách Import

### Cách 1: Qua Command Line (MySQL)

```bash
# SSH vào server (nếu cần)
ssh tooltinhreveneu@gmail.com@36.50.27.158 -p 2222

# Import database
mysql -u tooltinhreveneu_1 -p tooltinhreveneu_1 < database_schema_complete.sql

# Nhập password khi được hỏi: tooltinhreveneu@gndhsggkl
```

### Cách 2: Qua phpMyAdmin

1. Đăng nhập phpMyAdmin: http://36.50.27.158:2222/
2. Chọn database: `tooltinhreveneu_1`
3. Click tab **Import**
4. Chọn file: `database_schema_complete.sql`
5. Click **Go** hoặc **Execute**

### Cách 3: Qua MySQL Workbench / DBeaver

1. Kết nối đến database
2. Mở file `database_schema_complete.sql`
3. Execute script

## ✅ Kiểm Tra Sau Khi Import

```sql
-- Kiểm tra tables đã được tạo
SHOW TABLES;

-- Kết quả mong đợi:
-- admin_users
-- aggregated_metrics
-- computed_metrics
-- fetch_logs
-- formulas
-- raw_revenue_data

-- Kiểm tra formulas đã được insert
SELECT * FROM formulas;

-- Kết quả: 4 formulas
-- 1. rpm_total_net_revenue
-- 2. rpm_per_1000_players
-- 3. total_net_revenue
-- 4. rpm_combined
```

## 📊 Cấu Trúc Database

### Tables:

1. **raw_revenue_data** - Dữ liệu scrape (có fetch_date để track lịch sử)
2. **formulas** - Định nghĩa công thức
3. **computed_metrics** - Kết quả tính toán row-level
4. **aggregated_metrics** - Kết quả tính toán tổng hợp
5. **fetch_logs** - Lịch sử mỗi lần fetch
6. **admin_users** - Users cho admin panel

### Indexes:

- Tất cả indexes đã được tạo tự động
- Foreign keys đã được setup
- Unique constraints đã được thiết lập

## ⚠️ Lưu Ý

1. **Nếu database đã có tables**: 
   - File dùng `CREATE TABLE IF NOT EXISTS` nên an toàn
   - Formulas dùng `ON DUPLICATE KEY UPDATE` nên sẽ update nếu đã có

2. **Nếu muốn xóa và tạo lại**:
   ```sql
   DROP TABLE IF EXISTS computed_metrics;
   DROP TABLE IF EXISTS aggregated_metrics;
   DROP TABLE IF EXISTS raw_revenue_data;
   DROP TABLE IF EXISTS fetch_logs;
   DROP TABLE IF EXISTS formulas;
   DROP TABLE IF EXISTS admin_users;
   ```
   Sau đó import lại file `database_schema_complete.sql`

3. **Backup trước khi import** (nếu có data cũ):
   ```bash
   mysqldump -u tooltinhreveneu_1 -p tooltinhreveneu_1 > backup.sql
   ```

## 🎯 Sau Khi Import

1. ✅ Verify tables đã được tạo
2. ✅ Verify formulas đã được insert
3. ✅ Test kết nối từ backend
4. ✅ Chạy API và test endpoints

## 📝 Next Steps

Sau khi import thành công:
1. Cập nhật `.env` với database credentials
2. Test kết nối: `python3 test_db_direct.py`
3. Chạy API: `python3 backend/app.py`
4. Test API endpoints
