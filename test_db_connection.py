#!/usr/bin/env python3
"""
Test kết nối database MySQL
"""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv('backend/.env')

def test_connection():
    """Test kết nối database"""
    print("=" * 60)
    print("TEST KẾT NỐI DATABASE MYSQL")
    print("=" * 60)
    print()
    
    # Get database credentials
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_NAME = os.getenv("DB_NAME", "tooltinhreveneu_1")
    DB_USER = os.getenv("DB_USER", "tooltinhreveneu_1")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_TYPE = os.getenv("DB_TYPE", "mysql").lower()
    
    print(f"Database Type: {DB_TYPE}")
    print(f"Host: {DB_HOST}")
    print(f"Port: {DB_PORT}")
    print(f"Database: {DB_NAME}")
    print(f"Username: {DB_USER}")
    print(f"Password: {'*' * len(DB_PASSWORD)}")
    print()
    
    # Build connection string
    if DB_TYPE == "mysql":
        DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    else:
        DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    print(f"Connection String: {DATABASE_URL.split('@')[0]}@***")
    print()
    
    try:
        print("Đang kết nối đến database...")
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            echo=False
        )
        
        # Test connection
        with engine.connect() as conn:
            # Test query
            if DB_TYPE == "mysql":
                result = conn.execute(text("SELECT VERSION()"))
            else:
                result = conn.execute(text("SELECT version()"))
            
            version = result.fetchone()[0]
            print(f"✅ Kết nối thành công!")
            print(f"   Database Version: {version}")
            print()
            
            # Check if database exists and list tables
            if DB_TYPE == "mysql":
                result = conn.execute(text("SHOW TABLES"))
            else:
                result = conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = :schema
                """), {"schema": DB_NAME})
            
            tables = [row[0] for row in result.fetchall()]
            
            if tables:
                print(f"✅ Database có {len(tables)} bảng:")
                for table in tables:
                    print(f"   - {table}")
            else:
                print("⚠️  Database chưa có bảng nào")
                print("   Cần chạy database_schema.sql để tạo schema")
            
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
        print(f"Error: {str(e)}")
        print()
        print("Kiểm tra:")
        print("1. Database credentials trong backend/.env")
        print("2. Database server đang chạy")
        print("3. Network connection đến database host")
        print("4. Firewall rules cho phép kết nối")
        print("5. User có quyền truy cập database")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
