"""
Detailed analysis of the spyguy client data to understand the full date range
and recent activity.
"""

from supabase_client import supabase
from datetime import datetime, timedelta
from collections import defaultdict
import calendar

def get_detailed_transaction_analysis():
    """Get detailed analysis of all transactions."""
    try:
        print("🔍 Performing detailed transaction analysis...\n")
        
        # Get all transactions with full details
        result = supabase.table('transactions') \
            .select('transaction_date, vendor_name, amount, client_id') \
            .eq('client_id', 'spyguy') \
            .order('transaction_date', desc=False) \
            .execute()
        
        if not result.data:
            print("No transactions found")
            return
        
        transactions = result.data
        print(f"📊 Found {len(transactions)} total transactions for 'spyguy' client\n")
        
        # Analyze by date ranges
        dates = [txn['transaction_date'] for txn in transactions]
        amounts = [float(txn['amount']) for txn in transactions]
        
        # Overall statistics
        print(f"💰 Total transaction volume: ${sum(amounts):,.2f}")
        print(f"📅 Full date range: {min(dates)} to {max(dates)}")
        print(f"🕒 Days covered: {(datetime.strptime(max(dates), '%Y-%m-%d') - datetime.strptime(min(dates), '%Y-%m-%d')).days} days")
        
        # Monthly breakdown
        monthly_stats = defaultdict(list)
        for txn in transactions:
            month_key = txn['transaction_date'][:7]  # YYYY-MM format
            monthly_stats[month_key].append(float(txn['amount']))
        
        print(f"\n📈 Monthly Transaction Summary:")
        print(f"{'Month':<10} {'Count':<8} {'Total Amount':<15} {'Avg Amount':<12}")
        print("-" * 50)
        
        # Sort months chronologically
        sorted_months = sorted(monthly_stats.keys())
        recent_months = []
        
        for month in sorted_months:
            amounts_month = monthly_stats[month]
            count = len(amounts_month)
            total = sum(amounts_month)
            avg = total / count if count > 0 else 0
            
            # Mark recent months (2024 onwards)
            if month >= '2024-01':
                recent_months.append(month)
                marker = "🟢"
            elif month >= '2023-01':
                marker = "🟡"
            else:
                marker = "🔴"
            
            print(f"{month:<10} {count:<8} ${total:<14,.2f} ${avg:<11,.2f} {marker}")
        
        # Recent activity analysis
        print(f"\n🚀 Recent Activity Analysis:")
        if recent_months:
            print(f"✅ Found activity in {len(recent_months)} months since 2024:")
            for month in recent_months[-6:]:  # Show last 6 recent months
                count = len(monthly_stats[month])
                total = sum(monthly_stats[month])
                print(f"   {month}: {count} transactions, ${total:,.2f}")
                
            # Most recent transactions
            recent_txns = [txn for txn in transactions if txn['transaction_date'] >= '2025-01-01']
            if recent_txns:
                print(f"\n🔥 Most Recent Transactions (2025):")
                print(f"{'Date':<12} {'Amount':<12} {'Vendor'}")
                print("-" * 60)
                for txn in recent_txns[-10:]:  # Show last 10
                    print(f"{txn['transaction_date']:<12} ${float(txn['amount']):<11,.2f} {txn['vendor_name'][:35]}")
        else:
            print("❌ No activity found since 2024")
        
        # Weekly analysis for recent period
        if recent_months:
            latest_month = max(recent_months)
            latest_month_txns = [txn for txn in transactions if txn['transaction_date'].startswith(latest_month)]
            
            print(f"\n📅 Latest Month Activity ({latest_month}):")
            print(f"   Transactions: {len(latest_month_txns)}")
            print(f"   Total Amount: ${sum(float(txn['amount']) for txn in latest_month_txns):,.2f}")
            
            # Show some recent transactions
            print(f"\n   Recent transactions in {latest_month}:")
            for txn in latest_month_txns[-5:]:
                print(f"   {txn['transaction_date']} | ${float(txn['amount']):>10,.2f} | {txn['vendor_name'][:40]}")
        
        # Vendor analysis for recent period
        recent_vendors = defaultdict(list)
        for txn in [t for t in transactions if t['transaction_date'] >= '2024-01-01']:
            recent_vendors[txn['vendor_name']].append(float(txn['amount']))
        
        if recent_vendors:
            print(f"\n🏪 Top Vendors (2024+):")
            vendor_totals = [(vendor, sum(amounts), len(amounts)) for vendor, amounts in recent_vendors.items()]
            vendor_totals.sort(key=lambda x: abs(x[1]), reverse=True)
            
            print(f"{'Vendor':<40} {'Total':<12} {'Count'}")
            print("-" * 60)
            for vendor, total, count in vendor_totals[:10]:
                print(f"{vendor[:39]:<40} ${total:<11,.2f} {count}")
        
        return {
            'total_transactions': len(transactions),
            'date_range': (min(dates), max(dates)),
            'recent_activity': len(recent_months) > 0,
            'latest_transaction': max(dates),
            'recent_transaction_count': len([d for d in dates if d >= '2024-01-01'])
        }
        
    except Exception as e:
        print(f"Error in detailed analysis: {e}")
        return None

def main():
    """Main function."""
    print("=" * 80)
    print("DETAILED ANALYSIS OF SPYGUY CLIENT DATA")
    print("=" * 80)
    
    analysis = get_detailed_transaction_analysis()
    
    if analysis:
        print(f"\n" + "=" * 80)
        print("FINAL RECOMMENDATION")
        print("=" * 80)
        
        if analysis['recent_activity']:
            print("✅ GOOD NEWS: The 'spyguy' client has recent transaction data!")
            print(f"   • Latest transaction: {analysis['latest_transaction']}")
            print(f"   • Recent transactions (2024+): {analysis['recent_transaction_count']}")
            print(f"   • Total transactions: {analysis['total_transactions']}")
            print(f"\n🎯 RECOMMENDATION: Continue using 'spyguy' client")
            print("   This client has sufficient recent data for forecasting.")
        else:
            print("⚠️  The 'spyguy' client data is outdated")
            print(f"   • Latest transaction: {analysis['latest_transaction']}")
            print("   • Consider importing more recent data")
        
        print(f"\n📝 Current client context: spyguy")
        print(f"💡 No need to switch clients - this is the only available client with data")

if __name__ == "__main__":
    main()