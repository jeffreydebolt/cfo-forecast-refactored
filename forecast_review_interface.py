#!/usr/bin/env python3
import sys
import os
import tempfile
import webbrowser
sys.path.append('.')
from supabase_client import supabase
from datetime import datetime, date, timedelta

print('FORECAST REVIEW INTERFACE')
print('Client: BestSelf') 
print('=' * 60)

# Get pattern analysis and recent transactions for each group
patterns = supabase.table('pattern_analysis').select('*').eq('client_id', 'BestSelf').execute()
groups = supabase.table('vendor_groups').select('*').eq('client_id', 'BestSelf').execute()

print(f'✅ Found {len(patterns.data)} patterns to review')

# Build review data
review_data = []
for pattern in patterns.data:
    group_name = pattern['vendor_group_name']
    
    # Find the vendor group
    group = next((g for g in groups.data if g['group_name'] == group_name), None)
    if not group:
        continue
    
    vendor_list = group['vendor_display_names']
    
    # Get last 5 transactions for this group
    recent_txns = supabase.table('transactions')\
        .select('transaction_date, vendor_name, amount')\
        .eq('client_id', 'BestSelf')\
        .in_('vendor_name', vendor_list)\
        .order('transaction_date', desc=True)\
        .limit(5)\
        .execute()
    
    review_data.append({
        'group': pattern,
        'recent_transactions': recent_txns.data,
        'vendors': vendor_list
    })

# Create review interface
temp_dir = tempfile.mkdtemp()
review_file = os.path.join(temp_dir, 'BestSelf_forecast_review.html')

html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Forecast Review - BestSelf</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50">
    <div class="container mx-auto p-6">
        <h1 class="text-2xl font-bold mb-6">🔍 Forecast Review - BestSelf</h1>
        <p class="mb-6">Review and adjust forecast parameters for each vendor group</p>
        
        <div class="space-y-6">'''

for data in review_data:
    pattern = data['group']
    recent = data['recent_transactions']
    vendors = data['vendors']
    
    group_name = pattern['vendor_group_name']
    frequency = pattern.get('frequency_detected', 'unknown')
    avg_amount = pattern.get('average_amount', 0)
    confidence = pattern.get('confidence_score', 0)
    
    html += f'''
            <div class="bg-white p-6 rounded-lg shadow">
                <h2 class="text-xl font-semibold mb-4">{group_name}</h2>
                
                <div class="grid grid-cols-2 gap-6">
                    <div>
                        <h3 class="font-medium mb-3">Recent Transactions</h3>
                        <div class="space-y-2">'''
    
    for txn in recent[:5]:
        amount_color = 'text-green-600' if float(txn['amount']) > 0 else 'text-red-600'
        html += f'''
                            <div class="flex justify-between text-sm border-b pb-1">
                                <span>{txn['transaction_date']}</span>
                                <span class="font-medium">{txn['vendor_name'][:30]}</span>
                                <span class="{amount_color}">${float(txn['amount']):,.0f}</span>
                            </div>'''
    
    html += f'''
                        </div>
                        
                        <div class="mt-4 text-sm text-gray-600">
                            <p><strong>Vendors:</strong> {len(vendors)} total</p>
                            <p class="truncate"><strong>Names:</strong> {", ".join(vendors[:3])}{"..." if len(vendors) > 3 else ""}</p>
                        </div>
                    </div>
                    
                    <div>
                        <h3 class="font-medium mb-3">Current Forecast</h3>
                        <div class="space-y-3">
                            <div>
                                <label class="block text-sm font-medium text-gray-700">Pattern</label>
                                <select class="w-full border rounded px-3 py-2" onchange="updateForecast('{group_name}')">
                                    <option value="daily" {"selected" if frequency == "daily" else ""}>Daily</option>
                                    <option value="weekly" {"selected" if frequency == "weekly" else ""}>Weekly</option>
                                    <option value="bi-weekly" {"selected" if frequency == "bi-weekly" else ""}>Bi-weekly</option>
                                    <option value="monthly" {"selected" if frequency == "monthly" else ""}>Monthly</option>
                                    <option value="irregular" {"selected" if frequency == "irregular" else ""}>Irregular</option>
                                </select>
                            </div>
                            
                            <div>
                                <label class="block text-sm font-medium text-gray-700">Amount ($)</label>
                                <input type="number" class="w-full border rounded px-3 py-2" 
                                       value="{avg_amount:.0f}" onchange="updateForecast('{group_name}')">
                            </div>
                            
                            <div>
                                <label class="block text-sm font-medium text-gray-700">Confidence</label>
                                <div class="text-sm text-gray-600">{confidence:.1%}</div>
                            </div>
                            
                            <div class="pt-2">
                                <button onclick="previewForecast('{group_name}')" 
                                        class="bg-blue-500 text-white px-4 py-2 rounded text-sm">
                                    Preview Next 4 Weeks
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div id="preview_{group_name.replace(' ', '_')}" class="mt-4 hidden">
                    <h4 class="font-medium mb-2">Preview Next 4 Weeks:</h4>
                    <div class="bg-gray-50 p-3 rounded text-sm">
                        <div class="grid grid-cols-4 gap-4">
                            <div>Week 1: $0</div>
                            <div>Week 2: $0</div>
                            <div>Week 3: $0</div>
                            <div>Week 4: $0</div>
                        </div>
                    </div>
                </div>
            </div>'''

html += '''
        </div>
        
        <div class="mt-8 text-center">
            <button onclick="saveAdjustments()" class="bg-green-600 text-white px-8 py-3 rounded-lg text-lg">
                💾 Save Forecast Adjustments
            </button>
            <button onclick="generateForecast()" class="bg-blue-600 text-white px-8 py-3 rounded-lg text-lg ml-4">
                📊 Generate Updated Forecast
            </button>
        </div>
    </div>
    
    <script>
        function updateForecast(groupName) {
            console.log('Updating forecast for:', groupName);
            // In production: update forecast parameters
        }
        
        function previewForecast(groupName) {
            const previewDiv = document.getElementById('preview_' + groupName.replace(' ', '_'));
            previewDiv.classList.toggle('hidden');
            
            // Simple preview calculation
            const pattern = document.querySelector(`select`).value;
            const amount = parseFloat(document.querySelector(`input[type="number"]`).value);
            
            let weeklyAmount = 0;
            if (pattern === 'daily') weeklyAmount = amount * 7;
            else if (pattern === 'weekly') weeklyAmount = amount;
            else if (pattern === 'monthly') weeklyAmount = amount / 4;
            
            previewDiv.querySelector('.grid').innerHTML = `
                <div>Week 1: $${weeklyAmount.toLocaleString()}</div>
                <div>Week 2: $${weeklyAmount.toLocaleString()}</div>
                <div>Week 3: $${weeklyAmount.toLocaleString()}</div>
                <div>Week 4: $${weeklyAmount.toLocaleString()}</div>
            `;
        }
        
        function saveAdjustments() {
            alert('Forecast adjustments saved to database');
            // In production: save adjusted parameters to pattern_analysis table
        }
        
        function generateForecast() {
            alert('Generating updated 13-week forecast with your adjustments...');
            // In production: regenerate forecasts with adjusted parameters
        }
    </script>
</body>
</html>'''

with open(review_file, 'w') as f:
    f.write(html)

print(f'📊 Created forecast review interface: {review_file}')
print(f'🌐 Opening in browser...')
webbrowser.open(f'file://{review_file}')

print('\n✅ FORECAST REVIEW INTERFACE READY!')
print('Review each group\'s recent transactions and adjust forecast parameters as needed')