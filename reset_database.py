#!/usr/bin/env python3
"""
Database Reset Script
Cleans all data for fresh testing of onboarding system
"""

import sys
sys.path.append('.')

from supabase_client import supabase

def reset_database():
    """Reset all tables to fresh state"""
    print("🗑️ RESETTING DATABASE FOR FRESH TESTING")
    print("=" * 80)
    
    # List of tables to clear
    tables_to_clear = [
        'forecasts',
        'vendor_mappings', 
        'pattern_results',
        'forecast_configs',
        'onboarding_status',
        'forecast_variances',
        'client_settings',
        'transactions'  # Clear all imported transaction data
    ]
    
    for table in tables_to_clear:
        try:
            print(f"🧹 Clearing {table}...")
            # Use different approach for transactions table with UUID
            if table == 'transactions':
                # For transactions, delete by client_id to handle UUID primary key
                result = supabase.table(table).delete().gte('created_at', '2000-01-01').execute()
            else:
                result = supabase.table(table).delete().neq('id', 0).execute()
            print(f"   ✅ Cleared {table}")
        except Exception as e:
            print(f"   ⚠️ Error clearing {table}: {str(e)}")
            # Continue with other tables
    
    print("\n✅ DATABASE RESET COMPLETE")
    print("Ready for fresh onboarding test")
    print("\nNext steps for testing:")
    print("1. Import fresh transaction data")
    print("2. Run: python3 onboard_client.py --client=testclient")

def confirm_reset():
    """Confirm before deleting data"""
    print("⚠️ WARNING: This will delete ALL data from the database!")
    print("This includes:")
    print("- All transactions")
    print("- All forecasts") 
    print("- All vendor groupings")
    print("- All pattern results")
    print("- All configuration data")
    
    confirm = input("\nAre you sure you want to proceed? Type 'RESET' to confirm: ")
    
    if confirm == 'RESET':
        return True
    else:
        print("❌ Reset cancelled")
        return False

def main():
    """Main reset function"""
    if confirm_reset():
        reset_database()
    else:
        print("Database reset aborted")

if __name__ == "__main__":
    main()