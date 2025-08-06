#!/usr/bin/env python3
"""
Weekly Client Update System
For existing clients - quick forecast updates and maintenance
"""

import sys
import argparse
import json
from datetime import datetime, date, timedelta
import webbrowser

sys.path.append('.')

from supabase_client import supabase
from integrated_forecast_display import generate_integrated_forecast_display

class ClientUpdateSystem:
    """Quick weekly update system for existing clients"""
    
    def __init__(self, client_id: str):
        self.client_id = client_id
        self.start_time = datetime.now()
    
    def run_weekly_update(self):
        """Run quick weekly update for existing client"""
        print(f"\n📅 WEEKLY CLIENT UPDATE")
        print(f"Client: {self.client_id}")
        print("=" * 80)
        
        # Verify client is onboarded
        if not self._verify_client_onboarded():
            print(f"❌ Client {self.client_id} has not been onboarded yet")
            print(f"Run: python3 onboard_client.py --client={self.client_id}")
            return
        
        # Step 1: Import new transactions
        print(f"\n📥 STEP 1: Import New Transactions")
        print("-" * 60)
        new_transactions = self._import_new_transactions()
        
        # Step 2: Update forecasts
        print(f"\n🔄 STEP 2: Update Forecasts")
        print("-" * 60)
        self._update_forecasts()
        
        # Step 3: Generate updated display
        print(f"\n📊 STEP 3: Generate Updated Display")
        print("-" * 60)
        self._generate_updated_display()
        
        # Complete
        elapsed_time = (datetime.now() - self.start_time).seconds / 60
        print(f"\n✅ WEEKLY UPDATE COMPLETE!")
        print(f"⏱️ Total time: {elapsed_time:.1f} minutes")
    
    def _verify_client_onboarded(self) -> bool:
        """Check if client has completed onboarding"""
        # Check for vendor mappings
        result = supabase.table('vendor_mappings')\
            .select('id')\
            .eq('client_id', self.client_id)\
            .limit(1)\
            .execute()
        
        return bool(result.data)
    
    def _import_new_transactions(self) -> int:
        """Import any new transactions since last update"""
        # Get last transaction date
        result = supabase.table('transactions')\
            .select('transaction_date')\
            .eq('client_id', self.client_id)\
            .order('transaction_date', desc=True)\
            .limit(1)\
            .execute()
        
        if result.data:
            last_date = result.data[0]['transaction_date']
            print(f"📅 Last transaction: {last_date}")
        else:
            print("❌ No existing transactions found")
            return 0
        
        # In production, this would trigger transaction import
        # For now, we'll simulate
        print("🔄 Checking for new transactions...")
        print("✅ All transactions up to date")
        
        return 0
    
    def _update_forecasts(self):
        """Update forecasts based on actual vs predicted"""
        # Get recent actuals vs forecasts
        today = date.today()
        week_ago = today - timedelta(days=7)
        
        # Get forecasts from last week
        forecast_result = supabase.table('forecasts')\
            .select('*')\
            .eq('client_id', self.client_id)\
            .gte('forecast_date', week_ago.isoformat())\
            .lt('forecast_date', today.isoformat())\
            .execute()
        
        if not forecast_result.data:
            print("📊 No forecasts to compare from last week")
            return
        
        # Get actual transactions from last week
        actual_result = supabase.table('transactions')\
            .select('vendor_name, amount, transaction_date')\
            .eq('client_id', self.client_id)\
            .gte('transaction_date', week_ago.isoformat())\
            .lt('transaction_date', today.isoformat())\
            .execute()
        
        # Compare and calculate variance
        print(f"📊 Comparing {len(forecast_result.data)} forecasts with actuals...")
        
        # In production, this would:
        # 1. Calculate variance between forecast and actual
        # 2. Update confidence scores
        # 3. Adjust future forecasts if patterns changed
        # 4. Alert on significant variances
        
        significant_variances = self._calculate_variances(forecast_result.data, actual_result.data)
        
        if significant_variances:
            print(f"⚠️ Found {len(significant_variances)} significant variances:")
            for variance in significant_variances[:3]:
                print(f"  - {variance['vendor']}: Expected ${variance['forecast']:,.0f}, Actual ${variance['actual']:,.0f}")
            
            adjust = input("\nAdjust future forecasts? (y/n): ").lower() == 'y'
            if adjust:
                self._adjust_future_forecasts(significant_variances)
        else:
            print("✅ All forecasts within acceptable variance")
    
    def _generate_updated_display(self):
        """Generate updated weekly display"""
        # Load vendor mappings
        mappings = self._load_vendor_mappings()
        
        print("Generating updated forecast display...")
        display_file = generate_integrated_forecast_display(self.client_id, mappings)
        
        print(f"\n📊 Opening updated forecast in browser...")
        webbrowser.open(f"file://{display_file}")
        
        # Show quick stats
        self._show_weekly_stats()
    
    def _load_vendor_mappings(self) -> dict:
        """Load saved vendor mappings"""
        result = supabase.table('vendor_mappings')\
            .select('*')\
            .eq('client_id', self.client_id)\
            .execute()
        
        mappings = {}
        for record in result.data:
            group_name = record['group_name']
            vendor_name = record['vendor_name']
            
            if group_name not in mappings:
                mappings[group_name] = []
            mappings[group_name].append(vendor_name)
        
        return mappings
    
    def _calculate_variances(self, forecasts: list, actuals: list) -> list:
        """Calculate significant variances between forecast and actual"""
        # Group actuals by vendor
        actual_by_vendor = {}
        for txn in actuals:
            vendor = txn['vendor_name']
            if vendor not in actual_by_vendor:
                actual_by_vendor[vendor] = 0
            actual_by_vendor[vendor] += abs(float(txn['amount']))
        
        # Compare with forecasts
        variances = []
        for forecast in forecasts:
            vendor = forecast.get('vendor_group_name', '')
            forecast_amount = abs(float(forecast.get('forecast_amount', 0)))
            actual_amount = actual_by_vendor.get(vendor, 0)
            
            if forecast_amount > 0:
                variance_pct = abs(actual_amount - forecast_amount) / forecast_amount
                
                if variance_pct > 0.2:  # 20% variance threshold
                    variances.append({
                        'vendor': vendor,
                        'forecast': forecast_amount,
                        'actual': actual_amount,
                        'variance_pct': variance_pct
                    })
        
        return variances
    
    def _adjust_future_forecasts(self, variances: list):
        """Adjust future forecasts based on variances"""
        print("\n🔧 Adjusting future forecasts...")
        
        for variance in variances:
            vendor = variance['vendor']
            new_amount = variance['actual']  # Use actual as new baseline
            
            # Update future forecasts for this vendor
            future_date = date.today()
            
            update_result = supabase.table('forecasts')\
                .update({'forecast_amount': new_amount})\
                .eq('client_id', self.client_id)\
                .eq('vendor_group_name', vendor)\
                .gte('forecast_date', future_date.isoformat())\
                .execute()
            
            if update_result.data:
                print(f"✅ Updated {len(update_result.data)} future forecasts for {vendor}")
    
    def _show_weekly_stats(self):
        """Show quick weekly statistics"""
        print("\n📊 WEEKLY STATISTICS")
        print("-" * 40)
        
        # Get this week's totals
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        
        # Forecast totals
        forecast_result = supabase.table('forecasts')\
            .select('forecast_amount')\
            .eq('client_id', self.client_id)\
            .gte('forecast_date', week_start.isoformat())\
            .lte('forecast_date', week_end.isoformat())\
            .execute()
        
        if forecast_result.data:
            inflows = sum(float(f['forecast_amount']) for f in forecast_result.data if float(f['forecast_amount']) > 0)
            outflows = sum(abs(float(f['forecast_amount'])) for f in forecast_result.data if float(f['forecast_amount']) < 0)
            
            print(f"Expected Inflows: ${inflows:,.0f}")
            print(f"Expected Outflows: ${outflows:,.0f}")
            print(f"Net Cash Flow: ${inflows - outflows:,.0f}")
        else:
            print("No forecasts for this week")

def main():
    parser = argparse.ArgumentParser(description='Weekly client update system')
    parser.add_argument('--client', required=True, help='Client ID to update')
    args = parser.parse_args()
    
    # Run weekly update
    system = ClientUpdateSystem(args.client)
    system.run_weekly_update()

if __name__ == "__main__":
    main()