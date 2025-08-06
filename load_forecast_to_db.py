#!/usr/bin/env python3
"""
Load forecast CSV data into database as FORECAST type transactions
"""
import sys
import csv
import argparse
from datetime import datetime
sys.path.append('.')
from supabase_client import supabase

def load_forecast_csv(client_id, csv_file):
    """Load forecast data from CSV into database"""
    print(f"Loading forecast data for {client_id} from {csv_file}")
    
    # Clear existing forecast data for this client
    print("🗑️ Clearing existing forecast data...")
    delete_result = supabase.table('transactions').delete().eq('client_id', client_id).eq('type', 'FORECAST').execute()
    print(f"Deleted existing forecast transactions")
    
    # Read CSV and prepare transactions
    forecast_transactions = []
    row_count = 0
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            row_count += 1
            
            # Parse the CSV columns
            date_str = row.get('Date', '').strip()
            vendor = row.get('Vendor/Group', '').strip() or row.get('Vendor', '').strip() or row.get('Entity', '').strip()
            amount_str = row.get('Amount', '').strip()
            
            if not date_str or not vendor or not amount_str:
                print(f"⚠️ Skipping incomplete row {row_count}: {row}")
                continue
            
            try:
                # Parse date
                transaction_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                
                # Parse amount
                amount = float(amount_str.replace('$', '').replace(',', ''))
                
                # Create forecast transaction
                forecast_transaction = {
                    'transaction_id': f"{client_id}_FORECAST_{transaction_date}_{row_count}",
                    'client_id': client_id,
                    'transaction_date': transaction_date.isoformat(),
                    'vendor_name': vendor,
                    'amount': amount,
                    'type': 'FORECAST',
                    'created_at': datetime.now().isoformat()
                }
                
                forecast_transactions.append(forecast_transaction)
                
            except Exception as e:
                print(f"❌ Error parsing row {row_count}: {e}")
                print(f"Row data: {row}")
                continue
    
    print(f"📊 Parsed {len(forecast_transactions)} forecast transactions")
    
    if not forecast_transactions:
        print("❌ No valid forecast transactions found")
        return
    
    # Insert in batches
    batch_size = 100
    inserted = 0
    
    for i in range(0, len(forecast_transactions), batch_size):
        batch = forecast_transactions[i:i + batch_size]
        try:
            supabase.table('transactions').insert(batch).execute()
            inserted += len(batch)
            print(f"✅ Inserted batch {i//batch_size + 1}: {len(batch)} transactions")
        except Exception as e:
            print(f"❌ Error inserting batch: {str(e)}")
    
    print(f"💾 Total inserted: {inserted} forecast transactions")
    
    # Show summary
    if inserted > 0:
        # Get date range
        dates = [t['transaction_date'] for t in forecast_transactions]
        print(f"📅 Forecast range: {min(dates)} to {max(dates)}")
        
        # Get vendor summary
        vendors = {}
        for t in forecast_transactions:
            vendor = t['vendor_name']
            vendors[vendor] = vendors.get(vendor, 0) + 1
        
        print(f"🏷️ Vendors forecasted: {len(vendors)}")
        for vendor, count in sorted(vendors.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"   - {vendor}: {count} transactions")

def main():
    parser = argparse.ArgumentParser(description='Load forecast CSV into database')
    parser.add_argument('--client', required=True, help='Client ID')
    parser.add_argument('--csv', required=True, help='Forecast CSV file')
    
    args = parser.parse_args()
    
    print(f"🚀 LOADING FORECAST DATA")
    print(f"Client: {args.client}")
    print(f"CSV: {args.csv}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    load_forecast_csv(args.client, args.csv)
    
    print(f"\n✅ FORECAST LOAD COMPLETE")
    print(f"Now you can generate the dashboard with:")
    print(f"python3 generate_weekly_dashboard.py {args.client}")

if __name__ == "__main__":
    main()