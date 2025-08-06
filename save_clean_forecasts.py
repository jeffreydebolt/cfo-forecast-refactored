#!/usr/bin/env python3
"""
Save Clean Forecasts to Database
Use the 70 generated clean forecasts and save them properly
"""

import sys
sys.path.append('.')

from simple_clean_forecasting import SimpleCleanForecasting
from database.forecast_db_manager import forecast_db
from supabase_client import supabase
from datetime import datetime, date

def save_clean_forecasts_to_db(client_id: str = 'bestself'):
    """Save the 70 clean forecasts to database"""
    print("💾 SAVING CLEAN FORECASTS TO DATABASE")
    print("=" * 60)
    
    forecaster = SimpleCleanForecasting()
    
    # Generate the clean forecasts
    analysis_results = forecaster.analyze_client_patterns(client_id)
    forecasts = forecaster.generate_clean_forecasts(client_id, analysis_results, weeks_ahead=13)
    
    print(f"Generated {len(forecasts)} clean forecasts")
    
    # Use the create_forecasts method (plural)
    try:
        result = forecast_db.create_forecasts(forecasts)
        if result.get('success'):
            print(f"✅ Successfully saved {len(forecasts)} forecasts to database")
            return True
        else:
            print(f"❌ Failed to save forecasts: {result.get('error', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"❌ Error saving forecasts: {e}")
        return False

def create_simple_clean_dashboard(client_id: str = 'bestself'):
    """Create dashboard using the simple clean forecasts"""
    print("\n🎨 CREATING SIMPLE CLEAN DASHBOARD")
    print("=" * 60)
    
    from datetime import timedelta
    
    forecaster = SimpleCleanForecasting()
    analysis_results = forecaster.analyze_client_patterns(client_id)
    
    # Get forecasts from database
    start_date = date(2025, 8, 4)
    end_date = start_date + timedelta(weeks=13)
    forecasts = forecast_db.get_forecasts(client_id, start_date, end_date)
    
    print(f"Retrieved {len(forecasts)} forecasts from database")
    
    # Organize by week for dashboard
    from collections import defaultdict
    
    weekly_data = defaultdict(lambda: {'inflows': 0, 'outflows': 0, 'vendors': []})
    
    for forecast in forecasts:
        forecast_date = date.fromisoformat(forecast['forecast_date'])
        amount = float(forecast['forecast_amount'])
        vendor = forecast['vendor_group_name']
        
        # Calculate which week this belongs to
        week_num = (forecast_date - start_date).days // 7
        if 0 <= week_num < 13:  # Only include 13 weeks
            if amount > 0:
                weekly_data[week_num]['inflows'] += amount
            else:
                weekly_data[week_num]['outflows'] += abs(amount)
            
            weekly_data[week_num]['vendors'].append({
                'name': vendor,
                'amount': amount,
                'date': forecast_date.isoformat()
            })
    
    # Create simple HTML dashboard
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CFO Forecast - Simple Clean System</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .positive {{ color: #059669; }}
        .negative {{ color: #DC2626; }}
        .reliable {{ background-color: #F0FDF4; }}
        .manual {{ background-color: #FEF3E2; }}
    </style>
</head>
<body class="bg-gray-50">
    <nav class="bg-white shadow-sm border-b">
        <div class="max-w-7xl mx-auto px-4 py-4">
            <h1 class="text-2xl font-bold">💰 CFO Forecast - Simple Clean System</h1>
            <p class="text-gray-600">Mathematical pattern detection • No duplicates • Clean forecasting</p>
        </div>
    </nav>

    <main class="max-w-7xl mx-auto px-4 py-6">
        <!-- System Status -->
        <div class="bg-white rounded-lg shadow p-6 mb-6">
            <h2 class="text-lg font-semibold mb-4">🎯 Simple Clean System Status</h2>
            <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div class="text-center">
                    <div class="text-2xl font-bold text-green-600">{len(analysis_results)}</div>
                    <div class="text-sm text-gray-600">Unique Vendors</div>
                    <div class="text-xs text-gray-500">No duplicates</div>
                </div>
                <div class="text-center">
                    <div class="text-2xl font-bold text-blue-600">{len([v for v in analysis_results.values() if v['pattern']['confidence'] >= 0.6])}</div>
                    <div class="text-sm text-gray-600">Reliable Patterns</div>
                    <div class="text-xs text-gray-500">60%+ confidence</div>
                </div>
                <div class="text-center">
                    <div class="text-2xl font-bold text-orange-600">{len([v for v in analysis_results.values() if v['pattern']['confidence'] < 0.6])}</div>
                    <div class="text-sm text-gray-600">Manual Setup</div>
                    <div class="text-xs text-gray-500">Irregular patterns</div>
                </div>
                <div class="text-center">
                    <div class="text-2xl font-bold text-purple-600">{len(forecasts)}</div>
                    <div class="text-sm text-gray-600">Clean Forecasts</div>
                    <div class="text-xs text-gray-500">Specific dates & amounts</div>
                </div>
            </div>
        </div>

        <!-- Vendor Pattern Analysis -->
        <div class="bg-white rounded-lg shadow p-6 mb-6">
            <h2 class="text-lg font-semibold mb-4">📊 Simple Pattern Detection Results</h2>
            <div class="space-y-3">'''
    
    for vendor_name, analysis in analysis_results.items():
        pattern = analysis['pattern']
        is_reliable = pattern['confidence'] >= 0.6
        status_class = "reliable" if is_reliable else "manual"
        status_icon = "✅" if is_reliable else "⚠️"
        
        if pattern['frequency'] != 'irregular':
            pattern_text = f"{pattern['frequency']} ${pattern['average_amount']:,.2f}"
        else:
            pattern_text = "Irregular pattern - needs manual setup"
        
        html_content += f'''
                <div class="flex items-center justify-between p-3 rounded-lg {status_class}">
                    <div class="flex items-center">
                        <span class="mr-3 text-lg">{status_icon}</span>
                        <div>
                            <div class="font-medium">{vendor_name}</div>
                            <div class="text-sm text-gray-600">{pattern_text}</div>
                        </div>
                    </div>
                    <div class="text-right">
                        <div class="text-sm font-medium">{pattern['confidence']:.0%} confidence</div>
                        <div class="text-xs text-gray-500">{analysis['transaction_count']} transactions</div>
                    </div>
                </div>'''
    
    # Add weekly forecast table
    html_content += f'''
            </div>
        </div>

        <!-- 13-Week Clean Forecast -->
        <div class="bg-white rounded-lg shadow overflow-hidden">
            <div class="px-6 py-4 border-b">
                <h2 class="text-lg font-semibold">📅 13-Week Clean Forecast (Starting {start_date.strftime('%B %d, %Y')})</h2>
                <p class="text-sm text-gray-600">Mathematical pattern detection • No business logic complexity</p>
            </div>
            
            <div class="overflow-x-auto">
                <table class="min-w-full">
                    <thead class="bg-gray-50">
                        <tr>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Week</th>
                            <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Inflows</th>
                            <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Outflows</th>
                            <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Net</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Details</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-200">'''
    
    running_balance = 45230  # Starting balance
    for week_num in range(13):
        week_start = start_date + timedelta(weeks=week_num)
        week_data = weekly_data[week_num]
        
        inflows = week_data['inflows']
        outflows = week_data['outflows']
        net = inflows - outflows
        running_balance += net
        
        net_class = "positive" if net >= 0 else "negative"
        balance_class = "text-red-600 font-bold" if running_balance < 20000 else ""
        
        # Create vendor detail string
        vendor_details = []
        for vendor in week_data['vendors'][:3]:  # Show top 3
            vendor_details.append(f"{vendor['name']}: ${vendor['amount']:,.0f}")
        detail_text = " • ".join(vendor_details)
        if len(week_data['vendors']) > 3:
            detail_text += f" • +{len(week_data['vendors'])-3} more"
        
        html_content += f'''
                        <tr>
                            <td class="px-6 py-4 whitespace-nowrap">
                                <div class="font-medium">Week {week_num + 1}</div>
                                <div class="text-sm text-gray-500">{week_start.strftime('%b %d')}</div>
                                <div class="text-xs {balance_class}">Balance: ${running_balance:,.0f}</div>
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap text-right positive font-medium">
                                +${inflows:,.0f}
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap text-right negative font-medium">
                                -${outflows:,.0f}
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap text-right font-bold {net_class}">
                                {"+" if net >= 0 else ""}${net:,.0f}
                            </td>
                            <td class="px-6 py-4 text-sm text-gray-600">
                                {detail_text if detail_text else "No forecasts"}
                            </td>
                        </tr>'''
    
    html_content += '''
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Algorithm Explanation -->
        <div class="bg-white rounded-lg shadow p-6 mt-6">
            <h2 class="text-lg font-semibold mb-4">🧠 Simple Clean Algorithm</h2>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                    <h3 class="font-medium mb-2">1. Clean Vendor Grouping</h3>
                    <ul class="text-sm text-gray-600 space-y-1">
                        <li>• Group by display_name only</li>
                        <li>• No duplicates (Amazon = ONE group)</li>
                        <li>• No complex classification</li>
                    </ul>
                </div>
                <div>
                    <h3 class="font-medium mb-2">2. Simple Pattern Detection</h3>
                    <ul class="text-sm text-gray-600 space-y-1">
                        <li>• Calculate gaps between transactions</li>
                        <li>• 60%+ consistency = reliable pattern</li>
                        <li>• Average amount from recent history</li>
                    </ul>
                </div>
                <div>
                    <h3 class="font-medium mb-2">3. Generate Future Dates</h3>
                    <ul class="text-sm text-gray-600 space-y-1">
                        <li>• Apply pattern interval forward</li>
                        <li>• Specific calendar dates</li>
                        <li>• 13 weeks of forecasts</li>
                    </ul>
                </div>
            </div>
        </div>
    </main>
</body>
</html>'''
    
    # Save dashboard
    dashboard_file = '/Users/jeffreydebolt/Documents/cfo_forecast_refactored/simple_clean_dashboard.html'
    with open(dashboard_file, 'w') as f:
        f.write(html_content)
    
    print(f"✅ Created simple clean dashboard: {dashboard_file}")
    return dashboard_file

if __name__ == "__main__":
    print("🚀 SAVING CLEAN FORECASTS AND CREATING DASHBOARD")
    print("=" * 80)
    
    from datetime import timedelta
    
    # Save forecasts to database
    success = save_clean_forecasts_to_db('bestself')
    
    # Create clean dashboard
    if success:
        dashboard_file = create_simple_clean_dashboard('bestself')
        print(f"\n🎉 SUCCESS!")
        print(f"✅ Clean forecasts saved to database")
        print(f"📊 Simple clean dashboard created: {dashboard_file}")
        print(f"🔄 Complex enhanced system has been replaced")
    else:
        print(f"\n⚠️  Forecasts not saved to database, but dashboard can still be created")
        dashboard_file = create_simple_clean_dashboard('bestself')
        print(f"📊 Dashboard created: {dashboard_file}")