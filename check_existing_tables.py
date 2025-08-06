#!/usr/bin/env python3
"""
Check what tables exist in the database and what data we have.
"""

import sys
sys.path.append('.')

from supabase_client import supabase

def check_database_tables():
    """Check what tables exist and what data we have."""
    print("🔍 CHECKING EXISTING DATABASE TABLES")
    print("=" * 50)
    
    # Check vendors table
    try:
        result = supabase.table('vendors').select('*').limit(5).execute()
        print(f"✅ vendors table exists - {len(result.data)} sample records")
        
        if result.data:
            print("Sample vendor record:")
            print(f"  {result.data[0]}")
            
        # Get unique display names for bestself
        display_result = supabase.table('vendors').select('display_name').eq(
            'client_id', 'bestself'
        ).execute()
        
        if display_result.data:
            display_names = list(set(v['display_name'] for v in display_result.data if v['display_name']))
            print(f"\n📊 Found {len(display_names)} unique display names for bestself:")
            for name in display_names[:10]:  # Show first 10
                print(f"  • {name}")
                
    except Exception as e:
        print(f"❌ vendors table error: {e}")
    
    # Check transactions table
    try:
        result = supabase.table('transactions').select('*').limit(5).execute()
        print(f"\n✅ transactions table exists - {len(result.data)} sample records")
        
        if result.data:
            print("Sample transaction record:")
            print(f"  {result.data[0]}")
        
        # Count transactions for bestself
        count_result = supabase.table('transactions').select('*').eq(
            'client_id', 'bestself'
        ).execute()
        print(f"📊 Total transactions for bestself: {len(count_result.data)}")
        
    except Exception as e:
        print(f"❌ transactions table error: {e}")
    
    # Check if vendor_groups table exists
    try:
        result = supabase.table('vendor_groups').select('*').limit(1).execute()
        print(f"\n✅ vendor_groups table exists")
    except Exception as e:
        print(f"\n❌ vendor_groups table does not exist: {e}")
    
    # Check if forecasts table exists
    try:
        result = supabase.table('forecasts').select('*').limit(1).execute()
        print(f"✅ forecasts table exists")
    except Exception as e:
        print(f"❌ forecasts table does not exist: {e}")

def create_temporary_vendor_groups():
    """Create vendor groups from existing display names."""
    print("\n🔧 CREATING TEMPORARY VENDOR GROUPS FROM DISPLAY NAMES")
    print("=" * 60)
    
    try:
        # First, create the vendor_groups table using SQL
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS vendor_groups (
            id SERIAL PRIMARY KEY,
            client_id VARCHAR(255) NOT NULL,
            group_name VARCHAR(255) NOT NULL,
            vendor_display_names TEXT[] NOT NULL,
            pattern_frequency VARCHAR(20),
            pattern_timing VARCHAR(50),
            pattern_confidence DECIMAL(5,4) DEFAULT 0.0,
            forecast_method VARCHAR(20) DEFAULT 'weighted_average',
            weighted_average_amount DECIMAL(15,2) DEFAULT 0.0,
            forecast_frequency VARCHAR(20),
            forecast_day VARCHAR(50),
            forecast_amount DECIMAL(15,2),
            forecast_confidence DECIMAL(5,4),
            is_revenue BOOLEAN DEFAULT true,
            category VARCHAR(100),
            is_active BOOLEAN DEFAULT true,
            last_analyzed DATE,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(client_id, group_name)
        );
        """
        
        # Execute the SQL
        result = supabase.rpc('sql_query', {'query': create_table_sql}).execute()
        print("✅ vendor_groups table created successfully")
        
        # Get unique display names for bestself
        display_result = supabase.table('vendors').select('display_name').eq(
            'client_id', 'bestself'
        ).execute()
        
        if display_result.data:
            display_names = list(set(v['display_name'] for v in display_result.data if v['display_name']))
            
            # Create a vendor group for each display name
            created_count = 0
            for display_name in display_names:
                try:
                    group_data = {
                        'client_id': 'bestself',
                        'group_name': display_name,
                        'vendor_display_names': [display_name],
                        'is_active': True,
                        'is_revenue': True if 'Revenue' in display_name else False
                    }
                    
                    result = supabase.table('vendor_groups').insert(group_data).execute()
                    if result.data:
                        created_count += 1
                        
                except Exception as e:
                    print(f"  ⚠️  Failed to create group for {display_name}: {e}")
            
            print(f"✅ Created {created_count} vendor groups from display names")
            return True
        
    except Exception as e:
        print(f"❌ Error creating temporary vendor groups: {e}")
        return False

def main():
    """Main function."""
    print("🚀 DATABASE ANALYSIS AND SETUP")
    print("=" * 70)
    
    # Check existing tables
    check_database_tables()
    
    # Try to create temporary vendor groups
    create_temporary_vendor_groups()

if __name__ == "__main__":
    main()