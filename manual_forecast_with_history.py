#!/usr/bin/env python3
"""
Manual Forecast Setup WITH Transaction History
Shows past payment patterns to inform forecast decisions
"""

import sys
sys.path.append('.')

from pattern_detection_engine import PatternDetectionEngine
from supabase_client import supabase
from datetime import datetime, date, timedelta
from typing import Dict, List
import json

def create_manual_forecast_interface_with_history(client_id: str = 'spyguy'):
    """Create interface showing transaction history for each vendor"""
    
    # Get pattern analysis
    engine = PatternDetectionEngine()
    vendor_patterns = engine.analyze_vendor_patterns(client_id)
    
    # Filter for manual review vendors
    manual_vendors = [
        pattern for pattern in vendor_patterns.values() 
        if pattern.forecast_recommendation == 'manual'
    ]
    
    # Sort by transaction count
    manual_vendors.sort(key=lambda x: x.transaction_count, reverse=True)
    
    # Get transaction history for each vendor
    vendor_histories = {}
    for vendor in manual_vendors:
        result = supabase.table('transactions').select('transaction_date, amount')\
            .eq('client_id', client_id)\
            .eq('vendor_name', vendor.vendor_name)\
            .order('transaction_date', desc=True)\
            .limit(50)\
            .execute()
        
        vendor_histories[vendor.vendor_name] = result.data
    
    # Generate HTML
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>⚙️ Manual Forecast Setup - With History</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        .vendor-card {{ transition: all 0.3s ease; }}
        .vendor-card:hover {{ transform: translateY(-2px); }}
        .setup-complete {{ background: #F0FDF4; border-color: #10B981; }}
        .needs-setup {{ background: #FEF3E2; border-color: #F59E0B; }}
        .history-chart {{ height: 200px; }}
    </style>
</head>
<body class="bg-gray-50 min-h-screen">
    
    <!-- Header -->
    <header class="bg-white shadow-sm border-b sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 py-4">
            <div class="flex justify-between items-center">
                <div>
                    <h1 class="text-2xl font-bold text-gray-900">⚙️ Manual Forecast Setup</h1>
                    <p class="text-sm text-gray-600">Review transaction history • Configure forecasts • {len(manual_vendors)} vendors</p>
                </div>
                <div class="flex items-center space-x-4">
                    <div class="text-sm text-gray-500">
                        <span id="setupCount">0</span>/{len(manual_vendors)} configured
                    </div>
                    <button onclick="saveAllForecasts()" 
                            class="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 font-medium">
                        💾 Save All Forecasts
                    </button>
                </div>
            </div>
        </div>
    </header>

    <div class="max-w-7xl mx-auto px-4 py-6">'''
    
    # Generate vendor cards with history
    for i, vendor in enumerate(manual_vendors):
        history = vendor_histories.get(vendor.vendor_name, [])
        
        # Calculate time-based averages (not just transaction averages)
        recent_amounts = [abs(float(h['amount'])) for h in history[:12]]  # Use more history
        recent_dates = [datetime.fromisoformat(h['transaction_date']).date() for h in history[:12]]
        
        if recent_amounts and len(recent_dates) >= 2:
            # Calculate actual time-based averages
            total_amount = sum(recent_amounts)
            start_date = min(recent_dates)
            end_date = max(recent_dates)
            days_span = (end_date - start_date).days
            
            if days_span > 0:
                daily_avg = total_amount / days_span
                weekly_avg = daily_avg * 7
                monthly_avg = daily_avg * 30
            else:
                # Single day or same-day transactions
                weekly_avg = monthly_avg = total_amount
            
            recent_min = min(recent_amounts)
            recent_max = max(recent_amounts)
            
            # Use monthly average as primary display
            recent_avg = monthly_avg
        else:
            recent_avg = recent_min = recent_max = 0
            weekly_avg = monthly_avg = 0
        
        # Analyze timing patterns from history
        timing_insight = ""
        if len(recent_dates) >= 3:
            # Analyze day-of-month patterns
            days_of_month = [d.day for d in recent_dates]
            from collections import Counter
            common_days = Counter(days_of_month).most_common(2)
            
            if common_days[0][1] >= 2:  # At least 2 occurrences
                if len(common_days) > 1 and common_days[1][1] >= 2:
                    timing_insight = f"Usually {common_days[0][0]} or {common_days[1][0]} of month"
                else:
                    timing_insight = f"Usually {common_days[0][0]} of month"
            
            # Analyze day-of-week patterns
            weekdays = [d.strftime('%A') for d in recent_dates]
            common_weekdays = Counter(weekdays).most_common(2)
            
            if common_weekdays[0][1] >= 2:
                if not timing_insight:  # Only show if no monthly pattern found
                    timing_insight = f"Usually {common_weekdays[0][0]}s"
        
        # Format transaction history for display
        history_rows = ""
        for i, txn in enumerate(history[:6]):  # Show first 6 transactions
            date_str = datetime.fromisoformat(txn['transaction_date']).strftime('%b %d, %Y')
            amount_str = f"${abs(float(txn['amount'])):,.0f}"
            day_of_week = datetime.fromisoformat(txn['transaction_date']).strftime('%a')
            history_rows += f'''
                <tr>
                    <td class="px-3 py-1 text-sm">{date_str} <span class="text-gray-400">({day_of_week})</span></td>
                    <td class="px-3 py-1 text-sm text-right font-medium">{amount_str}</td>
                </tr>'''
        
        # Additional rows for "See More" (hidden initially)
        more_history_rows = ""
        for i, txn in enumerate(history[6:20]):  # Next 14 transactions
            date_str = datetime.fromisoformat(txn['transaction_date']).strftime('%b %d, %Y')
            amount_str = f"${abs(float(txn['amount'])):,.0f}"
            day_of_week = datetime.fromisoformat(txn['transaction_date']).strftime('%a')
            more_history_rows += f'''
                <tr>
                    <td class="px-3 py-1 text-sm">{date_str} <span class="text-gray-400">({day_of_week})</span></td>
                    <td class="px-3 py-1 text-sm text-right font-medium">{amount_str}</td>
                </tr>'''
        
        html_content += f'''
        <div class="vendor-card needs-setup bg-white rounded-lg shadow-md p-6 border-l-4 mb-6" id="vendor_{i}">
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <!-- Left: Vendor Info & History -->
                <div>
                    <div class="flex items-center mb-3">
                        <h3 class="text-lg font-semibold text-gray-900">{vendor.vendor_name}</h3>
                        <span class="ml-3 px-2 py-1 bg-orange-100 text-orange-800 text-xs rounded-full font-medium">
                            {vendor.transaction_count} total transactions
                        </span>
                    </div>
                    
                    <div class="mb-4">
                        <p class="text-sm text-gray-600 mb-2">{vendor.reasoning}</p>
                        <div class="flex flex-wrap gap-4 text-sm">
                            <span>Pattern: <strong>{vendor.timing_pattern.pattern_type}</strong></span>
                            <span>Avg Gap: <strong>{vendor.timing_pattern.frequency_days} days</strong></span>
                            <span>Variance: <strong>{vendor.amount_pattern.variance_coefficient:.1%}</strong></span>
                            {f'<span class="text-blue-600">💡 <strong>{timing_insight}</strong></span>' if timing_insight else ''}
                        </div>
                    </div>
                    
                    <!-- Transaction History Table -->
                    <div class="bg-gray-50 rounded-lg p-3">
                        <h4 class="font-medium text-gray-700 mb-2">Recent Transactions</h4>
                        <table class="w-full">
                            <thead>
                                <tr class="text-xs text-gray-500">
                                    <th class="text-left px-3 py-1">Date</th>
                                    <th class="text-right px-3 py-1">Amount</th>
                                </tr>
                            </thead>
                            <tbody class="divide-y divide-gray-200">
                                {history_rows if history_rows else '<tr><td colspan="2" class="text-center text-gray-500 py-2">No recent history</td></tr>'}
                                <tbody id="moreHistory_vendor_{i}" class="divide-y divide-gray-200 hidden">
                                    {more_history_rows}
                                </tbody>
                            </tbody>
                        </table>
                        {f'''<div class="flex justify-between items-center mt-2 pt-2 border-t">
                            <div class="text-xs text-gray-600">
                                Monthly Avg: <strong>${monthly_avg:,.0f}</strong> | 
                                Range: ${recent_min:,.0f} - ${recent_max:,.0f}
                            </div>
                            <button onclick="toggleMoreHistory('vendor_{i}')" 
                                    class="text-xs text-blue-600 hover:text-blue-800" id="moreBtn_vendor_{i}">
                                See More ({len(history) - 6} more)
                            </button>
                        </div>''' if len(history) > 6 else f'''<div class="mt-2 pt-2 border-t text-xs text-gray-600">
                            Monthly Avg: <strong>${monthly_avg:,.0f}</strong> | 
                            Range: ${recent_min:,.0f} - ${recent_max:,.0f}
                        </div>''' if recent_amounts else ''}
                    </div>
                </div>
                
                <!-- Right: Forecast Configuration -->
                <div>
                    <h4 class="font-medium text-gray-700 mb-3">Configure Forecast</h4>
                    
                    <!-- Quick Actions -->
                    <div class="grid grid-cols-2 gap-2 mb-4">
                        <button onclick="setRecurring('vendor_{i}', 'monthly', {int(recent_avg)})" 
                                class="bg-blue-100 text-blue-700 px-3 py-2 rounded text-sm hover:bg-blue-200">
                            📅 Monthly @ ${int(recent_avg):,}
                        </button>
                        <button onclick="setRecurring('vendor_{i}', 'weekly', {int(recent_avg)})" 
                                class="bg-blue-100 text-blue-700 px-3 py-2 rounded text-sm hover:bg-blue-200">
                            📅 Weekly @ ${int(recent_avg):,}
                        </button>
                        <button onclick="showManualEntry('vendor_{i}')" 
                                class="bg-purple-100 text-purple-700 px-3 py-2 rounded text-sm hover:bg-purple-200">
                            ✋ Manual Entry
                        </button>
                        <button onclick="skipVendor('vendor_{i}')" 
                                class="bg-gray-100 text-gray-700 px-3 py-2 rounded text-sm hover:bg-gray-200">
                            ⏭️ Skip This
                        </button>
                    </div>
                    
                    <!-- Custom Recurring Setup -->
                    <div class="bg-gray-50 rounded-lg p-3">
                        <h5 class="text-sm font-medium text-gray-700 mb-2">Custom Recurring Pattern</h5>
                        <div class="grid grid-cols-3 gap-2">
                            <div>
                                <label class="block text-xs text-gray-600 mb-1">Frequency</label>
                                <select class="w-full border rounded px-2 py-1 text-sm" id="freq_vendor_{i}">
                                    <option value="daily">Daily</option>
                                    <option value="weekly">Weekly</option>
                                    <option value="bi_weekly">Bi-weekly</option>
                                    <option value="monthly" selected>Monthly</option>
                                    <option value="quarterly">Quarterly</option>
                                </select>
                            </div>
                            <div>
                                <label class="block text-xs text-gray-600 mb-1">Amount</label>
                                <input type="number" class="w-full border rounded px-2 py-1 text-sm" 
                                       value="{int(recent_avg)}" id="amount_vendor_{i}">
                            </div>
                            <div>
                                <label class="block text-xs text-gray-600 mb-1">Start</label>
                                <input type="date" class="w-full border rounded px-2 py-1 text-sm" 
                                       value="{date.today().isoformat()}" id="start_vendor_{i}">
                            </div>
                        </div>
                        <button onclick="setupCustomRecurring('vendor_{i}')" 
                                class="mt-2 bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700">
                            Set Custom Pattern
                        </button>
                    </div>
                    
                    <!-- Manual Entry (Hidden by default) -->
                    <div id="manual_vendor_{i}" class="bg-purple-50 rounded-lg p-3 mt-3 hidden">
                        <h5 class="text-sm font-medium text-gray-700 mb-2">Manual Monthly Entries</h5>
                        <div class="grid grid-cols-3 gap-2">
                            <input type="number" placeholder="Aug" id="aug_vendor_{i}" 
                                   class="border rounded px-2 py-1 text-sm">
                            <input type="number" placeholder="Sep" id="sep_vendor_{i}" 
                                   class="border rounded px-2 py-1 text-sm">
                            <input type="number" placeholder="Oct" id="oct_vendor_{i}" 
                                   class="border rounded px-2 py-1 text-sm">
                        </div>
                        <button onclick="saveManualEntries('vendor_{i}')" 
                                class="mt-2 bg-purple-600 text-white px-3 py-1 rounded text-sm hover:bg-purple-700">
                            Save Manual Entries
                        </button>
                    </div>
                    
                    <!-- Status -->
                    <div id="status_vendor_{i}" class="mt-3 p-2 bg-green-50 rounded text-sm hidden">
                        <span class="text-green-700 font-medium" id="statusText_vendor_{i}">Configured</span>
                    </div>
                </div>
            </div>
        </div>'''
    
    html_content += '''
    </div>

    <script>
        let vendorConfigs = {};
        
        function setRecurring(vendorId, frequency, amount) {
            vendorConfigs[vendorId] = {
                method: 'recurring',
                frequency: frequency,
                amount: amount,
                startDate: new Date().toISOString().split('T')[0]
            };
            updateVendorStatus(vendorId, `${frequency} @ $${amount.toLocaleString()}`);
        }
        
        function setupCustomRecurring(vendorId) {
            const freq = document.getElementById(`freq_${vendorId}`).value;
            const amount = parseFloat(document.getElementById(`amount_${vendorId}`).value);
            const start = document.getElementById(`start_${vendorId}`).value;
            
            if (!amount) {
                alert('Please enter an amount');
                return;
            }
            
            vendorConfigs[vendorId] = {
                method: 'recurring',
                frequency: freq,
                amount: amount,
                startDate: start
            };
            updateVendorStatus(vendorId, `${freq} @ $${amount.toLocaleString()}`);
        }
        
        function showManualEntry(vendorId) {
            document.getElementById(`manual_${vendorId}`).classList.remove('hidden');
        }
        
        function saveManualEntries(vendorId) {
            const aug = document.getElementById(`aug_${vendorId}`).value;
            const sep = document.getElementById(`sep_${vendorId}`).value;
            const oct = document.getElementById(`oct_${vendorId}`).value;
            
            const entries = [];
            if (aug) entries.push({month: 'Aug', amount: parseFloat(aug)});
            if (sep) entries.push({month: 'Sep', amount: parseFloat(sep)});
            if (oct) entries.push({month: 'Oct', amount: parseFloat(oct)});
            
            if (entries.length === 0) {
                alert('Please enter at least one amount');
                return;
            }
            
            vendorConfigs[vendorId] = {
                method: 'manual',
                entries: entries
            };
            updateVendorStatus(vendorId, `${entries.length} manual entries`);
            document.getElementById(`manual_${vendorId}`).classList.add('hidden');
        }
        
        function skipVendor(vendorId) {
            vendorConfigs[vendorId] = {
                method: 'skip'
            };
            updateVendorStatus(vendorId, 'Skipped');
        }
        
        function updateVendorStatus(vendorId, statusText) {
            const card = document.getElementById(vendorId);
            const status = document.getElementById(`status_${vendorId}`);
            const statusTextEl = document.getElementById(`statusText_${vendorId}`);
            
            card.classList.remove('needs-setup');
            card.classList.add('setup-complete');
            status.classList.remove('hidden');
            statusTextEl.textContent = statusText;
            
            // Update counter
            document.getElementById('setupCount').textContent = Object.keys(vendorConfigs).length;
        }
        
        function toggleMoreHistory(vendorId) {
            const moreHistory = document.getElementById(`moreHistory_${vendorId}`);
            const btn = document.getElementById(`moreBtn_${vendorId}`);
            
            if (moreHistory.classList.contains('hidden')) {
                moreHistory.classList.remove('hidden');
                btn.textContent = 'Show Less';
            } else {
                moreHistory.classList.add('hidden');
                btn.textContent = btn.textContent.replace('Show Less', 'See More');
            }
        }
        
        function saveAllForecasts() {
            console.log('Saving forecasts:', vendorConfigs);
            alert(`Saving ${Object.keys(vendorConfigs).length} forecast configurations...`);
        }
    </script>
</body>
</html>'''
    
    # Save interface
    output_file = '/Users/jeffreydebolt/Documents/cfo_forecast_refactored/manual_forecast_with_history.html'
    with open(output_file, 'w') as f:
        f.write(html_content)
    
    print(f"✅ Manual Forecast Interface WITH HISTORY created: {output_file}")
    return output_file

def main():
    """Create the improved interface"""
    print("⚙️ CREATING MANUAL FORECAST INTERFACE WITH TRANSACTION HISTORY")
    print("=" * 80)
    
    interface_file = create_manual_forecast_interface_with_history('spyguy')
    
    print(f"\n🎉 SUCCESS!")
    print(f"📊 Shows recent transaction history for each vendor")
    print(f"💡 Quick action buttons based on historical amounts")
    print(f"🎯 No business logic assumptions")

if __name__ == "__main__":
    main()