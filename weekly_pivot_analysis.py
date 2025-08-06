"""
Create a detailed pivot table analysis of weekly transactions.
"""

import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict
from supabase_client import supabase
from config.client_context import get_current_client


def create_weekly_pivot_analysis(client_id: str, start_date: str, end_date: str):
    """
    Create a detailed pivot table analysis similar to the user's spreadsheet format.
    """
    print(f"\n{'='*100}")
    print(f"WEEKLY PIVOT TABLE ANALYSIS - {client_id}")
    print(f"Period: {start_date} to {end_date}")
    print(f"{'='*100}")
    
    try:
        # Get transactions for the week
        result = supabase.table('transactions') \
            .select('*') \
            .eq('client_id', client_id) \
            .gte('transaction_date', start_date) \
            .lte('transaction_date', end_date) \
            .order('transaction_date') \
            .execute()
        
        if not result.data:
            print("No transactions found for this period.")
            return
        
        # Get vendor mappings
        vendor_result = supabase.table('vendors') \
            .select('*') \
            .eq('client_id', client_id) \
            .execute()
        
        vendor_map = {}
        forecast_data = {}
        for vendor in vendor_result.data:
            if vendor.get('display_name'):
                # Map various vendor names to display name
                if vendor.get('vendor_name'):
                    vendor_map[vendor['vendor_name']] = vendor['display_name']
                if vendor.get('normalized_name'):
                    vendor_map[vendor['normalized_name']] = vendor['display_name']
                
                # Store forecast data
                if vendor.get('forecast_amount') and vendor.get('forecast_frequency'):
                    forecast_data[vendor['display_name']] = {
                        'amount': float(vendor['forecast_amount']),
                        'frequency': vendor['forecast_frequency'],
                        'method': vendor.get('forecast_method', 'unknown')
                    }
        
        # Process transactions by day
        daily_data = defaultdict(lambda: defaultdict(float))
        vendor_totals = defaultdict(float)
        
        # Get all days in the week
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        days = []
        current_day = start_dt
        while current_day <= end_dt:
            days.append(current_day.strftime('%Y-%m-%d'))
            current_day += timedelta(days=1)
        
        # Process each transaction
        for txn in result.data:
            amount = float(txn['amount'])
            vendor_name = txn.get('vendor_name', 'Unknown')
            date = txn['transaction_date']
            
            # Try to map to display name
            display_name = vendor_map.get(vendor_name, vendor_name)
            
            daily_data[display_name][date] += amount
            vendor_totals[display_name] += amount
        
        # Sort vendors by total absolute activity
        sorted_vendors = sorted(
            vendor_totals.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )
        
        # Create pivot table format
        print(f"\n{'DAILY BREAKDOWN PIVOT TABLE':^100}")
        print(f"{'='*100}")
        
        # Header
        header = f"{'Vendor/Date':<25}"
        for day in days:
            day_name = datetime.strptime(day, '%Y-%m-%d').strftime('%a %m/%d')
            header += f" | {day_name:>12}"
        header += f" | {'Total':>12}"
        print(header)
        print(f"{'-'*100}")
        
        # Data rows
        total_by_day = defaultdict(float)
        grand_total = 0
        
        for vendor_name, total in sorted_vendors:
            if abs(total) > 1:  # Only show vendors with significant activity
                row = f"{vendor_name[:24]:<25}"
                
                for day in days:
                    amount = daily_data[vendor_name][day]
                    if amount != 0:
                        row += f" | ${amount:>11,.2f}"
                        total_by_day[day] += amount
                    else:
                        row += f" | {'-':>12}"
                
                row += f" | ${total:>11,.2f}"
                print(row)
                grand_total += total
        
        # Totals row
        print(f"{'-'*100}")
        totals_row = f"{'DAILY TOTALS':<25}"
        for day in days:
            total = total_by_day[day]
            if total != 0:
                totals_row += f" | ${total:>11,.2f}"
            else:
                totals_row += f" | {'-':>12}"
        totals_row += f" | ${grand_total:>11,.2f}"
        print(totals_row)
        
        # Summary by category
        print(f"\n{'CATEGORY SUMMARY':^100}")
        print(f"{'='*100}")
        
        deposits = sum(amount for amount in vendor_totals.values() if amount > 0)
        withdrawals = sum(abs(amount) for amount in vendor_totals.values() if amount < 0)
        net_movement = deposits - withdrawals
        
        print(f"Total Deposits:    ${deposits:>15,.2f}")
        print(f"Total Withdrawals: ${withdrawals:>15,.2f}")
        print(f"Net Movement:      ${net_movement:>15,.2f}")
        print(f"Transaction Count: {len(result.data):>15}")
        
        # Forecast comparison
        print(f"\n{'FORECAST COMPARISON':^100}")
        print(f"{'='*100}")
        print(f"{'Vendor':<25} | {'Actual':>12} | {'Forecast':>12} | {'Variance':>12} | {'Accuracy':>8}")
        print(f"{'-'*100}")
        
        for vendor_name, actual_total in sorted_vendors[:10]:  # Top 10 vendors
            if vendor_name in forecast_data:
                forecast_amount = forecast_data[vendor_name]['amount']
                frequency = forecast_data[vendor_name]['frequency']
                
                # Adjust forecast for weekly period
                if frequency == 'monthly':
                    weekly_forecast = forecast_amount / 4.33  # Approximate weeks per month
                elif frequency == 'bi-weekly':
                    weekly_forecast = forecast_amount / 2
                else:  # weekly or other
                    weekly_forecast = forecast_amount
                
                variance = actual_total - weekly_forecast
                if weekly_forecast != 0:
                    accuracy = (1 - abs(variance) / abs(weekly_forecast)) * 100
                    accuracy = max(0, accuracy)  # Don't show negative accuracy
                else:
                    accuracy = 0
                
                print(f"{vendor_name[:24]:<25} | ${actual_total:>11,.2f} | ${weekly_forecast:>11,.2f} | ${variance:>11,.2f} | {accuracy:>7.1f}%")
        
        return {
            'daily_data': dict(daily_data),
            'vendor_totals': dict(vendor_totals),
            'total_deposits': deposits,
            'total_withdrawals': withdrawals,
            'net_movement': net_movement,
            'days_analyzed': days
        }
        
    except Exception as e:
        print(f"Error creating pivot analysis: {e}")
        return None


def export_to_csv(analysis_data, filename):
    """Export the pivot analysis to CSV format."""
    if not analysis_data:
        return
    
    try:
        # Create DataFrame
        df_data = []
        for vendor, daily_amounts in analysis_data['daily_data'].items():
            row = {'Vendor': vendor}
            for day in analysis_data['days_analyzed']:
                day_name = datetime.strptime(day, '%Y-%m-%d').strftime('%a_%m_%d')
                row[day_name] = daily_amounts.get(day, 0)
            row['Total'] = analysis_data['vendor_totals'][vendor]
            df_data.append(row)
        
        df = pd.DataFrame(df_data)
        df.to_csv(filename, index=False)
        print(f"\nPivot table exported to: {filename}")
        
    except Exception as e:
        print(f"Error exporting to CSV: {e}")


if __name__ == "__main__":
    # Analyze the week of April 21-27, 2025
    client_id = 'spyguy'
    start_date = '2025-04-21'
    end_date = '2025-04-27'
    
    analysis = create_weekly_pivot_analysis(client_id, start_date, end_date)
    
    if analysis:
        # Export to CSV
        filename = f"weekly_pivot_{client_id}_{start_date}_to_{end_date}.csv"
        export_to_csv(analysis, filename)