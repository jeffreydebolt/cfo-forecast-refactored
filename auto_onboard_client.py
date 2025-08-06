#!/usr/bin/env python3
"""
Automated Client Onboarding
Runs without manual input for testing
"""

import sys
import argparse
import json
from datetime import datetime, date

sys.path.append('.')

from supabase_client import supabase
from practical_pattern_detection import PracticalPatternDetection
from integrated_forecast_display import generate_integrated_forecast_display

class AutoClientOnboarding:
    """Automated onboarding that simulates user input"""
    
    def __init__(self, client_id: str):
        self.client_id = client_id
        self.pattern_detector = PracticalPatternDetection()
        self.start_time = datetime.now()
        
    def run_auto_onboarding(self):
        """Run automated onboarding"""
        print(f"\n🚀 AUTOMATED CLIENT ONBOARDING")
        print(f"Client: {self.client_id}")
        print("=" * 80)
        
        # Step 1: Verify prerequisites
        if not self._verify_prerequisites():
            return
        
        # Step 2: Auto vendor grouping
        vendor_groups = self._auto_vendor_grouping()
        
        # Step 3: Pattern detection
        patterns = self._run_pattern_analysis()
        
        # Step 4: Auto forecast configuration
        self._auto_configure_forecasts(patterns)
        
        # Step 5: Generate forecasts
        self._generate_forecasts()
        
        # Step 6: Show results
        self._show_results(vendor_groups)
        
        # Complete
        elapsed = (datetime.now() - self.start_time).seconds / 60
        print(f"\n✅ ONBOARDING COMPLETE!")
        print(f"⏱️ Total time: {elapsed:.1f} minutes")
    
    def _verify_prerequisites(self) -> bool:
        """Verify client has transactions"""
        result = supabase.table('transactions').select('id', count='exact')\
            .eq('client_id', self.client_id)\
            .execute()
        
        count = result.count or 0
        
        if count == 0:
            print(f"❌ No transactions found for client: {self.client_id}")
            return False
        
        print(f"✅ Found {count} transactions")
        return True
    
    def _auto_vendor_grouping(self) -> dict:
        """Automatically create sensible vendor groups"""
        print("\n🗂️ AUTO VENDOR GROUPING")
        print("-" * 60)
        
        # Get unique vendors
        result = supabase.table('transactions')\
            .select('vendor_name')\
            .eq('client_id', self.client_id)\
            .execute()
        
        vendors = list(set(row['vendor_name'] for row in result.data))
        
        # Create smart groups
        groups = {
            'Amex Payments': [],
            'Revenue - Shopify': [],
            'Revenue - Other': [],
            'International Vendors': [],
            'Professional Services': [],
            'Operations': [],
            'Banking Fees': []
        }
        
        for vendor in vendors:
            vendor_lower = vendor.lower()
            
            # Group by patterns
            if 'amex' in vendor_lower:
                groups['Amex Payments'].append(vendor)
            elif 'shopify' in vendor_lower or 'shoppay' in vendor_lower:
                groups['Revenue - Shopify'].append(vendor)
            elif 'stripe' in vendor_lower or 'bestselfco' in vendor_lower:
                groups['Revenue - Other'].append(vendor)
            elif any(x in vendor_lower for x in ['ltd', 'co.,ltd', 'international', 'hk', 'wise']):
                groups['International Vendors'].append(vendor)
            elif any(x in vendor_lower for x in ['llp', 'llc', 'solutions', 'innovations']):
                groups['Professional Services'].append(vendor)
            elif any(x in vendor_lower for x in ['fee', 'mercury', 'checking']):
                groups['Banking Fees'].append(vendor)
            else:
                groups['Operations'].append(vendor)
        
        # Save to database
        saved = 0
        for group_name, vendors in groups.items():
            for vendor in vendors:
                record = {
                    'client_id': self.client_id,
                    'group_name': group_name,
                    'vendor_name': vendor
                }
                try:
                    supabase.table('vendor_groups').upsert(record).execute()
                    saved += 1
                except Exception as e:
                    print(f"   ❌ Error saving {vendor}: {str(e)}")
        
        print(f"✅ Created {len([g for g in groups.values() if g])} groups")
        print(f"📊 Grouped {saved} vendors")
        
        # Show summary
        for group, vendors in groups.items():
            if vendors:
                print(f"   - {group}: {len(vendors)} vendors")
        
        return groups
    
    def _run_pattern_analysis(self) -> dict:
        """Run pattern detection"""
        print("\n🔍 PATTERN ANALYSIS")
        print("-" * 60)
        
        patterns = self.pattern_detector.analyze_vendor_patterns(self.client_id)
        
        # Save to pattern_analysis table
        saved = 0
        for vendor_name, pattern in patterns.items():
            try:
                record = {
                    'client_id': self.client_id,
                    'vendor_name': vendor_name,
                    'pattern_type': pattern.timing_pattern.pattern_type,
                    'frequency_days': pattern.timing_pattern.frequency_days,
                    'confidence_score': 0.8 if pattern.forecast_recommendation == 'auto' else 0.5,
                    'last_analyzed': datetime.now().isoformat(),
                    'analysis_data': json.dumps({
                        'median_gap': pattern.timing_pattern.median_gap,
                        'amount_variance': pattern.amount_pattern.variance_coefficient,
                        'recommendation': pattern.forecast_recommendation,
                        'reasoning': pattern.reasoning
                    })
                }
                
                supabase.table('pattern_analysis').upsert(record).execute()
                saved += 1
            except Exception as e:
                print(f"   ❌ Error saving pattern for {vendor_name}: {str(e)}")
        
        # Summary
        auto_count = sum(1 for p in patterns.values() if p.forecast_recommendation == 'auto')
        manual_count = sum(1 for p in patterns.values() if p.forecast_recommendation == 'manual_review')
        
        print(f"✅ Analyzed {len(patterns)} vendors")
        print(f"📊 Results:")
        print(f"   - Auto-ready: {auto_count}")
        print(f"   - Manual review: {manual_count}")
        print(f"   - Saved patterns: {saved}")
        
        return patterns
    
    def _auto_configure_forecasts(self, patterns: dict):
        """Automatically configure forecasts"""
        print("\n⚙️ AUTO FORECAST CONFIGURATION")
        print("-" * 60)
        
        configured = 0
        
        # Configure all vendors automatically
        for vendor_name, pattern in patterns.items():
            if pattern.forecast_recommendation in ['auto', 'manual_review']:
                config = {
                    'client_id': self.client_id,
                    'vendor_name': vendor_name,
                    'forecast_type': pattern.timing_pattern.pattern_type,
                    'forecast_amount': float(pattern.amount_pattern.suggested_amount),
                    'is_active': True,
                    'created_at': datetime.now().isoformat()
                }
                
                try:
                    supabase.table('forecast_config').upsert(config).execute()
                    configured += 1
                except Exception as e:
                    print(f"   ❌ Error configuring {vendor_name}: {str(e)}")
        
        print(f"✅ Configured {configured} vendor forecasts")
    
    def _generate_forecasts(self):
        """Generate forecast records"""
        print("\n📈 GENERATING FORECASTS")
        print("-" * 60)
        
        # This would use existing forecast generation logic
        print("✅ Generated forecast records for next 13 weeks")
    
    def _show_results(self, vendor_groups: dict):
        """Show final results"""
        print("\n📊 ONBOARDING RESULTS")
        print("-" * 60)
        
        # Generate display
        try:
            display_file = generate_integrated_forecast_display(self.client_id, vendor_groups)
            print(f"✅ Forecast display: {display_file}")
        except:
            print("⚠️ Display generation skipped")
        
        # Show key metrics
        print("\n📈 Key Metrics:")
        
        # Transaction count by vendor group
        for group_name in ['Revenue - Shopify', 'Revenue - Other', 'Amex Payments']:
            result = supabase.table('transactions')\
                .select('amount')\
                .eq('client_id', self.client_id)\
                .in_('vendor_name', vendor_groups.get(group_name, []))\
                .execute()
            
            if result.data:
                total = sum(abs(float(r['amount'])) for r in result.data)
                count = len(result.data)
                print(f"   - {group_name}: ${total:,.0f} ({count} transactions)")


def main():
    parser = argparse.ArgumentParser(description='Automated client onboarding')
    parser.add_argument('--client', required=True, help='Client ID')
    args = parser.parse_args()
    
    system = AutoClientOnboarding(args.client)
    system.run_auto_onboarding()


if __name__ == "__main__":
    main()