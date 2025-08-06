"""
Run Calendar-Based Forecast
Main script to run the restored pattern detection + calendar forecasting system.
"""

import sys
import logging
import argparse
from datetime import datetime, UTC
from services.forecast_service import ForecastService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Run calendar-based forecast')
    parser.add_argument('--client-id', default='bestself', help='Client ID to process')
    parser.add_argument('--weeks', type=int, default=13, help='Number of weeks to forecast')
    parser.add_argument('--detect-patterns', action='store_true', 
                       help='Run pattern detection before generating forecast')
    parser.add_argument('--show-events', action='store_true',
                       help='Show individual forecast events instead of weekly summary')
    
    args = parser.parse_args()
    
    logger.info(f"Starting calendar forecast for client: {args.client_id}")
    
    try:
        service = ForecastService()
        
        if args.detect_patterns:
            logger.info("Running pattern detection first...")
            pattern_results = service.detect_and_update_vendor_patterns(args.client_id)
            logger.info(f"Pattern detection: {pattern_results['successful']}/{pattern_results['processed']} vendors processed")
        
        if args.show_events:
            # Show individual events
            logger.info("Generating individual forecast events...")
            events = service.generate_calendar_forecast(args.client_id, weeks_ahead=args.weeks)
            
            if not events:
                logger.warning("No forecast events generated")
                return
            
            print(f"\n📅 Calendar Forecast Events ({len(events)} events):")
            print("=" * 80)
            
            current_month = None
            total_deposits = 0
            total_withdrawals = 0
            
            for event in events:
                # Group by month for readability
                event_month = event.date.strftime('%Y-%m')
                if event_month != current_month:
                    if current_month:
                        print("-" * 40)
                    print(f"\n{event.date.strftime('%B %Y')}")
                    print("-" * 40)
                    current_month = event_month
                
                # Format display
                amount_str = f"${event.amount:,.2f}"
                if event.amount > 0:
                    amount_str = f"📈 +{amount_str}"
                    total_deposits += event.amount
                else:
                    amount_str = f"📉 {amount_str}"
                    total_withdrawals += abs(event.amount)
                
                confidence_str = f"({event.confidence:.0%})" if event.confidence < 1.0 else ""
                source_str = "🔧" if event.source == 'manual_override' else ""
                
                print(f"{event.date.strftime('%m/%d')} {event.date.strftime('%a')} - {event.vendor_display_name:<25} {amount_str:>12} {confidence_str} {source_str}")
            
            print("\n" + "=" * 80)
            print(f"📊 Total Forecast Summary:")
            print(f"   Deposits:    ${total_deposits:,.2f}")
            print(f"   Withdrawals: ${total_withdrawals:,.2f}")
            print(f"   Net:         ${total_deposits - total_withdrawals:,.2f}")
        
        else:
            # Show weekly summary (default)
            logger.info("Generating weekly forecast summary...")
            weekly_forecast = service.generate_weekly_forecast_summary(args.client_id, weeks_ahead=args.weeks)
            
            if not weekly_forecast:
                logger.warning("No weekly forecast generated")
                return
            
            print(f"\n📊 Weekly Cash Flow Forecast ({len(weekly_forecast)} weeks):")
            print("=" * 100)
            print(f"{'Week':<6} {'Period':<20} {'Deposits':<12} {'Withdrawals':<12} {'Net':<12} {'Events':<8} {'Balance':<12}")
            print("-" * 100)
            
            running_balance = 0  # Could get current balance from database
            total_deposits = 0
            total_withdrawals = 0
            
            for week in weekly_forecast:
                running_balance += week['net_movement']
                total_deposits += week['deposits']
                total_withdrawals += week['withdrawals']
                
                print(f"W{week['week_number']:<5} {week['period_str']:<20} "
                      f"${week['deposits']:>10,.0f} ${week['withdrawals']:>10,.0f} "
                      f"${week['net_movement']:>10,.0f} {week['event_count']:>7} "
                      f"${running_balance:>10,.0f}")
            
            print("-" * 100)
            print(f"{'TOTAL':<27} ${total_deposits:>10,.0f} ${total_withdrawals:>10,.0f} "
                  f"${total_deposits - total_withdrawals:>10,.0f}")
            
            # Show vendor breakdown for first few weeks
            print(f"\n🔍 Vendor Breakdown (First 4 Weeks):")
            print("=" * 80)
            
            for i, week in enumerate(weekly_forecast[:4]):
                if week['events']:
                    print(f"\nWeek {week['week_number']} ({week['period_str']}):")
                    vendor_totals = {}
                    for event in week['events']:
                        vendor = event.vendor_display_name
                        vendor_totals[vendor] = vendor_totals.get(vendor, 0) + event.amount
                    
                    for vendor, amount in sorted(vendor_totals.items(), key=lambda x: abs(x[1]), reverse=True):
                        print(f"  {vendor:<30} ${amount:>10,.2f}")
        
        logger.info("Calendar forecast complete!")
        
    except Exception as e:
        logger.error(f"Error running forecast: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()