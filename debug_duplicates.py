#!/usr/bin/env python3
"""
Debug the duplicate detection issue.
"""

from supabase_client import supabase
from services.transaction_service import TransactionService
from importers.factory import import_csv_file
import hashlib
from collections import Counter

def debug_duplicate_detection():
    """Debug why we're getting so many duplicates."""
    
    print("🔍 Debugging duplicate detection...")
    
    # Check what's actually in the database for bestself
    result = supabase.table('transactions').select('*').eq('client_id', 'bestself').execute()
    print(f"📊 Current bestself transactions in DB: {len(result.data)}")
    
    if result.data:
        # Check transaction_id distribution
        transaction_ids = [t['transaction_id'] for t in result.data]
        id_counts = Counter(transaction_ids)
        duplicated_ids = {k: v for k, v in id_counts.items() if v > 1}
        
        print(f"🔄 Duplicate transaction_ids in DB: {len(duplicated_ids)}")
        if duplicated_ids:
            print("Examples of duplicated IDs:")
            for tid, count in list(duplicated_ids.items())[:5]:
                print(f"  - {tid}: {count} times")
        
        # Check date range
        dates = [t['transaction_date'] for t in result.data]
        print(f"📅 Date range: {min(dates)} to {max(dates)}")
        
        # Check for actual duplicate transactions (same date, vendor, amount)
        transaction_keys = []
        for t in result.data:
            key = f"{t['transaction_date']}_{t['vendor_name']}_{t['amount']}"
            transaction_keys.append(key)
        
        key_counts = Counter(transaction_keys)
        actual_dups = {k: v for k, v in key_counts.items() if v > 1}
        print(f"🎯 Actual business duplicates: {len(actual_dups)}")
        
        if actual_dups:
            print("Examples of business duplicates:")
            for key, count in list(actual_dups.items())[:5]:
                print(f"  - {key}: {count} times")
    
    # Now test the duplicate detection logic with a few sample transactions
    print(f"\n🧪 Testing duplicate detection logic...")
    
    # Test the transaction ID generation
    from importers.base import TransactionData
    from datetime import datetime
    
    sample_transaction = TransactionData(
        date=datetime(2025, 7, 28),
        vendor_name="SHOPIFY",
        amount=100.00,
        description="Test transaction"
    )
    
    # Generate transaction ID
    service = TransactionService()
    client_id = "bestself"
    key_string = f"{client_id}_{sample_transaction.date.strftime('%Y-%m-%d')}_{sample_transaction.vendor_name}_{sample_transaction.amount}_{sample_transaction.description[:50]}"
    transaction_id = hashlib.md5(key_string.encode()).hexdigest()
    
    print(f"Sample transaction ID generation:")
    print(f"  Key string: {key_string}")
    print(f"  Transaction ID: {transaction_id}")
    
    # Check if this ID exists
    existing = supabase.table('transactions').select('id').eq('transaction_id', transaction_id).execute()
    print(f"  Exists in DB: {len(existing.data) > 0}")

if __name__ == "__main__":
    debug_duplicate_detection()