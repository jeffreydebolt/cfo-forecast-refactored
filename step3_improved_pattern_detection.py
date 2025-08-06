#!/usr/bin/env python3
import sys
import csv
import statistics
from collections import defaultdict
from datetime import datetime, date, timedelta
sys.path.append('.')
from supabase_client import supabase

print('STEP 3: IMPROVED PATTERN DETECTION & FORECASTING LOGIC')
print('Client: BestSelf') 
print('=' * 60)

# Read your vendor mapping CSV manually (same as before)
print('📊 Reading your vendor groupings...')
vendor_groups = {}
individual_vendors = set()

# Your manual mappings
your_mappings = {
    'BESTSELFCO': 'Shopiofy',  
    'AMEX EPAYMENT': 'Amex',
    'AMEX (Mercury Checking xx6270)': 'Amex', 
    'GB HUB NOMOS — NEW (GB Hub Services LLC)': 'GB Hub',
    'GB HUB SERVICES LLC': 'GB Hub',
    'GB Hub Services, LLC': 'GB Hub',
    'Meow — We Spearhead (We Spearhead, LLC)': 'We Spearhead',
}

# Apply your manual mappings
for vendor_name, group_name in your_mappings.items():
    if group_name not in vendor_groups:
        vendor_groups[group_name] = []
    vendor_groups[group_name].append(vendor_name)

# Get all transactions and apply regex auto-mapping
transactions = supabase.table('transactions').select('*').eq('client_id', 'BestSelf').execute()
all_vendors = set(txn['vendor_name'] for txn in transactions.data)

from core.vendor_auto_mapping import auto_mapper

for vendor_name in all_vendors:
    if vendor_name not in your_mappings:
        suggested_group = auto_mapper.auto_map_vendor(vendor_name)
        if suggested_group:
            if suggested_group not in vendor_groups:
                vendor_groups[suggested_group] = []
            vendor_groups[suggested_group].append(vendor_name)
        else:
            individual_vendors.add(vendor_name)

print(f'✅ Found {len(vendor_groups)} groups and {len(individual_vendors)} individual vendors')

# Group transactions
grouped_transactions = defaultdict(list)
for txn in transactions.data:
    vendor_name = txn['vendor_name']
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

# IMPROVED PATTERN ANALYSIS
print('\n🔍 Running improved pattern analysis...')
pattern_analysis = []
today = date.today()

for entity_name, entity_transactions in grouped_transactions.items():
    if len(entity_transactions) < 2:
        continue
    
    # Sort by date
    entity_transactions.sort(key=lambda x: x['transaction_date'])
    
    # Calculate dates and amounts
    all_dates = [datetime.fromisoformat(t['transaction_date']).date() for t in entity_transactions]
    all_amounts = [float(t['amount']) for t in entity_transactions]
    
    last_payment_date = max(all_dates)
    days_since_last = (today - last_payment_date).days
    
    # IMPROVED LOGIC: Define recent period (last 90 days)
    recent_cutoff = today - timedelta(days=90)
    recent_transactions = [
        txn for txn in entity_transactions 
        if datetime.fromisoformat(txn['transaction_date']).date() >= recent_cutoff
    ]
    
    # VALIDATION 1: Check recency
    if days_since_last > 60:
        status = "POTENTIALLY_INACTIVE"
        confidence = 0.2
        frequency = "inactive"
        avg_gap = None
        consistency_score = 0
        forecast_dates = []
        analysis_notes = f"Last payment {days_since_last} days ago - may be inactive"
    
    # VALIDATION 2: Require minimum recent activity  
    elif len(recent_transactions) < 3:
        status = "INSUFFICIENT_RECENT_DATA"
        confidence = 0.3
        frequency = "irregular"
        avg_gap = None
        consistency_score = 0
        forecast_dates = []
        analysis_notes = f"Only {len(recent_transactions)} payments in last 90 days - insufficient for pattern"
    
    else:
        # ANALYSIS: We have sufficient recent data
        recent_dates = [datetime.fromisoformat(t['transaction_date']).date() for t in recent_transactions]
        recent_amounts = [float(t['amount']) for t in recent_transactions]
        
        # Calculate gaps between recent transactions only
        recent_gaps = []
        for i in range(1, len(recent_dates)):
            gap = (recent_dates[i] - recent_dates[i-1]).days
            if gap > 0:
                recent_gaps.append(gap)
        
        if len(recent_gaps) < 2:
            status = "INSUFFICIENT_GAPS"
            confidence = 0.3
            frequency = "irregular"
            avg_gap = None
            consistency_score = 0
            forecast_dates = []
            analysis_notes = "Not enough gaps between recent payments to determine pattern"
        else:
            # IMPROVED CALCULATION: Weighted average (recent gaps weighted more)
            weights = [(i + 1) / len(recent_gaps) for i in range(len(recent_gaps))]
            weighted_avg_gap = sum(gap * weight for gap, weight in zip(recent_gaps, weights)) / sum(weights)
            
            # CONSISTENCY CHECK: How consistent are the gaps?
            gap_std = statistics.stdev(recent_gaps) if len(recent_gaps) > 1 else 0
            consistency_score = 1 / (1 + gap_std / weighted_avg_gap) if weighted_avg_gap > 0 else 0
            
            avg_gap = weighted_avg_gap
            avg_amount = sum(recent_amounts) / len(recent_amounts)
            
            # FREQUENCY DETERMINATION: Based on weighted average gap
            if weighted_avg_gap <= 2:
                frequency = 'daily'
                forecast_interval = 1
            elif weighted_avg_gap <= 8:
                frequency = 'weekly' 
                forecast_interval = 7
            elif weighted_avg_gap <= 16:
                frequency = 'bi-weekly'
                forecast_interval = 14
            elif weighted_avg_gap <= 35:
                frequency = 'monthly'
                forecast_interval = 30
            elif weighted_avg_gap <= 95:
                frequency = 'quarterly'
                forecast_interval = 90
            else:
                frequency = 'irregular'
                forecast_interval = int(weighted_avg_gap)
            
            # CONFIDENCE CALCULATION: Based on consistency and recency
            recency_factor = max(0.5, 1 - (days_since_last / 30))  # Penalty for old payments
            confidence = consistency_score * recency_factor
            
            # STATUS DETERMINATION
            if consistency_score > 0.8 and confidence > 0.6:
                status = "ACTIVE_CONSISTENT"
            elif consistency_score > 0.5 and confidence > 0.4:
                status = "ACTIVE_MODERATE"
            else:
                status = "ACTIVE_INCONSISTENT"
            
            # FORECAST GENERATION: Only if confident and recent
            if confidence > 0.4 and days_since_last <= 45:
                forecast_dates = []
                next_date = last_payment_date
                for i in range(4):
                    next_date = next_date + timedelta(days=forecast_interval)
                    forecast_dates.append(next_date.isoformat())
            else:
                forecast_dates = []
            
            # ANALYSIS NOTES
            analysis_notes = f"Recent: {len(recent_transactions)} payments, Avg gap: {weighted_avg_gap:.1f}d, Consistency: {consistency_score:.2f}, Days since last: {days_since_last}"
    
    # Get last 3 payments for display (regardless of recent cutoff)
    last_3_payments = entity_transactions[-3:] if len(entity_transactions) >= 3 else entity_transactions
    
    pattern_analysis.append({
        'entity_name': entity_name,
        'entity_type': 'GROUP' if entity_name in vendor_groups else 'INDIVIDUAL',
        'status': status,
        'total_transactions': len(entity_transactions),
        'recent_transactions': len(recent_transactions) if 'recent_transactions' in locals() else 0,
        'last_3_payments': [
            f"{txn['transaction_date']}: ${float(txn['amount']):,.2f}" 
            for txn in last_3_payments
        ],
        'detected_frequency': frequency,
        'avg_gap_days': forecast_interval if 'forecast_interval' in locals() else (round(avg_gap, 1) if avg_gap else None),
        'consistency_score': round(consistency_score, 2),
        'confidence': round(confidence, 2),
        'avg_amount': sum(recent_amounts) / len(recent_amounts) if 'recent_amounts' in locals() and recent_amounts else sum(all_amounts) / len(all_amounts),
        'last_payment_date': last_payment_date.isoformat(),
        'days_since_last': days_since_last,
        'next_forecast_dates': forecast_dates,
        'analysis_notes': analysis_notes
    })

# Sort by confidence (most reliable patterns first)
pattern_analysis.sort(key=lambda x: (x['confidence'], abs(x['avg_amount'])), reverse=True)

print(f'✅ Analyzed {len(pattern_analysis)} entities with improved logic')

# Create improved pattern analysis CSV
csv_filename = 'bestself_improved_pattern_analysis.csv'
print(f'📝 Creating improved pattern analysis CSV: {csv_filename}')

with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    
    # Header with new columns
    writer.writerow([
        'Entity Name',
        'Type',
        'Status',
        'Total Txns',
        'Recent Txns (90d)',
        'Last 3 Payments',
        'Detected Frequency',
        'Avg Gap (Days)',
        'Consistency Score',
        'Confidence',
        'Avg Amount',
        'Last Payment Date',
        'Days Since Last',
        'Next 4 Forecast Dates',
        'Analysis Notes'
    ])
    
    for analysis in pattern_analysis:
        # Format data
        payments_display = ' | '.join(analysis['last_3_payments'])
        forecasts_display = ' | '.join(analysis['next_forecast_dates']) if analysis['next_forecast_dates'] else 'NO FORECASTS (Low confidence or inactive)'
        
        writer.writerow([
            analysis['entity_name'],
            analysis['entity_type'],
            analysis['status'],
            analysis['total_transactions'],
            analysis['recent_transactions'],
            payments_display,
            analysis['detected_frequency'],
            analysis['avg_gap_days'],
            analysis['consistency_score'],
            analysis['confidence'],
            f"${analysis['avg_amount']:,.2f}",
            analysis['last_payment_date'],
            analysis['days_since_last'],
            forecasts_display,
            analysis['analysis_notes']
        ])

print(f'✅ Created: {csv_filename}')

# SUMMARY ANALYSIS
print(f'\n📈 IMPROVED ANALYSIS SUMMARY:')

status_counts = defaultdict(int)
confidence_levels = {'High (>0.6)': 0, 'Medium (0.4-0.6)': 0, 'Low (<0.4)': 0}

for analysis in pattern_analysis:
    status_counts[analysis['status']] += 1
    
    if analysis['confidence'] > 0.6:
        confidence_levels['High (>0.6)'] += 1
    elif analysis['confidence'] > 0.4:
        confidence_levels['Medium (0.4-0.6)'] += 1
    else:
        confidence_levels['Low (<0.4)'] += 1

print('📊 Status Distribution:')
for status, count in status_counts.items():
    print(f'   - {status}: {count} entities')

print('\n📊 Confidence Distribution:')
for level, count in confidence_levels.items():
    print(f'   - {level}: {count} entities')

print(f'\n💡 HIGH CONFIDENCE PATTERNS (>0.6):')
high_confidence = [a for a in pattern_analysis if a['confidence'] > 0.6]
for analysis in high_confidence[:10]:
    print(f'   - {analysis["entity_name"]}: {analysis["detected_frequency"]} @ ${analysis["avg_amount"]:,.0f} (confidence: {analysis["confidence"]})')

print(f'\n⚠️ POTENTIALLY INACTIVE (>60 days since last payment):')
inactive = [a for a in pattern_analysis if a['days_since_last'] > 60]
for analysis in inactive[:5]:
    print(f'   - {analysis["entity_name"]}: Last payment {analysis["days_since_last"]} days ago')

print(f'\n📋 KEY IMPROVEMENTS:')
print(f'   ✅ Only uses recent data (last 90 days) for pattern detection')  
print(f'   ✅ Flags inactive vendors (>60 days since last payment)')
print(f'   ✅ Requires minimum 3 recent payments for reliable patterns')
print(f'   ✅ Calculates consistency score (how regular the pattern is)')
print(f'   ✅ Confidence score combines consistency + recency')
print(f'   ✅ No forecasts generated for low confidence/inactive vendors')