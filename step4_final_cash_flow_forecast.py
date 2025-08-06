#!/usr/bin/env python3
import sys
import csv
from datetime import datetime, date, timedelta
from collections import defaultdict
sys.path.append('.')

print('STEP 4: FINAL 13-WEEK CASH FLOW FORECAST')
print('Client: BestSelf') 
print('=' * 60)

# Read your corrected pattern analysis
print('📊 Reading your corrected pattern analysis...')
forecast_entities = []

with open('bestself_improved_pattern_analysis.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        # Only process entities that have forecast dates (not "NO FORECASTS")
        next_dates_str = row['Next 4 Forecast Dates'].strip()
        if next_dates_str and not next_dates_str.startswith('NO FORECASTS'):
            forecast_dates = [d.strip() for d in next_dates_str.split('|')]
            
            # Parse average amount (handle parentheses for negative amounts)
            avg_amount_str = row['Avg Amount'].replace('$', '').replace(',', '').strip()
            if avg_amount_str.startswith('(') and avg_amount_str.endswith(')'):
                avg_amount = -float(avg_amount_str[1:-1])
            else:
                avg_amount = float(avg_amount_str)
            
            # Parse detected frequency and gap
            frequency = row['Detected Frequency'].lower().strip()
            gap_str = row['Avg Gap (Days)']
            try:
                gap_days = float(gap_str) if gap_str else 14  # Default to 14 if missing
            except:
                gap_days = 14
            
            # Parse last payment date
            last_payment_str = row['Last Payment Date']
            try:
                # Handle different date formats
                if '/' in last_payment_str:
                    # Format like "7/28/25"
                    month, day, year = last_payment_str.split('/')
                    if len(year) == 2:
                        year = '20' + year
                    last_payment_date = date(int(year), int(month), int(day))
                else:
                    # Format like "2025-07-28"
                    last_payment_date = datetime.fromisoformat(last_payment_str).date()
            except:
                print(f"⚠️ Could not parse date for {row['Entity Name']}: {last_payment_str}")
                continue
            
            forecast_entities.append({
                'entity_name': row['Entity Name'],
                'frequency': frequency,
                'gap_days': int(gap_days),
                'avg_amount': avg_amount,
                'last_payment_date': last_payment_date,
                'confidence': float(row['Confidence'])
            })

print(f'✅ Found {len(forecast_entities)} entities with forecasts to generate')

# Generate 13-week forecast
print('\n📅 Generating 13-week daily cash flow forecast...')
start_date = date.today()  # August 1, 2025
end_date = start_date + timedelta(weeks=13)
print(f'Forecast period: {start_date} to {end_date}')

# Generate all forecast transactions
forecast_transactions = []

for entity in forecast_entities:
    entity_name = entity['entity_name']
    frequency = entity['frequency'] 
    gap_days = entity['gap_days']
    amount = entity['avg_amount']
    last_payment = entity['last_payment_date']
    
    print(f'   📊 {entity_name}: {frequency} every {gap_days}d @ ${amount:,.2f}')
    
    # Generate forecast dates from last payment
    current_forecast_date = last_payment
    forecast_count = 0
    
    while current_forecast_date <= end_date and forecast_count < 20:  # Safety limit
        # Calculate next payment date
        current_forecast_date = current_forecast_date + timedelta(days=gap_days)
        
        # Only include if within our forecast window
        if start_date <= current_forecast_date <= end_date:
            forecast_transactions.append({
                'date': current_forecast_date,
                'entity': entity_name,
                'amount': amount,
                'frequency': frequency
            })
            forecast_count += 1

print(f'✅ Generated {len(forecast_transactions)} forecast transactions')

# Sort by date
forecast_transactions.sort(key=lambda x: x['date'])

# Calculate running balance
print('\n💰 Calculating running bank balance...')
starting_balance = 50000  # You can adjust this
current_balance = starting_balance

# Add balance to each transaction
for txn in forecast_transactions:
    current_balance += txn['amount']
    txn['running_balance'] = current_balance

# Create the final CSV
csv_filename = 'bestself_13week_daily_cashflow_forecast.csv'
print(f'📝 Creating final cash flow forecast CSV: {csv_filename}')

with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    
    # Header
    writer.writerow([
        'Date',
        'Vendor/Group', 
        'Amount',
        'Running Balance',
        'Frequency Pattern'
    ])
    
    # Starting balance row
    writer.writerow([
        start_date.isoformat(),
        'STARTING BALANCE',
        f'${starting_balance:,.2f}',
        f'${starting_balance:,.2f}',
        'Initial'
    ])
    
    # All forecast transactions
    for txn in forecast_transactions:
        writer.writerow([
            txn['date'].isoformat(),
            txn['entity'],
            f'${txn["amount"]:,.2f}',
            f'${txn["running_balance"]:,.2f}',
            txn['frequency']
        ])

print(f'✅ Created: {csv_filename}')

# Summary statistics
print(f'\n📈 FORECAST SUMMARY:')
print(f'   📅 Period: {start_date} to {end_date} (13 weeks)')
print(f'   💰 Starting Balance: ${starting_balance:,.2f}')
print(f'   💰 Ending Balance: ${current_balance:,.2f}')
print(f'   📊 Net Cash Flow: ${current_balance - starting_balance:,.2f}')
print(f'   🔢 Total Transactions: {len(forecast_transactions)}')

# Break down by entity
entity_totals = defaultdict(float)
entity_counts = defaultdict(int)

for txn in forecast_transactions:
    entity_totals[txn['entity']] += txn['amount']
    entity_counts[txn['entity']] += 1

print(f'\n📊 TOP CASH FLOW CONTRIBUTORS:')
sorted_entities = sorted(entity_totals.items(), key=lambda x: abs(x[1]), reverse=True)
for entity, total in sorted_entities[:10]:
    count = entity_counts[entity]
    print(f'   - {entity}: ${total:,.2f} ({count} payments)')

print(f'\n🎉 FINAL CASH FLOW FORECAST COMPLETE!')
print(f'📁 Open {csv_filename} in Excel/Google Sheets to review the daily forecast')
print(f'\n💡 This shows exact payment dates based on your corrected patterns:')
print(f'   - Amazon Revenue: Every 14 days from last payment')
print(f'   - Lavery Innovations: Monthly at $20,000')
print(f'   - All other entities: Based on their detected patterns')