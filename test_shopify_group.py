#!/usr/bin/env python3
"""
Test Shopify group with ALL vendors included.
"""

import sys
sys.path.append('.')

from datetime import date, timedelta
from lean_forecasting.forecast_generator import forecast_generator

def test_complete_shopify_group():
    """Test Shopify group with ALL related vendors."""
    print("🧪 TESTING COMPLETE SHOPIFY GROUP")
    print("=" * 60)
    
    client_id = 'bestself'
    
    # Complete Shopify group as you described
    shopify_group = {
        'name': 'Shopify Complete',
        'display_names': [
            'Shopify Revenue',  # Direct Shopify 
            'Affirm Payments',  # Affirm connected to Shopify
            'BestSelf Revenue'  # BestSelf sales through Shopify
        ]
    }
    
    print(f"Testing Shopify group with vendors:")
    for vendor in shopify_group['display_names']:
        print(f"  • {vendor}")
    
    # Generate forecast for complete group
    forecasts = forecast_generator.generate_vendor_group_forecast(
        client_id=client_id,
        vendor_group_name=shopify_group['name'],
        display_names=shopify_group['display_names'],
        weeks_ahead=13
    )
    
    if not forecasts:
        print("❌ No forecasts generated")
        return
    
    # Show forecast for week of 8/4/25
    target_date = date(2025, 8, 4)  # Monday, Aug 4, 2025
    days_to_monday = target_date.weekday()
    week_start = target_date - timedelta(days=days_to_monday)
    
    week_result = forecast_generator.show_forecast_for_week(forecasts, week_start)
    
    print(f"\n🎯 SHOPIFY GROUP FORECAST FOR WEEK OF 8/4/25:")
    print(f"Expected: ~$12k per week")
    print(f"Actual: ${week_result['total']:.2f}")
    
    # Check if it's close to $12k
    expected_range = (10000, 15000)
    in_range = expected_range[0] <= week_result['total'] <= expected_range[1]
    
    print(f"Within $10k-$15k range: {'✅' if in_range else '❌'}")
    
    if week_result['total'] < 5000:
        print("⚠️  Still too low - missing vendors or transactions")
    
    return forecasts

if __name__ == "__main__":
    test_complete_shopify_group()