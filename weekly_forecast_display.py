#!/usr/bin/env python3
import sys
import os
import tempfile
import webbrowser
from collections import defaultdict
sys.path.append('.')
from supabase_client import supabase
from datetime import datetime, date, timedelta

print('WEEKLY FORECAST DISPLAY WITH BANK BALANCE')
print('Client: BestSelf') 
print('=' * 60)

# Get forecast data
forecasts = supabase.table('forecasts').select('*')\
    .eq('client_id', 'BestSelf')\
    .order('forecast_date')\
    .execute()

print(f'✅ Found {len(forecasts.data)} forecast records')

# Starting bank balance (you'll want to get this from user or database)
starting_balance = 50000  # Example starting balance
print(f'💰 Starting bank balance: ${starting_balance:,.0f}')

# Group by week and calculate daily balances
weekly_data = defaultdict(lambda: {
    'dates': [],
    'daily_flows': [],
    'daily_balances': [],
    'week_start': None,
    'week_end': None,
    'total_inflow': 0,
    'total_outflow': 0,
    'net_flow': 0
})

# Process each forecast record
current_balance = starting_balance
daily_flows = defaultdict(float)

# Sum up all flows by date
for forecast in forecasts.data:
    forecast_date = datetime.fromisoformat(forecast['forecast_date']).date()
    amount = float(forecast['forecast_amount'])
    daily_flows[forecast_date] += amount

# Calculate daily balances and group by week
start_date = min(daily_flows.keys()) if daily_flows else date.today()
end_date = max(daily_flows.keys()) if daily_flows else date.today() + timedelta(weeks=13)

current_date = start_date
while current_date <= end_date:
    # Get week number (ISO week)
    year, week_num, _ = current_date.isocalendar()
    week_key = f"{year}-W{week_num:02d}"
    
    # Daily flow for this date
    daily_flow = daily_flows.get(current_date, 0)
    current_balance += daily_flow
    
    # Add to weekly data
    if not weekly_data[week_key]['week_start']:
        weekly_data[week_key]['week_start'] = current_date
    weekly_data[week_key]['week_end'] = current_date
    
    weekly_data[week_key]['dates'].append(current_date)
    weekly_data[week_key]['daily_flows'].append(daily_flow)
    weekly_data[week_key]['daily_balances'].append(current_balance)
    
    if daily_flow > 0:
        weekly_data[week_key]['total_inflow'] += daily_flow
    else:
        weekly_data[week_key]['total_outflow'] += abs(daily_flow)
    
    weekly_data[week_key]['net_flow'] += daily_flow
    
    current_date += timedelta(days=1)

# Create HTML display
temp_dir = tempfile.mkdtemp()
display_file = os.path.join(temp_dir, 'BestSelf_weekly_forecast.html')

html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Weekly Forecast - BestSelf</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50">
    <div class="container mx-auto p-6">
        <h1 class="text-2xl font-bold mb-6">📅 Weekly Cash Flow Forecast - BestSelf</h1>
        <p class="mb-4">13-week forecast with daily bank balance tracking</p>
        <p class="mb-6">Starting Balance: <span class="font-bold text-blue-600">${starting_balance:,.0f}</span></p>
        
        <div class="space-y-6">'''

# Sort weeks chronologically
sorted_weeks = sorted(weekly_data.keys())

for week_key in sorted_weeks:
    week_data = weekly_data[week_key]
    week_start = week_data['week_start']
    week_end = week_data['week_end']
    
    # Calculate ending balance for the week
    ending_balance = week_data['daily_balances'][-1] if week_data['daily_balances'] else starting_balance
    
    html += f'''
            <div class="bg-white p-6 rounded-lg shadow">
                <div class="flex justify-between items-center mb-4">
                    <h2 class="text-lg font-semibold">{week_key}</h2>
                    <span class="text-sm text-gray-500">{week_start.strftime("%b %d")} - {week_end.strftime("%b %d, %Y")}</span>
                </div>
                
                <div class="grid grid-cols-4 gap-4 mb-4">
                    <div class="text-center">
                        <div class="text-sm text-gray-500">Total Inflow</div>
                        <div class="text-lg font-bold text-green-600">${week_data['total_inflow']:,.0f}</div>
                    </div>
                    <div class="text-center">
                        <div class="text-sm text-gray-500">Total Outflow</div>
                        <div class="text-lg font-bold text-red-600">${week_data['total_outflow']:,.0f}</div>
                    </div>
                    <div class="text-center">
                        <div class="text-sm text-gray-500">Net Flow</div>
                        <div class="text-lg font-bold {'text-green-600' if week_data['net_flow'] >= 0 else 'text-red-600'}">${week_data['net_flow']:,.0f}</div>
                    </div>
                    <div class="text-center">
                        <div class="text-sm text-gray-500">Ending Balance</div>
                        <div class="text-lg font-bold text-blue-600">${ending_balance:,.0f}</div>
                    </div>
                </div>
                
                <div class="overflow-x-auto">
                    <table class="w-full text-sm">
                        <thead>
                            <tr class="border-b">
                                <th class="text-left p-2">Date</th>
                                <th class="text-left p-2">Day</th>
                                <th class="text-right p-2">Daily Flow</th>
                                <th class="text-right p-2">Bank Balance</th>
                            </tr>
                        </thead>
                        <tbody>'''
    
    for i, date_obj in enumerate(week_data['dates']):
        daily_flow = week_data['daily_flows'][i]
        daily_balance = week_data['daily_balances'][i]
        day_name = date_obj.strftime("%a")
        
        flow_color = 'text-green-600' if daily_flow > 0 else ('text-red-600' if daily_flow < 0 else 'text-gray-500')
        balance_color = 'text-blue-600' if daily_balance > 0 else 'text-red-600'
        
        html += f'''
                            <tr class="border-b hover:bg-gray-50">
                                <td class="p-2">{date_obj.strftime("%m/%d")}</td>
                                <td class="p-2">{day_name}</td>
                                <td class="p-2 text-right {flow_color}">
                                    {"+" if daily_flow > 0 else ""}${daily_flow:,.0f}
                                </td>
                                <td class="p-2 text-right font-medium {balance_color}">
                                    ${daily_balance:,.0f}
                                </td>
                            </tr>'''
    
    html += '''
                        </tbody>
                    </table>
                </div>
            </div>'''

# Summary stats
final_balance = weekly_data[sorted_weeks[-1]]['daily_balances'][-1] if sorted_weeks else starting_balance
total_net_flow = final_balance - starting_balance

html += f'''
        </div>
        
        <div class="mt-6 bg-white p-6 rounded-lg shadow">
            <h2 class="text-lg font-semibold mb-4">13-Week Summary</h2>
            <div class="grid grid-cols-3 gap-6">
                <div class="text-center">
                    <div class="text-sm text-gray-500">Starting Balance</div>
                    <div class="text-xl font-bold text-blue-600">${starting_balance:,.0f}</div>
                </div>
                <div class="text-center">
                    <div class="text-sm text-gray-500">Total Net Flow</div>
                    <div class="text-xl font-bold {'text-green-600' if total_net_flow >= 0 else 'text-red-600'}">${total_net_flow:,.0f}</div>
                </div>
                <div class="text-center">
                    <div class="text-sm text-gray-500">Ending Balance</div>
                    <div class="text-xl font-bold text-blue-600">${final_balance:,.0f}</div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>'''

with open(display_file, 'w') as f:
    f.write(html)

print(f'📊 Created weekly forecast display: {display_file}')
print(f'🌐 Opening in browser...')
webbrowser.open(f'file://{display_file}')

print('\n✅ WEEKLY FORECAST WITH BANK BALANCE READY!')
print(f'📈 Final projected balance: ${final_balance:,.0f} (${total_net_flow:+,.0f} net flow)')