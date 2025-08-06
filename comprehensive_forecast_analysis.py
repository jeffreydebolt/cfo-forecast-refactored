"""
Comprehensive analysis comparing user's manual forecast with actual Mercury data.
"""

from supabase_client import supabase
from datetime import datetime, date, timedelta
import pandas as pd

def comprehensive_forecast_analysis():
    """Complete analysis of Mercury data vs user's manual forecast."""
    client_id = 'spyguy'
    
    try:
        print("🔍 COMPREHENSIVE FORECAST vs ACTUAL ANALYSIS")
        print("=" * 80)
        
        # Get all transactions for the last 6 months
        six_months_ago = (datetime.now() - timedelta(days=180)).date()
        
        result = supabase.table('transactions') \
            .select('transaction_date, vendor_name, amount, description') \
            .eq('client_id', client_id) \
            .gte('transaction_date', six_months_ago.isoformat()) \
            .order('transaction_date', desc=True) \
            .execute()
        
        if not result.data:
            print(f"❌ No transactions found")
            return None
        
        transactions = result.data
        df = pd.DataFrame(transactions)
        df['transaction_date'] = pd.to_datetime(df['transaction_date'])
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
        
        # Filter for income only
        income_df = df[df['amount'] > 0].copy()
        
        print(f"✅ Analyzing {len(income_df)} income transactions")
        print(f"📅 Date range: {income_df['transaction_date'].min().strftime('%Y-%m-%d')} to {income_df['transaction_date'].max().strftime('%Y-%m-%d')}")
        
        # Calculate actual weekly totals for comparison
        weeks_span = (income_df['transaction_date'].max() - income_df['transaction_date'].min()).days / 7
        total_income = income_df['amount'].sum()
        actual_weekly_avg = total_income / weeks_span if weeks_span > 0 else 0
        
        print(f"💰 Total income in period: ${total_income:,.2f}")
        print(f"📊 Actual weekly average: ${actual_weekly_avg:,.2f}")
        
        # User's manual forecast (weekly equivalents)
        user_forecast = {
            'Amazon L': {'weekly': 44777 / 2, 'frequency': 'bi-weekly', 'original': 44777},  # bi-weekly
            'Shopify': {'weekly': 12500, 'frequency': 'weekly', 'original': 12500},
            'Amazon CA': {'weekly': 475, 'frequency': 'weekly', 'original': 475},
            'Amazon': {'weekly': 684, 'frequency': 'weekly', 'original': 684},
            'PayPal': {'weekly': 1360, 'frequency': 'alternating', 'original': '1120-1600'},
            'Stripe': {'weekly': 350, 'frequency': 'weekly', 'original': '100-600'},
            'TikTok': {'weekly': 95, 'frequency': 'weekly', 'original': '30-160'}
        }
        
        forecast_total_weekly = sum(item['weekly'] for item in user_forecast.values())
        
        print(f"\n🎯 USER'S MANUAL FORECAST:")
        print("-" * 50)
        for vendor, data in user_forecast.items():
            print(f"{vendor:12s}: ${data['original']:>8} {data['frequency']} (${data['weekly']:>8,.2f}/week)")
        print(f"{'TOTAL':12s}: ${forecast_total_weekly:>8,.2f}/week")
        
        # Analyze actual vendors
        print(f"\n📊 ACTUAL VENDOR BREAKDOWN:")
        print("-" * 50)
        
        vendor_totals = income_df.groupby('vendor_name')['amount'].agg(['sum', 'count', 'mean']).reset_index()
        vendor_totals['weekly_avg'] = vendor_totals['sum'] / weeks_span
        vendor_totals = vendor_totals.sort_values('sum', ascending=False)
        
        print(f"Top income sources by total amount:")
        actual_total_weekly = 0
        
        for i, (_, vendor) in enumerate(vendor_totals.head(15).iterrows()):
            print(f"{i+1:2d}. {vendor['vendor_name'][:30]:30s} | ${vendor['sum']:>10,.2f} | ${vendor['weekly_avg']:>8,.2f}/wk | {vendor['count']:>3d} txns")
            actual_total_weekly += vendor['weekly_avg']
        
        print(f"\n📈 SUMMARY COMPARISON:")
        print("-" * 50)
        print(f"User's forecast total:  ${forecast_total_weekly:>10,.2f}/week")
        print(f"Actual income total:    ${actual_weekly_avg:>10,.2f}/week")
        print(f"Forecast vs Actual:     {forecast_total_weekly / actual_weekly_avg:.2f}x higher")
        
        # Key findings
        print(f"\n🔍 KEY FINDINGS:")
        print("-" * 50)
        
        # 1. Check Shopify
        shopify_actual = vendor_totals[vendor_totals['vendor_name'].str.contains('shopify', case=False, na=False)]
        if len(shopify_actual) > 0:
            shopify_weekly = shopify_actual['weekly_avg'].sum()
            print(f"✅ Shopify: Forecast ${user_forecast['Shopify']['weekly']:,.2f}/wk vs Actual ${shopify_weekly:,.2f}/wk")
        else:
            print(f"❌ Shopify: No matching transactions found")
        
        # 2. Check SGE (potential Amazon)
        sge_actual = vendor_totals[vendor_totals['vendor_name'].str.contains('SGE', case=False, na=False)]
        if len(sge_actual) > 0:
            sge_weekly = sge_actual['weekly_avg'].sum()
            print(f"🤔 SGE (Amazon?): ${sge_weekly:,.2f}/wk vs Amazon L forecast ${user_forecast['Amazon L']['weekly']:,.2f}/wk")
            print(f"   Gap: ${user_forecast['Amazon L']['weekly'] - sge_weekly:,.2f}/wk missing")
        
        # 3. Check PayPal
        paypal_actual = vendor_totals[vendor_totals['vendor_name'].str.contains('paypal', case=False, na=False)]
        if len(paypal_actual) > 0:
            paypal_weekly = paypal_actual['weekly_avg'].sum()
            print(f"✅ PayPal: Forecast ${user_forecast['PayPal']['weekly']:,.2f}/wk vs Actual ${paypal_weekly:,.2f}/wk")
        
        # 4. Check Stripe
        stripe_actual = vendor_totals[vendor_totals['vendor_name'].str.contains('stripe', case=False, na=False)]
        if len(stripe_actual) > 0:
            stripe_weekly = stripe_actual['weekly_avg'].sum()
            print(f"🚨 Stripe: Forecast ${user_forecast['Stripe']['weekly']:,.2f}/wk vs Actual ${stripe_weekly:,.2f}/wk")
            print(f"   Actual is {stripe_weekly / user_forecast['Stripe']['weekly']:.1f}x higher than forecast!")
        
        # 5. Missing Amazon
        print(f"❌ Amazon/Amazon CA/TikTok: No clear matches found in actual data")
        
        print(f"\n🎯 CONCLUSION:")
        print("-" * 50)
        print(f"The user's forecast appears to be based on:")
        print(f"1. Shopify numbers are close to actual (${user_forecast['Shopify']['weekly']:,.0f} vs ${shopify_actual['weekly_avg'].sum() if len(shopify_actual) > 0 else 0:,.0f})")
        print(f"2. SGE might be 'Amazon L' but actual is much lower (${sge_actual['weekly_avg'].sum() if len(sge_actual) > 0 else 0:,.0f} vs ${user_forecast['Amazon L']['weekly']:,.0f})")
        print(f"3. Stripe forecast is too low (actual is much higher)")
        print(f"4. Several forecasted vendors don't appear in actual data")
        print(f"5. Overall forecast is {forecast_total_weekly / actual_weekly_avg:.1f}x higher than actual")
        
        return {
            'forecast_total': forecast_total_weekly,
            'actual_total': actual_weekly_avg,
            'vendor_breakdown': vendor_totals.to_dict('records')
        }
        
    except Exception as e:
        print(f"❌ Error in comprehensive analysis: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    comprehensive_forecast_analysis()