#!/usr/bin/env python3
import sys
import os
import tempfile
import webbrowser
sys.path.append('.')
from supabase_client import supabase
from datetime import datetime, date, timedelta

print('STEP 5: GENERATE FORECAST DISPLAY')
print('Client: BestSelf') 
print('=' * 60)

# Get pattern analysis for forecast generation
patterns = supabase.table('pattern_analysis').select('*').eq('client_id', 'BestSelf').execute()
print(f'✅ Found {len(patterns.data)} patterns to forecast')

# Clear existing forecasts for this client
print('🗑️ Clearing existing forecasts...')
supabase.table('forecasts').delete().eq('client_id', 'BestSelf').execute()

# Generate forecast records for next 13 weeks
forecast_records = []
start_date = date.today()
end_date = start_date + timedelta(weeks=13)

print(f'📅 Generating forecasts from {start_date} to {end_date}')

for pattern in patterns.data:
    group_name = pattern['vendor_group_name']
    frequency = pattern.get('frequency_detected', 'monthly')
    amount = float(pattern.get('average_amount', 0))
    confidence = pattern.get('confidence_score', 0.5)
    
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
                'forecast_method': 'pattern_based',
                'pattern_confidence': confidence,
                'created_at': datetime.now().isoformat()
            })
            group_forecasts += 1
        
        current_date += timedelta(days=1)
    
    print(f'   ✅ Generated {group_forecasts} forecast records')

# Save all forecasts to database
if forecast_records:
    supabase.table('forecasts').insert(forecast_records).execute()
    print(f'\n💾 Saved {len(forecast_records)} forecast records to database')

# Create HTML display
temp_dir = tempfile.mkdtemp()
display_file = os.path.join(temp_dir, 'BestSelf_forecast.html')

# Calculate summary stats
total_inflows = sum(f['forecast_amount'] for f in forecast_records if f['forecast_amount'] > 0)
total_outflows = abs(sum(f['forecast_amount'] for f in forecast_records if f['forecast_amount'] < 0))
net_flow = sum(f['forecast_amount'] for f in forecast_records)

html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>13-Week Forecast - BestSelf</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50">
    <div class="container mx-auto p-6">
        <h1 class="text-2xl font-bold mb-6">📈 13-Week Cash Flow Forecast - BestSelf</h1>
        <p class="mb-4">Generated from {len(forecast_records)} forecast records</p>
        
        <div class="bg-white p-6 rounded-lg shadow">
            <h2 class="text-lg font-semibold mb-4">Summary</h2>
            <p>Total forecasted inflows: ${total_inflows:,.0f}</p>
            <p>Total forecasted outflows: ${total_outflows:,.0f}</p>
            <p>Net cash flow: ${net_flow:,.0f}</p>
        </div>
        
        <div class="mt-6 bg-white p-6 rounded-lg shadow">
            <h2 class="text-lg font-semibold mb-4">Forecast Records</h2>
            <div class="overflow-x-auto">
                <table class="w-full text-sm">
                    <thead>
                        <tr class="border-b">
                            <th class="text-left p-2">Date</th>
                            <th class="text-left p-2">Vendor Group</th>
                            <th class="text-right p-2">Amount</th>
                            <th class="text-left p-2">Type</th>
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
                            <td class="p-2">{forecast['vendor_group_name']}</td>
                            <td class="p-2 text-right {amount_color}">${forecast['forecast_amount']:,.0f}</td>
                            <td class="p-2">{forecast['forecast_type']}</td>
                        </tr>'''

html += '''
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</body>
</html>'''

with open(display_file, 'w') as f:
    f.write(html)

print(f'\n📊 Created forecast display: {display_file}')
print(f'🌐 Opening in browser...')

# Open in browser
webbrowser.open(f'file://{display_file}')

print('\n🎉 STEP 5 COMPLETE - 13-week forecast generated and displayed!')
print(f'📈 Summary: ${net_flow:,.0f} net cash flow over 13 weeks')