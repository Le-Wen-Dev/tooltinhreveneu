"""
Lock mechanism để tránh chạy trùng crawler
"""

from datetime import datetime
from crawler.db import CrawlRun, get_db_session
import os
import logging

logger = logging.getLogger(__name__)


def acquire_lock(db, fetch_date):
    """Acquire lock for a specific fetch_date. Reuse row if date already exists (completed/failed)."""
    try:
        # Bất kỳ bản ghi nào cho fetch_date này (running / completed / failed)
        existing = db.query(CrawlRun).filter(CrawlRun.fetch_date == fetch_date).first()

        if existing:
            if existing.status == 'running':
                # Kiểm tra process còn sống không
                try:
                    os.kill(existing.pid, 0)
                    logger.warning(f"Lock already held by process {existing.pid}")
                    return False
                except (OSError, ProcessLookupError):
                    pass  # process chết → dưới đây sẽ cập nhật lại
            # Cập nhật lại thành running (cho phép chạy lại sau khi completed/failed hoặc stale)
            existing.status = 'running'
            existing.pid = os.getpid()
            existing.started_at = datetime.utcnow()
            existing.completed_at = None
            db.commit()
            logger.info(f"Lock acquired for {fetch_date} (reused row)")
            return True

        # Chưa có bản ghi → tạo mới
        lock = CrawlRun(
            fetch_date=fetch_date,
            status='running',
            pid=os.getpid()
        )
        db.add(lock)
        db.commit()
        logger.info(f"Lock acquired for {fetch_date}")
        return True

    except Exception as e:
        logger.error(f"Error acquiring lock: {str(e)}")
        db.rollback()
        return False


def release_lock(db, fetch_date):
    """Release lock for a specific fetch_date"""
    try:
        lock = db.query(CrawlRun).filter(
            CrawlRun.fetch_date == fetch_date,
            CrawlRun.status == 'running'
        ).first()
        
        if lock:
            lock.status = 'completed'
            lock.completed_at = datetime.utcnow()
            db.commit()
            logger.info(f"Lock released for {fetch_date}")
        else:
            logger.warning(f"No lock found to release for {fetch_date}")
            
    except Exception as e:
        logger.error(f"Error releasing lock: {str(e)}")
        db.rollback()
