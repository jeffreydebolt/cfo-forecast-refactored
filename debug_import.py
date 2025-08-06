#!/usr/bin/env python3
"""
Debug the CSV import process to see what's really happening.
"""

from importers.factory import import_csv_file

def debug_import():
    """Debug the CSV import process."""
    
    csv_path = "/Users/jeffreydebolt/Downloads/mercury_transactions.csv"
    client_id = "bestself"
    
    print(f"🔍 Debugging CSV import for: {csv_path}")
    print(f"🏢 Client: {client_id}")
    
    # Parse the CSV
    result = import_csv_file(csv_path, client_id)
    
    summary = result.get_summary()
    print(f"\n📊 Import Result Summary:")
    print(f"  Success: {summary['success']}")
    print(f"  Transactions parsed: {summary['transactions_imported']}")
    print(f"  Errors: {summary['errors']}")
    print(f"  Warnings: {summary['warnings']}")
    print(f"  Skipped rows: {summary['skipped_rows']}")
    
    if result.errors:
        print(f"\n❌ Errors:")
        for error in result.errors[:10]:
            print(f"  - {error}")
    
    if result.warnings:
        print(f"\n⚠️ Warnings:")
        for warning in result.warnings[:10]:
            print(f"  - {warning}")
    
    print(f"\n📄 Sample parsed transactions:")
    for i, transaction in enumerate(result.transactions[:5]):
        print(f"  {i+1}. {transaction.date} | {transaction.vendor_name} | ${transaction.amount}")
    
    print(f"\n📈 Parsed transaction count: {len(result.transactions)}")
    
    # Check for duplicate transaction data in the parsed results
    from collections import Counter
    transaction_keys = []
    for t in result.transactions:
        key = f"{t.date.strftime('%Y-%m-%d')}_{t.vendor_name}_{t.amount}"
        transaction_keys.append(key)
    
    key_counts = Counter(transaction_keys)
    duplicates_in_parsed = {k: v for k, v in key_counts.items() if v > 1}
    
    print(f"\n🔄 Duplicates found in parsed data: {len(duplicates_in_parsed)}")
    if duplicates_in_parsed:
        print("Examples:")
        for key, count in list(duplicates_in_parsed.items())[:5]:
            print(f"  - {key}: {count} times")

if __name__ == "__main__":
    debug_import()