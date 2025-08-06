"""
Quick client summary - shows all available clients and their data status.
Run this anytime to see which clients have the most recent data.
"""

from supabase_client import supabase
from datetime import datetime
from collections import defaultdict

def quick_client_summary():
    """Quick summary of all clients and their data freshness."""
    try:
        # Get all transactions grouped by client
        result = supabase.table('transactions') \
            .select('client_id, transaction_date') \
            .execute()
        
        if not result.data:
            print("❌ No transaction data found")
            return
        
        # Group by client
        by_client = defaultdict(list)
        for txn in result.data:
            client_id = txn.get('client_id', 'UNKNOWN')
            by_client[client_id].append(txn['transaction_date'])
        
        print("🏢 CLIENT DATA SUMMARY")
        print("=" * 50)
        print(f"{'Client':<15} {'Transactions':<12} {'Latest Date':<12} {'Status'}")
        print("-" * 50)
        
        for client_id, dates in by_client.items():
            count = len(dates)
            latest = max(dates)
            days_old = (datetime.now() - datetime.strptime(latest, '%Y-%m-%d')).days
            
            if days_old <= 30:
                status = "🟢 Current"
            elif days_old <= 90:
                status = "🟡 Recent"
            elif days_old <= 180:
                status = "🟠 Older"
            else:
                status = "🔴 Old"
            
            print(f"{client_id:<15} {count:<12} {latest:<12} {status}")
        
        # Show current context
        from config.client_context import get_current_client
        current = get_current_client()
        print(f"\n✅ Currently using client: {current}")
        
        if len(by_client) == 1:
            print("💡 Only one client available - no need to switch")
        else:
            best_client = min(by_client.items(), 
                             key=lambda x: (datetime.now() - datetime.strptime(max(x[1]), '%Y-%m-%d')).days)
            print(f"💡 Client with most recent data: {best_client[0]}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    quick_client_summary()