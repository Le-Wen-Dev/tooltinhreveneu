#!/usr/bin/env python3
"""
Test crawl - chỉ lấy trang đầu tiên
"""

from scraper import RevenueShareScraper
import json

def test_first_page():
    """Test crawl trang đầu tiên"""
    USERNAME = "maxvaluemedia"
    PASSWORD = "gliacloud"
    TARGET_URL = "https://gstudio.gliacloud.com/ad-sharing/publisher/revenueshare/?channel=No+Filter&time_unit_date__range__gte=2026-01-26&time_unit_date__range__lte=2026-01-26"
    
    scraper = RevenueShareScraper(USERNAME, PASSWORD)
    
    print("=" * 60)
    print("TEST CRAWL - TRANG ĐẦU TIÊN")
    print("=" * 60)
    
    # Đăng nhập
    if not scraper.login():
        print("❌ Không thể đăng nhập")
        return None
    
    # Scrape chỉ trang đầu tiên
    print("\n📊 Đang lấy dữ liệu trang 1...")
    data = scraper.scrape_table_first_page_only(TARGET_URL)
    
    if data:
        print(f"\n✅ Đã lấy được {len(data)} dòng dữ liệu")
        print("\n📋 Mẫu dữ liệu:")
        print(json.dumps(data[:3], indent=2, ensure_ascii=False))
        
        # Lưu test data
        with open("test_data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Đã lưu vào test_data.json")
        
        return data
    else:
        print("❌ Không lấy được dữ liệu")
        return None

if __name__ == "__main__":
    test_first_page()
