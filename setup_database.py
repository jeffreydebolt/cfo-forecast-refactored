#!/usr/bin/env python3
"""
Setup Database Tables
Creates all required tables for the onboarding system
"""

import sys
sys.path.append('.')

from supabase_client import supabase

def create_tables():
    """Create all required database tables"""
    print("🔧 CREATING DATABASE TABLES")
    print("=" * 80)
    
    # SQL commands to create tables
    tables = [
        """
        CREATE TABLE IF NOT EXISTS vendor_mappings (
            id SERIAL PRIMARY KEY,
            client_id VARCHAR(50) NOT NULL,
            group_name VARCHAR(100) NOT NULL,
            vendor_name VARCHAR(100) NOT NULL,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(client_id, vendor_name)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS pattern_results (
            id SERIAL PRIMARY KEY,
            client_id VARCHAR(50) NOT NULL,
            vendor_group VARCHAR(100) NOT NULL,
            pattern_type VARCHAR(50),
            frequency_days INTEGER,
            median_gap_days INTEGER,
            amount_variance DECIMAL(5,2),
            forecast_recommendation VARCHAR(20),
            confidence VARCHAR(10),
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(client_id, vendor_group)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS forecast_configs (
            id SERIAL PRIMARY KEY,
            client_id VARCHAR(50) NOT NULL,
            vendor_group VARCHAR(100) NOT NULL,
            forecast_frequency VARCHAR(20),
            forecast_amount DECIMAL(10,2),
            custom_day_of_week INTEGER,
            custom_day_of_month INTEGER,
            is_active BOOLEAN DEFAULT TRUE,
            is_manual_override BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(client_id, vendor_group)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS onboarding_status (
            id SERIAL PRIMARY KEY,
            client_id VARCHAR(50) NOT NULL,
            step VARCHAR(50) NOT NULL,
            data JSONB,
            completed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(client_id, step)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS forecast_variances (
            id SERIAL PRIMARY KEY,
            client_id VARCHAR(50) NOT NULL,
            vendor_group VARCHAR(100) NOT NULL,
            forecast_date DATE NOT NULL,
            forecast_amount DECIMAL(10,2),
            actual_amount DECIMAL(10,2),
            variance_amount DECIMAL(10,2),
            variance_percentage DECIMAL(5,2),
            created_at TIMESTAMP DEFAULT NOW()
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS client_settings (
            id SERIAL PRIMARY KEY,
            client_id VARCHAR(50) NOT NULL UNIQUE,
            beginning_cash_balance DECIMAL(10,2) DEFAULT 50000,
            low_cash_threshold DECIMAL(10,2) DEFAULT 20000,
            forecast_horizon_weeks INTEGER DEFAULT 13,
            auto_adjust_patterns BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
        """
    ]
    
    # Create indexes
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_vendor_mappings_client ON vendor_mappings(client_id);",
        "CREATE INDEX IF NOT EXISTS idx_pattern_results_client ON pattern_results(client_id);",
        "CREATE INDEX IF NOT EXISTS idx_forecast_configs_client ON forecast_configs(client_id);",
        "CREATE INDEX IF NOT EXISTS idx_forecast_variances_client_date ON forecast_variances(client_id, forecast_date);"
    ]
    
    try:
        # Create tables
        for i, table_sql in enumerate(tables, 1):
            table_name = table_sql.split('TABLE IF NOT EXISTS ')[1].split(' (')[0]
            print(f"📋 Creating table {i}/6: {table_name}")
            
            result = supabase.rpc('exec_sql', {'sql': table_sql}).execute()
            print(f"   ✅ Created {table_name}")
        
        # Create indexes
        print(f"\n📊 Creating indexes...")
        for index_sql in indexes:
            result = supabase.rpc('exec_sql', {'sql': index_sql}).execute()
        print(f"   ✅ Created indexes")
        
        print(f"\n✅ DATABASE SETUP COMPLETE!")
        print(f"All tables and indexes created successfully")
        
    except Exception as e:
        print(f"❌ Error creating tables: {str(e)}")
        print(f"You may need to create them manually using the database_schema.sql file")

def main():
    create_tables()

if __name__ == "__main__":
    main()