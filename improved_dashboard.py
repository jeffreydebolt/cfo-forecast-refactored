#!/usr/bin/env python3
"""
Generate improved dashboard with proper categorization and expandable sections.
"""

import sys
sys.path.append('.')

from database.forecast_db_manager import forecast_db
from datetime import date, timedelta
import json

def analyze_vendor_categories():
    """Analyze vendors and categorize them properly based on transaction patterns."""
    print("🔍 ANALYZING VENDOR CATEGORIES")
    print("=" * 50)
    
    client_id = 'bestself'
    
    try:
        # Get all vendor groups
        vendor_groups = forecast_db.get_vendor_groups(client_id)
        
        # Get forecasts to analyze amounts
        start_date = date(2025, 8, 4)
        end_date = start_date + timedelta(weeks=13)
        forecasts = forecast_db.get_forecasts(client_id, start_date, end_date)
        
        # Analyze each vendor group
        categories = {
            'inflows': [],
            'cc': [],
            'people': [],
            'inventory': [],
            'admin': [],
            'financing': []
        }
        
        for group in vendor_groups:
            group_name = group['group_name']
            
            # Get forecasts for this group
            group_forecasts = [f for f in forecasts if f['vendor_group_name'] == group_name]
            
            if not group_forecasts:
                continue
                
            # Calculate average amount
            amounts = [float(f['forecast_amount']) for f in group_forecasts]
            avg_amount = sum(amounts) / len(amounts) if amounts else 0
            total_positive = sum(amt for amt in amounts if amt > 0)
            total_negative = sum(amt for amt in amounts if amt < 0)
            
            # Determine if primarily deposits or withdrawals
            is_deposit = total_positive > abs(total_negative)
            
            vendor_data = {
                'name': group_name,
                'avg_amount': avg_amount,
                'is_deposit': is_deposit,
                'frequency': group.get('pattern_frequency', 'irregular'),
                'timing': group.get('pattern_timing', ''),
                'forecasts': len(group_forecasts)
            }
            
            # Categorize based on name and deposit/withdrawal pattern
            if is_deposit:
                categories['inflows'].append(vendor_data)
            else:
                # Categorize withdrawals
                name_lower = group_name.lower()
                if any(term in name_lower for term in ['credit', 'card', 'amex', 'express']):
                    categories['cc'].append(vendor_data)
                elif any(term in name_lower for term in ['wise', 'contractor', 'payroll', 'people']):
                    categories['people'].append(vendor_data)
                elif any(term in name_lower for term in ['inventory', 'stock', 'goods']):
                    categories['inventory'].append(vendor_data)
                elif any(term in name_lower for term in ['admin', 'fee', 'wire', 'bank']):
                    categories['admin'].append(vendor_data)
                else:
                    categories['admin'].append(vendor_data)  # Default to admin
        
        print(f"📊 Categorization Results:")
        for cat, vendors in categories.items():
            print(f"   {cat}: {len(vendors)} vendors")
            
        return categories
        
    except Exception as e:
        print(f"❌ Error analyzing categories: {e}")
        return None

def generate_improved_dashboard():
    """Generate improved dashboard with proper categorization."""
    print("🚀 GENERATING IMPROVED DASHBOARD")
    print("=" * 50)
    
    # Analyze categories
    categories = analyze_vendor_categories()
    if not categories:
        print("❌ Failed to analyze categories")
        return
    
    # Get forecast data
    client_id = 'bestself'
    start_date = date(2025, 8, 4)
    end_date = start_date + timedelta(weeks=13)
    forecasts = forecast_db.get_forecasts(client_id, start_date, end_date)
    
    # Organize data by week
    weekly_data = {}
    for week_num in range(13):
        week_start = start_date + timedelta(weeks=week_num)
        week_end = week_start + timedelta(days=6)
        
        # Get forecasts for this week
        week_forecasts = [f for f in forecasts 
                        if week_start <= date.fromisoformat(f['forecast_date']) <= week_end]
        
        weekly_data[week_num] = {
            'week_start': week_start,
            'week_end': week_end,
            'forecasts': week_forecasts
        }
    
    # Generate week headers
    week_headers = ""
    for week_num in range(13):
        week_data = weekly_data[week_num]
        week_start = week_data['week_start']
        week_end = week_data['week_end']
        week_headers += f'''
            <th class="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider min-w-20">
                Week {week_num + 1}<br>
                <span class="font-normal text-xs text-gray-400">{week_start.strftime('%m/%d')}</span>
            </th>'''
    
    def generate_category_rows(category_name, vendors, category_class=""):
        """Generate rows for a category with expandable details."""
        if not vendors:
            return ""
        
        category_id = category_name.lower().replace(' ', '-')
        
        # Calculate category totals for each week
        category_totals = []
        for week_num in range(13):
            week_forecasts = weekly_data[week_num]['forecasts']
            week_total = sum(float(f['forecast_amount']) for f in week_forecasts 
                           if any(v['name'] == f['vendor_group_name'] for v in vendors))
            category_totals.append(week_total)
        
        # Category header row
        total_cells = ""
        for total in category_totals:
            if total != 0:
                color_class = "text-green-600" if total > 0 else "text-red-600"
                sign = "+" if total > 0 else ""
                total_cells += f'<td class="px-3 py-2 text-right text-sm font-medium {color_class}">{sign}${abs(total):,.0f}</td>'
            else:
                total_cells += '<td class="px-3 py-2 text-right text-sm text-gray-400">—</td>'
        
        rows = f'''
        <tr class="category-header {category_class}" onclick="toggleCategory('{category_id}')">
            <td class="px-4 py-3 font-semibold text-gray-900 cursor-pointer">
                <span class="expand-icon mr-2">▼</span>{category_name}
            </td>
            {total_cells}
        </tr>'''
        
        # Detail rows for each vendor
        for vendor in vendors:
            vendor_cells = ""
            for week_num in range(13):
                week_forecasts = weekly_data[week_num]['forecasts']
                vendor_amount = sum(float(f['forecast_amount']) for f in week_forecasts 
                                  if f['vendor_group_name'] == vendor['name'])
                
                if vendor_amount != 0:
                    color_class = "text-green-600" if vendor_amount > 0 else "text-red-600"
                    sign = "+" if vendor_amount > 0 else ""
                    vendor_cells += f'<td class="px-3 py-2 text-right text-xs {color_class}">{sign}${abs(vendor_amount):,.0f}</td>'
                else:
                    vendor_cells += '<td class="px-3 py-2 text-right text-xs text-gray-400">—</td>'
            
            frequency_badge = f'<span class="ml-2 px-1 py-0 text-xs bg-blue-100 text-blue-800 rounded">{vendor["frequency"]}</span>' if vendor["frequency"] != "irregular" else ""
            
            rows += f'''
            <tr class="vendor-detail {category_id}-details bg-gray-50">
                <td class="px-8 py-2 text-sm text-gray-700">
                    {vendor['name']}{frequency_badge}
                </td>
                {vendor_cells}
            </tr>'''
        
        return rows
    
    # Generate all category sections
    inflows_section = generate_category_rows("Inflows", categories['inflows'], "bg-green-50")
    cc_section = generate_category_rows("CC", categories['cc'], "bg-red-50")
    people_section = generate_category_rows("People", categories['people'], "bg-red-50")
    inventory_section = generate_category_rows("Inventory", categories['inventory'], "bg-red-50")
    admin_section = generate_category_rows("Admin", categories['admin'], "bg-red-50")
    
    # Calculate total operating outflows
    operating_totals = []
    for week_num in range(13):
        week_forecasts = weekly_data[week_num]['forecasts']
        outflow_vendors = categories['cc'] + categories['people'] + categories['inventory'] + categories['admin']
        week_outflow = sum(float(f['forecast_amount']) for f in week_forecasts 
                         if any(v['name'] == f['vendor_group_name'] for v in outflow_vendors))
        operating_totals.append(week_outflow)
    
    operating_total_cells = ""
    for total in operating_totals:
        if total != 0:
            operating_total_cells += f'<td class="px-3 py-2 text-right font-bold text-red-600">-${abs(total):,.0f}</td>'
        else:
            operating_total_cells += '<td class="px-3 py-2 text-right font-bold text-gray-400">—</td>'
    
    # Calculate net cash flow
    net_totals = []
    running_balance = 74860  # Starting balance from your example
    balance_cells = ""
    
    for week_num in range(13):
        week_forecasts = weekly_data[week_num]['forecasts']
        week_inflow = sum(float(f['forecast_amount']) for f in week_forecasts 
                        if any(v['name'] == f['vendor_group_name'] for v in categories['inflows']))
        week_outflow = sum(float(f['forecast_amount']) for f in week_forecasts 
                         if f['vendor_group_name'] not in [v['name'] for v in categories['inflows']])
        
        net_movement = week_inflow + week_outflow  # outflow is negative
        net_totals.append(net_movement)
        running_balance += net_movement
        
        # Net movement cells
        color_class = "text-green-600" if net_movement >= 0 else "text-red-600"
        sign = "+" if net_movement >= 0 else ""
        
        # Balance cells
        balance_color = "text-red-600 bg-red-100" if running_balance < 10000 else "text-gray-900"
        balance_cells += f'<td class="px-3 py-2 text-right font-bold {balance_color}">${running_balance:,.0f}</td>'
    
    net_cells = ""
    for net in net_totals:
        color_class = "text-green-600" if net >= 0 else "text-red-600"
        sign = "+" if net >= 0 else ""
        net_cells += f'<td class="px-3 py-2 text-right font-bold {color_class}">{sign}${abs(net):,.0f}</td>'
    
    # Generate HTML
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CFO Forecast - Improved Layout</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .category-header {{
            cursor: pointer;
            transition: all 0.2s;
        }}
        .category-header:hover {{
            background-color: #f3f4f6;
        }}
        .vendor-detail {{
            transition: all 0.3s;
        }}
        .expand-icon {{
            transition: transform 0.2s;
            display: inline-block;
        }}
        .collapsed .expand-icon {{
            transform: rotate(-90deg);
        }}
        .cash-table {{ 
            font-family: 'Monaco', 'Menlo', monospace; 
            font-size: 12px;
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
    </style>
</head>
<body class="bg-gray-50">
    <!-- Navigation -->
    <nav class="bg-white shadow-sm border-b">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-16">
                <div class="flex items-center">
                    <h1 class="text-xl font-semibold">💰 CFO Forecast</h1>
                    <span class="ml-4 text-gray-500">Improved Layout</span>
                </div>
                <div class="flex items-center space-x-4">
                    <select class="border rounded px-3 py-1">
                        <option>bestself</option>
                    </select>
                    <button class="px-3 py-1 text-sm border rounded hover:bg-gray-50" onclick="expandAll()">
                        📂 Expand All
                    </button>
                    <button class="px-3 py-1 text-sm border rounded hover:bg-gray-50" onclick="collapseAll()">
                        📁 Collapse All
                    </button>
                    <button class="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700">
                        🔄 Refresh
                    </button>
                </div>
            </div>
        </div>
    </nav>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto px-4 py-6">
        <!-- Header -->
        <div class="mb-6">
            <h2 class="text-lg font-semibold">13-Week Cash Flow Forecast</h2>
            <p class="text-sm text-gray-600">Starting {start_date.strftime('%m/%d/%Y')} • Updated with V2 Enhanced Patterns</p>
        </div>

        <!-- Starting Balances -->
        <div class="bg-white rounded-lg shadow mb-4 p-4">
            <div class="text-sm text-gray-600 mb-2">Cash Balance as of {start_date.strftime('%m/%d/%Y')}:</div>
            <div class="text-xl font-bold text-blue-600">$74,860.07</div>
        </div>

        <!-- Cash Flow Table -->
        <div class="bg-white rounded-lg shadow-lg overflow-hidden">
            <div class="scroll-container">
                <table class="cash-table min-w-full divide-y divide-gray-200">
                    <thead class="bg-gray-50">
                        <tr>
                            <th class="sticky-col px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider min-w-48">
                                Category
                            </th>
                            {week_headers}
                        </tr>
                    </thead>
                    <tbody class="bg-white divide-y divide-gray-200">
                        <!-- INFLOWS SECTION -->
                        {inflows_section}

                        <!-- OPERATING OUTFLOWS HEADER -->
                        <tr class="bg-gray-100">
                            <td colspan="14" class="px-4 py-3 font-semibold text-gray-900">
                                Operating Outflows
                            </td>
                        </tr>

                        <!-- CC SECTION -->
                        {cc_section}

                        <!-- PEOPLE SECTION -->
                        {people_section}

                        <!-- INVENTORY SECTION (if any) -->
                        {inventory_section}

                        <!-- ADMIN SECTION -->
                        {admin_section}

                        <!-- TOTAL OPERATING OUTFLOWS -->
                        <tr class="bg-red-100 border-t-2">
                            <td class="px-4 py-3 font-bold text-gray-900">Total Operating Outflows</td>
                            {operating_total_cells}
                        </tr>

                        <!-- NET CASH FLOW -->
                        <tr class="bg-blue-100 border-t-2">
                            <td class="px-4 py-3 font-bold text-gray-900">Net Cash Flow</td>
                            {net_cells}
                        </tr>

                        <!-- ENDING BALANCE -->
                        <tr class="bg-blue-200 border-t-2">
                            <td class="px-4 py-3 font-bold text-gray-900">Cash Balance Ending</td>
                            {balance_cells}
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </main>

    <script>
        function toggleCategory(categoryId) {{
            const details = document.querySelectorAll('.' + categoryId + '-details');
            const header = document.querySelector('[onclick*="' + categoryId + '"]');
            const icon = header.querySelector('.expand-icon');
            
            const isCollapsed = header.classList.contains('collapsed');
            
            if (isCollapsed) {{
                header.classList.remove('collapsed');
                details.forEach(row => row.style.display = '');
                icon.textContent = '▼';
            }} else {{
                header.classList.add('collapsed');
                details.forEach(row => row.style.display = 'none');
                icon.textContent = '▶';
            }}
        }}

        function expandAll() {{
            document.querySelectorAll('.category-header').forEach(header => {{
                header.classList.remove('collapsed');
                const icon = header.querySelector('.expand-icon');
                if (icon) icon.textContent = '▼';
            }});
            document.querySelectorAll('.vendor-detail').forEach(row => row.style.display = '');
        }}

        function collapseAll() {{
            document.querySelectorAll('.category-header').forEach(header => {{
                header.classList.add('collapsed');
                const icon = header.querySelector('.expand-icon');
                if (icon) icon.textContent = '▶';
            }});
            document.querySelectorAll('.vendor-detail').forEach(row => row.style.display = 'none');
        }}

        // Start with some categories collapsed
        document.addEventListener('DOMContentLoaded', function() {{
            // Collapse inventory and admin by default if they have few items
            setTimeout(() => {{
                const categoriesToCollapse = ['inventory', 'admin'];
                categoriesToCollapse.forEach(cat => {{
                    const details = document.querySelectorAll('.' + cat + '-details');
                    if (details.length <= 2) {{
                        toggleCategory(cat);
                    }}
                }});
            }}, 100);
        }});
    </script>
</body>
</html>'''
    
    # Write the improved dashboard
    output_file = '/Users/jeffreydebolt/Documents/cfo_forecast_refactored/improved_dashboard.html'
    
    with open(output_file, 'w') as f:
        f.write(html_content)
    
    print(f"✅ Improved dashboard generated: {output_file}")
    print(f"📊 Features:")
    print(f"   • Fixed Amazon duplication")
    print(f"   • Proper deposit/withdrawal categorization")
    print(f"   • Expandable/collapsible categories")
    print(f"   • Layout matches your examples")
    
    return output_file

def main():
    """Main function."""
    print("🚀 IMPROVED DASHBOARD GENERATOR")
    print("=" * 70)
    
    dashboard_file = generate_improved_dashboard()
    
    if dashboard_file:
        print(f"\n🎉 IMPROVED DASHBOARD READY!")
        print(f"📁 File: {dashboard_file}")
        print(f"🌐 Open in browser to view")
        print(f"✨ Fixed issues and matches your layout preference")

if __name__ == "__main__":
    main()