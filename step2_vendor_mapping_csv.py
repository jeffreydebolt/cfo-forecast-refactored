#!/usr/bin/env python3
import sys
import csv
from collections import defaultdict
sys.path.append('.')
from supabase_client import supabase
from core.vendor_auto_mapping import auto_mapper

print('STEP 2: VENDOR MAPPING CSV (REGEX FIRST!)')
print('Client: BestSelf') 
print('=' * 60)

# Get all unique vendors with transaction stats
print('📊 Analyzing all vendors...')
transactions = supabase.table('transactions').select('*').eq('client_id', 'BestSelf').execute()

vendor_stats = defaultdict(lambda: {'count': 0, 'total_amount': 0, 'transactions': []})

for txn in transactions.data:
    vendor = txn['vendor_name']
    amount = float(txn['amount'])
    vendor_stats[vendor]['count'] += 1
    vendor_stats[vendor]['total_amount'] += amount
    vendor_stats[vendor]['transactions'].append({
        'date': txn['transaction_date'],
        'amount': amount
    })

print(f'✅ Found {len(vendor_stats)} unique vendors')

# Apply regex patterns first
print('🤖 Applying regex patterns...')
vendor_mapping_data = []

for vendor_name, stats in vendor_stats.items():
    # Try regex auto-mapping first
    suggested_group = auto_mapper.auto_map_vendor(vendor_name)
    
    vendor_mapping_data.append({
        'vendor_name': vendor_name,
        'transaction_count': stats['count'],
        'total_amount': stats['total_amount'],
        'regex_suggested_group': suggested_group or '',
        'your_group_name': ''  # Empty for user to fill
    })

# Sort by total amount (highest first) to prioritize important vendors
vendor_mapping_data.sort(key=lambda x: abs(x['total_amount']), reverse=True)

# Create CSV for user to edit
csv_filename = 'bestself_vendor_mapping.csv'
print(f'📝 Creating vendor mapping CSV: {csv_filename}')

with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    
    # Header with instructions
    writer.writerow(['INSTRUCTIONS: Fill in YOUR_GROUP_NAME column. Leave blank to use vendor as individual. Put same group name for vendors you want combined.'])
    writer.writerow(['']) # Empty row
    writer.writerow(['Vendor Name', 'Transaction Count', 'Total Amount', 'Regex Suggested Group', 'YOUR GROUP NAME (EDIT THIS)'])
    
    for vendor_data in vendor_mapping_data:
        writer.writerow([
            vendor_data['vendor_name'],
            vendor_data['transaction_count'],
            f"${vendor_data['total_amount']:,.2f}",
            vendor_data['regex_suggested_group'],
            vendor_data['your_group_name']  # Empty for user to fill
        ])

print(f'✅ Created: {csv_filename}')
print(f'📊 {len(vendor_mapping_data)} vendors ready for your review')

# Show summary of regex suggestions
regex_groups = defaultdict(int)
for vendor in vendor_mapping_data:
    if vendor['regex_suggested_group']:
        regex_groups[vendor['regex_suggested_group']] += 1

print(f'\n🤖 Regex Auto-Mapping Summary:')
for group, count in regex_groups.items():
    print(f'   - {group}: {count} vendors')

unmapped_count = sum(1 for v in vendor_mapping_data if not v['regex_suggested_group'])
print(f'   - No regex match: {unmapped_count} vendors')

print(f'\n📋 NEXT STEPS:')
print(f'1. Open {csv_filename} in Excel/Google Sheets')
print(f'2. Review the "YOUR GROUP NAME" column')
print(f'3. For vendors you want to group together, put the SAME group name')
print(f'4. Leave blank for vendors you want to keep individual')
print(f'5. Save the CSV and let me know when ready for Step 3')

print(f'\n💡 TIP: Focus on the top vendors first (highest transaction amounts)')