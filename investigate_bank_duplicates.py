#!/usr/bin/env python3
"""
Investigate the supposed "duplicates" within the bank CSV export.
Banks should not export duplicate transactions.
"""

import csv
from collections import Counter, defaultdict

def investigate_bank_duplicates():
    """Investigate duplicates within the bank CSV file."""
    
    csv_path = "/Users/jeffreydebolt/Downloads/mercury_transactions.csv"
    
    print("🔍 Investigating potential duplicates in bank CSV export...")
    
    transactions = []
    duplicate_keys = []
    
    with open(csv_path, 'r') as file:
        reader = csv.DictReader(file)
        
        for row_num, row in enumerate(reader, start=2):
            # Skip failed/blocked transactions
            status = row.get("Status", "").strip().lower()
            if status in ["failed", "blocked", "cancelled", "pending"]:
                continue
            
            # Create the same key structure we use for duplicate detection
            date = row.get("Date (UTC)", "").strip()
            vendor = row.get("Description", "").strip()
            amount = row.get("Amount", "").strip()
            description = row.get("Bank Description", "").strip()
            
            # Skip invalid rows
            if not date or not vendor or not amount:
                continue
            
            transaction_key = f"{date}_{vendor}_{amount}"
            detailed_key = f"{date}_{vendor}_{amount}_{description[:50]}"
            
            transactions.append({
                'row_num': row_num,
                'date': date,
                'vendor': vendor,
                'amount': amount,
                'description': description,
                'status': row.get("Status", ""),
                'key': transaction_key,
                'detailed_key': detailed_key,
                'full_row': row
            })
    
    print(f"📊 Valid transactions found: {len(transactions)}")
    
    # Check for duplicates using simple key
    simple_keys = [t['key'] for t in transactions]
    simple_counts = Counter(simple_keys)
    simple_duplicates = {k: v for k, v in simple_counts.items() if v > 1}
    
    print(f"🔄 Simple duplicates (date+vendor+amount): {len(simple_duplicates)}")
    
    # Check for duplicates using detailed key  
    detailed_keys = [t['detailed_key'] for t in transactions]
    detailed_counts = Counter(detailed_keys)
    detailed_duplicates = {k: v for k, v in detailed_counts.items() if v > 1}
    
    print(f"🔄 Detailed duplicates (date+vendor+amount+description): {len(detailed_duplicates)}")
    
    # Analyze the duplicates in detail
    if simple_duplicates:
        print(f"\n📋 Analyzing simple duplicates:")
        for key, count in list(simple_duplicates.items())[:10]:  # Show first 10
            matching_transactions = [t for t in transactions if t['key'] == key]
            print(f"\n  Key: {key} ({count} occurrences)")
            
            for i, t in enumerate(matching_transactions):
                print(f"    {i+1}. Row {t['row_num']}: {t['status']} | {t['description']}")
                print(f"       Full description: {t['full_row'].get('Bank Description', 'N/A')}")
                print(f"       Reference: {t['full_row'].get('Reference', 'N/A')}")
                print(f"       Timestamp: {t['full_row'].get('Timestamp', 'N/A')}")
    
    # Check if these are truly identical or just similar
    print(f"\n🎯 Detailed analysis of 'duplicates':")
    
    # Group by simple key and examine differences
    grouped = defaultdict(list)
    for t in transactions:
        grouped[t['key']].append(t)
    
    true_duplicates = 0
    similar_transactions = 0
    
    for key, group in grouped.items():
        if len(group) > 1:
            # Check if they're truly identical
            first = group[0]
            are_identical = True
            
            for other in group[1:]:
                if (first['description'] != other['description'] or 
                    first['full_row'].get('Timestamp', '') != other['full_row'].get('Timestamp', '') or
                    first['full_row'].get('Reference', '') != other['full_row'].get('Reference', '')):
                    are_identical = False
                    break
            
            if are_identical:
                true_duplicates += len(group) - 1  # Count extras
                print(f"  TRUE DUPLICATE: {key} ({len(group)} identical transactions)")
                for t in group:
                    print(f"    Row {t['row_num']}: {t['full_row'].get('Timestamp', 'N/A')}")
            else:
                similar_transactions += len(group) - 1
                print(f"  SIMILAR (not duplicate): {key} ({len(group)} similar transactions)")
                for t in group:
                    print(f"    Row {t['row_num']}: {t['description'][:50]}... | {t['full_row'].get('Timestamp', 'N/A')}")
    
    print(f"\n📊 Final analysis:")
    print(f"  True duplicates: {true_duplicates}")
    print(f"  Similar transactions: {similar_transactions}")
    print(f"  Total flagged: {true_duplicates + similar_transactions}")
    
    if true_duplicates > 0:
        print(f"\n❗ ALERT: Found {true_duplicates} true duplicates in bank export!")
        print(f"   This suggests a data export issue from Mercury Bank.")
    else:
        print(f"\n✅ No true duplicates found - the 'duplicates' are actually similar but distinct transactions.")

if __name__ == "__main__":
    investigate_bank_duplicates()