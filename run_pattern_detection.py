#!/usr/bin/env python3
import sys
sys.path.append('.')
from supabase_client import supabase
from datetime import datetime, date

print('STEP 3: PATTERN DETECTION')
print('Client: BestSelf') 
print('=' * 60)

# Get your vendor groups
groups = supabase.table('vendor_groups').select('*').eq('client_id', 'BestSelf').execute()
print(f'✅ Found {len(groups.data)} vendor groups')

# Analyze each group
for group in groups.data:
    group_name = group['group_name']
    vendor_list = group['vendor_display_names']
    
    print(f'\n📊 Analyzing: {group_name}')
    print(f'   Vendors: {vendor_list}')
    
    # Get transactions for this group
    transactions = supabase.table('transactions')\
        .select('transaction_date, amount')\
        .eq('client_id', 'BestSelf')\
        .in_('vendor_name', vendor_list)\
        .order('transaction_date')\
        .execute()
    
    if len(transactions.data) < 3:
        print(f'   ⏭️ Insufficient data: {len(transactions.data)} transactions')
        continue
    
    # Analyze pattern
    dates = [datetime.fromisoformat(t['transaction_date']).date() for t in transactions.data]
    amounts = [abs(float(t['amount'])) for t in transactions.data]
    
    # Calculate gaps between transactions
    gaps = []
    for i in range(1, len(dates)):
        gap = (dates[i] - dates[i-1]).days
        if gap > 0:
            gaps.append(gap)
    
    if not gaps:
        print(f'   ⏭️ No gaps to analyze')
        continue
    
    avg_gap = sum(gaps) / len(gaps)
    avg_amount = sum(amounts) / len(amounts)
    
    # Determine pattern type
    if avg_gap < 3:
        pattern_type = 'daily'
    elif avg_gap < 10:
        pattern_type = 'weekly'
    elif avg_gap < 20: 
        pattern_type = 'bi-weekly'
    elif avg_gap < 35:
        pattern_type = 'monthly'
    else:
        pattern_type = 'irregular'
    
    print(f'   📈 Pattern: {pattern_type}')
    print(f'   💰 Avg Amount: ${avg_amount:,.0f}')
    print(f'   📅 Avg Gap: {avg_gap:.1f} days')
    print(f'   🔢 Transactions: {len(transactions.data)}')
    
    # Save pattern analysis
    analysis = {
        'client_id': 'BestSelf',
        'vendor_group_name': group_name,
        'analysis_date': date.today().isoformat(),
        'frequency_detected': pattern_type,
        'confidence_score': 0.8 if pattern_type != 'irregular' else 0.4,
        'sample_size': len(transactions.data),
        'average_amount': avg_amount,
        'explanation': f'Avg gap: {avg_gap:.1f} days, {len(transactions.data)} transactions'
    }
    
    supabase.table('pattern_analysis').upsert(analysis).execute()
    print(f'   ✅ Pattern saved to database')

print('\n🎉 STEP 3 COMPLETE - Pattern detection finished!')