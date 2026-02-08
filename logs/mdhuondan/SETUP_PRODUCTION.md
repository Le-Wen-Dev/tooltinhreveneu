# Setup Production - Tóm Tắt

## 📋 Thông Tin Đã Có

- **Hosting**: http://36.50.27.158:2222/
- **Database**: MySQL
- **DB Name**: tooltinhreveneu_1
- **DB User**: tooltinhreveneu_1
- **DB Password**: tooltinhreveneu@gndhsggkl
- **DB Host**: localhost (trên server) hoặc 36.50.27.158 (nếu cho phép remote)

## ⚠️ Vấn Đề Kết Nối

MySQL server **không cho phép kết nối từ bên ngoài** (timeout). Đây là bảo mật bình thường.

## ✅ Giải Pháp Đề Xuất

### **Chạy Backend TRÊN SERVER** (Khuyên dùng)

1. **Upload code lên server**:
   ```bash
   # Từ máy local
   scp -P 2222 -r toolgetdata tooltinhreveneu@gmail.com@36.50.27.158:/path/to/
   ```

2. **SSH vào server**:
   ```bash
   ssh tooltinhreveneu@gmail.com@36.50.27.158 -p 2222
   ```

3. **Cài đặt dependencies**:
   ```bash
   cd /path/to/toolgetdata
   pip3 install -r backend/requirements.txt
   ```

4. **Tạo file .env trên server**:
   ```env
   DB_TYPE=mysql
   DB_HOST=localhost
   DB_PORT=3306
   DB_NAME=tooltinhreveneu_1
   DB_USER=tooltinhreveneu_1
   DB_PASSWORD=tooltinhreveneu@gndhsggkl
   SCRAPER_USERNAME=maxvaluemedia
   SCRAPER_PASSWORD=gliacloud
   API_HOST=0.0.0.0
   API_PORT=8000
   ```

5. **Chạy schema**:
   ```bash
   mysql -u tooltinhreveneu_1 -p tooltinhreveneu_1 < database_schema_mysql.sql
   # Password: tooltinhreveneu@gndhsggkl
   ```

6. **Test kết nối**:
   ```bash
   python3 test_db_direct.py
   # (Sửa DB_HOST=localhost)
   ```

7. **Chạy API**:
   ```bash
   cd backend
   uvicorn app:app --host 0.0.0.0 --port 8000
   ```

## 📝 Files Đã Tạo

1. ✅ `database_schema_mysql.sql` - Schema cho MySQL
2. ✅ `backend/.env.example` - Template .env
3. ✅ `test_db_direct.py` - Script test kết nối
4. ✅ `backend/app.py` - Đã cập nhật hỗ trợ MySQL
5. ✅ `backend/requirements.txt` - Đã thêm pymysql

## 🔄 Workflow

1. **Upload code lên server**
2. **Tạo .env với DB_HOST=localhost**
3. **Chạy schema MySQL**
4. **Test kết nối**
5. **Chạy API server**
6. **Setup cron jobs** (trên server)

## 📞 Cần Làm

1. **Quyết định**: Chạy trên server hay dùng SSH tunnel?
2. **Upload code** lên server
3. **Tạo .env** với thông tin đúng
4. **Chạy schema** để tạo tables
5. **Test** và deploy

Xem chi tiết: `MYSQL_CONNECTION_GUIDE.md`
