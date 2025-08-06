#!/usr/bin/env python3
"""
Test complete forecasting system with multiple vendor groups.
"""

import sys
sys.path.append('.')

from datetime import date, timedelta
from lean_forecasting.forecast_generator import forecast_generator

def test_complete_forecasting():
    """Test forecasting for multiple BestSelf revenue streams."""
    print("🧪 TESTING COMPLETE FORECASTING SYSTEM")
    print("=" * 70)
    
    client_id = 'bestself'
    
    # Define vendor groups to forecast
    vendor_groups = [
        {
            'name': 'Amazon',
            'display_names': ['Amazon Revenue']
        },
        {
            'name': 'Shopify Revenue',
            'display_names': ['Shopify Revenue']
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
            weeks_ahead=13
        )
        
        if forecasts:
            all_forecasts[group['name']] = forecasts
            print(f"✅ Generated {len(forecasts)} forecasts for {group['name']}")
        else:
            print(f"⚠️  No forecasts for {group['name']}")
    
    # Show combined forecast for week of 8/4/25
    target_date = date(2025, 8, 4)  # Monday, Aug 4, 2025
    days_to_monday = target_date.weekday()
    week_start = target_date - timedelta(days=days_to_monday)
    
    print(f"\n{'='*70}")
    print(f"📊 COMPLETE FORECAST FOR WEEK OF {week_start}")
    print("=" * 70)
    
    total_week_revenue = 0
    week_breakdown = {}
    
    for group_name, forecasts in all_forecasts.items():
        week_result = forecast_generator.show_forecast_for_week(forecasts, week_start)
        
        if week_result['total'] > 0:
            total_week_revenue += week_result['total']
            week_breakdown[group_name] = week_result['total']
            
            # Show individual forecast dates for this group
            for forecast in week_result['forecasts']:
                date_obj = forecast['forecast_date']
                day_name = date_obj.strftime('%A')
                print(f"  {group_name}: {date_obj} ({day_name}) = ${forecast['forecast_amount']:.2f}")
    
    print(f"\n💰 TOTAL WEEK REVENUE: ${total_week_revenue:.2f}")
    
    # Show breakdown by group
    print(f"\n📋 BREAKDOWN BY VENDOR GROUP:")
    for group_name, amount in sorted(week_breakdown.items(), key=lambda x: x[1], reverse=True):
        percentage = (amount / total_week_revenue) * 100 if total_week_revenue > 0 else 0
        print(f"  {group_name}: ${amount:.2f} ({percentage:.1f}%)")
    
    # Compare with user's actual forecast
    print(f"\n🎯 COMPARISON WITH YOUR FORECAST:")
    print(f"Your Amazon forecast for 8/5/25: $46,000")
    print(f"System Amazon forecast: ${week_breakdown.get('Amazon', 0):.2f}")
    
    amazon_match = abs(week_breakdown.get('Amazon', 0) - 46000) < 3000
    print(f"Amazon match (within $3k): {'✅' if amazon_match else '❌'}")
    
    print(f"\nSystem shows individual date records with:")
    print(f"• Specific dates (not aggregated)")
    print(f"• Vendor group names (not individual vendors)")
    print(f"• Pattern-based timing (bi-weekly Tuesdays, etc.)")
    print(f"• Weighted average amounts")
    
    return all_forecasts

if __name__ == "__main__":
    test_complete_forecasting()