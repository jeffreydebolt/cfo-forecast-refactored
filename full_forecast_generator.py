#!/usr/bin/env python3
"""
Full Forecast Generator - Combines auto + manual forecasts
Creates a complete forecast view with all vendors
"""

import sys
sys.path.append('.')

from supabase_client import supabase
from datetime import datetime, date, timedelta
from collections import defaultdict
import random

def generate_full_forecast_data(client_id: str = 'spyguy'):
    """Generate complete forecast data for testing"""
    
    print("🔮 GENERATING FULL FORECAST DATA")
    print("=" * 80)
    
    # Get all regular vendors
    result = supabase.table('transactions').select('vendor_name, amount, transaction_date')\
        .eq('client_id', client_id)\
        .execute()
    
    transactions = result.data
    
    # Group by vendor
    vendor_data = defaultdict(list)
    for txn in transactions:
        vendor_data[txn['vendor_name']].append(txn)
    
    # Filter for regular vendors (2+ transactions)
    regular_vendors = {}
    for vendor_name, txns in vendor_data.items():
        if len(txns) >= 2:
            # Calculate average amount and frequency
            amounts = [abs(float(t['amount'])) for t in txns]
            avg_amount = sum(amounts) / len(amounts)
            
            # Simple frequency detection
            dates = sorted([datetime.fromisoformat(t['transaction_date']).date() for t in txns])
            if len(dates) >= 2:
                gaps = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
                avg_gap = sum(gaps) / len(gaps)
            else:
                avg_gap = 30  # Default monthly
            
            regular_vendors[vendor_name] = {
                'avg_amount': avg_amount,
                'avg_gap_days': avg_gap,
                'transaction_count': len(txns),
                'is_revenue': avg_amount > 0 if any(float(t['amount']) > 0 for t in txns) else False
            }
    
    print(f"📊 Found {len(regular_vendors)} regular vendors")
    
    # Generate forecasts for next 13 weeks
    forecast_records = []
    today = date.today()
    
    for vendor_name, vendor_info in regular_vendors.items():
        # Determine forecast frequency
        gap_days = vendor_info['avg_gap_days']
        
        if gap_days <= 7:
            frequency = 'weekly'
            interval_days = 7
        elif gap_days <= 15:
            frequency = 'bi_weekly'
            interval_days = 14
        elif gap_days <= 35:
            frequency = 'monthly'
            interval_days = 30
        else:
            frequency = 'irregular'
            interval_days = int(gap_days)
        
        # Generate forecast dates
        current_date = today
        for i in range(int(91 / interval_days)):  # 91 days = 13 weeks
            current_date += timedelta(days=interval_days)
            
            # Add some variance to amounts
            base_amount = vendor_info['avg_amount']
            variance = random.uniform(0.9, 1.1)  # +/- 10% variance
            forecast_amount = base_amount * variance
            
            # Make it negative if it's an expense
            if not vendor_info['is_revenue']:
                forecast_amount = -abs(forecast_amount)
            
            forecast_records.append({
                'client_id': client_id,
                'vendor_group_name': vendor_name,
                'forecast_date': current_date.isoformat(),
                'forecast_amount': forecast_amount,
                'forecast_type': 'scheduled',
                'forecast_method': 'generated',
                'pattern_confidence': 0.8 if frequency != 'irregular' else 0.5,
                'is_locked': False,
                'is_manual_override': False
            })
    
    print(f"✅ Generated {len(forecast_records)} forecast records")
    
    # Clear existing forecasts
    supabase.table('forecasts').delete().eq('client_id', client_id).execute()
    
    # Insert new forecasts in batches
    batch_size = 100
    for i in range(0, len(forecast_records), batch_size):
        batch = forecast_records[i:i+batch_size]
        supabase.table('forecasts').insert(batch).execute()
    
    print(f"💾 Saved {len(forecast_records)} forecasts to database")
    
    # Get actual bank balance
    bank_balance = get_current_bank_balance(client_id)
    print(f"💰 Current bank balance: ${bank_balance:,.0f}")
    
    return {
        'vendor_count': len(regular_vendors),
        'forecast_count': len(forecast_records),
        'bank_balance': bank_balance
    }

def get_current_bank_balance(client_id: str) -> float:
    """Get actual bank balance from transactions"""
    # For now, calculate from all transactions
    result = supabase.table('transactions').select('amount')\
        .eq('client_id', client_id)\
        .execute()
    
    if result.data:
        total = sum(float(txn['amount']) for txn in result.data)
        # Start with a base amount and add transaction total
        return 50000 + total  # Base $50k + net transactions
    else:
        return 50000  # Default

def main():
    """Generate full forecast data"""
    results = generate_full_forecast_data('spyguy')
    
    print(f"\n🎯 FORECAST GENERATION COMPLETE")
    print(f"Vendors: {results['vendor_count']}")
    print(f"Forecasts: {results['forecast_count']}")
    print(f"Bank Balance: ${results['bank_balance']:,.0f}")
    print(f"\n✅ Now run integrated_forecast_display.py to see the full view")

if __name__ == "__main__":
    main()