"""
Formula Calculation Engine
Handles computation of custom formulas on revenue data
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, List, Any, Optional
from decimal import Decimal
import re
import math
try:
    from backend.app import RawRevenueData, Formula, ComputedMetric, AggregatedMetric
except ImportError:
    try:
        from app import RawRevenueData, Formula, ComputedMetric, AggregatedMetric
    except ImportError:
        # Import from crawler.db (for crawler container)
        from crawler.db import RawRevenueData, Formula, ComputedMetric, AggregatedMetric


class FormulaEngine:
    def __init__(self, db: Session):
        self.db = db
    
    def _parse_value(self, value: str) -> Optional[Decimal]:
        """Parse string value to Decimal, handling commas and dashes"""
        if not value or value == '-' or value.strip() == '':
            return None
        try:
            # Remove commas and convert to decimal
            cleaned = value.replace(',', '').strip()
            return Decimal(cleaned)
        except:
            return None
    
    def _get_field_value(self, row: RawRevenueData, field_name: str) -> Optional[Decimal]:
        """Get field value from row"""
        field_map = {
            'total_player_impr': row.total_player_impr,
            'total_ad_impr': row.total_ad_impr,
            'rpm': row.rpm,
            'gross_revenue_usd': row.gross_revenue_usd,
            'net_revenue_usd': row.net_revenue_usd,
        }
        
        value = field_map.get(field_name)
        if value:
            return self._parse_value(value)
        return None
    
    def _evaluate_expression(self, expression: str, context: Dict[str, Any]) -> Optional[Decimal]:
        """Safely evaluate a Python expression with context"""
        try:
            # Replace field names with values from context
            for key, value in context.items():
                if value is not None:
                    expression = expression.replace(key, str(value))
                else:
                    # If value is None, return None for the whole expression
                    if key in expression:
                        return None
            
            # Only allow safe operations
            allowed_names = {
                "abs": abs, "round": round, "min": min, "max": max,
                "sum": sum, "math": math, "Decimal": Decimal
            }
            
            # Evaluate expression
            result = eval(expression, {"__builtins__": {}}, allowed_names)
            
            if isinstance(result, (int, float)):
                return Decimal(str(result))
            return result
        except Exception as e:
            print(f"Error evaluating expression: {expression}, Error: {e}")
            return None
    
    def compute_row_metric(self, row: RawRevenueData, formula: Formula) -> Optional[Decimal]:
        """Compute metric for a single row"""
        # Build context with row data
        context = {
            'total_player_impr': self._get_field_value(row, 'total_player_impr'),
            'total_ad_impr': self._get_field_value(row, 'total_ad_impr'),
            'rpm': self._get_field_value(row, 'rpm'),
            'gross_revenue_usd': self._get_field_value(row, 'gross_revenue_usd'),
            'net_revenue_usd': self._get_field_value(row, 'net_revenue_usd'),
        }
        
        # Handle special formulas
        if formula.name == 'rpm_per_1000_players':
            net_rev = context['net_revenue_usd']
            player_impr = context['total_player_impr']
            if net_rev and player_impr and player_impr > 0:
                return (net_rev / player_impr) * Decimal('1000')
            return None
        
        # Generic formula evaluation
        expression = formula.formula_expression
        
        # Replace common patterns
        expression = expression.replace('net_revenue_usd', 'net_revenue_usd')
        expression = expression.replace('total_player_impr', 'total_player_impr')
        expression = expression.replace('total_ad_impr', 'total_ad_impr')
        expression = expression.replace('gross_revenue_usd', 'gross_revenue_usd')
        
        return self._evaluate_expression(expression, context)
    
    def compute_aggregated_metric(self, formula: Formula, 
                                 channel: Optional[str] = None,
                                 time_unit: Optional[str] = None,
                                 fetch_date: Optional[Any] = None) -> Optional[Decimal]:
        """Compute aggregated metric across multiple rows"""
        # Build query
        query = self.db.query(RawRevenueData)
        
        if channel:
            query = query.filter(RawRevenueData.channel == channel)
        if time_unit:
            query = query.filter(RawRevenueData.time_unit == time_unit)
        if fetch_date:
            query = query.filter(RawRevenueData.fetch_date == fetch_date)
        
        rows = query.all()
        
        if not rows:
            return None
        
        # Handle RPM = Tổng Net Revenue (Mobile + Desktop)
        # Đây là tổng net revenue, KHÔNG chia cho impressions
        if formula.name == 'rpm_total_net_revenue':
            total_net_revenue = Decimal('0')
            for row in rows:
                net_rev = self._get_field_value(row, 'net_revenue_usd')
                if net_rev:
                    total_net_revenue += net_rev
            return total_net_revenue
        
        # Handle RPM Combined = (Tổng Net Revenue / Tổng Player Impressions) * 1000
        if formula.name == 'rpm_combined':
            total_net_revenue = Decimal('0')
            total_player_impr = Decimal('0')
            
            for row in rows:
                net_rev = self._get_field_value(row, 'net_revenue_usd')
                player_impr = self._get_field_value(row, 'total_player_impr')
                
                if net_rev:
                    total_net_revenue += net_rev
                if player_impr:
                    total_player_impr += player_impr
            
            if total_player_impr > 0:
                return (total_net_revenue / total_player_impr) * Decimal('1000')
            return None
        
        # Handle Total Net Revenue (tổng hợp)
        if formula.name == 'total_net_revenue':
            total = Decimal('0')
            for row in rows:
                net_rev = self._get_field_value(row, 'net_revenue_usd')
                if net_rev:
                    total += net_rev
            return total
        
        # Generic aggregated formula
        # For now, return sum of individual row computations
        total = Decimal('0')
        count = 0
        for row in rows:
            value = self.compute_row_metric(row, formula)
            if value:
                total += value
                count += 1
        
        return total if count > 0 else None
    
    def compute_formula(self, formula_id: int, 
                       compute_for_date: Optional[Any] = None) -> Dict[str, Any]:
        """Compute formula for all relevant data"""
        formula = self.db.query(Formula).filter(Formula.id == formula_id).first()
        if not formula:
            return {"error": "Formula not found"}
        
        if not formula.is_active:
            return {"error": "Formula is not active"}
        
        results = {
            "formula_id": formula_id,
            "formula_name": formula.name,
            "computed_metrics": 0,
            "aggregated_metrics": 0
        }
        
        # Determine if this is a row-level or aggregated formula
        # Aggregated formulas: rpm_total_net_revenue, rpm_combined, total_net_revenue
        aggregated_formulas = ['rpm_total_net_revenue', 'rpm_combined', 'total_net_revenue']
        is_aggregated = formula.name in aggregated_formulas or (
            formula.formula_type in ['rpm', 'revenue'] and 'sum' in formula.formula_expression.lower()
        )
        
        if is_aggregated:
            # Compute aggregated metrics
            # Get unique combinations of channel, time_unit, fetch_date
            query = self.db.query(
                RawRevenueData.channel,
                RawRevenueData.time_unit,
                RawRevenueData.fetch_date
            ).distinct()
            
            if compute_for_date:
                query = query.filter(RawRevenueData.fetch_date == compute_for_date)
            
            combinations = query.all()
            
            for channel, time_unit, fetch_date in combinations:
                value = self.compute_aggregated_metric(
                    formula, 
                    channel=channel,
                    time_unit=time_unit,
                    fetch_date=fetch_date
                )
                
                if value is not None:
                    # Check if aggregated metric already exists
                    existing = self.db.query(AggregatedMetric).filter(
                        AggregatedMetric.channel == channel,
                        AggregatedMetric.time_unit == time_unit,
                        AggregatedMetric.fetch_date == fetch_date,
                        AggregatedMetric.metric_name == formula.name,
                        AggregatedMetric.formula_id == formula_id
                    ).first()
                    
                    if existing:
                        existing.metric_value = value
                        existing.computed_at = func.now()
                    else:
                        agg_metric = AggregatedMetric(
                            channel=channel,
                            time_unit=time_unit,
                            fetch_date=fetch_date,
                            metric_name=formula.name,
                            metric_value=value,
                            formula_id=formula_id
                        )
                        self.db.add(agg_metric)
                    
                    results["aggregated_metrics"] += 1
        else:
            # Compute row-level metrics
            query = self.db.query(RawRevenueData)
            if compute_for_date:
                query = query.filter(RawRevenueData.fetch_date == compute_for_date)
            
            rows = query.all()
            
            for row in rows:
                value = self.compute_row_metric(row, formula)
                
                if value is not None:
                    # Check if computed metric already exists
                    existing = self.db.query(ComputedMetric).filter(
                        ComputedMetric.raw_data_id == row.id,
                        ComputedMetric.formula_id == formula_id,
                        ComputedMetric.metric_name == formula.name
                    ).first()
                    
                    if existing:
                        existing.metric_value = value
                        existing.computed_at = func.now()
                    else:
                        computed = ComputedMetric(
                            raw_data_id=row.id,
                            formula_id=formula_id,
                            metric_name=formula.name,
                            metric_value=value
                        )
                        self.db.add(computed)
                    
                    results["computed_metrics"] += 1
        
        self.db.commit()
        return results
    
    def compute_all_formulas(self, compute_for_date: Optional[Any] = None):
        """Compute all active formulas"""
        formulas = self.db.query(Formula).filter(Formula.is_active == True).all()
        results = []
        
        for formula in formulas:
            result = self.compute_formula(formula.id, compute_for_date)
            results.append(result)
        
        return results
