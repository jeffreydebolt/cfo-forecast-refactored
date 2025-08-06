#!/usr/bin/env python3
import sys
import csv
sys.path.append('.')
from supabase_client import supabase
from datetime import datetime, date

print('EXPORTING FORECAST DATA TO CSV')
print('Client: BestSelf') 
print('=' * 60)

# Export 1: Vendor Groups Summary
print('📊 Exporting vendor groups summary...')
with open('bestself_vendor_groups.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Group Type', 'Group Name', 'Vendor Count', 'Sample Vendors'])
    
    # Auto-mapped groups
    auto_vendors = supabase.table('vendors').select('*').eq('client_id', 'BestSelf').execute()
    auto_groups = {}
    for vendor in auto_vendors.data:
        display_name = vendor['display_name']
        if not display_name.startswith('[UNMAPPED]'):
            if display_name not in auto_groups:
                auto_groups[display_name] = []
            auto_groups[display_name].append(vendor['vendor_name'])
    
    for group_name, vendors in auto_groups.items():
        sample = ', '.join(vendors[:3]) + ('...' if len(vendors) > 3 else '')
        writer.writerow(['AUTO', group_name, len(vendors), sample])
    
    # Manual groups
    manual_groups = supabase.table('vendor_groups').select('*').eq('client_id', 'BestSelf').execute()
    for group in manual_groups.data:
        vendors = group['vendor_display_names']
        sample = ', '.join(vendors[:3]) + ('...' if len(vendors) > 3 else '')
        writer.writerow(['MANUAL', group['group_name'], len(vendors), sample])

print('✅ Created: bestself_vendor_groups.csv')

# Export 2: 13-Week Forecast
print('📊 Exporting 13-week forecast...')
forecasts = supabase.table('forecasts').select('*').eq('client_id', 'BestSelf').order('forecast_date').execute()

with open('bestself_13week_forecast.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Date', 'Group Name', 'Amount', 'Frequency', 'Method', 'Confidence'])
    
    for forecast in forecasts.data:
        writer.writerow([
            forecast['forecast_date'],
            forecast['vendor_group_name'],
            forecast['forecast_amount'],
            forecast['forecast_type'],
            forecast['forecast_method'],
            forecast.get('pattern_confidence', 0)
        ])

print('✅ Created: bestself_13week_forecast.csv')

# Export 3: Weekly Summary
print('📊 Exporting weekly summary...')
from collections import defaultdict

weekly_totals = defaultdict(float)
weekly_by_group = defaultdict(lambda: defaultdict(float))

start_date = date.today()
for forecast in forecasts.data:
    forecast_date = datetime.fromisoformat(forecast['forecast_date']).date()
    week_diff = (forecast_date - start_date).days // 7
    if 0 <= week_diff < 13:
        week_key = f"Week {week_diff + 1}"
        amount = float(forecast['forecast_amount'])
        group = forecast['vendor_group_name']
        
        weekly_totals[week_key] += amount
        weekly_by_group[week_key][group] += amount

with open('bestself_weekly_summary.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    
    # Get all unique groups
    all_groups = set()
    for week_groups in weekly_by_group.values():
        all_groups.update(week_groups.keys())
    
    header = ['Week'] + sorted(all_groups) + ['Weekly Total']
    writer.writerow(header)
    
    for week in range(1, 14):
        week_key = f"Week {week}"
        row = [week_key]
        
        for group in sorted(all_groups):
            amount = weekly_by_group[week_key].get(group, 0)
            row.append(f"${amount:,.0f}" if amount != 0 else "")
        
        row.append(f"${weekly_totals[week_key]:,.0f}")
        writer.writerow(row)

print('✅ Created: bestself_weekly_summary.csv')

# Export 4: Unmapped Vendors (need manual review)
print('📊 Exporting unmapped vendors...')
unmapped = supabase.table('vendors').select('*').eq('client_id', 'BestSelf').like('display_name', '[UNMAPPED]%').execute()

with open('bestself_unmapped_vendors.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Vendor Name', 'Category', 'Created At'])
    
    for vendor in unmapped.data:
        writer.writerow([
            vendor['vendor_name'].replace('[UNMAPPED] ', ''),
            vendor.get('category', ''),
            vendor.get('created_at', '')
        ])

print('✅ Created: bestself_unmapped_vendors.csv')

print('\n🎉 ALL CSV FILES EXPORTED!')
print('📁 Files created:')
print('   - bestself_vendor_groups.csv (group summary)')  
print('   - bestself_13week_forecast.csv (daily forecast records)')
print('   - bestself_weekly_summary.csv (weekly pivot table)')
print('   - bestself_unmapped_vendors.csv (vendors needing review)')
print('\nOpen these in Excel/Google Sheets to review and adjust!')