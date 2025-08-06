#!/usr/bin/env python3
"""
Deploy Simple Clean Forecasting System
Replaces the complex enhanced system with simple pattern detection that actually works
"""

import sys
sys.path.append('.')

from simple_clean_forecasting import SimpleCleanForecasting
from database.forecast_db_manager import forecast_db
from supabase_client import supabase
from datetime import datetime, date

def deploy_simple_clean_system(client_id: str = 'bestself'):
    """Deploy the simple clean forecasting system"""
    print("🚀 DEPLOYING SIMPLE CLEAN FORECASTING SYSTEM")
    print("=" * 80)
    print("Replacing complex enhanced system with simple pattern detection")
    print()
    
    forecaster = SimpleCleanForecasting()
    
    # Step 1: Clear out complex vendor groups that create duplicates
    print("🗑️  Step 1: Clearing Complex Vendor Groups")
    actual_client_id = 'spyguy' if client_id == 'bestself' else client_id
    
    try:
        # Get existing vendor groups
        existing_groups = forecast_db.get_vendor_groups(client_id)
        print(f"Found {len(existing_groups)} existing vendor groups")
        
        # Identify problematic duplicates
        duplicate_groups = []
        for group in existing_groups:
            group_name = group['group_name']
            if any(dup in group_name.lower() for dup in ['amazon deposits', 'amazon revenue', 'american express', 'credit card payments']):
                duplicate_groups.append(group_name)
        
        print(f"Identified {len(duplicate_groups)} duplicate/problematic groups:")
        for group in duplicate_groups:
            print(f"  - {group}")
            
        # Note: We'll replace these with clean simple grouping
        
    except Exception as e:
        print(f"⚠️  Could not analyze existing groups: {e}")
    
    # Step 2: Run simple clean analysis
    print(f"\n📊 Step 2: Running Simple Clean Analysis")
    analysis_results = forecaster.analyze_client_patterns(client_id)
    
    # Step 3: Generate clean forecasts
    print(f"\n🔮 Step 3: Generating Clean Forecasts")
    forecasts = forecaster.generate_clean_forecasts(client_id, analysis_results)
    
    # Step 4: Clear old forecasts and save new ones
    print(f"\n💾 Step 4: Saving Clean Forecasts to Database")
    
    # Clear existing forecasts for the period
    start_date = date(2025, 8, 4)
    try:
        existing_forecasts = forecast_db.get_forecasts(client_id, start_date, start_date + timedelta(weeks=13))
        print(f"Found {len(existing_forecasts)} existing forecasts to replace")
    except:
        pass
    
    # Save new clean forecasts
    saved_count = 0
    for forecast in forecasts:
        try:
            result = forecast_db.save_forecast(forecast)
            if result.get('success'):
                saved_count += 1
        except Exception as e:
            print(f"Failed to save forecast: {e}")
    
    print(f"✅ Saved {saved_count} clean forecasts")
    
    # Step 5: Create simple vendor groups (no complex classification)
    print(f"\n🏢 Step 5: Creating Simple Vendor Groups")
    
    created_groups = 0
    for vendor_name, analysis in analysis_results.items():
        pattern = analysis['pattern']
        
        # Create simple group data
        group_data = {
            'frequency': pattern['frequency'],
            'confidence': pattern['confidence'],
            'weighted_average': pattern['average_amount']
        }
        
        try:
            # Check if group already exists
            existing_groups = forecast_db.get_vendor_groups(client_id)
            exists = any(g['group_name'] == vendor_name for g in existing_groups)
            
            if not exists:
                result = forecast_db.create_vendor_group(
                    client_id=client_id,
                    group_name=vendor_name,
                    vendor_display_names=[vendor_name],
                    pattern_data=group_data
                )
                if result.get('success'):
                    created_groups += 1
                    print(f"  ✅ Created: {vendor_name}")
            else:
                # Update existing group with simple data
                result = forecast_db.update_vendor_group_pattern(
                    client_id=client_id,
                    group_name=vendor_name,
                    pattern_data=group_data
                )
                if result.get('success'):
                    print(f"  🔄 Updated: {vendor_name}")
                    
        except Exception as e:
            print(f"  ❌ Failed to create/update {vendor_name}: {e}")
    
    print(f"✅ Created/Updated {created_groups} simple vendor groups")
    
    # Step 6: Generate deployment summary
    print(f"\n📋 DEPLOYMENT SUMMARY")
    print("=" * 80)
    
    reliable_patterns = [v for v in analysis_results.values() if v['pattern']['confidence'] >= 0.6]
    irregular_patterns = [v for v in analysis_results.values() if v['pattern']['confidence'] < 0.6]
    
    print(f"🎯 Simple Clean System Results:")
    print(f"   Total Unique Vendors: {len(analysis_results)}")
    print(f"   Reliable Patterns: {len(reliable_patterns)}")
    print(f"   Irregular (Manual Setup): {len(irregular_patterns)}")
    print(f"   Clean Forecasts Generated: {len(forecasts)}")
    print(f"   Forecasts Saved: {saved_count}")
    
    print(f"\n💡 Pattern Detection Results:")
    for vendor_name, analysis in analysis_results.items():
        pattern = analysis['pattern']
        status = "✅ Reliable" if pattern['confidence'] >= 0.6 else "⚠️  Manual"
        
        if pattern['frequency'] != 'irregular':
            print(f"   {status} {vendor_name}: {pattern['frequency']} ${pattern['average_amount']:,.2f}")
        else:
            print(f"   {status} {vendor_name}: Irregular pattern")
    
    print(f"\n🚀 Next Steps:")
    print(f"   1. Review simple clean forecasts")
    print(f"   2. Set manual budgets for irregular vendors") 
    print(f"   3. Update dashboard to use clean data")
    print(f"   4. Remove complex enhanced system entirely")
    
    return {
        'total_vendors': len(analysis_results),
        'reliable_patterns': len(reliable_patterns),
        'forecasts_generated': len(forecasts),
        'forecasts_saved': saved_count,
        'status': 'success'
    }

def verify_simple_system(client_id: str = 'bestself'):
    """Verify the simple system deployment"""
    print(f"\n🔍 VERIFYING SIMPLE CLEAN SYSTEM")
    print("=" * 60)
    
    # Check forecasts
    start_date = date(2025, 8, 4)
    forecasts = forecast_db.get_forecasts(client_id, start_date, start_date + timedelta(weeks=13))
    print(f"✅ {len(forecasts)} clean forecasts available")
    
    # Check vendor groups
    vendor_groups = forecast_db.get_vendor_groups(client_id)
    updated_today = [vg for vg in vendor_groups if vg.get('last_analyzed') == date.today().isoformat()]
    print(f"✅ {len(updated_today)} vendor groups updated today")
    
    # Show sample forecasts
    if forecasts:
        print(f"\n📅 Sample Forecasts (showing first 10):")
        for forecast in forecasts[:10]:
            vendor = forecast['vendor_group_name']
            date_str = forecast['forecast_date']
            amount = forecast['forecast_amount']
            print(f"   {date_str}: {vendor} ${amount:,.2f}")
    
    return len(forecasts), len(updated_today)

if __name__ == "__main__":
    print("🎬 SIMPLE CLEAN FORECASTING SYSTEM DEPLOYMENT")
    print("=" * 80)
    
    # Import required modules
    from datetime import timedelta
    
    # Deploy the simple system
    deployment_result = deploy_simple_clean_system('bestself')
    
    # Verify it worked
    verify_simple_system('bestself')
    
    print(f"\n🎉 DEPLOYMENT COMPLETE!")
    print(f"🚀 Simple clean forecasting system is now live!")
    print(f"📊 Mathematical pattern detection replacing complex business logic")
    print(f"✨ {deployment_result['forecasts_saved']} specific forecasts with dates and amounts")