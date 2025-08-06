#!/usr/bin/env python3
"""
Simplified Client Onboarding System
Works with existing database structure
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

class SimpleClientOnboarding:
    """Simplified onboarding that works with existing tables"""
    
    def __init__(self, client_id: str):
        self.client_id = client_id
        self.pattern_detector = PracticalPatternDetection()
        self.start_time = datetime.now()
        
    def run_complete_onboarding(self):
        """Run simplified onboarding process"""
        print(f"\\n🚀 SIMPLIFIED CLIENT ONBOARDING")
        print(f"Client: {self.client_id}")
        print("=" * 80)
        
        # Step 1: Verify Transactions
        print(f"\\n📊 STEP 1: Verify Transaction Data")
        print("-" * 60)
        transaction_count = self._verify_transactions()
        if transaction_count == 0:
            return
        
        # Step 2: Vendor Grouping
        print(f"\\n🗂️ STEP 2: Vendor Grouping")
        print("-" * 60)
        vendor_mappings = self._create_vendor_grouping()
        
        # Step 3: Pattern Detection
        print(f"\\n🔍 STEP 3: Pattern Detection")
        print("-" * 60)
        pattern_results = self._run_pattern_detection()
        
        # Step 4: Manual Configuration
        print(f"\\n⚙️ STEP 4: Manual Forecast Configuration")
        print("-" * 60)
        self._manual_configuration()
        
        # Step 5: Generate Display
        print(f"\\n📈 STEP 5: Generate Forecast Display")
        print("-" * 60)
        self._generate_display(vendor_mappings)
        
        # Complete
        elapsed_time = (datetime.now() - self.start_time).seconds / 60
        print(f"\\n✅ ONBOARDING COMPLETE!")
        print(f"⏱️ Total time: {elapsed_time:.1f} minutes")
    
    def _verify_transactions(self) -> int:
        """Verify client has transaction data"""
        try:
            # Get transaction count
            result = supabase.table('transactions').select('id', count='exact')\
                .eq('client_id', self.client_id)\
                .execute()
            
            transaction_count = result.count or 0
            
            if transaction_count == 0:
                print(f"❌ No transactions found for client: {self.client_id}")
                print("Please import transactions first")
                return 0
            
            # Get date range
            date_result = supabase.table('transactions')\
                .select('transaction_date')\
                .eq('client_id', self.client_id)\
                .order('transaction_date')\
                .limit(1)\
                .execute()
            
            first_date = date_result.data[0]['transaction_date'] if date_result.data else 'Unknown'
            
            print(f"✅ Found {transaction_count} transactions")
            print(f"📅 Date range: {first_date} to present")
            
            return transaction_count
            
        except Exception as e:
            print(f"❌ Error checking transactions: {str(e)}")
            return 0
    
    def _create_vendor_grouping(self) -> dict:
        """Create vendor grouping interface"""
        try:
            print("Creating vendor grouping interface...")
            interface_file = create_simple_grouping_interface(self.client_id)
            
            print(f"\\n📋 Opening grouping interface in browser...")
            webbrowser.open(f"file://{interface_file}")
            
            print("\\n⏳ Please complete vendor grouping in the browser")
            print("Group similar vendors together (e.g., 'AMEX EPAYMENT' + 'Amex' = 'Amex Payments')")
            
            input("\\nPress Enter when you've completed vendor grouping...")
            
            # For demo, return some example mappings
            return {
                "Amex Payments": ["AMEX EPAYMENT", "Amex"],
                "State Sales Tax": ["VA DEPT TAXATION", "NC DEPT REVENUE"],
                "Stripe Revenue": ["Stripe", "STRIPE PAYMENTS"]
            }
            
        except Exception as e:
            print(f"❌ Error creating vendor grouping: {str(e)}")
            return {}
    
    def _run_pattern_detection(self) -> dict:
        """Run pattern detection analysis"""
        try:
            print("Analyzing vendor patterns...")
            
            # Get patterns for all vendors
            vendor_patterns = self.pattern_detector.analyze_vendor_patterns(self.client_id)
            
            # Summarize results
            auto_count = sum(1 for p in vendor_patterns.values() if p.forecast_recommendation == 'auto')
            manual_count = sum(1 for p in vendor_patterns.values() if p.forecast_recommendation == 'manual_review')
            
            print(f"\\n📊 Pattern Detection Results:")
            print(f"├── Auto-ready: {auto_count} vendors")
            print(f"├── Manual setup needed: {manual_count} vendors")
            print(f"└── Total forecastable: {auto_count + manual_count} vendors")
            
            return vendor_patterns
            
        except Exception as e:
            print(f"❌ Error in pattern detection: {str(e)}")
            return {}
    
    def _manual_configuration(self):
        """Configure manual forecasts"""
        try:
            print("Creating manual forecast configuration interface...")
            interface_file = create_manual_forecast_interface_with_history(self.client_id)
            
            print(f"\\n📋 Opening manual forecast interface in browser...")
            webbrowser.open(f"file://{interface_file}")
            
            print("\\n⏳ Please configure forecasts for irregular vendors")
            print("Review transaction history and set appropriate patterns")
            
            input("\\nPress Enter when you've completed forecast configuration...")
            
            print("✅ Manual configuration completed")
            
        except Exception as e:
            print(f"❌ Error in manual configuration: {str(e)}")
    
    def _generate_display(self, vendor_mappings: dict):
        """Generate final display"""
        try:
            print("Generating integrated forecast display...")
            
            display_file = generate_integrated_forecast_display(self.client_id, vendor_mappings)
            
            print(f"\\n📊 Opening forecast display in browser...")
            webbrowser.open(f"file://{display_file}")
            
            print("\\n✅ Forecast display generated!")
            print("📅 Shows 13-week cash flow forecast")
            print("✏️ Double-click any cell to edit forecasts")
            
        except Exception as e:
            print(f"❌ Error generating display: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Simplified client onboarding')
    parser.add_argument('--client', required=True, help='Client ID to onboard')
    args = parser.parse_args()
    
    # Run onboarding
    system = SimpleClientOnboarding(args.client)
    system.run_complete_onboarding()

if __name__ == "__main__":
    main()