"""
Search for Amazon-related transactions more broadly to understand 
the $44k bi-weekly Amazon deposits the user mentioned.
"""

from supabase_client import supabase
from datetime import datetime, date, timedelta
import pandas as pd
import re

def search_amazon_patterns():
    """Search for all possible Amazon-related transactions."""
    client_id = 'spyguy'
    
    try:
        print("🔍 SEARCHING FOR AMAZON-RELATED TRANSACTIONS")
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
        
        # Filter for positive amounts (income only)
        income_df = df[df['amount'] > 0].copy()
        
        print(f"✅ Found {len(income_df)} income transactions to search")
        
        # Search for Amazon-like patterns in vendor names and descriptions
        amazon_keywords = [
            'amazon', 'amzn', 'amz', 'aws', 'kindle', 'audible', 
            'whole foods', 'twitch', 'a9', 'alexa', 'prime'
        ]
        
        print(f"\n🔍 Searching for keywords: {', '.join(amazon_keywords)}")
        
        # Create a comprehensive search
        amazon_pattern = '|'.join([f'\\b{keyword}' for keyword in amazon_keywords])
        
        # Search in both vendor_name and description
        potential_amazon = income_df[
            income_df['vendor_name'].str.contains(amazon_pattern, case=False, na=False, regex=True) |
            income_df['description'].str.contains(amazon_pattern, case=False, na=False, regex=True)
        ].copy()
        
        print(f"\n✅ Found {len(potential_amazon)} potential Amazon transactions")
        
        if len(potential_amazon) > 0:
            # Sort by amount descending to find large deposits
            potential_amazon = potential_amazon.sort_values('amount', ascending=False)
            
            print(f"\n💰 Top 20 Amazon-related transactions by amount:")
            for i, (_, txn) in enumerate(potential_amazon.head(20).iterrows()):
                print(f"  {i+1:2d}. {txn['transaction_date'].strftime('%Y-%m-%d')} | ${txn['amount']:>10,.2f} | {txn['vendor_name'][:30]}")
                if txn['description'] and txn['description'] != txn['vendor_name']:
                    print(f"      Description: {txn['description'][:60]}")
            
            # Look for large transactions ($40k+) that could be the bi-weekly deposits
            large_amazon = potential_amazon[potential_amazon['amount'] >= 40000]
            
            if len(large_amazon) > 0:
                print(f"\n🎯 LARGE AMAZON TRANSACTIONS ($40k+): {len(large_amazon)} found")
                print("-" * 60)
                
                for _, txn in large_amazon.iterrows():
                    print(f"💰 ${txn['amount']:,.2f} on {txn['transaction_date'].strftime('%Y-%m-%d')}")
                    print(f"   Vendor: {txn['vendor_name']}")
                    if txn['description']:
                        print(f"   Description: {txn['description']}")
                    print()
                
                # Analyze intervals between large transactions
                if len(large_amazon) > 1:
                    large_amazon_sorted = large_amazon.sort_values('transaction_date')
                    large_amazon_sorted['days_between'] = large_amazon_sorted['transaction_date'].diff().dt.days
                    
                    intervals = large_amazon_sorted['days_between'].dropna()
                    print(f"📊 Intervals between large Amazon transactions:")
                    for interval in intervals:
                        print(f"   {interval} days")
                    
                    if len(intervals) > 0:
                        avg_interval = intervals.mean()
                        print(f"   Average: {avg_interval:.1f} days")
                        
                        if 12 <= avg_interval <= 16:
                            print(f"   ✅ This matches a bi-weekly pattern!")
            else:
                print(f"\n❌ No large Amazon transactions ($40k+) found")
                
                # Show largest Amazon transactions found
                if len(potential_amazon) > 0:
                    max_amount = potential_amazon['amount'].max()
                    print(f"   📊 Largest Amazon transaction found: ${max_amount:,.2f}")
        
        # Also search for very large transactions regardless of vendor
        print(f"\n🔍 SEARCHING FOR VERY LARGE TRANSACTIONS (any vendor)")
        print("-" * 60)
        
        large_transactions = income_df[income_df['amount'] >= 30000].sort_values('amount', ascending=False)
        
        if len(large_transactions) > 0:
            print(f"✅ Found {len(large_transactions)} transactions >= $30k:")
            
            for _, txn in large_transactions.iterrows():
                print(f"💰 ${txn['amount']:,.2f} on {txn['transaction_date'].strftime('%Y-%m-%d')} | {txn['vendor_name']}")
                if txn['description'] and txn['description'] != txn['vendor_name']:
                    print(f"   Description: {txn['description']}")
        else:
            print(f"❌ No transactions >= $30k found")
            
            # Show largest transactions overall
            largest = income_df.nlargest(10, 'amount')
            print(f"\n📊 Top 10 largest transactions overall:")
            for i, (_, txn) in enumerate(largest.iterrows()):
                print(f"  {i+1:2d}. ${txn['amount']:>8,.2f} | {txn['transaction_date'].strftime('%Y-%m-%d')} | {txn['vendor_name'][:40]}")
        
        return potential_amazon
        
    except Exception as e:
        print(f"❌ Error searching patterns: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    search_amazon_patterns()