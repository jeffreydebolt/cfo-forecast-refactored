#!/usr/bin/env python3
"""
BestSelf forecast using approved vendor mappings.
"""

import sys
sys.path.append('.')

from lean_forecasting.temp_vendor_groups import temp_vendor_group_manager
from datetime import datetime, date, timedelta
import pandas as pd

def create_approved_bestself_group():
    """Create BestSelf Revenue group using approved vendor mappings."""
    print("✅ CREATING BESTSELF REVENUE GROUP WITH APPROVED MAPPINGS")
    print("=" * 70)
    
    client_id = 'bestself'
    
    # Use exactly the approved revenue streams
    approved_revenue_streams = [
        'Amazon Revenue',
        'BestSelf Revenue', 
        'Faire Revenue',
        'PayPal Revenue',
        'Shopify Revenue',
        'Stripe Revenue',
        'TikTok Revenue'
    ]
    
    # Create the vendor group
    group_result = temp_vendor_group_manager.create_vendor_group_from_display_names(
        client_id=client_id,
        group_name='BestSelf All Revenue',
        display_names=approved_revenue_streams
    )
    
    if not group_result['success']:
        print(f"❌ Failed to create group: {group_result.get('error')}")
        return None
    
    print(f"✅ Created 'BestSelf All Revenue' group")
    print(f"   Revenue streams: {len(approved_revenue_streams)}")
    print(f"   Total vendor names: {group_result['group_info']['vendor_count']}")
    
    return group_result['group_info']

def analyze_approved_group_pattern():
    """Analyze pattern for the approved BestSelf Revenue group."""
    print(f"\n📊 PATTERN ANALYSIS - APPROVED REVENUE STREAMS")
    print("=" * 70)
    
    client_id = 'bestself'
    approved_revenue_streams = [
        'Amazon Revenue', 'BestSelf Revenue', 'Faire Revenue',
        'PayPal Revenue', 'Shopify Revenue', 'Stripe Revenue', 'TikTok Revenue'
    ]
    
    # Analyze pattern
    pattern_analysis = temp_vendor_group_manager.analyze_group_pattern(
        client_id, 'BestSelf All Revenue', approved_revenue_streams
    )
    
    print(f"Pattern: {pattern_analysis['pattern']}")
    print(f"Details: {pattern_analysis['details']}")
    print(f"Confidence: {pattern_analysis['confidence']:.2f}")
    print(f"Transaction count: {pattern_analysis['transaction_count']}")
    print(f"Average amount: ${pattern_analysis['avg_amount']:.2f}")
    print(f"Date range: {pattern_analysis['date_range']}")
    
    return pattern_analysis

def generate_approved_forecast(pattern_analysis, weeks_ahead=13):
    """Generate forecast using approved pattern analysis."""
    print(f"\n🔮 GENERATING {weeks_ahead}-WEEK FORECAST")
    print("=" * 70)
    
    if not pattern_analysis or pattern_analysis['transaction_count'] == 0:
        print("❌ No pattern data to forecast from")
        return []
    
    pattern = pattern_analysis['pattern']
    avg_amount = pattern_analysis['avg_amount']
    
    forecasts = []
    start_date = date.today()
    
    print(f"Using approved vendor mappings:")
    print(f"- Amazon Revenue (83 vendor names)")
    print(f"- BestSelf Revenue, Faire Revenue, PayPal Revenue")
    print(f"- Shopify Revenue, Stripe Revenue, TikTok Revenue")
    print(f"Total: {pattern_analysis['transaction_count']} transactions, ${avg_amount:.2f} average")
    print()
    
    if pattern == 'daily':
        print(f"📅 Daily pattern - forecasting ${avg_amount:.2f} per weekday")
        
        for i in range(weeks_ahead * 7):
            forecast_date = start_date + timedelta(days=i)
            
            # Only forecast for weekdays
            if forecast_date.weekday() < 5:  # Monday = 0, Friday = 4
                forecasts.append({
                    'date': forecast_date,
                    'amount': avg_amount,
                    'type': 'daily',
                    'confidence': pattern_analysis['confidence'],
                    'vendor_group': 'BestSelf All Revenue (Amazon + 6 others)'
                })
    
    elif pattern == 'weekly':
        print(f"📅 Weekly pattern - forecasting ${avg_amount:.2f} per week")
        
        for week in range(weeks_ahead):
            days_ahead = week * 7
            forecast_date = start_date + timedelta(days=days_ahead)
            
            forecasts.append({
                'date': forecast_date,
                'amount': avg_amount,
                'type': 'weekly',
                'confidence': pattern_analysis['confidence'],
                'vendor_group': 'BestSelf All Revenue (Amazon + 6 others)'
            })
    
    return forecasts

def show_week_forecast(forecasts, target_week_start):
    """Show forecast for specific week with vendor breakdown."""
    print(f"\n📊 FORECAST FOR WEEK OF {target_week_start}")
    print("=" * 70)
    
    week_end = target_week_start + timedelta(days=6)
    week_forecasts = [
        f for f in forecasts 
        if target_week_start <= f['date'] <= week_end
    ]
    
    if not week_forecasts:
        print("❌ No forecasts for this week")
        return 0
    
    print(f"📋 INCLUDES ALL APPROVED REVENUE STREAMS:")
    print(f"   • Amazon Revenue (83 vendor names like AMAZON.CXYZ)")
    print(f"   • BestSelf Revenue (BESTSELFCO)")
    print(f"   • Faire Revenue, PayPal Revenue, Shopify Revenue")
    print(f"   • Stripe Revenue, TikTok Revenue")
    print()
    
    total_week_amount = 0
    for forecast in week_forecasts:
        day_name = forecast['date'].strftime('%A')
        print(f"{forecast['date']} ({day_name}): ${forecast['amount']:.2f} ({forecast['type']})")
        total_week_amount += forecast['amount']
    
    print(f"\n💰 TOTAL FOR WEEK: ${total_week_amount:.2f}")
    print(f"🎯 CONFIDENCE: {week_forecasts[0]['confidence']:.2f}")
    print(f"📊 VENDOR GROUP: {week_forecasts[0]['vendor_group']}")
    
    return total_week_amount

def main():
    """Main function using approved vendor mappings."""
    try:
        # Step 1: Create approved group
        group_info = create_approved_bestself_group()
        if not group_info:
            return
        
        # Step 2: Analyze pattern
        pattern_analysis = analyze_approved_group_pattern()
        if not pattern_analysis:
            return
        
        # Step 3: Generate forecast
        forecasts = generate_approved_forecast(pattern_analysis, weeks_ahead=13)
        if not forecasts:
            return
        
        print(f"\n✅ Generated {len(forecasts)} forecast records")
        
        # Step 4: Show forecast for week of 8/4/25
        target_date = date(2025, 8, 4)  # Monday, Aug 4, 2025
        days_to_monday = target_date.weekday()
        week_start = target_date - timedelta(days=days_to_monday)
        
        weekly_total = show_week_forecast(forecasts, week_start)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()