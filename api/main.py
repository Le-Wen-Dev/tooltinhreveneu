"""
API Service - FastAPI để query metrics
"""

from fastapi import FastAPI, HTTPException, Depends, Query, Request, Form, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
import secrets
from starlette.middleware.sessions import SessionMiddleware

from crawler.db import (
    get_db_session,
    RawRevenueData,
    ComputedMetric,
    AggregatedMetric,
    FetchLog,
    Formula,
    User,
)

# Import processed data model
try:
    from backend.data_processor import ProcessedRevenueData
except ImportError:
    # Create model inline if import fails
    from sqlalchemy import Column, Integer, String, Numeric, DateTime, Date
    from sqlalchemy.ext.declarative import declarative_base
    
    Base = declarative_base()
    
    class ProcessedRevenueData(Base):
        __tablename__ = "processed_revenue_data"
        
        id = Column(Integer, primary_key=True, index=True)
        slot = Column(String(255), nullable=False)
        time_unit = Column(String(50), nullable=False)
        total_player_impr = Column(Numeric(20, 2))
        revenue = Column(Numeric(20, 2))
        rpm = Column(Numeric(10, 2))
        share = Column(Numeric(5, 2))
        total_player_impr_2 = Column(Numeric(20, 2))
        revenue_2 = Column(Numeric(20, 2))
        rpm_2 = Column(Numeric(10, 2))
        fetch_date = Column(Date, nullable=False)
        processed_at = Column(DateTime)
from sqlalchemy import text
from sqlalchemy.exc import OperationalError, ProgrammingError
import os
import html
import threading
from datetime import date as date_type, datetime
from pydantic import BaseModel

app = FastAPI(
    title="Revenue Share Data API",
    description="API for querying revenue share metrics",
    version="1.0.0"
)

# Global variable to track crawl status
crawl_status = {
    "running": False,
    "last_run": None,
    "last_result": None
}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production-use-env")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Base URL for API Docs / links (from env, no trailing slash)
BASE_URL = os.getenv("BASE_URL", "https://beta.gliacloud.online").rstrip("/")
API_DOCS_URL = BASE_URL + "/api-docs"


def _parse_optional_date(s) -> Optional[date]:
    """Parse query param to date; empty string or invalid -> None."""
    if s is None or (isinstance(s, str) and not s.strip()):
        return None
    if isinstance(s, date):
        return s
    try:
        return datetime.strptime(str(s).strip()[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


# Dependency
def get_db():
    db = next(get_db_session())
    try:
        yield db
    finally:
        db.close()


# Auth helpers
from passlib.context import CryptContext
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

def _password_72(password: str) -> str:
    """Bcrypt chỉ chấp nhận tối đa 72 byte; cắt bớt nếu dài hơn."""
    raw = password.encode("utf-8")
    if len(raw) <= 72:
        return password
    return raw[:72].decode("utf-8", errors="replace")

def hash_password(password: str) -> str:
    return pwd_ctx.hash(_password_72(password))

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(_password_72(plain), hashed)

def generate_api_key() -> str:
    return secrets.token_urlsafe(32)

def get_current_user(request: Request, db: Session = Depends(get_db)):
    """Require login; return user or redirect to login."""
    user_id = request.session.get("user_id")
    if not user_id:
        if request.url.path.startswith("/api/"):
            raise HTTPException(status_code=401, detail="Not authenticated")
        return RedirectResponse(url="/login", status_code=302)
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        request.session.clear()
        if request.url.path.startswith("/api/"):
            raise HTTPException(status_code=401, detail="Invalid session")
        return RedirectResponse(url="/login", status_code=302)
    return user

def require_admin(request: Request, user: User = Depends(get_current_user)):
    if not isinstance(user, User):
        return user  # redirect response
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return user

def require_can_view_data(request: Request, user: User = Depends(get_current_user)):
    if not isinstance(user, User):
        return user
    if user.role != "admin" and not user.can_view_data:
        request.session.clear()
        return RedirectResponse(url="/login", status_code=302)
    return user

def get_user_for_api(
    request: Request,
    x_api_key: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """Resolve user from session (web) or X-API-Key header (API)."""
    user_id = request.session.get("user_id")
    if user_id:
        user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
        if user and (user.role == "admin" or user.can_view_data):
            return user
    if x_api_key:
        user = db.query(User).filter(User.api_key == x_api_key, User.is_active == True).first()
        if user and (user.role == "admin" or user.can_view_data):
            return user
    return None


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Trang chủ (view) – từ đây vào Login, Admin, API Docs."""
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception:
        # Fallback: trả HTML trực tiếp nếu template lỗi
        return HTMLResponse("""
        <!DOCTYPE html>
        <html><head><meta charset="UTF-8"><title>Revenue Share Data</title></head>
        <body style="font-family:sans-serif;max-width:400px;margin:80px auto;padding:24px;text-align:center;">
        <h1>Revenue Share Data</h1>
        <p><a href="/login" style="display:block;margin:12px 0;padding:12px;background:#10b981;color:white;text-decoration:none;border-radius:8px;">Đăng nhập</a></p>
        <p><a href="/register" style="display:block;margin:12px 0;padding:12px;background:#e5e7eb;color:#1f2937;text-decoration:none;border-radius:8px;">Đăng ký</a></p>
        <p><a href="/login" style="display:block;margin:12px 0;padding:12px;border:1px solid #10b981;color:#10b981;text-decoration:none;border-radius:8px;">Đăng nhập</a></p>
        <p><a href="/health" style="font-size:14px;color:#9ca3af;">Health (API)</a></p>
        </body></html>
        """)


@app.get("/setup", response_class=HTMLResponse)
async def setup_page(request: Request, db: Session = Depends(get_db)):
    """One-time setup: create first admin when no users exist."""
    try:
        if db.query(User).count() > 0:
            return RedirectResponse(url="/login", status_code=302)
    except (OperationalError, ProgrammingError):
        return _users_table_missing_error()
    return templates.TemplateResponse("setup.html", {"request": request})

def _setup_error_html(err_msg) -> str:
    """Escape and render setup error so browser always shows it (no 500 replacement)."""
    try:
        safe = html.escape(str(err_msg))
    except Exception:
        safe = html.escape(repr(err_msg))
    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Setup error</title></head>
<body style="font-family:sans-serif;max-width:560px;margin:60px auto;padding:24px;">
<h1>Setup lỗi</h1>
<p><strong>Chi tiết:</strong> <code style="background:#f0f0f0;padding:4px;word-break:break-all;">{safe}</code></p>
<p><a href="/setup">Thử lại /setup</a> | <a href="/login">Login</a></p>
</body></html>"""


@app.exception_handler(Exception)
async def _catch_setup_errors(request: Request, exc: Exception):
    """Bắt mọi lỗi khi POST /setup (kể cả lỗi từ get_db/Form) để hiển thị Chi tiết thay vì Internal Server Error."""
    if request.url.path == "/setup" and request.method == "POST":
        return HTMLResponse(_setup_error_html(exc), status_code=200)
    raise exc


@app.post("/setup")
async def setup_submit(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        try:
            if db.query(User).count() > 0:
                return RedirectResponse(url="/login", status_code=302)
            if db.query(User).filter(User.username == username.strip()).first():
                return templates.TemplateResponse("setup.html", {"request": request, "error": "Username already exists"})
            if db.query(User).filter(User.email == email.strip()).first():
                return templates.TemplateResponse("setup.html", {"request": request, "error": "Email already registered"})
        except (OperationalError, ProgrammingError):
            return _users_table_missing_error()

        admin = User(
            username=username.strip(),
            email=email.strip(),
            password_hash=hash_password(password),
            role="admin",
            can_view_data=True,
            api_key=generate_api_key(),
        )
        db.add(admin)
        db.commit()
        return RedirectResponse(url="/login", status_code=303)
    except Exception as e:
        try:
            db.rollback()
        except Exception:
            pass
        return HTMLResponse(_setup_error_html(str(e)), status_code=200)


@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except:
        return {"status": "unhealthy", "database": "disconnected"}


@app.get("/api/computed-metrics")
async def get_computed_metrics(
    raw_data_id: Optional[int] = Query(None),
    formula_id: Optional[int] = Query(None),
    metric_name: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db)
):
    """Get computed metrics (row-level)"""
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
            "computed_at": r.computed_at.isoformat() if r.computed_at else None
        }
        for r in results
    ]


@app.get("/api/aggregated-metrics")
async def get_aggregated_metrics(
    channel: Optional[str] = Query(None),
    time_unit: Optional[str] = Query(None),
    fetch_date: Optional[date] = Query(None),
    metric_name: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
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
    
    results = query.order_by(AggregatedMetric.fetch_date.desc()).limit(limit).all()
    return [
        {
            "id": r.id,
            "channel": r.channel,
            "time_unit": r.time_unit,
            "fetch_date": r.fetch_date.isoformat() if r.fetch_date else None,
            "metric_name": r.metric_name,
            "metric_value": float(r.metric_value) if r.metric_value else None,
            "formula_id": r.formula_id,
            "computed_at": r.computed_at.isoformat() if r.computed_at else None
        }
        for r in results
    ]


def require_api_user(user: Optional[User] = Depends(get_user_for_api)):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required: log in or provide X-API-Key header")
    return user


def require_api_admin(user: Optional[User] = Depends(get_user_for_api)):
    """Chỉ admin mới được gọi (session hoặc API key của user admin)."""
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required: log in or provide X-API-Key header")
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only. Use GET /api/data for data access.")
    return user


@app.get("/api/raw-data")
async def get_raw_data(
    fetch_date: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None, description="Filter from date (inclusive)"),
    to_date: Optional[str] = Query(None, description="Filter to date (inclusive)"),
    channel: Optional[str] = Query(None),
    limit: int = Query(100, le=2000),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    user: User = Depends(require_api_admin),
):
    """Raw revenue data. Admin only. Third parties use GET /api/data."""
    fd = _parse_optional_date(fetch_date)
    from_d = _parse_optional_date(from_date)
    to_d = _parse_optional_date(to_date)
    query = db.query(RawRevenueData)
    
    if fd:
        query = query.filter(RawRevenueData.fetch_date == fd)
    else:
        if from_d:
            query = query.filter(RawRevenueData.fetch_date >= from_d)
        if to_d:
            query = query.filter(RawRevenueData.fetch_date <= to_d)
    if channel:
        query = query.filter(RawRevenueData.channel == channel)
    
    results = query.order_by(RawRevenueData.fetch_date.desc()).offset(offset).limit(limit).all()
    return [
        {
            "id": r.id,
            "channel": r.channel,
            "slot": r.slot,
            "time_unit": r.time_unit,
            "total_player_impr": r.total_player_impr,
            "total_ad_impr": r.total_ad_impr,
            "rpm": r.rpm,
            "gross_revenue_usd": r.gross_revenue_usd,
            "net_revenue_usd": r.net_revenue_usd,
            "fetch_date": r.fetch_date.isoformat() if r.fetch_date else None,
            "fetched_at": r.fetched_at.isoformat() if r.fetched_at else None
        }
        for r in results
    ]


@app.get("/api/fetch-logs")
async def get_fetch_logs(
    fetch_date: Optional[date] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db)
):
    """Get fetch logs (lịch sử fetch)"""
    query = db.query(FetchLog)
    
    if fetch_date:
        query = query.filter(FetchLog.fetch_date == fetch_date)
    if status:
        query = query.filter(FetchLog.status == status)
    
    results = query.order_by(FetchLog.started_at.desc()).limit(limit).all()
    return [
        {
            "id": r.id,
            "fetch_date": r.fetch_date.isoformat() if r.fetch_date else None,
            "status": r.status,
            "records_fetched": r.records_fetched,
            "records_created": r.records_created,
            "records_updated": r.records_updated,
            "pages_fetched": r.pages_fetched,
            "error_message": r.error_message,
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            "duration_seconds": r.duration_seconds
        }
        for r in results
    ]


@app.get("/api/formulas")
async def get_formulas(
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """Get all formulas"""
    query = db.query(Formula)
    if is_active is not None:
        query = query.filter(Formula.is_active == is_active)
    
    results = query.all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "description": r.description,
            "formula_expression": r.formula_expression,
            "formula_type": r.formula_type,
            "is_active": r.is_active,
            "created_at": r.created_at.isoformat() if r.created_at else None
        }
        for r in results
    ]


@app.get("/api/data")
async def get_processed_data(
    fetch_date: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None, description="Filter from date (inclusive)"),
    to_date: Optional[str] = Query(None, description="Filter to date (inclusive)"),
    slot: Optional[str] = Query(None),
    limit: int = Query(100, le=2000),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    user: User = Depends(require_api_user),
):
    """Get processed revenue data. Use from_date/to_date for date range, or fetch_date for single day. Auth: session or X-API-Key."""
    fd = _parse_optional_date(fetch_date)
    from_d = _parse_optional_date(from_date)
    to_d = _parse_optional_date(to_date)
    if ProcessedRevenueData is None:
        raise HTTPException(status_code=503, detail="Processed data model not available")
    
    query = db.query(ProcessedRevenueData)
    
    if fd:
        query = query.filter(ProcessedRevenueData.fetch_date == fd)
    else:
        if from_d:
            query = query.filter(ProcessedRevenueData.fetch_date >= from_d)
        if to_d:
            query = query.filter(ProcessedRevenueData.fetch_date <= to_d)
    if slot:
        query = query.filter(ProcessedRevenueData.slot == slot)
    
    results = query.order_by(ProcessedRevenueData.fetch_date.desc(), ProcessedRevenueData.slot).offset(offset).limit(limit).all()
    is_admin = getattr(user, "role", None) == "admin"

    out = []
    for r in results:
        if is_admin:
            out.append({
                "id": r.id,
                "slot": r.slot,
                "time_unit": r.time_unit,
                "total_player_impr": float(r.total_player_impr) if r.total_player_impr else None,
                "revenue": float(r.revenue) if r.revenue else None,
                "rpm": float(r.rpm) if r.rpm else None,
                "total_player_impr_2": float(r.total_player_impr_2) if r.total_player_impr_2 else None,
                "revenue_2": float(r.revenue_2) if r.revenue_2 else None,
                "rpm_2": float(r.rpm_2) if r.rpm_2 else None,
                "fetch_date": r.fetch_date.isoformat() if r.fetch_date else None
            })
        else:
            # User role: same as table view — IMPR 2 → IMPR, Revenue 2 → Revenue, RPM 2 → RPM; time_unit = fetch_date; no _2 or fetch_date
            out.append({
                "id": r.id,
                "slot": r.slot,
                "time_unit": r.fetch_date.isoformat() if r.fetch_date else (r.time_unit or None),
                "total_player_impr": float(r.total_player_impr_2) if r.total_player_impr_2 else None,
                "revenue": float(r.revenue_2) if r.revenue_2 else None,
                "rpm": float(r.rpm_2) if r.rpm_2 else None
            })
    return out


class TriggerCrawlRequest(BaseModel):
    date: Optional[date_type] = None
    first_page_only: bool = False


@app.post("/api/trigger-crawl")
async def trigger_crawl(
    request: Optional[TriggerCrawlRequest] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Trigger crawler manually (admin only)"""
    if not isinstance(user, User):
        return user
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    global crawl_status
    
    if crawl_status["running"]:
        return {
            "status": "error",
            "message": "Crawler is already running",
            "last_run": crawl_status["last_run"]
        }
    
    def run_crawler(req: Optional[TriggerCrawlRequest]):
        global crawl_status
        try:
            crawl_status["running"] = True
            crawl_status["last_run"] = datetime.now().isoformat()
            
            # Import data fetcher
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).parent.parent))
            
            from backend.data_fetcher import DataFetcher
            from datetime import date, timedelta
            
            target_date = req.date if req and req.date else date.today() - timedelta(days=1)
            first_page_only = req.first_page_only if req else False
            
            # Use DataFetcher instead of crawler.main
            fetcher = DataFetcher()
            result = fetcher.fetch_and_store(target_date=target_date, first_page_only=first_page_only)
            crawl_status["last_result"] = result
            crawl_status["running"] = False
            
        except Exception as e:
            crawl_status["running"] = False
            crawl_status["last_result"] = {"status": "error", "error": str(e)}
    
    # Run in background thread
    thread = threading.Thread(target=run_crawler, args=(request,), daemon=True)
    thread.start()
    
    return {
        "status": "started",
        "message": "Crawler started in background",
        "target_date": (request.date.isoformat() if request and request.date else None),
        "first_page_only": (request.first_page_only if request else False)
    }


@app.get("/api/crawl-status")
async def get_crawl_status():
    """Get current crawl status"""
    return crawl_status


# Templates
try:
    from starlette.templating import Jinja2Templates
except ImportError:
    from fastapi.templating import Jinja2Templates
template_dir = "backend/templates"
if not os.path.exists(template_dir):
    template_dir = "/app/backend/templates"
templates = Jinja2Templates(directory=template_dir)


def _users_table_missing_error() -> HTMLResponse:
    """Trả trang hướng dẫn khi bảng users chưa tồn tại."""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html><head><meta charset="UTF-8"><title>Database setup</title></head>
    <body style="font-family:sans-serif;max-width:560px;margin:60px auto;padding:24px;">
    <h1>Bảng <code>users</code> chưa tồn tại</h1>
    <p>Chạy migration để tạo bảng users (auth). Trên VPS dùng <code>docker-compose</code> (có gạch ngang):</p>
    <pre style="background:#f0f0f0;padding:12px;border-radius:8px;overflow:auto;">
docker-compose -f docker-compose.vps.yml exec -T db mysql -u tooltinhreveneu_1 -p'MẬT_KHẨU_DB' tooltinhreveneu_1 &lt; migrations_add_users_table.sql
</pre>
    <p>Sau đó seed user: <code>... &lt; seed_users.sql</code></p>
    <p>Hoặc nếu chạy local (không Docker):</p>
    <pre style="background:#f0f0f0;padding:12px;border-radius:8px;">mysql -u tooltinhreveneu_1 -p tooltinhreveneu_1 &lt; migrations_add_users_table.sql</pre>
    <p><a href="/login">Thử lại /login</a></p>
    </body></html>
    """, status_code=503)


# ----- Auth: login, register, logout -----
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, db: Session = Depends(get_db)):
    if request.session.get("user_id"):
        return RedirectResponse(url="/data", status_code=302)
    try:
        if db.query(User).count() == 0:
            return RedirectResponse(url="/setup", status_code=302)
    except (OperationalError, ProgrammingError):
        return _users_table_missing_error()
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        user = db.query(User).filter(User.username == username, User.is_active == True).first()
    except (OperationalError, ProgrammingError):
        return _users_table_missing_error()
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid username or password"})
    request.session["user_id"] = user.id
    user.last_login = datetime.utcnow()
    db.commit()
    if user.role == "admin":
        return RedirectResponse(url="/data", status_code=303)
    return RedirectResponse(url="/data", status_code=303)

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=302)

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, db: Session = Depends(get_db)):
    if request.session.get("user_id"):
        return RedirectResponse(url="/data", status_code=302)
    try:
        db.query(User).count()  # check table exists
    except (OperationalError, ProgrammingError):
        return _users_table_missing_error()
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
async def register_submit(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        if db.query(User).filter(User.username == username).first():
            return templates.TemplateResponse("register.html", {"request": request, "error": "Username already exists"})
        if db.query(User).filter(User.email == email).first():
            return templates.TemplateResponse("register.html", {"request": request, "error": "Email already registered"})
    except (OperationalError, ProgrammingError):
        return _users_table_missing_error()
    user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
        role="user",
        can_view_data=False,
    )
    db.add(user)
    db.commit()
    return RedirectResponse(url="/login", status_code=303)


@app.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not isinstance(user, User):
        return user
    if user.role != "admin":
        return RedirectResponse(url="/data", status_code=302)
    """Admin dashboard"""
    formulas = db.query(Formula).all()
    return templates.TemplateResponse("admin_dashboard.html", {
        "request": request,
        "formulas": formulas,
        "user": user,
    })


@app.get("/admin", response_class=HTMLResponse)
async def admin_redirect(request: Request):
    """Backward compat: /admin -> /dashboard"""
    return RedirectResponse(url="/dashboard", status_code=302)


@app.get("/formulas", response_class=HTMLResponse)
async def list_formulas(request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not isinstance(user, User):
        return user
    """List all formulas"""
    formulas = db.query(Formula).order_by(Formula.created_at.desc()).all()
    return templates.TemplateResponse("formulas_list.html", {
        "request": request,
        "formulas": formulas,
        "user": user,
    })

@app.get("/formulas/new", response_class=HTMLResponse)
async def new_formula_form(request: Request, user: User = Depends(get_current_user)):
    if not isinstance(user, User):
        return user
    """New formula form"""
    return templates.TemplateResponse("formula_form.html", {
        "request": request,
        "formula": None,
        "formula_types": ["rpm", "revenue", "custom", "irpm"],
        "user": user,
    })

@app.get("/formulas/{formula_id}/edit", response_class=HTMLResponse)
async def edit_formula_form(request: Request, formula_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not isinstance(user, User):
        return user
    """Edit formula form"""
    formula = db.query(Formula).filter(Formula.id == formula_id).first()
    if not formula:
        raise HTTPException(status_code=404, detail="Formula not found")
    
    return templates.TemplateResponse("formula_form.html", {
        "request": request,
        "formula": formula,
        "formula_types": ["rpm", "revenue", "custom", "irpm"],
        "user": user,
    })

@app.post("/formulas")
async def create_formula(
    request: Request,
    name: str = Form(...),
    description: Optional[str] = Form(None),
    formula_expression: str = Form(...),
    formula_type: str = Form(...),
    is_active: bool = Form(True),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not isinstance(user, User):
        return user
    """Create new formula"""
    formula = Formula(
        name=name,
        description=description,
        formula_expression=formula_expression,
        formula_type=formula_type,
        is_active=is_active
    )
    db.add(formula)
    db.commit()
    db.refresh(formula)
    
    return RedirectResponse(url="/formulas", status_code=303)

@app.post("/formulas/{formula_id}")
async def update_formula(
    request: Request,
    formula_id: int,
    name: str = Form(...),
    description: Optional[str] = Form(None),
    formula_expression: str = Form(...),
    formula_type: str = Form(...),
    is_active: bool = Form(True),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not isinstance(user, User):
        return user
    """Update existing formula"""
    formula = db.query(Formula).filter(Formula.id == formula_id).first()
    if not formula:
        raise HTTPException(status_code=404, detail="Formula not found")
    
    formula.name = name
    formula.description = description
    formula.formula_expression = formula_expression
    formula.formula_type = formula_type
    formula.is_active = is_active
    formula.updated_at = datetime.utcnow()
    
    db.commit()
    
    return RedirectResponse(url="/formulas", status_code=303)

@app.post("/formulas/{formula_id}/compute")
async def compute_formula_endpoint(
    request: Request,
    formula_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not isinstance(user, User):
        return user
    """Trigger computation for a formula"""
    from backend.formula_engine import FormulaEngine
    engine = FormulaEngine(db)
    result = engine.compute_formula(formula_id)
    
    return RedirectResponse(
        url=f"/formulas?computed={formula_id}",
        status_code=303
    )

@app.post("/formulas/{formula_id}/delete")
async def delete_formula_endpoint(
    request: Request,
    formula_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not isinstance(user, User):
        return user
    """Delete (deactivate) formula"""
    formula = db.query(Formula).filter(Formula.id == formula_id).first()
    if not formula:
        raise HTTPException(status_code=404, detail="Formula not found")
    
    formula.is_active = False
    db.commit()
    
    return RedirectResponse(url="/formulas", status_code=303)


# ----- Users CRUD (admin only) -----
@app.get("/users", response_class=HTMLResponse)
async def list_users(request: Request, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    if not isinstance(user, User):
        return user
    users = db.query(User).order_by(User.created_at.desc()).all()
    return templates.TemplateResponse("users_list.html", {"request": request, "users": users, "user": user})

@app.get("/users/new", response_class=HTMLResponse)
async def new_user_form(request: Request, user: User = Depends(require_admin)):
    if not isinstance(user, User):
        return user
    return templates.TemplateResponse("user_form.html", {"request": request, "edit_user": None})

@app.post("/users")
async def create_user(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form("user"),
    can_view_data: bool = Form(False),
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    if not isinstance(user, User):
        return user
    if db.query(User).filter(User.username == username).first():
        return templates.TemplateResponse("user_form.html", {"request": request, "edit_user": None, "error": "Username already exists"})
    if db.query(User).filter(User.email == email).first():
        return templates.TemplateResponse("user_form.html", {"request": request, "edit_user": None, "error": "Email already registered"})
    new_user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
        role=role,
        can_view_data=can_view_data,
        api_key=generate_api_key() if can_view_data else None,
    )
    db.add(new_user)
    db.commit()
    return RedirectResponse(url="/users", status_code=303)

@app.get("/users/{user_id}/edit", response_class=HTMLResponse)
async def edit_user_form(request: Request, user_id: int, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    if not isinstance(user, User):
        return user
    edit_user = db.query(User).filter(User.id == user_id).first()
    if not edit_user:
        raise HTTPException(status_code=404, detail="User not found")
    return templates.TemplateResponse("user_form.html", {"request": request, "edit_user": edit_user})

@app.post("/users/{user_id}")
async def update_user(
    request: Request,
    user_id: int,
    username: str = Form(...),
    email: str = Form(...),
    role: str = Form("user"),
    can_view_data: bool = Form(False),
    password: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    if not isinstance(user, User):
        return user
    edit_user = db.query(User).filter(User.id == user_id).first()
    if not edit_user:
        raise HTTPException(status_code=404, detail="User not found")
    other = db.query(User).filter(User.username == username, User.id != user_id).first()
    if other:
        return templates.TemplateResponse("user_form.html", {"request": request, "edit_user": edit_user, "error": "Username already exists"})
    other = db.query(User).filter(User.email == email, User.id != user_id).first()
    if other:
        return templates.TemplateResponse("user_form.html", {"request": request, "edit_user": edit_user, "error": "Email already registered"})
    edit_user.username = username
    edit_user.email = email
    edit_user.role = role
    edit_user.can_view_data = can_view_data
    if password:
        edit_user.password_hash = hash_password(password)
    if can_view_data and not edit_user.api_key:
        edit_user.api_key = generate_api_key()
    elif not can_view_data:
        edit_user.api_key = None
    db.commit()
    return RedirectResponse(url="/users", status_code=303)

@app.post("/users/{user_id}/delete")
async def delete_user(request: Request, user_id: int, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    if not isinstance(user, User):
        return user
    edit_user = db.query(User).filter(User.id == user_id).first()
    if not edit_user:
        raise HTTPException(status_code=404, detail="User not found")
    edit_user.is_active = False
    db.commit()
    return RedirectResponse(url="/users", status_code=303)


@app.get("/api-docs", response_class=HTMLResponse)
async def api_docs_page(request: Request, user: User = Depends(require_can_view_data)):
    if not isinstance(user, User):
        return user
    return templates.TemplateResponse("api_docs.html", {"request": request, "user": user, "base_url": BASE_URL, "api_docs_url": API_DOCS_URL})


@app.get("/admin/api-docs", response_class=HTMLResponse)
async def api_docs_redirect(request: Request):
    """Backward compat: /admin/api-docs -> /api-docs"""
    return RedirectResponse(url="/api-docs", status_code=302)


@app.get("/admin/data", response_class=HTMLResponse)
async def admin_data_redirect(
    request: Request,
    fetch_date: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    channel: Optional[str] = Query(None),
    slot: Optional[str] = Query(None),
    view_type: Optional[str] = Query(None),
):
    """Redirect /admin/data to /data (canonical URL without admin)."""
    params = []
    if view_type == "processed":
        params.append("view_type=datafull")
    elif view_type:
        params.append(f"view_type={view_type}")
    if fetch_date:
        params.append(f"fetch_date={fetch_date}")
    if from_date:
        params.append(f"from_date={from_date}")
    if to_date:
        params.append(f"to_date={to_date}")
    if channel:
        params.append(f"channel={channel}")
    if slot:
        params.append(f"slot={slot}")
    q = "&".join(params) if params else ""
    return RedirectResponse(url=f"/data?{q}" if q else "/data", status_code=302)


PAGE_SIZE = 5

@app.get("/data", response_class=HTMLResponse)
async def view_data(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_can_view_data),
    fetch_date: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    channel: Optional[str] = Query(None),
    slot: Optional[str] = Query(None),
    view_type: str = Query("datafull", regex="^(raw|datafull)$"),
    page: int = Query(1, ge=1),
):
    """View data in table format - datafull (default) or raw. Raw chỉ admin; user xem datafull."""
    if view_type == "raw" and (not user or getattr(user, "role", None) != "admin"):
        q = "view_type=datafull"
        if from_date:
            q += f"&from_date={from_date}"
        if to_date:
            q += f"&to_date={to_date}"
        if fetch_date:
            q += f"&fetch_date={fetch_date}"
        if channel:
            q += f"&channel={channel}"
        if slot:
            q += f"&slot={slot}"
        return RedirectResponse(url=f"/data?{q}", status_code=302)

    fd = _parse_optional_date(fetch_date)
    from_d = _parse_optional_date(from_date)
    to_d = _parse_optional_date(to_date)

    if view_type == "datafull" and ProcessedRevenueData:
        query = db.query(ProcessedRevenueData)
        
        if fd:
            query = query.filter(ProcessedRevenueData.fetch_date == fd)
        else:
            if from_d:
                query = query.filter(ProcessedRevenueData.fetch_date >= from_d)
            if to_d:
                query = query.filter(ProcessedRevenueData.fetch_date <= to_d)
        if slot:
            query = query.filter(ProcessedRevenueData.slot == slot)
        
        total_count = query.count()
        total_pages = max(1, (total_count + PAGE_SIZE - 1) // PAGE_SIZE)
        page = min(page, total_pages)
        offset = (page - 1) * PAGE_SIZE
        data = query.order_by(ProcessedRevenueData.fetch_date.desc(), ProcessedRevenueData.slot).offset(offset).limit(PAGE_SIZE).all()
        available_dates = db.query(ProcessedRevenueData.fetch_date).distinct().order_by(ProcessedRevenueData.fetch_date.desc()).limit(365).all()
        available_dates = [d[0] for d in available_dates]
        available_slots = db.query(ProcessedRevenueData.slot).distinct().order_by(ProcessedRevenueData.slot).all()
        available_slots = [s[0] for s in available_slots]
        
        return templates.TemplateResponse("processed_data_table.html", {
            "request": request,
            "data": data,
            "available_dates": available_dates,
            "available_slots": available_slots,
            "current_date": fd,
            "from_date": from_d,
            "to_date": to_d,
            "current_slot": slot,
            "view_type": "datafull",
            "user": user,
            "page": page,
            "total_pages": total_pages,
            "total_count": total_count,
            "page_size": PAGE_SIZE,
            "base_url": BASE_URL,
            "api_docs_url": API_DOCS_URL,
        })
    else:
        query = db.query(RawRevenueData)
        
        if fd:
            query = query.filter(RawRevenueData.fetch_date == fd)
        else:
            if from_d:
                query = query.filter(RawRevenueData.fetch_date >= from_d)
            if to_d:
                query = query.filter(RawRevenueData.fetch_date <= to_d)
        if channel:
            query = query.filter(RawRevenueData.channel == channel)
        if slot:
            query = query.filter(RawRevenueData.slot == slot)
        
        total_count = query.count()
        total_pages = max(1, (total_count + PAGE_SIZE - 1) // PAGE_SIZE)
        page = min(page, total_pages)
        offset = (page - 1) * PAGE_SIZE
        data = query.order_by(RawRevenueData.fetch_date.desc(), RawRevenueData.channel, RawRevenueData.slot).offset(offset).limit(PAGE_SIZE).all()
        available_dates = db.query(RawRevenueData.fetch_date).distinct().order_by(RawRevenueData.fetch_date.desc()).limit(365).all()
        available_dates = [d[0] for d in available_dates]
        available_slots_raw = db.query(RawRevenueData.slot).distinct().order_by(RawRevenueData.slot).all()
        available_slots_raw = [s[0] for s in available_slots_raw]
        
        return templates.TemplateResponse("data_table.html", {
            "request": request,
            "data": data,
            "available_dates": available_dates,
            "available_slots": available_slots_raw,
            "current_date": fd,
            "from_date": from_d,
            "to_date": to_d,
            "current_channel": channel,
            "current_slot": slot,
            "base_url": BASE_URL,
            "api_docs_url": API_DOCS_URL,
            "view_type": "raw",
            "user": user,
            "page": page,
            "total_pages": total_pages,
            "total_count": total_count,
            "page_size": PAGE_SIZE,
        })

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("API_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
