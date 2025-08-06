"""
Analyze actual transactions for a specific week and compare to forecast.
"""

import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict
from supabase_client import supabase
from config.client_context import get_current_client


def analyze_week_transactions(client_id: str, start_date: str, end_date: str):
    """
    Analyze actual transactions for a specific week.
    
    Args:
        client_id: Client ID to analyze
        start_date: Start date (YYYY-MM-DD format)
        end_date: End date (YYYY-MM-DD format)
    """
    print(f"\n{'='*80}")
    print(f"ACTUAL TRANSACTIONS ANALYSIS - {client_id}")
    print(f"Period: {start_date} to {end_date}")
    print(f"{'='*80}")
    
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
        
        transactions = result.data
        print(f"Total transactions found: {len(transactions)}")
        
        # Get vendor mappings
        vendor_result = supabase.table('vendors') \
            .select('*') \
            .eq('client_id', client_id) \
            .execute()
        
        vendor_map = {}
        for vendor in vendor_result.data:
            if vendor.get('display_name'):
                # Map various vendor names to display name
                if vendor.get('vendor_name'):
                    vendor_map[vendor['vendor_name']] = vendor['display_name']
                if vendor.get('normalized_name'):
                    vendor_map[vendor['normalized_name']] = vendor['display_name']
        
        # Process transactions
        vendor_summary = defaultdict(lambda: {'deposits': 0, 'withdrawals': 0, 'count': 0, 'transactions': []})
        total_deposits = 0
        total_withdrawals = 0
        
        for txn in transactions:
            amount = float(txn['amount'])
            vendor_name = txn.get('vendor_name', 'Unknown')
            
            # Try to map to display name
            display_name = vendor_map.get(vendor_name, vendor_name)
            
            # Categorize as deposit or withdrawal
            if amount > 0:
                vendor_summary[display_name]['deposits'] += amount
                total_deposits += amount
            else:
                vendor_summary[display_name]['withdrawals'] += abs(amount)
                total_withdrawals += abs(amount)
            
            vendor_summary[display_name]['count'] += 1
            vendor_summary[display_name]['transactions'].append({
                'date': txn['transaction_date'],
                'amount': amount,
                'description': txn.get('description', ''),
                'original_vendor': vendor_name
            })
        
        # Print summary by vendor
        print(f"\n{'VENDOR BREAKDOWN':^80}")
        print(f"{'='*80}")
        print(f"{'Vendor':<30} | {'Deposits':>12} | {'Withdrawals':>12} | {'Net':>12} | {'Count':>5}")
        print(f"{'-'*80}")
        
        # Sort vendors by total activity (deposits + withdrawals)
        sorted_vendors = sorted(
            vendor_summary.items(),
            key=lambda x: x[1]['deposits'] + x[1]['withdrawals'],
            reverse=True
        )
        
        for vendor_name, data in sorted_vendors:
            net_amount = data['deposits'] - data['withdrawals']
            print(f"{vendor_name[:29]:<30} | ${data['deposits']:>11,.2f} | ${data['withdrawals']:>11,.2f} | ${net_amount:>11,.2f} | {data['count']:>5}")
        
        # Print totals
        print(f"{'-'*80}")
        net_total = total_deposits - total_withdrawals
        print(f"{'TOTALS':<30} | ${total_deposits:>11,.2f} | ${total_withdrawals:>11,.2f} | ${net_total:>11,.2f} | {len(transactions):>5}")
        
        # Print detailed transactions for significant vendors
        print(f"\n{'DETAILED TRANSACTIONS':^80}")
        print(f"{'='*80}")
        
        for vendor_name, data in sorted_vendors[:5]:  # Top 5 vendors by activity
            if data['deposits'] + data['withdrawals'] > 100:  # Only show significant vendors
                print(f"\n{vendor_name}:")
                print(f"{'Date':<12} | {'Amount':>12} | {'Description':<40}")
                print(f"{'-'*70}")
                
                for txn in sorted(data['transactions'], key=lambda x: x['date']):
                    desc = txn['description'][:39] if txn['description'] else ''
                    print(f"{txn['date']:<12} | ${txn['amount']:>11,.2f} | {desc:<40}")
        
        return {
            'total_deposits': total_deposits,
            'total_withdrawals': total_withdrawals,
            'net_movement': net_total,
            'vendor_summary': dict(vendor_summary),
            'transaction_count': len(transactions)
        }
        
    except Exception as e:
        print(f"Error analyzing transactions: {e}")
        return None


def get_forecast_for_week(client_id: str, start_date: str, end_date: str):
    """Get forecast data for the same week period."""
    try:
        # Get vendor configurations with forecast settings
        vendors = supabase.table('vendors') \
            .select('*') \
            .eq('client_id', client_id) \
            .not_.is_('forecast_method', 'null') \
            .execute()
        
        forecasted_deposits = 0
        forecasted_withdrawals = 0
        
        for vendor in vendors.data:
            if vendor.get('forecast_amount') and vendor.get('forecast_frequency'):
                amount = float(vendor['forecast_amount'])
                frequency = vendor['forecast_frequency']
                
                # For simplicity, assume weekly transactions for this comparison
                # In reality, you'd need to calculate based on actual frequency
                if frequency in ['weekly', 'bi-weekly', 'monthly']:
                    if amount > 0:
                        forecasted_deposits += amount
                    else:
                        forecasted_withdrawals += abs(amount)
        
        return {
            'forecasted_deposits': forecasted_deposits,
            'forecasted_withdrawals': forecasted_withdrawals,
            'forecasted_net': forecasted_deposits - forecasted_withdrawals
        }
        
    except Exception as e:
        print(f"Error getting forecast data: {e}")
        return None


def compare_actual_vs_forecast(client_id: str, start_date: str, end_date: str):
    """Compare actual transactions vs forecast for the week."""
    actual = analyze_week_transactions(client_id, start_date, end_date)
    if not actual:
        return
    
    forecast = get_forecast_for_week(client_id, start_date, end_date)
    if not forecast:
        print("\nUnable to retrieve forecast data for comparison.")
        return
    
    print(f"\n{'ACTUAL VS FORECAST COMPARISON':^80}")
    print(f"{'='*80}")
    print(f"{'Category':<20} | {'Actual':>15} | {'Forecast':>15} | {'Variance':>15}")
    print(f"{'-'*80}")
    
    # Deposits comparison
    dep_variance = actual['total_deposits'] - forecast['forecasted_deposits']
    print(f"{'Deposits':<20} | ${actual['total_deposits']:>14,.2f} | ${forecast['forecasted_deposits']:>14,.2f} | ${dep_variance:>14,.2f}")
    
    # Withdrawals comparison
    with_variance = actual['total_withdrawals'] - forecast['forecasted_withdrawals']
    print(f"{'Withdrawals':<20} | ${actual['total_withdrawals']:>14,.2f} | ${forecast['forecasted_withdrawals']:>14,.2f} | ${with_variance:>14,.2f}")
    
    # Net movement comparison
    net_variance = actual['net_movement'] - forecast['forecasted_net']
    print(f"{'Net Movement':<20} | ${actual['net_movement']:>14,.2f} | ${forecast['forecasted_net']:>14,.2f} | ${net_variance:>14,.2f}")
    
    print(f"{'-'*80}")
    
    # Calculate accuracy percentages
    if forecast['forecasted_deposits'] > 0:
        dep_accuracy = (1 - abs(dep_variance) / forecast['forecasted_deposits']) * 100
        print(f"Deposit forecast accuracy: {dep_accuracy:.1f}%")
    
    if forecast['forecasted_withdrawals'] > 0:
        with_accuracy = (1 - abs(with_variance) / forecast['forecasted_withdrawals']) * 100
        print(f"Withdrawal forecast accuracy: {with_accuracy:.1f}%")


if __name__ == "__main__":
    # Analyze the week of April 21-27, 2025 (July data not available yet)
    client_id = 'spyguy'
    start_date = '2025-04-21'
    end_date = '2025-04-27'
    
    print("Note: Analyzing April 21-27, 2025 instead of July 21-27, 2025")
    print("(July 2025 data is not yet available in the database)")
    
    compare_actual_vs_forecast(client_id, start_date, end_date)