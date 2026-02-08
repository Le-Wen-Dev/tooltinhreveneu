#!/usr/bin/env python3
"""
Tool để đăng nhập và scrape dữ liệu từ trang revenue share
Giả lập hành vi người dùng để tránh bị phát hiện
"""

import requests
from bs4 import BeautifulSoup
import time
import csv
import json
from typing import List, Dict
import sys
from urllib.parse import urljoin, urlparse, parse_qs


class RevenueShareScraper:
    def __init__(self, username: str, password: str, base_url: str = "https://gstudio.gliacloud.com"):
        self.username = username
        self.password = password
        self.base_url = base_url
        self.session = requests.Session()
        
        # Giả lập trình duyệt thật
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def _human_delay(self, min_seconds: float = 1.0, max_seconds: float = 3.0):
        """Thêm delay ngẫu nhiên để giả lập hành vi người dùng"""
        import random
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def login(self, redirect_url: str = None) -> bool:
        """Đăng nhập vào hệ thống"""
        print("Đang truy cập trang đăng nhập...")
        
        # URL đăng nhập chính xác dựa trên cấu trúc form
        login_path = "/ad-sharing/login/"
        login_url = urljoin(self.base_url, login_path)
        
        # Nếu có redirect_url, thêm vào query string
        if redirect_url:
            from urllib.parse import quote
            next_param = quote(redirect_url, safe='')
            login_url = f"{login_url}?next={next_param}"
        
        try:
            response = self.session.get(login_url)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Lỗi khi truy cập trang đăng nhập: {e}")
            return False
        
        self._human_delay(1, 2)
        
        # Parse HTML để lấy CSRF token và form action
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Tìm form đăng nhập (form có id="login-form")
        login_form = soup.find('form', {'id': 'login-form'})
        if not login_form:
            # Thử tìm form bất kỳ có action chứa "login"
            login_form = soup.find('form', {'action': lambda x: x and 'login' in x.lower()})
        
        if not login_form:
            print("Không tìm thấy form đăng nhập!")
            return False
        
        # Lấy action của form (có thể là relative URL)
        form_action = login_form.get('action', '')
        if form_action:
            # Nếu là relative URL, join với base_url
            if form_action.startswith('/'):
                full_login_url = urljoin(self.base_url, form_action)
            else:
                full_login_url = urljoin(login_url, form_action)
        else:
            full_login_url = login_url
        
        # Lấy CSRF token từ input hidden
        csrf_input = login_form.find('input', {'name': 'csrfmiddlewaretoken'})
        if not csrf_input:
            # Thử lấy từ cookie
            csrf_token = self.session.cookies.get('csrftoken')
            if not csrf_token:
                csrf_token = self.session.cookies.get('csrf')
        else:
            csrf_token = csrf_input.get('value')
        
        if not csrf_token:
            print("Không tìm thấy CSRF token!")
            return False
        
        print(f"Đã lấy CSRF token: {csrf_token[:20]}...")
        
        # Lấy giá trị 'next' từ form (nếu có)
        next_input = login_form.find('input', {'name': 'next'})
        next_value = None
        if next_input:
            next_value = next_input.get('value')
        elif redirect_url:
            next_value = redirect_url
        
        # Thực hiện đăng nhập
        print("Đang đăng nhập...")
        login_data = {
            'username': self.username,
            'password': self.password,
            'csrfmiddlewaretoken': csrf_token,
        }
        
        # Thêm field 'next' nếu có
        if next_value:
            login_data['next'] = next_value
        
        # Cập nhật headers cho POST request
        self.session.headers.update({
            'Referer': login_url,
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': self.base_url,
        })
        
        try:
            response = self.session.post(full_login_url, data=login_data, allow_redirects=True)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Lỗi khi đăng nhập: {e}")
            return False
        
        self._human_delay(1, 2)
        
        # Kiểm tra xem đăng nhập có thành công không
        # Nếu vẫn ở trang login, có thể đăng nhập thất bại
        if 'login' in response.url.lower():
            post_soup = BeautifulSoup(response.text, 'html.parser')
            # Tìm thông báo lỗi
            error_elements = post_soup.find_all(['div', 'p', 'span'], 
                string=lambda text: text and any(keyword in text.lower() 
                    for keyword in ['error', 'invalid', 'incorrect', 'wrong', 'failed']))
            
            if error_elements:
                print("Đăng nhập thất bại: Tên đăng nhập hoặc mật khẩu không đúng")
                # In thông báo lỗi nếu có
                for elem in error_elements[:1]:  # Chỉ in lỗi đầu tiên
                    error_text = elem.get_text(strip=True)
                    if error_text:
                        print(f"  Chi tiết: {error_text}")
                return False
        
        # Kiểm tra xem có thể truy cập trang đích không
        test_url = "https://gstudio.gliacloud.com/ad-sharing/publisher/revenueshare/"
        try:
            test_response = self.session.get(test_url)
            if test_response.status_code == 200:
                # Kiểm tra xem có redirect về login không
                if 'login' not in test_response.url.lower():
                    print("✅ Đăng nhập thành công!")
                    return True
                else:
                    print("⚠️  Cảnh báo: Có thể đăng nhập không thành công (redirect về login)")
                    return False
            else:
                print(f"⚠️  Cảnh báo: Không thể truy cập trang đích (status: {test_response.status_code})")
                return False
        except Exception as e:
            print(f"⚠️  Cảnh báo: Lỗi khi kiểm tra đăng nhập: {e}")
            return False
    
    def _build_page_url(self, base_url: str, page: int) -> str:
        """Xây dựng URL cho trang cụ thể"""
        parsed_url = urlparse(base_url)
        query_params = parse_qs(parsed_url.query)
        
        if page > 1:
            query_params['p'] = [str(page)]
        elif 'p' in query_params:
            del query_params['p']
        
        # Tái tạo query string, giữ nguyên format cho 'channel'
        query_parts = []
        for k, v in query_params.items():
            if k == 'channel':
                # Giữ nguyên format "No+Filter"
                query_parts.append(f"{k}={v[0]}")
            else:
                query_parts.append(f"{k}={v[0]}")
        
        new_query = '&'.join(query_parts)
        return f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}?{new_query}"
    
    def scrape_table_first_page_only(self, url: str) -> List[Dict]:
        """Scrape dữ liệu từ bảng - chỉ trang đầu tiên"""
        print(f"Đang truy cập URL: {url}")
        
        all_data = []
        headers = None
        
        current_url = url
        print(f"Đang lấy dữ liệu trang 1...")
        
        try:
            response = self.session.get(current_url)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Lỗi khi truy cập trang: {e}")
            return []
        
        self._human_delay(1, 2)
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Tìm bảng
        table = soup.find('table', {'id': 'result_list'})
        if not table:
            print(f"Không tìm thấy bảng")
            return []
        
        # Lấy headers
        if headers is None:
            headers = []
            thead = table.find('thead')
            if thead:
                header_row = thead.find('tr')
                if header_row:
                    for th in header_row.find_all('th'):
                        # Lấy text từ th, có thể có nested div
                        div = th.find('div', class_='text')
                        if div:
                            header_text = div.get_text(strip=True)
                        else:
                            header_text = th.get_text(strip=True)
                        # Giữ nguyên case của header (không lowercase)
                        headers.append(header_text)
        
        # Lấy dữ liệu từ tbody
        tbody = table.find('tbody')
        if tbody:
            rows = tbody.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) == len(headers):
                    row_data = {}
                    for i, cell in enumerate(cells):
                        cell_text = cell.get_text(strip=True)
                        row_data[headers[i]] = cell_text
                    all_data.append(row_data)
        
        print(f"Đã lấy được {len(all_data)} dòng dữ liệu từ trang 1")
        return all_data
    
    def scrape_table(self, url: str) -> List[Dict]:
        """Scrape dữ liệu từ bảng"""
        print(f"Đang truy cập URL: {url}")
        
        all_data = []
        page = 1
        headers = None
        
        while True:
            current_url = self._build_page_url(url, page)
            print(f"Đang lấy dữ liệu trang {page}...")
            
            try:
                response = self.session.get(current_url)
                response.raise_for_status()
            except requests.RequestException as e:
                print(f"Lỗi khi truy cập trang {page}: {e}")
                break
            
            self._human_delay(1, 2)
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Tìm bảng
            table = soup.find('table', {'id': 'result_list'})
            if not table:
                print(f"Không tìm thấy bảng trên trang {page}")
                break
            
            # Lấy headers (chỉ lần đầu)
            if headers is None:
                headers = []
                thead = table.find('thead')
                if thead:
                    header_row = thead.find('tr')
                    if header_row:
                        for th in header_row.find_all('th'):
                            # Lấy text từ th, có thể có nested div
                            div = th.find('div', class_='text')
                            if div:
                                header_text = div.get_text(strip=True)
                            else:
                                header_text = th.get_text(strip=True)
                            # Giữ nguyên case của header (không lowercase)
                            headers.append(header_text)
            
            # Lấy dữ liệu từ tbody
            tbody = table.find('tbody')
            page_data_count = 0
            if tbody:
                rows = tbody.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) == len(headers):
                        row_data = {}
                        for i, cell in enumerate(cells):
                            cell_text = cell.get_text(strip=True)
                            row_data[headers[i]] = cell_text
                        all_data.append(row_data)
                        page_data_count += 1
            
            print(f"  → Lấy được {page_data_count} dòng từ trang {page}")
            
            # Kiểm tra phân trang
            paginator = soup.find('div', class_='changelist-footer')
            has_next_page = False
            
            if paginator:
                # Tìm trang hiện tại
                this_page_span = paginator.find('span', class_='this-page')
                current_page_num = page
                if this_page_span:
                    try:
                        current_page_num = int(this_page_span.get_text(strip=True))
                    except:
                        pass
                
                # Tìm tất cả các link trang để xác định trang cuối
                page_links = paginator.find_all('a', href=True)
                max_page_num = current_page_num
                
                for link in page_links:
                    href = link.get('href', '')
                    if 'p=' in href:
                        try:
                            # Parse URL để lấy số trang
                            link_url = urljoin(self.base_url, href)
                            parsed_link = urlparse(link_url)
                            link_params = parse_qs(parsed_link.query)
                            if 'p' in link_params:
                                link_page = int(link_params['p'][0])
                                max_page_num = max(max_page_num, link_page)
                        except:
                            pass
                
                # Kiểm tra xem có trang tiếp theo không
                if current_page_num < max_page_num:
                    has_next_page = True
                elif page_data_count == 0:
                    # Không có dữ liệu trên trang này, dừng lại
                    has_next_page = False
                else:
                    # Có thể đã đến trang cuối, nhưng kiểm tra thêm
                    # Nếu không có link nào có số trang lớn hơn trang hiện tại
                    has_next_page = False
            
            if not has_next_page:
                print(f"Đã đến trang cuối (trang {page})")
                break
            
            page += 1
            
            # Giới hạn số trang để tránh vòng lặp vô hạn
            if page > 1000:
                print("Đã đạt giới hạn 1000 trang")
                break
        
        print(f"\nĐã lấy được {len(all_data)} dòng dữ liệu từ {page - 1} trang")
        return all_data
    
    def save_to_csv(self, data: List[Dict], filename: str = "revenue_share_data.csv"):
        """Lưu dữ liệu ra file CSV"""
        if not data:
            print("Không có dữ liệu để lưu")
            return
        
        print(f"Đang lưu dữ liệu vào {filename}...")
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        
        print(f"Đã lưu {len(data)} dòng vào {filename}")
    
    def save_to_json(self, data: List[Dict], filename: str = "revenue_share_data.json"):
        """Lưu dữ liệu ra file JSON"""
        if not data:
            print("Không có dữ liệu để lưu")
            return
        
        print(f"Đang lưu dữ liệu vào {filename}...")
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"Đã lưu {len(data)} dòng vào {filename}")


def main():
    # Thông tin đăng nhập
    USERNAME = "maxvaluemedia"
    PASSWORD = "gliacloud"
    
    # URL cần scrape
    TARGET_URL = "https://gstudio.gliacloud.com/ad-sharing/publisher/revenueshare/?channel=No+Filter&time_unit_date__range__gte=2026-01-26&time_unit_date__range__lte=2026-01-26"
    
    # Tạo scraper
    scraper = RevenueShareScraper(USERNAME, PASSWORD)
    
    # Đăng nhập
    if not scraper.login():
        print("Không thể đăng nhập. Thoát chương trình.")
        sys.exit(1)
    
    # Scrape dữ liệu
    data = scraper.scrape_table(TARGET_URL)
    
    if data:
        # Lưu ra CSV
        scraper.save_to_csv(data, "revenue_share_data.csv")
        
        # Lưu ra JSON
        scraper.save_to_json(data, "revenue_share_data.json")
        
        # Hiển thị một vài dòng đầu
        print("\n=== Mẫu dữ liệu (5 dòng đầu) ===")
        for i, row in enumerate(data[:5], 1):
            print(f"\nDòng {i}:")
            for key, value in row.items():
                print(f"  {key}: {value}")
    else:
        print("Không lấy được dữ liệu nào")


if __name__ == "__main__":
    main()
