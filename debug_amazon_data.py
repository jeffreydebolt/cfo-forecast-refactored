#!/usr/bin/env python3
"""
Debug Amazon transaction data to understand the actual pattern.
"""

import sys
sys.path.append('.')

from lean_forecasting.group_pattern_detector import group_pattern_detector
import pandas as pd

def debug_amazon_transactions():
    """Look at actual Amazon transaction data."""
    print("🔍 DEBUGGING AMAZON TRANSACTION DATA")
    print("=" * 60)
    
    client_id = 'bestself'
    amazon_display_names = ['Amazon Revenue']
    
    # Get transactions
    transactions = group_pattern_detector.get_vendor_group_transactions(
        client_id, 'Amazon', amazon_display_names, days_back=90
    )
    
    if not transactions:
        print("❌ No transactions found")
        return
    
    # Convert to DataFrame for analysis
    df = pd.DataFrame(transactions)
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])
    df['amount'] = df['amount'].astype(float)
    
    print(f"Total transactions: {len(transactions)}")
    print(f"Date range: {df['transaction_date'].min().date()} to {df['transaction_date'].max().date()}")
    print(f"Total amount: ${df['amount'].sum():,.2f}")
    
    # Show all transactions sorted by date
    print(f"\n📅 ALL AMAZON TRANSACTIONS (sorted by date):")
    df_sorted = df.sort_values('transaction_date')
    
    for _, row in df_sorted.iterrows():
        date_obj = row['transaction_date']
        day_name = date_obj.strftime('%A')
        print(f"{date_obj.date()} ({day_name}): ${row['amount']:,.2f} - {row['vendor_name']}")
    
    # Group by date to see daily totals
    print(f"\n📊 DAILY TOTALS (grouped by date):")
    daily_totals = df.groupby(df['transaction_date'].dt.date)['amount'].sum().reset_index()
    daily_totals['transaction_date'] = pd.to_datetime(daily_totals['transaction_date'])
    daily_totals = daily_totals.sort_values('transaction_date')
    
    for _, row in daily_totals.iterrows():
        date_obj = row['transaction_date']
        day_name = date_obj.strftime('%A')
        print(f"{date_obj.date()} ({day_name}): ${row['amount']:,.2f}")
    
    # Calculate gaps between transactions
    print(f"\n⏱️  GAPS BETWEEN TRANSACTION DATES:")
    dates = daily_totals['transaction_date'].dt.date.tolist()
    
    for i in range(1, len(dates)):
        gap = (dates[i] - dates[i-1]).days
        prev_day = pd.to_datetime(dates[i-1]).strftime('%A')
        curr_day = pd.to_datetime(dates[i]).strftime('%A')
        print(f"{dates[i-1]} ({prev_day}) → {dates[i]} ({curr_day}): {gap} days")
    
    # Look for large transactions (potential deposits)
    print(f"\n💰 LARGE TRANSACTIONS (>$10k):")
    large_txns = df[df['amount'] > 10000].sort_values('transaction_date')
    
    for _, row in large_txns.iterrows():
        date_obj = row['transaction_date']
        day_name = date_obj.strftime('%A')
        print(f"{date_obj.date()} ({day_name}): ${row['amount']:,.2f} - {row['vendor_name']}")
    
    # Calculate gaps between large transactions
    if len(large_txns) > 1:
        print(f"\n⏱️  GAPS BETWEEN LARGE TRANSACTIONS:")
        large_dates = large_txns['transaction_date'].dt.date.tolist()
        
        for i in range(1, len(large_dates)):
            gap = (large_dates[i] - large_dates[i-1]).days
            prev_day = pd.to_datetime(large_dates[i-1]).strftime('%A')
            curr_day = pd.to_datetime(large_dates[i]).strftime('%A')
            print(f"{large_dates[i-1]} ({prev_day}) → {large_dates[i]} ({curr_day}): {gap} days")

if __name__ == "__main__":
    debug_amazon_transactions()