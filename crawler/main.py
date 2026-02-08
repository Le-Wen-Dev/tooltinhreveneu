#!/usr/bin/env python3
"""
Crawler Service - Chạy độc lập, crawl data và lưu vào DB
"""

import sys
import os
from datetime import datetime, date, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scraper import RevenueShareScraper
from crawler.db import get_db_session, RawRevenueData, FetchLog
from crawler.lock import acquire_lock, release_lock
import logging

# Import FormulaEngine
try:
    from backend.formula_engine import FormulaEngine
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from backend.formula_engine import FormulaEngine

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/crawler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def parse_numeric_value(value: str) -> str:
    """Parse numeric value, keeping original format for storage"""
    if not value or value == '-':
        return None
    return value.replace(',', '') if ',' in value else value


def fetch_and_store(target_date: date = None, first_page_only: bool = False):
    """Fetch data and store in database"""
    if target_date is None:
        target_date = date.today() - timedelta(days=1)  # Yesterday by default
    
    db = next(get_db_session())
    
    # Acquire lock to prevent concurrent runs
    lock_acquired = acquire_lock(db, target_date)
    if not lock_acquired:
        logger.warning(f"Another crawler is already running for {target_date}. Exiting.")
        return {"status": "skipped", "reason": "lock_acquired"}
    
    try:
        fetch_log = FetchLog(
            fetch_date=target_date,
            status='started',
            started_at=datetime.utcnow()
        )
        db.add(fetch_log)
        db.commit()
        fetch_log_id = fetch_log.id
        
        logger.info(f"Starting fetch for date: {target_date}")
        
        # Initialize scraper
        scraper = RevenueShareScraper(
            username=os.getenv("SCRAPER_USERNAME", "maxvaluemedia"),
            password=os.getenv("SCRAPER_PASSWORD", "gliacloud")
        )
        
        # Login
        if not scraper.login():
            fetch_log.status = 'failed'
            fetch_log.error_message = "Login failed"
            fetch_log.completed_at = datetime.utcnow()
            db.commit()
            logger.error("Login failed")
            return {"status": "failed", "error": "Login failed"}
        
        # Build URL
        date_str = target_date.strftime("%Y-%m-%d")
        url = f"https://gstudio.gliacloud.com/ad-sharing/publisher/revenueshare/?channel=No+Filter&time_unit_date__range__gte={date_str}&time_unit_date__range__lte={date_str}"
        
        # Fetch data
        logger.info(f"Fetching data from: {url}")
        if first_page_only:
            data = scraper.scrape_table_first_page_only(url)
        else:
            data = scraper.scrape_table(url)
        
        if not data:
            fetch_log.status = 'failed'
            fetch_log.error_message = "No data fetched"
            fetch_log.completed_at = datetime.utcnow()
            db.commit()
            logger.error("No data fetched")
            return {"status": "failed", "error": "No data fetched"}
        
        logger.info(f"Fetched {len(data)} records")
        
        # Store data (update existing or create new)
        records_created = 0
        records_updated = 0
        
        for row_data in data:
            # Check if record already exists
            existing = db.query(RawRevenueData).filter(
                RawRevenueData.channel == row_data.get('channel', ''),
                RawRevenueData.slot == row_data.get('slot', ''),
                RawRevenueData.time_unit == row_data.get('time unit', ''),
                RawRevenueData.fetch_date == target_date
            ).first()
            
            if existing:
                # Update existing record (ghi đè)
                existing.total_player_impr = row_data.get('total player impr', '')
                existing.total_ad_impr = row_data.get('total ad impr', '')
                existing.rpm = row_data.get('rpm', '')
                existing.gross_revenue_usd = row_data.get('gross revenue (usd)', '')
                existing.net_revenue_usd = row_data.get('net revenue (usd)', '')
                existing.fetched_at = datetime.utcnow()
                records_updated += 1
            else:
                # Create new record
                db_row = RawRevenueData(
                    channel=row_data.get('channel', ''),
                    slot=row_data.get('slot', ''),
                    time_unit=row_data.get('time unit', ''),
                    total_player_impr=row_data.get('total player impr', ''),
                    total_ad_impr=row_data.get('total ad impr', ''),
                    rpm=row_data.get('rpm', ''),
                    gross_revenue_usd=row_data.get('gross revenue (usd)', ''),
                    net_revenue_usd=row_data.get('net revenue (usd)', ''),
                    fetch_date=target_date
                )
                db.add(db_row)
                records_created += 1
        
        db.commit()
        logger.info(f"Stored: {records_created} created, {records_updated} updated")
        
        # Compute formulas
        logger.info("Computing formulas...")
        engine = FormulaEngine(db)
        engine.compute_all_formulas(compute_for_date=target_date)
        logger.info("Formulas computed successfully")
        
        # Process revenue data (tổng hợp desktop + mobile → processed_revenue_data for dashboard)
        try:
            from crawler.process_revenue import process_revenue_data
            process_revenue_data(db, target_date)
            db.commit()
            logger.info("Processed revenue data updated for dashboard.")
        except Exception as e:
            logger.warning("process_revenue_data failed (dashboard may not update): %s", e)
        
        # Update fetch log
        fetch_log = db.query(FetchLog).filter(FetchLog.id == fetch_log_id).first()
        fetch_log.status = 'success'
        fetch_log.records_fetched = records_created + records_updated
        fetch_log.records_created = records_created
        fetch_log.records_updated = records_updated
        fetch_log.pages_fetched = 1 if first_page_only else len(data) // 100
        fetch_log.completed_at = datetime.utcnow()
        fetch_log.duration_seconds = int((fetch_log.completed_at - fetch_log.started_at).total_seconds())
        db.commit()
        
        logger.info(f"Fetch completed successfully in {fetch_log.duration_seconds}s")
        
        return {
            "status": "success",
            "records_created": records_created,
            "records_updated": records_updated,
            "total_records": records_created + records_updated,
            "fetch_date": target_date.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error during fetch: {str(e)}", exc_info=True)
        fetch_log = db.query(FetchLog).filter(FetchLog.id == fetch_log_id).first()
        if fetch_log:
            fetch_log.status = 'failed'
            fetch_log.error_message = str(e)
            fetch_log.completed_at = datetime.utcnow()
            db.commit()
        return {"status": "failed", "error": str(e)}
    finally:
        # Release lock
        release_lock(db, target_date)
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Revenue Data Crawler")
    parser.add_argument("--date", type=str, help="Date to fetch (YYYY-MM-DD), defaults to yesterday")
    parser.add_argument("--first-page-only", action="store_true", help="Fetch only first page")
    
    args = parser.parse_args()
    
    target_date = None
    if args.date:
        target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    
    result = fetch_and_store(target_date, args.first_page_only)
    print(result)
    sys.exit(0 if result.get("status") == "success" else 1)
