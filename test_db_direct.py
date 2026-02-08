#!/usr/bin/env python3
"""
Test kết nối database MySQL trực tiếp với thông tin từ file
"""

from sqlalchemy import create_engine, text
from urllib.parse import quote_plus

# Thông tin database từ file thongtinenv.text
DB_HOST = "36.50.27.158"  # IP của server
DB_PORT = 3306
DB_NAME = "tooltinhreveneu_1"
DB_USER = "tooltinhreveneu_1"
DB_PASSWORD = "tooltinhreveneu@gndhsggkl"  # Password có ký tự @ cần encode

def test_connection():
    """Test kết nối database"""
    print("=" * 60)
    print("TEST KẾT NỐI DATABASE MYSQL (Production)")
    print("=" * 60)
    print()
    
    print(f"Host: {DB_HOST}")
    print(f"Port: {DB_PORT}")
    print(f"Database: {DB_NAME}")
    print(f"Username: {DB_USER}")
    print(f"Password: {'*' * len(DB_PASSWORD)}")
    print()
    
    # Build connection string (URL encode password để xử lý ký tự đặc biệt)
    encoded_password = quote_plus(DB_PASSWORD)
    DATABASE_URL = f"mysql+pymysql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    
    print(f"Connection String: mysql+pymysql://{DB_USER}:***@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    print()
    
    try:
        print("Đang kết nối đến database...")
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            echo=False,
            connect_args={
                "connect_timeout": 10
            }
        )
        
        # Test connection
        with engine.connect() as conn:
            # Test query
            result = conn.execute(text("SELECT VERSION()"))
            version = result.fetchone()[0]
            print(f"✅ Kết nối thành công!")
            print(f"   MySQL Version: {version}")
            print()
            
            # Check if database exists and list tables
            result = conn.execute(text("SHOW TABLES"))
            tables = [row[0] for row in result.fetchall()]
            
            if tables:
                print(f"✅ Database có {len(tables)} bảng:")
                for table in tables:
                    print(f"   - {table}")
            else:
                print("⚠️  Database chưa có bảng nào")
                print("   Cần chạy database_schema_mysql.sql để tạo schema")
            
            # Check database size
            result = conn.execute(text(f"SELECT ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'DB Size in MB' FROM information_schema.tables WHERE table_schema = '{DB_NAME}'"))
            size = result.fetchone()[0]
            if size:
                print(f"   Database size: {size} MB")
            
            print()
            print("=" * 60)
            print("✅ TEST KẾT NỐI THÀNH CÔNG!")
            print("=" * 60)
            return True
            
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ LỖI KẾT NỐI DATABASE")
        print("=" * 60)
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}")
        print()
        print("Nguyên nhân có thể:")
        print("1. Database server không cho phép kết nối từ IP này")
        print("2. Firewall block port 3306")
        print("3. MySQL chỉ cho phép kết nối từ localhost")
        print("4. User không có quyền remote access")
        print("5. Database server chưa được cấu hình để accept remote connections")
        print()
        print("Giải pháp:")
        print("- Kiểm tra MySQL config: bind-address trong my.cnf")
        print("- Kiểm tra firewall rules")
        print("- Kiểm tra user có quyền '%' (all hosts) hoặc IP cụ thể")
        print("- Thử kết nối từ server (SSH vào server rồi test)")
        return False

if __name__ == "__main__":
    import sys
    success = test_connection()
    sys.exit(0 if success else 1)
