#!/usr/bin/env python3
"""
Test BestSelf forecasting with the lean approach.
"""

import sys
sys.path.append('.')

from lean_forecasting.temp_vendor_groups import temp_vendor_group_manager
from datetime import datetime, date, timedelta
import pandas as pd

def analyze_bestself_pattern():
    """Analyze BestSelf revenue pattern for forecasting."""
    print("🔍 ANALYZING BESTSELF REVENUE PATTERN")
    print("=" * 60)
    
    client_id = 'bestself'
    
    # Get available display names
    display_names = temp_vendor_group_manager.get_available_display_names(client_id)
    print(f"Available display names: {display_names}")
    
    # Focus on revenue streams
    revenue_display_names = [dn for dn in display_names if 'Revenue' in dn or 'BESTSELFCO' in dn]
    print(f"\nRevenue display names: {revenue_display_names}")
    
    if not revenue_display_names:
        print("❌ No revenue display names found")
        return
    
    # Create a logical group for BestSelf Revenue
    group_result = temp_vendor_group_manager.create_vendor_group_from_display_names(
        client_id=client_id,
        group_name='BestSelf Revenue',
        display_names=revenue_display_names
    )
    
    if not group_result['success']:
        print(f"❌ Failed to create group: {group_result.get('error')}")
        return
    
    print(f"✅ Created group: {group_result['group_info']}")
    
    # Analyze pattern
    pattern_analysis = temp_vendor_group_manager.analyze_group_pattern(
        client_id, 'BestSelf Revenue', revenue_display_names
    )
    
    print(f"\n📊 PATTERN ANALYSIS:")
    print(f"Pattern: {pattern_analysis['pattern']}")
    print(f"Details: {pattern_analysis['details']}")
    print(f"Confidence: {pattern_analysis['confidence']:.2f}")
    print(f"Transaction count: {pattern_analysis['transaction_count']}")
    print(f"Average amount: ${pattern_analysis['avg_amount']:.2f}")
    print(f"Date range: {pattern_analysis['date_range']}")
    
    return pattern_analysis

def generate_simple_forecast(pattern_analysis, weeks_ahead=13):
    """Generate a simple forecast based on pattern analysis."""
    print(f"\n🔮 GENERATING {weeks_ahead}-WEEK FORECAST")
    print("=" * 60)
    
    if not pattern_analysis or pattern_analysis['transaction_count'] == 0:
        print("❌ No pattern data to forecast from")
        return []
    
    pattern = pattern_analysis['pattern']
    avg_amount = pattern_analysis['avg_amount']
    
    forecasts = []
    start_date = date.today()
    
    # Simple forecast logic based on detected pattern
    if pattern == 'daily':
        print(f"📅 Daily pattern detected - forecasting ${avg_amount:.2f} per weekday")
        
        for i in range(weeks_ahead * 7):
            forecast_date = start_date + timedelta(days=i)
            
            # Only forecast for weekdays if it's a business pattern
            if forecast_date.weekday() < 5:  # Monday = 0, Friday = 4
                forecasts.append({
                    'date': forecast_date,
                    'amount': avg_amount,
                    'type': 'daily',
                    'confidence': pattern_analysis['confidence']
                })
    
    elif pattern == 'weekly':
        print(f"📅 Weekly pattern detected - forecasting ${avg_amount:.2f} per week")
        
        # Find the most common day of week from the pattern analysis
        # For now, assume Monday (weekday 0)
        forecast_day = 0  # Monday
        
        for week in range(weeks_ahead):
            # Find the next occurrence of the forecast day
            days_ahead = week * 7 + (forecast_day - start_date.weekday()) % 7
            forecast_date = start_date + timedelta(days=days_ahead)
            
            forecasts.append({
                'date': forecast_date,
                'amount': avg_amount,
                'type': 'weekly',
                'confidence': pattern_analysis['confidence']
            })
    
    elif pattern == 'monthly':
        print(f"📅 Monthly pattern detected - forecasting ${avg_amount:.2f} per month")
        
        # Simple monthly forecast - assume middle of month
        current_month = start_date.replace(day=15)
        
        for month in range((weeks_ahead // 4) + 1):  # Approximate months
            forecast_date = current_month + timedelta(days=month * 30)
            
            forecasts.append({
                'date': forecast_date,
                'amount': avg_amount,
                'type': 'monthly',
                'confidence': pattern_analysis['confidence']
            })
    
    else:
        print(f"⚠️  {pattern} pattern - no forecast generated")
    
    return forecasts

def show_forecast_for_week(forecasts, target_week_start, pattern_analysis=None):
    """Show forecast for a specific week."""
    print(f"\n📊 FORECAST FOR WEEK OF {target_week_start}")
    print("=" * 60)
    
    week_end = target_week_start + timedelta(days=6)
    week_forecasts = [
        f for f in forecasts 
        if target_week_start <= f['date'] <= week_end
    ]
    
    if not week_forecasts:
        print("❌ No forecasts for this week")
        return 0
    
    # Show which vendors are included in this forecast
    if pattern_analysis:
        print(f"📋 VENDORS INCLUDED IN THIS FORECAST:")
        print(f"   Group: BestSelf Revenue")
        print(f"   Display Names: Amazon Revenue, BestSelf Revenue, Faire Revenue,")
        print(f"                 PayPal Revenue, Shopify Revenue, Stripe Revenue, TikTok Revenue")
        print(f"   Based on {pattern_analysis['transaction_count']} transactions")
        print()
    
    total_week_amount = 0
    for forecast in week_forecasts:
        print(f"{forecast['date']} ({forecast['date'].strftime('%A')}): ${forecast['amount']:.2f} ({forecast['type']})")
        total_week_amount += forecast['amount']
    
    print(f"\n💰 TOTAL FOR WEEK: ${total_week_amount:.2f}")
    print(f"🎯 CONFIDENCE: {week_forecasts[0]['confidence']:.2f}")
    
    return total_week_amount

def main():
    """Main test function."""
    try:
        # Step 1: Analyze pattern
        pattern_analysis = analyze_bestself_pattern()
        
        if not pattern_analysis:
            return
        
        # Step 2: Generate forecast
        forecasts = generate_simple_forecast(pattern_analysis, weeks_ahead=13)
        
        if not forecasts:
            return
        
        print(f"\n✅ Generated {len(forecasts)} forecast records")
        
        # Step 3: Show forecast for week of 8/4/25 (user's specific request)
        target_date = date(2025, 8, 4)  # Monday, Aug 4, 2025
        
        # Find the Monday of that week
        days_to_monday = target_date.weekday()  # 0 = Monday
        week_start = target_date - timedelta(days=days_to_monday)
        
        weekly_total = show_forecast_for_week(forecasts, week_start, pattern_analysis)
        
        # Show some other weeks for context
        print(f"\n📈 SAMPLE OF OTHER WEEKS:")
        for i in range(3):
            sample_week = date.today() + timedelta(weeks=i*2)
            sample_week_start = sample_week - timedelta(days=sample_week.weekday())
            print(f"\nWeek of {sample_week_start}:")
            show_forecast_for_week(forecasts, sample_week_start)
        
    except Exception as e:
        print(f"❌ Error in main: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()