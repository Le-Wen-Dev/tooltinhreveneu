# Revenue Share Data Scraper

Tool Python để đăng nhập và scrape dữ liệu từ trang revenue share của GStudio.

## Tính năng

- ✅ Giả lập hành vi người dùng thật (delay ngẫu nhiên, headers trình duyệt)
- ✅ Xử lý đăng nhập với CSRF token
- ✅ Scrape dữ liệu từ bảng HTML
- ✅ Tự động xử lý phân trang (pagination)
- ✅ Export dữ liệu ra CSV và JSON

## Cài đặt

```bash
pip install -r requirements.txt
```

## Sử dụng

### Chạy trực tiếp

```bash
python scraper.py
```

### Sử dụng như module

```python
from scraper import RevenueShareScraper

scraper = RevenueShareScraper("username", "password")
scraper.login()
data = scraper.scrape_table("https://gstudio.gliacloud.com/ad-sharing/publisher/revenueshare/?...")
scraper.save_to_csv(data, "output.csv")
```

## Cấu trúc dữ liệu

Bảng dữ liệu bao gồm các cột:
- channel
- slot
- time unit
- total player impr
- total ad impr
- rpm
- gross revenue (usd)
- net revenue (usd)

## Output

Tool sẽ tạo 2 file:
- `revenue_share_data.csv` - Dữ liệu dạng CSV
- `revenue_share_data.json` - Dữ liệu dạng JSON

## Lưu ý

- Tool có delay ngẫu nhiên giữa các request để tránh bị phát hiện
- Tự động xử lý phân trang, lấy tất cả dữ liệu từ các trang
- Giới hạn tối đa 1000 trang để tránh vòng lặp vô hạn (có thể điều chỉnh trong code)
