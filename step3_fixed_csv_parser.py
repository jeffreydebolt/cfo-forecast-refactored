#!/usr/bin/env python3
import sys
import csv
from collections import defaultdict
from datetime import datetime, date, timedelta
sys.path.append('.')
from supabase_client import supabase

print('STEP 3: PATTERN ANALYSIS & FORECASTING LOGIC (FIXED)')
print('Client: BestSelf') 
print('=' * 60)

# Read your vendor mapping CSV manually
print('📊 Reading your vendor groupings...')
vendor_groups = {}
individual_vendors = set()

# Based on your CSV, I can see the mappings directly:
your_mappings = {
    'BESTSELFCO': 'Shopiofy',  # Note: typo in CSV but I'll use it
    'AMEX EPAYMENT': 'Amex',
    'AMEX (Mercury Checking xx6270)': 'Amex', 
    'GB HUB NOMOS — NEW (GB Hub Services LLC)': 'GB Hub',
    'GB HUB SERVICES LLC': 'GB Hub',
    'GB Hub Services, LLC': 'GB Hub',
    'Meow — We Spearhead (We Spearhead, LLC)': 'We Spearhead',
    # All AMAZON.* already auto-mapped to Amazon Revenue by regex
    # All other vendors without group will be individual
}

# Apply your manual mappings
for vendor_name, group_name in your_mappings.items():
    if group_name not in vendor_groups:
        vendor_groups[group_name] = []
    vendor_groups[group_name].append(vendor_name)

# Get all transactions to find all vendors
transactions = supabase.table('transactions').select('*').eq('client_id', 'BestSelf').execute()
all_vendors = set(txn['vendor_name'] for txn in transactions.data)

# Apply regex auto-mapping for Amazon, Shopify, etc.
from core.vendor_auto_mapping import auto_mapper

for vendor_name in all_vendors:
    if vendor_name not in your_mappings:
        # Try regex auto-mapping
        suggested_group = auto_mapper.auto_map_vendor(vendor_name)
        if suggested_group:
            if suggested_group not in vendor_groups:
                vendor_groups[suggested_group] = []
            vendor_groups[suggested_group].append(vendor_name)
        else:
            # Keep as individual
            individual_vendors.add(vendor_name)

print(f'✅ Found {len(vendor_groups)} groups and {len(individual_vendors)} individual vendors')
for group_name, vendors in vendor_groups.items():
    print(f'   - {group_name}: {len(vendors)} vendors')

# Group transactions by your groupings
print('\n🔍 Analyzing transaction patterns...')
grouped_transactions = defaultdict(list)

for txn in transactions.data:
    vendor_name = txn['vendor_name']
    
    # Find which group this vendor belongs to
    assigned_group = None
    for group_name, group_vendors in vendor_groups.items():
        if vendor_name in group_vendors:
            assigned_group = group_name
            break
    
    if assigned_group:
        grouped_transactions[assigned_group].append(txn)
    elif vendor_name in individual_vendors:
        grouped_transactions[vendor_name].append(txn)

print(f'✅ Grouped transactions into {len(grouped_transactions)} entities')

# Analyze patterns for each group/vendor
pattern_analysis = []

for entity_name, entity_transactions in grouped_transactions.items():
    if len(entity_transactions) < 2:
        print(f'   ⏭️ {entity_name}: Insufficient data ({len(entity_transactions)} transactions)')
        continue
    
    # Sort by date
    entity_transactions.sort(key=lambda x: x['transaction_date'])
    
    # Get last 3 months of data for analysis
    end_date = date.today()
    start_date = end_date - timedelta(days=90)
    
    recent_transactions = [
        txn for txn in entity_transactions 
        if datetime.fromisoformat(txn['transaction_date']).date() >= start_date
    ]
    
    if len(recent_transactions) < 2:
        # Use all data if not enough recent data
        recent_transactions = entity_transactions
    
    # Calculate gaps between transactions
    dates = [datetime.fromisoformat(t['transaction_date']).date() for t in recent_transactions]
    amounts = [float(t['amount']) for t in recent_transactions]
    
    gaps = []
    for i in range(1, len(dates)):
        gap = (dates[i] - dates[i-1]).days
        if gap > 0:
            gaps.append(gap)
    
    if not gaps:
        continue
    
    avg_gap = sum(gaps) / len(gaps)
    avg_amount = sum(amounts) / len(amounts)
    
    # Determine frequency pattern
    if avg_gap <= 1.5:
        frequency = 'daily'
        forecast_interval = 1
    elif avg_gap <= 7.5:
        frequency = 'weekly' 
        forecast_interval = 7
    elif avg_gap <= 16:
        frequency = 'bi-weekly'
        forecast_interval = 14
    elif avg_gap <= 32:
        frequency = 'monthly'
        forecast_interval = 30
    elif avg_gap <= 95:
        frequency = 'quarterly'
        forecast_interval = 90
    else:
        frequency = 'irregular'
        forecast_interval = int(avg_gap)
    
    # Find last payment date for forecasting
    last_payment_date = max(dates)
    
    # Calculate next forecast dates based on EXACT intervals from last payment
    next_dates = []
    current_forecast_date = last_payment_date
    
    for i in range(4):
        current_forecast_date = current_forecast_date + timedelta(days=forecast_interval)
        next_dates.append(current_forecast_date)
    
    # Get last 3 payments for display
    last_3_payments = recent_transactions[-3:] if len(recent_transactions) >= 3 else recent_transactions
    
    pattern_analysis.append({
        'entity_name': entity_name,
        'entity_type': 'GROUP' if entity_name in vendor_groups else 'INDIVIDUAL',
        'total_transactions': len(entity_transactions),
        'last_3_months_transactions': len(recent_transactions),
        'last_3_payments': [
            f"{txn['transaction_date']}: ${float(txn['amount']):,.2f}" 
            for txn in last_3_payments
        ],
        'detected_frequency': frequency,
        'avg_gap_days': round(avg_gap, 1),
        'avg_amount': avg_amount,
        'last_payment_date': last_payment_date.isoformat(),
        'next_forecast_dates': [d.isoformat() for d in next_dates],
        'forecast_interval_days': forecast_interval
    })

# Sort by absolute average amount (most important first)
pattern_analysis.sort(key=lambda x: abs(x['avg_amount']), reverse=True)

print(f'✅ Analyzed patterns for {len(pattern_analysis)} entities')

# Create pattern analysis CSV
csv_filename = 'bestself_pattern_analysis.csv'
print(f'📝 Creating pattern analysis CSV: {csv_filename}')

with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    
    # Header
    writer.writerow([
        'Entity Name',
        'Type (GROUP/INDIVIDUAL)', 
        'Total Transactions',
        'Last 3 Months Count',
        'Last 3 Payments (Date: Amount)',
        'Detected Frequency',
        'Avg Gap (Days)',
        'Avg Amount',
        'Last Payment Date',
        'Next 4 Forecast Dates',
        'Forecast Logic'
    ])
    
    for analysis in pattern_analysis:
        # Format last 3 payments
        payments_display = ' | '.join(analysis['last_3_payments'])
        
        # Format next forecast dates
        forecasts_display = ' | '.join(analysis['next_forecast_dates'])
        
        # Create forecast logic explanation
        if analysis['detected_frequency'] == 'daily':
            logic = f"Daily pattern: Every {analysis['forecast_interval_days']} day(s)"
        elif analysis['detected_frequency'] == 'weekly':
            logic = f"Weekly pattern: Every {analysis['forecast_interval_days']} days"
        elif analysis['detected_frequency'] == 'bi-weekly':
            logic = f"Bi-weekly pattern: Every {analysis['forecast_interval_days']} days"
        elif analysis['detected_frequency'] == 'monthly':
            logic = f"Monthly pattern: Every {analysis['forecast_interval_days']} days"  
        elif analysis['detected_frequency'] == 'quarterly':
            logic = f"Quarterly pattern: Every {analysis['forecast_interval_days']} days"
        else:
            logic = f"Irregular pattern: Avg {analysis['avg_gap_days']} days between payments"
        
        writer.writerow([
            analysis['entity_name'],
            analysis['entity_type'],
            analysis['total_transactions'],
            analysis['last_3_months_transactions'],
            payments_display,
            analysis['detected_frequency'],
            analysis['avg_gap_days'],
            f"${analysis['avg_amount']:,.2f}",
            analysis['last_payment_date'],
            forecasts_display,
            logic
        ])

print(f'✅ Created: {csv_filename}')
print(f'📊 {len(pattern_analysis)} entities analyzed')

# Show summary
print(f'\n📈 PATTERN SUMMARY:')
frequency_counts = defaultdict(int)
for analysis in pattern_analysis:
    frequency_counts[analysis['detected_frequency']] += 1

for freq, count in frequency_counts.items():
    print(f'   - {freq}: {count} entities')

print(f'\n💡 KEY INSIGHTS (Top 10):')
top_10 = pattern_analysis[:10]
for analysis in top_10:
    print(f'   - {analysis["entity_name"]}: {analysis["detected_frequency"]} @ ${analysis["avg_amount"]:,.0f}')

print(f'\n📋 NEXT STEPS:')
print(f'1. Open {csv_filename} in Excel/Google Sheets')
print(f'2. Review the detected patterns and forecast logic')
print(f'3. Check if the "Next 4 Forecast Dates" look correct based on last payment')
print(f'4. Let me know if you want to adjust any patterns')
print(f'5. When ready, I\'ll generate the full 13-week cash flow forecast')