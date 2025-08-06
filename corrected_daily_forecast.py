#!/usr/bin/env python3
import sys
import os
import tempfile
import webbrowser
sys.path.append('.')
from supabase_client import supabase
from datetime import datetime, date, timedelta

print('CORRECTED DAILY FORECAST - ONLY YOUR MANUAL GROUPS')
print('Client: BestSelf') 
print('=' * 60)

# Get ONLY the vendor groups YOU manually created
manual_groups = supabase.table('vendor_groups').select('*').eq('client_id', 'BestSelf').execute()
print(f'✅ Found {len(manual_groups.data)} manual groups you created')

for group in manual_groups.data:
    print(f'   - {group["group_name"]}: {len(group["vendor_display_names"])} vendors')

# Clear existing forecasts
print('🗑️ Clearing existing forecasts...')
supabase.table('forecasts').delete().eq('client_id', 'BestSelf').execute()

# Generate forecasts ONLY for your manual groups
forecast_records = []
start_date = date.today()
end_date = start_date + timedelta(weeks=13)

print(f'📅 Generating forecasts from {start_date} to {end_date}')

for group in manual_groups.data:
    group_name = group['group_name']
    vendor_list = group['vendor_display_names']
    
    # Get pattern analysis for this group
    pattern = supabase.table('pattern_analysis').select('*')\
        .eq('client_id', 'BestSelf')\
        .eq('vendor_group_name', group_name)\
        .execute()
    
    if not pattern.data:
        print(f'⚠️ No pattern found for {group_name} - skipping')
        continue
    
    pattern_data = pattern.data[0]
    frequency = pattern_data.get('frequency_detected', 'monthly')
    amount = float(pattern_data.get('average_amount', 0))
    confidence = pattern_data.get('confidence_score', 0.5)
    
    print(f'\n📊 {group_name}: {frequency} @ ${amount:,.0f}')
    
    current_date = start_date
    group_forecasts = 0
    
    while current_date <= end_date:
        should_forecast = False
        
        if frequency == 'daily':
            should_forecast = True
        elif frequency == 'weekly' and current_date.weekday() == 0:  # Mondays
            should_forecast = True
        elif frequency == 'monthly' and current_date.day == 1:  # First of month
            should_forecast = True
        
        if should_forecast:
            forecast_records.append({
                'client_id': 'BestSelf',
                'vendor_group_name': group_name,
                'forecast_date': current_date.isoformat(),
                'forecast_amount': amount,
                'forecast_type': frequency,
                'forecast_method': 'manual_group_pattern',
                'pattern_confidence': confidence,
                'created_at': datetime.now().isoformat()
            })
            group_forecasts += 1
        
        current_date += timedelta(days=1)
    
    print(f'   ✅ Generated {group_forecasts} forecast records')

# Show ungrouped vendors (ones not in your manual groups)
all_grouped_vendors = []
for group in manual_groups.data:
    all_grouped_vendors.extend(group['vendor_display_names'])

ungrouped_vendors = supabase.table('transactions').select('vendor_name')\
    .eq('client_id', 'BestSelf')\
    .execute()

unique_vendors = set(txn['vendor_name'] for txn in ungrouped_vendors.data)
ungrouped = [v for v in unique_vendors if v not in all_grouped_vendors]

print(f'\n📋 UNGROUPED VENDORS: {len(ungrouped)} vendors not in your groups')
for vendor in sorted(ungrouped)[:10]:  # Show first 10
    print(f'   - {vendor}')
if len(ungrouped) > 10:
    print(f'   ... and {len(ungrouped) - 10} more ungrouped vendors')

# Save forecasts to database
if forecast_records:
    supabase.table('forecasts').insert(forecast_records).execute()
    print(f'\n💾 Saved {len(forecast_records)} forecast records to database')

# Create HTML display
temp_dir = tempfile.mkdtemp()
display_file = os.path.join(temp_dir, 'BestSelf_corrected_forecast.html')

total_net_flow = sum(f['forecast_amount'] for f in forecast_records)

html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Corrected Daily Forecast - BestSelf</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50">
    <div class="container mx-auto p-6">
        <h1 class="text-2xl font-bold mb-6">📈 Daily Forecast - BestSelf (Manual Groups Only)</h1>
        <p class="mb-4">Generated from {len(forecast_records)} forecast records</p>
        <p class="mb-4">Using only your {len(manual_groups.data)} manually created groups</p>
        
        <div class="bg-white p-6 rounded-lg shadow mb-6">
            <h2 class="text-lg font-semibold mb-4">Manual Groups Summary</h2>'''

for group in manual_groups.data:
    html += f'''
            <div class="mb-2">
                <strong>{group['group_name']}:</strong> {len(group['vendor_display_names'])} vendors
                <span class="text-sm text-gray-500">({", ".join(group['vendor_display_names'][:3])}{" ..." if len(group['vendor_display_names']) > 3 else ""})</span>
            </div>'''

html += f'''
        </div>
        
        <div class="bg-white p-6 rounded-lg shadow mb-6">
            <h2 class="text-lg font-semibold mb-4">Forecast Summary</h2>
            <p>Total forecasted flow: ${total_net_flow:,.0f}</p>
            <p>Ungrouped vendors: {len(ungrouped)} (not forecasted)</p>
        </div>
        
        <div class="bg-white p-6 rounded-lg shadow">
            <h2 class="text-lg font-semibold mb-4">Daily Forecast Records</h2>
            <div class="overflow-x-auto">
                <table class="w-full text-sm">
                    <thead>
                        <tr class="border-b">
                            <th class="text-left p-2">Date</th>
                            <th class="text-left p-2">Manual Group</th>
                            <th class="text-right p-2">Amount</th>
                            <th class="text-left p-2">Pattern</th>
                        </tr>
                    </thead>
                    <tbody>'''

# Sort forecast records by date
forecast_records.sort(key=lambda x: x['forecast_date'])

for forecast in forecast_records:
    amount_color = 'text-green-600' if forecast['forecast_amount'] > 0 else 'text-red-600'
    html += f'''
                        <tr class="border-b hover:bg-gray-50">
                            <td class="p-2">{forecast['forecast_date']}</td>
                            <td class="p-2 font-medium">{forecast['vendor_group_name']}</td>
                            <td class="p-2 text-right {amount_color}">${forecast['forecast_amount']:,.0f}</td>
                            <td class="p-2">{forecast['forecast_type']}</td>
                        </tr>'''

html += f'''
                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="mt-6 bg-yellow-50 p-4 rounded border border-yellow-200">
            <h3 class="font-semibold text-yellow-800">Note: Ungrouped Vendors</h3>
            <p class="text-yellow-700">You have {len(ungrouped)} vendors that are not in your manual groups. These are not included in the forecast.</p>
            <p class="text-yellow-700">Create additional groups or individual forecasts for these vendors if needed.</p>
        </div>
    </div>
</body>
</html>'''

with open(display_file, 'w') as f:
    f.write(html)

print(f'\n📊 Created corrected daily forecast: {display_file}')
print(f'🌐 Opening in browser...')
webbrowser.open(f'file://{display_file}')

print('\n✅ CORRECTED DAILY FORECAST READY!')
print(f'📈 Only using your {len(manual_groups.data)} manual groups - no automated grouping')
print(f'⚠️ {len(ungrouped)} ungrouped vendors not forecasted')