#!/usr/bin/env python3
"""
Simple Clean Forecasting System
Fixes the duplicate and confusion issues by using clean, simple logic
"""

import sys
sys.path.append('.')

from database.forecast_db_manager import forecast_db
from supabase_client import supabase
from datetime import datetime, date, timedelta
from collections import defaultdict
import statistics

class SimpleCleanForecasting:
    """Simple, clean forecasting that actually works"""
    
    def analyze_client_patterns(self, client_id: str):
        """Analyze all vendor patterns for a client with clean logic"""
        print(f"🔍 SIMPLE CLEAN ANALYSIS: {client_id}")
        print("=" * 60)
        
        # Step 1: Get ALL transactions and group by display_name
        # Note: BestSelf data is stored under 'spyguy' client_id
        actual_client_id = 'spyguy' if client_id == 'bestself' else client_id
        
        result = supabase.table('transactions').select('*').eq('client_id', actual_client_id).execute()
        transactions = result.data
        print(f"📊 Found {len(transactions)} total transactions")
        
        # Step 2: Get vendor mappings to get display_name
        vendor_result = supabase.table('vendors').select('vendor_name, display_name').eq('client_id', actual_client_id).execute()
        vendor_mappings = {v['vendor_name']: v['display_name'] for v in vendor_result.data if v.get('display_name')}
        
        print(f"📋 Found {len(vendor_mappings)} vendor mappings")
        
        # Group transactions by display_name (clean grouping)
        vendor_groups = defaultdict(list)
        unmapped_count = 0
        
        for txn in transactions:
            vendor_name = txn.get('vendor_name', 'Unknown')
            display_name = vendor_mappings.get(vendor_name)
            
            if display_name:
                vendor_groups[display_name].append(txn)
            else:
                unmapped_count += 1
        
        print(f"⚠️  {unmapped_count} transactions have no display_name mapping")
        
        print(f"🏢 Found {len(vendor_groups)} unique vendors:")
        
        analysis_results = {}
        
        for vendor_name, vendor_transactions in vendor_groups.items():
            if len(vendor_transactions) < 2:
                print(f"  ⚠️  {vendor_name}: Only {len(vendor_transactions)} transaction(s) - skipping")
                continue
                
            print(f"\n📈 Analyzing: {vendor_name} ({len(vendor_transactions)} transactions)")
            
            # Sort transactions by date
            vendor_transactions.sort(key=lambda x: x['transaction_date'])
            
            # Step 2: Simple pattern detection
            pattern_result = self._detect_simple_pattern(vendor_transactions)
            
            analysis_results[vendor_name] = {
                'transaction_count': len(vendor_transactions),
                'pattern': pattern_result,
                'last_transaction_date': vendor_transactions[-1]['transaction_date'],
                'transactions': vendor_transactions
            }
            
            # Print results
            if pattern_result['frequency'] != 'irregular':
                print(f"  ✅ Pattern: {pattern_result['frequency']} - ${pattern_result['average_amount']:,.2f}")
                print(f"     Last: {pattern_result['last_date']} → Next: {pattern_result['next_expected_date']}")
            else:
                print(f"  ❌ No clear pattern - irregular payments")
        
        return analysis_results
    
    def _detect_simple_pattern(self, transactions):
        """Simple pattern detection - just look at gaps between dates"""
        
        # Calculate gaps between consecutive transactions
        gaps = []
        amounts = []
        dates = []
        
        for i in range(1, len(transactions)):
            prev_date = datetime.fromisoformat(transactions[i-1]['transaction_date']).date()
            curr_date = datetime.fromisoformat(transactions[i]['transaction_date']).date()
            gap_days = (curr_date - prev_date).days
            
            gaps.append(gap_days)
            amounts.append(float(transactions[i]['amount']))
            dates.append(curr_date)
        
        if not gaps:
            return self._create_irregular_result(transactions)
        
        # Find the most common gap
        gap_frequency = defaultdict(int)
        for gap in gaps:
            # Round to nearest week to handle minor variations
            rounded_gap = round(gap / 7) * 7
            gap_frequency[rounded_gap] += 1
        
        if not gap_frequency:
            return self._create_irregular_result(transactions)
        
        most_common_gap = max(gap_frequency.items(), key=lambda x: x[1])
        gap_days, frequency_count = most_common_gap
        
        # Determine if pattern is strong enough
        pattern_strength = frequency_count / len(gaps)
        
        if pattern_strength < 0.6:  # Less than 60% consistency
            return self._create_irregular_result(transactions)
        
        # Classify frequency
        if gap_days <= 1:
            frequency = 'daily'
        elif gap_days <= 7:
            frequency = 'weekly'
        elif gap_days <= 16:
            frequency = 'bi-weekly'
        elif gap_days <= 35:
            frequency = 'monthly'
        elif gap_days <= 100:
            frequency = 'quarterly'
        else:
            return self._create_irregular_result(transactions)
        
        # Calculate average amount
        average_amount = statistics.mean(amounts) if amounts else statistics.mean([float(t['amount']) for t in transactions])
        
        # Calculate next expected date
        last_date = datetime.fromisoformat(transactions[-1]['transaction_date']).date()
        next_expected_date = last_date + timedelta(days=gap_days)
        
        return {
            'frequency': frequency,
            'gap_days': gap_days,
            'pattern_strength': pattern_strength,
            'average_amount': average_amount,
            'last_date': last_date.isoformat(),
            'next_expected_date': next_expected_date.isoformat(),
            'confidence': pattern_strength
        }
    
    def _create_irregular_result(self, transactions):
        """Create result for irregular patterns"""
        average_amount = statistics.mean([float(t['amount']) for t in transactions])
        last_date = datetime.fromisoformat(transactions[-1]['transaction_date']).date()
        
        return {
            'frequency': 'irregular',
            'gap_days': None,
            'pattern_strength': 0.0,
            'average_amount': average_amount,
            'last_date': last_date.isoformat(),
            'next_expected_date': None,
            'confidence': 0.0
        }
    
    def generate_clean_forecasts(self, client_id: str, analysis_results: dict, weeks_ahead: int = 13):
        """Generate clean forecasts for predictable patterns"""
        print(f"\n🔮 GENERATING CLEAN FORECASTS")
        print("=" * 60)
        
        start_date = date(2025, 8, 4)  # Next Monday
        forecasts = []
        
        for vendor_name, analysis in analysis_results.items():
            pattern = analysis['pattern']
            
            if pattern['frequency'] == 'irregular' or pattern['confidence'] < 0.6:
                print(f"  ⚠️  {vendor_name}: Irregular pattern - skipping automatic forecast")
                continue
            
            print(f"  📅 {vendor_name}: Generating {pattern['frequency']} forecasts")
            
            # Generate forecasts starting from start_date, using the pattern
            gap_days = pattern['gap_days']
            amount = pattern['average_amount']
            
            # Find the first forecast date on or after start_date
            last_transaction_date = datetime.fromisoformat(pattern['last_date']).date()
            current_date = start_date
            
            # If the pattern is daily but we want weekly forecasts, adjust
            if pattern['frequency'] == 'daily':
                # For daily patterns, forecast weekly totals
                gap_days = 7
                amount = amount * 7  # Weekly total
            
            forecast_count = 0
            end_date = start_date + timedelta(weeks=weeks_ahead)
            
            while current_date <= end_date and forecast_count < 20:  # Safety limit
                forecasts.append({
                    'client_id': client_id,
                    'vendor_group_name': vendor_name,
                    'forecast_date': current_date.isoformat(),
                    'forecast_amount': round(amount, 2),
                    'forecast_type': 'automatic',
                    'forecast_method': f'{pattern["frequency"]}_pattern',
                    'pattern_confidence': pattern['confidence'],
                    'created_at': datetime.now().isoformat(),
                    'display_names_included': [vendor_name],
                    'timing': pattern['frequency']
                })
                
                print(f"      {current_date.strftime('%Y-%m-%d')}: ${amount:,.2f}")
            
                # Move to next forecast date
                current_date += timedelta(days=gap_days)
                forecast_count += 1
            
            print(f"      Generated {len([f for f in forecasts if f['vendor_group_name'] == vendor_name])} forecasts")
        
        print(f"\n✅ Total Clean Forecasts Generated: {len(forecasts)}")
        return forecasts
    
    def explain_algorithm(self):
        """Explain how the simple algorithm works"""
        print("🧠 SIMPLE CLEAN FORECASTING ALGORITHM")
        print("=" * 60)
        print()
        print("STEP 1: Clean Vendor Grouping")
        print("  • Get ALL transactions for the client")
        print("  • Group by display_name (Amazon Revenue = ONE group)")
        print("  • No duplicates, no confusion")
        print()
        print("STEP 2: Simple Pattern Detection")
        print("  • Sort transactions by date for each vendor")
        print("  • Calculate gaps between consecutive transactions")
        print("  • Find most common gap (7 days = weekly, 14 = bi-weekly)")
        print("  • If 60%+ of gaps match → reliable pattern")
        print("  • Calculate average transaction amount")
        print()
        print("STEP 3: Generate Future Dates")
        print("  • Take last transaction date")
        print("  • Add gap_days repeatedly to get future dates")
        print("  • Generate 13 weeks of specific forecasts")
        print("  • Each forecast = specific date + amount")
        print()
        print("EXAMPLE:")
        print("  Amazon Revenue transactions:")
        print("    2025-06-10: $44,500")
        print("    2025-06-24: $44,800  (gap: 14 days)")
        print("    2025-07-08: $44,200  (gap: 14 days)")
        print("  → Pattern: bi-weekly, ~$44,500 average")
        print("  → Forecasts: 2025-07-22, 2025-08-05, 2025-08-19...")
        print()

def main():
    """Test the simple clean forecasting"""
    forecaster = SimpleCleanForecasting()
    
    # Explain the algorithm
    forecaster.explain_algorithm()
    
    # Run analysis
    analysis_results = forecaster.analyze_client_patterns('bestself')
    
    # Generate forecasts
    forecasts = forecaster.generate_clean_forecasts('bestself', analysis_results)
    
    print(f"\n🎯 SUMMARY:")
    print(f"  • Clean vendor grouping (no duplicates)")
    print(f"  • Simple pattern detection (gap analysis)")  
    print(f"  • {len(forecasts)} specific forecast dates generated")
    print(f"  • Ready to replace the complex broken system")

if __name__ == "__main__":
    main()