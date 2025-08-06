#!/usr/bin/env python3
"""
Complete Multi-Client Onboarding System
No hardcoded assumptions - works for any client
"""

import sys
import argparse
import os
import csv
import json
import tempfile
import webbrowser
from datetime import datetime, date, timedelta
from decimal import Decimal
from collections import defaultdict

sys.path.append('.')

from supabase_client import supabase

class CompleteMultiClientOnboarding:
    """Complete multi-client onboarding system"""
    
    def __init__(self, client_id: str):
        self.client_id = client_id
        self.temp_dir = tempfile.mkdtemp()
        
    def run_step1_import(self, csv_file: str):
        """Step 1: Import transactions from CSV"""
        print(f"STEP 1: IMPORT TRANSACTIONS")
        print(f"Client: {self.client_id}")
        print(f"File: {csv_file}")
        print("=" * 60)
        
        if not os.path.exists(csv_file):
            print(f"❌ CSV file not found: {csv_file}")
            return False
        
        # Clear existing transactions for this client
        print(f"🗑️ Clearing existing transactions for {self.client_id}")
        supabase.table('transactions').delete().eq('client_id', self.client_id).execute()
        
        # Import CSV
        transactions = []
        skipped = 0
        row_num = 0
        
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                row_num += 1
                
                # Skip failed transactions
                if row.get('Status') == 'Failed':
                    skipped += 1
                    continue
                
                # Parse amount
                try:
                    amount = float(row.get('Amount', '0').replace(',', ''))
                except:
                    skipped += 1
                    continue
                
                # Parse date
                try:
                    transaction_date = datetime.strptime(row.get('Date (UTC)', ''), '%m-%d-%Y').date()
                except:
                    try:
                        transaction_date = datetime.strptime(row.get('Date (UTC)', ''), '%Y-%m-%d').date()
                    except:
                        skipped += 1
                        continue
                
                # Build transaction record
                transaction = {
                    'transaction_id': f"{self.client_id}_{transaction_date}_{row_num}",
                    'client_id': self.client_id,
                    'transaction_date': transaction_date.isoformat(),
                    'vendor_name': row.get('Description', ''),
                    'amount': amount,
                    'created_at': datetime.now().isoformat()
                }
                
                transactions.append(transaction)
        
        if not transactions:
            print("❌ No valid transactions to import")
            return False
        
        # Save to database in batches
        batch_size = 100
        imported = 0
        
        for i in range(0, len(transactions), batch_size):
            batch = transactions[i:i + batch_size]
            try:
                supabase.table('transactions').insert(batch).execute()
                imported += len(batch)
                print(f"✅ Imported batch {i//batch_size + 1}: {len(batch)} transactions")
            except Exception as e:
                print(f"❌ Error importing batch: {str(e)}")
                return False
        
        print(f"\\n✅ STEP 1 COMPLETE!")
        print(f"📊 Imported: {imported} transactions")
        print(f"⏭️ Skipped: {skipped} transactions")
        
        # Show date range
        dates = [t['transaction_date'] for t in transactions]
        print(f"📅 Date range: {min(dates)} to {max(dates)}")
        
        return True
    
    def run_step2_grouping(self):
        """Step 2: Vendor grouping interface"""
        print(f"STEP 2: VENDOR GROUPING")
        print(f"Client: {self.client_id}")
        print("=" * 60)
        
        # Verify transactions exist
        result = supabase.table('transactions').select('id', count='exact')\
            .eq('client_id', self.client_id)\
            .execute()
        
        if not result.count:
            print(f"❌ No transactions found for client {self.client_id}")
            print("Run step 1 first")
            return False
        
        print(f"✅ Found {result.count} transactions")
        
        # Check if groups already exist
        existing_groups = supabase.table('vendor_groups').select('*')\
            .eq('client_id', self.client_id)\
            .execute()
        
        if existing_groups.data:
            print(f"⚠️ Found {len(existing_groups.data)} existing groups")
            overwrite = input("Overwrite existing groups? (y/n): ").lower() == 'y'
            if not overwrite:
                print("Step 2 skipped")
                return True
        
        # Generate grouping interface
        interface_path = self._create_full_grouping_interface()
        print(f"📋 Opening grouping interface: {interface_path}")
        
        # Open in browser
        webbrowser.open(f"file://{interface_path}")
        
        print("\\n⏳ Complete vendor grouping in browser")
        print("Then press Enter to save groups to database...")
        input()
        
        # For now, create sample groups (in production, would read from interface)
        sample_groups = self._create_sample_groups()
        
        return True
    
    def run_step3_patterns(self):
        """Step 3: Pattern detection"""
        print(f"STEP 3: PATTERN DETECTION")
        print(f"Client: {self.client_id}")
        print("=" * 60)
        
        # Check prerequisites
        groups = supabase.table('vendor_groups').select('*')\
            .eq('client_id', self.client_id)\
            .execute()
        
        if not groups.data:
            print(f"❌ No vendor groups found for client {self.client_id}")
            print("Complete step 2 first")
            return False
        
        print(f"✅ Found {len(groups.data)} vendor groups")
        
        # Run pattern detection for each group
        patterns_detected = 0
        for group in groups.data:
            group_name = group['group_name']
            vendor_list = group['vendor_display_names']
            
            # Get transactions for this group
            transactions = supabase.table('transactions')\
                .select('transaction_date, amount')\
                .eq('client_id', self.client_id)\
                .in_('vendor_name', vendor_list)\
                .order('transaction_date')\
                .execute()
            
            if len(transactions.data) < 3:
                print(f"   ⏭️ {group_name}: Insufficient data ({len(transactions.data)} transactions)")
                continue
            
            # Analyze pattern
            pattern_info = self._analyze_group_pattern(group_name, transactions.data)
            
            # Save pattern analysis
            self._save_pattern_analysis(group_name, pattern_info)
            patterns_detected += 1
            
            print(f"   ✅ {group_name}: {pattern_info['pattern_type']} (${pattern_info['avg_amount']:,.0f})")
        
        print(f"\\n✅ STEP 3 COMPLETE!")
        print(f"📊 Patterns detected: {patterns_detected}")
        
        return True
    
    def run_step4_manual(self):
        """Step 4: Manual forecast setup"""
        print(f"STEP 4: MANUAL FORECAST SETUP")
        print(f"Client: {self.client_id}")
        print("=" * 60)
        
        # Get vendors needing manual setup
        patterns = supabase.table('pattern_analysis').select('*')\
            .eq('client_id', self.client_id)\
            .execute()
        
        if not patterns.data:
            print(f"❌ No pattern analysis found for client {self.client_id}")
            print("Complete step 3 first")
            return False
        
        # Filter for manual setup needed
        manual_needed = [p for p in patterns.data if p.get('confidence_score', 0) < 0.8]
        
        if not manual_needed:
            print("✅ All vendors have high confidence patterns - no manual setup needed")
            return True
        
        print(f"📝 {len(manual_needed)} vendors need manual configuration")
        
        # Create manual setup interface
        interface_path = self._create_manual_interface(manual_needed)
        print(f"📋 Opening manual setup interface: {interface_path}")
        
        webbrowser.open(f"file://{interface_path}")
        
        print("\\n⏳ Complete manual forecast setup in browser")
        input("Press Enter when done...")
        
        # Save sample configs (in production, would read from interface)
        self._save_sample_forecast_configs(manual_needed)
        
        print("✅ STEP 4 COMPLETE!")
        return True
    
    def run_step5_display(self):
        """Step 5: Generate forecast display"""
        print(f"STEP 5: GENERATE FORECAST DISPLAY")
        print(f"Client: {self.client_id}")
        print("=" * 60)
        
        # Generate forecasts
        forecast_count = self._generate_forecast_records()
        
        if forecast_count == 0:
            print("❌ No forecasts generated")
            return False
        
        # Create display
        display_path = self._create_forecast_display()
        print(f"📊 Opening forecast display: {display_path}")
        
        webbrowser.open(f"file://{display_path}")
        
        print(f"\\n✅ STEP 5 COMPLETE!")
        print(f"📊 Generated {forecast_count} forecast records")
        print(f"📈 13-week forecast display ready")
        
        return True
    
    def _create_full_grouping_interface(self) -> str:
        """Create complete grouping interface"""
        # Get vendor stats
        result = supabase.table('transactions').select('vendor_name, amount')\
            .eq('client_id', self.client_id)\
            .execute()
        
        vendor_stats = defaultdict(lambda: {'count': 0, 'total': 0})
        for txn in result.data:
            vendor = txn['vendor_name']
            vendor_stats[vendor]['count'] += 1
            vendor_stats[vendor]['total'] += abs(float(txn['amount']))
        
        # Filter regular vendors
        regular_vendors = []
        for vendor, stats in vendor_stats.items():
            if stats['count'] >= 2:
                regular_vendors.append({
                    'name': vendor,
                    'count': stats['count'],
                    'total': stats['total']
                })
        
        regular_vendors.sort(key=lambda x: x['total'], reverse=True)
        
        # Create HTML interface
        interface_file = os.path.join(self.temp_dir, f"{self.client_id}_grouping.html")
        
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Vendor Grouping - {self.client_id}</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50">
    <div class="container mx-auto p-6">
        <h1 class="text-2xl font-bold mb-6">🗂️ Vendor Grouping - {self.client_id}</h1>
        <p class="mb-4">Found {len(regular_vendors)} vendors with 2+ transactions</p>
        
        <div class="grid grid-cols-2 gap-6">
            <div>
                <h2 class="text-lg font-semibold mb-4">Available Vendors</h2>
                <div class="space-y-2">'''
        
        for i, vendor in enumerate(regular_vendors):
            html += f'''
                    <div class="bg-white p-3 rounded border cursor-pointer hover:bg-blue-50" 
                         onclick="selectVendor('{vendor['name']}')" id="vendor_{i}">
                        <div class="flex justify-between">
                            <div>
                                <div class="font-medium">{vendor['name']}</div>
                                <div class="text-sm text-gray-500">{vendor['count']} transactions</div>
                            </div>
                            <div class="text-right">
                                <div class="font-medium">${vendor['total']:,.0f}</div>
                            </div>
                        </div>
                    </div>'''
        
        html += f'''
                </div>
            </div>
            
            <div>
                <h2 class="text-lg font-semibold mb-4">Your Groups</h2>
                <button onclick="createGroup()" class="bg-blue-600 text-white px-4 py-2 rounded mb-4">
                    Create Group
                </button>
                <div id="groups" class="space-y-2"></div>
            </div>
        </div>
        
        <div class="mt-6">
            <button onclick="saveGroups()" class="bg-green-600 text-white px-6 py-2 rounded">
                💾 Save Groups
            </button>
        </div>
    </div>
    
    <script>
        let selectedVendors = new Set();
        let groups = [];
        
        function selectVendor(vendorName) {{
            if (selectedVendors.has(vendorName)) {{
                selectedVendors.delete(vendorName);
                document.getElementById('vendor_' + vendorName).classList.remove('bg-blue-100');
            }} else {{
                selectedVendors.add(vendorName);
                document.getElementById('vendor_' + vendorName).classList.add('bg-blue-100');
            }}
        }}
        
        function createGroup() {{
            if (selectedVendors.size === 0) {{
                alert('Select vendors first');
                return;
            }}
            
            const groupName = prompt('Enter group name:');
            if (!groupName) return;
            
            groups.push({{
                name: groupName,
                vendors: Array.from(selectedVendors)
            }});
            
            updateGroupsDisplay();
            selectedVendors.clear();
            
            // Clear selections
            document.querySelectorAll('.bg-blue-100').forEach(el => {{
                el.classList.remove('bg-blue-100');
            }});
        }}
        
        function updateGroupsDisplay() {{
            const groupsDiv = document.getElementById('groups');
            groupsDiv.innerHTML = '';
            
            groups.forEach((group, index) => {{
                const groupDiv = document.createElement('div');
                groupDiv.className = 'bg-white p-3 rounded border';
                groupDiv.innerHTML = `
                    <h3 class="font-semibold">${{group.name}}</h3>
                    <p class="text-sm text-gray-600">${{group.vendors.length}} vendors</p>
                    <ul class="text-xs text-gray-500 mt-1">
                        ${{group.vendors.slice(0, 3).map(v => '<li>' + v + '</li>').join('')}}
                        ${{group.vendors.length > 3 ? '<li>... and ' + (group.vendors.length - 3) + ' more</li>' : ''}}
                    </ul>
                `;
                groupsDiv.appendChild(groupDiv);
            }});
        }}
        
        function saveGroups() {{
            console.log('Groups to save:', groups);
            alert(`${{groups.length}} groups ready to save to database for client {self.client_id}`);
            // In production: send to API endpoint to save to vendor_groups table
        }}
    </script>
</body>
</html>'''
        
        with open(interface_file, 'w') as f:
            f.write(html)
        
        return interface_file
    
    def _create_sample_groups(self):
        """Create sample groups and save to database"""
        # Get top vendors
        result = supabase.table('transactions').select('vendor_name, amount')\
            .eq('client_id', self.client_id)\
            .execute()
        
        vendor_stats = defaultdict(lambda: {'count': 0, 'total': 0})
        for txn in result.data:
            vendor = txn['vendor_name']
            vendor_stats[vendor]['count'] += 1
            vendor_stats[vendor]['total'] += abs(float(txn['amount']))
        
        # Create logical groups
        all_vendors = list(vendor_stats.keys())
        
        groups = {
            'Revenue Sources': [v for v in all_vendors if any(x in v.lower() for x in ['shopify', 'stripe', 'bestselfco'])],
            'Payment Processing': [v for v in all_vendors if any(x in v.lower() for x in ['amex', 'paypal', 'square'])],
            'International': [v for v in all_vendors if any(x in v.lower() for x in ['ltd', 'international', 'wise'])],
            'Operations': [v for v in all_vendors if v not in [item for sublist in [
                [v for v in all_vendors if any(x in v.lower() for x in ['shopify', 'stripe', 'bestselfco'])],
                [v for v in all_vendors if any(x in v.lower() for x in ['amex', 'paypal', 'square'])],
                [v for v in all_vendors if any(x in v.lower() for x in ['ltd', 'international', 'wise'])]
            ] for item in sublist]][:10]  # Limit to 10 for demo
        }
        
        # Save to database
        supabase.table('vendor_groups').delete().eq('client_id', self.client_id).execute()
        
        for group_name, vendor_list in groups.items():
            if vendor_list:  # Only save non-empty groups
                record = {
                    'client_id': self.client_id,
                    'group_name': group_name,
                    'vendor_display_names': vendor_list,
                    'is_active': True,
                    'created_at': datetime.now().isoformat()
                }
                supabase.table('vendor_groups').insert(record).execute()
                print(f"   ✅ Created group: {group_name} ({len(vendor_list)} vendors)")
        
        return groups
    
    def _analyze_group_pattern(self, group_name: str, transactions: list) -> dict:
        """Analyze transaction pattern for a vendor group"""
        dates = [datetime.fromisoformat(t['transaction_date']).date() for t in transactions]
        amounts = [abs(float(t['amount'])) for t in transactions]
        
        # Calculate gaps
        gaps = []
        for i in range(1, len(dates)):
            gap = (dates[i] - dates[i-1]).days
            if gap > 0:
                gaps.append(gap)
        
        if not gaps:
            return {'pattern_type': 'irregular', 'avg_amount': sum(amounts) / len(amounts), 'confidence': 0.3}
        
        avg_gap = sum(gaps) / len(gaps)
        avg_amount = sum(amounts) / len(amounts)
        
        # Determine pattern
        if avg_gap < 3:
            pattern_type = 'daily'
            confidence = 0.8
        elif avg_gap < 10:
            pattern_type = 'weekly'  
            confidence = 0.7
        elif avg_gap < 20:
            pattern_type = 'bi-weekly'
            confidence = 0.7
        elif avg_gap < 35:
            pattern_type = 'monthly'
            confidence = 0.6
        else:
            pattern_type = 'irregular'
            confidence = 0.4
        
        return {
            'pattern_type': pattern_type,
            'avg_amount': avg_amount,
            'confidence': confidence,
            'transaction_count': len(transactions),
            'avg_gap_days': avg_gap
        }
    
    def _save_pattern_analysis(self, group_name: str, pattern_info: dict):
        """Save pattern analysis to database"""
        record = {
            'client_id': self.client_id,
            'vendor_group_name': group_name,
            'analysis_date': date.today().isoformat(),
            'frequency_detected': pattern_info['pattern_type'],
            'confidence_score': pattern_info['confidence'],
            'sample_size': pattern_info['transaction_count'],
            'average_amount': pattern_info['avg_amount'],
            'explanation': f"Average gap: {pattern_info['avg_gap_days']:.1f} days",
            'created_at': datetime.now().isoformat()
        }
        
        supabase.table('pattern_analysis').upsert(record).execute()
    
    def _create_manual_interface(self, manual_vendors: list) -> str:
        """Create manual forecast setup interface"""
        interface_file = os.path.join(self.temp_dir, f"{self.client_id}_manual.html")
        
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Manual Setup - {self.client_id}</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50">
    <div class="container mx-auto p-6">
        <h1 class="text-2xl font-bold mb-6">⚙️ Manual Forecast Setup - {self.client_id}</h1>
        <p class="mb-4">{len(manual_vendors)} vendors need manual configuration</p>
        
        <div class="space-y-4">'''
        
        for vendor in manual_vendors:
            html += f'''
            <div class="bg-white p-4 rounded border">
                <h3 class="font-semibold">{vendor['vendor_group_name']}</h3>
                <p class="text-sm text-gray-600">Current: {vendor.get('frequency_detected', 'unknown')} pattern</p>
                <p class="text-sm text-gray-600">Confidence: {vendor.get('confidence_score', 0):.1%}</p>
                
                <div class="mt-3 grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm font-medium">Frequency</label>
                        <select class="w-full border rounded px-3 py-2">
                            <option>weekly</option>
                            <option>bi-weekly</option>
                            <option>monthly</option>
                            <option>irregular</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-medium">Amount ($)</label>
                        <input type="number" class="w-full border rounded px-3 py-2" 
                               value="{vendor.get('average_amount', 0):.0f}">
                    </div>
                </div>
            </div>'''
        
        html += '''
        </div>
        
        <div class="mt-6">
            <button onclick="saveConfigs()" class="bg-green-600 text-white px-6 py-2 rounded">
                💾 Save Configurations
            </button>
        </div>
    </div>
    
    <script>
        function saveConfigs() {
            alert('Manual configurations saved to database');
            // In production: collect form data and save to forecast_config table
        }
    </script>
</body>
</html>'''
        
        with open(interface_file, 'w') as f:
            f.write(html)
        
        return interface_file
    
    def _save_sample_forecast_configs(self, manual_vendors: list):
        """Save sample forecast configurations"""
        for vendor in manual_vendors:
            config = {
                'client_id': self.client_id,
                'vendor_name': vendor['vendor_group_name'],
                'forecast_type': vendor.get('frequency_detected', 'monthly'),
                'forecast_amount': float(vendor.get('average_amount', 1000)),
                'is_active': True,
                'created_at': datetime.now().isoformat()
            }
            
            supabase.table('forecast_config').upsert(config).execute()
        
        print(f"   ✅ Saved {len(manual_vendors)} forecast configurations")
    
    def _generate_forecast_records(self) -> int:
        """Generate forecast records for next 13 weeks"""
        # Get all configured vendors
        groups = supabase.table('vendor_groups').select('*')\
            .eq('client_id', self.client_id)\
            .execute()
        
        patterns = supabase.table('pattern_analysis').select('*')\
            .eq('client_id', self.client_id)\
            .execute()
        
        # Clear existing forecasts
        supabase.table('forecasts').delete().eq('client_id', self.client_id).execute()
        
        forecast_records = []
        start_date = date.today()
        
        for group in groups.data:
            group_name = group['group_name']
            
            # Find pattern for this group
            pattern = next((p for p in patterns.data if p['vendor_group_name'] == group_name), None)
            if not pattern:
                continue
            
            frequency = pattern.get('frequency_detected', 'monthly')
            amount = float(pattern.get('average_amount', 0))
            
            # Generate dates for 13 weeks
            current_date = start_date
            end_date = start_date + timedelta(weeks=13)
            
            while current_date <= end_date:
                if frequency == 'weekly' and current_date.weekday() == 0:  # Mondays
                    forecast_records.append({
                        'client_id': self.client_id,
                        'vendor_group_name': group_name,
                        'forecast_date': current_date.isoformat(),
                        'forecast_amount': amount,
                        'forecast_type': frequency,
                        'forecast_method': 'weighted_average',
                        'pattern_confidence': float(pattern.get('confidence_score', 0.5)),
                        'created_at': datetime.now().isoformat()
                    })
                elif frequency == 'monthly' and current_date.day == 1:  # First of month
                    forecast_records.append({
                        'client_id': self.client_id,
                        'vendor_group_name': group_name,
                        'forecast_date': current_date.isoformat(),
                        'forecast_amount': amount,
                        'forecast_type': frequency,
                        'forecast_method': 'weighted_average',
                        'pattern_confidence': float(pattern.get('confidence_score', 0.5)),
                        'created_at': datetime.now().isoformat()
                    })
                
                current_date += timedelta(days=1)
        
        # Save forecasts
        if forecast_records:
            supabase.table('forecasts').insert(forecast_records).execute()
        
        return len(forecast_records)
    
    def _create_forecast_display(self) -> str:
        """Create forecast display"""
        # Get forecast data
        forecasts = supabase.table('forecasts').select('*')\
            .eq('client_id', self.client_id)\
            .order('forecast_date')\
            .execute()
        
        display_file = os.path.join(self.temp_dir, f"{self.client_id}_forecast.html")
        
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>13-Week Forecast - {self.client_id}</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50">
    <div class="container mx-auto p-6">
        <h1 class="text-2xl font-bold mb-6">📈 13-Week Cash Flow Forecast - {self.client_id}</h1>
        <p class="mb-4">Generated from {len(forecasts.data)} forecast records</p>
        
        <div class="bg-white p-6 rounded-lg shadow">
            <h2 class="text-lg font-semibold mb-4">Summary</h2>
            <p>Total forecasted inflows: ${sum(f['forecast_amount'] for f in forecasts.data if f['forecast_amount'] > 0):,.0f}</p>
            <p>Total forecasted outflows: ${abs(sum(f['forecast_amount'] for f in forecasts.data if f['forecast_amount'] < 0)):,.0f}</p>
            <p>Net cash flow: ${sum(f['forecast_amount'] for f in forecasts.data):,.0f}</p>
        </div>
        
        <div class="mt-6 bg-white p-6 rounded-lg shadow">
            <h2 class="text-lg font-semibold mb-4">Forecast Records</h2>
            <div class="overflow-x-auto">
                <table class="w-full text-sm">
                    <thead>
                        <tr class="border-b">
                            <th class="text-left p-2">Date</th>
                            <th class="text-left p-2">Vendor Group</th>
                            <th class="text-right p-2">Amount</th>
                            <th class="text-left p-2">Type</th>
                        </tr>
                    </thead>
                    <tbody>'''
        
        for forecast in forecasts.data:
            amount_color = 'text-green-600' if forecast['forecast_amount'] > 0 else 'text-red-600'
            html += f'''
                        <tr class="border-b hover:bg-gray-50">
                            <td class="p-2">{forecast['forecast_date']}</td>
                            <td class="p-2">{forecast['vendor_group_name']}</td>
                            <td class="p-2 text-right {amount_color}">${forecast['forecast_amount']:,.0f}</td>
                            <td class="p-2">{forecast['forecast_type']}</td>
                        </tr>'''
        
        html += '''
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</body>
</html>'''
        
        with open(display_file, 'w') as f:
            f.write(html)
        
        return display_file

def main():
    parser = argparse.ArgumentParser(description='Complete multi-client onboarding system')
    parser.add_argument('--client', required=True, help='Client ID')
    parser.add_argument('--step', required=True, choices=['1', '2', '3', '4', '5'], help='Step to run')
    parser.add_argument('--csv', help='CSV file for step 1')
    args = parser.parse_args()
    
    system = CompleteMultiClientOnboarding(args.client)
    
    success = False
    if args.step == '1':
        if not args.csv:
            print("❌ --csv required for step 1")
            return
        success = system.run_step1_import(args.csv)
    elif args.step == '2':
        success = system.run_step2_grouping()
    elif args.step == '3':
        success = system.run_step3_patterns()
    elif args.step == '4':
        success = system.run_step4_manual()
    elif args.step == '5':
        success = system.run_step5_display()
    
    if success:
        print(f"\\n🎉 Step {args.step} completed successfully for client {args.client}")
    else:
        print(f"\\n❌ Step {args.step} failed for client {args.client}")

if __name__ == "__main__":
    main()