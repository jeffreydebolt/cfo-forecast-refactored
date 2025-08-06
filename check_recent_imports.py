"""
Check recent imports and total transaction count.
"""

from supabase_client import supabase
from datetime import datetime

def check_recent_imports():
    """Check recent imports and database status."""
    try:
        print("🔍 Checking transaction database status...")
        print("=" * 60)
        
        # Get total count
        result = supabase.table('transactions').select('*', count='exact').execute()
        total_count = result.count
        print(f"📊 Total transactions in database: {total_count:,}")
        
        # Get most recently created transactions
        recent_created = supabase.table('transactions') \
            .select('*') \
            .order('created_at', desc=True) \
            .limit(10) \
            .execute()
        
        if recent_created.data:
            print(f"\n🕒 Most recently imported transactions:")
            for txn in recent_created.data:
                created_at = txn.get('created_at', 'N/A')
                if created_at != 'N/A':
                    # Parse and format the timestamp
                    try:
                        dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        created_at = dt.strftime('%Y-%m-%d %H:%M:%S UTC')
                    except:
                        pass
                
                print(f"  Created: {created_at}")
                print(f"  Date: {txn['transaction_date']} | ${txn['amount']:>10,.2f} | {txn['vendor_name']}")
                print()
        
        # Check for any transactions from today
        today = datetime.now().strftime('%Y-%m-%d')
        today_imports = supabase.table('transactions') \
            .select('*') \
            .gte('created_at', f'{today}T00:00:00') \
            .execute()
        
        if today_imports.data:
            print(f"📅 Transactions imported today ({today}): {len(today_imports.data)}")
            
            # Group by client
            clients = {}
            for txn in today_imports.data:
                client = txn['client_id']
                if client not in clients:
                    clients[client] = 0
                clients[client] += 1
            
            for client, count in clients.items():
                print(f"  • {client}: {count} transactions")
        else:
            print(f"📅 No transactions imported today ({today})")
        
        # Check if there were any recent imports that might be the 1,955 mentioned
        recent_24h = supabase.table('transactions') \
            .select('*') \
            .gte('created_at', f'{(datetime.now().replace(hour=0, minute=0, second=0)).strftime("%Y-%m-%d")}T00:00:00') \
            .execute()
        
        if recent_24h.data:
            print(f"\n📈 Recent imports (last 24h): {len(recent_24h.data)} transactions")
        
        return {
            'total_count': total_count,
            'recent_created': recent_created.data,
            'today_imports': today_imports.data if today_imports.data else []
        }
        
    except Exception as e:
        print(f"❌ Error checking imports: {e}")
        return None

if __name__ == "__main__":
    check_recent_imports()