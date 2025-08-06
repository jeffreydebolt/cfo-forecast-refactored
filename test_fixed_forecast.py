#!/usr/bin/env python3
"""
Test the bestself forecast after fixing Amazon mappings.
"""

import logging
from services.forecast_service import ForecastService

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_fixed_forecast():
    """Test the forecast after Amazon mappings are fixed."""
    
    print("🚀 Testing bestself forecast after Amazon fix...")
    print("=" * 60)
    
    service = ForecastService()
    
    # Run the full forecast pipeline
    result = service.run_full_forecast_pipeline('bestself')
    
    if result['status'] == 'success':
        print("✅ Forecast pipeline completed successfully!")
        print(f"   Duration: {result['duration_seconds']} seconds")
        
        # Show pattern detection results
        pattern_results = result['pattern_detection']
        print(f"\n📊 PATTERN DETECTION RESULTS:")
        print(f"   Processed: {pattern_results['processed']} vendors")
        print(f"   Successful: {pattern_results['successful']} vendors")
        
        # Show forecast summary
        forecast_summary = result['forecast_summary']
        print(f"\n📊 13-WEEK FORECAST SUMMARY:")
        print(f"   Weeks Generated: {forecast_summary['weeks_generated']}")
        print(f"   Total Deposits: ${forecast_summary['total_deposits']:,.2f}")
        print(f"   Total Withdrawals: ${forecast_summary['total_withdrawals']:,.2f}")
        print(f"   Net Cash Flow: ${forecast_summary['net_movement']:,.2f}")
        
        # Show weekly breakdown
        weekly_forecast = result['weekly_forecast']
        print(f"\n📅 WEEKLY BREAKDOWN (First 8 weeks):")
        for i, week in enumerate(weekly_forecast[:8]):
            period = week.get('period_str', f'Week {i+1}')
            net_movement = week.get('net_movement', week.get('net', 0))
            print(f"   Week {i+1} ({period}): Deposits ${week['deposits']:,.2f}, Net ${net_movement:,.2f}")
        
        # Calculate monthly estimates
        monthly_deposits = forecast_summary['total_deposits'] * (52/13) / 12  # Convert 13 weeks to monthly
        print(f"\n📊 ESTIMATED MONTHLY REVENUE: ${monthly_deposits:,.2f}")
        
        # Compare to the original problem
        print(f"\n🎯 IMPROVEMENT ANALYSIS:")
        original_13_week = 8664  # The original problem amount
        new_13_week = forecast_summary['total_deposits']
        improvement = new_13_week - original_13_week
        
        print(f"   Original 13-week deposits: ${original_13_week:,.2f}")
        print(f"   New 13-week deposits: ${new_13_week:,.2f}")
        print(f"   Improvement: ${improvement:,.2f} ({improvement/original_13_week*100:.1f}% increase)")
        
        if new_13_week > 400000:  # Close to the expected $500k
            print("   ✅ Forecast is now in the expected range!")
        else:
            print("   ⚠️  Still below expected ~$500k range")
            
    else:
        print(f"❌ Forecast pipeline failed: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    test_fixed_forecast()