#!/usr/bin/env python3
"""
Initialize the forecast database with tables and test data.
"""

import sys
sys.path.append('.')

from database.forecast_db_manager import forecast_db
from lean_forecasting.group_pattern_detector import group_pattern_detector
from lean_forecasting.forecast_generator import forecast_generator
from datetime import date, timedelta

def test_database_setup():
    """Test if database tables exist by trying to query them."""
    print("🔍 TESTING DATABASE SETUP")
    print("=" * 50)
    
    try:
        # Test vendor_groups table
        groups = forecast_db.get_vendor_groups('test_client')
        print("✅ vendor_groups table - accessible")
        
        # Test forecasts table  
        forecasts = forecast_db.get_forecasts('test_client')
        print("✅ forecasts table - accessible")
        
        # Test pattern_analysis table
        from supabase_client import supabase
        result = supabase.table('pattern_analysis').select('*').limit(1).execute()
        print("✅ pattern_analysis table - accessible")
        
        # Test actuals_import table
        result = supabase.table('actuals_import').select('*').limit(1).execute()
        print("✅ actuals_import table - accessible")
        
        return True
        
    except Exception as e:
        print(f"❌ Database setup issue: {e}")
        print("\n💡 Please run the SQL from database/create_forecast_tables.sql in Supabase dashboard")
        return False

def create_sample_vendor_groups():
    """Create sample vendor groups with pattern analysis."""
    print("\n🧪 CREATING SAMPLE VENDOR GROUPS")
    print("=" * 50)
    
    client_id = 'bestself'
    
    # Define vendor groups
    sample_groups = [
        {
            'name': 'Amazon',
            'display_names': ['Amazon Revenue'],
            'description': 'Amazon marketplace deposits'
        },
        {
            'name': 'E-commerce Revenue', 
            'display_names': ['Shopify Revenue', 'BestSelf Revenue', 'Affirm Payments'],
            'description': 'Combined e-commerce revenue streams'
        },
        {
            'name': 'Payment Processing',
            'display_names': ['Stripe Revenue', 'PayPal Revenue'],
            'description': 'Payment processor revenues'
        },
        {
            'name': 'Credit Card Payments',
            'display_names': ['American Express Payments'],
            'description': 'Credit card payment expenses'
        },
        {
            'name': 'Contractor Payments',
            'display_names': ['Wise Transfers'],
            'description': 'International contractor payments'
        }
    ]
    
    created_groups = []
    
    for group_data in sample_groups:
        print(f"\nCreating group: {group_data['name']}")
        
        # Analyze pattern for this group
        pattern_analysis = group_pattern_detector.analyze_vendor_group_pattern(
            client_id, group_data['name'], group_data['display_names']
        )
        
        if pattern_analysis['frequency'] != 'irregular':
            # Create vendor group with pattern data
            result = forecast_db.create_vendor_group(
                client_id=client_id,
                group_name=group_data['name'],
                vendor_display_names=group_data['display_names'],
                pattern_data={
                    'frequency': pattern_analysis['frequency'],
                    'timing': pattern_analysis.get('timing', 'unknown'),
                    'confidence': pattern_analysis['frequency_confidence'],
                    'forecast_method': 'weighted_average',
                    'weighted_average': pattern_analysis['weighted_average']
                }
            )
            
            if result['success']:
                print(f"✅ Created: {group_data['name']}")
                created_groups.append(group_data['name'])
                
                # Save pattern analysis for audit trail
                forecast_db.save_pattern_analysis(
                    client_id, group_data['name'], pattern_analysis
                )
            else:
                print(f"❌ Failed: {group_data['name']} - {result.get('error')}")
        else:
            print(f"⚠️  Skipped: {group_data['name']} - irregular pattern")
    
    return created_groups

def generate_sample_forecasts():
    """Generate and store 13-week forecasts."""
    print("\n🔮 GENERATING SAMPLE FORECASTS")
    print("=" * 50)
    
    client_id = 'bestself'
    start_date = date(2025, 8, 4)
    
    # Get all vendor groups
    vendor_groups = forecast_db.get_vendor_groups(client_id)
    
    if not vendor_groups:
        print("❌ No vendor groups found")
        return
    
    total_forecasts_created = 0
    
    for group in vendor_groups:
        group_name = group['group_name']
        display_names = group['vendor_display_names']
        
        print(f"\nGenerating forecasts for: {group_name}")
        
        # Generate forecast records
        forecast_records = forecast_generator.generate_vendor_group_forecast(
            client_id=client_id,
            vendor_group_name=group_name,
            display_names=display_names,
            weeks_ahead=13,
            start_date=start_date
        )
        
        if forecast_records:
            # Store in database
            result = forecast_db.create_forecasts(forecast_records)
            
            if result['success']:
                count = result['count']
                total_forecasts_created += count
                print(f"✅ Stored {count} forecast records for {group_name}")
            else:
                print(f"❌ Failed to store forecasts for {group_name}: {result.get('error')}")
        else:
            print(f"⚠️  No forecasts generated for {group_name}")
    
    print(f"\n📊 TOTAL FORECAST RECORDS CREATED: {total_forecasts_created}")
    
    return total_forecasts_created

def show_forecast_summary():
    """Show summary of stored forecasts."""
    print("\n📋 FORECAST SUMMARY")
    print("=" * 50)
    
    client_id = 'bestself'
    start_date = date(2025, 8, 4)
    end_date = start_date + timedelta(weeks=13)
    
    summary = forecast_db.get_forecast_summary(client_id, start_date, end_date)
    
    if 'error' in summary:
        print(f"❌ Error getting summary: {summary['error']}")
        return
    
    print(f"Date Range: {summary['date_range']}")
    print(f"Total Forecast Amount: ${summary['total_amount']:,.2f}")
    print(f"Number of Forecast Records: {summary['forecast_count']}")
    print(f"Vendor Groups: {len(summary['vendor_groups'])}")
    
    print(f"\nBreakdown by Vendor Group:")
    for vendor, amount in sorted(summary['by_vendor'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {vendor}: ${amount:,.2f}")

def main():
    """Main initialization function."""
    print("🚀 INITIALIZING FORECAST DATABASE")
    print("=" * 70)
    
    # Step 1: Test database setup
    if not test_database_setup():
        return
    
    # Step 2: Create sample vendor groups
    created_groups = create_sample_vendor_groups()
    
    if not created_groups:
        print("❌ No vendor groups created - cannot proceed")
        return
    
    # Step 3: Generate sample forecasts
    forecast_count = generate_sample_forecasts()
    
    if forecast_count == 0:
        print("❌ No forecasts generated")
        return
    
    # Step 4: Show summary
    show_forecast_summary()
    
    print(f"\n🎉 DATABASE INITIALIZATION COMPLETE!")
    print(f"✅ Created {len(created_groups)} vendor groups")
    print(f"✅ Generated {forecast_count} forecast records")
    print(f"✅ Database ready for production use")

if __name__ == "__main__":
    main()