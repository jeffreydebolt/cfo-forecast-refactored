"""
Analyze recent trends to see if there are any emerging patterns
that might explain the user's higher forecast numbers.
"""

from supabase_client import supabase
from datetime import datetime, date, timedelta
import pandas as pd

def recent_trends_analysis():
    """Analyze recent trends in transaction data."""
    client_id = 'spyguy'
    
    try:
        print("🔍 RECENT TRENDS ANALYSIS")
        print("=" * 60)
        
        # Get all available transactions
        result = supabase.table('transactions') \
            .select('transaction_date, vendor_name, amount, description') \
            .eq('client_id', client_id) \
            .order('transaction_date', desc=True) \
            .execute()
        
        if not result.data:
            print(f"❌ No transactions found")
            return None
        
        transactions = result.data
        df = pd.DataFrame(transactions)
        df['transaction_date'] = pd.to_datetime(df['transaction_date'])
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
        
        # Filter for income only
        income_df = df[df['amount'] > 0].copy()
        
        print(f"✅ Found {len(income_df)} income transactions")
        print(f"📅 Full date range: {income_df['transaction_date'].min().strftime('%Y-%m-%d')} to {income_df['transaction_date'].max().strftime('%Y-%m-%d')}")
        
        # Analyze by month to see trends
        income_df['month'] = income_df['transaction_date'].dt.to_period('M')
        monthly_totals = income_df.groupby('month')['amount'].sum().reset_index()
        monthly_totals = monthly_totals.sort_values('month')
        
        print(f"\n📊 MONTHLY INCOME TRENDS:")
        print("-" * 40)
        for _, month_data in monthly_totals.iterrows():
            # Convert to weekly average for that month
            days_in_month = month_data['month'].days_in_month
            weekly_avg = month_data['amount'] / (days_in_month / 7)
            print(f"{month_data['month']}: ${month_data['amount']:>10,.2f} (${weekly_avg:>8,.2f}/wk)")
        
        # Focus on most recent weeks
        last_30_days = income_df[income_df['transaction_date'] >= (datetime.now() - timedelta(days=30))]
        last_60_days = income_df[income_df['transaction_date'] >= (datetime.now() - timedelta(days=60))]
        
        if len(last_30_days) > 0:
            recent_weekly_avg = last_30_days['amount'].sum() / (30/7)
            print(f"\n🔥 LAST 30 DAYS: ${last_30_days['amount'].sum():,.2f} (${recent_weekly_avg:,.2f}/wk)")
        
        if len(last_60_days) > 0:
            recent_60_weekly_avg = last_60_days['amount'].sum() / (60/7)
            print(f"🔥 LAST 60 DAYS: ${last_60_days['amount'].sum():,.2f} (${recent_60_weekly_avg:,.2f}/wk)")
        
        # Check for any very recent large transactions that might indicate new patterns
        print(f"\n🔍 RECENT LARGE TRANSACTIONS (>$5,000):")
        print("-" * 50)
        
        recent_large = income_df[
            (income_df['transaction_date'] >= (datetime.now() - timedelta(days=60))) &
            (income_df['amount'] >= 5000)
        ].sort_values('transaction_date', ascending=False)
        
        if len(recent_large) > 0:
            for _, txn in recent_large.iterrows():
                print(f"{txn['transaction_date'].strftime('%Y-%m-%d')} | ${txn['amount']:>10,.2f} | {txn['vendor_name']}")
        else:
            print("No transactions >$5,000 in last 60 days")
        
        # Analyze weekly patterns in recent data
        print(f"\n📈 WEEKLY BREAKDOWN (Last 8 weeks):")
        print("-" * 50)
        
        # Group by week
        income_df['week_start'] = income_df['transaction_date'].dt.to_period('W').dt.start_time
        weekly_totals = income_df.groupby('week_start')['amount'].sum().reset_index()
        weekly_totals = weekly_totals.sort_values('week_start', ascending=False)
        
        for i, (_, week) in enumerate(weekly_totals.head(8).iterrows()):
            week_end = week['week_start'] + timedelta(days=6)
            print(f"Week {i+1}: {week['week_start'].strftime('%m/%d')} - {week_end.strftime('%m/%d')} | ${week['amount']:>10,.2f}")
        
        # Check if there are any patterns that show growth
        recent_weeks = weekly_totals.head(4)['amount'].tolist()
        older_weeks = weekly_totals.iloc[4:8]['amount'].tolist()
        
        if len(recent_weeks) >= 4 and len(older_weeks) >= 4:
            recent_avg = sum(recent_weeks) / len(recent_weeks)
            older_avg = sum(older_weeks) / len(older_weeks)
            growth_rate = (recent_avg - older_avg) / older_avg * 100
            
            print(f"\n📊 GROWTH ANALYSIS:")
            print(f"Recent 4 weeks average: ${recent_avg:,.2f}")
            print(f"Previous 4 weeks average: ${older_avg:,.2f}")
            print(f"Growth rate: {growth_rate:+.1f}%")
            
            if growth_rate > 20:
                print(f"🚀 Strong growth trend detected! This might explain higher forecasts.")
            elif growth_rate > 5:
                print(f"📈 Moderate growth trend detected.")
            else:
                print(f"📊 Relatively stable pattern.")
        
        # Check for any missing data or gaps
        print(f"\n🔍 DATA COMPLETENESS CHECK:")
        print("-" * 40)
        
        # Check for gaps in dates
        date_range = pd.date_range(
            start=income_df['transaction_date'].min(),
            end=income_df['transaction_date'].max(),
            freq='D'
        )
        
        dates_with_transactions = set(income_df['transaction_date'].dt.date)
        total_days = len(date_range)
        days_with_transactions = len(dates_with_transactions)
        
        print(f"Total days in range: {total_days}")
        print(f"Days with transactions: {days_with_transactions}")
        print(f"Coverage: {days_with_transactions/total_days*100:.1f}%")
        
        # Check for recent data
        most_recent_date = income_df['transaction_date'].max().date()
        days_since_last = (datetime.now().date() - most_recent_date).days
        
        print(f"Most recent transaction: {most_recent_date}")
        print(f"Days since last transaction: {days_since_last}")
        
        if days_since_last > 7:
            print(f"⚠️  Warning: No transactions in last {days_since_last} days - data might not be current")
        
        return {
            'monthly_totals': monthly_totals.to_dict('records'),
            'weekly_totals': weekly_totals.head(8).to_dict('records'),
            'recent_trends': {
                'last_30_days': recent_weekly_avg if len(last_30_days) > 0 else 0,
                'last_60_days': recent_60_weekly_avg if len(last_60_days) > 0 else 0,
                'growth_rate': growth_rate if 'growth_rate' in locals() else 0
            }
        }
        
    except Exception as e:
        print(f"❌ Error in recent trends analysis: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    recent_trends_analysis()