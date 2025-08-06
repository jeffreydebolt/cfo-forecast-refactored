"""
Analyze the specific week of July 21-27, 2025 for BestSelf transactions.
This script will be ready to run once the July 2025 data is imported.
"""

import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict
from supabase_client import supabase
from weekly_pivot_analysis import create_weekly_pivot_analysis, export_to_csv

def analyze_july_week_bestself():
    """
    Analyze the specific week of July 21-27, 2025 for BestSelf (spyguy client).
    Provides comprehensive analysis including:
    1. Date range verification
    2. Sample transactions
    3. Pivot table summary
    4. Deposits vs withdrawals by vendor
    """
    client_id = 'spyguy'  # BestSelf data is stored under spyguy client
    target_start = '2025-07-21'
    target_end = '2025-07-27'
    
    print("🎯 BESTSELF ANALYSIS: July 21-27, 2025")
    print("=" * 80)
    
    try:
        # Step 1: Check if we have data for this period
        print("Step 1: Checking data availability...")
        result = supabase.table('transactions') \
            .select('transaction_date, vendor_name, amount, description') \
            .eq('client_id', client_id) \
            .gte('transaction_date', target_start) \
            .lte('transaction_date', target_end) \
            .order('transaction_date') \
            .execute()
        
        if not result.data:
            print(f"❌ No transactions found for July 21-27, 2025")
            
            # Check what data we do have
            all_data_result = supabase.table('transactions') \
                .select('transaction_date') \
                .eq('client_id', client_id) \
                .order('transaction_date', desc=True) \
                .limit(1) \
                .execute()
            
            if all_data_result.data:
                latest_date = all_data_result.data[0]['transaction_date']
                print(f"ℹ️  Latest available data: {latest_date}")
                print(f"ℹ️  Target week starts: {target_start}")
                print(f"ℹ️  Data needs to be imported for July 2025")
            
            return None
        
        transactions = result.data
        print(f"✅ Found {len(transactions)} transactions for July 21-27, 2025")
        
        # Step 2: Show sample transactions
        print(f"\nStep 2: Sample transactions from July 21-27, 2025:")
        print("-" * 80)
        df = pd.DataFrame(transactions)
        df['transaction_date'] = pd.to_datetime(df['transaction_date'])
        df_sorted = df.sort_values(['transaction_date', 'amount'], ascending=[True, False])
        
        print(f"{'Date':<12} | {'Amount':>12} | {'Vendor':<30} | {'Description'}")
        print("-" * 80)
        
        for i, (_, txn) in enumerate(df_sorted.head(15).iterrows()):
            date_str = txn['transaction_date'].strftime('%Y-%m-%d')
            vendor = (txn['vendor_name'] or 'Unknown')[:30]
            description = (txn['description'] or '')[:40]
            print(f"{date_str} | ${txn['amount']:>11,.2f} | {vendor:<30} | {description}")
        
        if len(df_sorted) > 15:
            print(f"... and {len(df_sorted) - 15} more transactions")
        
        # Step 3: Run comprehensive pivot analysis
        print(f"\nStep 3: Creating comprehensive pivot table analysis...")
        print("=" * 80)
        
        analysis = create_weekly_pivot_analysis(client_id, target_start, target_end)
        
        if analysis:
            # Step 4: Export detailed CSV
            filename = f"bestself_july_week_analysis_{target_start}_to_{target_end}.csv"
            export_to_csv(analysis, filename)
            
            # Step 5: Additional analysis - Deposits vs Withdrawals by Vendor
            print(f"\nStep 4: Deposits vs Withdrawals Summary by Vendor:")
            print("=" * 80)
            
            vendor_summary = defaultdict(lambda: {'deposits': 0, 'withdrawals': 0, 'net': 0, 'count': 0})
            
            for txn in transactions:
                vendor = txn.get('vendor_name', 'Unknown')
                amount = float(txn['amount'])
                
                vendor_summary[vendor]['count'] += 1
                vendor_summary[vendor]['net'] += amount
                
                if amount > 0:
                    vendor_summary[vendor]['deposits'] += amount
                else:
                    vendor_summary[vendor]['withdrawals'] += abs(amount)
            
            # Sort by total activity (deposits + withdrawals)
            sorted_vendors = sorted(
                vendor_summary.items(),
                key=lambda x: x[1]['deposits'] + x[1]['withdrawals'],
                reverse=True
            )
            
            print(f"{'Vendor':<25} | {'Deposits':>12} | {'Withdrawals':>12} | {'Net':>12} | {'Count':>6}")
            print("-" * 80)
            
            total_deposits = 0
            total_withdrawals = 0
            total_transactions = 0
            
            for vendor, data in sorted_vendors:
                if data['deposits'] + data['withdrawals'] > 1:  # Only show significant activity
                    vendor_short = vendor[:24]
                    print(f"{vendor_short:<25} | ${data['deposits']:>11,.2f} | ${data['withdrawals']:>11,.2f} | ${data['net']:>11,.2f} | {data['count']:>6}")
                    
                    total_deposits += data['deposits']
                    total_withdrawals += data['withdrawals']
                    total_transactions += data['count']
            
            print("-" * 80)
            net_total = total_deposits - total_withdrawals
            print(f"{'TOTALS':<25} | ${total_deposits:>11,.2f} | ${total_withdrawals:>11,.2f} | ${net_total:>11,.2f} | {total_transactions:>6}")
            
            # Step 6: Week summary
            print(f"\nStep 5: Week Summary:")
            print("=" * 40)
            print(f"Analysis Period:     {target_start} to {target_end}")
            print(f"Total Transactions:  {len(transactions)}")
            print(f"Unique Vendors:      {len([v for v, d in vendor_summary.items() if d['count'] > 0])}")
            print(f"Total Deposits:      ${total_deposits:,.2f}")
            print(f"Total Withdrawals:   ${total_withdrawals:,.2f}")
            print(f"Net Cash Flow:       ${net_total:,.2f}")
            
            # Calculate daily averages
            print(f"Daily Average Flow:  ${net_total/7:,.2f}")
            
            return {
                'transactions': transactions,
                'vendor_summary': dict(vendor_summary),
                'totals': {
                    'deposits': total_deposits,
                    'withdrawals': total_withdrawals,
                    'net': net_total,
                    'count': len(transactions)
                }
            }
        
    except Exception as e:
        print(f"❌ Error analyzing July week: {e}")
        return None

def check_data_availability():
    """Check if July 2025 data is available yet."""
    try:
        result = supabase.table('transactions') \
            .select('transaction_date') \
            .eq('client_id', 'spyguy') \
            .gte('transaction_date', '2025-07-01') \
            .lte('transaction_date', '2025-07-31') \
            .limit(1) \
            .execute()
        
        if result.data:
            print("✅ July 2025 data is available!")
            return True
        else:
            print("❌ July 2025 data not yet available")
            
            # Show latest available date
            latest_result = supabase.table('transactions') \
                .select('transaction_date') \
                .eq('client_id', 'spyguy') \
                .order('transaction_date', desc=True) \
                .limit(1) \
                .execute()
            
            if latest_result.data:
                latest_date = latest_result.data[0]['transaction_date']
                print(f"Latest available data: {latest_date}")
            
            return False
    
    except Exception as e:
        print(f"Error checking data availability: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Checking if July 2025 data is available...")
    
    if check_data_availability():
        print("\n" + "="*80)
        analyze_july_week_bestself()
    else:
        print("\n💡 This script is ready to run once July 2025 data is imported.")
        print("   The analysis will include:")
        print("   • Date range verification")
        print("   • Sample transactions display")
        print("   • Comprehensive pivot table")
        print("   • Deposits vs withdrawals by vendor")
        print("   • Export to CSV for further analysis")