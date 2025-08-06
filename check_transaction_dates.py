"""
Check what transaction dates are available in the database.
"""

from supabase_client import supabase
from config.client_context import get_current_client

def check_transaction_dates(client_id: str):
    """Check available transaction dates for a client."""
    try:
        # Get all transactions and their dates
        result = supabase.table('transactions') \
            .select('transaction_date, vendor_name, amount') \
            .eq('client_id', client_id) \
            .order('transaction_date', desc=True) \
            .execute()
        
        if not result.data:
            print(f"No transactions found for client: {client_id}")
            return
        
        print(f"Found {len(result.data)} transactions for client: {client_id}")
        print("\nMost recent transactions:")
        for i, txn in enumerate(result.data[:20]):  # Show first 20
            print(f"{txn['transaction_date']} | ${txn['amount']:>10,.2f} | {txn['vendor_name'][:50]}")
        
        # Show date range
        dates = [txn['transaction_date'] for txn in result.data]
        print(f"\nDate range: {min(dates)} to {max(dates)}")
        
        # Show transactions around July 2025
        july_transactions = [txn for txn in result.data if txn['transaction_date'].startswith('2025-07')]
        if july_transactions:
            print(f"\nJuly 2025 transactions ({len(july_transactions)} found):")
            for txn in july_transactions:
                print(f"{txn['transaction_date']} | ${txn['amount']:>10,.2f} | {txn['vendor_name']}")
        else:
            print("\nNo July 2025 transactions found.")
            
        return result.data
        
    except Exception as e:
        print(f"Error checking transactions: {e}")
        return None

if __name__ == "__main__":
    check_transaction_dates('spyguy')