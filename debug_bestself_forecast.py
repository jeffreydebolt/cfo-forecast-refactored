#!/usr/bin/env python3
"""
Debug bestself forecasting to understand why revenues are so low.
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from supabase_client import supabase
from services.forecast_service import ForecastService
import pandas as pd

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_vendor_configurations():
    """Check how vendors are configured for bestself."""
    
    print("🔍 Checking bestself vendor configurations...")
    
    try:
        # Get all vendor configurations
        response = supabase.table('vendors').select(
            '*'
        ).eq('client_id', 'bestself').execute()
        
        vendors = response.data
        print(f"📊 Found {len(vendors)} vendor configurations\n")
        
        if not vendors:
            print("❌ No vendor configurations found!")
            return
        
        df = pd.DataFrame(vendors)
        
        # Show revenue vendors
        revenue_vendors = df[df['is_revenue'] == True]
        print(f"=== REVENUE VENDORS ({len(revenue_vendors)}) ===")
        if len(revenue_vendors) > 0:
            print(revenue_vendors[['vendor_name', 'display_name', 'forecast_frequency', 'forecast_day', 'forecast_amount', 'forecast_confidence']].to_string())
        else:
            print("❌ No revenue vendors configured!")
        print()
        
        # Show all vendors with forecast data
        forecast_vendors = df[(df['forecast_frequency'].notna()) & (df['forecast_frequency'] != 'irregular')]
        print(f"=== VENDORS WITH FORECAST CONFIG ({len(forecast_vendors)}) ===")
        if len(forecast_vendors) > 0:
            print(forecast_vendors[['vendor_name', 'display_name', 'forecast_frequency', 'forecast_day', 'forecast_amount', 'forecast_confidence']].to_string())
        else:
            print("❌ No vendors with forecast configuration!")
        print()
        
        # Check Amazon configurations
        amazon_vendors = df[df['vendor_name'].str.contains('AMAZON', case=False, na=False)]
        print(f"=== AMAZON VENDORS ({len(amazon_vendors)}) ===")
        if len(amazon_vendors) > 0:
            print(amazon_vendors[['vendor_name', 'display_name', 'is_revenue', 'forecast_frequency', 'forecast_amount']].to_string())
        else:
            print("❌ No Amazon vendors configured!")
        print()
        
        # Check Shopify configurations
        shopify_vendors = df[df['vendor_name'].str.contains('SHOPIFY', case=False, na=False)]
        print(f"=== SHOPIFY VENDORS ({len(shopify_vendors)}) ===")
        if len(shopify_vendors) > 0:
            print(shopify_vendors[['vendor_name', 'display_name', 'is_revenue', 'forecast_frequency', 'forecast_amount']].to_string())
        else:
            print("❌ No Shopify vendors configured!")
        print()
        
        return df
        
    except Exception as e:
        print(f"❌ Error checking vendor configurations: {e}")
        return None

def test_pattern_detection():
    """Test pattern detection on major revenue sources."""
    
    print("🔍 Testing pattern detection...")
    
    service = ForecastService()
    
    # Test major revenue sources we found
    major_vendors = ['SHOPIFY', 'BESTSELFCO', 'Shopify Revenue']
    
    for vendor_name in major_vendors:
        print(f"\n=== TESTING {vendor_name} ===")
        
        # Get transactions for this vendor
        transactions = service.get_vendor_transactions(vendor_name, 'bestself')
        print(f"Found {len(transactions)} transactions")
        
        if transactions:
            # Show recent transactions
            df = pd.DataFrame(transactions)
            df['transaction_date'] = pd.to_datetime(df['transaction_date'])
            df = df.sort_values('transaction_date', ascending=False)
            
            print("Recent transactions:")
            print(df[['transaction_date', 'amount', 'vendor_name']].head(10).to_string())
            
            # Test pattern detection
            from core.pattern_detection import classify_vendor_pattern
            result = classify_vendor_pattern(transactions, 'bestself')
            
            print(f"\nPattern Detection Result:")
            print(f"  Frequency: {result['frequency']}")
            print(f"  Forecast Day: {result['forecast_day']}")
            print(f"  Forecast Amount: ${result['forecast_amount']}")
            print(f"  Confidence: {result['confidence']}")
            print(f"  Explanation: {result['explanation']}")
        else:
            print("No transactions found for this vendor")

def test_full_forecast():
    """Test the full forecast pipeline for bestself."""
    
    print("🔍 Testing full forecast pipeline...")
    
    service = ForecastService()
    
    # Run pattern detection first
    print("\n=== RUNNING PATTERN DETECTION ===")
    pattern_results = service.detect_and_update_vendor_patterns('bestself')
    print(f"Pattern detection results: {pattern_results}")
    
    # Generate forecast
    print("\n=== GENERATING FORECAST ===")
    weekly_forecast = service.generate_weekly_forecast_summary('bestself')
    
    if weekly_forecast:
        print(f"Generated {len(weekly_forecast)} weeks of forecast:")
        
        for week in weekly_forecast[:8]:  # Show first 8 weeks
            print(f"Week {week['week_start']}: Deposits ${week['deposits']:,.2f}, Withdrawals ${week['withdrawals']:,.2f}, Net ${week['net']:,.2f}")
            
            # Show vendor breakdown
            if 'vendor_events' in week:
                for event in week['vendor_events'][:5]:  # Top 5 events
                    print(f"  - {event['vendor_name']}: ${event['amount']:,.2f}")
        
        # Calculate totals
        total_deposits = sum(week['deposits'] for week in weekly_forecast)
        total_withdrawals = sum(week['withdrawals'] for week in weekly_forecast)
        
        print(f"\n📊 13-WEEK FORECAST TOTALS:")
        print(f"Total Deposits: ${total_deposits:,.2f}")
        print(f"Total Withdrawals: ${total_withdrawals:,.2f}")
        print(f"Net Cash Flow: ${total_deposits - total_withdrawals:,.2f}")
        
    else:
        print("❌ No forecast generated!")

def check_missing_amazon_vendors():
    """Check if we're missing Amazon vendor mappings."""
    
    print("🔍 Checking for missing Amazon vendor mappings...")
    
    try:
        # Get all Amazon transaction vendor names from transactions
        response = supabase.table('transactions').select(
            'vendor_name'
        ).eq('client_id', 'bestself').ilike('vendor_name', '%AMAZON%').execute()
        
        amazon_transaction_vendors = set(t['vendor_name'] for t in response.data if t['vendor_name'])
        print(f"Found {len(amazon_transaction_vendors)} unique Amazon vendor names in transactions")
        
        # Get Amazon vendor names from vendors table
        response = supabase.table('vendors').select(
            'vendor_name'
        ).eq('client_id', 'bestself').ilike('vendor_name', '%AMAZON%').execute()
        
        amazon_mapped_vendors = set(v['vendor_name'] for v in response.data if v['vendor_name'])
        print(f"Found {len(amazon_mapped_vendors)} Amazon vendor names in vendors table")
        
        # Find unmapped Amazon vendors
        unmapped_amazon = amazon_transaction_vendors - amazon_mapped_vendors
        print(f"\n❌ UNMAPPED AMAZON VENDORS ({len(unmapped_amazon)}):")
        for vendor in sorted(unmapped_amazon):
            print(f"  - {vendor}")
            
        # Get transaction totals for unmapped vendors
        if unmapped_amazon:
            print("\n📊 UNMAPPED AMAZON REVENUE:")
            for vendor in sorted(unmapped_amazon):
                response = supabase.table('transactions').select(
                    'amount'
                ).eq('client_id', 'bestself').eq('vendor_name', vendor).execute()
                
                total = sum(float(t['amount']) for t in response.data)
                count = len(response.data)
                print(f"  {vendor}: ${total:,.2f} ({count} transactions)")
                
        return unmapped_amazon
        
    except Exception as e:
        print(f"❌ Error checking Amazon vendors: {e}")
        return set()

def main():
    """Main debug function."""
    
    print("🚀 Starting bestself forecast debugging...")
    print("=" * 60)
    
    # Check vendor configurations
    vendor_configs = check_vendor_configurations()
    
    # Check for missing Amazon vendors
    unmapped_amazon = check_missing_amazon_vendors()
    
    # Test pattern detection on key vendors
    test_pattern_detection()
    
    # Test full forecast
    test_full_forecast()
    
    print("\n" + "=" * 60)
    print("🔍 DEBUG SUMMARY")
    print("=" * 60)
    
    print("KEY ISSUES IDENTIFIED:")
    
    if unmapped_amazon:
        print(f"❌ {len(unmapped_amazon)} Amazon vendor names are not mapped to display names")
        print("   This means Amazon revenue is not being included in forecasts!")
    
    if vendor_configs is not None:
        revenue_count = len(vendor_configs[vendor_configs['is_revenue'] == True])
        forecast_count = len(vendor_configs[(vendor_configs['forecast_frequency'].notna()) & (vendor_configs['forecast_frequency'] != 'irregular')])
        
        print(f"📊 Only {revenue_count} vendors marked as revenue")
        print(f"📊 Only {forecast_count} vendors have forecast configurations")
        
        if revenue_count < 5:
            print("❌ Too few revenue vendors configured!")
        if forecast_count < 5:
            print("❌ Too few vendors with forecast configurations!")
    
    print("\n✅ Debug complete!")

if __name__ == "__main__":
    main()