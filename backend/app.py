"""
FastAPI Backend for Revenue Share Data System
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Numeric, Boolean, DateTime, Date, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.mysql import JSON as MySQLJSON
import json
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import os
from dotenv import load_dotenv
import json
import decimal

load_dotenv()

# Database Configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    None
)

# If DATABASE_URL not set, build from individual components (for MySQL)
if not DATABASE_URL:
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_NAME = os.getenv("DB_NAME", "tooltinhreveneu_1")
    DB_USER = os.getenv("DB_USER", "tooltinhreveneu_1")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    
    # Detect database type from connection string or use MySQL as default
    DB_TYPE = os.getenv("DB_TYPE", "mysql").lower()
    
    if DB_TYPE == "mysql":
        from urllib.parse import quote_plus
        encoded_password = quote_plus(DB_PASSWORD)
        DATABASE_URL = f"mysql+pymysql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    else:
        DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create engine with pool settings
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,    # Recycle connections after 1 hour
    echo=False  # Set to True for SQL debugging
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ============================================
# Database Models
# ============================================

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
    # Use JSONB for PostgreSQL, JSON for MySQL
    # Renamed to formula_metadata to avoid SQLAlchemy reserved keyword
    formula_metadata = Column(JSONB if 'postgresql' in DATABASE_URL else MySQLJSON)


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


class FetchLog(Base):
    __tablename__ = "fetch_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    fetch_date = Column(Date, nullable=False)
    status = Column(String(50), nullable=False)
    records_fetched = Column(Integer, default=0)
    pages_fetched = Column(Integer, default=0)
    error_message = Column(Text)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    duration_seconds = Column(Integer)


# ============================================
# Pydantic Models
# ============================================

class RawRevenueDataCreate(BaseModel):
    channel: str
    slot: str
    time_unit: str
    total_player_impr: Optional[str] = None
    total_ad_impr: Optional[str] = None
    rpm: Optional[str] = None
    gross_revenue_usd: Optional[str] = None
    net_revenue_usd: Optional[str] = None
    fetch_date: date


class RawRevenueDataResponse(BaseModel):
    id: int
    channel: str
    slot: str
    time_unit: str
    total_player_impr: Optional[str]
    total_ad_impr: Optional[str]
    rpm: Optional[str]
    gross_revenue_usd: Optional[str]
    net_revenue_usd: Optional[str]
    fetched_at: datetime
    fetch_date: date
    
    class Config:
        from_attributes = True


class FormulaCreate(BaseModel):
    name: str
    description: Optional[str] = None
    formula_expression: str
    formula_type: str
    is_active: bool = True
    metadata: Optional[Dict[str, Any]] = None


class FormulaResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    formula_expression: str
    formula_type: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    metadata: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True


class ComputedMetricResponse(BaseModel):
    id: int
    raw_data_id: int
    formula_id: int
    metric_name: str
    metric_value: Optional[float]
    computed_at: datetime
    
    class Config:
        from_attributes = True


class AggregatedMetricResponse(BaseModel):
    id: int
    channel: Optional[str]
    time_unit: Optional[str]
    fetch_date: date
    metric_name: str
    metric_value: Optional[float]
    formula_id: Optional[int]
    computed_at: datetime
    
    class Config:
        from_attributes = True


# ============================================
# FastAPI App
# ============================================

app = FastAPI(
    title="Revenue Share Data API",
    description="API for managing revenue share data, formulas, and computed metrics",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================
# API Endpoints
# ============================================

@app.get("/")
async def root():
    return {"message": "Revenue Share Data API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}


# Raw Data Endpoints
@app.post("/api/raw-data", response_model=RawRevenueDataResponse, status_code=status.HTTP_201_CREATED)
async def create_raw_data(data: RawRevenueDataCreate, db: Session = Depends(get_db)):
    """Create new raw revenue data entry"""
    db_data = RawRevenueData(**data.dict())
    db.add(db_data)
    db.commit()
    db.refresh(db_data)
    return db_data


@app.post("/api/raw-data/bulk", status_code=status.HTTP_201_CREATED)
async def create_bulk_raw_data(data_list: List[RawRevenueDataCreate], db: Session = Depends(get_db)):
    """Bulk create raw revenue data"""
    db_data_list = [RawRevenueData(**data.dict()) for data in data_list]
    db.add_all(db_data_list)
    db.commit()
    return {"created": len(db_data_list), "message": "Bulk data created successfully"}


@app.get("/api/raw-data", response_model=List[RawRevenueDataResponse])
async def get_raw_data(
    fetch_date: Optional[date] = None,
    channel: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get raw revenue data with optional filters"""
    query = db.query(RawRevenueData)
    
    if fetch_date:
        query = query.filter(RawRevenueData.fetch_date == fetch_date)
    if channel:
        query = query.filter(RawRevenueData.channel == channel)
    
    return query.order_by(RawRevenueData.fetch_date.desc()).offset(offset).limit(limit).all()


@app.get("/api/raw-data/{data_id}", response_model=RawRevenueDataResponse)
async def get_raw_data_by_id(data_id: int, db: Session = Depends(get_db)):
    """Get specific raw revenue data by ID"""
    data = db.query(RawRevenueData).filter(RawRevenueData.id == data_id).first()
    if not data:
        raise HTTPException(status_code=404, detail="Data not found")
    return data


# Formula Endpoints
@app.post("/api/formulas", response_model=FormulaResponse, status_code=status.HTTP_201_CREATED)
async def create_formula(formula: FormulaCreate, db: Session = Depends(get_db)):
    """Create new formula"""
    db_formula = Formula(**formula.dict())
    db.add(db_formula)
    db.commit()
    db.refresh(db_formula)
    return db_formula


@app.get("/api/formulas", response_model=List[FormulaResponse])
async def get_formulas(is_active: Optional[bool] = None, db: Session = Depends(get_db)):
    """Get all formulas"""
    query = db.query(Formula)
    if is_active is not None:
        query = query.filter(Formula.is_active == is_active)
    return query.all()


@app.get("/api/formulas/{formula_id}", response_model=FormulaResponse)
async def get_formula(formula_id: int, db: Session = Depends(get_db)):
    """Get specific formula by ID"""
    formula = db.query(Formula).filter(Formula.id == formula_id).first()
    if not formula:
        raise HTTPException(status_code=404, detail="Formula not found")
    return formula


@app.put("/api/formulas/{formula_id}", response_model=FormulaResponse)
async def update_formula(formula_id: int, formula: FormulaCreate, db: Session = Depends(get_db)):
    """Update existing formula"""
    db_formula = db.query(Formula).filter(Formula.id == formula_id).first()
    if not db_formula:
        raise HTTPException(status_code=404, detail="Formula not found")
    
    for key, value in formula.dict().items():
        setattr(db_formula, key, value)
    
    db_formula.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_formula)
    return db_formula


@app.delete("/api/formulas/{formula_id}")
async def delete_formula(formula_id: int, db: Session = Depends(get_db)):
    """Delete formula (soft delete by setting is_active=False)"""
    db_formula = db.query(Formula).filter(Formula.id == formula_id).first()
    if not db_formula:
        raise HTTPException(status_code=404, detail="Formula not found")
    
    db_formula.is_active = False
    db.commit()
    return {"message": "Formula deactivated successfully"}


# Computed Metrics Endpoints
@app.get("/api/computed-metrics")
async def get_computed_metrics(
    raw_data_id: Optional[int] = None,
    formula_id: Optional[int] = None,
    metric_name: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get computed metrics with optional filters"""
    query = db.query(ComputedMetric)
    
    if raw_data_id:
        query = query.filter(ComputedMetric.raw_data_id == raw_data_id)
    if formula_id:
        query = query.filter(ComputedMetric.formula_id == formula_id)
    if metric_name:
        query = query.filter(ComputedMetric.metric_name == metric_name)
    
    results = query.limit(limit).all()
    return [
        {
            "id": r.id,
            "raw_data_id": r.raw_data_id,
            "formula_id": r.formula_id,
            "metric_name": r.metric_name,
            "metric_value": float(r.metric_value) if r.metric_value else None,
            "computed_at": r.computed_at
        }
        for r in results
    ]


@app.get("/api/aggregated-metrics")
async def get_aggregated_metrics(
    channel: Optional[str] = None,
    time_unit: Optional[str] = None,
    fetch_date: Optional[date] = None,
    metric_name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get aggregated metrics"""
    query = db.query(AggregatedMetric)
    
    if channel:
        query = query.filter(AggregatedMetric.channel == channel)
    if time_unit:
        query = query.filter(AggregatedMetric.time_unit == time_unit)
    if fetch_date:
        query = query.filter(AggregatedMetric.fetch_date == fetch_date)
    if metric_name:
        query = query.filter(AggregatedMetric.metric_name == metric_name)
    
    results = query.all()
    return [
        {
            "id": r.id,
            "channel": r.channel,
            "time_unit": r.time_unit,
            "fetch_date": r.fetch_date,
            "metric_name": r.metric_name,
            "metric_value": float(r.metric_value) if r.metric_value else None,
            "formula_id": r.formula_id,
            "computed_at": r.computed_at
        }
        for r in results
    ]


# Fetch Logs Endpoints
@app.get("/api/fetch-logs")
async def get_fetch_logs(
    fetch_date: Optional[date] = None,
    status: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get fetch logs (lịch sử fetch data)"""
    query = db.query(FetchLog)
    
    if fetch_date:
        query = query.filter(FetchLog.fetch_date == fetch_date)
    if status:
        query = query.filter(FetchLog.status == status)
    
    results = query.order_by(FetchLog.started_at.desc()).limit(limit).all()
    return [
        {
            "id": r.id,
            "fetch_date": r.fetch_date,
            "status": r.status,
            "records_fetched": r.records_fetched,
            "pages_fetched": r.pages_fetched,
            "error_message": r.error_message,
            "started_at": r.started_at,
            "completed_at": r.completed_at,
            "duration_seconds": r.duration_seconds
        }
        for r in results
    ]


# Trigger computation endpoint
@app.post("/api/compute/{formula_id}")
async def compute_metrics(formula_id: int, db: Session = Depends(get_db)):
    """Trigger computation for a specific formula"""
    try:
        from backend.formula_engine import FormulaEngine
    except ImportError:
        from formula_engine import FormulaEngine
    
    formula = db.query(Formula).filter(Formula.id == formula_id).first()
    if not formula:
        raise HTTPException(status_code=404, detail="Formula not found")
    
    engine = FormulaEngine(db)
    result = engine.compute_formula(formula_id)
    
    return {"message": "Computation triggered", "results": result}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
