#!/usr/bin/env python3
"""
Migrate to V2 Forecasting System
Smoothly transition from old forecast service to new pattern-based system.
"""

import sys
sys.path.append('.')

from services.forecast_service_v2 import forecast_service_v2
from datetime import date, timedelta

def test_v2_service():
    """Test the V2 forecast service."""
    print("🧪 TESTING V2 FORECAST SERVICE")
    print("=" * 60)
    
    client_id = 'bestself'
    
    try:
        # Step 1: Get or create vendor groups
        print("\n1️⃣ CHECKING VENDOR GROUPS...")
        vendor_groups = forecast_service_v2.get_or_create_vendor_groups(client_id)
        print(f"✅ Found/created {len(vendor_groups)} vendor groups")
        
        # Step 2: Run pattern detection
        print("\n2️⃣ RUNNING PATTERN DETECTION...")
        pattern_result = forecast_service_v2.detect_all_patterns(client_id)
        print(f"✅ Processed {pattern_result['processed']} groups")
        print(f"✅ Successfully detected patterns for {pattern_result['successful']} groups")
        
        # Step 3: Generate forecasts
        print("\n3️⃣ GENERATING FORECASTS...")
        start_date = date(2025, 8, 4)
        forecast_result = forecast_service_v2.generate_all_forecasts(
            client_id, start_date=start_date, weeks_ahead=13
        )
        print(f"✅ Generated {forecast_result['generated']} forecast records")
        
        # Step 4: Test retrieval for UI
        print("\n4️⃣ TESTING FORECAST RETRIEVAL...")
        end_date = start_date + timedelta(weeks=2)
        calendar_events = forecast_service_v2.get_calendar_forecasts(
            client_id, start_date, end_date
        )
        print(f"✅ Retrieved {len(calendar_events)} calendar events")
        
        # Show sample events
        if calendar_events:
            print("\nSample forecast events:")
            for event in calendar_events[:5]:
                print(f"  {event.date}: {event.vendor_name} - ${event.amount:,.2f} ({event.frequency})")
        
        # Step 5: Test summary
        print("\n5️⃣ TESTING FORECAST SUMMARY...")
        summary = forecast_service_v2.get_forecast_summary(
            client_id, start_date, start_date + timedelta(weeks=13)
        )
        
        if 'error' not in summary:
            print(f"✅ Total forecast amount: ${summary['total_amount']:,.2f}")
            print(f"✅ Forecast records: {summary['forecast_count']}")
            print(f"✅ Vendor groups: {len(summary['vendor_groups'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing V2 service: {e}")
        import traceback
        traceback.print_exc()
        return False

def update_main_py():
    """Show how to update main.py to use V2 service."""
    print("\n📝 UPDATE INSTRUCTIONS FOR main.py")
    print("=" * 60)
    
    print("""
To integrate V2 forecasting into main.py:

1. Import the new service:
   ```python
   from services.forecast_service_v2 import forecast_service_v2
   ```

2. Replace forecast generation calls:
   
   OLD:
   ```python
   from services.forecast_service import ForecastService
   forecast_service = ForecastService()
   events = forecast_service.generate_calendar_forecast(client_id)
   ```
   
   NEW:
   ```python
   from services.forecast_service_v2 import forecast_service_v2
   events = forecast_service_v2.generate_calendar_forecast(client_id)
   ```

3. Add new commands for pattern detection:
   ```python
   def cmd_detect_patterns(args):
       client_id = args.client_id
       result = forecast_service_v2.detect_all_patterns(client_id)
       print(f"Detected patterns for {result['successful']} vendor groups")
   
   def cmd_generate_forecasts(args):
       client_id = args.client_id
       result = forecast_service_v2.generate_all_forecasts(client_id, weeks_ahead=13)
       print(f"Generated {result['generated']} forecast records")
   ```

4. The calendar view and forecast display will work automatically since
   we maintain backward compatibility with ForecastEvent objects.
""")

def show_ui_integration():
    """Show how the UI can access the new features."""
    print("\n🖥️  UI INTEGRATION POINTS")
    print("=" * 60)
    
    print("""
The V2 service provides these UI integration points:

1. **Vendor Group Management**
   - List vendor groups: `forecast_service_v2.db.get_vendor_groups(client_id)`
   - Create/edit groups: `forecast_service_v2.db.create_vendor_group(...)`
   - View patterns: Shows frequency, timing, confidence

2. **Pattern Analysis View**
   - Pattern history: Query `pattern_analysis` table
   - Confidence scores: Displayed with each forecast
   - Timing details: "Tuesdays", "15th of month", etc.

3. **Manual Overrides**
   - Override forecast: `forecast_service_v2.update_manual_forecast(...)`
   - Overrides are stored in database and marked clearly

4. **Forecast Summary**
   - Weekly/monthly totals: `forecast_service_v2.get_forecast_summary(...)`
   - By vendor group breakdown
   - Actual vs forecast comparison (when actuals imported)

5. **Data Export**
   - All forecast data is in structured database tables
   - Easy to export to CSV, Excel, etc.
""")

def main():
    """Main migration function."""
    print("🚀 MIGRATING TO V2 FORECASTING SYSTEM")
    print("=" * 70)
    
    # Test the V2 service
    if test_v2_service():
        print("\n✅ V2 FORECAST SERVICE IS WORKING!")
        
        # Show integration instructions
        update_main_py()
        show_ui_integration()
        
        print("\n🎉 MIGRATION GUIDE COMPLETE!")
        print("The V2 service is ready for integration.")
    else:
        print("\n❌ V2 service test failed. Please check the error messages above.")

if __name__ == "__main__":
    main()