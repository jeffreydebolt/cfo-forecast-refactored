#!/usr/bin/env python3
"""
Analyze actual vendor patterns to see why pattern detection is failing
"""

import sys
sys.path.append('.')

from supabase_client import supabase
from datetime import datetime
from collections import defaultdict
import statistics

# Get vendor data
result = supabase.table('transactions').select('vendor_name, amount, transaction_date').eq('client_id', 'spyguy').execute()
transactions = result.data

# Group by vendor
vendor_data = defaultdict(list)
for txn in transactions:
    vendor_data[txn['vendor_name']].append(txn)

print('TOP VENDORS WITH TRANSACTION PATTERNS:')
print('=' * 80)

# Analyze top vendors
for vendor_name, txns in sorted(vendor_data.items(), key=lambda x: len(x[1]), reverse=True)[:15]:
    if len(txns) < 3:  # Need at least 3 for pattern
        continue
    
    # Get dates and amounts
    txns_sorted = sorted(txns, key=lambda x: x['transaction_date'])
    dates = [datetime.fromisoformat(t['transaction_date']).date() for t in txns_sorted]
    amounts = [abs(float(t['amount'])) for t in txns_sorted]
    
    # Calculate gaps between consecutive transactions
    gaps = []
    for i in range(1, len(dates)):
        gap_days = (dates[i] - dates[i-1]).days
        gaps.append(gap_days)
    
    # Statistics
    avg_gap = statistics.mean(gaps) if gaps else 0
    median_gap = statistics.median(gaps) if gaps else 0
    gap_std = statistics.stdev(gaps) if len(gaps) > 1 else 0
    
    avg_amount = statistics.mean(amounts)
    amount_std = statistics.stdev(amounts) if len(amounts) > 1 else 0
    amount_cv = amount_std / avg_amount if avg_amount > 0 else 0
    
    # Pattern detection
    pattern = "UNKNOWN"
    if 6 <= avg_gap <= 8:
        pattern = "WEEKLY"
    elif 13 <= avg_gap <= 15:
        pattern = "BI-WEEKLY"
    elif 28 <= avg_gap <= 32:
        pattern = "MONTHLY"
    elif 85 <= avg_gap <= 95:
        pattern = "QUARTERLY"
    elif avg_gap < 5:
        pattern = "DAILY/FREQUENT"
    
    print(f'\n{vendor_name}:')
    print(f'  Transactions: {len(txns)}')
    print(f'  Pattern: {pattern}')
    print(f'  Avg Gap: {avg_gap:.1f} days (median: {median_gap}, std: {gap_std:.1f})')
    print(f'  Avg Amount: ${avg_amount:,.0f} (CV: {amount_cv:.1%})')
    print(f'  Recent gaps: {gaps[-5:]} days')
    print(f'  Recent amounts: ${", ".join(f"{a:,.0f}" for a in amounts[-5:])}')

print('\n\nPATTERN DETECTION ISSUES:')
print('=' * 80)
print('1. Too strict on timing - real vendors have variance')
print('2. Amount variance threshold (15%) is too tight')
print('3. Not recognizing obvious patterns like "every 2 weeks-ish"')
print('4. Should use median gap, not just average')