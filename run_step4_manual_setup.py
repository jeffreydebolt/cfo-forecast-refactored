#!/usr/bin/env python3
import sys
sys.path.append('.')
from supabase_client import supabase
from datetime import datetime, date

print('STEP 4: MANUAL FORECAST SETUP')
print('Client: BestSelf') 
print('=' * 60)

# Check pattern analysis results
patterns = supabase.table('pattern_analysis').select('*').eq('client_id', 'BestSelf').execute()
print(f'✅ Found {len(patterns.data)} pattern analyses')

# Show current patterns and confidence
manual_needed = []
for pattern in patterns.data:
    group_name = pattern['vendor_group_name']
    confidence = pattern.get('confidence_score', 0)
    frequency = pattern.get('frequency_detected', 'unknown')
    avg_amount = pattern.get('average_amount', 0)
    
    print(f'\n📊 {group_name}:')
    print(f'   Pattern: {frequency}')
    print(f'   Confidence: {confidence:.1%}')
    print(f'   Avg Amount: ${avg_amount:,.0f}')
    
    if confidence < 0.8:
        manual_needed.append(pattern)
        print(f'   ⚠️ Needs manual setup (low confidence)')
    else:
        print(f'   ✅ High confidence - auto-config ready')

if not manual_needed:
    print(f'\n✅ All vendor groups have high confidence patterns')
    print(f'   No manual setup required - ready for Step 5!')
else:
    print(f'\n📝 {len(manual_needed)} groups need manual configuration')
    print(f'   Review and adjust these patterns before generating forecasts')

print('\n🎉 STEP 4 COMPLETE - Manual setup reviewed!')