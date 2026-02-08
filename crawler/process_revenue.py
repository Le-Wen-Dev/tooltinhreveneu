"""
Process raw revenue data into processed_revenue_data (aggregated by slot for dashboard).
Uses crawler.db models only so it runs inside the crawler container.
"""
import re
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy.orm import Session
from sqlalchemy import and_

from crawler.db import RawRevenueData, ProcessedRevenueData


def parse_numeric(value) -> Decimal:
    if not value or value == '-' or (isinstance(value, str) and value.strip() == ''):
        return Decimal('0')
    s = str(value).replace(',', '').strip()
    try:
        return Decimal(s)
    except Exception:
        return Decimal('0')


def extract_base_slot(slot: str) -> str:
    slot = re.sub(r'_(desktop|mobile|news_desktop|news_mobile|true_desktop|true_mobile)$', '', slot)
    return slot


def process_revenue_data(db: Session, target_date: date) -> dict:
    raw_data = db.query(RawRevenueData).filter(RawRevenueData.fetch_date == target_date).all()
    if not raw_data:
        return {"status": "no_data", "records_processed": 0}

    grouped = {}
    for row in raw_data:
        base_slot = extract_base_slot(row.slot)
        key = (base_slot, row.time_unit)
        if key not in grouped:
            grouped[key] = {
                'slot': base_slot, 'time_unit': row.time_unit,
                'desktop': None, 'mobile': None, 'news_desktop': None, 'news_mobile': None,
                'true_desktop': None, 'true_mobile': None
            }
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

    records_processed = records_created = records_updated = 0
    share = Decimal('50.00')
    pairs = [
        ('desktop', 'mobile', lambda g: g['slot']),
        ('news_desktop', 'news_mobile', lambda g: f"{g['slot']}_news"),
        ('true_desktop', 'true_mobile', lambda g: f"{g['slot']}_true"),
    ]

    for group_data in grouped.values():
        time_unit = group_data['time_unit']
        for desktop_key, mobile_key, slot_fn in pairs:
            desktop_row = group_data.get(desktop_key)
            mobile_row = group_data.get(mobile_key)
            if not desktop_row and not mobile_row:
                continue
            slot_name = slot_fn(group_data)
            total_player_impr = parse_numeric(desktop_row.total_player_impr if desktop_row else '0') + parse_numeric(mobile_row.total_player_impr if mobile_row else '0')
            total_revenue = parse_numeric(desktop_row.net_revenue_usd if desktop_row else '0') + parse_numeric(mobile_row.net_revenue_usd if mobile_row else '0')
            rpm = (total_revenue / total_player_impr * Decimal('1000')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) if total_player_impr > 0 else Decimal('0')
            total_player_impr_2 = total_player_impr
            revenue_2 = (total_revenue * (share / Decimal('100'))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            rpm_2 = (revenue_2 / total_player_impr_2 * Decimal('1000')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) if total_player_impr_2 > 0 else Decimal('0')

            existing = db.query(ProcessedRevenueData).filter(
                and_(
                    ProcessedRevenueData.slot == slot_name,
                    ProcessedRevenueData.time_unit == time_unit,
                    ProcessedRevenueData.fetch_date == target_date
                )
            ).first()
            if existing:
                existing.total_player_impr = total_player_impr
                existing.revenue = total_revenue
                existing.rpm = rpm
                existing.share = share
                existing.total_player_impr_2 = total_player_impr_2
                existing.revenue_2 = revenue_2
                existing.rpm_2 = rpm_2
                records_updated += 1
            else:
                db.add(ProcessedRevenueData(
                    slot=slot_name, time_unit=time_unit,
                    total_player_impr=total_player_impr, revenue=total_revenue, rpm=rpm, share=share,
                    total_player_impr_2=total_player_impr_2, revenue_2=revenue_2, rpm_2=rpm_2,
                    fetch_date=target_date
                ))
                records_created += 1
            records_processed += 1

    return {"status": "success", "records_processed": records_processed, "records_created": records_created, "records_updated": records_updated}
