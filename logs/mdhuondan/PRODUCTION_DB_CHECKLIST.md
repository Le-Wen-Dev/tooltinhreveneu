# Production Database - Checklist Thông Tin Cần Thiết

## 📋 Thông Tin Cần Cung Cấp

Để kết nối với database production, tôi cần các thông tin sau:

### 1. Database Connection String

**Format**: `postgresql://username:password@host:port/database_name`

**Hoặc cung cấp từng phần**:

```
✅ Database Host: _______________
✅ Database Port: _______________ (thường là 5432)
✅ Database Name: _______________
✅ Database Username: _______________
✅ Database Password: _______________
```

**Ví dụ**:
```
Database Host: db.example.com
Database Port: 5432
Database Name: revenue_production
Database Username: revenue_user
Database Password: SecurePass123!
```

### 2. Database Type

- [ ] PostgreSQL (khuyên dùng)
- [ ] MySQL 8+
- [ ] Khác: _______________

### 3. SSL/TLS Connection

- [ ] Có yêu cầu SSL connection
- [ ] Không yêu cầu SSL
- [ ] SSL certificate file (nếu có): _______________

### 4. Network Access

- [ ] Database cho phép kết nối từ internet
- [ ] Chỉ cho phép kết nối từ IP cụ thể
  - IP whitelist: _______________
- [ ] Cần VPN để kết nối
- [ ] Firewall rules cần cấu hình

### 5. Database Schema

- [ ] Database đã có schema chưa?
  - [ ] Chưa có → Tôi sẽ tạo schema mới
  - [ ] Đã có → Cần thông tin về schema hiện tại
- [ ] Có cần migrate data từ database cũ không?

### 6. Backup & Recovery

- [ ] Database có tự động backup không?
- [ ] Tần suất backup: _______________
- [ ] Retention period: _______________

### 7. Performance & Limits

- [ ] Max connections: _______________
- [ ] Database size limit: _______________
- [ ] Có giới hạn query time không?

## 🔧 Sau Khi Có Thông Tin

Tôi sẽ:

1. ✅ Cập nhật file `.env` với database credentials
2. ✅ Test kết nối database
3. ✅ Chạy migration/schema nếu cần
4. ✅ Verify các tables đã được tạo đúng
5. ✅ Test API endpoints với database production
6. ✅ Setup cron jobs (nếu dùng VPS)

## 📝 Template File .env

Sau khi có thông tin, file `.env` sẽ như sau:

```env
# Production Database
DATABASE_URL=postgresql://username:password@host:port/database_name

# Hoặc từng biến riêng:
DB_HOST=db.example.com
DB_PORT=5432
DB_NAME=revenue_production
DB_USER=revenue_user
DB_PASSWORD=SecurePass123!

# Scraper Credentials
SCRAPER_USERNAME=maxvaluemedia
SCRAPER_PASSWORD=gliacloud

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Optional: SSL
DB_SSL_MODE=require
# DB_SSL_CERT=/path/to/cert.pem
```

## 🔒 Security Checklist

Trước khi cung cấp thông tin, đảm bảo:

- [ ] Database user có quyền phù hợp (không phải superuser)
- [ ] Password mạnh (16+ ký tự)
- [ ] Database không expose ra internet công khai
- [ ] Có firewall rules
- [ ] SSL/TLS được enable
- [ ] Có backup strategy

## 🧪 Test Connection

Sau khi setup, tôi sẽ test:

```bash
# Test connection
python3 -c "
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv('backend/.env')
engine = create_engine(os.getenv('DATABASE_URL'))
conn = engine.connect()
print('✅ Database connection successful!')
conn.close()
"

# Test schema
psql $DATABASE_URL -c "\dt"

# Test API
curl http://localhost:8000/health
```

## 📞 Thông Tin Bổ Sung

Nếu có thông tin bổ sung sau, vui lòng cung cấp:

- [ ] Database version (PostgreSQL 12+, MySQL 8+)
- [ ] Timezone settings
- [ ] Character encoding (UTF-8)
- [ ] Connection pool settings
- [ ] Read replicas (nếu có)

## ✅ Checklist Hoàn Thành

Sau khi có đầy đủ thông tin:

- [ ] Database connection string đã được cấu hình
- [ ] Schema đã được tạo/migrate
- [ ] Test connection thành công
- [ ] API endpoints hoạt động với production DB
- [ ] Cron jobs đã được setup (nếu cần)
- [ ] Monitoring/logging đã được cấu hình

---

**Vui lòng cung cấp thông tin database production để tôi có thể setup và test kết nối.**
