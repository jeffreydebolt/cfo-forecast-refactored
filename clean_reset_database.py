#!/usr/bin/env python3
"""
Clean Database Reset Script
Properly handles all 7 existing tables + new tables
"""

import sys
sys.path.append('.')

from supabase_client import supabase

def reset_all_data():
    """Reset all data from all tables"""
    print("🗑️ RESETTING ALL DATABASE DATA")
    print("=" * 80)
    
    # All tables to clear
    all_tables = [
        # Existing 7 tables
        'actuals_import',
        'forecast_config', 
        'forecasts',
        'pattern_analysis',
        'transactions',
        'vendor_groups',
        'vendors',
        
        # New tables (if they exist)
        'onboarding_status',
        'forecast_variances',
        'client_settings'
    ]
    
    success_count = 0
    fail_count = 0
    
    for table in all_tables:
        try:
            print(f"🧹 Clearing {table}...")
            
            # Different approach based on table
            if table == 'transactions':
                # Handle UUID primary key
                result = supabase.table(table).delete().gte('created_at', '1900-01-01').execute()
            else:
                # Try standard delete first
                try:
                    result = supabase.table(table).delete().neq('id', 0).execute()
                except:
                    # If that fails, try created_at approach
                    result = supabase.table(table).delete().gte('created_at', '1900-01-01').execute()
            
            # Check if we deleted anything
            if hasattr(result, 'data'):
                print(f"   ✅ Cleared {table}")
                success_count += 1
            else:
                print(f"   ✅ Cleared {table} (no data returned)")
                success_count += 1
                
        except Exception as e:
            error_msg = str(e)
            if 'does not exist' in error_msg:
                print(f"   ⏭️ Skipped {table} (table doesn't exist)")
            else:
                print(f"   ❌ Error clearing {table}: {error_msg}")
                fail_count += 1
    
    print(f"\n📊 SUMMARY")
    print(f"✅ Successfully cleared: {success_count} tables")
    if fail_count > 0:
        print(f"❌ Failed to clear: {fail_count} tables")
    
    print("\n✅ DATABASE RESET COMPLETE")
    print("Ready for fresh data import")

def confirm_reset():
    """Confirm before deleting data"""
    print("⚠️ WARNING: This will delete ALL data from ALL tables!")
    print("\nThis includes:")
    print("- All transactions")
    print("- All forecasts") 
    print("- All vendor data")
    print("- All pattern analysis")
    print("- All configurations")
    print("- All client settings")
    
    confirm = input("\nType 'RESET' to confirm deletion: ")
    
    if confirm == 'RESET':
        return True
    else:
        print("❌ Reset cancelled")
        return False

def main():
    """Main reset function"""
    if confirm_reset():
        reset_all_data()
    else:
        print("Database reset aborted")

if __name__ == "__main__":
    main()