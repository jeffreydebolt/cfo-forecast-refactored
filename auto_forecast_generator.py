#!/usr/bin/env python3
"""
Auto-Forecast Generator - Phase 4
Generates forecasts for vendors with consistent, predictable patterns
"""

import sys
sys.path.append('.')

from pattern_detection_engine import PatternDetectionEngine
from supabase_client import supabase
from datetime import datetime, date, timedelta
from dataclasses import dataclass
from typing import Dict, List, Optional
import calendar

@dataclass
class ForecastRecord:
    """Individual forecast record for a specific date"""
    vendor_name: str
    forecast_date: date
    predicted_amount: float
    confidence: float
    pattern_type: str
    reasoning: str

class AutoForecastGenerator:
    """Generates forecasts for vendors with predictable patterns"""
    
    def __init__(self):
        self.pattern_engine = PatternDetectionEngine()
        self.forecast_horizon_days = 90  # 3 months ahead
    
    def generate_auto_forecasts(self, client_id: str) -> List[ForecastRecord]:
        """Generate forecasts for all auto-ready vendors"""
        print("🔮 AUTO-FORECAST GENERATOR")
        print("=" * 80)
        
        # Get pattern analysis
        vendor_patterns = self.pattern_engine.analyze_vendor_patterns(client_id)
        
        # Filter for auto-forecast ready vendors
        auto_vendors = {
            name: pattern for name, pattern in vendor_patterns.items() 
            if pattern.forecast_recommendation == 'auto'
        }
        
        print(f"🎯 Generating forecasts for {len(auto_vendors)} auto-ready vendors")
        
        # Generate forecasts for each vendor
        all_forecasts = []
        
        for vendor_name, pattern in auto_vendors.items():
            forecasts = self._generate_vendor_forecasts(vendor_name, pattern, client_id)
            all_forecasts.extend(forecasts)
            print(f"├── {vendor_name}: {len(forecasts)} forecast records generated")
        
        print(f"\n✅ Generated {len(all_forecasts)} total forecast records")
        print(f"📅 Forecast period: {date.today()} to {date.today() + timedelta(days=self.forecast_horizon_days)}")
        
        return all_forecasts
    
    def _generate_vendor_forecasts(self, vendor_name: str, pattern, client_id: str) -> List[ForecastRecord]:
        """Generate forecast records for a single vendor"""
        
        # Get the vendor's transaction history
        result = supabase.table('transactions').select('*')\
            .eq('client_id', client_id)\
            .eq('vendor_name', vendor_name)\
            .order('transaction_date')\
            .execute()
        
        transactions = result.data
        if not transactions:
            return []
        
        # Find the last transaction date
        last_txn_date = datetime.fromisoformat(transactions[-1]['transaction_date']).date()
        
        # Generate forecast dates based on timing pattern
        forecast_dates = self._calculate_forecast_dates(
            last_txn_date, 
            pattern.timing_pattern,
            self.forecast_horizon_days
        )
        
        # Create forecast records
        forecasts = []
        for forecast_date in forecast_dates:
            forecast = ForecastRecord(
                vendor_name=vendor_name,
                forecast_date=forecast_date,
                predicted_amount=pattern.amount_pattern.average_amount,
                confidence=min(pattern.timing_pattern.confidence, pattern.amount_pattern.confidence),
                pattern_type=pattern.timing_pattern.pattern_type,
                reasoning=f"{pattern.timing_pattern.pattern_type.title()} pattern, ${pattern.amount_pattern.average_amount:,.0f} average"
            )
            forecasts.append(forecast)
        
        return forecasts
    
    def _calculate_forecast_dates(self, last_date: date, timing_pattern, horizon_days: int) -> List[date]:
        """Calculate future forecast dates based on timing pattern"""
        forecast_dates = []
        start_date = max(last_date, date.today())  # Don't forecast in the past
        current_date = start_date
        end_date = date.today() + timedelta(days=horizon_days)
        
        if timing_pattern.pattern_type == 'daily':
            # Daily pattern
            while current_date <= end_date:
                current_date += timedelta(days=1)
                forecast_dates.append(current_date)
        
        elif timing_pattern.pattern_type == 'weekly':
            # Weekly pattern - same day of week
            target_weekday = timing_pattern.day_of_week if timing_pattern.day_of_week is not None else last_date.weekday()
            
            # Find next occurrence of target weekday
            days_ahead = (target_weekday - current_date.weekday()) % 7
            if days_ahead == 0:  # If it's the same day, go to next week
                days_ahead = 7
            
            current_date += timedelta(days=days_ahead)
            
            while current_date <= end_date:
                forecast_dates.append(current_date)
                current_date += timedelta(days=7)
        
        elif timing_pattern.pattern_type == 'bi_weekly':
            # Bi-weekly pattern - every 14 days, same day of week
            target_weekday = timing_pattern.day_of_week if timing_pattern.day_of_week is not None else last_date.weekday()
            
            # Find next occurrence of target weekday
            days_ahead = (target_weekday - current_date.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 14  # Skip to next bi-weekly occurrence
            
            current_date += timedelta(days=days_ahead)
            
            while current_date <= end_date:
                forecast_dates.append(current_date)
                current_date += timedelta(days=14)
        
        elif timing_pattern.pattern_type == 'monthly':
            # Monthly pattern - same day of month
            target_day = timing_pattern.day_of_month if timing_pattern.day_of_month is not None else last_date.day
            
            # Move to next month
            if current_date.month == 12:
                next_month = current_date.replace(year=current_date.year + 1, month=1)
            else:
                next_month = current_date.replace(month=current_date.month + 1)
            
            # Adjust for target day
            try:
                current_date = next_month.replace(day=target_day)
            except ValueError:
                # Handle end-of-month cases (e.g., Feb 30 -> Feb 28)
                last_day = calendar.monthrange(next_month.year, next_month.month)[1]
                current_date = next_month.replace(day=min(target_day, last_day))
            
            while current_date <= end_date:
                forecast_dates.append(current_date)
                
                # Move to next month
                if current_date.month == 12:
                    next_month = current_date.replace(year=current_date.year + 1, month=1, day=1)
                else:
                    next_month = current_date.replace(month=current_date.month + 1, day=1)
                
                try:
                    current_date = next_month.replace(day=target_day)
                except ValueError:
                    last_day = calendar.monthrange(next_month.year, next_month.month)[1]
                    current_date = next_month.replace(day=min(target_day, last_day))
        
        elif timing_pattern.pattern_type == 'quarterly':
            # Quarterly pattern - every 3 months
            while current_date <= end_date:
                # Move to next quarter
                if current_date.month <= 3:
                    current_date = current_date.replace(month=4)
                elif current_date.month <= 6:
                    current_date = current_date.replace(month=7)
                elif current_date.month <= 9:
                    current_date = current_date.replace(month=10)
                else:
                    current_date = current_date.replace(year=current_date.year + 1, month=1)
                
                if current_date <= end_date:
                    forecast_dates.append(current_date)
        
        else:
            # Irregular pattern - use average frequency
            frequency_days = timing_pattern.frequency_days if timing_pattern.frequency_days > 0 else 30
            
            while current_date <= end_date:
                current_date += timedelta(days=frequency_days)
                forecast_dates.append(current_date)
        
        return forecast_dates
    
    def save_forecasts_to_database(self, forecasts: List[ForecastRecord], client_id: str):
        """Save generated forecasts to database"""
        print(f"\n💾 SAVING FORECASTS TO DATABASE")
        print("=" * 80)
        
        # Clear existing auto-generated forecasts for this client
        supabase.table('forecasts').delete().eq('client_id', client_id).eq('forecast_method', 'auto').execute()
        
        # Prepare forecast records for database
        forecast_records = []
        for forecast in forecasts:
            record = {
                'client_id': client_id,
                'vendor_group_name': forecast.vendor_name,  # Using vendor_group_name column
                'forecast_date': forecast.forecast_date.isoformat(),
                'forecast_amount': forecast.predicted_amount,  # Using forecast_amount column
                'forecast_type': 'scheduled',  # Type of forecast
                'forecast_method': 'auto',  # How it was generated
                'pattern_confidence': forecast.confidence,  # Confidence score
                'is_locked': False,  # Not locked by default
                'is_manual_override': False  # Not a manual override
            }
            forecast_records.append(record)
        
        # Batch insert forecasts
        if forecast_records:
            supabase.table('forecasts').insert(forecast_records).execute()
            print(f"✅ Saved {len(forecast_records)} forecast records to database")
        else:
            print("⚠️ No forecasts to save")
    
    def print_forecast_summary(self, forecasts: List[ForecastRecord]):
        """Print formatted forecast summary"""
        
        if not forecasts:
            print("No forecasts generated")
            return
        
        # Group by vendor
        vendor_forecasts = {}
        for forecast in forecasts:
            if forecast.vendor_name not in vendor_forecasts:
                vendor_forecasts[forecast.vendor_name] = []
            vendor_forecasts[forecast.vendor_name].append(forecast)
        
        print(f"\n📊 FORECAST SUMMARY")
        print("=" * 80)
        
        for vendor_name, vendor_forecasts_list in vendor_forecasts.items():
            total_amount = sum(f.predicted_amount for f in vendor_forecasts_list)
            avg_confidence = sum(f.confidence for f in vendor_forecasts_list) / len(vendor_forecasts_list)
            
            print(f"\n├── {vendor_name}")
            print(f"│   ├── {len(vendor_forecasts_list)} forecast events")
            print(f"│   ├── ${total_amount:,.0f} total predicted")
            print(f"│   ├── {avg_confidence:.1%} average confidence")
            print(f"│   └── Next: {vendor_forecasts_list[0].forecast_date} (${vendor_forecasts_list[0].predicted_amount:,.0f})")

def main():
    """Test the auto-forecast generator"""
    generator = AutoForecastGenerator()
    
    print("🔮 AUTO-FORECAST GENERATOR TEST")
    print("=" * 80)
    
    # Generate forecasts
    forecasts = generator.generate_auto_forecasts('spyguy')
    
    # Print summary
    generator.print_forecast_summary(forecasts)
    
    # Save to database
    generator.save_forecasts_to_database(forecasts, 'spyguy')
    
    print(f"\n🎯 COMPLETION STATUS")
    print(f"Auto-forecasting complete for predictable vendors")
    print(f"Next: Create manual setup interface for irregular vendors")
    
    return forecasts

if __name__ == "__main__":
    main()