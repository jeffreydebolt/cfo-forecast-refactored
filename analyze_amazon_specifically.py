#!/usr/bin/env python3
"""
Analyze Amazon Revenue specifically for BestSelf to see actual patterns.
"""

import sys
sys.path.append('.')

from lean_forecasting.temp_vendor_groups import temp_vendor_group_manager
from datetime import datetime, date, timedelta
import pandas as pd

def analyze_amazon_only():
    """Analyze just Amazon Revenue for BestSelf."""
    print("🔍 ANALYZING AMAZON REVENUE ONLY")
    print("=" * 60)
    
    client_id = 'bestself'
    
    # Get Amazon Revenue transactions specifically
    amazon_transactions = temp_vendor_group_manager.get_vendor_group_transactions(
        client_id, ['Amazon Revenue'], 90
    )
    
    print(f"Found {len(amazon_transactions)} Amazon Revenue transactions in last 90 days")
    
    if not amazon_transactions:
        print("❌ No Amazon Revenue transactions found")
        return
    
    # Convert to DataFrame for analysis
    df = pd.DataFrame(amazon_transactions)
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])
    df['amount'] = df['amount'].astype(float)
    
    print(f"\nDATE RANGE: {df['transaction_date'].min().date()} to {df['transaction_date'].max().date()}")
    print(f"TOTAL AMAZON REVENUE: ${df['amount'].sum():,.2f}")
    print(f"AVERAGE PER TRANSACTION: ${df['amount'].mean():.2f}")
    
    # Show recent transactions
    print(f"\n📊 RECENT AMAZON TRANSACTIONS:")
    recent = df.head(10).sort_values('transaction_date', ascending=False)
    for _, row in recent.iterrows():
        print(f"{row['transaction_date'].date()}: ${row['amount']:,.2f} - {row['vendor_name']}")
    
    # Show daily totals for last 2 weeks
    print(f"\n📅 DAILY AMAZON TOTALS (LAST 14 DAYS):")
    last_14_days = df[df['transaction_date'] >= df['transaction_date'].max() - pd.Timedelta(days=14)]
    daily_totals = last_14_days.groupby(last_14_days['transaction_date'].dt.date)['amount'].sum().sort_index(ascending=False)
    
    for date_val, amount in daily_totals.items():
        day_name = pd.to_datetime(date_val).strftime('%A')
        print(f"{date_val} ({day_name}): ${amount:,.2f}")
    
    # Pattern analysis
    df['day_of_week'] = df['transaction_date'].dt.dayofweek + 1  # 1=Monday
    dow_totals = df.groupby('day_of_week')['amount'].agg(['count', 'sum', 'mean'])
    
    print(f"\n📈 AMAZON REVENUE BY DAY OF WEEK:")
    day_names = {1: 'Monday', 2: 'Tuesday', 3: 'Wednesday', 4: 'Thursday', 
                5: 'Friday', 6: 'Saturday', 7: 'Sunday'}
    
    for dow, stats in dow_totals.iterrows():
        print(f"{day_names[dow]}: {stats['count']} transactions, ${stats['sum']:,.2f} total, ${stats['mean']:.2f} avg")
    
    return {
        'transaction_count': len(amazon_transactions),
        'total_amount': df['amount'].sum(),
        'avg_amount': df['amount'].mean(),
        'daily_avg': df['amount'].sum() / 90,  # Daily average over 90 days
        'dow_analysis': dow_totals
    }

def analyze_all_revenue_streams():
    """Analyze each revenue stream separately."""
    print("\n🔍 ANALYZING ALL REVENUE STREAMS SEPARATELY")
    print("=" * 60)
    
    client_id = 'bestself'
    revenue_streams = ['Amazon Revenue', 'BestSelf Revenue', 'Faire Revenue', 
                      'PayPal Revenue', 'Shopify Revenue', 'Stripe Revenue', 'TikTok Revenue']
    
    stream_analysis = {}
    
    for stream in revenue_streams:
        transactions = temp_vendor_group_manager.get_vendor_group_transactions(
            client_id, [stream], 90
        )
        
        if transactions:
            df = pd.DataFrame(transactions)
            df['amount'] = df['amount'].astype(float)
            total = df['amount'].sum()
            count = len(transactions)
            avg = df['amount'].mean()
            
            stream_analysis[stream] = {
                'total': total,
                'count': count,
                'avg': avg,
                'daily_avg': total / 90
            }
            
            print(f"{stream}: {count} txns, ${total:,.2f} total, ${avg:.2f} avg, ${total/90:.2f}/day")
        else:
            print(f"{stream}: No transactions found")
            stream_analysis[stream] = {'total': 0, 'count': 0, 'avg': 0, 'daily_avg': 0}
    
    return stream_analysis

def main():
    """Main analysis function."""
    try:
        # Analyze Amazon specifically
        amazon_analysis = analyze_amazon_only()
        
        # Analyze all streams
        all_streams = analyze_all_revenue_streams()
        
        print(f"\n📊 SUMMARY FOR WEEK OF 8/4/25 FORECAST:")
        print("=" * 60)
        
        print(f"If Amazon follows its pattern:")
        if amazon_analysis:
            amazon_daily = amazon_analysis['daily_avg']
            amazon_weekly = amazon_daily * 5  # M-F
            print(f"  Amazon Revenue: ${amazon_weekly:.2f} (${amazon_daily:.2f}/day × 5 weekdays)")
        
        print(f"\nAll revenue streams combined:")
        total_daily = sum(stream['daily_avg'] for stream in all_streams.values())
        total_weekly = total_daily * 5
        print(f"  Total Revenue: ${total_weekly:.2f} (${total_daily:.2f}/day × 5 weekdays)")
        
        print(f"\nBreakdown by stream (5-day week):")
        for stream, data in all_streams.items():
            if data['daily_avg'] > 0:
                weekly = data['daily_avg'] * 5
                print(f"  {stream}: ${weekly:.2f}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()