"""
Check BestSelf transaction data, specifically looking for July 21-27, 2025.
"""

from supabase_client import supabase
from datetime import datetime, date
import pandas as pd

def check_bestself_transactions():
    """Check BestSelf transactions and look for July 2025 data."""
    client_id = 'spyguy'  # Transactions are stored under spyguy client ID
    
    try:
        print(f"🔍 Checking transactions for client: {client_id}")
        print("=" * 60)
        
        # Get all transactions for BestSelf
        result = supabase.table('transactions') \
            .select('transaction_date, vendor_name, amount, description') \
            .eq('client_id', client_id) \
            .order('transaction_date', desc=True) \
            .execute()
        
        if not result.data:
            print(f"❌ No transactions found for client: {client_id}")
            return None
        
        transactions = result.data
        print(f"✅ Found {len(transactions)} transactions for client: {client_id}")
        
        # Convert to DataFrame for easier analysis
        df = pd.DataFrame(transactions)
        df['transaction_date'] = pd.to_datetime(df['transaction_date'])
        
        # Show overall date range
        min_date = df['transaction_date'].min()
        max_date = df['transaction_date'].max()
        print(f"\n📅 Overall date range: {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}")
        
        # Show most recent transactions
        print(f"\n🔝 Most recent 10 transactions:")
        recent_transactions = df.head(10)
        for _, txn in recent_transactions.iterrows():
            print(f"  {txn['transaction_date'].strftime('%Y-%m-%d')} | ${txn['amount']:>10,.2f} | {txn['vendor_name'][:40]}")
        
        # Check for July 2025 data
        july_2025 = df[df['transaction_date'].dt.strftime('%Y-%m') == '2025-07']
        
        if len(july_2025) > 0:
            print(f"\n🎯 July 2025 transactions found: {len(july_2025)}")
            
            # Show all July 2025 transactions
            print(f"\n📊 All July 2025 transactions:")
            for _, txn in july_2025.sort_values('transaction_date').iterrows():
                print(f"  {txn['transaction_date'].strftime('%Y-%m-%d')} | ${txn['amount']:>10,.2f} | {txn['vendor_name'][:40]}")
            
            # Check specifically for July 21-27, 2025
            target_week_start = datetime(2025, 7, 21).date()
            target_week_end = datetime(2025, 7, 27).date()
            
            week_transactions = july_2025[
                (july_2025['transaction_date'].dt.date >= target_week_start) & 
                (july_2025['transaction_date'].dt.date <= target_week_end)
            ]
            
            if len(week_transactions) > 0:
                print(f"\n🎯 Transactions for target week (July 21-27, 2025): {len(week_transactions)}")
                print("=" * 60)
                
                total_inflow = week_transactions[week_transactions['amount'] > 0]['amount'].sum()
                total_outflow = abs(week_transactions[week_transactions['amount'] < 0]['amount'].sum())
                net_flow = total_inflow - total_outflow
                
                print(f"💰 Week Summary:")
                print(f"  Total Inflow:  ${total_inflow:>10,.2f}")
                print(f"  Total Outflow: ${total_outflow:>10,.2f}")
                print(f"  Net Flow:      ${net_flow:>10,.2f}")
                print()
                
                print(f"📝 Detailed transactions for July 21-27, 2025:")
                for _, txn in week_transactions.sort_values('transaction_date').iterrows():
                    flow_type = "IN " if txn['amount'] > 0 else "OUT"
                    print(f"  {txn['transaction_date'].strftime('%Y-%m-%d')} | {flow_type} | ${abs(txn['amount']):>10,.2f} | {txn['vendor_name'][:40]}")
                    if txn['description'] and txn['description'] != txn['vendor_name']:
                        print(f"    Description: {txn['description'][:80]}")
                
                return week_transactions.to_dict('records')
            else:
                print(f"\n❌ No transactions found for the specific week: July 21-27, 2025")
                
                # Show what dates we do have in July 2025
                july_dates = sorted(july_2025['transaction_date'].dt.date.unique())
                print(f"\n📅 Available July 2025 dates:")
                for d in july_dates:
                    print(f"  {d}")
        else:
            print(f"\n❌ No July 2025 transactions found")
            
            # Show what months we do have data for
            months = df['transaction_date'].dt.strftime('%Y-%m').value_counts().sort_index()
            print(f"\n📅 Available months with transaction counts:")
            for month, count in months.items():
                print(f"  {month}: {count} transactions")
        
        return transactions
        
    except Exception as e:
        print(f"❌ Error checking transactions: {e}")
        return None

if __name__ == "__main__":
    check_bestself_transactions()