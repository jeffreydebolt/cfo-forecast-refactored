#!/usr/bin/env python3
"""
Remove duplicate transactions from the database.
"""

from supabase_client import supabase
from collections import defaultdict

def deduplicate_transactions(client_id='spyguy', dry_run=True):
    """Remove duplicate transactions based on date, amount, and vendor."""
    
    print(f"🔍 Finding duplicate transactions for client: {client_id}")
    
    # Get all transactions (Supabase has a 1000 row limit by default)
    all_transactions = []
    page_size = 1000
    offset = 0
    
    while True:
        result = supabase.table('transactions') \
            .select('*') \
            .eq('client_id', client_id) \
            .range(offset, offset + page_size - 1) \
            .execute()
        
        if not result.data:
            break
            
        all_transactions.extend(result.data)
        offset += page_size
        
        if len(result.data) < page_size:
            break
    
    print(f"📊 Total transactions: {len(all_transactions)}")
    
    # Group transactions by (date, amount, vendor_name) to find duplicates
    groups = defaultdict(list)
    
    for transaction in all_transactions:
        key = (
            transaction['transaction_date'],
            transaction['amount'],
            transaction['vendor_name']
        )
        groups[key].append(transaction)
    
    # Find duplicates
    duplicates_to_remove = []
    unique_transactions = len(groups)
    total_duplicates = 0
    
    for key, transactions in groups.items():
        if len(transactions) > 1:
            # Keep the first transaction, mark others for removal
            for duplicate in transactions[1:]:
                duplicates_to_remove.append(duplicate['id'])
                total_duplicates += 1
    
    print(f"📈 Unique transaction groups: {unique_transactions}")
    print(f"🔄 Duplicate transactions found: {total_duplicates}")
    print(f"📉 After deduplication: {len(all_transactions) - total_duplicates} transactions")
    
    if not duplicates_to_remove:
        print("✅ No duplicates found!")
        return
    
    if dry_run:
        print(f"\n🔬 DRY RUN - Would remove {len(duplicates_to_remove)} duplicate transactions")
        
        # Show some examples
        print("\nExample duplicates that would be removed:")
        for i, duplicate_id in enumerate(duplicates_to_remove[:10]):
            # Find the transaction details
            for txn in all_transactions:
                if txn['id'] == duplicate_id:
                    print(f"  {txn['transaction_date']} | ${txn['amount']} | {txn['vendor_name']}")
                    break
        
        if len(duplicates_to_remove) > 10:
            print(f"  ... and {len(duplicates_to_remove) - 10} more")
            
        print(f"\nTo actually remove duplicates, run with: dry_run=False")
        
    else:
        print(f"\n🗑️  Removing {len(duplicates_to_remove)} duplicate transactions...")
        
        # Remove duplicates in batches
        batch_size = 100
        removed_count = 0
        
        for i in range(0, len(duplicates_to_remove), batch_size):
            batch = duplicates_to_remove[i:i + batch_size]
            
            try:
                result = supabase.table('transactions').delete().in_('id', batch).execute()
                removed_count += len(batch)
                print(f"  Removed batch {i//batch_size + 1}: {removed_count}/{len(duplicates_to_remove)}")
                
            except Exception as e:
                print(f"  ❌ Error removing batch {i//batch_size + 1}: {e}")
                break
        
        print(f"✅ Successfully removed {removed_count} duplicate transactions")

if __name__ == "__main__":
    # First run in dry-run mode to see what would be removed
    deduplicate_transactions(dry_run=True)