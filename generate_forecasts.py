#!/usr/bin/env python3
"""
Generate forecast records from vendor group patterns
"""

import sys
import argparse
from datetime import datetime, date, timedelta

sys.path.append('.')

from supabase_client import supabase

def generate_forecasts(client_id: str, weeks: int = 13):
    """Generate forecast records for client"""
    print(f"📈 GENERATING FORECASTS")
    print(f"Client: {client_id}")
    print(f"Horizon: {weeks} weeks")
    print("=" * 80)
    
    # Get vendor groups with patterns
    groups = supabase.table('vendor_groups')\
        .select('*')\
        .eq('client_id', client_id)\
        .eq('is_active', True)\
        .execute()
    
    if not groups.data:
        print("❌ No vendor groups found")
        return
    
    print(f"📊 Found {len(groups.data)} vendor groups")
    
    # Clear existing forecasts
    supabase.table('forecasts')\
        .delete()\
        .eq('client_id', client_id)\
        .execute()
    print("🗑️ Cleared existing forecasts")
    
    # Generate forecasts
    forecast_records = []
    start_date = date.today()
    end_date = start_date + timedelta(weeks=weeks)
    
    for group in groups.data:
        group_name = group['group_name']
        pattern = group.get('pattern_frequency', 'monthly')
        amount = float(group.get('weighted_average_amount', 0))
        
        print(f"\n📋 {group_name}: {pattern} pattern, ${amount:,.0f}")
        
        # Generate dates based on pattern
        forecast_dates = []
        current_date = start_date
        
        if pattern == 'daily':
            # Skip weekends for daily patterns
            while current_date <= end_date:
                if current_date.weekday() < 5:  # Monday=0, Friday=4
                    forecast_dates.append(current_date)
                current_date += timedelta(days=1)
        
        elif pattern == 'weekly':
            # Every Monday
            while current_date <= end_date:
                if current_date.weekday() == 0:  # Monday
                    forecast_dates.append(current_date)
                current_date += timedelta(days=1)
        
        elif pattern == 'bi-weekly':
            # Every other Monday
            while current_date <= end_date:
                if current_date.weekday() == 0:  # Monday
                    forecast_dates.append(current_date)
                    current_date += timedelta(days=14)
                else:
                    current_date += timedelta(days=1)
        
        elif pattern == 'monthly':
            # First business day of each month
            while current_date <= end_date:
                if current_date.day == 1 or (current_date.day <= 3 and current_date.weekday() == 0):
                    forecast_dates.append(current_date)
                    # Jump to next month
                    if current_date.month == 12:
                        current_date = current_date.replace(year=current_date.year + 1, month=1, day=1)
                    else:
                        current_date = current_date.replace(month=current_date.month + 1, day=1)
                else:
                    current_date += timedelta(days=1)
        
        # Create forecast records
        for forecast_date in forecast_dates:
            record = {
                'client_id': client_id,
                'vendor_group_name': group_name,
                'forecast_date': forecast_date.isoformat(),
                'forecast_amount': amount,
                'forecast_type': pattern,
                'forecast_method': 'weighted_average',
                'pattern_confidence': float(group.get('pattern_confidence', 0.75)),
                'is_manual_override': False,
                'created_at': datetime.now().isoformat()
            }
            forecast_records.append(record)
        
        print(f"   ✅ Generated {len(forecast_dates)} forecast entries")
    
    # Save all forecasts
    if forecast_records:
        # Save in batches
        batch_size = 100
        saved = 0
        
        for i in range(0, len(forecast_records), batch_size):
            batch = forecast_records[i:i + batch_size]
            try:
                supabase.table('forecasts').insert(batch).execute()
                saved += len(batch)
            except Exception as e:
                print(f"❌ Error saving batch: {str(e)}")
                break
        
        print(f"\n✅ FORECAST GENERATION COMPLETE!")
        print(f"📊 Saved {saved} forecast records")
        
        # Show summary by group
        print(f"\n📈 FORECAST SUMMARY:")
        print("-" * 60)
        for group in groups.data:
            group_name = group['group_name']
            group_forecasts = [f for f in forecast_records if f['vendor_group_name'] == group_name]
            total_amount = sum(f['forecast_amount'] for f in group_forecasts)
            print(f"{group_name}: {len(group_forecasts)} entries, ${total_amount:,.0f} total")
    
    else:
        print("❌ No forecast records generated")

def main():
    parser = argparse.ArgumentParser(description='Generate forecast records')
    parser.add_argument('--client', required=True, help='Client ID')
    parser.add_argument('--weeks', type=int, default=13, help='Forecast horizon in weeks')
    args = parser.parse_args()
    
    generate_forecasts(args.client, args.weeks)

if __name__ == "__main__":
    main()