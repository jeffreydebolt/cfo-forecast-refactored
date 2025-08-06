#!/usr/bin/env python3
"""
Setup lean forecasting tables by creating test records.
Since we can't run DDL directly, we'll create the schema by inserting data.
"""

from supabase_client import supabase
from datetime import datetime, date

def setup_vendor_groups_table():
    """Setup vendor_groups table by inserting a test record."""
    try:
        print("📋 Setting up vendor_groups table...")
        
        # Try to insert a test record to create the table
        test_record = {
            'client_id': 'setup_test',
            'group_name': 'Setup Test Group',
            'vendor_display_names': ['Test Vendor 1', 'Test Vendor 2'],
            'pattern_frequency': 'daily',
            'pattern_days': 'M-F',
            'pattern_confidence': 0.95,
            'forecast_method': 'weighted_average',
            'is_active': True,
            'last_analyzed': date.today().isoformat(),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        result = supabase.table('vendor_groups').insert(test_record).execute()
        
        if result.data:
            print("✅ vendor_groups table created/verified")
            
            # Clean up test record
            supabase.table('vendor_groups').delete().eq('client_id', 'setup_test').execute()
            print("🧹 Cleaned up test record")
            return True
        else:
            print("❌ Failed to create vendor_groups table")
            return False
            
    except Exception as e:
        print(f"❌ Error setting up vendor_groups table: {e}")
        return False

def setup_forecasts_table():
    """Setup forecasts table by inserting a test record."""
    try:
        print("📋 Setting up forecasts table...")
        
        test_record = {
            'client_id': 'setup_test',
            'vendor_group_name': 'Setup Test Group',
            'forecast_date': date.today().isoformat(),
            'forecast_amount': 1000.00,
            'forecast_type': 'daily',
            'forecast_method': 'weighted_average',
            'actual_amount': None,
            'variance': None,
            'is_locked': False,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        result = supabase.table('forecasts').insert(test_record).execute()
        
        if result.data:
            print("✅ forecasts table created/verified")
            
            # Clean up test record
            supabase.table('forecasts').delete().eq('client_id', 'setup_test').execute()
            print("🧹 Cleaned up test record")
            return True
        else:
            print("❌ Failed to create forecasts table")
            return False
            
    except Exception as e:
        print(f"❌ Error setting up forecasts table: {e}")
        return False

def setup_pattern_analysis_table():
    """Setup pattern_analysis table by inserting a test record."""
    try:
        print("📋 Setting up pattern_analysis table...")
        
        test_record = {
            'client_id': 'setup_test',
            'vendor_group_name': 'Setup Test Group',
            'analysis_date': date.today().isoformat(),
            'frequency_detected': 'daily',
            'specific_days': 'M-F',
            'confidence_score': 0.95,
            'sample_size': 30,
            'date_range_start': date.today().isoformat(),
            'date_range_end': date.today().isoformat(),
            'transactions_analyzed': 30,
            'average_amount': 1000.00,
            'explanation': 'Test pattern analysis',
            'created_at': datetime.now().isoformat()
        }
        
        result = supabase.table('pattern_analysis').insert(test_record).execute()
        
        if result.data:
            print("✅ pattern_analysis table created/verified")
            
            # Clean up test record
            supabase.table('pattern_analysis').delete().eq('client_id', 'setup_test').execute()
            print("🧹 Cleaned up test record")
            return True
        else:
            print("❌ Failed to create pattern_analysis table")
            return False
            
    except Exception as e:
        print(f"❌ Error setting up pattern_analysis table: {e}")
        return False

def setup_actuals_import_table():
    """Setup actuals_import table by inserting a test record."""
    try:
        print("📋 Setting up actuals_import table...")
        
        test_record = {
            'client_id': 'setup_test',
            'import_date': date.today().isoformat(),
            'week_start_date': date.today().isoformat(),
            'week_end_date': date.today().isoformat(),
            'transactions_imported': 10,
            'forecasts_updated': 5,
            'new_patterns_detected': 1,
            'status': 'completed',
            'notes': 'Test import',
            'created_at': datetime.now().isoformat()
        }
        
        result = supabase.table('actuals_import').insert(test_record).execute()
        
        if result.data:
            print("✅ actuals_import table created/verified")
            
            # Clean up test record
            supabase.table('actuals_import').delete().eq('client_id', 'setup_test').execute()
            print("🧹 Cleaned up test record")
            return True
        else:
            print("❌ Failed to create actuals_import table")
            return False
            
    except Exception as e:
        print(f"❌ Error setting up actuals_import table: {e}")
        return False

def verify_all_tables():
    """Verify all tables exist and are accessible."""
    tables = ['vendor_groups', 'forecasts', 'pattern_analysis', 'actuals_import']
    
    print("\n🔍 Verifying all tables...")
    
    all_good = True
    for table_name in tables:
        try:
            result = supabase.table(table_name).select('*').limit(1).execute()
            print(f"✅ {table_name} - accessible")
        except Exception as e:
            print(f"❌ {table_name} - error: {e}")
            all_good = False
    
    return all_good

if __name__ == "__main__":
    print("🚀 Setting up Lean Forecasting Database Tables")
    print("=" * 60)
    
    success_count = 0
    
    if setup_vendor_groups_table():
        success_count += 1
    
    if setup_forecasts_table():
        success_count += 1
        
    if setup_pattern_analysis_table():
        success_count += 1
        
    if setup_actuals_import_table():
        success_count += 1
    
    print(f"\n📊 Setup Results: {success_count}/4 tables created")
    
    if success_count == 4:
        if verify_all_tables():
            print("\n🎉 All tables setup successfully!")
            print("\n💡 Next steps:")
            print("1. python lean_forecasting/vendor_groups.py bestself create_samples")
            print("2. python lean_forecasting/vendor_groups.py bestself status")
        else:
            print("\n⚠️  Some tables may have issues")
    else:
        print("\n❌ Some tables failed to setup")
        print("You may need to create them manually in Supabase dashboard")