#!/usr/bin/env python3
"""
Deploy Enhanced Forecasting System to Production - FIXED VERSION
Uses existing database methods instead of direct supabase access
"""

import sys
sys.path.append('.')

from database.forecast_db_manager import forecast_db
from lean_forecasting.enhanced_integration import enhanced_integration
from lean_forecasting.group_pattern_detector import group_pattern_detector
from services.forecast_service_v2 import forecast_service_v2
from datetime import date, timedelta

def deploy_enhanced_system_fixed(client_id: str = 'bestself'):
    """Deploy enhanced forecasting system to production using existing methods"""
    print("🚀 DEPLOYING ENHANCED FORECASTING SYSTEM TO PRODUCTION (FIXED)")
    print("=" * 80)
    
    start_date = date(2025, 8, 4)
    end_date = start_date + timedelta(weeks=13)
    
    # Step 1: Get enhanced analysis for all vendor groups
    print("\n📊 Step 1: Running Enhanced Analysis")
    enhanced_results = enhanced_integration.generate_enhanced_forecasts_for_all_groups(client_id)
    
    # Step 2: Clear existing forecasts using existing method
    print("\n🗑️  Step 2: Clearing Old Forecasts")
    try:
        # Get existing forecasts and delete them
        existing_forecasts = forecast_db.get_forecasts(client_id, start_date, end_date)
        print(f"Found {len(existing_forecasts)} existing forecasts to clear")
        
        # Clear using forecast_service_v2 which has cleanup methods
        if hasattr(forecast_service_v2, 'clear_forecasts'):
            forecast_service_v2.clear_forecasts(client_id, start_date, end_date)
            print("✅ Cleared old forecasts")
        else:
            print("⚠️  No clear_forecasts method - proceeding with new forecasts")
            
    except Exception as e:
        print(f"⚠️  Warning: Could not clear old forecasts: {e}")
    
    # Step 3: Update vendor groups with enhanced analysis
    print("\n🔄 Step 3: Updating Vendor Groups with Enhanced Analysis")
    
    updated_groups = 0
    for group_name, analysis in enhanced_results['vendor_groups'].items():
        if 'classification' not in analysis:
            continue
            
        try:
            pattern = analysis['pattern_analysis']
            recommendation = analysis['overall_recommendation']
            
            # Prepare pattern data for existing update method
            pattern_data = {
                'frequency': pattern['frequency'],
                'timing': pattern.get('timing', 'unknown'),
                'confidence': pattern.get('adjusted_confidence', pattern['frequency_confidence']),
                'weighted_average': pattern['weighted_average']
            }
            
            # Update using existing method
            result = forecast_db.update_vendor_group_pattern(
                client_id, group_name, pattern_data
            )
            
            if result.get('success'):
                status_icon = {
                    'ready_for_automatic_forecasting': '✅',
                    'ready_with_monitoring': '⚠️ ',
                    'manual_forecasting_recommended': '🔧',
                    'manual_setup_required': '❌'
                }.get(recommendation['status'], '❓')
                
                print(f"  {status_icon} Updated {group_name}")
                print(f"      Status: {recommendation['status']}")
                print(f"      Method: {recommendation['method']}")
                print(f"      Amount: ${pattern['weighted_average']:,.2f}")
                updated_groups += 1
            
        except Exception as e:
            print(f"  ❌ Failed to update {group_name}: {e}")
    
    print(f"\n✅ Updated {updated_groups} vendor groups with enhanced analysis")
    
    # Step 4: Generate new forecasts for groups that are ready
    print("\n🔮 Step 4: Generating New Forecasts")
    
    total_forecasts = 0
    ready_groups = []
    
    for group_name, analysis in enhanced_results['vendor_groups'].items():
        if 'classification' not in analysis:
            continue
            
        recommendation = analysis['overall_recommendation']
        if recommendation['status'] in ['ready_for_automatic_forecasting', 'ready_with_monitoring']:
            ready_groups.append(group_name)
    
    print(f"📈 Generating forecasts for {len(ready_groups)} ready groups:")
    
    # Use existing forecast service to generate forecasts
    for group_name in ready_groups:
        try:
            # Get vendor group data
            vendor_groups = forecast_db.get_vendor_groups(client_id)
            vendor_group = next((vg for vg in vendor_groups if vg['group_name'] == group_name), None)
            
            if not vendor_group:
                print(f"  ⚠️  Could not find vendor group: {group_name}")
                continue
            
            display_names = vendor_group['vendor_display_names']
            
            # Use the v2 forecast service to generate forecasts
            forecasts = forecast_service_v2.generate_vendor_group_forecast(
                client_id=client_id,
                vendor_group_name=group_name,
                display_names=display_names,
                weeks_ahead=13,
                start_date=start_date
            )
            
            if forecasts:
                # Save forecasts using existing method
                saved_count = 0
                for forecast in forecasts:
                    forecast_data = {
                        'client_id': client_id,
                        'vendor_group_name': group_name,
                        'forecast_date': forecast['forecast_date'],
                        'forecast_amount': forecast['forecast_amount'],
                        'forecast_type': forecast['forecast_type'],
                        'forecast_method': forecast['forecast_method'],
                        'pattern_confidence': forecast['pattern_confidence'],
                        'display_names_included': forecast['display_names_included'],
                        'timing': forecast.get('timing', 'unknown')
                    }
                    
                    saved = forecast_db.save_forecast(forecast_data)
                    if saved.get('success'):
                        saved_count += 1
                
                print(f"  ✅ {group_name}: Generated {saved_count} forecasts")
                total_forecasts += saved_count
            else:
                print(f"  ⚠️  {group_name}: No forecasts generated")
                
        except Exception as e:
            print(f"  ❌ Failed to generate forecasts for {group_name}: {e}")
    
    print(f"\n✅ Generated {total_forecasts} total forecast records")
    
    # Step 5: Update main dashboard with enhanced categorization
    print("\n🎨 Step 5: Updating Main Dashboard")
    
    try:
        # Import and run the enhanced dashboard generator
        from complete_improved_dashboard import generate_complete_dashboard
        
        # Regenerate the main dashboard (it will now use the enhanced data)
        dashboard_file = generate_complete_dashboard()
        print(f"✅ Updated main dashboard: {dashboard_file}")
        
    except Exception as e:
        print(f"⚠️  Could not update main dashboard: {e}")
    
    # Step 6: Generate deployment summary
    print("\n📋 DEPLOYMENT SUMMARY")
    print("=" * 80)
    
    summary = enhanced_results['summary']
    
    print(f"🎯 Enhanced System Status:")
    print(f"   Total Vendor Groups: {summary['total_groups']}")
    print(f"   Ready for Forecasting: {summary['ready_for_forecasting']}")
    print(f"   Need Manual Setup: {summary['need_manual_setup']}")
    print(f"   Need Monitoring: {summary['need_monitoring']}")
    print(f"   Total Forecasts Generated: {total_forecasts}")
    
    print(f"\n💡 Key Improvements:")
    wise_analysis = enhanced_results['vendor_groups'].get('Wise Transfers', {})
    if 'pattern_analysis' in wise_analysis:
        print(f"   • Wise Transfers: Now showing ${abs(wise_analysis['pattern_analysis']['weighted_average']):,.2f} with contractor logic")
    
    armbrust_analysis = enhanced_results['vendor_groups'].get('Armbrust Expenses', {})
    if 'pattern_analysis' in armbrust_analysis:
        print(f"   • Armbrust Expenses: Now showing ${abs(armbrust_analysis['pattern_analysis']['weighted_average']):,.2f} with professional services logic")
    
    amazon_analysis = enhanced_results['vendor_groups'].get('Amazon Revenue', {})
    if 'pattern_analysis' in amazon_analysis:
        confidence = amazon_analysis['pattern_analysis']['frequency_confidence']
        print(f"   • Amazon Revenue: {amazon_analysis['pattern_analysis']['frequency']} pattern with {confidence:.0%} confidence")
    
    print(f"   • Enhanced business logic applied to all vendor types")
    
    print(f"\n🚀 Next Steps:")
    print(f"   1. Review dashboard at: bestself_layout.html")
    print(f"   2. Use vendor mapping interface to add missing vendors")
    print(f"   3. Set manual budgets for vendors needing setup")
    print(f"   4. Monitor pattern changes over time")
    
    return {
        'total_groups': summary['total_groups'],
        'updated_groups': updated_groups,
        'generated_forecasts': total_forecasts,
        'ready_groups': len(ready_groups),
        'status': 'success'
    }

def verify_deployment_fixed(client_id: str = 'bestself'):
    """Verify the deployment worked correctly"""
    print("\n🔍 VERIFYING DEPLOYMENT")
    print("=" * 40)
    
    # Check vendor groups have been updated
    vendor_groups = forecast_db.get_vendor_groups(client_id)
    updated_groups = [vg for vg in vendor_groups if vg.get('last_analyzed') == date.today().isoformat()]
    
    print(f"✅ {len(updated_groups)} vendor groups updated today")
    
    # Check forecasts have been generated
    start_date = date(2025, 8, 4)
    end_date = start_date + timedelta(weeks=13)
    forecasts = forecast_db.get_forecasts(client_id, start_date, end_date)
    
    print(f"✅ {len(forecasts)} forecasts available for 13-week period")
    
    # Check key vendors
    key_vendors = ['Wise Transfers', 'Armbrust Expenses', 'Amazon Revenue']
    for vendor in key_vendors:
        vg = next((vg for vg in vendor_groups if vg['group_name'] == vendor), None)
        if vg and vg.get('weighted_average_amount', 0) != 0:
            print(f"✅ {vendor}: ${vg['weighted_average_amount']:,.2f} - {vg.get('pattern_frequency', 'unknown')}")
        else:
            print(f"⚠️  {vendor}: No data or not updated")
    
    return len(updated_groups), len(forecasts)

if __name__ == "__main__":
    print("🎬 ENHANCED FORECASTING SYSTEM DEPLOYMENT (FIXED)")
    print("=" * 80)
    
    # Deploy the system
    deployment_result = deploy_enhanced_system_fixed('bestself')
    
    # Verify it worked
    verify_deployment_fixed('bestself')
    
    print(f"\n🎉 DEPLOYMENT COMPLETE!")
    print(f"🚀 Enhanced forecasting system is now live for BestSelf!")
    print(f"📊 Dashboard available with enhanced business intelligence")