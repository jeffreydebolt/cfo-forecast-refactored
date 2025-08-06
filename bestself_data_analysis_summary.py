"""
Summary analysis of BestSelf transaction data availability.
"""

from supabase_client import supabase
from datetime import datetime
import pandas as pd

def generate_bestself_analysis_summary():
    """Generate a comprehensive summary of BestSelf data availability."""
    print("🔍 BESTSELF TRANSACTION DATA ANALYSIS SUMMARY")
    print("=" * 80)
    
    try:
        # Check all clients in database
        result = supabase.table('transactions').select('client_id').execute()
        client_counts = {}
        for row in result.data:
            client_id = row['client_id']
            client_counts[client_id] = client_counts.get(client_id, 0) + 1
        
        print("📊 CURRENT DATABASE STATUS:")
        print(f"   Total transactions: {sum(client_counts.values()):,}")
        print(f"   Clients in database: {list(client_counts.keys())}")
        for client_id, count in client_counts.items():
            print(f"   • {client_id}: {count:,} transactions")
        
        # Get date range for main client
        main_client = max(client_counts, key=client_counts.get)
        date_result = supabase.table('transactions') \
            .select('transaction_date') \
            .eq('client_id', main_client) \
            .order('transaction_date') \
            .execute()
        
        if date_result.data:
            dates = [row['transaction_date'] for row in date_result.data]
            print(f"\n📅 DATE RANGE FOR {main_client.upper()}:")
            print(f"   From: {min(dates)}")
            print(f"   To:   {max(dates)}")
        
        # Check for July 2025 specifically
        july_2025_result = supabase.table('transactions') \
            .select('transaction_date, vendor_name, amount') \
            .gte('transaction_date', '2025-07-01') \
            .lt('transaction_date', '2025-08-01') \
            .execute()
        
        print(f"\n🎯 JULY 2025 DATA AVAILABILITY:")
        if july_2025_result.data:
            print(f"   ✅ Found {len(july_2025_result.data)} transactions in July 2025")
            
            # Check for specific week July 21-27, 2025
            week_transactions = []
            for txn in july_2025_result.data:
                txn_date = datetime.strptime(txn['transaction_date'], '%Y-%m-%d').date()
                if datetime(2025, 7, 21).date() <= txn_date <= datetime(2025, 7, 27).date():
                    week_transactions.append(txn)
            
            if week_transactions:
                print(f"   🎯 Week 7/21-7/27/2025: {len(week_transactions)} transactions found")
                
                total_inflow = sum(t['amount'] for t in week_transactions if t['amount'] > 0)
                total_outflow = abs(sum(t['amount'] for t in week_transactions if t['amount'] < 0))
                
                print(f"   💰 Week Summary:")
                print(f"      Inflow:  ${total_inflow:>12,.2f}")
                print(f"      Outflow: ${total_outflow:>12,.2f}")
                print(f"      Net:     ${total_inflow - total_outflow:>12,.2f}")
            else:
                print(f"   ❌ No transactions found for week 7/21-7/27/2025")
        else:
            print(f"   ❌ No July 2025 data found in database")
        
        # Show what we need for July 2025 analysis
        print(f"\n📋 REQUIREMENTS FOR JULY 2025 ANALYSIS:")
        print(f"   • Target week: July 21-27, 2025")
        print(f"   • Current status: {'✅ Available' if july_2025_result.data else '❌ Missing'}")
        
        if not july_2025_result.data:
            print(f"\n💡 NEXT STEPS:")
            print(f"   1. Import BestSelf transaction data for July 2025")
            print(f"   2. Ensure transactions are tagged with correct client_id")
            print(f"   3. Verify data includes the target week (7/21-7/27/2025)")
            print(f"   4. Run weekly analysis once data is available")
            
            # Show latest available data
            latest_result = supabase.table('transactions') \
                .select('transaction_date') \
                .eq('client_id', main_client) \
                .order('transaction_date', desc=True) \
                .limit(1) \
                .execute()
            
            if latest_result.data:
                latest_date = latest_result.data[0]['transaction_date']
                print(f"\n📈 LATEST AVAILABLE DATA:")
                print(f"   Most recent transaction: {latest_date}")
                
                # Calculate gap
                latest_dt = datetime.strptime(latest_date, '%Y-%m-%d')
                target_dt = datetime(2025, 7, 21)
                gap_days = (target_dt - latest_dt).days
                
                if gap_days > 0:
                    print(f"   Gap to target week: {gap_days} days")
                    print(f"   Missing months: {gap_days // 30} months approximately")
        
        return {
            'has_july_2025_data': bool(july_2025_result.data),
            'has_target_week': bool(july_2025_result.data and any(
                datetime(2025, 7, 21).date() <= datetime.strptime(t['transaction_date'], '%Y-%m-%d').date() <= datetime(2025, 7, 27).date()
                for t in july_2025_result.data
            )),
            'total_transactions': sum(client_counts.values()),
            'clients': list(client_counts.keys())
        }
        
    except Exception as e:
        print(f"❌ Error generating summary: {e}")
        return None

if __name__ == "__main__":
    result = generate_bestself_analysis_summary()
    if result:
        print(f"\n{'='*80}")
        print(f"✅ Analysis complete. Ready for July 2025 data: {'Yes' if result['has_target_week'] else 'No'}")
    else:
        print(f"\n❌ Analysis failed.")