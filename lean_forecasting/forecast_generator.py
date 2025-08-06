#!/usr/bin/env python3
"""
Forecast Generator - Creates individual date records for forecasts.
Follows the exact specification in FORECASTING_LOGIC_CORE_REQUIREMENTS.md
"""

import sys
sys.path.append('.')

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, date, timedelta
from lean_forecasting.group_pattern_detector import group_pattern_detector

logger = logging.getLogger(__name__)

class ForecastGenerator:
    """Generates individual forecast records for vendor groups."""
    
    def __init__(self):
        pass
    
    def generate_forecast_dates(self, pattern: Dict[str, Any], 
                              start_date: Optional[date] = None,
                              weeks_ahead: int = 13) -> List[date]:
        """Generate list of forecast dates based on pattern."""
        if start_date is None:
            start_date = date.today()
        
        frequency = pattern['frequency']
        timing = pattern.get('timing', 'unknown')
        
        forecast_dates = []
        
        if frequency == 'daily':
            # For daily patterns, generate weekly dates (since we calculate weekly amounts)
            # Use Monday as the weekly forecast date
            for week in range(weeks_ahead):
                # Find Monday of each week
                days_ahead = (0 - start_date.weekday()) % 7  # 0 = Monday
                if days_ahead == 0 and start_date.weekday() == 0:
                    days_ahead = 0  # Start today if it's Monday
                
                forecast_date = start_date + timedelta(days=days_ahead + (week * 7))
                forecast_dates.append(forecast_date)
        
        elif frequency == 'weekly':
            # Generate weekly dates on specific weekday
            preferred_weekday = pattern.get('weekday', 0)  # Default Monday
            
            # Find next occurrence of the preferred weekday
            days_ahead = (preferred_weekday - start_date.weekday()) % 7
            if days_ahead == 0 and start_date.weekday == preferred_weekday:
                days_ahead = 0  # Start today if it's the right day
            
            for week in range(weeks_ahead):
                forecast_date = start_date + timedelta(days=days_ahead + (week * 7))
                forecast_dates.append(forecast_date)
        
        elif frequency == 'bi-weekly':
            # Generate bi-weekly dates on specific weekday
            preferred_weekday = pattern.get('weekday', 1)  # Default Tuesday (Amazon pattern)
            
            # Find next occurrence of the preferred weekday
            days_ahead = (preferred_weekday - start_date.weekday()) % 7
            if days_ahead == 0 and start_date.weekday() == preferred_weekday:
                days_ahead = 0  # Start today if it's the right day
            
            # Generate bi-weekly dates (every 14 days)
            weeks_to_generate = (weeks_ahead // 2) + 2  # Extra dates to cover 13 weeks
            for period in range(weeks_to_generate):
                forecast_date = start_date + timedelta(days=days_ahead + (period * 14))
                
                # Only include dates within the next 13+ weeks
                if forecast_date <= start_date + timedelta(weeks=weeks_ahead):
                    forecast_dates.append(forecast_date)
        
        elif frequency == 'monthly':
            # Generate monthly dates on specific day of month
            preferred_day = pattern.get('day_of_month', 15)  # Default 15th
            
            months_to_generate = (weeks_ahead // 4) + 2  # Approximate months
            current_date = start_date.replace(day=min(preferred_day, 28))  # Avoid day overflow
            
            for month in range(months_to_generate):
                try:
                    if month == 0:
                        forecast_date = current_date
                    else:
                        # Add month (handle year rollover)
                        year = current_date.year + ((current_date.month + month - 1) // 12)
                        month_val = ((current_date.month + month - 1) % 12) + 1
                        forecast_date = date(year, month_val, preferred_day)
                    
                    # Only include dates within the next 13+ weeks
                    if forecast_date <= start_date + timedelta(weeks=weeks_ahead):
                        forecast_dates.append(forecast_date)
                        
                except ValueError:
                    # Handle day overflow (e.g., Feb 30th)
                    continue
        
        else:  # irregular or unknown
            # For irregular patterns, generate quarterly estimates 
            # This ensures they appear in the dashboard even if unpredictable
            if frequency == 'irregular':
                for quarter in range(4):  # Generate quarterly estimates
                    forecast_date = start_date + timedelta(days=quarter * 90)  # Every ~3 months
                    if forecast_date <= start_date + timedelta(weeks=weeks_ahead):
                        forecast_dates.append(forecast_date)
        
        return sorted(forecast_dates)
    
    def generate_vendor_group_forecast(self, client_id: str, vendor_group_name: str,
                                     display_names: List[str], weeks_ahead: int = 13,
                                     start_date: Optional[date] = None) -> List[Dict[str, Any]]:
        """Generate complete forecast for a vendor group."""
        print(f"\n🔮 GENERATING FORECAST FOR GROUP: {vendor_group_name}")
        print("=" * 60)
        
        # Step 1: Analyze pattern
        pattern = group_pattern_detector.analyze_vendor_group_pattern(
            client_id, vendor_group_name, display_names
        )
        
        if pattern['weighted_average'] == 0:
            print(f"⚠️  No forecast generated - zero amount")
            return []
        
        if pattern['frequency'] == 'irregular':
            print(f"⚠️  Irregular pattern detected - generating quarterly forecast estimate")
            print(f"   Average amount: ${pattern['weighted_average']:.2f}")
            print(f"   Will generate quarterly forecasts to capture the variance")
        
        # Step 2: Generate forecast dates
        forecast_dates = self.generate_forecast_dates(pattern, start_date, weeks_ahead)
        
        if not forecast_dates:
            print(f"⚠️  No forecast dates generated")
            return []
        
        print(f"Generated {len(forecast_dates)} forecast dates")
        print(f"Pattern: {pattern['frequency']} on {pattern['timing']}s")
        print(f"Amount: ${pattern['weighted_average']:.2f} per occurrence")
        
        # Step 3: Create individual forecast records
        forecast_records = []
        
        for forecast_date in forecast_dates:
            record = {
                'client_id': client_id,
                'vendor_group_name': vendor_group_name,
                'forecast_date': forecast_date,
                'forecast_amount': pattern['weighted_average'],
                'forecast_type': pattern['frequency'],
                'forecast_method': 'weighted_average',
                'pattern_confidence': pattern['frequency_confidence'],
                'created_at': datetime.now(),
                'display_names_included': display_names,
                'timing': pattern['timing']
            }
            forecast_records.append(record)
        
        print(f"✅ Created {len(forecast_records)} individual forecast records")
        
        # Show sample dates
        if forecast_records:
            print(f"\n📅 SAMPLE FORECAST DATES:")
            for i, record in enumerate(forecast_records[:5]):  # Show first 5
                date_obj = record['forecast_date']
                day_name = date_obj.strftime('%A')
                print(f"{date_obj} ({day_name}): ${record['forecast_amount']:.2f}")
            
            if len(forecast_records) > 5:
                print(f"... and {len(forecast_records) - 5} more dates")
        
        return forecast_records
    
    def show_forecast_for_week(self, forecast_records: List[Dict[str, Any]], 
                             target_week_start: date) -> Dict[str, Any]:
        """Show forecast for a specific week."""
        print(f"\n📊 FORECAST FOR WEEK OF {target_week_start}")
        print("=" * 60)
        
        week_end = target_week_start + timedelta(days=6)
        week_forecasts = [
            record for record in forecast_records 
            if target_week_start <= record['forecast_date'] <= week_end
        ]
        
        if not week_forecasts:
            print("❌ No forecasts for this week")
            return {'total': 0, 'forecasts': []}
        
        # Show vendor group info
        if week_forecasts:
            sample_record = week_forecasts[0]
            print(f"📋 VENDOR GROUP: {sample_record['vendor_group_name']}")
            print(f"   Display Names: {', '.join(sample_record['display_names_included'])}")
            print(f"   Pattern: {sample_record['forecast_type']} on {sample_record['timing']}s")
            print(f"   Confidence: {sample_record['pattern_confidence']:.2f}")
            print()
        
        total_week_amount = 0
        for record in week_forecasts:
            forecast_date = record['forecast_date']
            day_name = forecast_date.strftime('%A')
            amount = record['forecast_amount']
            print(f"{forecast_date} ({day_name}): ${amount:.2f} ({record['forecast_type']})")
            total_week_amount += amount
        
        print(f"\n💰 TOTAL FOR WEEK: ${total_week_amount:.2f}")
        
        return {
            'total': total_week_amount,
            'forecasts': week_forecasts,
            'vendor_group': sample_record['vendor_group_name'] if week_forecasts else '',
            'pattern': f"{sample_record['forecast_type']} on {sample_record['timing']}s" if week_forecasts else ''
        }

# Global instance
forecast_generator = ForecastGenerator()

def test_amazon_forecast(client_id: str = 'bestself'):
    """Test complete Amazon forecast generation."""
    print("🧪 TESTING AMAZON FORECAST GENERATION")
    print("=" * 60)
    
    # Generate Amazon forecast
    amazon_forecasts = forecast_generator.generate_vendor_group_forecast(
        client_id=client_id,
        vendor_group_name='Amazon',
        display_names=['Amazon Revenue'],
        weeks_ahead=13
    )
    
    if not amazon_forecasts:
        print("❌ No forecasts generated")
        return
    
    # Show forecast for week of 8/4/25 (user's specific request)
    target_date = date(2025, 8, 4)  # Monday, Aug 4, 2025
    
    # Find the Monday of that week
    days_to_monday = target_date.weekday()  # 0 = Monday
    week_start = target_date - timedelta(days=days_to_monday)
    
    week_result = forecast_generator.show_forecast_for_week(amazon_forecasts, week_start)
    
    print(f"\n🎯 VALIDATION FOR WEEK OF 8/4/25:")
    print(f"Expected: bi-weekly Tuesday pattern, ~$44k")
    print(f"Detected: {week_result['pattern']}, ${week_result['total']:.2f}")
    
    # Expected: Amazon deposits on Tuesdays (8/5/25 is a Tuesday)
    expected_amount = 44654.12  # From pattern detection
    actual_amount = week_result['total']
    
    # Check if Tuesday 8/5/25 has a forecast
    tuesday_8_5 = date(2025, 8, 5)
    has_tuesday_forecast = any(
        f['forecast_date'] == tuesday_8_5 for f in week_result['forecasts']
    )
    
    print(f"Has Tuesday 8/5/25 forecast: {'✅' if has_tuesday_forecast else '❌'}")
    print(f"Amount match: {'✅' if abs(actual_amount - expected_amount) < 1000 else '❌'}")
    
    return amazon_forecasts

if __name__ == "__main__":
    test_amazon_forecast()