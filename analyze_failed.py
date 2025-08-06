#!/usr/bin/env python3
"""
Analyze failed transactions in Mercury CSV
"""

import csv

def analyze_failed_transactions():
    with open('BS_mercury_transactions.csv', 'r') as f:
        reader = csv.DictReader(f)
        failed = []
        total_count = 0
        
        for row in reader:
            total_count += 1
            if row.get('Status') == 'Failed':
                failed.append({
                    'date': row['Date (UTC)'],
                    'vendor': row['Description'],
                    'amount': row['Amount'],
                    'source': row.get('Source Account', ''),
                    'note': row.get('Note', '')
                })
        
        print(f'FAILED TRANSACTIONS ANALYSIS')
        print('=' * 80)
        print(f'Total transactions: {total_count}')
        print(f'Failed transactions: {len(failed)} ({len(failed)/total_count*100:.1f}%)')
        
        # Group by vendor
        by_vendor = {}
        for f in failed:
            vendor = f['vendor']
            if vendor not in by_vendor:
                by_vendor[vendor] = []
            by_vendor[vendor].append(f)
        
        # Show summary
        print(f'\nTop 10 vendors with failed transactions:')
        print('-' * 60)
        for vendor, transactions in sorted(by_vendor.items(), key=lambda x: len(x[1]), reverse=True)[:10]:
            amounts = []
            for t in transactions:
                try:
                    amt = float(t['amount'].replace(',',''))
                    amounts.append(amt)
                except:
                    pass
            
            total = sum(abs(a) for a in amounts)
            print(f'\n{vendor}:')
            print(f'  Failed count: {len(transactions)}')
            print(f'  Total amount: ${total:,.0f}')
            
            # Show first few examples
            for t in transactions[:2]:
                print(f'  - {t["date"]}: {t["amount"]} ({t["source"]})')

if __name__ == '__main__':
    analyze_failed_transactions()