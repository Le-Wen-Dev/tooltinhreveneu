# Hướng Dẫn Setup Cron Job - Fetch Data 2 Lần Mỗi Ngày

## 📋 Tổng Quan

Hệ thống đã được cấu hình để:
- ✅ **Fetch data 2 lần mỗi ngày** (8:00 AM và 8:00 PM)
- ✅ **Ghi đè dữ liệu cũ** (update thay vì insert mới)
- ✅ **Tự động tính toán formulas** sau mỗi lần fetch
- ✅ **Log mọi hoạt động** vào file log

## 🚀 Cách 1: Setup Tự Động (Khuyên dùng)

```bash
# Chạy script setup
chmod +x setup_cron.sh
./setup_cron.sh
```

Script sẽ tự động:
- Tạo thư mục logs
- Cập nhật đường dẫn trong script
- Thêm cron jobs vào crontab

## 🔧 Cách 2: Setup Thủ Công

### Bước 1: Chỉnh sửa đường dẫn

Mở file `cron_fetch.sh` và thay đổi `PROJECT_DIR`:

```bash
PROJECT_DIR="/path/to/toolgetdata"  # Thay đổi thành đường dẫn thực tế
```

### Bước 2: Cho phép thực thi script

```bash
chmod +x cron_fetch.sh
```

### Bước 3: Thêm vào crontab

```bash
# Mở crontab editor
crontab -e

# Thêm 2 dòng sau (thay đổi đường dẫn cho đúng):
0 8 * * * /path/to/toolgetdata/cron_fetch.sh
0 20 * * * /path/to/toolgetdata/cron_fetch.sh

# Lưu và thoát
```

## ⏰ Thay Đổi Thời Gian Fetch

Nếu muốn thay đổi thời gian fetch, sửa trong crontab:

```bash
crontab -e
```

**Format cron**: `phút giờ * * * command`

**Ví dụ**:
- `0 6,18 * * *` → 6:00 AM và 6:00 PM
- `0 9,21 * * *` → 9:00 AM và 9:00 PM
- `0 */12 * * *` → Mỗi 12 giờ (0:00 và 12:00)
- `30 7,19 * * *` → 7:30 AM và 7:30 PM

## 📊 Kiểm Tra Cron Jobs

### Xem cron jobs hiện tại:
```bash
crontab -l
```

### Test script thủ công:
```bash
./cron_fetch.sh
```

### Xem logs:
```bash
tail -f logs/cron_fetch.log
```

## 🔄 Cách Hoạt Động

1. **Cron trigger**: Cron chạy script `cron_fetch.sh` vào giờ đã định
2. **Script chạy**: Script gọi `backend/data_fetcher.py` với ngày hôm nay
3. **Fetch data**: Scraper đăng nhập và lấy dữ liệu
4. **Update database**: 
   - Nếu record đã tồn tại → **Update (ghi đè)**
   - Nếu record chưa có → **Insert mới**
5. **Compute formulas**: Tự động tính toán các formulas
6. **Log**: Ghi log vào `logs/cron_fetch.log`

## 📝 Logic Ghi Đè

Hệ thống sẽ **ghi đè** dữ liệu cũ dựa trên:
- `channel`
- `slot`
- `time_unit`
- `fetch_date`

Nếu 4 trường này khớp → Update record cũ
Nếu không khớp → Tạo record mới

## 🐛 Troubleshooting

### Cron không chạy

1. **Kiểm tra cron service**:
   ```bash
   # macOS
   sudo launchctl list | grep cron
   
   # Linux
   sudo systemctl status cron
   ```

2. **Kiểm tra permissions**:
   ```bash
   ls -l cron_fetch.sh
   # Phải có quyền execute: -rwxr-xr-x
   ```

3. **Kiểm tra đường dẫn**:
   - Đảm bảo đường dẫn trong crontab là **absolute path**
   - Không dùng `~` hoặc relative path

4. **Kiểm tra Python path**:
   - Nếu dùng venv, đảm bảo đường dẫn đúng
   - Hoặc sửa `cron_fetch.sh` để dùng `python3` system

### Logs không được ghi

1. **Kiểm tra quyền ghi**:
   ```bash
   mkdir -p logs
   chmod 755 logs
   ```

2. **Kiểm tra đường dẫn**:
   - Đảm bảo `PROJECT_DIR` đúng

### Data không được update

1. **Kiểm tra database connection**:
   - Xem file `.env` có đúng không
   - Test kết nối database

2. **Kiểm tra logs**:
   ```bash
   tail -n 50 logs/cron_fetch.log
   ```

3. **Test thủ công**:
   ```bash
   python3 backend/data_fetcher.py --date $(date +%Y-%m-%d)
   ```

## 📅 Lịch Fetch Mặc Định

- **8:00 AM** - Fetch dữ liệu buổi sáng
- **8:00 PM** - Fetch dữ liệu buổi tối

Có thể thay đổi trong crontab.

## 🔍 Monitor Cron Jobs

### Xem log real-time:
```bash
tail -f logs/cron_fetch.log
```

### Xem cron history (macOS):
```bash
grep CRON /var/log/system.log
```

### Xem cron history (Linux):
```bash
grep CRON /var/log/syslog
# hoặc
journalctl -u cron
```

## ✅ Checklist

- [ ] Đã chỉnh sửa `PROJECT_DIR` trong `cron_fetch.sh`
- [ ] Đã chmod script: `chmod +x cron_fetch.sh`
- [ ] Đã thêm cron jobs vào crontab
- [ ] Đã test script thủ công: `./cron_fetch.sh`
- [ ] Đã kiểm tra logs: `tail logs/cron_fetch.log`
- [ ] Database connection đã được cấu hình trong `.env`

## 📞 Support

Nếu gặp vấn đề:
1. Kiểm tra logs: `logs/cron_fetch.log`
2. Test script thủ công
3. Kiểm tra crontab: `crontab -l`
4. Xem database có data mới không
