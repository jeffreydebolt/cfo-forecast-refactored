"""
Analyze SGE (possibly Amazon-related) transaction patterns to understand
if these are the large deposits the user is forecasting.
"""

from supabase_client import supabase
from datetime import datetime, date, timedelta
import pandas as pd

def analyze_sge_patterns():
    """Analyze SGE transaction patterns."""
    client_id = 'spyguy'
    
    try:
        print("🔍 ANALYZING SGE TRANSACTION PATTERNS")
        print("=" * 60)
        
        # Get all transactions for the last 6 months
        six_months_ago = (datetime.now() - timedelta(days=180)).date()
        
        result = supabase.table('transactions') \
            .select('transaction_date, vendor_name, amount, description') \
            .eq('client_id', client_id) \
            .gte('transaction_date', six_months_ago.isoformat()) \
            .order('transaction_date', desc=True) \
            .execute()
        
        if not result.data:
            print(f"❌ No transactions found")
            return None
        
        transactions = result.data
        df = pd.DataFrame(transactions)
        df['transaction_date'] = pd.to_datetime(df['transaction_date'])
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
        
        # Search for SGE transactions
        sge_transactions = df[
            df['vendor_name'].str.contains('SGE', case=False, na=False) |
            df['description'].str.contains('SGE', case=False, na=False)
        ].copy()
        
        print(f"✅ Found {len(sge_transactions)} SGE transactions")
        
        if len(sge_transactions) == 0:
            return None
        
        # Separate income and expenses
        sge_income = sge_transactions[sge_transactions['amount'] > 0].copy()
        sge_expenses = sge_transactions[sge_transactions['amount'] < 0].copy()
        
        print(f"💰 SGE Income transactions: {len(sge_income)}")
        print(f"💸 SGE Expense transactions: {len(sge_expenses)}")
        
        # Analyze income patterns
        if len(sge_income) > 0:
            print(f"\n📊 SGE INCOME ANALYSIS:")
            print("-" * 40)
            
            sge_income = sge_income.sort_values('transaction_date')
            
            print(f"💰 Total SGE income: ${sge_income['amount'].sum():,.2f}")
            print(f"📈 Average per transaction: ${sge_income['amount'].mean():,.2f}")
            print(f"📅 Date range: {sge_income['transaction_date'].min().strftime('%Y-%m-%d')} to {sge_income['transaction_date'].max().strftime('%Y-%m-%d')}")
            
            print(f"\n🔍 All SGE Income transactions:")
            for _, txn in sge_income.iterrows():
                print(f"  {txn['transaction_date'].strftime('%Y-%m-%d')} | ${txn['amount']:>10,.2f} | {txn['vendor_name']}")
                if txn['description'] and txn['description'] != txn['vendor_name']:
                    print(f"    Description: {txn['description']}")
            
            # Analyze intervals
            if len(sge_income) > 1:
                sge_income['days_between'] = sge_income['transaction_date'].diff().dt.days
                intervals = sge_income['days_between'].dropna()
                
                print(f"\n📊 Intervals between SGE income transactions:")
                for i, (_, txn) in enumerate(sge_income.iterrows()):
                    if pd.notna(txn['days_between']):
                        print(f"  Transaction {i+1}: {txn['days_between']:.0f} days after previous")
                
                if len(intervals) > 0:
                    avg_interval = intervals.mean()
                    print(f"\n📈 Average interval: {avg_interval:.1f} days")
                    
                    # Check for patterns
                    weekly_count = sum(1 for x in intervals if 5 <= x <= 9)
                    biweekly_count = sum(1 for x in intervals if 12 <= x <= 16)
                    monthly_count = sum(1 for x in intervals if 25 <= x <= 35)
                    
                    print(f"📊 Pattern analysis:")
                    print(f"  Weekly pattern (5-9 days): {weekly_count}/{len(intervals)} transactions")
                    print(f"  Bi-weekly pattern (12-16 days): {biweekly_count}/{len(intervals)} transactions")
                    print(f"  Monthly pattern (25-35 days): {monthly_count}/{len(intervals)} transactions")
                    
                    if biweekly_count > 0:
                        print(f"  ✅ Bi-weekly pattern detected!")
            
            # Check if these could be the $44k Amazon deposits
            print(f"\n🎯 COMPARISON WITH FORECAST:")
            print("-" * 40)
            print(f"User's forecast: $44,777 bi-weekly from 'Amazon L'")
            
            # Calculate what the SGE pattern would be
            weeks_span = (sge_income['transaction_date'].max() - sge_income['transaction_date'].min()).days / 7
            if weeks_span > 0:
                weekly_avg = sge_income['amount'].sum() / weeks_span
                biweekly_projection = weekly_avg * 2
                
                print(f"SGE actual weekly average: ${weekly_avg:,.2f}")
                print(f"SGE bi-weekly projection: ${biweekly_projection:,.2f}")
                print(f"Forecast vs SGE ratio: {44777 / biweekly_projection:.2f}x")
                
                # Recent trend
                recent_sge = sge_income.tail(3)
                if len(recent_sge) > 0:
                    recent_avg = recent_sge['amount'].mean()
                    print(f"Recent SGE average: ${recent_avg:,.2f}")
        
        # Analyze expense patterns too
        if len(sge_expenses) > 0:
            print(f"\n📊 SGE EXPENSE ANALYSIS:")
            print("-" * 40)
            
            sge_expenses = sge_expenses.sort_values('transaction_date')
            
            print(f"💸 Total SGE expenses: ${abs(sge_expenses['amount'].sum()):,.2f}")
            print(f"📉 Average per transaction: ${abs(sge_expenses['amount'].mean()):,.2f}")
            
            print(f"\n🔍 All SGE Expense transactions:")
            for _, txn in sge_expenses.iterrows():
                print(f"  {txn['transaction_date'].strftime('%Y-%m-%d')} | ${abs(txn['amount']):>10,.2f} | {txn['vendor_name']}")
                if txn['description'] and txn['description'] != txn['vendor_name']:
                    print(f"    Description: {txn['description']}")
        
        return sge_transactions
        
    except Exception as e:
        print(f"❌ Error analyzing SGE patterns: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    analyze_sge_patterns()