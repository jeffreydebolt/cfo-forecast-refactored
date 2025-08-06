#!/usr/bin/env python3
"""
Import Mercury CSV transactions into database
Handles the specific Mercury CSV format
"""

import sys
import csv
import argparse
from datetime import datetime
from decimal import Decimal

sys.path.append('.')

from supabase_client import supabase

def parse_mercury_date(date_str):
    """Parse Mercury date format (MM-DD-YYYY)"""
    try:
        return datetime.strptime(date_str, '%m-%d-%Y').date()
    except:
        # Try alternate format
        return datetime.strptime(date_str, '%Y-%m-%d').date()

def import_mercury_csv(filename: str, client_id: str):
    """Import Mercury CSV file to transactions table"""
    print(f"📥 IMPORTING MERCURY TRANSACTIONS")
    print(f"File: {filename}")
    print(f"Client: {client_id}")
    print("=" * 80)
    
    transactions = []
    skipped = 0
    row_num = 0
    
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                row_num += 1
                # Skip failed transactions
                if row.get('Status') == 'Failed':
                    skipped += 1
                    continue
                
                # Parse amount (negative for outflows)
                amount = Decimal(row['Amount'].replace(',', ''))
                
                # Parse date
                transaction_date = parse_mercury_date(row['Date (UTC)'])
                
                # Build transaction record - include unique transaction_id
                transaction = {
                    'transaction_id': f"{client_id}_{transaction_date}_{row_num}",
                    'client_id': client_id,
                    'transaction_date': transaction_date.isoformat(),
                    'vendor_name': row['Description'],
                    'amount': float(amount),
                    'created_at': datetime.now().isoformat()
                }
                
                transactions.append(transaction)
        
        print(f"📊 Found {len(transactions)} valid transactions")
        print(f"⏭️ Skipped {skipped} failed transactions")
        
        if not transactions:
            print("❌ No valid transactions to import")
            return
        
        # Import in batches
        batch_size = 100
        total_imported = 0
        
        for i in range(0, len(transactions), batch_size):
            batch = transactions[i:i + batch_size]
            
            try:
                result = supabase.table('transactions').insert(batch).execute()
                total_imported += len(batch)
                print(f"✅ Imported batch {i//batch_size + 1}: {len(batch)} transactions")
            except Exception as e:
                print(f"❌ Error importing batch: {str(e)}")
                # Try to understand the error
                if 'columns' in str(e):
                    print("\nColumn mismatch. Let me check the table structure...")
                    check_table_structure()
                return
        
        print(f"\n✅ IMPORT COMPLETE!")
        print(f"📊 Total imported: {total_imported} transactions")
        
        # Show date range
        dates = [t['transaction_date'] for t in transactions]
        print(f"📅 Date range: {min(dates)} to {max(dates)}")
        
        # Show top vendors
        vendors = {}
        for t in transactions:
            vendor = t['vendor_name']
            if vendor not in vendors:
                vendors[vendor] = 0
            vendors[vendor] += 1
        
        print(f"\n📈 Top 5 vendors by transaction count:")
        for vendor, count in sorted(vendors.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"   - {vendor}: {count} transactions")
        
    except FileNotFoundError:
        print(f"❌ File not found: {filename}")
    except Exception as e:
        print(f"❌ Error reading CSV: {str(e)}")

def check_table_structure():
    """Check the structure of transactions table"""
    try:
        result = supabase.table('transactions').select('*').limit(1).execute()
        if result.data:
            print("\nExisting columns:", list(result.data[0].keys()))
        else:
            # Try to get table info another way
            print("\nTable exists but is empty")
    except Exception as e:
        print(f"\nCouldn't check table structure: {e}")

def main():
    parser = argparse.ArgumentParser(description='Import Mercury CSV transactions')
    parser.add_argument('--file', default='BS_mercury_transactions.csv', help='CSV file to import')
    parser.add_argument('--client', required=True, help='Client ID for the transactions')
    args = parser.parse_args()
    
    import_mercury_csv(args.file, args.client)

if __name__ == "__main__":
    main()