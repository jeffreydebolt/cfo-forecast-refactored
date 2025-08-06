#!/usr/bin/env python3
import sys
import csv
sys.path.append('.')
from supabase_client import supabase
from datetime import datetime, date
from core.vendor_auto_mapping import auto_mapper

print('STEP 1: CLEAN SLATE - DELETE & RE-IMPORT')
print('Client: BestSelf') 
print('=' * 60)

# Delete all existing data for clean start
print('🗑️ Clearing all existing data...')
tables_to_clear = ['forecasts', 'pattern_analysis', 'vendor_groups', 'vendors', 'transactions']

for table in tables_to_clear:
    try:
        result = supabase.table(table).delete().eq('client_id', 'BestSelf').execute()
        print(f'   ✅ Cleared {table}')
    except Exception as e:
        print(f'   ⚠️ Error clearing {table}: {e}')

# Re-import Mercury transactions
print('\n📥 Re-importing Mercury transactions...')
csv_file = 'BS_mercury_transactions.csv'

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
            'transaction_id': f"BestSelf_{transaction_date}_{row_num}",
            'client_id': 'BestSelf',
            'transaction_date': transaction_date.isoformat(),
            'vendor_name': row.get('Description', '').strip(),
            'amount': amount,
            'created_at': datetime.now().isoformat()
        }
        
        transactions.append(transaction)

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

print(f"\n✅ IMPORT COMPLETE!")
print(f"📊 Imported: {imported} transactions")
print(f"⏭️ Skipped: {skipped} transactions")

# Show date range
dates = [t['transaction_date'] for t in transactions]
print(f"📅 Date range: {min(dates)} to {max(dates)}")

print(f"\n🎉 Ready for Step 2: Vendor Mapping CSV")