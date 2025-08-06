#!/usr/bin/env python3
"""
Integrated Forecast Display - Final Output
Shows forecasts in the weekly view format from prototype_bestself_layout.html
Pulls data from all phases: import, grouping, pattern detection, forecasting
"""

import sys
sys.path.append('.')

from supabase_client import supabase
from datetime import datetime, date, timedelta
from collections import defaultdict
from typing import Dict, List, Optional
import json

def generate_integrated_forecast_display(client_id: str = 'spyguy', vendor_mappings: Dict = None):
    """Generate the final forecast display using data from all phases"""
    
    print("🎯 GENERATING INTEGRATED FORECAST DISPLAY")
    print("=" * 80)
    
    # Get forecast data from database
    forecast_result = supabase.table('forecasts').select('*')\
        .eq('client_id', client_id)\
        .gte('forecast_date', date.today().isoformat())\
        .lte('forecast_date', (date.today() + timedelta(weeks=13)).isoformat())\
        .order('forecast_date')\
        .execute()
    
    forecasts = forecast_result.data
    print(f"📊 Found {len(forecasts)} forecast records")
    
    # Get actual transactions for comparison
    transaction_result = supabase.table('transactions').select('*')\
        .eq('client_id', client_id)\
        .gte('transaction_date', (date.today() - timedelta(days=90)).isoformat())\
        .execute()
    
    transactions = transaction_result.data
    
    # Apply vendor mappings if provided
    if vendor_mappings:
        forecasts = apply_mappings_to_forecasts(forecasts, vendor_mappings)
        transactions = apply_mappings_to_transactions(transactions, vendor_mappings)
    
    # Calculate weekly aggregates
    weekly_data = calculate_weekly_aggregates(forecasts, transactions)
    
    # Generate HTML display
    html_content = generate_weekly_forecast_html(weekly_data, vendor_mappings, client_id)
    
    # Save to file
    output_file = '/Users/jeffreydebolt/Documents/cfo_forecast_refactored/integrated_forecast_display.html'
    with open(output_file, 'w') as f:
        f.write(html_content)
    
    print(f"✅ Integrated forecast display created: {output_file}")
    return output_file

def apply_mappings_to_forecasts(forecasts, mappings):
    """Apply vendor mappings to forecast records"""
    # Create reverse mapping
    vendor_to_group = {}
    for group_name, vendors in mappings.items():
        for vendor in vendors:
            vendor_to_group[vendor] = group_name
    
    # Update forecast vendor names
    for forecast in forecasts:
        original_vendor = forecast.get('vendor_group_name', '')
        forecast['display_name'] = vendor_to_group.get(original_vendor, original_vendor)
    
    return forecasts

def apply_mappings_to_transactions(transactions, mappings):
    """Apply vendor mappings to transaction records"""
    # Create reverse mapping
    vendor_to_group = {}
    for group_name, vendors in mappings.items():
        for vendor in vendors:
            vendor_to_group[vendor] = group_name
    
    # Update transaction vendor names
    for txn in transactions:
        original_vendor = txn.get('vendor_name', '')
        txn['display_name'] = vendor_to_group.get(original_vendor, original_vendor)
    
    return transactions

def calculate_weekly_aggregates(forecasts, transactions):
    """Calculate weekly totals for display"""
    weekly_data = defaultdict(lambda: defaultdict(lambda: {'forecast': 0, 'actual': 0}))
    
    # Get week boundaries
    today = date.today()
    current_week_start = today - timedelta(days=today.weekday())
    
    # Process forecasts
    for forecast in forecasts:
        forecast_date = datetime.fromisoformat(forecast['forecast_date']).date()
        week_num = (forecast_date - current_week_start).days // 7
        
        if 0 <= week_num < 13:
            vendor = forecast.get('display_name', forecast.get('vendor_group_name', 'Unknown'))
            amount = float(forecast.get('forecast_amount', 0))
            
            # Determine if revenue or expense
            if amount > 0:
                weekly_data['inflows'][vendor][f'week_{week_num}'] = amount
            else:
                weekly_data['outflows'][vendor][f'week_{week_num}'] = abs(amount)
    
    return weekly_data

def generate_weekly_forecast_html(weekly_data, vendor_mappings, client_id='spyguy'):
    """Generate HTML in the prototype_bestself_layout format"""
    
    # Calculate week dates
    today = date.today()
    current_week_start = today - timedelta(days=today.weekday())
    week_dates = []
    for i in range(13):
        week_start = current_week_start + timedelta(weeks=i)
        week_dates.append(week_start.strftime('%b %d'))
    
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CFO Forecast - Integrated View</title>
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
        .editable-cell.editing {{
            background-color: #fef3c7;
            border: 2px solid #f59e0b;
        }}
        .manual-override {{
            border-left: 3px solid #f59e0b;
            background-color: #fef3c7;
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
                        💰 CFO Forecast Dashboard - Integrated View
                    </h1>
                </div>
                <div class="flex items-center space-x-4">
                    <select class="border rounded-lg px-3 py-2 bg-white shadow-sm">
                        <option>{client_id}</option>
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
                    <p class="text-gray-600 mt-1">Generated from integrated onboarding system</p>
                </div>
                <div class="text-right">
                    <div class="text-sm text-gray-600">Vendor Groups: {len(vendor_mappings) if vendor_mappings else 'None'}</div>
                    <div class="text-sm text-gray-600">Forecast Records: {len(weekly_data.get('inflows', {})) + len(weekly_data.get('outflows', {}))}</div>
                </div>
            </div>
        </div>

        <!-- Cash Table -->
        <div class="glass-effect rounded-xl shadow-custom">
            <div class="scroll-container">
                <table class="w-full cash-table">
                    <thead>
                        <tr class="border-b border-gray-200">
                            <th class="sticky-col px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Cash Flow Items
                            </th>'''
    
    # Add week headers
    for i, week_date in enumerate(week_dates):
        html_content += f'''
                            <th class="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider min-w-[100px]">
                                <div>Week {i+1}</div>
                                <div class="text-gray-400 normal-case">{week_date}</div>
                            </th>'''
    
    html_content += '''
                        </tr>
                    </thead>
                    <tbody class="bg-white divide-y divide-gray-200">
                        <!-- Beginning Cash -->
                        <tr class="bg-blue-50">
                            <td class="sticky-col px-6 py-3 text-sm font-semibold text-gray-700">
                                💵 Beginning Cash
                            </td>'''
    
    # Add beginning cash row
    beginning_cash = 50000  # Default starting cash
    for i in range(13):
        html_content += f'''
                            <td class="px-3 py-3 text-center text-sm font-semibold text-blue-600">
                                ${beginning_cash:,.0f}
                            </td>'''
    
    html_content += '''
                        </tr>

                        <!-- INFLOWS SECTION -->
                        <tr class="category-header bg-gray-50 cursor-pointer hover:bg-gray-100 transition-all" onclick="toggleCategory('inflows')">
                            <td class="px-6 py-3 text-base font-semibold text-gray-700">
                                <span class="expand-icon mr-2 text-gray-600">▼</span>💰 Inflows
                            </td>'''
    
    # Calculate inflow totals
    inflow_totals = [0] * 13
    for vendor, weeks in weekly_data.get('inflows', {}).items():
        for week_num in range(13):
            amount = weeks.get(f'week_{week_num}', 0)
            inflow_totals[week_num] += amount
    
    # Add inflow total cells
    for total in inflow_totals:
        html_content += f'''
                            <td class="px-3 py-3 text-right text-sm text-green-600 font-semibold">
                                ${total:,.0f}
                            </td>'''
    
    html_content += '''
                        </tr>'''
    
    # Add individual inflow vendors
    for vendor, weeks in sorted(weekly_data.get('inflows', {}).items()):
        html_content += f'''
                        <tr class="vendor-detail inflows-details hover:bg-gray-50">
                            <td class="px-10 py-2 text-sm text-gray-700">
                                {vendor}
                            </td>'''
        
        for week_num in range(13):
            amount = weeks.get(f'week_{week_num}', 0)
            if amount > 0:
                html_content += f'''
                            <td class="px-3 py-2 text-right text-sm text-green-600 editable-cell cursor-pointer hover:bg-blue-50" 
                                data-vendor="{vendor}" data-week="{week_num}" data-amount="{amount}" ondblclick="editCell(this)">
                                ${amount:,.0f}
                            </td>'''
            else:
                html_content += f'''
                            <td class="px-3 py-2 text-right text-sm text-gray-400">
                                —
                            </td>'''
        
        html_content += '''
                        </tr>'''
    
    # OUTFLOWS SECTION
    html_content += '''
                        <!-- OUTFLOWS SECTION -->
                        <tr class="category-header bg-gray-50 cursor-pointer hover:bg-gray-100 transition-all" onclick="toggleCategory('outflows')">
                            <td class="px-6 py-3 text-base font-semibold text-gray-700">
                                <span class="expand-icon mr-2 text-gray-600">▼</span>💸 Outflows
                            </td>'''
    
    # Calculate outflow totals
    outflow_totals = [0] * 13
    for vendor, weeks in weekly_data.get('outflows', {}).items():
        for week_num in range(13):
            amount = weeks.get(f'week_{week_num}', 0)
            outflow_totals[week_num] += amount
    
    # Add outflow total cells
    for total in outflow_totals:
        html_content += f'''
                            <td class="px-3 py-3 text-right text-sm text-red-600 font-semibold">
                                ${total:,.0f}
                            </td>'''
    
    html_content += '''
                        </tr>'''
    
    # Add individual outflow vendors
    for vendor, weeks in sorted(weekly_data.get('outflows', {}).items()):
        html_content += f'''
                        <tr class="vendor-detail outflows-details hover:bg-gray-50">
                            <td class="px-10 py-2 text-sm text-gray-700">
                                {vendor}
                            </td>'''
        
        for week_num in range(13):
            amount = weeks.get(f'week_{week_num}', 0)
            if amount > 0:
                html_content += f'''
                            <td class="px-3 py-2 text-right text-sm text-red-600 editable-cell cursor-pointer hover:bg-blue-50" 
                                data-vendor="{vendor}" data-week="{week_num}" data-amount="{amount}" ondblclick="editCell(this)">
                                ${amount:,.0f}
                            </td>'''
            else:
                html_content += f'''
                            <td class="px-3 py-2 text-right text-sm text-gray-400">
                                —
                            </td>'''
        
        html_content += '''
                        </tr>'''
    
    # NET CASH FLOW
    html_content += '''
                        <!-- Net Cash Flow -->
                        <tr class="bg-gray-100 font-semibold">
                            <td class="sticky-col px-6 py-3 text-sm text-gray-700">
                                📊 Net Cash Flow
                            </td>'''
    
    for i in range(13):
        net_flow = inflow_totals[i] - outflow_totals[i]
        color = 'text-green-600' if net_flow >= 0 else 'text-red-600'
        html_content += f'''
                            <td class="px-3 py-3 text-right text-sm {color}">
                                ${net_flow:,.0f}
                            </td>'''
    
    html_content += '''
                        </tr>

                        <!-- Ending Cash -->
                        <tr class="bg-blue-50 font-semibold">
                            <td class="sticky-col px-6 py-3 text-sm text-gray-700">
                                💰 Ending Cash
                            </td>'''
    
    # Calculate ending cash
    running_cash = beginning_cash
    for i in range(13):
        running_cash += inflow_totals[i] - outflow_totals[i]
        color = 'text-blue-600' if running_cash >= 20000 else 'text-red-600'
        html_content += f'''
                            <td class="px-3 py-3 text-center text-sm {color}">
                                ${running_cash:,.0f}
                            </td>'''
    
    html_content += '''
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </main>

    <script>
        function toggleCategory(category) {
            const details = document.querySelectorAll(`.${category}-details`);
            const header = event.currentTarget;
            const icon = header.querySelector('.expand-icon');
            
            details.forEach(row => {
                row.classList.toggle('hidden');
            });
            
            header.classList.toggle('collapsed');
        }
        
        function expandAll() {
            document.querySelectorAll('.vendor-detail').forEach(row => {
                row.classList.remove('hidden');
            });
            document.querySelectorAll('.category-header').forEach(header => {
                header.classList.remove('collapsed');
            });
        }
        
        function collapseAll() {
            document.querySelectorAll('.vendor-detail').forEach(row => {
                row.classList.add('hidden');
            });
            document.querySelectorAll('.category-header').forEach(header => {
                header.classList.add('collapsed');
            });
        }
        
        function editCell(cell) {
            const currentValue = cell.getAttribute('data-amount');
            const vendor = cell.getAttribute('data-vendor');
            const week = cell.getAttribute('data-week');
            
            const input = document.createElement('input');
            input.type = 'number';
            input.value = currentValue;
            input.className = 'w-full px-2 py-1 text-sm border rounded';
            
            input.onblur = function() {
                const newValue = parseFloat(input.value) || 0;
                cell.setAttribute('data-amount', newValue);
                cell.textContent = newValue > 0 ? `$${newValue.toLocaleString()}` : '—';
                cell.classList.add('manual-override');
                
                // Recalculate totals
                recalculateTotals();
            };
            
            input.onkeydown = function(e) {
                if (e.key === 'Enter') {
                    input.blur();
                }
            };
            
            cell.textContent = '';
            cell.appendChild(input);
            input.focus();
            input.select();
        }
        
        function recalculateTotals() {
            // Recalculate all totals based on current cell values
            console.log('Recalculating totals...');
            // Implementation would update totals and ending cash
        }
        
        // Initialize
        console.log('Integrated forecast display loaded');
        console.log('Data from all phases: import → grouping → patterns → forecasts');
    </script>
</body>
</html>'''
    
    return html_content

def main():
    """Generate the integrated forecast display"""
    
    # Example vendor mappings (would come from user grouping interface)
    example_mappings = {
        "Amex Payments": ["AMEX EPAYMENT", "Amex"],
        "State Sales Tax": ["VA DEPT TAXATION", "NC DEPT REVENUE", "FLA DEPT REVENUE"],
        "Mercury Transfers": ["SGE OpEx (Mercury Checking xx3526)", "SGE Income (Mercury Checking xx9292)"]
    }
    
    # Generate display
    display_file = generate_integrated_forecast_display('spyguy', example_mappings)
    
    print(f"\n🎉 SUCCESS!")
    print(f"📊 Weekly forecast view generated")
    print(f"🔗 Integrated data from all phases")
    print(f"✏️ Double-click to edit any forecast")

if __name__ == "__main__":
    main()