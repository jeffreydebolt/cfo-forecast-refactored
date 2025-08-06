#!/usr/bin/env python3
"""
Generate 13-week forecast using proper vendor groupings.
"""

import sys
sys.path.append('.')

from datetime import date, timedelta
from lean_forecasting.forecast_generator import forecast_generator

def generate_13_week_forecast():
    """Generate complete 13-week forecast with proper groupings."""
    print("📊 13-WEEK FORECAST FOR BESTSELF")
    print("=" * 70)
    
    client_id = 'bestself'
    start_date = date(2025, 8, 4)  # Week of 8/4/25
    
    # Define proper vendor groups
    vendor_groups = [
        {
            'name': 'Amazon',
            'display_names': ['Amazon Revenue']
        },
        {
            'name': 'E-commerce Revenue',  # Combined Shopify group
            'display_names': ['Shopify Revenue', 'BestSelf Revenue', 'Affirm Payments']
        },
        {
            'name': 'PayPal Revenue',
            'display_names': ['PayPal Revenue']
        },
        {
            'name': 'Stripe Revenue',
            'display_names': ['Stripe Revenue']
        },
        {
            'name': 'TikTok Revenue',
            'display_names': ['TikTok Revenue']
        },
        {
            'name': 'Faire Revenue',
            'display_names': ['Faire Revenue']
        }
    ]
    
    # Generate forecasts for all groups
    all_forecasts = {}
    
    for group in vendor_groups:
        print(f"\n{'='*70}")
        forecasts = forecast_generator.generate_vendor_group_forecast(
            client_id=client_id,
            vendor_group_name=group['name'],
            display_names=group['display_names'],
            weeks_ahead=13,
            start_date=start_date
        )
        
        if forecasts:
            all_forecasts[group['name']] = forecasts
            print(f"✅ Generated {len(forecasts)} forecasts for {group['name']}")
        else:
            print(f"⚠️  No forecasts for {group['name']}")
    
    # Create 13-week summary
    print(f"\n{'='*70}")
    print(f"📋 13-WEEK FORECAST SUMMARY")
    print("=" * 70)
    print(f"{'Week Starting':<15} {'Amazon':<12} {'E-commerce':<12} {'Other':<10} {'Weekly Total':<15}")
    print("-" * 70)
    
    weekly_totals = []
    
    for week in range(13):
        week_start = start_date + timedelta(weeks=week)
        week_end = week_start + timedelta(days=6)
        
        # Calculate totals for this week
        week_total = 0
        amazon_amount = 0
        ecommerce_amount = 0
        other_amount = 0
        
        for group_name, forecasts in all_forecasts.items():
            for forecast in forecasts:
                forecast_date = forecast['forecast_date']
                if week_start <= forecast_date <= week_end:
                    amount = forecast['forecast_amount']
                    week_total += amount
                    
                    if group_name == 'Amazon':
                        amazon_amount += amount
                    elif group_name == 'E-commerce Revenue':
                        ecommerce_amount += amount
                    else:
                        other_amount += amount
        
        weekly_totals.append(week_total)
        
        print(f"{week_start.strftime('%m/%d')}            ${amazon_amount:>8,.0f}   ${ecommerce_amount:>8,.0f}   ${other_amount:>6,.0f}   ${week_total:>11,.0f}")
    
    # Summary statistics
    total_13_weeks = sum(weekly_totals)
    avg_weekly = total_13_weeks / 13 if weekly_totals else 0
    
    print("-" * 70)
    print(f"{'TOTALS':<15} ${sum(f['forecast_amount'] for forecasts in all_forecasts.values() for f in forecasts if f['vendor_group_name'] == 'Amazon'):>8,.0f}   ${sum(f['forecast_amount'] for forecasts in all_forecasts.values() for f in forecasts if f['vendor_group_name'] == 'E-commerce Revenue'):>8,.0f}   ${sum(f['forecast_amount'] for forecasts in all_forecasts.values() for f in forecasts if f['vendor_group_name'] not in ['Amazon', 'E-commerce Revenue']):>6,.0f}   ${total_13_weeks:>11,.0f}")
    
    print(f"\n📈 FORECAST SUMMARY:")
    print(f"Total 13-week revenue: ${total_13_weeks:,.2f}")
    print(f"Average weekly revenue: ${avg_weekly:,.2f}")
    
    # Show key patterns
    print(f"\n🔍 KEY PATTERNS DETECTED:")
    for group_name, forecasts in all_forecasts.items():
        if forecasts:
            sample = forecasts[0]
            pattern = sample.get('forecast_type', 'unknown')
            timing = sample.get('timing', 'unknown')
            amount = sample.get('forecast_amount', 0)
            print(f"  {group_name}: {pattern} on {timing}s, ${amount:,.0f} per occurrence")
    
    return all_forecasts

if __name__ == "__main__":
    generate_13_week_forecast()