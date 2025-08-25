#!/usr/bin/env python3
"""
Check existing Supabase tables
"""

import sys
sys.path.append('.')
from supabase_client import supabase

def check_tables():
    """Check what tables exist in Supabase"""
    try:
        # Try to query existing tables we know about
        tables_to_check = [
            'transactions',
            'vendors', 
            'vendor_groups',
            'vendor_group_mappings',
            'vendor_forecast_rules',
            'forecast_records',
            'cash_balances'
        ]
        
        print("🔍 Checking existing tables in Supabase:")
        print("=" * 50)
        
        for table in tables_to_check:
            try:
                result = supabase.table(table).select('*').limit(1).execute()
                print(f"✅ {table} - exists ({len(result.data)} sample records)")
                if result.data:
                    print(f"   Columns: {list(result.data[0].keys())}")
            except Exception as e:
                print(f"❌ {table} - does not exist or error: {str(e)[:100]}")
        
        print("\n" + "=" * 50)
        print("📊 Checking transactions table specifically:")
        
        try:
            result = supabase.table('transactions').select('*').limit(5).execute()
            print(f"Found {len(result.data)} transactions")
            if result.data:
                print("Sample transaction:", result.data[0])
        except Exception as e:
            print(f"Error querying transactions: {e}")
            
    except Exception as e:
        print(f"Error checking tables: {e}")

if __name__ == "__main__":
    check_tables()