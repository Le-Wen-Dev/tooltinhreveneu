#!/usr/bin/env python3
"""
Ví dụ sử dụng RevenueShareScraper với các tham số tùy chỉnh
"""

from scraper import RevenueShareScraper
from datetime import datetime, timedelta

def example_basic():
    """Ví dụ cơ bản"""
    scraper = RevenueShareScraper("maxvaluemedia", "gliacloud")
    
    if scraper.login():
        url = "https://gstudio.gliacloud.com/ad-sharing/publisher/revenueshare/?channel=No+Filter&time_unit_date__range__gte=2026-01-26&time_unit_date__range__lte=2026-01-26"
        data = scraper.scrape_table(url)
        
        if data:
            scraper.save_to_csv(data, "output.csv")
            scraper.save_to_json(data, "output.json")
            print(f"Đã lưu {len(data)} dòng dữ liệu")

def example_custom_date_range():
    """Ví dụ với khoảng thời gian tùy chỉnh"""
    scraper = RevenueShareScraper("maxvaluemedia", "gliacloud")
    
    if scraper.login():
        # Tùy chỉnh ngày bắt đầu và kết thúc
        start_date = "2026-01-01"
        end_date = "2026-01-31"
        
        url = f"https://gstudio.gliacloud.com/ad-sharing/publisher/revenueshare/?channel=No+Filter&time_unit_date__range__gte={start_date}&time_unit_date__range__lte={end_date}"
        
        data = scraper.scrape_table(url)
        
        if data:
            filename = f"revenue_{start_date}_to_{end_date}.csv"
            scraper.save_to_csv(data, filename)
            print(f"Đã lưu dữ liệu vào {filename}")

def example_specific_channel():
    """Ví dụ lọc theo channel cụ thể"""
    scraper = RevenueShareScraper("maxvaluemedia", "gliacloud")
    
    if scraper.login():
        # Thay "No+Filter" bằng tên channel cụ thể
        channel = "maxvaluemedia_spotpariz"  # URL encode: maxvaluemedia+spotpariz
        channel_encoded = channel.replace("_", "+")
        
        start_date = "2026-01-26"
        end_date = "2026-01-26"
        
        url = f"https://gstudio.gliacloud.com/ad-sharing/publisher/revenueshare/?channel={channel_encoded}&time_unit_date__range__gte={start_date}&time_unit_date__range__lte={end_date}"
        
        data = scraper.scrape_table(url)
        
        if data:
            scraper.save_to_csv(data, f"revenue_{channel}.csv")
            print(f"Đã lưu dữ liệu cho channel {channel}")

if __name__ == "__main__":
    print("Chọn ví dụ:")
    print("1. Ví dụ cơ bản")
    print("2. Ví dụ với khoảng thời gian tùy chỉnh")
    print("3. Ví dụ lọc theo channel")
    
    choice = input("Nhập số (1-3): ").strip()
    
    if choice == "1":
        example_basic()
    elif choice == "2":
        example_custom_date_range()
    elif choice == "3":
        example_specific_channel()
    else:
        print("Lựa chọn không hợp lệ")
