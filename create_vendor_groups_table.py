#!/usr/bin/env python3
"""
Create vendor_groups table for logical vendor grouping.
"""

from supabase_client import supabase

def create_vendor_groups_table():
    """Create the vendor_groups table if it doesn't exist."""
    
    # SQL to create vendor_groups table
    sql = """
    CREATE TABLE IF NOT EXISTS vendor_groups (
        id SERIAL PRIMARY KEY,
        client_id VARCHAR(255) NOT NULL,
        group_name VARCHAR(255) NOT NULL,
        vendor_display_names TEXT[] NOT NULL,
        is_revenue BOOLEAN DEFAULT true,
        category VARCHAR(255) DEFAULT 'Revenue',
        forecast_frequency VARCHAR(50),
        forecast_day INTEGER,
        forecast_amount DECIMAL(15,2) DEFAULT 0.00,
        forecast_confidence DECIMAL(5,4) DEFAULT 0.00,
        forecast_method VARCHAR(50) DEFAULT 'pattern_detected',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        UNIQUE(client_id, group_name)
    );
    
    -- Create index for faster queries
    CREATE INDEX IF NOT EXISTS idx_vendor_groups_client ON vendor_groups(client_id);
    """
    
    try:
        result = supabase.rpc('exec_sql', {'sql': sql}).execute()
        print("✅ Created vendor_groups table successfully")
        return True
    except Exception as e:
        print(f"❌ Error creating vendor_groups table: {e}")
        # Try alternative approach - direct SQL execution might not work
        # Let's create it manually through the Supabase dashboard or use a different approach
        return False

def check_table_exists():
    """Check if vendor_groups table exists by trying to query it."""
    try:
        result = supabase.table('vendor_groups').select('*').limit(1).execute()
        print("✅ vendor_groups table exists")
        return True
    except Exception as e:
        print(f"⚠️  vendor_groups table doesn't exist: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Setting up vendor_groups table...")
    
    if not check_table_exists():
        print("Creating vendor_groups table...")
        create_vendor_groups_table()
    else:
        print("Table already exists, nothing to do.")