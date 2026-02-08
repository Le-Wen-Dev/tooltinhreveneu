"""
Database connection and models for crawler
"""

import os
from sqlalchemy import create_engine, Column, Integer, String, Numeric, Boolean, DateTime, Date, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.dialects.mysql import JSON as MySQLJSON
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

# Database Configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "tooltinhreveneu_1")
DB_USER = os.getenv("DB_USER", "tooltinhreveneu_1")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_TYPE = os.getenv("DB_TYPE", "mysql").lower()

# Build connection string
if DB_TYPE == "mysql":
    encoded_password = quote_plus(DB_PASSWORD)
    DATABASE_URL = f"mysql+pymysql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
else:
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Database Models
class RawRevenueData(Base):
    __tablename__ = "raw_revenue_data"
    
    id = Column(Integer, primary_key=True, index=True)
    channel = Column(String(255), nullable=False)
    slot = Column(String(255), nullable=False)
    time_unit = Column(String(50), nullable=False)
    total_player_impr = Column(String(50))
    total_ad_impr = Column(String(50))
    rpm = Column(String(50))
    gross_revenue_usd = Column(String(50))
    net_revenue_usd = Column(String(50))
    fetched_at = Column(DateTime, default=datetime.utcnow)
    fetch_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    computed_metrics = relationship("ComputedMetric", back_populates="raw_data")


class Formula(Base):
    __tablename__ = "formulas"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text)
    formula_expression = Column(Text, nullable=False)
    formula_type = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255))
    formula_metadata = Column(JSONB if 'postgresql' in DATABASE_URL else MySQLJSON)  # Renamed from 'metadata' (reserved word)


class ComputedMetric(Base):
    __tablename__ = "computed_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    raw_data_id = Column(Integer, ForeignKey("raw_revenue_data.id"), nullable=False)
    formula_id = Column(Integer, ForeignKey("formulas.id"), nullable=False)
    metric_name = Column(String(255), nullable=False)
    metric_value = Column(Numeric(20, 6))
    computed_at = Column(DateTime, default=datetime.utcnow)
    
    raw_data = relationship("RawRevenueData", back_populates="computed_metrics")
    formula = relationship("Formula")


class AggregatedMetric(Base):
    __tablename__ = "aggregated_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    channel = Column(String(255))
    time_unit = Column(String(50))
    fetch_date = Column(Date, nullable=False)
    metric_name = Column(String(255), nullable=False)
    metric_value = Column(Numeric(20, 6))
    formula_id = Column(Integer, ForeignKey("formulas.id"))
    computed_at = Column(DateTime, default=datetime.utcnow)


class ProcessedRevenueData(Base):
    """Aggregated data for dashboard (desktop + mobile by slot)."""
    __tablename__ = "processed_revenue_data"
    id = Column(Integer, primary_key=True, index=True)
    slot = Column(String(255), nullable=False)
    time_unit = Column(String(50), nullable=False)
    total_player_impr = Column(Numeric(20, 2))
    revenue = Column(Numeric(20, 2))
    rpm = Column(Numeric(10, 2))
    share = Column(Numeric(5, 2), default=50.00)
    total_player_impr_2 = Column(Numeric(20, 2))
    revenue_2 = Column(Numeric(20, 2))
    rpm_2 = Column(Numeric(10, 2))
    fetch_date = Column(Date, nullable=False)
    processed_at = Column(DateTime, default=datetime.utcnow)


class FetchLog(Base):
    __tablename__ = "fetch_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    fetch_date = Column(Date, nullable=False)
    status = Column(String(50), nullable=False)
    records_fetched = Column(Integer, default=0)
    records_created = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    pages_fetched = Column(Integer, default=0)
    error_message = Column(Text)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    duration_seconds = Column(Integer)


class CrawlRun(Base):
    """Lock table để tránh chạy trùng crawler"""
    __tablename__ = "crawl_runs"
    
    id = Column(Integer, primary_key=True, index=True)
    fetch_date = Column(Date, nullable=False, unique=True)
    status = Column(String(50), nullable=False)  # 'running', 'completed', 'failed'
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    pid = Column(Integer)  # Process ID


class User(Base):
    """Users: login, role (admin/user), can_view_data, api_key for API access"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="user")  # admin | user
    can_view_data = Column(Boolean, default=False)
    api_key = Column(String(64), unique=True, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)


# Dependency
def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# FormulaEngine sẽ được import trong main.py
