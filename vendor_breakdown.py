#!/usr/bin/env python3
"""
Show vendor-by-vendor breakdown of weekly forecasts
"""

from weekly_cash_flow import WeeklyCashFlow
from datetime import datetime, timedelta
from collections import defaultdict

def show_vendor_breakdown(client_id='spyguy', weeks=13):
    """Show detailed vendor breakdown by week."""
    
    # Create weekly cash flow generator
    wcf = WeeklyCashFlow(client_id, weeks)
    
    # Get forecasted transactions
    forecasted_txns = wcf._get_forecasted_transactions()
    
    print(f'Found {len(forecasted_txns)} forecasted transactions:')
    print()
    
    # Group by week and vendor
    by_week = defaultdict(lambda: defaultdict(list))
    
    for txn in forecasted_txns:
        week_start = wcf.start_date
        week_num = 1
        
        # Find which week this transaction falls into
        while week_num <= weeks:
            week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)
            if week_start <= txn['date'] <= week_end:
                break
            week_start = week_start + timedelta(days=7)
            week_num += 1
        
        if week_num <= weeks:
            by_week[week_num][txn['vendor_name']].append(txn['amount'])
    
    # Print breakdown
    for week in range(1, weeks + 1):
        week_start = wcf.start_date + timedelta(days=(week-1)*7)
        week_end = week_start + timedelta(days=6)
        print(f'WEEK {week} ({week_start.strftime("%m/%d")} - {week_end.strftime("%m/%d")}):')
        
        if week in by_week:
            total_deposits = 0
            total_withdrawals = 0
            
            for vendor, amounts in by_week[week].items():
                total_amount = sum(amounts)
                if total_amount > 0:
                    total_deposits += total_amount
                    print(f'  + {vendor}: ${total_amount:.2f}')
                else:
                    total_withdrawals += abs(total_amount)
                    print(f'  - {vendor}: ${abs(total_amount):.2f}')
            
            print(f'  → Week Total: Deposits ${total_deposits:.2f}, Withdrawals ${total_withdrawals:.2f}')
        else:
            print('  → No transactions')
        print()

if __name__ == "__main__":
    show_vendor_breakdown()