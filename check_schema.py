#!/usr/bin/env python3
"""
Check the actual database schema to understand table structure.
"""

from supabase_client import supabase

def check_table_structure():
    """Check what tables and columns exist."""
    
    print("🔍 Checking database schema...")
    
    # Try to get table info using information_schema
    try:
        # Get all tables
        tables_response = supabase.rpc('get_tables').execute()
        print("Available tables:")
        print(tables_response.data)
    except Exception as e:
        print(f"Could not get table list: {e}")
    
    # Try to query transactions table with minimal fields
    try:
        print("\n🔍 Checking transactions table structure...")
        response = supabase.table('transactions').select('*').limit(1).execute()
        if response.data:
            print("Transactions table columns:")
            for key in response.data[0].keys():
                print(f"  - {key}")
        else:
            print("No data in transactions table")
    except Exception as e:
        print(f"Error checking transactions: {e}")
    
    # Try to query vendors table
    try:
        print("\n🔍 Checking vendors table structure...")
        response = supabase.table('vendors').select('*').limit(1).execute()
        if response.data:
            print("Vendors table columns:")
            for key in response.data[0].keys():
                print(f"  - {key}")
        else:
            print("No data in vendors table")
    except Exception as e:
        print(f"Error checking vendors: {e}")
    
    # Check for other potential tables
    potential_tables = ['bank_transactions', 'transaction_data', 'weekly_cashflow', 'forecast_data']
    for table_name in potential_tables:
        try:
            print(f"\n🔍 Checking {table_name} table...")
            response = supabase.table(table_name).select('*').limit(1).execute()
            if response.data:
                print(f"{table_name} table columns:")
                for key in response.data[0].keys():
                    print(f"  - {key}")
            else:
                print(f"No data in {table_name} table")
        except Exception as e:
            print(f"Table {table_name} does not exist or error: {e}")

if __name__ == "__main__":
    check_table_structure()