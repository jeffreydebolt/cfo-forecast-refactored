#!/usr/bin/env python3
"""
Analyze Amazon transaction timing to fix the Monday vs Tuesday issue.
"""

import sys
sys.path.append('.')

from supabase_client import supabase
from datetime import datetime, date
import pandas as pd

def analyze_amazon_transactions():
    """Deep dive into Amazon transaction timing."""
    print("🔍 ANALYZING AMAZON TRANSACTION TIMING")
    print("=" * 60)
    
    client_id = 'bestself'
    
    try:
        # Get all Amazon transactions
        result = supabase.table('vendors').select('vendor_name').eq(
            'client_id', client_id
        ).eq(
            'display_name', 'Amazon Revenue'
        ).execute()
        
        if not result.data:
            print("❌ No Amazon vendors found")
            return
        
        vendor_names = [v['vendor_name'] for v in result.data]
        print(f"📊 Found {len(vendor_names)} Amazon vendor names")
        
        # Get all transactions for these vendors
        txn_result = supabase.table('transactions').select(
            'transaction_date, amount, vendor_name'
        ).eq(
            'client_id', client_id
        ).in_(
            'vendor_name', vendor_names
        ).execute()
        
        if not txn_result.data:
            print("❌ No Amazon transactions found")
            return
        
        print(f"📊 Found {len(txn_result.data)} Amazon transactions")
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(txn_result.data)
        df['transaction_date'] = pd.to_datetime(df['transaction_date'])
        df['amount'] = df['amount'].astype(float)
        df['weekday'] = df['transaction_date'].dt.day_name()
        df['weekday_num'] = df['transaction_date'].dt.weekday  # 0=Monday, 1=Tuesday, etc.
        
        # Focus on large transactions (likely the main deposits)
        large_txns = df[df['amount'] >= 10000.0].copy()
        large_txns = large_txns.sort_values('transaction_date')
        
        print(f"\n💰 LARGE AMAZON TRANSACTIONS (>=$10k):")
        print(f"Found {len(large_txns)} large transactions")
        
        for _, txn in large_txns.iterrows():
            weekday = txn['weekday']
            date_str = txn['transaction_date'].strftime('%Y-%m-%d')
            amount = txn['amount']
            print(f"  {date_str} ({weekday}): ${amount:,.2f}")
        
        # Analyze weekday patterns
        if len(large_txns) > 0:
            weekday_counts = large_txns['weekday'].value_counts()
            weekday_num_counts = large_txns['weekday_num'].value_counts()
            
            print(f"\n📊 WEEKDAY DISTRIBUTION:")
            for weekday, count in weekday_counts.items():
                percentage = (count / len(large_txns)) * 100
                print(f"  {weekday}: {count} transactions ({percentage:.1f}%)")
            
            most_common_weekday = weekday_counts.index[0]
            most_common_count = weekday_counts.iloc[0]
            
            print(f"\n🎯 MOST COMMON DAY: {most_common_weekday} ({most_common_count}/{len(large_txns)} transactions)")
            
            # Check if there's a pattern issue
            if most_common_weekday == 'Tuesday':
                print(f"\n🤔 INVESTIGATION: Why Tuesday instead of Monday?")
                
                # Check if these are actually Monday deposits processed on Tuesday
                print(f"\nLet's check ALL Amazon transactions by weekday:")
                all_weekday_counts = df['weekday'].value_counts()
                for weekday, count in all_weekday_counts.items():
                    avg_amount = df[df['weekday'] == weekday]['amount'].mean()
                    print(f"  {weekday}: {count} txns, avg ${avg_amount:,.2f}")
        
        # Check transaction gaps for bi-weekly pattern
        if len(large_txns) > 1:
            print(f"\n📅 TRANSACTION GAPS (days between large deposits):")
            gaps = []
            for i in range(1, len(large_txns)):
                prev_date = large_txns.iloc[i-1]['transaction_date']
                curr_date = large_txns.iloc[i]['transaction_date']
                gap = (curr_date - prev_date).days
                gaps.append(gap)
                print(f"  {prev_date.strftime('%Y-%m-%d')} → {curr_date.strftime('%Y-%m-%d')}: {gap} days")
            
            if gaps:
                avg_gap = sum(gaps) / len(gaps)
                most_common_gap = max(set(gaps), key=gaps.count)
                print(f"\n📊 Average gap: {avg_gap:.1f} days")
                print(f"📊 Most common gap: {most_common_gap} days")
                
                if most_common_gap == 14:
                    print("✅ Confirmed: 14-day bi-weekly pattern")
                elif 13 <= most_common_gap <= 15:
                    print(f"✅ Close to bi-weekly: {most_common_gap} days")
        
        return large_txns
        
    except Exception as e:
        print(f"❌ Error analyzing Amazon transactions: {e}")
        import traceback
        traceback.print_exc()
        return None

def suggest_timing_fix(large_txns):
    """Suggest how to fix the timing detection."""
    print(f"\n🔧 TIMING DETECTION FIX SUGGESTIONS")
    print("=" * 50)
    
    if large_txns is None or len(large_txns) == 0:
        print("❌ No data to analyze")
        return
    
    weekday_counts = large_txns['weekday_num'].value_counts()
    most_common_weekday_num = weekday_counts.index[0]
    
    weekday_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    detected_day = weekday_names[most_common_weekday_num]
    
    print(f"Current detection: {detected_day}")
    print(f"User expectation: Monday")
    
    if most_common_weekday_num == 1:  # Tuesday
        print(f"\n💡 POSSIBLE EXPLANATIONS:")
        print(f"1. Amazon processes on Monday, deposits appear Tuesday")
        print(f"2. Bank processing delay (Monday → Tuesday)")
        print(f"3. Time zone differences in transaction recording")
        
        print(f"\n🔧 RECOMMENDED FIXES:")
        print(f"1. Add 'processing_delay' adjustment (-1 day for Amazon)")
        print(f"2. Allow user to override detected timing")
        print(f"3. Use Monday as forecast day even if deposits show Tuesday")
        
        return {
            'detected_day': detected_day,
            'user_expected_day': 'Monday',
            'recommended_forecast_day': 'Monday',
            'processing_delay': -1
        }
    
    return None

def main():
    """Main analysis function."""
    print("🚀 AMAZON TIMING ANALYSIS")
    print("=" * 70)
    
    large_txns = analyze_amazon_transactions()
    fix_suggestion = suggest_timing_fix(large_txns)
    
    if fix_suggestion:
        print(f"\n✅ ANALYSIS COMPLETE")
        print(f"Fix needed: {fix_suggestion}")
    else:
        print(f"\n❌ No clear timing issue found")

if __name__ == "__main__":
    main()