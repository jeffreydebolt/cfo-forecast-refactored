#!/usr/bin/env python3
"""
Debug version - Onboarding with correct database schema
"""

import sys
import argparse
import json
from datetime import datetime, date

sys.path.append('.')

from supabase_client import supabase
from practical_pattern_detection import PracticalPatternDetection
from integrated_forecast_display import generate_integrated_forecast_display

class DebugClientOnboarding:
    """Onboarding that matches actual database schema"""
    
    def __init__(self, client_id: str):
        self.client_id = client_id
        self.pattern_detector = PracticalPatternDetection()
        self.start_time = datetime.now()
        
    def run_debug_onboarding(self):
        """Run onboarding with correct schema"""
        print(f"\n🚀 DEBUG CLIENT ONBOARDING")
        print(f"Client: {self.client_id}")
        print("=" * 80)
        
        # Step 1: Verify transactions
        if not self._verify_transactions():
            return
        
        # Step 2: Create vendor groups with correct schema
        vendor_groups = self._create_vendor_groups()
        
        # Step 3: Pattern analysis
        patterns = self._analyze_patterns()
        
        # Step 4: Create forecasts
        self._create_forecasts(patterns)
        
        # Complete
        elapsed = (datetime.now() - self.start_time).seconds / 60
        print(f"\n✅ ONBOARDING COMPLETE!")
        print(f"⏱️ Total time: {elapsed:.1f} minutes")
    
    def _verify_transactions(self) -> bool:
        """Verify transactions exist"""
        result = supabase.table('transactions').select('id', count='exact')\
            .eq('client_id', self.client_id)\
            .execute()
        
        count = result.count or 0
        print(f"✅ Found {count} transactions")
        return count > 0
    
    def _create_vendor_groups(self) -> dict:
        """Create vendor groups matching actual schema"""
        print("\n🗂️ CREATING VENDOR GROUPS")
        print("-" * 60)
        
        # Get unique vendors
        result = supabase.table('transactions')\
            .select('vendor_name')\
            .eq('client_id', self.client_id)\
            .execute()
        
        vendors = list(set(row['vendor_name'] for row in result.data))
        
        # Group vendors intelligently
        groups = {}
        
        # Group 1: Amex Payments
        amex_vendors = [v for v in vendors if 'amex' in v.lower()]
        if amex_vendors:
            groups['Amex Payments'] = amex_vendors
        
        # Group 2: Shopify Revenue
        shopify_vendors = [v for v in vendors if 'shopify' in v.lower() or 'shoppay' in v.lower()]
        if shopify_vendors:
            groups['Shopify Revenue'] = shopify_vendors
        
        # Group 3: Stripe Revenue  
        stripe_vendors = [v for v in vendors if 'stripe' in v.lower()]
        if stripe_vendors:
            groups['Stripe Revenue'] = stripe_vendors
        
        # Group 4: BestSelf Revenue
        bestself_vendors = [v for v in vendors if 'bestselfco' in v.lower()]
        if bestself_vendors:
            groups['BestSelf Revenue'] = bestself_vendors
        
        # Group 5: International Vendors
        intl_vendors = [v for v in vendors if any(x in v.lower() for x in ['ltd', 'co.,ltd', 'international', 'wise'])]
        if intl_vendors:
            groups['International Vendors'] = intl_vendors[:10]  # Limit size
        
        # Save to database with correct schema
        saved = 0
        for group_name, vendor_list in groups.items():
            record = {
                'client_id': self.client_id,
                'group_name': group_name,
                'vendor_display_names': vendor_list,  # Array field
                'is_active': True,
                'created_at': datetime.now().isoformat()
            }
            
            try:
                result = supabase.table('vendor_groups').upsert(record).execute()
                saved += 1
                print(f"   ✅ {group_name}: {len(vendor_list)} vendors")
            except Exception as e:
                print(f"   ❌ Error saving {group_name}: {str(e)}")
        
        print(f"\n📊 Created {saved} vendor groups")
        return groups
    
    def _analyze_patterns(self) -> dict:
        """Analyze patterns for vendor groups"""
        print("\n🔍 PATTERN ANALYSIS")
        print("-" * 60)
        
        # Get vendor groups
        result = supabase.table('vendor_groups')\
            .select('*')\
            .eq('client_id', self.client_id)\
            .execute()
        
        if not result.data:
            print("❌ No vendor groups found")
            return {}
        
        patterns = {}
        saved = 0
        
        for group in result.data:
            group_name = group['group_name']
            vendor_list = group['vendor_display_names']
            
            # Get transactions for this group
            transactions = supabase.table('transactions')\
                .select('transaction_date, amount')\
                .eq('client_id', self.client_id)\
                .in_('vendor_name', vendor_list)\
                .order('transaction_date')\
                .execute()
            
            if len(transactions.data) < 3:
                print(f"   ⏭️ {group_name}: Not enough data ({len(transactions.data)} transactions)")
                continue
            
            # Simple pattern detection
            dates = [datetime.fromisoformat(t['transaction_date']).date() for t in transactions.data]
            amounts = [abs(float(t['amount'])) for t in transactions.data]
            
            # Calculate gaps between transactions
            gaps = []
            for i in range(1, len(dates)):
                gap = (dates[i] - dates[i-1]).days
                if gap > 0:
                    gaps.append(gap)
            
            if gaps:
                avg_gap = sum(gaps) / len(gaps)
                avg_amount = sum(amounts) / len(amounts)
                
                # Determine pattern
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
                
                # Save pattern analysis
                analysis_record = {
                    'client_id': self.client_id,
                    'vendor_group_name': group_name,
                    'analysis_date': date.today().isoformat(),
                    'frequency_detected': pattern_type,
                    'confidence_score': 0.75,
                    'sample_size': len(transactions.data),
                    'date_range_start': min(dates).isoformat(),
                    'date_range_end': max(dates).isoformat(),
                    'transactions_analyzed': len(transactions.data),
                    'average_amount': avg_amount,
                    'explanation': f"Average gap: {avg_gap:.1f} days",
                    'created_at': datetime.now().isoformat()
                }
                
                try:
                    supabase.table('pattern_analysis').insert(analysis_record).execute()
                    saved += 1
                    print(f"   ✅ {group_name}: {pattern_type} pattern (${avg_amount:,.0f})")
                    
                    patterns[group_name] = {
                        'pattern_type': pattern_type,
                        'avg_amount': avg_amount,
                        'confidence': 0.75
                    }
                except Exception as e:
                    print(f"   ❌ Error saving pattern for {group_name}: {str(e)}")
        
        print(f"\n📊 Analyzed {len(patterns)} patterns, saved {saved}")
        return patterns
    
    def _create_forecasts(self, patterns: dict):
        """Create forecast records"""
        print("\n📈 CREATING FORECASTS")
        print("-" * 60)
        
        # Update vendor groups with patterns
        for group_name, pattern in patterns.items():
            try:
                update = {
                    'pattern_frequency': pattern['pattern_type'],
                    'pattern_confidence': pattern['confidence'],
                    'weighted_average_amount': pattern['avg_amount'],
                    'last_analyzed': date.today().isoformat()
                }
                
                supabase.table('vendor_groups')\
                    .update(update)\
                    .eq('client_id', self.client_id)\
                    .eq('group_name', group_name)\
                    .execute()
                    
                print(f"   ✅ Updated {group_name} with pattern data")
            except Exception as e:
                print(f"   ❌ Error updating {group_name}: {str(e)}")
        
        # Generate forecast records would go here
        print(f"\n✅ Pattern data saved to vendor_groups table")


def main():
    parser = argparse.ArgumentParser(description='Debug onboarding with correct schema')
    parser.add_argument('--client', required=True, help='Client ID')
    args = parser.parse_args()
    
    system = DebugClientOnboarding(args.client)
    system.run_debug_onboarding()


if __name__ == "__main__":
    main()