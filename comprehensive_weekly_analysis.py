"""
Comprehensive weekly analysis and forecast accuracy assessment.
"""

import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict
from supabase_client import supabase
from config.client_context import get_current_client


def get_most_recent_complete_week(client_id: str):
    """Find the most recent complete week of data."""
    try:
        # Get the most recent transaction date
        result = supabase.table('transactions') \
            .select('transaction_date') \
            .eq('client_id', client_id) \
            .order('transaction_date', desc=True) \
            .limit(1) \
            .execute()
        
        if not result.data:
            return None
        
        latest_date = datetime.strptime(result.data[0]['transaction_date'], '%Y-%m-%d')
        
        # Find the most recent complete week (ending on the latest date or before)
        # Go back to find a Monday
        days_back = latest_date.weekday()  # 0 = Monday, 6 = Sunday
        week_start = latest_date - timedelta(days=days_back + 7)  # Go back one full week
        week_end = week_start + timedelta(days=6)
        
        return week_start.strftime('%Y-%m-%d'), week_end.strftime('%Y-%m-%d')
        
    except Exception as e:
        print(f"Error finding recent week: {e}")
        return None


def analyze_forecast_accuracy(client_id: str, start_date: str, end_date: str):
    """Comprehensive forecast accuracy analysis."""
    
    print(f"\n{'='*120}")
    print(f"COMPREHENSIVE WEEKLY ANALYSIS & FORECAST ACCURACY ASSESSMENT")
    print(f"Client: {client_id}")
    print(f"Analysis Period: {start_date} to {end_date}")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*120}")
    
    try:
        # Get actual transactions
        result = supabase.table('transactions') \
            .select('*') \
            .eq('client_id', client_id) \
            .gte('transaction_date', start_date) \
            .lte('transaction_date', end_date) \
            .order('transaction_date') \
            .execute()
        
        if not result.data:
            print("❌ No transactions found for this period.")
            return None
        
        # Get vendor mappings and forecast data
        vendor_result = supabase.table('vendors') \
            .select('*') \
            .eq('client_id', client_id) \
            .execute()
        
        vendor_map = {}
        forecast_data = {}
        
        for vendor in vendor_result.data:
            display_name = vendor.get('display_name')
            if display_name:
                # Map vendor names to display names
                if vendor.get('vendor_name'):
                    vendor_map[vendor['vendor_name']] = display_name
                if vendor.get('normalized_name'):
                    vendor_map[vendor['normalized_name']] = display_name
                
                # Store forecast configuration
                if vendor.get('forecast_amount') is not None:
                    forecast_data[display_name] = {
                        'amount': float(vendor['forecast_amount']),
                        'frequency': vendor.get('forecast_frequency', 'monthly'),
                        'method': vendor.get('forecast_method', 'unknown'),
                        'confidence': vendor.get('confidence_level', 0.5)
                    }
        
        # Process actual transactions
        actual_by_vendor = defaultdict(lambda: {'deposits': 0, 'withdrawals': 0, 'net': 0, 'count': 0})
        
        for txn in result.data:
            amount = float(txn['amount'])
            vendor_name = txn.get('vendor_name', 'Unknown')
            display_name = vendor_map.get(vendor_name, vendor_name)
            
            if amount > 0:
                actual_by_vendor[display_name]['deposits'] += amount
            else:
                actual_by_vendor[display_name]['withdrawals'] += abs(amount)
            
            actual_by_vendor[display_name]['net'] += amount
            actual_by_vendor[display_name]['count'] += 1
        
        # Calculate forecast vs actual
        print(f"\n{'FORECAST ACCURACY BY VENDOR':^120}")
        print(f"{'='*120}")
        print(f"{'Vendor':<30} | {'Actual Net':>12} | {'Forecast':>12} | {'Variance':>12} | {'Accuracy':>10} | {'Confidence':>10}")
        print(f"{'-'*120}")
        
        total_actual_net = 0
        total_forecast_net = 0
        accurate_forecasts = 0
        total_forecasts = 0
        
        # Sort by absolute actual amount
        sorted_vendors = sorted(
            actual_by_vendor.items(),
            key=lambda x: abs(x[1]['net']),
            reverse=True
        )
        
        for vendor_name, actual_data in sorted_vendors:
            actual_net = actual_data['net']
            total_actual_net += actual_net
            
            if vendor_name in forecast_data:
                forecast_config = forecast_data[vendor_name]
                weekly_forecast = calculate_weekly_forecast(forecast_config)
                total_forecast_net += weekly_forecast
                
                variance = actual_net - weekly_forecast
                
                # Calculate accuracy (higher is better)
                if weekly_forecast != 0:
                    accuracy = max(0, (1 - abs(variance) / abs(weekly_forecast)) * 100)
                else:
                    accuracy = 100 if actual_net == 0 else 0
                
                # Count as accurate if within 20% or within $500
                is_accurate = (abs(variance) / max(abs(weekly_forecast), 1) < 0.2) or (abs(variance) < 500)
                if is_accurate:
                    accurate_forecasts += 1
                total_forecasts += 1
                
                confidence = forecast_config.get('confidence', 0.5) * 100
                
                print(f"{vendor_name[:29]:<30} | ${actual_net:>11,.2f} | ${weekly_forecast:>11,.2f} | ${variance:>11,.2f} | {accuracy:>9.1f}% | {confidence:>9.1f}%")
            else:
                print(f"{vendor_name[:29]:<30} | ${actual_net:>11,.2f} | {'N/A':>12} | {'N/A':>12} | {'N/A':>10} | {'N/A':>10}")
        
        print(f"{'-'*120}")
        total_variance = total_actual_net - total_forecast_net
        
        if total_forecast_net != 0:
            overall_accuracy = max(0, (1 - abs(total_variance) / abs(total_forecast_net)) * 100)
        else:
            overall_accuracy = 0
        
        print(f"{'TOTALS':<30} | ${total_actual_net:>11,.2f} | ${total_forecast_net:>11,.2f} | ${total_variance:>11,.2f} | {overall_accuracy:>9.1f}% | {'':>10}")
        
        # Summary statistics
        print(f"\n{'FORECAST PERFORMANCE SUMMARY':^120}")
        print(f"{'='*120}")
        
        if total_forecasts > 0:
            forecast_hit_rate = (accurate_forecasts / total_forecasts) * 100
            print(f"Vendors with Forecasts:     {total_forecasts:>3}")
            print(f"Accurate Forecasts:         {accurate_forecasts:>3} ({forecast_hit_rate:.1f}%)")
            print(f"Overall Forecast Accuracy:  {overall_accuracy:>6.1f}%")
        else:
            print("❌ No forecasts available for comparison")
        
        print(f"Total Transactions:         {len(result.data):>3}")
        print(f"Unique Vendors:             {len(actual_by_vendor):>3}")
        
        # Breakdown by transaction type
        total_deposits = sum(data['deposits'] for data in actual_by_vendor.values())
        total_withdrawals = sum(data['withdrawals'] for data in actual_by_vendor.values())
        
        print(f"\nActual Cash Flow:")
        print(f"  Total Deposits:     ${total_deposits:>13,.2f}")
        print(f"  Total Withdrawals:  ${total_withdrawals:>13,.2f}")
        print(f"  Net Movement:       ${total_actual_net:>13,.2f}")
        
        # Top movers analysis
        print(f"\n{'TOP 5 CASH FLOW CONTRIBUTORS':^120}")
        print(f"{'='*120}")
        print(f"{'Vendor':<30} | {'Deposits':>12} | {'Withdrawals':>12} | {'Net Impact':>12} | {'# Txns':>8}")
        print(f"{'-'*120}")
        
        for vendor_name, data in sorted_vendors[:5]:
            print(f"{vendor_name[:29]:<30} | ${data['deposits']:>11,.2f} | ${data['withdrawals']:>11,.2f} | ${data['net']:>11,.2f} | {data['count']:>8}")
        
        # Recommendations
        print(f"\n{'FORECAST IMPROVEMENT RECOMMENDATIONS':^120}")
        print(f"{'='*120}")
        
        if overall_accuracy < 70:
            print("🔴 POOR FORECAST ACCURACY - Immediate attention needed")
            print("   • Review vendor mapping and categorization")
            print("   • Update forecast amounts based on recent trends")
            print("   • Consider seasonal adjustments")
        elif overall_accuracy < 85:
            print("🟡 MODERATE FORECAST ACCURACY - Room for improvement")
            print("   • Fine-tune forecast amounts for major vendors")
            print("   • Review frequency assumptions")
        else:
            print("🟢 GOOD FORECAST ACCURACY - Minor adjustments needed")
            print("   • Continue monitoring for drift")
            print("   • Consider confidence level adjustments")
        
        # Missing forecasts
        vendors_without_forecasts = [v for v in actual_by_vendor.keys() if v not in forecast_data]
        if vendors_without_forecasts:
            print(f"\n⚠️  VENDORS WITHOUT FORECASTS ({len(vendors_without_forecasts)}):")
            for vendor in sorted(vendors_without_forecasts, key=lambda x: abs(actual_by_vendor[x]['net']), reverse=True)[:10]:
                net = actual_by_vendor[vendor]['net']
                print(f"   • {vendor[:40]} (${net:,.2f} impact)")
        
        return {
            'period': f"{start_date} to {end_date}",
            'total_actual_net': total_actual_net,
            'total_forecast_net': total_forecast_net,
            'overall_accuracy': overall_accuracy,
            'forecast_hit_rate': forecast_hit_rate if total_forecasts > 0 else 0,
            'vendors_analyzed': len(actual_by_vendor),
            'vendors_with_forecasts': total_forecasts,
            'transactions_count': len(result.data)
        }
        
    except Exception as e:
        print(f"❌ Error in analysis: {e}")
        return None


def calculate_weekly_forecast(forecast_config):
    """Calculate weekly forecast amount based on frequency."""
    amount = forecast_config['amount']
    frequency = forecast_config['frequency']
    
    if frequency == 'weekly':
        return amount
    elif frequency == 'bi-weekly':
        return amount / 2
    elif frequency == 'monthly':
        return amount / 4.33  # Average weeks per month
    elif frequency == 'quarterly':
        return amount / 13  # Approximate weeks per quarter
    elif frequency == 'annually':
        return amount / 52
    else:
        return amount  # Default to weekly


if __name__ == "__main__":
    client_id = 'spyguy'
    
    # Find the most recent complete week
    recent_week = get_most_recent_complete_week(client_id)
    
    if recent_week:
        start_date, end_date = recent_week
        print(f"📊 Analyzing most recent complete week: {start_date} to {end_date}")
    else:
        # Fallback to specific week
        start_date = '2025-04-21'
        end_date = '2025-04-27'
        print(f"📊 Using fallback week: {start_date} to {end_date}")
    
    analysis_result = analyze_forecast_accuracy(client_id, start_date, end_date)
    
    if analysis_result:
        print(f"\n✅ Analysis completed successfully!")
        print(f"📈 Overall forecast accuracy: {analysis_result['overall_accuracy']:.1f}%")
    else:
        print(f"\n❌ Analysis failed - please check the data and try again.")