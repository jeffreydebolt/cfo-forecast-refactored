#!/usr/bin/env python3
"""
Investigate bestself revenue discrepancies in forecast.
Focus on Shopify and Amazon transaction patterns.
"""

import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from supabase_client import supabase
import pandas as pd

def query_bestself_transactions():
    """Query recent bestself transactions to understand revenue patterns."""
    
    print("🔍 Investigating bestself transaction data...")
    
    # Get transactions from last 6 months
    six_months_ago = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
    
    try:
        # Query all bestself transactions
        response = supabase.table('transactions').select(
            'id, client_id, transaction_date, amount, description, vendor_name, type'
        ).eq('client_id', 'bestself').gte('transaction_date', six_months_ago).order('transaction_date', desc=True).execute()
        
        transactions = response.data
        print(f"📊 Found {len(transactions)} bestself transactions in last 6 months\n")
        
        if not transactions:
            print("❌ No bestself transactions found!")
            return
            
        # Convert to DataFrame for analysis
        df = pd.DataFrame(transactions)
        df['amount'] = df['amount'].astype(float)
        df['transaction_date'] = pd.to_datetime(df['transaction_date'])
        
        # Analyze by vendor patterns
        print("=== VENDOR ANALYSIS ===")
        vendor_summary = df.groupby('vendor_name').agg({
            'amount': ['sum', 'count', 'mean'],
            'transaction_date': ['min', 'max']
        }).round(2)
        
        # Flatten column names
        vendor_summary.columns = ['total_amount', 'transaction_count', 'avg_amount', 'first_date', 'last_date']
        vendor_summary = vendor_summary.sort_values('total_amount', ascending=False)
        
        print("Top 20 vendors by total amount:")
        print(vendor_summary.head(20))
        print()
        
        # Look for Shopify patterns
        shopify_transactions = df[df['vendor_name'].str.contains('shopify|SHOPIFY', case=False, na=False)]
        print(f"=== SHOPIFY ANALYSIS ===")
        print(f"Shopify transactions found: {len(shopify_transactions)}")
        if len(shopify_transactions) > 0:
            print(f"Total Shopify amount: ${shopify_transactions['amount'].sum():,.2f}")
            print(f"Average Shopify transaction: ${shopify_transactions['amount'].mean():.2f}")
            print(f"Date range: {shopify_transactions['transaction_date'].min()} to {shopify_transactions['transaction_date'].max()}")
            print("Sample Shopify transactions:")
            print(shopify_transactions[['transaction_date', 'amount', 'description', 'vendor_name']].head(10))
        print()
        
        # Look for Amazon patterns
        amazon_transactions = df[df['vendor_name'].str.contains('amazon|AMAZON', case=False, na=False)]
        print(f"=== AMAZON ANALYSIS ===")
        print(f"Amazon transactions found: {len(amazon_transactions)}")
        if len(amazon_transactions) > 0:
            print(f"Total Amazon amount: ${amazon_transactions['amount'].sum():,.2f}")
            print(f"Average Amazon transaction: ${amazon_transactions['amount'].mean():.2f}")
            print(f"Date range: {amazon_transactions['transaction_date'].min()} to {amazon_transactions['transaction_date'].max()}")
            print("Sample Amazon transactions:")
            print(amazon_transactions[['transaction_date', 'amount', 'description', 'vendor_name']].head(10))
        print()
        
        # Look for large deposits (>$1000)
        large_deposits = df[df['amount'] > 1000].sort_values('amount', ascending=False)
        print(f"=== LARGE DEPOSITS (>$1000) ===")
        print(f"Large deposits found: {len(large_deposits)}")
        if len(large_deposits) > 0:
            print(f"Total large deposits: ${large_deposits['amount'].sum():,.2f}")
            print("Top 20 large deposits:")
            print(large_deposits[['transaction_date', 'amount', 'description', 'vendor_name']].head(20))
        print()
        
        # Recent monthly totals
        print("=== MONTHLY REVENUE TOTALS ===")
        df['month'] = df['transaction_date'].dt.to_period('M')
        monthly_totals = df.groupby('month')['amount'].sum().sort_index(ascending=False)
        print("Last 6 months revenue:")
        for month, total in monthly_totals.head(6).items():
            print(f"{month}: ${total:,.2f}")
        print()
        
        # Daily patterns for recent data
        print("=== RECENT DAILY PATTERNS ===")
        recent_30_days = df[df['transaction_date'] >= (datetime.now() - timedelta(days=30))]
        if len(recent_30_days) > 0:
            daily_totals = recent_30_days.groupby(recent_30_days['transaction_date'].dt.date)['amount'].sum().sort_index(ascending=False)
            print("Last 30 days daily revenue:")
            for date, total in daily_totals.head(15).items():
                print(f"{date}: ${total:,.2f}")
        
        return df
        
    except Exception as e:
        print(f"❌ Error querying transactions: {e}")
        return None

def check_vendor_mappings():
    """Check vendor mappings for missing Amazon/Shopify entries."""
    
    print("\n🔍 Checking vendor mappings...")
    
    try:
        # Query vendor mappings for bestself
        response = supabase.table('vendors').select(
            'vendor_name, display_name, category, method, client_id'
        ).eq('client_id', 'bestself').execute()
        
        vendors = response.data
        print(f"📊 Found {len(vendors)} vendor mappings for bestself\n")
        
        if not vendors:
            print("❌ No vendor mappings found for bestself!")
            return
        
        # Convert to DataFrame
        df = pd.DataFrame(vendors)
        
        # Look for Shopify mappings
        shopify_vendors = df[df['vendor_name'].str.contains('shopify|SHOPIFY', case=False, na=False)]
        print(f"=== SHOPIFY VENDOR MAPPINGS ===")
        print(f"Shopify vendor mappings: {len(shopify_vendors)}")
        if len(shopify_vendors) > 0:
            print(shopify_vendors[['vendor_name', 'display_name', 'category', 'method']])
        else:
            print("❌ No Shopify vendor mappings found!")
        print()
        
        # Look for Amazon mappings
        amazon_vendors = df[df['vendor_name'].str.contains('amazon|AMAZON', case=False, na=False)]
        print(f"=== AMAZON VENDOR MAPPINGS ===")
        print(f"Amazon vendor mappings: {len(amazon_vendors)}")
        if len(amazon_vendors) > 0:
            print(amazon_vendors[['vendor_name', 'display_name', 'category', 'method']])
        else:
            print("❌ No Amazon vendor mappings found!")
        print()
        
        # Show all vendor mappings by category
        print("=== ALL VENDOR MAPPINGS BY CATEGORY ===")
        category_summary = df.groupby(['category', 'method']).size().reset_index(name='count')
        print(category_summary)
        print()
        
        # Show top vendors by name
        print("=== TOP VENDOR NAMES ===")
        vendor_counts = df['vendor_name'].value_counts()
        print(vendor_counts.head(20))
        
        return df
        
    except Exception as e:
        print(f"❌ Error querying vendor mappings: {e}")
        return None

def analyze_transaction_patterns():
    """Analyze transaction patterns to understand what might be missing."""
    
    print("\n🔍 Analyzing transaction patterns...")
    
    try:
        # Get all transactions without date filter to see full picture
        response = supabase.table('transactions').select(
            'id, client_id, transaction_date, amount, description, vendor_name, type'
        ).eq('client_id', 'bestself').order('transaction_date', desc=True).execute()
        
        transactions = response.data
        print(f"📊 Found {len(transactions)} total bestself transactions\n")
        
        if not transactions:
            return None
            
        df = pd.DataFrame(transactions)
        df['amount'] = df['amount'].astype(float)
        df['transaction_date'] = pd.to_datetime(df['transaction_date'])
        
        # Look for patterns in descriptions that might indicate missed revenue sources
        print("=== DESCRIPTION PATTERN ANALYSIS ===")
        
        # Look for common revenue keywords in descriptions
        revenue_keywords = ['shopify', 'amazon', 'stripe', 'paypal', 'square', 'payment', 'deposit', 'transfer', 'sales']
        
        for keyword in revenue_keywords:
            keyword_transactions = df[df['description'].str.contains(keyword, case=False, na=False)]
            if len(keyword_transactions) > 0:
                print(f"\n'{keyword.upper()}' in descriptions: {len(keyword_transactions)} transactions")
                print(f"Total amount: ${keyword_transactions['amount'].sum():,.2f}")
                print("Sample transactions:")
                print(keyword_transactions[['transaction_date', 'amount', 'description', 'vendor_name']].head(5))
        
        # Look for unmapped large transactions
        print("\n=== UNMAPPED LARGE TRANSACTIONS ===")
        unmapped_large = df[(df['amount'] > 1000) & (df['vendor_name'].isna() | (df['vendor_name'] == ''))]
        if len(unmapped_large) > 0:
            print(f"Found {len(unmapped_large)} large unmapped transactions:")
            print(unmapped_large[['transaction_date', 'amount', 'description']].head(10))
        else:
            print("No large unmapped transactions found")
            
        return df
        
    except Exception as e:
        print(f"❌ Error analyzing patterns: {e}")
        return None

def main():
    """Main investigation function."""
    
    print("🚀 Starting bestself revenue investigation...")
    print("=" * 60)
    
    # Check transaction data
    transactions_df = query_bestself_transactions()
    
    # Check vendor mappings
    vendors_df = check_vendor_mappings()
    
    # Analyze transaction patterns
    patterns_df = analyze_transaction_patterns()
    
    print("\n" + "=" * 60)
    print("🔍 INVESTIGATION SUMMARY")
    print("=" * 60)
    
    if transactions_df is not None:
        total_revenue = transactions_df['amount'].sum()
        avg_daily = total_revenue / 180  # 6 months
        print(f"📊 Total revenue (6 months): ${total_revenue:,.2f}")
        print(f"📊 Average daily revenue: ${avg_daily:,.2f}")
        print(f"📊 Total transactions: {len(transactions_df)}")
        
        # Key findings
        shopify_count = len(transactions_df[transactions_df['vendor_name'].str.contains('shopify|SHOPIFY', case=False, na=False)])
        amazon_count = len(transactions_df[transactions_df['vendor_name'].str.contains('amazon|AMAZON', case=False, na=False)])
        
        print(f"\n🔑 KEY FINDINGS:")
        print(f"   - Shopify transactions: {shopify_count}")
        print(f"   - Amazon transactions: {amazon_count}")
        
        if shopify_count == 0:
            print("   ❌ No Shopify transactions found - this could be the issue!")
        if amazon_count == 0:
            print("   ❌ No Amazon transactions found - this could be the issue!")
    
    print("\n✅ Investigation complete!")

if __name__ == "__main__":
    main()