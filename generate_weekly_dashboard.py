#!/usr/bin/env python3
"""
Generate HTML dashboard with real data from Supabase
"""
import sys
sys.path.append('.')
from supabase_client import supabase
from datetime import datetime, date, timedelta
from collections import defaultdict

def get_monday(date_obj):
    """Get Monday of the week containing date_obj"""
    days = date_obj.weekday()
    return date_obj - timedelta(days=days)

def format_currency(amount):
    """Format amount as currency"""
    if amount == 0:
        return ""
    prefix = "-$" if amount < 0 else "$"
    return f"{prefix}{abs(amount):,.0f}"

def generate_dashboard(client_id='BestSelf'):
    print(f"Generating dashboard for {client_id}...")
    
    # Get date range from FORECAST transactions
    result = supabase.table('transactions').select('transaction_date').eq('client_id', client_id).eq('type', 'FORECAST').order('transaction_date').limit(1).execute()
    if not result.data:
        print("No forecast transactions found")
        return
    
    first_date = datetime.strptime(result.data[0]['transaction_date'], '%Y-%m-%d').date()
    start_monday = get_monday(first_date)
    end_date = start_monday + timedelta(days=13*7)
    
    print(f"Date range: {start_monday} to {end_date}")
    
    # Get forecast transactions (not historical raw data)
    transactions = supabase.table('transactions').select('*').eq('client_id', client_id).eq('type', 'FORECAST').gte('transaction_date', start_monday.isoformat()).lte('transaction_date', end_date.isoformat()).execute()
    
    print(f"Found {len(transactions.data)} transactions")
    
    # Group by vendor and week
    vendor_week_data = defaultdict(lambda: [0] * 13)
    week_totals = [0] * 13
    
    for txn in transactions.data:
        vendor = txn['vendor_name']
        txn_date = datetime.strptime(txn['transaction_date'], '%Y-%m-%d').date()
        week_num = (txn_date - start_monday).days // 7
        
        if 0 <= week_num < 13:
            vendor_week_data[vendor][week_num] += txn['amount']
            week_totals[week_num] += txn['amount']
    
    # Generate HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CFO Forecast - {client_id}</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50">
    <nav class="bg-white shadow-sm border-b">
        <div class="max-w-7xl mx-auto px-4 py-4">
            <h1 class="text-2xl font-bold">💰 CFO Forecast - {client_id}</h1>
        </div>
    </nav>

    <main class="max-w-7xl mx-auto px-4 py-6">
        <!-- Starting Balance -->
        <div class="bg-white rounded-lg shadow p-6 mb-6">
            <div class="text-sm text-gray-600">Starting Cash Balance</div>
            <div class="text-3xl font-bold text-gray-800">$100,000</div>
            <div class="text-sm text-gray-500 mt-1">As of {start_monday.strftime('%m/%d/%Y')}</div>
        </div>

        <!-- 13-Week Table -->
        <div class="bg-white rounded-lg shadow overflow-hidden">
            <div class="overflow-x-auto">
                <table class="min-w-full">
                    <thead class="bg-gray-800 text-white">
                        <tr>
                            <th class="px-6 py-3 text-left text-sm font-semibold">Vendor/Group</th>"""
    
    # Week headers
    for i in range(13):
        week_start = start_monday + timedelta(days=i*7)
        html += f"""
                            <th class="px-4 py-3 text-center text-sm font-semibold min-w-[100px]">
                                Week {i+1}<br>
                                <span class="text-xs font-normal">{week_start.strftime('%m/%d')}</span>
                            </th>"""
    
    html += """
                            <th class="px-4 py-3 text-center text-sm font-semibold">Total</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-200">"""
    
    # Vendor rows
    for vendor, weeks in sorted(vendor_week_data.items()):
        vendor_total = sum(weeks)
        total_class = "text-green-600" if vendor_total > 0 else "text-red-600" if vendor_total < 0 else ""
        
        html += f"""
                        <tr class="hover:bg-gray-50">
                            <td class="px-6 py-3 text-sm font-medium">{vendor}</td>"""
        
        for amount in weeks:
            color_class = "text-green-600" if amount > 0 else "text-red-600" if amount < 0 else ""
            html += f"""
                            <td class="px-4 py-3 text-center text-sm {color_class}">{format_currency(amount)}</td>"""
        
        html += f"""
                            <td class="px-4 py-3 text-center text-sm font-medium {total_class}">{format_currency(vendor_total)}</td>
                        </tr>"""
    
    # Footer rows
    html += """
                    </tbody>
                    <tfoot class="bg-gray-100 font-bold">
                        <tr>
                            <td class="px-6 py-3">Net Cash Flow</td>"""
    
    running_balance = 100000
    grand_total = 0
    
    for total in week_totals:
        color_class = "text-green-600" if total > 0 else "text-red-600" if total < 0 else ""
        html += f"""
                            <td class="px-4 py-3 text-center text-sm {color_class}">{format_currency(total)}</td>"""
        grand_total += total
    
    total_class = "text-green-600" if grand_total > 0 else "text-red-600" if grand_total < 0 else ""
    html += f"""
                            <td class="px-4 py-3 text-center text-sm {total_class}">{format_currency(grand_total)}</td>
                        </tr>
                        <tr class="bg-gray-200">
                            <td class="px-6 py-3">Ending Balance</td>"""
    
    # Balance row
    for total in week_totals:
        running_balance += total
        balance_class = "text-red-600 font-bold" if running_balance < 0 else ""
        html += f"""
                            <td class="px-4 py-3 text-center text-sm {balance_class}">{format_currency(running_balance)}</td>"""
    
    html += f"""
                            <td class="px-4 py-3 text-center text-sm">{format_currency(running_balance)}</td>
                        </tr>
                    </tfoot>
                </table>
            </div>
        </div>
    </main>
</body>
</html>"""
    
    # Save HTML
    filename = f'{client_id}_weekly_dashboard.html'
    with open(filename, 'w') as f:
        f.write(html)
    
    print(f"Generated: {filename}")
    return filename

if __name__ == "__main__":
    client = sys.argv[1] if len(sys.argv) > 1 else 'BestSelf'
    filename = generate_dashboard(client)
    
    # Open in browser
    import webbrowser
    import os
    full_path = os.path.abspath(filename)
    webbrowser.open(f'file://{full_path}')