#!/usr/bin/env python3
"""
Tạo user mới từ dòng lệnh (CLI).
Chạy: python create_user.py --username USER --email EMAIL --password PASS [--role admin|user] [--can-view-data]

Ví dụ:
  python create_user.py --username newuser --email new@example.com --password MyPass123
  python create_user.py --username newadmin --email admin2@local --password Secret --role admin --can-view-data
"""

import argparse
import secrets
import sys
from pathlib import Path

# Load .env từ thư mục gốc
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dotenv import load_dotenv
load_dotenv()

# Hash password (giống api/main.py: bcrypt, tối đa 72 byte)
try:
    import bcrypt
    def hash_password(password: str) -> str:
        raw = password.encode("utf-8")
        if len(raw) > 72:
            raw = raw[:72]
        return bcrypt.hashpw(raw, bcrypt.gensalt()).decode("utf-8")
except ImportError:
    from passlib.context import CryptContext
    pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
    def hash_password(password: str) -> str:
        raw = password.encode("utf-8")
        if len(raw) > 72:
            password = raw[:72].decode("utf-8", errors="replace")
        return pwd_ctx.hash(password)


def main():
    parser = argparse.ArgumentParser(description="Tạo user mới (CLI)")
    parser.add_argument("--username", required=True, help="Tên đăng nhập")
    parser.add_argument("--email", required=True, help="Email (unique)")
    parser.add_argument("--password", required=True, help="Mật khẩu")
    parser.add_argument("--role", default="user", choices=["user", "admin"], help="Role (default: user)")
    parser.add_argument("--can-view-data", action="store_true", help="Cho phép xem data và dùng API")
    args = parser.parse_args()

    from crawler.db import get_db_session, User

    db = next(get_db_session())
    try:
        if db.query(User).filter(User.username == args.username).first():
            print(f"Lỗi: Username '{args.username}' đã tồn tại.")
            sys.exit(1)
        if db.query(User).filter(User.email == args.email).first():
            print(f"Lỗi: Email '{args.email}' đã tồn tại.")
            sys.exit(1)

        api_key = secrets.token_urlsafe(32)
        user = User(
            username=args.username.strip(),
            email=args.email.strip(),
            password_hash=hash_password(args.password),
            role=args.role,
            can_view_data=args.can_view_data,
            api_key=api_key,
            is_active=True,
        )
        db.add(user)
        db.commit()
        print(f"Đã tạo user: {args.username} (role={args.role}, can_view_data={args.can_view_data})")
        print(f"API Key: {api_key}")
    except Exception as e:
        db.rollback()
        print(f"Lỗi: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
