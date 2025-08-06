#!/usr/bin/env python3
"""
Create the lean forecasting database tables.
"""

from supabase_client import supabase
import sys

def create_tables():
    """Create all tables for the lean forecasting system."""
    
    tables = {
        "vendor_groups": """
        CREATE TABLE IF NOT EXISTS vendor_groups (
            id SERIAL PRIMARY KEY,
            client_id VARCHAR(255) NOT NULL,
            group_name VARCHAR(255) NOT NULL,
            vendor_display_names TEXT[] NOT NULL,
            
            -- Pattern Detection Results
            pattern_frequency VARCHAR(20), 
            pattern_days TEXT, 
            pattern_confidence DECIMAL(5,4) DEFAULT 0.0,
            
            -- Forecasting Method
            forecast_method VARCHAR(20) DEFAULT 'weighted_average',
            
            -- Metadata
            is_active BOOLEAN DEFAULT true,
            last_analyzed DATE,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            
            UNIQUE(client_id, group_name)
        );
        """,
        
        "forecasts": """
        CREATE TABLE IF NOT EXISTS forecasts (
            id SERIAL PRIMARY KEY,
            client_id VARCHAR(255) NOT NULL,
            vendor_group_name VARCHAR(255) NOT NULL,
            forecast_date DATE NOT NULL,
            
            -- Forecast Data
            forecast_amount DECIMAL(15,2) NOT NULL,
            forecast_type VARCHAR(20) NOT NULL,
            forecast_method VARCHAR(20) NOT NULL,
            
            -- Actual Data (filled in during reconciliation)
            actual_amount DECIMAL(15,2),
            variance DECIMAL(15,2),
            is_locked BOOLEAN DEFAULT false,
            
            -- Metadata
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            
            UNIQUE(client_id, vendor_group_name, forecast_date)
        );
        """,
        
        "pattern_analysis": """
        CREATE TABLE IF NOT EXISTS pattern_analysis (
            id SERIAL PRIMARY KEY,
            client_id VARCHAR(255) NOT NULL,
            vendor_group_name VARCHAR(255) NOT NULL,
            analysis_date DATE NOT NULL,
            
            -- Analysis Results
            frequency_detected VARCHAR(20),
            specific_days TEXT,
            confidence_score DECIMAL(5,4),
            sample_size INTEGER,
            date_range_start DATE,
            date_range_end DATE,
            
            -- Raw Data
            transactions_analyzed INTEGER,
            average_amount DECIMAL(15,2),
            explanation TEXT,
            
            created_at TIMESTAMP DEFAULT NOW()
        );
        """,
        
        "actuals_import": """
        CREATE TABLE IF NOT EXISTS actuals_import (
            id SERIAL PRIMARY KEY,
            client_id VARCHAR(255) NOT NULL,
            import_date DATE NOT NULL,
            week_start_date DATE NOT NULL,
            week_end_date DATE NOT NULL,
            
            -- Import Results
            transactions_imported INTEGER,
            forecasts_updated INTEGER,
            new_patterns_detected INTEGER,
            
            -- Status
            status VARCHAR(20) DEFAULT 'completed',
            notes TEXT,
            
            created_at TIMESTAMP DEFAULT NOW(),
            
            UNIQUE(client_id, week_start_date)
        );
        """
    }
    
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_vendor_groups_client ON vendor_groups(client_id);",
        "CREATE INDEX IF NOT EXISTS idx_forecasts_client_date ON forecasts(client_id, forecast_date);",
        "CREATE INDEX IF NOT EXISTS idx_forecasts_group_date ON forecasts(vendor_group_name, forecast_date);",
        "CREATE INDEX IF NOT EXISTS idx_forecasts_unlocked ON forecasts(client_id, is_locked) WHERE is_locked = false;"
    ]
    
    print("🏗️  Creating lean forecasting database tables...")
    
    # Create tables by inserting dummy data and letting Supabase auto-create
    for table_name, sql in tables.items():
        try:
            print(f"📋 Creating table: {table_name}")
            
            # Test if table exists by trying to select from it
            try:
                supabase.table(table_name).select('*').limit(1).execute()
                print(f"✅ Table {table_name} already exists")
            except:
                print(f"⚠️  Table {table_name} doesn't exist, need to create it")
                print(f"📄 SQL for {table_name}:")
                print(sql)
                print("\n" + "="*80)
                
        except Exception as e:
            print(f"❌ Error with table {table_name}: {e}")
    
    print("\n💡 Since we can't execute DDL directly, you'll need to:")
    print("1. Go to your Supabase dashboard")
    print("2. Navigate to SQL Editor")
    print("3. Run the SQL statements printed above")
    print("4. Or create the tables manually using the Table Editor")
    
    return True

def test_basic_operations():
    """Test basic CRUD operations on the new tables."""
    print("\n🧪 Testing basic operations...")
    
    try:
        # Test vendor_groups insert
        test_group = {
            'client_id': 'test_client',
            'group_name': 'Test Revenue Group',
            'vendor_display_names': ['Amazon Revenue', 'Shopify Revenue'],
            'pattern_frequency': 'daily',
            'pattern_days': 'M-F',
            'forecast_method': 'weighted_average'
        }
        
        result = supabase.table('vendor_groups').insert(test_group).execute()
        
        if result.data:
            print("✅ Successfully inserted test vendor group")
            
            # Clean up test data
            supabase.table('vendor_groups').delete().eq('client_id', 'test_client').execute()
            print("✅ Cleaned up test data")
            
        return True
        
    except Exception as e:
        print(f"❌ Error testing operations: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Setting up Lean Forecasting System Database")
    print("=" * 60)
    
    if create_tables():
        print("\n✅ Database setup instructions provided")
        
        # Only test if tables actually exist
        if len(sys.argv) > 1 and sys.argv[1] == "--test":
            test_basic_operations()
    else:
        print("\n❌ Database setup failed")