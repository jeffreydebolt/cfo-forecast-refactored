"""
Check what client IDs exist in the transactions table.
"""

from supabase_client import supabase

def check_all_clients():
    """Check what client IDs exist in the database."""
    try:
        print("🔍 Checking all client IDs in transactions table...")
        print("=" * 60)
        
        # Get distinct client IDs
        result = supabase.table('transactions') \
            .select('client_id') \
            .execute()
        
        if not result.data:
            print("❌ No transactions found in database")
            return
        
        # Count transactions by client
        client_counts = {}
        for row in result.data:
            client_id = row['client_id']
            client_counts[client_id] = client_counts.get(client_id, 0) + 1
        
        print(f"📊 Found transactions for {len(client_counts)} client(s):")
        print()
        
        for client_id, count in sorted(client_counts.items()):
            print(f"  📁 {client_id}: {count:,} transactions")
            
            # Show sample transaction for each client
            sample = supabase.table('transactions') \
                .select('transaction_date, vendor_name, amount') \
                .eq('client_id', client_id) \
                .order('transaction_date', desc=True) \
                .limit(1) \
                .execute()
            
            if sample.data:
                txn = sample.data[0]
                print(f"     Latest: {txn['transaction_date']} | ${txn['amount']:>10,.2f} | {txn['vendor_name'][:30]}")
            print()
        
        return list(client_counts.keys())
        
    except Exception as e:
        print(f"❌ Error checking clients: {e}")
        return None

if __name__ == "__main__":
    check_all_clients()