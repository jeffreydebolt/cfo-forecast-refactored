#!/usr/bin/env python3
"""
Check the forecast database to see what was stored.
"""

import sys
sys.path.append('.')

from database.forecast_db_manager import forecast_db
from supabase_client import supabase
from datetime import date, timedelta

def check_stored_forecasts():
    """Check what forecasts are stored in the database."""
    print("🔍 CHECKING STORED FORECASTS IN DATABASE")
    print("=" * 60)
    
    client_id = 'bestself'
    
    try:
        # Check vendor groups
        vendor_groups = forecast_db.get_vendor_groups(client_id)
        print(f"📊 Vendor Groups: {len(vendor_groups)}")
        
        for group in vendor_groups:
            pattern_freq = group.get('pattern_frequency', 'N/A')
            pattern_timing = group.get('pattern_timing', 'N/A')
            confidence = group.get('pattern_confidence', 0.0)
            amount = group.get('weighted_average_amount', 0.0)
            
            print(f"  • {group['group_name']}")
            print(f"    Pattern: {pattern_freq} ({pattern_timing})")
            print(f"    Amount: ${amount:,.2f} (confidence: {confidence:.2f})")
        
        # Check forecasts
        start_date = date(2025, 8, 1)
        end_date = date(2025, 8, 31)
        
        forecasts = forecast_db.get_forecasts(client_id, start_date, end_date)
        print(f"\n📅 Forecasts for August 2025: {len(forecasts)}")
        
        # Group by week
        week_of_8_4 = date(2025, 8, 4)
        week_end = week_of_8_4 + timedelta(days=6)
        
        week_forecasts = []
        for f in forecasts:
            forecast_date = date.fromisoformat(f['forecast_date'])
            if week_of_8_4 <= forecast_date <= week_end:
                week_forecasts.append(f)
        
        print(f"\n🎯 Week of 8/4/25 Forecasts: {len(week_forecasts)}")
        
        if week_forecasts:
            week_total = 0
            for f in week_forecasts:
                amount = float(f['forecast_amount'])
                week_total += amount
                forecast_date = date.fromisoformat(f['forecast_date'])
                print(f"  {forecast_date} ({forecast_date.strftime('%A')}): {f['vendor_group_name']} - ${amount:,.2f}")
            
            print(f"\n💰 Week Total: ${week_total:,.2f}")
        else:
            print("❌ No forecasts found for week of 8/4/25")
            
            # Check if there are any forecasts at all
            all_forecasts = supabase.table('forecasts').select('*').eq('client_id', client_id).execute()
            print(f"📊 Total forecast records in database: {len(all_forecasts.data)}")
            
            if all_forecasts.data:
                print("Sample forecast records:")
                for f in all_forecasts.data[:5]:
                    print(f"  {f['forecast_date']}: {f['vendor_group_name']} - ${float(f['forecast_amount']):,.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking forecasts: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function."""
    print("🚀 FORECAST DATABASE CHECK")
    print("=" * 70)
    
    check_stored_forecasts()

if __name__ == "__main__":
    main()