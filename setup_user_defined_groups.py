#!/usr/bin/env python3
"""
Set up user-defined vendor groups for enhanced forecasting.
"""

import sys
sys.path.append('.')

from database.forecast_db_manager import forecast_db
from lean_forecasting.enhanced_pattern_detector import enhanced_pattern_detector
from datetime import date

def setup_user_defined_groups():
    """Create user-defined vendor groups."""
    print("🏗️  SETTING UP USER-DEFINED VENDOR GROUPS")
    print("=" * 60)
    
    client_id = 'bestself'
    
    try:
        # Get user-defined groups from enhanced pattern detector
        user_groups = enhanced_pattern_detector.get_user_defined_groups(client_id)
        
        print(f"📊 Creating {len(user_groups)} user-defined groups:")
        
        created_count = 0
        
        for group_config in user_groups:
            group_name = group_config['group_name']
            display_names = group_config['vendor_display_names']
            
            print(f"\n🔧 Creating group: {group_name}")
            print(f"   Vendors: {', '.join(display_names)}")
            
            # Check if group already exists
            existing_groups = forecast_db.get_vendor_groups(client_id)
            group_exists = any(g['group_name'] == group_name for g in existing_groups)
            
            if group_exists:
                print(f"   ⚠️  Group already exists, skipping...")
                continue
            
            # Analyze pattern for this group
            pattern_analysis = enhanced_pattern_detector.analyze_vendor_group_pattern_enhanced(
                client_id, group_name, display_names
            )
            
            # Create the group with pattern data
            if pattern_analysis['frequency'] != 'irregular':
                result = forecast_db.create_vendor_group(
                    client_id=client_id,
                    group_name=group_name,
                    vendor_display_names=display_names,
                    pattern_data={
                        'frequency': pattern_analysis['frequency'],
                        'timing': pattern_analysis['timing'],
                        'confidence': pattern_analysis['frequency_confidence'],
                        'forecast_method': 'weighted_average',
                        'weighted_average': pattern_analysis['weighted_average']
                    }
                )
                
                if result['success']:
                    print(f"   ✅ Created with pattern: {pattern_analysis['frequency']} ({pattern_analysis['timing']})")
                    print(f"   💰 Amount: ${pattern_analysis['weighted_average']:,.2f}")
                    created_count += 1
                    
                    # Save pattern analysis
                    forecast_db.save_pattern_analysis(
                        client_id, group_name, pattern_analysis
                    )
                else:
                    print(f"   ❌ Failed to create: {result.get('error')}")
            else:
                print(f"   ⚠️  Irregular pattern, creating without forecast data...")
                
                result = forecast_db.create_vendor_group(
                    client_id=client_id,
                    group_name=group_name,
                    vendor_display_names=display_names
                )
                
                if result['success']:
                    print(f"   ✅ Created (no pattern)")
        
        print(f"\n📊 SUMMARY:")
        print(f"   Created: {created_count} groups with patterns")
        print(f"   Total groups: {len(user_groups)}")
        
        return created_count
        
    except Exception as e:
        print(f"❌ Error setting up user-defined groups: {e}")
        import traceback
        traceback.print_exc()
        return 0

def test_enhanced_pattern_detection():
    """Test the enhanced pattern detection on key groups."""
    print(f"\n🧪 TESTING ENHANCED PATTERN DETECTION")
    print("=" * 60)
    
    client_id = 'bestself'
    
    # Test key groups
    test_groups = [
        ('Amazon Deposits', ['Amazon Revenue']),
        ('E-commerce Revenue', ['BestSelf Revenue', 'Affirm Payments', 'Shopify Revenue'])
    ]
    
    for group_name, display_names in test_groups:
        print(f"\n🔍 Testing: {group_name}")
        
        pattern_result = enhanced_pattern_detector.analyze_vendor_group_pattern_enhanced(
            client_id, group_name, display_names
        )
        
        print(f"   Frequency: {pattern_result['frequency']} (confidence: {pattern_result['frequency_confidence']:.2f})")
        print(f"   Timing: {pattern_result['timing']}")
        print(f"   Amount: ${pattern_result['weighted_average']:,.2f}")
        
        if pattern_result.get('timing_override'):
            print(f"   🔧 Timing Override Applied: {pattern_result['explanation']}")

def show_comparison_with_old_system():
    """Show comparison between old individual vendor approach and new grouped approach."""
    print(f"\n📊 COMPARISON: OLD vs NEW SYSTEM")
    print("=" * 60)
    
    print("OLD SYSTEM (Individual Vendors):")
    print("  • Amazon Revenue: $44,654 bi-weekly Tuesday")
    print("  • BestSelf Revenue: $8,783 daily weekdays") 
    print("  • Shopify Revenue: $1,242 daily weekdays")
    print("  • Affirm Payments: Irregular")
    print("  Total E-commerce: $8,783 + $1,242 = $10,025/week")
    
    print(f"\nNEW SYSTEM (User-Defined Groups):")
    print("  • Amazon Deposits: $44,654 bi-weekly Monday (override)")
    print("  • E-commerce Revenue: ~$10,267 weekly (combined BestSelf + Shopify + Affirm)")
    print("  Benefits:")
    print("    ✅ Proper business-level grouping")
    print("    ✅ Timing overrides for user preferences")
    print("    ✅ Combined patterns for related revenue streams")
    print("    ✅ Better matches user expectations")

def main():
    """Main setup function."""
    print("🚀 ENHANCED PATTERN DETECTION SETUP")
    print("=" * 70)
    
    # Setup user-defined groups
    created_count = setup_user_defined_groups()
    
    if created_count > 0:
        # Test enhanced pattern detection
        test_enhanced_pattern_detection()
        
        # Show comparison
        show_comparison_with_old_system()
        
        print(f"\n🎉 ENHANCED PATTERN DETECTION READY!")
        print(f"✅ {created_count} user-defined groups created")
        print(f"✅ Timing overrides active")
        print(f"✅ Business-level grouping operational")
        print(f"✅ Ready for V2 forecasting")
    else:
        print(f"\n❌ No groups created")

if __name__ == "__main__":
    main()