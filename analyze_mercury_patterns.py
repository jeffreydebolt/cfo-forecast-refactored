"""
Analyze Mercury transaction patterns for bestself client to understand 
how user arrived at manual forecast numbers.

Compares actual transaction data with user's forecast:
- Amazon L: $44,777 bi-weekly
- Shopify: $12,500 weekly  
- Amazon CA: $450-500 weekly
- Amazon: $684 weekly
- PayPal: $1,120-1,600 alternating
- Stripe: $100-600 weekly
- TikTok: $30-160 weekly
"""

from supabase_client import supabase
from datetime import datetime, date, timedelta
import pandas as pd
from collections import defaultdict
import re

def analyze_mercury_patterns():
    """Analyze Mercury transaction patterns for bestself client."""
    client_id = 'spyguy'  # Transactions are stored under spyguy client ID
    
    try:
        print("🔍 MERCURY TRANSACTION PATTERN ANALYSIS FOR BESTSELF CLIENT")
        print("=" * 80)
        
        # Get all transactions for the last 6 months
        six_months_ago = (datetime.now() - timedelta(days=180)).date()
        
        result = supabase.table('transactions') \
            .select('transaction_date, vendor_name, amount, description') \
            .eq('client_id', client_id) \
            .gte('transaction_date', six_months_ago.isoformat()) \
            .order('transaction_date', desc=True) \
            .execute()
        
        if not result.data:
            print(f"❌ No transactions found for client: {client_id}")
            return None
        
        transactions = result.data
        print(f"✅ Found {len(transactions)} transactions since {six_months_ago}")
        
        # Convert to DataFrame
        df = pd.DataFrame(transactions)
        df['transaction_date'] = pd.to_datetime(df['transaction_date'])
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
        
        # Filter for positive amounts (income only)
        income_df = df[df['amount'] > 0].copy()
        
        print(f"💰 Found {len(income_df)} income transactions")
        print(f"📅 Date range: {income_df['transaction_date'].min().strftime('%Y-%m-%d')} to {income_df['transaction_date'].max().strftime('%Y-%m-%d')}")
        
        # Analyze major vendors mentioned in forecast
        vendor_patterns = {
            'Amazon L': ['amazon', 'amzn'],
            'Shopify': ['shopify', 'shop'],
            'Amazon CA': ['amazon.ca', 'amazon ca'],
            'Amazon': ['amazon', 'amzn'],
            'PayPal': ['paypal', 'pp '],
            'Stripe': ['stripe'],
            'TikTok': ['tiktok', 'bytedance']
        }
        
        print("\n🎯 ANALYZING VENDOR PATTERNS")
        print("=" * 80)
        
        vendor_analysis = {}
        
        for forecast_vendor, keywords in vendor_patterns.items():
            print(f"\n📊 {forecast_vendor.upper()} ANALYSIS:")
            print("-" * 50)
            
            # Find matching transactions
            vendor_txns = income_df[
                income_df['vendor_name'].str.contains('|'.join(keywords), case=False, na=False) |
                income_df['description'].str.contains('|'.join(keywords), case=False, na=False)
            ].copy()
            
            if len(vendor_txns) == 0:
                print(f"❌ No transactions found for {forecast_vendor}")
                continue
            
            # Sort by date
            vendor_txns = vendor_txns.sort_values('transaction_date')
            
            print(f"✅ Found {len(vendor_txns)} transactions")
            print(f"💰 Total amount: ${vendor_txns['amount'].sum():,.2f}")
            print(f"📈 Average per transaction: ${vendor_txns['amount'].mean():,.2f}")
            print(f"📅 Date range: {vendor_txns['transaction_date'].min().strftime('%Y-%m-%d')} to {vendor_txns['transaction_date'].max().strftime('%Y-%m-%d')}")
            
            # Show recent transactions
            print(f"\n🔍 Recent transactions (last 10):")
            recent = vendor_txns.tail(10)
            for _, txn in recent.iterrows():
                print(f"  {txn['transaction_date'].strftime('%Y-%m-%d')} | ${txn['amount']:>10,.2f} | {txn['vendor_name'][:40]}")
            
            # Analyze patterns
            analyze_vendor_patterns(vendor_txns, forecast_vendor)
            
            vendor_analysis[forecast_vendor] = vendor_txns
        
        # Weekly analysis for recent months
        print("\n📈 WEEKLY PATTERN ANALYSIS")
        print("=" * 80)
        
        analyze_weekly_patterns(income_df, vendor_analysis)
        
        # Compare with forecast numbers
        print("\n🎯 FORECAST COMPARISON")
        print("=" * 80)
        
        compare_with_forecast(vendor_analysis)
        
        return vendor_analysis
        
    except Exception as e:
        print(f"❌ Error analyzing patterns: {e}")
        import traceback
        traceback.print_exc()
        return None

def analyze_vendor_patterns(vendor_txns, vendor_name):
    """Analyze specific patterns for a vendor."""
    if len(vendor_txns) < 2:
        return
    
    print(f"\n🔍 Pattern Analysis for {vendor_name}:")
    
    # Calculate days between transactions
    vendor_txns = vendor_txns.sort_values('transaction_date')
    vendor_txns['days_since_last'] = vendor_txns['transaction_date'].diff().dt.days
    
    # Remove NaN (first transaction)
    intervals = vendor_txns['days_since_last'].dropna()
    
    if len(intervals) > 0:
        print(f"  📊 Transaction intervals (days): {intervals.describe()}")
        
        # Check for weekly pattern (7 days ± 2)
        weekly_pattern = intervals[(intervals >= 5) & (intervals <= 9)]
        if len(weekly_pattern) > len(intervals) * 0.5:
            print(f"  ✅ Weekly pattern detected: {len(weekly_pattern)}/{len(intervals)} transactions are ~7 days apart")
        
        # Check for bi-weekly pattern (14 days ± 3)
        biweekly_pattern = intervals[(intervals >= 11) & (intervals <= 17)]
        if len(biweekly_pattern) > len(intervals) * 0.3:
            print(f"  ✅ Bi-weekly pattern detected: {len(biweekly_pattern)}/{len(intervals)} transactions are ~14 days apart")
        
        # Check for monthly pattern (28-31 days)
        monthly_pattern = intervals[(intervals >= 25) & (intervals <= 35)]
        if len(monthly_pattern) > len(intervals) * 0.3:
            print(f"  ✅ Monthly pattern detected: {len(monthly_pattern)}/{len(intervals)} transactions are ~30 days apart")
    
    # Amount patterns
    amounts = vendor_txns['amount']
    print(f"  💰 Amount patterns:")
    print(f"    Min: ${amounts.min():,.2f}")
    print(f"    Max: ${amounts.max():,.2f}")
    print(f"    Median: ${amounts.median():,.2f}")
    print(f"    Std Dev: ${amounts.std():,.2f}")
    
    # Check for consistent amounts
    amount_groups = amounts.round(-2).value_counts()  # Round to nearest $100
    if len(amount_groups) <= 5:
        print(f"  📈 Common amounts:")
        for amount, count in amount_groups.head().items():
            print(f"    ~${amount:,.0f}: {count} times")

def analyze_weekly_patterns(income_df, vendor_analysis):
    """Analyze weekly patterns for all vendors."""
    
    # Group by week
    income_df['week_start'] = income_df['transaction_date'].dt.to_period('W').dt.start_time
    weekly_totals = income_df.groupby('week_start')['amount'].sum().reset_index()
    weekly_totals = weekly_totals.sort_values('week_start', ascending=False)
    
    print(f"📅 Weekly totals for last 8 weeks:")
    for _, week in weekly_totals.head(8).iterrows():
        week_end = week['week_start'] + timedelta(days=6)
        print(f"  {week['week_start'].strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}: ${week['amount']:>10,.2f}")
    
    # Analyze each vendor's weekly patterns
    for vendor_name, vendor_txns in vendor_analysis.items():
        if len(vendor_txns) == 0:
            continue
            
        print(f"\n📊 {vendor_name} Weekly Breakdown:")
        vendor_txns['week_start'] = vendor_txns['transaction_date'].dt.to_period('W').dt.start_time
        vendor_weekly = vendor_txns.groupby('week_start')['amount'].sum().reset_index()
        vendor_weekly = vendor_weekly.sort_values('week_start', ascending=False)
        
        for _, week in vendor_weekly.head(6).iterrows():
            week_end = week['week_start'] + timedelta(days=6)
            print(f"    {week['week_start'].strftime('%m-%d')} to {week_end.strftime('%m-%d')}: ${week['amount']:>8,.2f}")

def compare_with_forecast(vendor_analysis):
    """Compare actual patterns with user's forecast numbers."""
    
    forecast_numbers = {
        'Amazon L': {'amount': 44777, 'frequency': 'bi-weekly'},
        'Shopify': {'amount': 12500, 'frequency': 'weekly'},
        'Amazon CA': {'amount': 475, 'frequency': 'weekly'},  # midpoint of 450-500
        'Amazon': {'amount': 684, 'frequency': 'weekly'},
        'PayPal': {'amount': 1360, 'frequency': 'alternating'},  # midpoint of 1120-1600
        'Stripe': {'amount': 350, 'frequency': 'weekly'},  # midpoint of 100-600
        'TikTok': {'amount': 95, 'frequency': 'weekly'}  # midpoint of 30-160
    }
    
    print("🎯 FORECAST vs ACTUAL COMPARISON:")
    print("-" * 60)
    
    for vendor_name, forecast in forecast_numbers.items():
        print(f"\n📊 {vendor_name}:")
        print(f"  🎯 Forecast: ${forecast['amount']:,.2f} {forecast['frequency']}")
        
        if vendor_name in vendor_analysis and len(vendor_analysis[vendor_name]) > 0:
            actual_txns = vendor_analysis[vendor_name]
            
            # Calculate actual weekly average
            weeks_span = (actual_txns['transaction_date'].max() - actual_txns['transaction_date'].min()).days / 7
            if weeks_span > 0:
                actual_weekly = actual_txns['amount'].sum() / weeks_span
                print(f"  📈 Actual weekly average: ${actual_weekly:,.2f}")
                
                # Compare based on frequency
                if forecast['frequency'] == 'weekly':
                    ratio = actual_weekly / forecast['amount']
                    print(f"  📊 Actual vs Forecast ratio: {ratio:.2f}x")
                elif forecast['frequency'] == 'bi-weekly':
                    actual_biweekly = actual_weekly * 2
                    ratio = actual_biweekly / forecast['amount']
                    print(f"  📊 Actual bi-weekly vs Forecast: ${actual_biweekly:,.2f} vs ${forecast['amount']:,.2f} (ratio: {ratio:.2f}x)")
                
                # Recent trend
                recent_txns = actual_txns.tail(5)
                if len(recent_txns) > 0:
                    recent_avg = recent_txns['amount'].mean()
                    print(f"  🔥 Recent 5 transactions average: ${recent_avg:,.2f}")
        else:
            print(f"  ❌ No actual transactions found")

if __name__ == "__main__":
    analyze_mercury_patterns()