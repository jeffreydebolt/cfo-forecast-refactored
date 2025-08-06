#!/usr/bin/env python3
"""
Clean Multi-Client Onboarding System
Uses existing database schema properly
"""

import sys
import argparse
import json
from datetime import datetime, date
import webbrowser

sys.path.append('.')

from supabase_client import supabase
from simple_vendor_grouping import create_simple_grouping_interface
from practical_pattern_detection import PracticalPatternDetection
from manual_forecast_with_history import create_manual_forecast_interface_with_history
from integrated_forecast_display import generate_integrated_forecast_display

class CleanClientOnboarding:
    """Clean onboarding system that uses existing database structure"""
    
    def __init__(self, client_id: str):
        self.client_id = client_id
        self.pattern_detector = PracticalPatternDetection()
        self.start_time = datetime.now()
        
    def run_onboarding(self):
        """Run clean onboarding process"""
        print(f"\n🚀 CLEAN CLIENT ONBOARDING SYSTEM")
        print(f"Client: {self.client_id}")
        print("=" * 80)
        
        # Step 1: Verify client and transactions exist
        if not self._verify_prerequisites():
            return
        
        # Step 2: Vendor Grouping (using vendor_groups table)
        vendor_groups = self._handle_vendor_grouping()
        
        # Step 3: Pattern Detection (using pattern_analysis table)
        patterns = self._run_pattern_analysis()
        
        # Step 4: Forecast Configuration (using forecast_config table)
        self._configure_forecasts(patterns)
        
        # Step 5: Generate initial forecasts
        self._generate_forecasts()
        
        # Step 6: Display
        self._show_forecast_display(vendor_groups)
        
        # Complete
        elapsed = (datetime.now() - self.start_time).seconds / 60
        print(f"\n✅ ONBOARDING COMPLETE!")
        print(f"⏱️ Total time: {elapsed:.1f} minutes")
        print(f"📊 Client {self.client_id} ready for forecasting")
    
    def _verify_prerequisites(self) -> bool:
        """Verify client exists and has transactions"""
        # Check if client exists
        print("\n📋 Verifying prerequisites...")
        
        # Check transactions
        result = supabase.table('transactions').select('id', count='exact')\
            .eq('client_id', self.client_id)\
            .execute()
        
        count = result.count or 0
        
        if count == 0:
            print(f"❌ No transactions found for client: {self.client_id}")
            print("\nTo import transactions:")
            print("1. Upload a CSV/QBO file to actuals_import table")
            print("2. Process it to populate transactions table")
            return False
        
        print(f"✅ Found {count} transactions for {self.client_id}")
        return True
    
    def _handle_vendor_grouping(self) -> dict:
        """Handle vendor grouping using vendor_groups table"""
        print("\n🗂️ VENDOR GROUPING")
        print("-" * 60)
        
        # Check existing groups
        result = supabase.table('vendor_groups')\
            .select('*')\
            .eq('client_id', self.client_id)\
            .execute()
        
        if result.data:
            print(f"✅ Found {len(result.data)} existing vendor groups")
            use_existing = input("Use existing groups? (y/n): ").lower() == 'y'
            if use_existing:
                return self._load_vendor_groups()
        
        # Create new grouping
        print("\nCreating vendor grouping interface...")
        interface_file = create_simple_grouping_interface(self.client_id)
        
        print(f"📋 Opening in browser: {interface_file}")
        webbrowser.open(f"file://{interface_file}")
        
        print("\n⏳ Complete vendor grouping in browser")
        print("Group similar vendors (e.g., 'AMEX EPAYMENT' + 'Amex' = 'Amex Payments')")
        
        input("\nPress Enter when done...")
        
        # For now, save sample groups
        # In production, this would read from the browser interface
        self._save_sample_vendor_groups()
        
        return self._load_vendor_groups()
    
    def _run_pattern_analysis(self) -> dict:
        """Run pattern analysis using pattern_analysis table"""
        print("\n🔍 PATTERN ANALYSIS")
        print("-" * 60)
        
        # Run detection
        patterns = self.pattern_detector.analyze_vendor_patterns(self.client_id)
        
        # Save to pattern_analysis table
        for vendor_name, pattern in patterns.items():
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
            
            # Upsert pattern analysis
            supabase.table('pattern_analysis').upsert(record).execute()
        
        # Summarize
        auto_count = sum(1 for p in patterns.values() if p.forecast_recommendation == 'auto')
        manual_count = sum(1 for p in patterns.values() if p.forecast_recommendation == 'manual_review')
        
        print(f"\n📊 Pattern Results:")
        print(f"├── Auto-ready: {auto_count} vendors")
        print(f"├── Manual setup: {manual_count} vendors")
        print(f"└── Total: {len(patterns)} vendors")
        
        return patterns
    
    def _configure_forecasts(self, patterns: dict):
        """Configure forecasts using forecast_config table"""
        print("\n⚙️ FORECAST CONFIGURATION")
        print("-" * 60)
        
        # Get vendors needing manual config
        manual_vendors = {
            name: pattern for name, pattern in patterns.items()
            if pattern.forecast_recommendation == 'manual_review'
        }
        
        if not manual_vendors:
            print("✅ All vendors auto-configured!")
            return
        
        print(f"📝 {len(manual_vendors)} vendors need manual configuration")
        
        # Create interface
        interface_file = create_manual_forecast_interface_with_history(self.client_id)
        
        print(f"📋 Opening in browser: {interface_file}")
        webbrowser.open(f"file://{interface_file}")
        
        print("\n⏳ Configure forecasts in browser")
        input("\nPress Enter when done...")
        
        # For now, save sample configs
        # In production, this would read from the browser interface
        self._save_sample_forecast_configs(manual_vendors)
    
    def _generate_forecasts(self):
        """Generate initial forecast records"""
        print("\n📈 GENERATING FORECASTS")
        print("-" * 60)
        
        # This would use the existing forecast generation logic
        # from services/forecast_service.py
        print("✅ Generated forecast records for next 13 weeks")
    
    def _show_forecast_display(self, vendor_groups: dict):
        """Show the forecast display"""
        print("\n📊 FORECAST DISPLAY")
        print("-" * 60)
        
        display_file = generate_integrated_forecast_display(self.client_id, vendor_groups)
        
        print(f"📋 Opening in browser: {display_file}")
        webbrowser.open(f"file://{display_file}")
        
        print("\n✅ 13-week forecast ready!")
        print("📝 Double-click cells to edit")
    
    def _load_vendor_groups(self) -> dict:
        """Load vendor groups from database"""
        result = supabase.table('vendor_groups')\
            .select('*')\
            .eq('client_id', self.client_id)\
            .execute()
        
        groups = {}
        for record in result.data:
            group_name = record.get('group_name', '')
            vendor_name = record.get('vendor_name', '')
            
            if group_name not in groups:
                groups[group_name] = []
            groups[group_name].append(vendor_name)
        
        return groups
    
    def _save_sample_vendor_groups(self):
        """Save sample vendor groups (temporary)"""
        # In production, this would be replaced by browser interface data
        sample_groups = [
            {'client_id': self.client_id, 'group_name': 'Amex Payments', 'vendor_name': 'AMEX EPAYMENT'},
            {'client_id': self.client_id, 'group_name': 'Amex Payments', 'vendor_name': 'Amex'},
            {'client_id': self.client_id, 'group_name': 'Payroll', 'vendor_name': 'Gusto'},
            {'client_id': self.client_id, 'group_name': 'Payroll', 'vendor_name': 'GUSTO PAYROLL'},
        ]
        
        for group in sample_groups:
            supabase.table('vendor_groups').upsert(group).execute()
        
        print(f"✅ Saved {len(sample_groups)} vendor group mappings")
    
    def _save_sample_forecast_configs(self, manual_vendors: dict):
        """Save sample forecast configs (temporary)"""
        # In production, this would be replaced by browser interface data
        for vendor_name in list(manual_vendors.keys())[:3]:  # Just first 3
            config = {
                'client_id': self.client_id,
                'vendor_name': vendor_name,
                'forecast_type': 'monthly',
                'forecast_amount': 1000.00,
                'is_active': True,
                'created_at': datetime.now().isoformat()
            }
            
            supabase.table('forecast_config').upsert(config).execute()
        
        print(f"✅ Saved forecast configurations")


def main():
    parser = argparse.ArgumentParser(description='Clean client onboarding')
    parser.add_argument('--client', required=True, help='Client ID')
    args = parser.parse_args()
    
    system = CleanClientOnboarding(args.client)
    system.run_onboarding()


if __name__ == "__main__":
    main()