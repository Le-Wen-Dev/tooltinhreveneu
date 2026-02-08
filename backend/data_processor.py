"""
Data Processor - Xử lý raw data thành processed data
Tổng hợp desktop + mobile theo slot
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Optional
import re

try:
    from backend.app import RawRevenueData, engine, Base
except ImportError:
    from app import RawRevenueData, engine, Base

# Import processed table model
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Date
from sqlalchemy.ext.declarative import declarative_base

# Create processed table model
class ProcessedRevenueData(Base):
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
    processed_at = Column(DateTime, default=lambda: __import__('datetime').datetime.utcnow())


def parse_numeric(value: str) -> Optional[Decimal]:
    """Parse numeric value from string, handling commas and dashes"""
    if not value or value == '-' or value.strip() == '':
        return Decimal('0')
    
    # Remove commas
    value = value.replace(',', '').strip()
    
    try:
        return Decimal(value)
    except:
        return Decimal('0')


def extract_base_slot(slot: str) -> str:
    """Extract base slot name (remove _desktop, _mobile, etc.)"""
    # Remove _desktop, _mobile, _news_desktop, _news_mobile, _true_desktop, _true_mobile
    slot = re.sub(r'_(desktop|mobile|news_desktop|news_mobile|true_desktop|true_mobile)$', '', slot)
    return slot


def process_revenue_data(db: Session, target_date: date) -> Dict:
    """
    Xử lý raw data thành processed data
    - Tổng hợp desktop + mobile theo slot
    - Tính toán các metrics
    """
    # Lấy tất cả raw data cho ngày này
    raw_data = db.query(RawRevenueData).filter(
        RawRevenueData.fetch_date == target_date
    ).all()
    
    if not raw_data:
        return {
            "status": "no_data",
            "message": f"No raw data found for date {target_date}",
            "records_processed": 0
        }
    
    # Group by base slot và time_unit
    grouped = {}
    
    for row in raw_data:
        base_slot = extract_base_slot(row.slot)
        key = (base_slot, row.time_unit)
        
        if key not in grouped:
            grouped[key] = {
                'slot': base_slot,
                'time_unit': row.time_unit,
                'desktop': None,
                'mobile': None,
                'news_desktop': None,
                'news_mobile': None,
                'true_desktop': None,
                'true_mobile': None
            }
        
        # Phân loại theo slot type
        if row.slot.endswith('_desktop') and not row.slot.endswith('_news_desktop') and not row.slot.endswith('_true_desktop'):
            grouped[key]['desktop'] = row
        elif row.slot.endswith('_mobile') and not row.slot.endswith('_news_mobile') and not row.slot.endswith('_true_mobile'):
            grouped[key]['mobile'] = row
        elif row.slot.endswith('_news_desktop'):
            grouped[key]['news_desktop'] = row
        elif row.slot.endswith('_news_mobile'):
            grouped[key]['news_mobile'] = row
        elif row.slot.endswith('_true_desktop'):
            grouped[key]['true_desktop'] = row
        elif row.slot.endswith('_true_mobile'):
            grouped[key]['true_mobile'] = row
    
    records_processed = 0
    records_created = 0
    records_updated = 0
    
    # Xử lý từng group
    for key, group_data in grouped.items():
        base_slot = group_data['slot']
        time_unit = group_data['time_unit']
        
        # Xử lý từng cặp desktop + mobile
        pairs = [
            ('desktop', 'mobile', base_slot),
            ('news_desktop', 'news_mobile', f"{base_slot}_news"),
            ('true_desktop', 'true_mobile', f"{base_slot}_true")
        ]
        
        for desktop_key, mobile_key, slot_name in pairs:
            desktop_row = group_data.get(desktop_key)
            mobile_row = group_data.get(mobile_key)
            
            # Chỉ xử lý nếu có ít nhất 1 row
            if not desktop_row and not mobile_row:
                continue
            
            # Tính tổng
            total_player_impr = Decimal('0')
            total_revenue = Decimal('0')
            
            if desktop_row:
                total_player_impr += parse_numeric(desktop_row.total_player_impr or '0')
                total_revenue += parse_numeric(desktop_row.net_revenue_usd or '0')
            
            if mobile_row:
                total_player_impr += parse_numeric(mobile_row.total_player_impr or '0')
                total_revenue += parse_numeric(mobile_row.net_revenue_usd or '0')
            
            # Tính RPM
            rpm = Decimal('0')
            if total_player_impr > 0:
                rpm = (total_revenue / total_player_impr) * Decimal('1000')
                rpm = rpm.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
            # Dynamic share lookup per slot + date
            try:
                from crawler.db import get_share_for_slot
                share = get_share_for_slot(db, slot_name, target_date)
            except ImportError:
                share = Decimal('50.00')
            
            # Total player IMPR 2 = Total player IMPR
            total_player_impr_2 = total_player_impr
            
            # Revenue 2 = Revenue * Share
            revenue_2 = total_revenue * (share / Decimal('100'))
            revenue_2 = revenue_2.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
            # RPM 2
            rpm_2 = Decimal('0')
            if total_player_impr_2 > 0:
                rpm_2 = (revenue_2 / total_player_impr_2) * Decimal('1000')
                rpm_2 = rpm_2.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
            # Check if record exists
            existing = db.query(ProcessedRevenueData).filter(
                and_(
                    ProcessedRevenueData.slot == slot_name,
                    ProcessedRevenueData.time_unit == time_unit,
                    ProcessedRevenueData.fetch_date == target_date
                )
            ).first()
            
            if existing:
                # Update
                existing.total_player_impr = total_player_impr
                existing.revenue = total_revenue
                existing.rpm = rpm
                existing.share = share
                existing.total_player_impr_2 = total_player_impr_2
                existing.revenue_2 = revenue_2
                existing.rpm_2 = rpm_2
                records_updated += 1
            else:
                # Create
                processed = ProcessedRevenueData(
                    slot=slot_name,
                    time_unit=time_unit,
                    total_player_impr=total_player_impr,
                    revenue=total_revenue,
                    rpm=rpm,
                    share=share,
                    total_player_impr_2=total_player_impr_2,
                    revenue_2=revenue_2,
                    rpm_2=rpm_2,
                    fetch_date=target_date
                )
                db.add(processed)
                records_created += 1
            
            records_processed += 1
    
    db.commit()
    
    return {
        "status": "success",
        "records_processed": records_processed,
        "records_created": records_created,
        "records_updated": records_updated,
        "fetch_date": target_date.isoformat()
    }
