#!/usr/bin/env python3
import sys
import os
import tempfile
import webbrowser
from collections import defaultdict
sys.path.append('.')
from supabase_client import supabase
from datetime import datetime, date, timedelta

print('CORRECTED WEEKLY FORECAST - MATCHING PROTOTYPE LAYOUT')
print('Client: BestSelf') 
print('=' * 60)

# Get ONLY your manual groups
manual_groups = supabase.table('vendor_groups').select('*').eq('client_id', 'BestSelf').execute()
print(f'✅ Found {len(manual_groups.data)} manual groups you created')

# Get forecasts for your manual groups only
forecasts = supabase.table('forecasts').select('*')\
    .eq('client_id', 'BestSelf')\
    .order('forecast_date')\
    .execute()

print(f'✅ Found {len(forecasts.data)} forecast records')

# Starting bank balance
starting_balance = 50000

# Group forecasts by week and calculate weekly amounts
weekly_forecasts = defaultdict(lambda: defaultdict(float))
start_date = date.today()

for forecast in forecasts.data:
    forecast_date = datetime.fromisoformat(forecast['forecast_date']).date()
    group_name = forecast['vendor_group_name']
    amount = float(forecast['forecast_amount'])
    
    # Calculate week number from start date
    week_diff = (forecast_date - start_date).days // 7
    if 0 <= week_diff < 13:
        weekly_forecasts[week_diff][group_name] += amount

# Calculate weekly bank balances
weekly_balances = []
current_balance = starting_balance

for week in range(13):
    week_total = sum(weekly_forecasts[week].values())
    current_balance += week_total
    weekly_balances.append(current_balance)

# Create HTML matching the prototype layout
temp_dir = tempfile.mkdtemp()
display_file = os.path.join(temp_dir, 'BestSelf_corrected_weekly_layout.html')

html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CFO Forecast - BestSelf (Manual Groups Only)</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .category-header {{
            cursor: pointer;
            transition: all 0.2s;
        }}
        .category-header:hover {{
            background-color: rgba(59, 130, 246, 0.1);
        }}
        .expand-icon {{
            transition: transform 0.2s;
            display: inline-block;
        }}
        .collapsed .expand-icon {{
            transform: rotate(-90deg);
        }}
        .cash-table {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            font-size: 14px;
        }}
        .scroll-container {{
            overflow-x: auto;
            scrollbar-width: thin;
        }}
        .sticky-col {{
            position: sticky;
            left: 0;
            background: white;
            z-index: 10;
            border-right: 2px solid #e5e7eb;
        }}
        .vendor-detail {{
            transition: all 0.3s;
        }}
        body {{
            background: #f8fafc;
            min-height: 100vh;
        }}
        .glass-effect {{
            background: white;
            border: 1px solid #e2e8f0;
        }}
        .shadow-custom {{
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }}
    </style>
</head>
<body>
    <!-- Navigation -->
    <nav class="glass-effect shadow-custom">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-16">
                <div class="flex items-center">
                    <h1 class="text-xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                        💰 CFO Forecast Dashboard - Manual Groups Only
                    </h1>
                </div>
                <div class="flex items-center space-x-4">
                    <select class="border rounded-lg px-3 py-2 bg-white shadow-sm">
                        <option>BestSelf</option>
                    </select>
                    <button class="px-4 py-2 text-sm bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-lg shadow-sm hover:from-blue-600 hover:to-blue-700 transition-all" onclick="expandAll()">
                        📂 Expand All
                    </button>
                    <button class="px-4 py-2 text-sm bg-gradient-to-r from-gray-500 to-gray-600 text-white rounded-lg shadow-sm hover:from-gray-600 hover:to-gray-700 transition-all" onclick="collapseAll()">
                        📁 Collapse All
                    </button>
                </div>
            </div>
        </div>
    </nav>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto px-4 py-6">
        <!-- Header Card -->
        <div class="glass-effect rounded-xl shadow-custom p-6 mb-6">
            <div class="flex justify-between items-center">
                <div>
                    <h2 class="text-2xl font-bold text-gray-800">13-Week Cash Flow Forecast</h2>
                    <p class="text-gray-600 mt-1">Using only your {len(manual_groups.data)} manually created groups</p>
                </div>
                <div class="text-right">
                    <div class="text-sm text-gray-500">Starting Balance</div>
                    <div class="text-2xl font-bold text-blue-600">${starting_balance:,.0f}</div>
                </div>
            </div>
        </div>

        <!-- Forecast Table -->
        <div class="glass-effect rounded-xl shadow-custom overflow-hidden">
            <div class="scroll-container">
                <table class="cash-table w-full">
                    <thead class="bg-gradient-to-r from-blue-600 to-blue-700 text-white">
                        <tr>
                            <th class="sticky-col px-6 py-4 text-left text-sm font-semibold min-w-48">
                                Vendor Groups & Categories
                            </th>'''

# Generate week headers
for week in range(13):
    week_start = start_date + timedelta(weeks=week)
    week_end = week_start + timedelta(days=6)
    balance = weekly_balances[week]
    
    html += f'''
                            <th class="px-3 py-3 text-center text-sm font-semibold text-white min-w-24" data-week="{week}">
                                Week {week + 1}<br>
                                <span class="text-xs font-normal opacity-75">{week_start.strftime('%m/%d')}</span><br>
                                <span class="text-xs font-normal text-green-400">${balance:,.0f}</span>
                            </th>'''

html += '''
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-200">
                        <!-- YOUR MANUAL GROUPS SECTION -->
                        <tr class="bg-gray-100">
                            <td colspan="14" class="px-6 py-3 text-base font-semibold text-gray-700">
                                ✅ Your Manual Groups
                            </td>
                        </tr>'''

# Add your manual groups
for group in manual_groups.data:
    group_name = group['group_name']
    vendors = group['vendor_display_names']
    
    # Get pattern info for this group
    pattern = supabase.table('pattern_analysis').select('*')\
        .eq('client_id', 'BestSelf')\
        .eq('vendor_group_name', group_name)\
        .execute()
    
    frequency = 'unknown'
    if pattern.data:
        frequency = pattern.data[0].get('frequency_detected', 'unknown')
    
    # Determine pattern badge color
    badge_color = {
        'daily': 'bg-gray-100 text-gray-800',
        'weekly': 'bg-green-100 text-green-800', 
        'monthly': 'bg-purple-100 text-purple-800',
        'bi-weekly': 'bg-blue-100 text-blue-800'
    }.get(frequency, 'bg-gray-100 text-gray-800')
    
    html += f'''
                        <tr class="vendor-detail hover:bg-gray-50">
                            <td class="px-10 py-2 text-sm text-gray-700">
                                {group_name}<span class="ml-2 px-1 py-0 text-xs {badge_color} rounded">{frequency}</span>
                                <div class="text-xs text-gray-500 mt-1">{len(vendors)} vendors: {", ".join(vendors[:2])}{" ..." if len(vendors) > 2 else ""}</div>
                            </td>'''
    
    # Add weekly amounts for this group
    for week in range(13):
        amount = weekly_forecasts[week].get(group_name, 0)
        if amount != 0:
            color = 'text-green-600' if amount > 0 else 'text-red-600'
            html += f'<td class="px-3 py-2 text-right text-sm {color}">${amount:,.0f}</td>'
        else:
            html += f'<td class="px-3 py-2 text-right text-sm text-gray-400">—</td>'
    
    html += '</tr>'

# Add ungrouped vendors section
all_grouped_vendors = []
for group in manual_groups.data:
    all_grouped_vendors.extend(group['vendor_display_names'])

ungrouped_vendors = supabase.table('transactions').select('vendor_name')\
    .eq('client_id', 'BestSelf')\
    .execute()

unique_vendors = set(txn['vendor_name'] for txn in ungrouped_vendors.data)
ungrouped = [v for v in unique_vendors if v not in all_grouped_vendors]

html += f'''
                        <!-- UNGROUPED VENDORS SECTION -->
                        <tr class="bg-yellow-50 border-l-4 border-yellow-400">
                            <td colspan="14" class="px-6 py-3 text-base font-semibold text-yellow-800">
                                ⚠️ Ungrouped Vendors ({len(ungrouped)} vendors not forecasted)
                            </td>
                        </tr>'''

# Show some ungrouped vendors (first 10)
for vendor in sorted(ungrouped)[:10]:
    html += f'''
                        <tr class="vendor-detail hover:bg-yellow-50 opacity-50">
                            <td class="px-10 py-2 text-sm text-gray-500">
                                {vendor} <span class="text-xs text-yellow-600">(not forecasted)</span>
                            </td>'''
    
    for week in range(13):
        html += f'<td class="px-3 py-2 text-right text-sm text-gray-400">—</td>'
    
    html += '</tr>'

if len(ungrouped) > 10:
    html += f'''
                        <tr class="vendor-detail hover:bg-yellow-50 opacity-50">
                            <td class="px-10 py-2 text-sm text-gray-500 italic">
                                ... and {len(ungrouped) - 10} more ungrouped vendors
                            </td>'''
    for week in range(13):
        html += f'<td class="px-3 py-2 text-right text-sm text-gray-400">—</td>'
    html += '</tr>'

# Add totals row
html += '''
                        <!-- TOTALS SECTION -->
                        <tr class="bg-blue-50 border-t-2 border-blue-200">
                            <td class="px-6 py-3 text-base font-bold text-blue-800">
                                💰 Net Weekly Flow
                            </td>'''

for week in range(13):
    week_total = sum(weekly_forecasts[week].values())
    if week_total != 0:
        color = 'text-green-600' if week_total > 0 else 'text-red-600'
        html += f'<td class="px-3 py-3 text-right text-sm font-bold {color}">${week_total:,.0f}</td>'
    else:
        html += f'<td class="px-3 py-3 text-right text-sm text-gray-400 font-bold">—</td>'

html += '''
                        </tr>
                        
                        <!-- RUNNING BALANCE ROW -->
                        <tr class="bg-blue-100 border-t border-blue-300">
                            <td class="px-6 py-3 text-base font-bold text-blue-900">
                                💳 Running Bank Balance
                            </td>'''

for week in range(13):
    balance = weekly_balances[week]
    color = 'text-blue-600' if balance > 0 else 'text-red-600'
    html += f'<td class="px-3 py-3 text-right text-sm font-bold {color}">${balance:,.0f}</td>'

html += '''
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </main>

    <script>
        function expandAll() {
            document.querySelectorAll('.category-header').forEach(header => {
                header.classList.remove('collapsed');
                const icon = header.querySelector('.expand-icon');
                if (icon) icon.textContent = '▼';
            });
            document.querySelectorAll('.vendor-detail').forEach(row => row.style.display = '');
        }

        function collapseAll() {
            document.querySelectorAll('.category-header').forEach(header => {
                header.classList.add('collapsed');
                const icon = header.querySelector('.expand-icon');
                if (icon) icon.textContent = '▶';
            });
            document.querySelectorAll('.vendor-detail').forEach(row => row.style.display = 'none');
        }
    </script>
</body>
</html>'''

with open(display_file, 'w') as f:
    f.write(html)

print(f'📊 Created corrected weekly forecast layout: {display_file}')
print(f'🌐 Opening in browser...')
webbrowser.open(f'file://{display_file}')

print('\n✅ CORRECTED WEEKLY FORECAST LAYOUT READY!')
print(f'📈 Matches prototype layout using ONLY your {len(manual_groups.data)} manual groups')
print(f'⚠️ {len(ungrouped)} ungrouped vendors shown but not forecasted')
print(f'💰 Final balance: ${weekly_balances[-1]:,.0f}')