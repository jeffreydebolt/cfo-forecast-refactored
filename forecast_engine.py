#!/usr/bin/env python3
"""
Cash Flow Forecast Engine
Handles pattern detection, forecast generation, and reconciliation
"""

import sys
import json
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import pandas as pd
import numpy as np

sys.path.append('.')
from supabase_client import supabase

@dataclass
class PatternResult:
    frequency: str  # 'daily', 'weekly', 'bi-weekly', 'monthly', 'quarterly', 'irregular'
    timing_details: Dict
    avg_amount: Decimal
    confidence: float
    transaction_count: int

@dataclass
class ForecastRecord:
    client_id: str
    forecast_date: date
    vendor_group_id: int
    forecasted_amount: Decimal
    pattern_type: str
    forecast_method: str = 'system'

class ForecastEngine:
    def __init__(self, client_id: str):
        self.client_id = client_id
    
    def detect_vendor_group_pattern(self, vendor_group_id: int, 
                                  start_date: date = None, 
                                  end_date: date = None) -> PatternResult:
        """Detect patterns for a specific vendor group"""
        
        if not start_date:
            start_date = date.today() - timedelta(days=90)  # 3 months default
        if not end_date:
            end_date = date.today()
        
        # Get all transactions for this vendor group
        transactions = self._get_vendor_group_transactions(vendor_group_id, start_date, end_date)
        
        if len(transactions) < 3:
            return PatternResult('irregular', {}, Decimal('0'), 0.0, len(transactions))
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(transactions)
        df['transaction_date'] = pd.to_datetime(df['transaction_date'])
        df['amount'] = df['amount'].abs()  # Use absolute values for pattern detection
        
        # Try different pattern detection methods
        patterns = [
            self._detect_daily_pattern(df),
            self._detect_weekly_pattern(df),
            self._detect_biweekly_pattern(df),
            self._detect_monthly_pattern(df),
            self._detect_quarterly_pattern(df)
        ]
        
        # Select best pattern based on confidence
        best_pattern = max(patterns, key=lambda p: p.confidence)
        
        return best_pattern
    
    def _get_vendor_group_transactions(self, vendor_group_id: int, 
                                     start_date: date, end_date: date) -> List[Dict]:
        """Get all transactions for vendors in this group"""
        
        # Get vendor names in this group
        vendor_mappings = supabase.table('vendor_group_mappings').select('vendor_name').eq('vendor_group_id', vendor_group_id).execute()
        vendor_names = [m['vendor_name'] for m in vendor_mappings.data]
        
        if not vendor_names:
            return []
        
        # Get transactions for these vendors
        transactions = []
        for vendor_name in vendor_names:
            result = supabase.table('transactions').select(
                'transaction_date, amount, vendor_name'
            ).eq('client_id', self.client_id).eq('vendor_name', vendor_name).gte(
                'transaction_date', start_date.isoformat()
            ).lte('transaction_date', end_date.isoformat()).execute()
            
            transactions.extend(result.data)
        
        return transactions
    
    def _detect_daily_pattern(self, df: pd.DataFrame) -> PatternResult:
        """Detect daily patterns (M-F, all days, etc.)"""
        
        if len(df) < 10:
            return PatternResult('daily', {}, Decimal('0'), 0.0, len(df))
        
        # Group by date
        daily_amounts = df.groupby(df['transaction_date'].dt.date)['amount'].sum()
        
        # Check if mostly weekdays
        weekday_txns = df[df['transaction_date'].dt.dayofweek < 5]  # M-F
        weekend_txns = df[df['transaction_date'].dt.dayofweek >= 5]
        
        weekday_ratio = len(weekday_txns) / len(df)
        
        # If 80%+ on weekdays, it's a M-F pattern
        if weekday_ratio > 0.8:
            avg_amount = weekday_txns['amount'].mean()
            confidence = min(0.9, weekday_ratio)
            timing_details = {'days_of_week': [0, 1, 2, 3, 4]}  # M-F
        else:
            avg_amount = df['amount'].mean()
            confidence = 0.6
            timing_details = {'days_of_week': list(range(7))}  # All days
        
        # Check consistency
        if daily_amounts.std() / daily_amounts.mean() < 0.5:  # Low variance
            confidence += 0.1
        
        return PatternResult('daily', timing_details, Decimal(str(avg_amount)), confidence, len(df))
    
    def _detect_weekly_pattern(self, df: pd.DataFrame) -> PatternResult:
        """Detect weekly patterns (same day each week)"""
        
        if len(df) < 4:
            return PatternResult('weekly', {}, Decimal('0'), 0.0, len(df))
        
        # Group by day of week
        dow_counts = df['transaction_date'].dt.dayofweek.value_counts()
        
        # If 70%+ transactions on same day of week
        if dow_counts.iloc[0] / len(df) > 0.7:
            primary_dow = dow_counts.index[0]
            
            # Calculate average weekly amount
            weekly_txns = df[df['transaction_date'].dt.dayofweek == primary_dow]
            avg_amount = weekly_txns['amount'].mean()
            
            confidence = min(0.9, dow_counts.iloc[0] / len(df))
            timing_details = {'day_of_week': primary_dow}
            
            return PatternResult('weekly', timing_details, Decimal(str(avg_amount)), confidence, len(df))
        
        return PatternResult('weekly', {}, Decimal('0'), 0.2, len(df))
    
    def _detect_biweekly_pattern(self, df: pd.DataFrame) -> PatternResult:
        """Detect bi-weekly patterns (every 2 weeks or 15th/30th)"""
        
        if len(df) < 6:
            return PatternResult('bi-weekly', {}, Decimal('0'), 0.0, len(df))
        
        # Check for 15th/30th pattern
        df['day_of_month'] = df['transaction_date'].dt.day
        mid_month = ((df['day_of_month'] >= 14) & (df['day_of_month'] <= 16)).sum()
        end_month = (df['day_of_month'] >= 28).sum()
        
        # If most transactions on 15th or end of month
        if (mid_month + end_month) / len(df) > 0.7:
            avg_amount = df['amount'].mean()
            confidence = min(0.85, (mid_month + end_month) / len(df))
            timing_details = {'days_of_month': [15, 30]}
            
            return PatternResult('bi-weekly', timing_details, Decimal(str(avg_amount)), confidence, len(df))
        
        # Check for every-other-week pattern
        df_sorted = df.sort_values('transaction_date')
        date_diffs = df_sorted['transaction_date'].diff().dt.days.dropna()
        
        # Look for ~14 day intervals
        biweekly_intervals = ((date_diffs >= 12) & (date_diffs <= 16)).sum()
        
        if biweekly_intervals / len(date_diffs) > 0.6:
            primary_dow = df['transaction_date'].dt.dayofweek.mode().iloc[0]
            avg_amount = df['amount'].mean()
            confidence = min(0.8, biweekly_intervals / len(date_diffs))
            timing_details = {'interval_weeks': 2, 'day_of_week': primary_dow}
            
            return PatternResult('bi-weekly', timing_details, Decimal(str(avg_amount)), confidence, len(df))
        
        return PatternResult('bi-weekly', {}, Decimal('0'), 0.1, len(df))
    
    def _detect_monthly_pattern(self, df: pd.DataFrame) -> PatternResult:
        """Detect monthly patterns (same day each month)"""
        
        if len(df) < 3:
            return PatternResult('monthly', {}, Decimal('0'), 0.0, len(df))
        
        # Group by day of month
        dom_counts = df['transaction_date'].dt.day.value_counts()
        
        # If 60%+ transactions on same day of month
        if dom_counts.iloc[0] / len(df) > 0.6:
            primary_dom = dom_counts.index[0]
            avg_amount = df['amount'].mean()
            confidence = min(0.85, dom_counts.iloc[0] / len(df))
            timing_details = {'day_of_month': primary_dom}
            
            return PatternResult('monthly', timing_details, Decimal(str(avg_amount)), confidence, len(df))
        
        return PatternResult('monthly', {}, Decimal('0'), 0.2, len(df))
    
    def _detect_quarterly_pattern(self, df: pd.DataFrame) -> PatternResult:
        """Detect quarterly patterns"""
        
        if len(df) < 2:
            return PatternResult('quarterly', {}, Decimal('0'), 0.0, len(df))
        
        # Simple quarterly check - transactions ~90 days apart
        df_sorted = df.sort_values('transaction_date')
        date_diffs = df_sorted['transaction_date'].diff().dt.days.dropna()
        
        quarterly_intervals = ((date_diffs >= 80) & (date_diffs <= 100)).sum()
        
        if quarterly_intervals / len(date_diffs) > 0.5:
            avg_amount = df['amount'].mean()
            confidence = min(0.7, quarterly_intervals / len(date_diffs))
            timing_details = {'interval_months': 3}
            
            return PatternResult('quarterly', timing_details, Decimal(str(avg_amount)), confidence, len(df))
        
        return PatternResult('quarterly', {}, Decimal('0'), 0.1, len(df))
    
    def update_vendor_group_forecast_rule(self, vendor_group_id: int, 
                                        pattern: PatternResult = None,
                                        manual_amount: Decimal = None) -> bool:
        """Update or create forecast rule for a vendor group"""
        
        if not pattern:
            pattern = self.detect_vendor_group_pattern(vendor_group_id)
        
        base_amount = manual_amount if manual_amount else pattern.avg_amount
        
        # Upsert forecast rule
        rule_data = {
            'client_id': self.client_id,
            'vendor_group_id': vendor_group_id,
            'frequency': pattern.frequency,
            'timing_details': json.dumps(pattern.timing_details),
            'amount_method': 'manual' if manual_amount else 'weighted_average',
            'base_amount': float(base_amount),
            'is_active': True,
            'last_pattern_update': datetime.now().isoformat()
        }
        
        try:
            # Try update first
            result = supabase.table('vendor_forecast_rules').upsert(rule_data).execute()
            return True
        except Exception as e:
            print(f"Error updating forecast rule: {e}")
            return False
    
    def generate_forecasts(self, start_date: date = None, weeks: int = 12) -> List[ForecastRecord]:
        """Generate forecast records for all vendor groups"""
        
        if not start_date:
            # Start from next Monday
            today = date.today()
            days_ahead = 0 - today.weekday()  # Monday is 0
            if days_ahead <= 0:
                days_ahead += 7
            start_date = today + timedelta(days=days_ahead)
        
        end_date = start_date + timedelta(weeks=weeks)
        
        # Get all active forecast rules
        rules_result = supabase.table('vendor_forecast_rules').select(
            '*, vendor_groups(*)'
        ).eq('client_id', self.client_id).eq('is_active', True).execute()
        
        forecast_records = []
        
        for rule in rules_result.data:
            timing_details = json.loads(rule['timing_details'] or '{}')
            
            # Generate dates based on pattern
            dates = self._generate_forecast_dates(
                start_date, end_date, 
                rule['frequency'], 
                timing_details
            )
            
            # Create forecast record for each date
            for forecast_date in dates:
                record = ForecastRecord(
                    client_id=self.client_id,
                    forecast_date=forecast_date,
                    vendor_group_id=rule['vendor_group_id'],
                    forecasted_amount=Decimal(str(rule['base_amount'])),
                    pattern_type=rule['frequency'],
                    forecast_method='system'
                )
                forecast_records.append(record)
        
        return forecast_records
    
    def _generate_forecast_dates(self, start_date: date, end_date: date,
                               frequency: str, timing_details: Dict) -> List[date]:
        """Generate specific dates for forecasting based on pattern"""
        
        dates = []
        current_date = start_date
        
        if frequency == 'daily':
            days_of_week = timing_details.get('days_of_week', list(range(7)))
            while current_date <= end_date:
                if current_date.weekday() in days_of_week:
                    dates.append(current_date)
                current_date += timedelta(days=1)
        
        elif frequency == 'weekly':
            target_dow = timing_details.get('day_of_week', 0)  # Monday default
            # Find first occurrence
            days_ahead = target_dow - current_date.weekday()
            if days_ahead < 0:
                days_ahead += 7
            current_date += timedelta(days=days_ahead)
            
            while current_date <= end_date:
                dates.append(current_date)
                current_date += timedelta(days=7)
        
        elif frequency == 'bi-weekly':
            if 'days_of_month' in timing_details:
                # 15th/30th pattern
                current_month = current_date.replace(day=1)
                while current_month.year <= end_date.year and current_month.month <= end_date.month:
                    for day in timing_details['days_of_month']:
                        try:
                            forecast_date = current_month.replace(day=day)
                            if start_date <= forecast_date <= end_date:
                                dates.append(forecast_date)
                        except ValueError:
                            # Handle months without 30th/31st
                            if day == 30:
                                # Use last day of month
                                next_month = current_month.replace(month=current_month.month + 1) if current_month.month < 12 else current_month.replace(year=current_month.year + 1, month=1)
                                last_day = next_month - timedelta(days=1)
                                if start_date <= last_day <= end_date:
                                    dates.append(last_day)
                    
                    # Move to next month
                    if current_month.month == 12:
                        current_month = current_month.replace(year=current_month.year + 1, month=1)
                    else:
                        current_month = current_month.replace(month=current_month.month + 1)
            else:
                # Every other week pattern
                target_dow = timing_details.get('day_of_week', 0)
                interval_weeks = timing_details.get('interval_weeks', 2)
                
                # Find first occurrence
                days_ahead = target_dow - current_date.weekday()
                if days_ahead < 0:
                    days_ahead += 7
                current_date += timedelta(days=days_ahead)
                
                while current_date <= end_date:
                    dates.append(current_date)
                    current_date += timedelta(weeks=interval_weeks)
        
        elif frequency == 'monthly':
            target_dom = timing_details.get('day_of_month', 1)
            current_month = current_date.replace(day=1)
            
            while current_month.year <= end_date.year and current_month.month <= end_date.month:
                try:
                    forecast_date = current_month.replace(day=target_dom)
                    if start_date <= forecast_date <= end_date:
                        dates.append(forecast_date)
                except ValueError:
                    # Handle day not existing in month
                    pass
                
                # Move to next month
                if current_month.month == 12:
                    current_month = current_month.replace(year=current_month.year + 1, month=1)
                else:
                    current_month = current_month.replace(month=current_month.month + 1)
        
        elif frequency == 'quarterly':
            interval_months = timing_details.get('interval_months', 3)
            current_month = current_date.replace(day=1)
            
            while current_month <= end_date:
                if start_date <= current_month <= end_date:
                    dates.append(current_month)
                # Add interval months
                new_month = current_month.month + interval_months
                new_year = current_month.year
                while new_month > 12:
                    new_month -= 12
                    new_year += 1
                current_month = current_month.replace(year=new_year, month=new_month)
        
        return sorted(dates)
    
    def save_forecasts(self, forecast_records: List[ForecastRecord]) -> bool:
        """Save forecast records to database"""
        
        if not forecast_records:
            return True
        
        # Convert to dict format for Supabase
        records_data = []
        for record in forecast_records:
            records_data.append({
                'client_id': record.client_id,
                'forecast_date': record.forecast_date.isoformat(),
                'vendor_group_id': record.vendor_group_id,
                'forecasted_amount': float(record.forecasted_amount),
                'pattern_type': record.pattern_type,
                'forecast_method': record.forecast_method,
                'is_actual': False,
                'is_locked': False
            })
        
        try:
            # Use upsert to handle duplicates
            result = supabase.table('forecast_records').upsert(records_data).execute()
            print(f"✅ Saved {len(records_data)} forecast records")
            return True
        except Exception as e:
            print(f"❌ Error saving forecasts: {e}")
            return False
    
    def get_forecast_dashboard_data(self, start_date: date = None, weeks: int = 12) -> Dict:
        """Get formatted data for the forecast dashboard"""
        
        if not start_date:
            # Start from this Monday
            today = date.today()
            days_behind = today.weekday()
            start_date = today - timedelta(days=days_behind)
        
        end_date = start_date + timedelta(weeks=weeks)
        
        # Get forecast data
        forecast_result = supabase.table('forecast_dashboard_view').select('*').eq(
            'client_id', self.client_id
        ).gte('forecast_date', start_date.isoformat()).lte(
            'forecast_date', end_date.isoformat()
        ).order('forecast_date', 'category', 'subcategory').execute()
        
        # Get cash balances
        balance_result = supabase.table('cash_balances').select('*').eq(
            'client_id', self.client_id
        ).gte('balance_date', start_date.isoformat()).lte(
            'balance_date', end_date.isoformat()
        ).order('balance_date').execute()
        
        # Format data for frontend
        forecast_data = {}
        for record in forecast_result.data:
            date_key = record['forecast_date']
            category = record['category']
            subcategory = record['subcategory']
            
            if date_key not in forecast_data:
                forecast_data[date_key] = {}
            if category not in forecast_data[date_key]:
                forecast_data[date_key][category] = {}
            if subcategory not in forecast_data[date_key][category]:
                forecast_data[date_key][category][subcategory] = {
                    'forecasted': 0,
                    'actual': 0,
                    'variance': 0,
                    'is_actual': False
                }
            
            forecast_data[date_key][category][subcategory]['forecasted'] += record['forecasted_amount'] or 0
            forecast_data[date_key][category][subcategory]['actual'] += record['actual_amount'] or 0
            forecast_data[date_key][category][subcategory]['variance'] += record['variance_amount'] or 0
            if record['is_actual']:
                forecast_data[date_key][category][subcategory]['is_actual'] = True
        
        return {
            'forecast_data': forecast_data,
            'cash_balances': {b['balance_date']: b for b in balance_result.data},
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        }


def main():
    """Test the forecast engine"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Forecast Engine')
    parser.add_argument('--client', required=True, help='Client ID')
    parser.add_argument('--generate', action='store_true', help='Generate forecasts')
    args = parser.parse_args()
    
    engine = ForecastEngine(args.client)
    
    if args.generate:
        print("Generating forecasts...")
        forecasts = engine.generate_forecasts()
        print(f"Generated {len(forecasts)} forecast records")
        
        success = engine.save_forecasts(forecasts)
        if success:
            print("✅ Forecasts saved successfully")
        else:
            print("❌ Error saving forecasts")

if __name__ == "__main__":
    main()