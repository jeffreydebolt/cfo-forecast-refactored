#!/usr/bin/env python3
"""
Manual Forecast Setup Interface - Phase 5
Interactive interface for setting up forecasts for irregular/variable vendors
"""

import sys
sys.path.append('.')

from pattern_detection_engine import PatternDetectionEngine
from supabase_client import supabase
from datetime import datetime, date, timedelta
from typing import Dict, List

def create_manual_forecast_interface(client_id: str = 'spyguy'):
    """Create interactive interface for manual forecast setup"""
    
    # Get pattern analysis
    engine = PatternDetectionEngine()
    vendor_patterns = engine.analyze_vendor_patterns(client_id)
    
    # Filter for manual review vendors
    manual_vendors = [
        pattern for pattern in vendor_patterns.values() 
        if pattern.forecast_recommendation == 'manual'
    ]
    
    # Sort by transaction count (most transactions first)
    manual_vendors.sort(key=lambda x: x.transaction_count, reverse=True)
    
    # Generate HTML interface
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>⚙️ Manual Forecast Setup</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .vendor-card {{ transition: all 0.3s ease; }}
        .vendor-card:hover {{ transform: translateY(-2px); }}
        .setup-complete {{ background: #F0FDF4; border-color: #10B981; }}
        .needs-setup {{ background: #FEF3E2; border-color: #F59E0B; }}
        .forecast-method {{ display: none; }}
        .forecast-method.active {{ display: block; }}
    </style>
</head>
<body class="bg-gray-50 min-h-screen">
    
    <!-- Header -->
    <header class="bg-white shadow-sm border-b sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 py-4">
            <div class="flex justify-between items-center">
                <div>
                    <h1 class="text-2xl font-bold text-gray-900">⚙️ Manual Forecast Setup</h1>
                    <p class="text-sm text-gray-600">Configure forecasts for irregular vendors • {len(manual_vendors)} vendors need setup</p>
                </div>
                <div class="flex items-center space-x-4">
                    <div class="text-sm text-gray-500">
                        <span id="setupCount">0</span>/{len(manual_vendors)} vendors configured
                    </div>
                    <button onclick="saveAllForecasts()" 
                            class="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 font-medium">
                        💾 Save All Forecasts
                    </button>
                </div>
            </div>
        </div>
    </header>

    <div class="max-w-7xl mx-auto px-4 py-6">
        
        <!-- Overview -->
        <div class="bg-gradient-to-r from-orange-500 to-red-600 text-white rounded-lg p-6 mb-8">
            <h2 class="text-2xl font-bold mb-2">🔧 Manual Setup Required</h2>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
                <div>
                    <div class="text-3xl font-bold">{len(manual_vendors)}</div>
                    <div class="text-orange-100">Irregular Vendors</div>
                </div>
                <div>
                    <div class="text-3xl font-bold">{sum(v.transaction_count for v in manual_vendors)}</div>
                    <div class="text-orange-100">Total Transactions</div>
                </div>
                <div>
                    <div class="text-3xl font-bold">~15 min</div>
                    <div class="text-orange-100">Estimated Setup Time</div>
                </div>
            </div>
        </div>

        <!-- Vendor Setup Cards -->
        <div class="space-y-6">'''
    
    # Generate cards for each manual vendor
    for i, vendor in enumerate(manual_vendors):
        # Get recent transaction amounts for context
        recent_amounts = []
        if hasattr(vendor, 'amount_pattern') and hasattr(vendor.amount_pattern, 'amounts'):
            recent_amounts = vendor.amount_pattern.amounts[-5:]  # Last 5 amounts
        else:
            recent_amounts = [vendor.amount_pattern.average_amount]  # Fallback
        
        html_content += f'''
            <div class="vendor-card needs-setup bg-white rounded-lg shadow-md p-6 border-l-4" id="vendor_{i}">
                <div class="flex justify-between items-start mb-4">
                    <div class="flex-1">
                        <div class="flex items-center mb-2">
                            <h3 class="text-lg font-semibold text-gray-900">{vendor.vendor_name}</h3>
                            <span class="ml-3 px-2 py-1 bg-orange-100 text-orange-800 text-xs rounded-full font-medium">
                                {vendor.transaction_count} transactions
                            </span>
                        </div>
                        <p class="text-sm text-gray-600 mb-3">{vendor.reasoning}</p>
                        <div class="text-sm text-gray-500">
                            Pattern: {vendor.timing_pattern.pattern_type} • 
                            Average: ${vendor.amount_pattern.average_amount:,.0f} • 
                            Variance: {vendor.amount_pattern.variance_coefficient:.1%}
                        </div>
                    </div>
                    <div class="flex space-x-2">
                        <button onclick="showForecastMethod('vendor_{i}', 'recurring')" 
                                class="bg-blue-600 text-white px-3 py-2 rounded text-sm hover:bg-blue-700">
                            🔄 Set Recurring
                        </button>
                        <button onclick="showForecastMethod('vendor_{i}', 'manual')" 
                                class="bg-purple-600 text-white px-3 py-2 rounded text-sm hover:bg-purple-700">
                            ✋ Manual Entry
                        </button>
                        <button onclick="skipVendor('vendor_{i}')" 
                                class="bg-gray-600 text-white px-3 py-2 rounded text-sm hover:bg-gray-700">
                            ⏭️ Skip
                        </button>
                    </div>
                </div>
                
                <!-- Recurring Pattern Setup -->
                <div id="recurring_vendor_{i}" class="forecast-method">
                    <div class="bg-blue-50 rounded-lg p-4">
                        <h4 class="font-medium text-gray-700 mb-3">🔄 Recurring Pattern Setup</h4>
                        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-1">Frequency</label>
                                <select class="w-full border rounded px-3 py-2" id="frequency_vendor_{i}">
                                    <option value="weekly">Weekly</option>
                                    <option value="bi_weekly">Bi-weekly</option>
                                    <option value="monthly" selected>Monthly</option>
                                    <option value="quarterly">Quarterly</option>
                                    <option value="custom">Custom days</option>
                                </select>
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-1">Amount</label>
                                <input type="number" class="w-full border rounded px-3 py-2" 
                                       placeholder="${vendor.amount_pattern.average_amount:.0f}"
                                       value="{vendor.amount_pattern.average_amount:.0f}"
                                       id="amount_vendor_{i}">
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
                                <input type="date" class="w-full border rounded px-3 py-2" 
                                       value="{date.today().isoformat()}"
                                       id="startdate_vendor_{i}">
                            </div>
                        </div>
                        <div class="mt-3 flex space-x-2">
                            <button onclick="setupRecurring('vendor_{i}')" 
                                    class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
                                ✅ Setup Recurring
                            </button>
                            <button onclick="hideForecastMethod('vendor_{i}')" 
                                    class="bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700">
                                Cancel
                            </button>
                        </div>
                    </div>
                </div>
                
                <!-- Manual Entry Setup -->
                <div id="manual_vendor_{i}" class="forecast-method">
                    <div class="bg-purple-50 rounded-lg p-4">
                        <h4 class="font-medium text-gray-700 mb-3">✋ Manual Entry Setup</h4>
                        <p class="text-sm text-gray-600 mb-3">
                            Add individual forecast entries for the next 3 months. Leave blank to skip a month.
                        </p>
                        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-1">August 2025</label>
                                <input type="number" class="w-full border rounded px-3 py-2" 
                                       placeholder="Amount" id="aug_vendor_{i}">
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-1">September 2025</label>
                                <input type="number" class="w-full border rounded px-3 py-2" 
                                       placeholder="Amount" id="sep_vendor_{i}">
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-1">October 2025</label>
                                <input type="number" class="w-full border rounded px-3 py-2" 
                                       placeholder="Amount" id="oct_vendor_{i}">
                            </div>
                        </div>
                        <div class="mt-3 flex space-x-2">
                            <button onclick="setupManual('vendor_{i}')" 
                                    class="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700">
                                ✅ Setup Manual
                            </button>
                            <button onclick="hideForecastMethod('vendor_{i}')" 
                                    class="bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700">
                                Cancel
                            </button>
                        </div>
                    </div>
                </div>
                
                <!-- Setup Status -->
                <div id="status_vendor_{i}" class="mt-4 p-3 bg-gray-50 rounded border hidden">
                    <div class="flex items-center">
                        <span class="text-green-600 mr-2">✅</span>
                        <span class="text-sm font-medium text-gray-700" id="statusText_vendor_{i}">Forecast configured</span>
                    </div>
                </div>
            </div>'''
    
    html_content += f'''
        </div>

        <!-- Summary -->
        <div class="mt-8 bg-white rounded-lg shadow-sm p-6">
            <h3 class="text-lg font-semibold mb-4">🎯 Setup Summary</h3>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div class="text-center p-4 bg-green-50 rounded-lg">
                    <div class="text-2xl font-bold text-green-600" id="recurringCount">0</div>
                    <div class="text-sm text-gray-600">Recurring Patterns</div>
                </div>
                <div class="text-center p-4 bg-purple-50 rounded-lg">
                    <div class="text-2xl font-bold text-purple-600" id="manualCount">0</div>
                    <div class="text-sm text-gray-600">Manual Entries</div>
                </div>
                <div class="text-center p-4 bg-gray-50 rounded-lg">
                    <div class="text-2xl font-bold text-gray-600" id="skippedCount">0</div>
                    <div class="text-sm text-gray-600">Skipped</div>
                </div>
            </div>
            
            <div class="mt-6 border-t pt-4">
                <h4 class="font-medium text-gray-700 mb-2">Next Steps:</h4>
                <ol class="list-decimal list-inside text-sm text-gray-600 space-y-1">
                    <li>Configure forecast method for each vendor above</li>
                    <li>Review and adjust amounts based on business knowledge</li>
                    <li>Save all forecasts to generate cash flow predictions</li>
                    <li>Monitor and adjust forecasts monthly</li>
                </ol>
            </div>
        </div>
    </div>

    <script>
        let vendorConfigs = {{}};
        let setupCount = 0;
        
        function showForecastMethod(vendorId, method) {{
            // Hide all method divs for this vendor
            const recurring = document.getElementById(`recurring_${{vendorId}}`);
            const manual = document.getElementById(`manual_${{vendorId}}`);
            
            recurring.classList.remove('active');
            manual.classList.remove('active');
            
            // Show selected method
            if (method === 'recurring') {{
                recurring.classList.add('active');
            }} else if (method === 'manual') {{
                manual.classList.add('active');
            }}
        }}
        
        function hideForecastMethod(vendorId) {{
            const recurring = document.getElementById(`recurring_${{vendorId}}`);
            const manual = document.getElementById(`manual_${{vendorId}}`);
            
            recurring.classList.remove('active');
            manual.classList.remove('active');
        }}
        
        function setupRecurring(vendorId) {{
            const frequency = document.getElementById(`frequency_${{vendorId}}`).value;
            const amount = document.getElementById(`amount_${{vendorId}}`).value;
            const startDate = document.getElementById(`startdate_${{vendorId}}`).value;
            
            if (!amount || !startDate) {{
                alert('Please fill in amount and start date');
                return;
            }}
            
            vendorConfigs[vendorId] = {{
                method: 'recurring',
                frequency: frequency,
                amount: parseFloat(amount),
                startDate: startDate
            }};
            
            completeVendorSetup(vendorId, `Recurring ${{frequency}} at $${{amount}}`);
        }}
        
        function setupManual(vendorId) {{
            const aug = document.getElementById(`aug_${{vendorId}}`).value;
            const sep = document.getElementById(`sep_${{vendorId}}`).value;
            const oct = document.getElementById(`oct_${{vendorId}}`).value;
            
            const entries = [];
            if (aug) entries.push({{month: 'Aug', amount: parseFloat(aug)}});
            if (sep) entries.push({{month: 'Sep', amount: parseFloat(sep)}});
            if (oct) entries.push({{month: 'Oct', amount: parseFloat(oct)}});
            
            if (entries.length === 0) {{
                alert('Please enter at least one monthly amount');
                return;
            }}
            
            vendorConfigs[vendorId] = {{
                method: 'manual',
                entries: entries
            }};
            
            completeVendorSetup(vendorId, `${{entries.length}} manual entries`);
        }}
        
        function skipVendor(vendorId) {{
            vendorConfigs[vendorId] = {{
                method: 'skip'
            }};
            
            completeVendorSetup(vendorId, 'Skipped forecasting');
        }}
        
        function completeVendorSetup(vendorId, statusText) {{
            // Update visual state
            const card = document.getElementById(vendorId);
            const status = document.getElementById(`status_${{vendorId}}`);
            const statusTextEl = document.getElementById(`statusText_${{vendorId}}`);
            
            card.classList.remove('needs-setup');
            card.classList.add('setup-complete');
            
            status.classList.remove('hidden');
            statusTextEl.textContent = statusText;
            
            // Hide method divs
            hideForecastMethod(vendorId);
            
            // Update counters
            updateCounters();
        }}
        
        function updateCounters() {{
            setupCount = Object.keys(vendorConfigs).length;
            document.getElementById('setupCount').textContent = setupCount;
            
            let recurring = 0, manual = 0, skipped = 0;
            
            Object.values(vendorConfigs).forEach(config => {{
                if (config.method === 'recurring') recurring++;
                else if (config.method === 'manual') manual++;
                else if (config.method === 'skip') skipped++;
            }});
            
            document.getElementById('recurringCount').textContent = recurring;
            document.getElementById('manualCount').textContent = manual;
            document.getElementById('skippedCount').textContent = skipped;
        }}
        
        function saveAllForecasts() {{
            if (setupCount < {len(manual_vendors)}) {{
                const remaining = {len(manual_vendors)} - setupCount;
                if (!confirm(`${{remaining}} vendors still need setup. Save anyway?`)) {{
                    return;
                }}
            }}
            
            console.log('Saving forecast configurations:', vendorConfigs);
            alert(`Saved forecasts for ${{setupCount}} vendors! Configurations logged to console.`);
            
            // In production, this would save to database
        }}
        
        // Initialize
        console.log('Manual Forecast Setup Interface loaded');
        console.log('{len(manual_vendors)} vendors need manual configuration');
    </script>
</body>
</html>'''
    
    # Save interface
    output_file = '/Users/jeffreydebolt/Documents/cfo_forecast_refactored/manual_forecast_interface.html'
    with open(output_file, 'w') as f:
        f.write(html_content)
    
    print(f"✅ Manual Forecast Interface created: {output_file}")
    return output_file

def main():
    """Create the manual forecast setup interface"""
    print("⚙️ CREATING MANUAL FORECAST SETUP INTERFACE")
    print("=" * 80)
    
    interface_file = create_manual_forecast_interface('spyguy')
    
    print(f"\n🎉 SUCCESS!")
    print(f"📊 Manual forecast setup interface ready")
    print(f"🎯 Configure forecasts for irregular vendors")
    print(f"⏭️ Save configurations to generate predictions")

if __name__ == "__main__":
    main()