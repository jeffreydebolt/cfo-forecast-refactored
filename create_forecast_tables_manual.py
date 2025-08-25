#!/usr/bin/env python3
"""
Manually create forecast tables in Supabase
"""

import sys
sys.path.append('.')
from supabase_client import supabase

def create_table_if_not_exists(table_name: str, create_sql: str):
    """Try to create a table, handle if it already exists"""
    try:
        # First check if table exists by trying a simple query
        result = supabase.table(table_name).select('*').limit(1).execute()
        print(f"✅ Table {table_name} already exists")
        return True
    except:
        # Table doesn't exist, try to create it
        print(f"🔨 Creating table {table_name}...")
        try:
            # We can't execute DDL directly through Supabase client
            # Let's create the data using the existing table structure
            print(f"⚠️ Cannot create {table_name} via client - needs to be done in Supabase dashboard")
            return False
        except Exception as e:
            print(f"❌ Error creating {table_name}: {e}")
            return False

def setup_tables_manually():
    """Setup tables manually by working with existing structure"""
    
    print("🗄️ Setting up forecast tables manually...")
    print("Since we can't execute DDL via the client, we'll work with the existing structure")
    
    # Check vendor_groups table structure
    try:
        # Add missing columns to vendor_groups if needed
        print("\n📋 Checking vendor_groups table structure...")
        result = supabase.table('vendor_groups').select('*').limit(1).execute()
        if result.data:
            columns = list(result.data[0].keys()) if result.data else []
            print(f"Existing columns in vendor_groups: {columns}")
        
        # Since vendor_groups exists but might be missing columns, let's try to insert a test record
        test_group = {
            'client_id': 'test',
            'group_name': 'test_group',
            'display_name': 'Test Group',
            'category': 'revenue',
            'subcategory': 'core_capital',
            'is_inflow': True
        }
        
        try:
            result = supabase.table('vendor_groups').insert([test_group]).execute()
            print("✅ vendor_groups table has correct structure")
            # Delete the test record
            supabase.table('vendor_groups').delete().eq('client_id', 'test').execute()
        except Exception as e:
            print(f"❌ vendor_groups missing columns: {e}")
            
    except Exception as e:
        print(f"Error checking vendor_groups: {e}")
    
    print("\n" + "="*60)
    print("🚨 MANUAL SETUP REQUIRED")
    print("The forecast tables need to be created in the Supabase dashboard.")
    print("Please run the SQL in database/forecast_schema.sql manually.")
    print("=" * 60)

if __name__ == "__main__":
    setup_tables_manually()