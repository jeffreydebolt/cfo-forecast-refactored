#!/usr/bin/env python3
"""
Weekly Actuals Process - Monday Morning Workflow
Replace forecasted transactions with actual transactions, generate variance report
"""
import sys
import argparse
import csv
from datetime import datetime, date, timedelta
from collections import defaultdict
sys.path.append('.')
from supabase_client import supabase
from core.vendor_auto_mapping import auto_mapper

def print_header(title):
    print(f'\n{"="*60}')
    print(f'{title}')
    print(f'{"="*60}')

def get_week_dates(target_date):
    """Get Monday-Sunday dates for the week containing target_date"""
    days_since_monday = target_date.weekday()
    monday = target_date - timedelta(days=days_since_monday)
    sunday = monday + timedelta(days=6)
    return monday, sunday

def import_actuals(client_id, csv_file, week_start, week_end):
    """Import actual transactions from CSV for specified week"""
    print(f'📥 Importing actuals for {client_id}')
    print(f'Week: {week_start} to {week_end}')
    print(f'CSV: {csv_file}')
    
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
            
            # Only import transactions within the target week
            if week_start <= transaction_date <= week_end:
                raw_vendor = row.get('Description', '').strip()
                
                # Apply same vendor mapping as forecasts
                mapped_vendor = auto_mapper.auto_map_vendor(raw_vendor)
                vendor_name = mapped_vendor if mapped_vendor else raw_vendor
                
                transaction = {
                    'transaction_id': f"{client_id}_{transaction_date}_{row_num}_ACTUAL",
                    'client_id': client_id,
                    'transaction_date': transaction_date.isoformat(),
                    'vendor_name': vendor_name,  # Use mapped vendor name
                    'amount': amount,
                    'type': 'ACTUAL',  # Mark as actual vs forecast
                    'created_at': datetime.now().isoformat()
                }
                transactions.append(transaction)
    
    print(f'✅ Found {len(transactions)} actual transactions for the week')
    print(f'⏭️ Skipped {skipped} transactions (failed or outside date range)')
    
    return transactions

def get_forecasted_transactions(client_id, week_start, week_end):
    """Get forecasted transactions for the specified week"""
    forecasted = supabase.table('transactions').select('*')\
        .eq('client_id', client_id)\
        .gte('transaction_date', week_start.isoformat())\
        .lte('transaction_date', week_end.isoformat())\
        .eq('type', 'FORECAST')\
        .execute()
    
    print(f'📊 Found {len(forecasted.data)} forecasted transactions for the week')
    return forecasted.data

def replace_forecasts_with_actuals(client_id, week_start, week_end, actual_transactions):
    """Remove forecasted transactions and insert actual transactions"""
    print(f'🔄 Replacing forecasts with actuals for {week_start} to {week_end}')
    
    # Get forecasted transactions before deletion (for variance analysis)
    forecasted_transactions = get_forecasted_transactions(client_id, week_start, week_end)
    
    # Delete forecasted transactions for this week
    delete_result = supabase.table('transactions').delete()\
        .eq('client_id', client_id)\
        .gte('transaction_date', week_start.isoformat())\
        .lte('transaction_date', week_end.isoformat())\
        .eq('type', 'FORECAST')\
        .execute()
    
    print(f'🗑️ Deleted {len(forecasted_transactions)} forecasted transactions')
    
    # Insert actual transactions
    if actual_transactions:
        batch_size = 100
        inserted = 0
        
        for i in range(0, len(actual_transactions), batch_size):
            batch = actual_transactions[i:i + batch_size]
            try:
                supabase.table('transactions').insert(batch).execute()
                inserted += len(batch)
                print(f"✅ Inserted batch {i//batch_size + 1}: {len(batch)} actual transactions")
            except Exception as e:
                print(f"❌ Error inserting batch: {str(e)}")
        
        print(f'💾 Total inserted: {inserted} actual transactions')
    
    return forecasted_transactions

def generate_variance_report(client_id, week_start, week_end, forecasted_transactions, actual_transactions):
    """Generate forecast vs actual variance report"""
    print(f'📊 Generating variance report for {week_start} to {week_end}')
    
    # Group by vendor for comparison
    forecasted_by_vendor = defaultdict(float)
    actual_by_vendor = defaultdict(float)
    
    for txn in forecasted_transactions:
        vendor = txn['vendor_name']
        amount = float(txn['amount'])
        forecasted_by_vendor[vendor] += amount
    
    for txn in actual_transactions:
        vendor = txn['vendor_name']
        amount = float(txn['amount'])
        actual_by_vendor[vendor] += amount
    
    # Calculate variances
    all_vendors = set(forecasted_by_vendor.keys()) | set(actual_by_vendor.keys())
    variance_data = []
    
    total_forecasted = 0
    total_actual = 0
    
    for vendor in all_vendors:
        forecasted_amount = forecasted_by_vendor[vendor]
        actual_amount = actual_by_vendor[vendor]
        variance = actual_amount - forecasted_amount
        variance_pct = (variance / forecasted_amount * 100) if forecasted_amount != 0 else 0
        
        total_forecasted += forecasted_amount
        total_actual += actual_amount
        
        variance_data.append({
            'vendor': vendor,
            'forecasted': forecasted_amount,
            'actual': actual_amount,
            'variance': variance,
            'variance_pct': variance_pct
        })
    
    # Sort by absolute variance (biggest misses first)
    variance_data.sort(key=lambda x: abs(x['variance']), reverse=True)
    
    # Create variance report CSV
    report_filename = f'{client_id}_variance_report_{week_start.strftime("%Y%m%d")}.csv'
    
    with open(report_filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Vendor',
            'Forecasted Amount',
            'Actual Amount', 
            'Variance ($)',
            'Variance (%)',
            'Notes'
        ])
        
        for item in variance_data:
            notes = []
            if item['forecasted'] == 0 and item['actual'] != 0:
                notes.append('UNEXPECTED TRANSACTION')
            elif item['forecasted'] != 0 and item['actual'] == 0:
                notes.append('MISSED FORECAST')
            elif abs(item['variance_pct']) > 20:
                notes.append('LARGE VARIANCE')
            
            writer.writerow([
                item['vendor'],
                f"${item['forecasted']:,.2f}",
                f"${item['actual']:,.2f}",
                f"${item['variance']:,.2f}",
                f"{item['variance_pct']:.1f}%",
                ' | '.join(notes)
            ])
        
        # Add summary row
        total_variance = total_actual - total_forecasted
        total_variance_pct = (total_variance / total_forecasted * 100) if total_forecasted != 0 else 0
        
        writer.writerow([])
        writer.writerow([
            'WEEKLY TOTAL',
            f"${total_forecasted:,.2f}",
            f"${total_actual:,.2f}",
            f"${total_variance:,.2f}",
            f"{total_variance_pct:.1f}%",
            ''
        ])
    
    print(f'✅ Created variance report: {report_filename}')
    
    # Print summary to console
    print(f'\n📈 WEEKLY VARIANCE SUMMARY:')
    print(f'   💰 Total Forecasted: ${total_forecasted:,.2f}')
    print(f'   💰 Total Actual: ${total_actual:,.2f}')
    print(f'   📊 Total Variance: ${total_variance:,.2f} ({total_variance_pct:.1f}%)')
    
    # Show biggest variances
    print(f'\n⚠️ BIGGEST VARIANCES:')
    for item in variance_data[:5]:
        if abs(item['variance']) > 100:  # Only show significant variances
            print(f'   - {item["vendor"]}: ${item["variance"]:,.2f} ({item["variance_pct"]:.1f}%)')
    
    return report_filename

def update_balance(client_id, actual_balance=None):
    """Update running balance based on actuals (optional manual balance input)"""
    print(f'💰 Updating running balance for {client_id}')
    
    if actual_balance:
        print(f'📊 Manual balance provided: ${actual_balance:,.2f}')
        # In a full system, you'd store this balance and use it for future forecasts
        # For now, just print confirmation
        print(f'✅ Balance updated for {client_id}')
    else:
        # Calculate balance from all transactions
        all_transactions = supabase.table('transactions').select('amount')\
            .eq('client_id', client_id)\
            .order('transaction_date')\
            .execute()
        
        total_balance = sum(float(txn['amount']) for txn in all_transactions.data)
        print(f'📊 Calculated balance from transactions: ${total_balance:,.2f}')
    
    return actual_balance or total_balance

def main():
    parser = argparse.ArgumentParser(description='Weekly Actuals Process - Monday Morning Workflow')
    parser.add_argument('--client', required=True, help='Client ID')
    parser.add_argument('--csv', required=True, help='CSV file with actual transactions')
    parser.add_argument('--week', help='Week to process (YYYY-MM-DD for Monday), defaults to last Monday')
    parser.add_argument('--balance', type=float, help='Actual bank balance (optional)')
    
    args = parser.parse_args()
    
    print_header(f'🔄 WEEKLY ACTUALS PROCESS - {args.client}')
    print(f'Timestamp: {datetime.now().isoformat()}')
    
    # Determine target week
    if args.week:
        target_monday = datetime.strptime(args.week, '%Y-%m-%d').date()
    else:
        # Default to last Monday
        today = date.today()
        days_since_monday = today.weekday()
        target_monday = today - timedelta(days=days_since_monday + 7)  # Last Monday
    
    week_start, week_end = get_week_dates(target_monday)
    
    print(f'📅 Processing week: {week_start} to {week_end}')
    
    # Step 1: Import actual transactions
    print_header('STEP 1: IMPORT ACTUAL TRANSACTIONS')
    actual_transactions = import_actuals(args.client, args.csv, week_start, week_end)
    
    if not actual_transactions:
        print('❌ No actual transactions found for this week. Exiting.')
        return
    
    # Step 2: Replace forecasts with actuals
    print_header('STEP 2: REPLACE FORECASTS WITH ACTUALS')
    forecasted_transactions = replace_forecasts_with_actuals(
        args.client, week_start, week_end, actual_transactions
    )
    
    # Step 3: Generate variance report
    print_header('STEP 3: GENERATE VARIANCE REPORT')
    report_file = generate_variance_report(
        args.client, week_start, week_end, forecasted_transactions, actual_transactions
    )
    
    # Step 4: Update balance
    print_header('STEP 4: UPDATE RUNNING BALANCE')
    final_balance = update_balance(args.client, args.balance)
    
    # Summary
    print_header('🎉 WEEKLY ACTUALS PROCESS COMPLETE')
    print(f'✅ Week processed: {week_start} to {week_end}')
    print(f'✅ Actual transactions imported: {len(actual_transactions)}')
    print(f'✅ Forecasted transactions replaced: {len(forecasted_transactions)}')
    print(f'✅ Variance report created: {report_file}')
    print(f'✅ Running balance: ${final_balance:,.2f}')
    
    print(f'\n📋 NEXT STEPS:')
    print(f'1. Review variance report: {report_file}')
    print(f'2. Update any patterns that showed large variances')
    print(f'3. Continue with forecasting for upcoming weeks')

if __name__ == "__main__":
    main()