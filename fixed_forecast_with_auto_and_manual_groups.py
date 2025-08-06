#!/usr/bin/env python3
import sys
import os
import tempfile
import webbrowser
sys.path.append('.')
from supabase_client import supabase
from datetime import datetime, date, timedelta
from core.vendor_auto_mapping import auto_mapper

print('FIXED FORECAST - AUTO GROUPS + YOUR MANUAL GROUPS')
print('Client: BestSelf') 
print('=' * 60)

# Step 1: Run the auto-mapping system to create vendor groups
print('🤖 Running auto-mapping system...')
stats = auto_mapper.bulk_process_vendors('BestSelf')
print(f'   Auto-mapped: {stats["auto_mapped"]} vendors')
print(f'   Needs review: {stats["needs_review"]} vendors')

# Step 2: Get auto-mapped vendor groups (from vendors table)
auto_vendors = supabase.table('vendors').select('*').eq('client_id', 'BestSelf').execute()
print(f'✅ Found {len(auto_vendors.data)} auto-mapped vendors')

# Group auto-mapped vendors by display_name
auto_groups = {}
for vendor in auto_vendors.data:
    display_name = vendor['display_name']
    if not display_name.startswith('[UNMAPPED]'):  # Skip unmapped ones
        vendor_name = vendor['vendor_name']
        if display_name not in auto_groups:
            auto_groups[display_name] = []
        auto_groups[display_name].append(vendor_name)

print(f'📊 Created {len(auto_groups)} auto-groups:')
for group_name, vendors in auto_groups.items():
    print(f'   - {group_name}: {len(vendors)} vendors')

# Step 3: Get your manual groups
manual_groups = supabase.table('vendor_groups').select('*').eq('client_id', 'BestSelf').execute()
print(f'✅ Found {len(manual_groups.data)} manual groups you created:')
for group in manual_groups.data:
    print(f'   - {group["group_name"]}: {len(group["vendor_display_names"])} vendors')

# Step 4: Generate forecasts for BOTH auto-groups AND manual groups
print('\n🔮 Generating forecasts for all groups...')

# Clear existing forecasts
supabase.table('forecasts').delete().eq('client_id', 'BestSelf').execute()

forecast_records = []
start_date = date.today()
end_date = start_date + timedelta(weeks=13)

# Process auto-groups (from regex patterns)
for group_name, vendor_list in auto_groups.items():
    # Get transactions for this auto-group
    transactions = supabase.table('transactions')\
        .select('transaction_date, amount')\
        .eq('client_id', 'BestSelf')\
        .in_('vendor_name', vendor_list)\
        .order('transaction_date')\
        .execute()
    
    if len(transactions.data) < 3:
        print(f'   ⏭️ {group_name}: Insufficient data ({len(transactions.data)} transactions)')
        continue
    
    # Calculate pattern (simplified - using average amount)
    amounts = [abs(float(t['amount'])) for t in transactions.data]
    avg_amount = sum(amounts) / len(amounts)
    
    # Determine frequency based on transaction count (simplified)
    days_span = (datetime.fromisoformat(transactions.data[-1]['transaction_date']).date() - 
                datetime.fromisoformat(transactions.data[0]['transaction_date']).date()).days
    
    if days_span > 0:
        avg_gap = days_span / len(transactions.data)
        if avg_gap < 3:
            frequency = 'daily'
        elif avg_gap < 10:
            frequency = 'weekly' 
        elif avg_gap < 35:
            frequency = 'monthly'
        else:
            frequency = 'irregular'
    else:
        frequency = 'monthly'
    
    print(f'   📊 {group_name}: {frequency} @ ${avg_amount:,.0f} ({len(transactions.data)} transactions)')
    
    # Generate forecast records
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
                'forecast_amount': avg_amount,
                'forecast_type': frequency,
                'forecast_method': 'auto_regex_pattern',
                'pattern_confidence': 0.7,
                'created_at': datetime.now().isoformat()
            })
            group_forecasts += 1
        
        current_date += timedelta(days=1)
    
    print(f'      ✅ Generated {group_forecasts} forecast records')

# Process your manual groups 
for group in manual_groups.data:
    group_name = group['group_name']
    vendor_list = group['vendor_display_names']
    
    # Get pattern analysis for this manual group
    pattern = supabase.table('pattern_analysis').select('*')\
        .eq('client_id', 'BestSelf')\
        .eq('vendor_group_name', group_name)\
        .execute()
    
    if not pattern.data:
        print(f'⚠️ No pattern found for manual group {group_name} - skipping')
        continue
    
    pattern_data = pattern.data[0]
    frequency = pattern_data.get('frequency_detected', 'monthly')
    amount = float(pattern_data.get('average_amount', 0))
    confidence = pattern_data.get('confidence_score', 0.5)
    
    print(f'   📊 {group_name} (MANUAL): {frequency} @ ${amount:,.0f}')
    
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
                'vendor_group_name': f"{group_name} (MANUAL)",
                'forecast_date': current_date.isoformat(),
                'forecast_amount': amount,
                'forecast_type': frequency,
                'forecast_method': 'manual_group_pattern',
                'pattern_confidence': confidence,
                'created_at': datetime.now().isoformat()
            })
            group_forecasts += 1
        
        current_date += timedelta(days=1)
    
    print(f'      ✅ Generated {group_forecasts} forecast records')

# Save all forecasts to database
if forecast_records:
    supabase.table('forecasts').insert(forecast_records).execute()
    print(f'\n💾 Saved {len(forecast_records)} total forecast records to database')

# Create daily view HTML
temp_dir = tempfile.mkdtemp()
daily_file = os.path.join(temp_dir, 'BestSelf_fixed_daily_forecast.html')

total_flow = sum(f['forecast_amount'] for f in forecast_records)

html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Fixed Daily Forecast - BestSelf</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50">
    <div class="container mx-auto p-6">
        <h1 class="text-2xl font-bold mb-6">📈 Fixed Daily Forecast - BestSelf</h1>
        <p class="mb-4">Using auto-mapped groups + your manual groups</p>
        <p class="mb-6">Generated from {len(forecast_records)} forecast records</p>
        
        <div class="bg-white p-6 rounded-lg shadow mb-6">
            <h2 class="text-lg font-semibold mb-4">Group Summary</h2>
            <div class="grid grid-cols-2 gap-6">
                <div>
                    <h3 class="font-medium mb-2">🤖 Auto-Mapped Groups ({len(auto_groups)})</h3>
                    <ul class="text-sm text-gray-600 space-y-1">'''

for group_name, vendors in list(auto_groups.items())[:10]:  # Show first 10
    html += f'<li>• {group_name} ({len(vendors)} vendors)</li>'

if len(auto_groups) > 10:
    html += f'<li class="italic">... and {len(auto_groups) - 10} more auto-groups</li>'

html += f'''
                    </ul>
                </div>
                <div>
                    <h3 class="font-medium mb-2">✋ Your Manual Groups ({len(manual_groups.data)})</h3>
                    <ul class="text-sm text-gray-600 space-y-1">'''

for group in manual_groups.data:
    html += f'<li>• {group["group_name"]} ({len(group["vendor_display_names"])} vendors)</li>'

html += f'''
                    </ul>
                </div>
            </div>
        </div>
        
        <div class="bg-white p-6 rounded-lg shadow mb-6">
            <h2 class="text-lg font-semibold mb-4">Forecast Summary</h2>
            <p class="text-lg">Total forecasted flow: <span class="font-bold text-green-600">${total_flow:,.0f}</span></p>
        </div>
        
        <div class="bg-white p-6 rounded-lg shadow">
            <h2 class="text-lg font-semibold mb-4">Daily Forecast Records</h2>
            <div class="overflow-x-auto">
                <table class="w-full text-sm">
                    <thead>
                        <tr class="border-b">
                            <th class="text-left p-2">Date</th>
                            <th class="text-left p-2">Group</th>
                            <th class="text-right p-2">Amount</th>
                            <th class="text-left p-2">Type</th>
                            <th class="text-left p-2">Method</th>
                        </tr>
                    </thead>
                    <tbody>'''

# Sort and show forecast records
forecast_records.sort(key=lambda x: x['forecast_date'])
for forecast in forecast_records[:50]:  # Show first 50 records
    amount_color = 'text-green-600' if forecast['forecast_amount'] > 0 else 'text-red-600'
    method = 'AUTO' if forecast['forecast_method'] == 'auto_regex_pattern' else 'MANUAL'
    method_color = 'text-blue-600' if method == 'AUTO' else 'text-purple-600'
    
    html += f'''
                        <tr class="border-b hover:bg-gray-50">
                            <td class="p-2">{forecast['forecast_date']}</td>
                            <td class="p-2">{forecast['vendor_group_name']}</td>
                            <td class="p-2 text-right {amount_color}">${forecast['forecast_amount']:,.0f}</td>
                            <td class="p-2">{forecast['forecast_type']}</td>
                            <td class="p-2 {method_color} font-medium">{method}</td>
                        </tr>'''

if len(forecast_records) > 50:
    html += f'<tr><td colspan="5" class="p-2 text-center text-gray-500 italic">... and {len(forecast_records) - 50} more records</td></tr>'

html += '''
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</body>
</html>'''

with open(daily_file, 'w') as f:
    f.write(html)

print(f'\n📊 Created fixed daily forecast: {daily_file}')
print(f'🌐 Opening in browser...')
webbrowser.open(f'file://{daily_file}')

print('\n✅ FIXED FORECAST READY!')
print(f'🤖 Auto-mapped {len(auto_groups)} vendor groups using regex patterns')
print(f'✋ Plus your {len(manual_groups.data)} manual groups')
print(f'📈 Total: {len(forecast_records)} forecast records over 13 weeks')
print(f'💰 Projected flow: ${total_flow:,.0f}')