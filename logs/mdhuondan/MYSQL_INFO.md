# MySQL - Không Cần Setup Gì Thêm

## ✅ MySQL Đã Có Sẵn Trên VPS

Bạn **KHÔNG CẦN** setup MySQL container vì:
- ✅ MySQL đã có sẵn trên VPS (36.50.27.158)
- ✅ Database: `tooltinhreveneu_1` đã tồn tại
- ✅ User: `tooltinhreveneu_1` đã có quyền

## 🔧 Chỉ Cần

### 1. Import Schema (1 lần duy nhất)

```bash
# SSH vào VPS
ssh tooltinhreveneu@gmail.com@36.50.27.158 -p 2222

# Import schema
mysql -u tooltinhreveneu_1 -p tooltinhreveneu_1 < database_schema_complete.sql
# Password: tooltinhreveneu@gndhsggkl
```

### 2. Cấu Hình .env

Trên VPS, tạo file `.env`:

```env
DB_TYPE=mysql
DB_HOST=localhost  # Vì MySQL trên cùng server
DB_PORT=3306
DB_NAME=tooltinhreveneu_1
DB_USER=tooltinhreveneu_1
DB_PASSWORD=tooltinhreveneu@gndhsggkl
SCRAPER_USERNAME=maxvaluemedia
SCRAPER_PASSWORD=gliacloud
API_PORT=8000
```

### 3. Docker Compose

Trong `docker-compose.yml`, **KHÔNG CẦN** section `db` vì:
- MySQL đã có sẵn
- Containers sẽ kết nối đến `localhost:3306` (MySQL trên host)

## 📝 Lưu Ý

- **DB_HOST=localhost**: Containers kết nối đến MySQL trên host
- **Không cần MySQL container**: Đã comment trong docker-compose.yml
- **Network mode**: Có thể cần `network_mode: host` nếu có vấn đề kết nối

## 🔄 Nếu Có Vấn Đề Kết Nối

Nếu containers không kết nối được đến MySQL trên host:

**Option 1**: Dùng `network_mode: host` trong docker-compose.yml:
```yaml
services:
  crawler:
    network_mode: host
    # ...
  api:
    network_mode: host
    # ...
```

**Option 2**: Dùng host.docker.internal (macOS/Windows):
```env
DB_HOST=host.docker.internal
```

**Option 3**: Dùng IP của host:
```env
DB_HOST=172.17.0.1  # Docker bridge gateway
```

## ✅ Tóm Lại

- ❌ **KHÔNG CẦN** tạo MySQL container
- ❌ **KHÔNG CẦN** setup MySQL mới
- ✅ **CHỈ CẦN** import schema vào database có sẵn
- ✅ **CHỈ CẦN** cấu hình `.env` với `DB_HOST=localhost`
