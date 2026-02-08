"""
Data Fetcher Service
Handles scheduled fetching of revenue data
"""

import sys
import os
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import List, Dict
# schedule and time only needed for scheduled runs, not for manual fetch
# Make them optional to avoid import errors
try:
    import schedule
    import time
except ImportError:
    schedule = None
    time = None

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper import RevenueShareScraper
try:
    from backend.app import RawRevenueData, FetchLog, Base, engine
    from backend.formula_engine import FormulaEngine
except ImportError:
    from app import RawRevenueData, FetchLog, Base, engine
    from formula_engine import FormulaEngine


class DataFetcher:
    def __init__(self, db_url: str = None):
        if db_url:
            self.engine = create_engine(db_url)
        else:
            self.engine = engine
        
        SessionLocal = sessionmaker(bind=self.engine)
        self.db = SessionLocal()
        
        self.scraper = RevenueShareScraper(
            username=os.getenv("SCRAPER_USERNAME", "maxvaluemedia"),
            password=os.getenv("SCRAPER_PASSWORD", "gliacloud")
        )
    
    def _parse_numeric_value(self, value: str) -> str:
        """Parse numeric value, keeping original format for storage"""
        if not value or value == '-':
            return None
        return value.replace(',', '') if ',' in value else value
    
    def fetch_and_store(self, target_date: date = None, first_page_only: bool = False) -> Dict:
        """Fetch data and store in database"""
        if target_date is None:
            target_date = date.today() - timedelta(days=1)  # Yesterday by default
        
        fetch_log = FetchLog(
            fetch_date=target_date,
            status='started',
            started_at=datetime.utcnow()
        )
        self.db.add(fetch_log)
        self.db.commit()
        
        try:
            # Login
            if not self.scraper.login():
                fetch_log.status = 'failed'
                fetch_log.error_message = "Login failed"
                fetch_log.completed_at = datetime.utcnow()
                self.db.commit()
                return {"status": "failed", "error": "Login failed"}
            
            # Build URL
            date_str = target_date.strftime("%Y-%m-%d")
            url = f"https://gstudio.gliacloud.com/ad-sharing/publisher/revenueshare/?channel=No+Filter&time_unit_date__range__gte={date_str}&time_unit_date__range__lte={date_str}"
            
            # Fetch data
            if first_page_only:
                data = self.scraper.scrape_table_first_page_only(url)
            else:
                data = self.scraper.scrape_table(url)
            
            if not data:
                fetch_log.status = 'failed'
                fetch_log.error_message = "No data fetched"
                fetch_log.completed_at = datetime.utcnow()
                self.db.commit()
                return {"status": "failed", "error": "No data fetched"}
            
            # Store data (update existing or create new)
            records_created = 0
            records_updated = 0
            
            # Normalize keys - try both lowercase and original case
            def get_value(row_data, key_variants):
                for key in key_variants:
                    if key in row_data:
                        return row_data[key]
                return ''
            
            for row_data in data:
                # Check if record already exists
                existing = self.db.query(RawRevenueData).filter(
                    RawRevenueData.channel == get_value(row_data, ['channel', 'Channel', 'CHANNEL']),
                    RawRevenueData.slot == get_value(row_data, ['slot', 'Slot', 'SLOT']),
                    RawRevenueData.time_unit == get_value(row_data, ['time unit', 'time_unit', 'Time Unit', 'TIME UNIT']),
                    RawRevenueData.fetch_date == target_date
                ).first()
                
                if existing:
                    # Update existing record (ghi đè)
                    existing.total_player_impr = get_value(row_data, ['total player impr', 'total_player_impr', 'Total Player Impr', 'TOTAL PLAYER IMPR'])
                    existing.total_ad_impr = get_value(row_data, ['total ad impr', 'total_ad_impr', 'Total Ad Impr', 'TOTAL AD IMPR'])
                    existing.rpm = get_value(row_data, ['rpm', 'RPM'])
                    existing.gross_revenue_usd = get_value(row_data, ['gross revenue (usd)', 'gross_revenue_usd', 'Gross Revenue (USD)', 'GROSS REVENUE (USD)'])
                    existing.net_revenue_usd = get_value(row_data, ['net revenue (usd)', 'net_revenue_usd', 'Net Revenue (USD)', 'NET REVENUE (USD)'])
                    existing.fetched_at = datetime.utcnow()
                    records_updated += 1
                else:
                    # Create new record
                    db_row = RawRevenueData(
                        channel=get_value(row_data, ['channel', 'Channel', 'CHANNEL']),
                        slot=get_value(row_data, ['slot', 'Slot', 'SLOT']),
                        time_unit=get_value(row_data, ['time unit', 'time_unit', 'Time Unit', 'TIME UNIT']),
                        total_player_impr=get_value(row_data, ['total player impr', 'total_player_impr', 'Total Player Impr', 'TOTAL PLAYER IMPR']),
                        total_ad_impr=get_value(row_data, ['total ad impr', 'total_ad_impr', 'Total Ad Impr', 'TOTAL AD IMPR']),
                        rpm=get_value(row_data, ['rpm', 'RPM']),
                        gross_revenue_usd=get_value(row_data, ['gross revenue (usd)', 'gross_revenue_usd', 'Gross Revenue (USD)', 'GROSS REVENUE (USD)']),
                        net_revenue_usd=get_value(row_data, ['net revenue (usd)', 'net_revenue_usd', 'Net Revenue (USD)', 'NET REVENUE (USD)']),
                        fetch_date=target_date
                    )
                    self.db.add(db_row)
                    records_created += 1
            
            self.db.commit()
            
            # Compute formulas
            engine = FormulaEngine(self.db)
            engine.compute_all_formulas(compute_for_date=target_date)
            
            # Process data (tổng hợp desktop + mobile)
            from backend.data_processor import process_revenue_data
            process_result = process_revenue_data(self.db, target_date)
            
            # Update fetch log
            fetch_log.status = 'success'
            fetch_log.records_fetched = records_created + records_updated
            fetch_log.pages_fetched = 1 if first_page_only else len(data) // 100  # Approximate
            fetch_log.completed_at = datetime.utcnow()
            fetch_log.duration_seconds = int((fetch_log.completed_at - fetch_log.started_at).total_seconds())
            self.db.commit()
            
            return {
                "status": "success",
                "records_created": records_created,
                "records_updated": records_updated,
                "total_records": records_created + records_updated,
                "fetch_date": target_date.isoformat()
            }
            
        except Exception as e:
            fetch_log.status = 'failed'
            fetch_log.error_message = str(e)
            fetch_log.completed_at = datetime.utcnow()
            self.db.commit()
            return {"status": "failed", "error": str(e)}
    
    def run_scheduled_fetch(self):
        """Run scheduled fetch (to be called by scheduler)"""
        print(f"[{datetime.now()}] Starting scheduled fetch...")
        result = self.fetch_and_store()
        print(f"[{datetime.now()}] Fetch completed: {result}")
        return result


def setup_daily_scheduler():
    """Setup daily scheduler for data fetching"""
    if schedule is None or time is None:
        raise ImportError("schedule module is required for scheduled fetching. Install with: pip install schedule")
    
    fetcher = DataFetcher()
    
    # Schedule daily fetch at 2 AM
    schedule.every().day.at("02:00").do(fetcher.run_scheduled_fetch)
    
    print("Scheduler started. Daily fetch scheduled at 02:00")
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Data Fetcher Service")
    parser.add_argument("--date", type=str, help="Date to fetch (YYYY-MM-DD), defaults to yesterday")
    parser.add_argument("--first-page-only", action="store_true", help="Fetch only first page")
    parser.add_argument("--schedule", action="store_true", help="Run as scheduled service")
    
    args = parser.parse_args()
    
    fetcher = DataFetcher()
    
    if args.schedule:
        setup_daily_scheduler()
    else:
        target_date = None
        if args.date:
            target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
        
        result = fetcher.fetch_and_store(target_date, args.first_page_only)
        print(result)
