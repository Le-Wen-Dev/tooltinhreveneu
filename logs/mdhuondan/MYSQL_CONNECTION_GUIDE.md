# Hướng Dẫn Kết Nối MySQL Production

## ❌ Vấn Đề Hiện Tại

Kết nối bị timeout vì:
- MySQL server có thể chỉ cho phép kết nối từ **localhost** (không cho remote)
- Firewall có thể block port 3306
- MySQL `bind-address` có thể chỉ là `127.0.0.1`

## ✅ Giải Pháp

### Option 1: Kết Nối Từ Server (Khuyên dùng)

**Chạy backend code TRÊN SERVER** (36.50.27.158):

1. SSH vào server:
   ```bash
   ssh tooltinhreveneu@gmail.com@36.50.27.158 -p 2222
   ```

2. Upload code lên server và chạy:
   ```bash
   # Trên server
   cd /path/to/toolgetdata
   python3 backend/app.py
   ```

3. Database connection sẽ dùng `localhost` thay vì IP:
   ```env
   DB_HOST=localhost
   ```

### Option 2: SSH Tunnel (Nếu muốn chạy từ máy local)

Tạo SSH tunnel để forward port MySQL:

```bash
# Tạo tunnel
ssh -L 3307:localhost:3306 tooltinhreveneu@gmail.com@36.50.27.158 -p 2222

# Sau đó kết nối qua localhost:3307
DB_HOST=localhost
DB_PORT=3307
```

### Option 3: Cấu Hình MySQL Cho Remote Access

**CẢNH BÁO**: Chỉ làm nếu bạn có quyền admin và hiểu rủi ro bảo mật.

1. SSH vào server
2. Sửa MySQL config:
   ```bash
   sudo nano /etc/mysql/mysql.conf.d/mysqld.cnf
   ```
   
   Thay đổi:
   ```ini
   bind-address = 0.0.0.0  # Thay vì 127.0.0.1
   ```

3. Tạo user với remote access:
   ```sql
   CREATE USER 'tooltinhreveneu_1'@'%' IDENTIFIED BY 'tooltinhreveneu@gndhsggkl';
   GRANT ALL PRIVILEGES ON tooltinhreveneu_1.* TO 'tooltinhreveneu_1'@'%';
   FLUSH PRIVILEGES;
   ```

4. Restart MySQL:
   ```bash
   sudo systemctl restart mysql
   ```

5. Mở firewall:
   ```bash
   sudo ufw allow 3306/tcp
   ```

## 📝 Cấu Hình .env

### Nếu chạy TRÊN SERVER:
```env
DB_TYPE=mysql
DB_HOST=localhost
DB_PORT=3306
DB_NAME=tooltinhreveneu_1
DB_USER=tooltinhreveneu_1
DB_PASSWORD=tooltinhreveneu@gndhsggkl
```

### Nếu dùng SSH Tunnel:
```env
DB_TYPE=mysql
DB_HOST=localhost
DB_PORT=3307  # Port của tunnel
DB_NAME=tooltinhreveneu_1
DB_USER=tooltinhreveneu_1
DB_PASSWORD=tooltinhreveneu@gndhsggkl
```

### Nếu MySQL cho phép remote:
```env
DB_TYPE=mysql
DB_HOST=36.50.27.158
DB_PORT=3306
DB_NAME=tooltinhreveneu_1
DB_USER=tooltinhreveneu_1
DB_PASSWORD=tooltinhreveneu@gndhsggkl
```

## 🧪 Test Kết Nối

### Từ Server:
```bash
# SSH vào server
ssh tooltinhreveneu@gmail.com@36.50.27.158 -p 2222

# Test MySQL connection
mysql -u tooltinhreveneu_1 -p tooltinhreveneu_1
# Nhập password: tooltinhreveneu@gndhsggkl

# Nếu kết nối được → OK
```

### Từ Local (với SSH tunnel):
```bash
# Terminal 1: Tạo tunnel
ssh -L 3307:localhost:3306 tooltinhreveneu@gmail.com@36.50.27.158 -p 2222

# Terminal 2: Test connection
python3 test_db_direct.py
# (Sửa DB_PORT=3307 trong script)
```

## 🔒 Bảo Mật

**QUAN TRỌNG**: 
- Không expose MySQL ra internet công khai
- Sử dụng SSH tunnel hoặc chạy code trên server
- Chỉ enable remote access nếu thực sự cần và có firewall rules

## 📞 Next Steps

1. **Quyết định phương án**:
   - [ ] Chạy backend trên server (Option 1) - **Khuyên dùng**
   - [ ] Dùng SSH tunnel (Option 2)
   - [ ] Cấu hình remote access (Option 3) - **Cần quyền admin**

2. **Cập nhật .env** với thông tin phù hợp

3. **Test kết nối** lại

4. **Chạy schema**:
   ```bash
   mysql -u tooltinhreveneu_1 -p tooltinhreveneu_1 < database_schema_mysql.sql
   ```

5. **Test API**:
   ```bash
   python3 backend/app.py
   ```
