#!/usr/bin/env python3
"""
Multi-Client Cash Flow Forecasting System
Complete workflow from import to forecast for any client
"""
import sys
import argparse
import os
from datetime import datetime

def print_header(step, description):
    print(f'\n{"="*60}')
    print(f'STEP {step}: {description}')
    print(f'{"="*60}')

def run_step1_import(client_id, csv_file):
    """Step 1: Clean import transactions"""
    print_header(1, f'CLEAN IMPORT - {client_id}')
    
    import subprocess
    
    # Create client-specific import script
    import_script = f"""#!/usr/bin/env python3
import sys
import csv
sys.path.append('.')
from supabase_client import supabase
from datetime import datetime, date

print('IMPORTING TRANSACTIONS FOR CLIENT: {client_id}')
print('CSV File: {csv_file}')

# Clear existing data for this client
print('🗑️ Clearing existing data for {client_id}...')
tables_to_clear = ['forecasts', 'pattern_analysis', 'vendor_groups', 'vendors', 'transactions']

for table in tables_to_clear:
    try:
        result = supabase.table(table).delete().eq('client_id', '{client_id}').execute()
        print(f'   ✅ Cleared {{table}}')
    except Exception as e:
        print(f'   ⚠️ Error clearing {{table}}: {{e}}')

# Import CSV
transactions = []
skipped = 0
row_num = 0

with open('{csv_file}', 'r', encoding='utf-8') as file:
    reader = csv.DictReader(file)
    
    for row in reader:
        row_num += 1
        
        if row.get('Status') == 'Failed':
            skipped += 1
            continue
        
        try:
            amount = float(row.get('Amount', '0').replace(',', ''))
        except:
            skipped += 1
            continue
        
        try:
            transaction_date = datetime.strptime(row.get('Date (UTC)', ''), '%m-%d-%Y').date()
        except:
            try:
                transaction_date = datetime.strptime(row.get('Date (UTC)', ''), '%Y-%m-%d').date()
            except:
                skipped += 1
                continue
        
        transaction = {{
            'transaction_id': f"{client_id}_{{transaction_date}}_{{row_num}}",
            'client_id': '{client_id}',
            'transaction_date': transaction_date.isoformat(),
            'vendor_name': row.get('Description', '').strip(),
            'amount': amount,
            'created_at': datetime.now().isoformat()
        }}
        
        transactions.append(transaction)

# Save to database in batches
batch_size = 100
imported = 0

for i in range(0, len(transactions), batch_size):
    batch = transactions[i:i + batch_size]
    try:
        supabase.table('transactions').insert(batch).execute()
        imported += len(batch)
        print(f"✅ Imported batch {{i//batch_size + 1}}: {{len(batch)}} transactions")
    except Exception as e:
        print(f"❌ Error importing batch: {{str(e)}}")

print(f"\\n✅ IMPORT COMPLETE FOR {client_id}!")
print(f"📊 Imported: {{imported}} transactions")
print(f"⏭️ Skipped: {{skipped}} transactions")

dates = [t['transaction_date'] for t in transactions]
if dates:
    print(f"📅 Date range: {{min(dates)}} to {{max(dates)}}")
"""
    
    # Write and execute import script
    with open(f'temp_import_{client_id}.py', 'w') as f:
        f.write(import_script)
    
    try:
        result = subprocess.run([sys.executable, f'temp_import_{client_id}.py'], 
                              capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(f"Errors: {result.stderr}")
    finally:
        # Clean up temp file
        if os.path.exists(f'temp_import_{client_id}.py'):
            os.remove(f'temp_import_{client_id}.py')

def run_step2_vendor_mapping(client_id):
    """Step 2: Generate vendor mapping CSV"""
    print_header(2, f'VENDOR MAPPING CSV - {client_id}')
    
    import subprocess
    
    # Create client-specific vendor mapping script
    mapping_script = f"""#!/usr/bin/env python3
import sys
import csv
from collections import defaultdict
sys.path.append('.')
from supabase_client import supabase
from core.vendor_auto_mapping import auto_mapper

print('GENERATING VENDOR MAPPING FOR CLIENT: {client_id}')

# Get all unique vendors with transaction stats
transactions = supabase.table('transactions').select('*').eq('client_id', '{client_id}').execute()

vendor_stats = defaultdict(lambda: {{'count': 0, 'total_amount': 0}})

for txn in transactions.data:
    vendor = txn['vendor_name']
    amount = float(txn['amount'])
    vendor_stats[vendor]['count'] += 1
    vendor_stats[vendor]['total_amount'] += amount

print(f'✅ Found {{len(vendor_stats)}} unique vendors')

# Apply regex patterns and create mapping data
vendor_mapping_data = []

for vendor_name, stats in vendor_stats.items():
    suggested_group = auto_mapper.auto_map_vendor(vendor_name)
    
    vendor_mapping_data.append({{
        'vendor_name': vendor_name,
        'transaction_count': stats['count'],
        'total_amount': stats['total_amount'],
        'regex_suggested_group': suggested_group or '',
        'your_group_name': ''
    }})

# Sort by total amount (highest first)
vendor_mapping_data.sort(key=lambda x: abs(x['total_amount']), reverse=True)

# Create CSV
csv_filename = '{client_id}_vendor_mapping.csv'
with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    
    writer.writerow(['INSTRUCTIONS: Fill in YOUR_GROUP_NAME column. Leave blank to use vendor as individual.'])
    writer.writerow([''])
    writer.writerow(['Vendor Name', 'Transaction Count', 'Total Amount', 'Regex Suggested Group', 'YOUR GROUP NAME (EDIT THIS)'])
    
    for vendor_data in vendor_mapping_data:
        writer.writerow([
            vendor_data['vendor_name'],
            vendor_data['transaction_count'],
            f"${{vendor_data['total_amount']:,.2f}}",
            vendor_data['regex_suggested_group'],
            vendor_data['your_group_name']
        ])

print(f'✅ Created: {{csv_filename}}')
print(f'📊 {{len(vendor_mapping_data)}} vendors ready for review')

# Show regex summary
regex_groups = defaultdict(int)
for vendor in vendor_mapping_data:
    if vendor['regex_suggested_group']:
        regex_groups[vendor['regex_suggested_group']] += 1

print(f'\\n🤖 Regex Auto-Mapping Summary:')
for group, count in regex_groups.items():
    print(f'   - {{group}}: {{count}} vendors')

unmapped_count = sum(1 for v in vendor_mapping_data if not v['regex_suggested_group'])
print(f'   - No regex match: {{unmapped_count}} vendors')
"""
    
    # Write and execute mapping script
    with open(f'temp_mapping_{client_id}.py', 'w') as f:
        f.write(mapping_script)
    
    try:
        result = subprocess.run([sys.executable, f'temp_mapping_{client_id}.py'], 
                              capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(f"Errors: {result.stderr}")
    finally:
        # Clean up temp file
        if os.path.exists(f'temp_mapping_{client_id}.py'):
            os.remove(f'temp_mapping_{client_id}.py')

def main():
    parser = argparse.ArgumentParser(description='Multi-Client Cash Flow Forecasting System')
    parser.add_argument('--client', required=True, help='Client ID (e.g., BestSelf, ClientB)')
    parser.add_argument('--step', required=True, choices=['1', '2', '3', '4', 'all'], 
                       help='Step to run (1=import, 2=mapping, 3=patterns, 4=forecast, all=complete workflow)')
    parser.add_argument('--csv', help='CSV file for step 1 (import)')
    
    args = parser.parse_args()
    
    print(f'🚀 MULTI-CLIENT FORECASTING SYSTEM')
    print(f'Client: {args.client}')
    print(f'Step: {args.step}')
    print(f'Timestamp: {datetime.now().isoformat()}')
    
    if args.step in ['1', 'all']:
        if not args.csv:
            print("❌ --csv required for import step")
            return
        run_step1_import(args.client, args.csv)
    
    if args.step in ['2', 'all']:
        run_step2_vendor_mapping(args.client)
        
        if args.step == 'all':
            print(f'\\n⏸️ WORKFLOW PAUSED')
            print(f'📝 Please edit {args.client}_vendor_mapping.csv')
            print(f'💡 Add your group names in the last column')
            print(f'🎯 Then run: python3 multi_client_workflow.py --client {args.client} --step 3')
            return
    
    if args.step in ['3']:
        print_header(3, f'PATTERN ANALYSIS - {args.client}')
        
        # Check if vendor mapping CSV exists
        mapping_file = f'{args.client}_vendor_mapping.csv'
        if not os.path.exists(mapping_file):
            print(f"❌ Vendor mapping file not found: {mapping_file}")
            print(f"💡 Please run step 2 first or ensure the file exists")
            return
        
        # Run existing pattern detection script
        import subprocess
        try:
            result = subprocess.run([
                sys.executable, 'step3_improved_pattern_detection.py', 
                '--client', args.client
            ], capture_output=True, text=True)
            print(result.stdout)
            if result.stderr:
                print(f"Errors: {result.stderr}")
        except Exception as e:
            print(f"❌ Error running pattern analysis: {e}")
    
    if args.step in ['4']:
        print_header(4, f'FORECAST GENERATION - {args.client}')
        
        # Check if pattern analysis CSV exists
        pattern_file = f'{args.client}_pattern_analysis.csv'
        if not os.path.exists(pattern_file):
            print(f"❌ Pattern analysis file not found: {pattern_file}")
            print(f"💡 Please run step 3 first or ensure the file exists")
            return
        
        # Run existing forecast generation script
        import subprocess
        try:
            result = subprocess.run([
                sys.executable, 'step4_final_cash_flow_forecast.py', 
                '--client', args.client
            ], capture_output=True, text=True)
            print(result.stdout)
            if result.stderr:
                print(f"Errors: {result.stderr}")
        except Exception as e:
            print(f"❌ Error running forecast generation: {e}")
    
    print(f'\\n🎉 COMPLETED STEPS FOR CLIENT: {args.client}')

if __name__ == "__main__":
    main()