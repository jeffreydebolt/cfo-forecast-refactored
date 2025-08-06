#!/usr/bin/env python3
"""
Export detailed 13-week forecast to CSV format.
"""

import sys
import csv
from datetime import datetime, timedelta
from services.forecast_service import ForecastService

def export_forecast_to_csv(client_id: str, weeks: int = 13):
    """Export detailed forecast to CSV."""
    
    # Initialize service
    forecast_service = ForecastService()
    
    # Calculate date range
    start_date = datetime.now().date()
    end_date = start_date + timedelta(weeks=weeks)
    
    print(f"🔄 Generating {weeks}-week forecast for {client_id}...")
    
    try:
        # Generate forecast data
        weekly_summary = forecast_service.generate_weekly_forecast_summary(client_id, start_date, end_date)
        calendar_forecast = forecast_service.generate_calendar_forecast(client_id, start_date, end_date)
        
        # Create CSV filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        csv_filename = f'{client_id}_{weeks}week_forecast_{timestamp}.csv'
        
        print(f"📊 Found {len(weekly_summary)} weeks")
        print(f"📊 Found {len(calendar_forecast.events)} total events")
        
        # Write to CSV
        with open(csv_filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Header
            writer.writerow([
                'Week', 'Start_Date', 'End_Date', 'Event_Date', 'Vendor', 
                'Amount', 'Type', 'Week_Deposits', 'Week_Withdrawals', 
                'Week_Net', 'Running_Balance'
            ])
            
            # Track running balance
            running_balance = 0
            
            for week_data in weekly_summary:
                week_num = week_data['week']
                start_date_str = week_data['start_date']
                end_date_str = week_data['end_date']
                week_deposits = week_data['total_deposits']
                week_withdrawals = week_data['total_withdrawals'] 
                week_net = week_data['net_cash_flow']
                
                # Update running balance
                running_balance += week_net
                
                # Get events for this week
                week_events = []
                for event in calendar_forecast.events:
                    event_date_str = event.date.strftime('%Y-%m-%d')
                    if start_date_str <= event_date_str <= end_date_str:
                        week_events.append(event)
                
                if week_events:
                    # Sort events by date
                    week_events.sort(key=lambda x: x.date)
                    
                    for i, event in enumerate(week_events):
                        vendor = event.vendor_display_name
                        amount = event.amount
                        event_date = event.date.strftime('%Y-%m-%d')
                        event_type = 'Deposit' if amount > 0 else 'Withdrawal'
                        
                        # Only show week totals on first row for each week
                        if i == 0:
                            writer.writerow([
                                f'W{week_num}', start_date_str, end_date_str, event_date, vendor, 
                                f'{amount:.2f}', event_type, f'{week_deposits:.2f}', 
                                f'{week_withdrawals:.2f}', f'{week_net:.2f}', f'{running_balance:.2f}'
                            ])
                        else:
                            writer.writerow([
                                '', '', '', event_date, vendor, f'{amount:.2f}', event_type, 
                                '', '', '', ''
                            ])
                else:
                    # Week with no events
                    writer.writerow([
                        f'W{week_num}', start_date_str, end_date_str, '', 'No Events', '0.00', '',
                        f'{week_deposits:.2f}', f'{week_withdrawals:.2f}', f'{week_net:.2f}', f'{running_balance:.2f}'
                    ])
        
        print(f"✅ Detailed forecast exported to: {csv_filename}")
        print(f"📂 File location: ./{csv_filename}")
        
        # Also create a summary CSV
        summary_filename = f'{client_id}_{weeks}week_summary_{timestamp}.csv'
        with open(summary_filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Summary header
            writer.writerow([
                'Week', 'Period', 'Deposits', 'Withdrawals', 'Net', 'Events', 'Balance'
            ])
            
            running_balance = 0
            for week_data in weekly_summary:
                running_balance += week_data['net_cash_flow']
                
                writer.writerow([
                    f"W{week_data['week']}", 
                    f"{week_data['start_date']} - {week_data['end_date']}",
                    f"${week_data['total_deposits']:>10,.0f}",
                    f"${week_data['total_withdrawals']:>10,.0f}",
                    f"${week_data['net_cash_flow']:>10,.0f}",
                    week_data['event_count'],
                    f"${running_balance:>10,.0f}"
                ])
        
        print(f"✅ Summary exported to: {summary_filename}")
        
        return csv_filename, summary_filename
        
    except Exception as e:
        print(f"❌ Error generating forecast: {e}")
        import traceback
        traceback.print_exc()
        return None, None

if __name__ == "__main__":
    client_id = sys.argv[1] if len(sys.argv) > 1 else 'bestself'
    weeks = int(sys.argv[2]) if len(sys.argv) > 2 else 13
    
    export_forecast_to_csv(client_id, weeks)