#!/usr/bin/env python3
"""
Generate enhanced HTML dashboard with V2 forecasting data.
"""

import sys
sys.path.append('.')

from database.forecast_db_manager import forecast_db
from services.forecast_service_v2 import forecast_service_v2
from datetime import date, timedelta
import json

def get_enhanced_forecast_data():
    """Get real forecast data from V2 system."""
    print("📊 GETTING ENHANCED FORECAST DATA")
    print("=" * 50)
    
    client_id = 'bestself'
    start_date = date(2025, 8, 4)  # Monday
    
    try:
        # Get 13 weeks of forecasts
        end_date = start_date + timedelta(weeks=13)
        
        # Get forecasts from database
        forecasts = forecast_db.get_forecasts(client_id, start_date, end_date)
        print(f"📅 Found {len(forecasts)} forecast records")
        
        # Get vendor groups with patterns
        vendor_groups = forecast_db.get_vendor_groups(client_id)
        active_groups = [g for g in vendor_groups if g.get('pattern_frequency') and 
                        g['pattern_frequency'] != 'irregular']
        print(f"🏢 Found {len(active_groups)} active vendor groups")
        
        # Organize data by week
        weekly_data = {}
        
        for week_num in range(13):
            week_start = start_date + timedelta(weeks=week_num)
            week_end = week_start + timedelta(days=6)
            
            # Get forecasts for this week
            week_forecasts = [f for f in forecasts 
                            if week_start <= date.fromisoformat(f['forecast_date']) <= week_end]
            
            # Calculate totals
            deposits = sum(float(f['forecast_amount']) for f in week_forecasts 
                          if float(f['forecast_amount']) > 0)
            withdrawals = abs(sum(float(f['forecast_amount']) for f in week_forecasts 
                                if float(f['forecast_amount']) < 0))
            net_movement = deposits - withdrawals
            
            weekly_data[week_num] = {
                'week_start': week_start,
                'week_end': week_end,
                'deposits': deposits,
                'withdrawals': withdrawals,
                'net_movement': net_movement,
                'forecasts': week_forecasts
            }
        
        return {
            'weekly_data': weekly_data,
            'vendor_groups': active_groups,
            'start_date': start_date
        }
        
    except Exception as e:
        print(f"❌ Error getting forecast data: {e}")
        return None

def generate_enhanced_dashboard():
    """Generate enhanced HTML dashboard."""
    print("🚀 GENERATING ENHANCED DASHBOARD")
    print("=" * 50)
    
    # Get real data
    data = get_enhanced_forecast_data()
    if not data:
        print("❌ Failed to get forecast data")
        return
    
    weekly_data = data['weekly_data']
    vendor_groups = data['vendor_groups']
    start_date = data['start_date']
    
    # Generate week headers
    week_headers = ""
    for week_num in range(13):
        week_data = weekly_data[week_num]
        week_start = week_data['week_start']
        week_end = week_data['week_end']
        week_headers += f'''
            <th class="px-4 py-3 text-right font-medium text-gray-900 min-w-28">Week {week_num + 1}<br>
                <span class="font-normal text-xs text-gray-500">{week_start.strftime('%b %d')}-{week_end.strftime('%d')}</span>
            </th>'''
    
    # Generate deposit rows
    deposit_total_row = ""
    for week_num in range(13):
        deposits = weekly_data[week_num]['deposits']
        deposit_total_row += f'<td class="px-4 py-3 text-right positive font-medium">+${deposits:,.0f}</td>'
    
    # Generate withdrawal rows  
    withdrawal_total_row = ""
    for week_num in range(13):
        withdrawals = weekly_data[week_num]['withdrawals']
        withdrawal_total_row += f'<td class="px-4 py-3 text-right negative font-medium">-${withdrawals:,.0f}</td>'
    
    # Generate net movement row
    net_movement_row = ""
    running_balance = 45230  # Starting balance
    ending_balance_row = ""
    
    for week_num in range(13):
        net_movement = weekly_data[week_num]['net_movement']
        running_balance += net_movement
        
        net_class = "positive" if net_movement >= 0 else "negative"
        balance_class = "critical" if running_balance < 10000 else ""
        
        net_movement_row += f'<td class="px-4 py-3 text-right font-bold {net_class}">{"+" if net_movement >= 0 else ""}${net_movement:,.0f}</td>'
        ending_balance_row += f'<td class="px-4 py-3 text-right font-bold {balance_class}">${running_balance:,.0f}</td>'
    
    # Generate vendor group breakdown
    vendor_group_rows = ""
    for group in vendor_groups[:5]:  # Show top 5 groups
        group_name = group['group_name']
        pattern = group.get('pattern_frequency', 'N/A')
        timing = group.get('pattern_timing', 'N/A')
        confidence = group.get('pattern_confidence', 0.0)
        
        # Get weekly amounts for this group
        group_row = f'''
        <tr class="bg-gray-25 text-xs text-gray-600 group-detail" data-group="{group_name}">
            <td class="sticky-col px-6 py-2 flex items-center">
                <span class="mr-2">  {group_name}</span>
                <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    {pattern}
                </span>
                <span class="ml-1 text-xs text-gray-500" title="{timing}">
                    {confidence:.0%} conf
                </span>
            </td>'''
        
        for week_num in range(13):
            # Find forecasts for this group this week
            week_forecasts = weekly_data[week_num]['forecasts']
            group_amount = sum(float(f['forecast_amount']) for f in week_forecasts 
                             if f['vendor_group_name'] == group_name)
            
            if group_amount != 0:
                sign = "+" if group_amount > 0 else ""
                group_row += f'<td class="px-4 py-2 text-right">{sign}${group_amount:,.0f}</td>'
            else:
                group_row += '<td class="px-4 py-2 text-right">—</td>'
        
        group_row += '</tr>'
        vendor_group_rows += group_row
    
    # Calculate confidence levels
    high_conf_groups = len([g for g in vendor_groups if g.get('pattern_confidence', 0) >= 0.8])
    med_conf_groups = len([g for g in vendor_groups if 0.5 <= g.get('pattern_confidence', 0) < 0.8])
    low_conf_groups = len([g for g in vendor_groups if g.get('pattern_confidence', 0) < 0.5])
    
    overall_confidence = (high_conf_groups * 0.9 + med_conf_groups * 0.7 + low_conf_groups * 0.4) / len(vendor_groups) if vendor_groups else 0.5
    
    # Generate insights
    min_balance = min(running_balance for week_num in range(13) for running_balance in [45230 + sum(weekly_data[w]['net_movement'] for w in range(week_num + 1))])
    avg_deposits = sum(weekly_data[w]['deposits'] for w in range(13)) / 13
    avg_withdrawals = sum(weekly_data[w]['withdrawals'] for w in range(13)) / 13
    
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CFO Forecast - Enhanced V2 Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .cash-table {{ font-family: 'Monaco', 'Menlo', monospace; }}
        .positive {{ color: #059669; }}
        .negative {{ color: #DC2626; }}
        .warning {{ background-color: #FEF3C7; }}
        .critical {{ background-color: #FEE2E2; }}
        .scroll-container {{
            overflow-x: auto;
            scrollbar-width: thin;
        }}
        .scroll-container::-webkit-scrollbar {{
            height: 6px;
        }}
        .scroll-container::-webkit-scrollbar-track {{
            background: #f1f1f1;
            border-radius: 3px;
        }}
        .scroll-container::-webkit-scrollbar-thumb {{
            background: #c1c1c1;
            border-radius: 3px;
        }}
        .sticky-col {{
            position: sticky;
            left: 0;
            background: white;
            z-index: 10;
            border-right: 2px solid #e5e7eb;
        }}
        .group-detail {{
            transition: all 0.2s;
        }}
        .group-detail:hover {{
            background-color: #f3f4f6;
        }}
        .confidence-bar {{
            height: 4px;
            border-radius: 2px;
            transition: all 0.3s;
        }}
    </style>
</head>
<body class="bg-gray-50">
    <!-- Navigation -->
    <nav class="bg-white shadow-sm border-b">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-16">
                <div class="flex items-center">
                    <h1 class="text-xl font-semibold">💰 CFO Forecast</h1>
                    <span class="ml-4 text-gray-500">Enhanced V2 Dashboard</span>
                    <span class="ml-4 px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full font-medium">
                        🔮 AI-Powered Patterns
                    </span>
                </div>
                <div class="flex items-center space-x-4">
                    <select class="border rounded px-3 py-1">
                        <option>bestself</option>
                    </select>
                    <button class="px-3 py-1 text-sm border rounded hover:bg-gray-50" onclick="toggleGroupView()">
                        📊 Toggle Groups
                    </button>
                    <button class="px-3 py-1 text-sm border rounded hover:bg-gray-50">💾 Export</button>
                    <button class="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700" onclick="refreshForecast()">
                        🔄 Refresh
                    </button>
                </div>
            </div>
        </div>
    </nav>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto px-4 py-6">
        <!-- Period Controls -->
        <div class="flex justify-between items-center mb-6">
            <div>
                <h2 class="text-lg font-semibold">13-Week Enhanced Cash Flow Projection</h2>
                <p class="text-sm text-gray-600">Starting {start_date.strftime('%B %d, %Y')} • Enhanced with V2 Pattern Detection</p>
                <div class="flex items-center mt-2 space-x-4">
                    <div class="flex items-center">
                        <div class="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
                        <span class="text-xs text-gray-600">High Confidence ({high_conf_groups} groups)</span>
                    </div>
                    <div class="flex items-center">
                        <div class="w-3 h-3 bg-yellow-500 rounded-full mr-2"></div>
                        <span class="text-xs text-gray-600">Medium Confidence ({med_conf_groups} groups)</span>
                    </div>
                    <div class="flex items-center">
                        <div class="w-3 h-3 bg-red-500 rounded-full mr-2"></div>
                        <span class="text-xs text-gray-600">Low Confidence ({low_conf_groups} groups)</span>
                    </div>
                </div>
            </div>
            <div class="flex space-x-2">
                <button class="px-3 py-1 text-sm border rounded">← Previous 13 Weeks</button>
                <button class="px-3 py-1 text-sm border rounded">Next 13 Weeks →</button>
            </div>
        </div>

        <!-- Cash Flow Table -->
        <div class="bg-white rounded-lg shadow-lg overflow-hidden">
            <div class="scroll-container">
                <table class="cash-table min-w-full text-sm">
                    <thead class="bg-gray-50">
                        <tr>
                            <th class="sticky-col px-4 py-3 text-left font-medium text-gray-900 min-w-48">Period</th>
                            {week_headers}
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-200">
                        <!-- Starting Balance -->
                        <tr class="bg-blue-50">
                            <td class="sticky-col px-4 py-3 font-medium text-gray-900">Starting Balance</td>
                            <td class="px-4 py-3 text-right font-medium">$45,230</td>
                            {ending_balance_row}
                        </tr>

                        <!-- Deposits (Inflows) -->
                        <tr>
                            <td class="sticky-col px-4 py-3 font-medium text-gray-900 bg-green-50">💰 Total Deposits</td>
                            {deposit_total_row}
                        </tr>

                        <!-- Enhanced Vendor Group Details -->
                        {vendor_group_rows}

                        <!-- Withdrawals (Outflows) -->
                        <tr>
                            <td class="sticky-col px-4 py-3 font-medium text-gray-900 bg-red-50">💸 Total Withdrawals</td>
                            {withdrawal_total_row}
                        </tr>

                        <!-- Net Cash Movement -->
                        <tr class="border-t-2">
                            <td class="sticky-col px-4 py-3 font-bold text-gray-900">📊 Net Cash Movement</td>
                            {net_movement_row}
                        </tr>

                        <!-- Ending Balance -->
                        <tr class="bg-blue-50 border-t-2">
                            <td class="sticky-col px-4 py-3 font-bold text-gray-900">💳 Ending Balance</td>
                            {ending_balance_row}
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Enhanced Summary Cards -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mt-6">
            <div class="bg-white rounded-lg shadow p-6">
                <h3 class="text-lg font-semibold mb-4">🤖 AI Insights</h3>
                <ul class="space-y-2 text-sm">
                    <li class="flex items-start">
                        <span class="text-blue-500 mr-2">🎯</span>
                        <span>Amazon: bi-weekly $44.7k deposits</span>
                    </li>
                    <li class="flex items-start">
                        <span class="text-green-500 mr-2">📈</span>
                        <span>E-commerce: stable $10.3k weekly</span>
                    </li>
                    <li class="flex items-start">
                        <span class="text-purple-500 mr-2">🔍</span>
                        <span>Min balance: ${min_balance:,.0f}</span>
                    </li>
                </ul>
            </div>

            <div class="bg-white rounded-lg shadow p-6">
                <h3 class="text-lg font-semibold mb-4">📊 Pattern Analysis</h3>
                <div class="space-y-3">
                    <div>
                        <div class="flex justify-between text-sm mb-1">
                            <span>Overall Confidence</span>
                            <span class="font-medium">{overall_confidence:.0%}</span>
                        </div>
                        <div class="w-full bg-gray-200 rounded-full h-2">
                            <div class="bg-green-500 h-2 rounded-full confidence-bar" style="width: {overall_confidence:.0%}"></div>
                        </div>
                    </div>
                    <div class="text-xs text-gray-600">
                        <div>• {len(vendor_groups)} active patterns detected</div>
                        <div>• {len([g for g in vendor_groups if 'bi-weekly' in g.get('pattern_frequency', '')])} bi-weekly cycles</div>
                        <div>• {len([g for g in vendor_groups if 'weekly' in g.get('pattern_frequency', '')])} weekly patterns</div>
                    </div>
                </div>
            </div>

            <div class="bg-white rounded-lg shadow p-6">
                <h3 class="text-lg font-semibold mb-4">💡 Recommendations</h3>
                <ul class="space-y-2 text-sm">
                    <li>• Amazon timing override available (Mon vs Tue)</li>
                    <li>• E-commerce grouping optimized</li>
                    <li>• Consider manual overrides for holidays</li>
                    <li>• Review irregular patterns monthly</li>
                </ul>
            </div>

            <div class="bg-white rounded-lg shadow p-6">
                <h3 class="text-lg font-semibold mb-4">🔧 Controls</h3>
                <div class="space-y-2">
                    <button class="w-full text-left px-3 py-2 text-sm border rounded hover:bg-gray-50" onclick="manageGroups()">
                        🏢 Manage Vendor Groups
                    </button>
                    <button class="w-full text-left px-3 py-2 text-sm border rounded hover:bg-gray-50" onclick="viewPatterns()">
                        🔍 View Pattern Details
                    </button>
                    <button class="w-full text-left px-3 py-2 text-sm border rounded hover:bg-gray-50" onclick="manualOverride()">
                        ✏️ Manual Overrides
                    </button>
                    <button class="w-full text-left px-3 py-2 text-sm border rounded hover:bg-gray-50" onclick="exportData()">
                        📄 Export Data
                    </button>
                </div>
            </div>
        </div>
    </main>

    <script>
        function toggleGroupView() {{
            const groupRows = document.querySelectorAll('.group-detail');
            groupRows.forEach(row => {{
                row.style.display = row.style.display === 'none' ? '' : 'none';
            }});
        }}

        function refreshForecast() {{
            alert('🔄 Refreshing forecasts with latest V2 patterns...');
            // In real implementation, this would call the forecast API
        }}

        function manageGroups() {{
            alert('🏢 Vendor Group Management UI would open here');
            // Future: Open vendor grouping interface
        }}

        function viewPatterns() {{
            alert('🔍 Pattern Analysis Details would open here');
            // Future: Show detailed pattern analysis
        }}

        function manualOverride() {{
            alert('✏️ Manual Override Interface would open here');
            // Future: Allow editing individual forecasts
        }}

        function exportData() {{
            alert('📄 Export functionality would download CSV/Excel here');
            // Future: Export forecast data
        }}

        // Auto-refresh every 5 minutes
        setInterval(() => {{
            console.log('Auto-refreshing forecast data...');
        }}, 300000);
    </script>
</body>
</html>'''
    
    # Write the enhanced dashboard
    output_file = '/Users/jeffreydebolt/Documents/cfo_forecast_refactored/enhanced_dashboard_v2.html'
    
    with open(output_file, 'w') as f:
        f.write(html_content)
    
    print(f"✅ Enhanced dashboard generated: {output_file}")
    print(f"📊 Features included:")
    print(f"   • Real V2 forecast data")
    print(f"   • {len(vendor_groups)} vendor groups with patterns")
    print(f"   • Pattern confidence indicators")
    print(f"   • Enhanced insights and recommendations")
    print(f"   • Interactive controls (placeholders)")
    
    return output_file

def main():
    """Main function."""
    print("🚀 ENHANCED DASHBOARD GENERATOR")
    print("=" * 70)
    
    dashboard_file = generate_enhanced_dashboard()
    
    if dashboard_file:
        print(f"\n🎉 ENHANCED DASHBOARD READY!")
        print(f"📁 File: {dashboard_file}")
        print(f"🌐 Open in browser to view")
        print(f"✨ Features V2 forecasting with pattern detection")
    else:
        print(f"\n❌ Failed to generate enhanced dashboard")

if __name__ == "__main__":
    main()