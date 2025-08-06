#!/usr/bin/env python3
"""
Setup Vendor Mapping Workflow
Comprehensive workflow to map vendors into logical groups and run pattern detection.
"""

import argparse
from vendor_mapping_manager import VendorMappingManager
from core.group_pattern_detection import group_pattern_detector

def setup_bestself_example_mapping():
    """Set up example mapping for bestself client to demonstrate the concept."""
    print("🎯 SETTING UP EXAMPLE VENDOR MAPPING FOR BESTSELF")
    print("=" * 80)
    
    manager = VendorMappingManager()
    client_id = 'bestself'
    
    # Show current status
    print("\n📊 CURRENT MAPPING STATUS:")
    manager.show_mapping_status(client_id)
    
    # Define logical groupings
    example_groups = [
        {
            'group_name': 'Shopify Revenue',
            'vendors': ['Shopify Revenue', 'BestSelf Revenue', 'Affirm Payments'],
            'is_revenue': True,
            'category': 'E-commerce Revenue'
        },
        {
            'group_name': 'Amazon Revenue', 
            'vendors': ['Amazon Revenue'],
            'is_revenue': True,
            'category': 'E-commerce Revenue'
        },
        {
            'group_name': 'Other Revenue',
            'vendors': ['TikTok Revenue', 'Stripe Revenue', 'Faire Revenue'],
            'is_revenue': True,
            'category': 'E-commerce Revenue'
        },
        {
            'group_name': 'Credit Card Payments',
            'vendors': ['American Express Payments'],
            'is_revenue': False,
            'category': 'Credit Card Payments'
        },
        {
            'group_name': 'Business Expenses',
            'vendors': ['Armbrust Expenses', 'Wise Transfers', 'Wire Fees'],
            'is_revenue': False,
            'category': 'Operating Expenses'
        }
    ]
    
    print(f"\n🔧 CREATING {len(example_groups)} LOGICAL VENDOR GROUPS:")
    print("-" * 60)
    
    created_count = 0
    for group_data in example_groups:
        print(f"\n📁 Creating group: {group_data['group_name']}")
        print(f"   Vendors: {', '.join(group_data['vendors'])}")
        
        success = manager.create_vendor_group(
            client_id=client_id,
            group_name=group_data['group_name'],
            vendor_display_names=group_data['vendors'],
            is_revenue=group_data['is_revenue'],
            category=group_data['category']
        )
        
        if success:
            created_count += 1
            print(f"   ✅ Success")
        else:
            print(f"   ⚠️  Failed (may already exist)")
    
    print(f"\n🎉 MAPPING SETUP COMPLETE!")
    print(f"Created {created_count} vendor groups")
    
    # Show final status
    print("\n📊 FINAL MAPPING STATUS:")
    manager.show_mapping_status(client_id)
    
    return created_count > 0

def run_group_pattern_detection(client_id: str):
    """Run pattern detection on vendor groups."""
    print(f"\n🔍 RUNNING PATTERN DETECTION ON VENDOR GROUPS FOR {client_id.upper()}")
    print("=" * 80)
    
    # Process all vendor groups
    results = group_pattern_detector.process_all_groups(client_id)
    
    print(f"\n📊 PATTERN DETECTION RESULTS:")
    print(f"  • Processed: {results['processed']} groups")
    print(f"  • Successful: {results['successful']} groups")
    print(f"  • Failed: {results['failed']} groups")
    
    if results['group_results']:
        print(f"\n📋 DETAILED RESULTS:")
        print("-" * 60)
        
        for group_result in results['group_results']:
            group_name = group_result['group_name']
            success = group_result['success']
            pattern = group_result['pattern']
            
            status_icon = "✅" if success else "❌"
            print(f"\n{status_icon} {group_name}")
            
            if success and pattern:
                print(f"   Pattern: {pattern['frequency']}")
                print(f"   Amount: ${pattern.get('forecast_amount', 0):,.2f}")
                print(f"   Confidence: {pattern.get('confidence', 0):.2f}")
                print(f"   Explanation: {pattern.get('explanation', 'N/A')}")
                print(f"   Transactions: {pattern.get('transaction_count', 0)}")
    
    return results

def generate_group_forecast(client_id: str):
    """Generate forecast based on vendor groups."""
    print(f"\n📈 GENERATING GROUP-BASED FORECAST FOR {client_id.upper()}")
    print("=" * 80)
    
    # Import and run the forecast system with group-based detection
    try:
        import subprocess
        result = subprocess.run(
            ['python3', 'run_calendar_forecast.py', '--client', client_id, '--weeks', '13'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Forecast generated successfully!")
            print("\n" + result.stdout)
        else:
            print("❌ Forecast generation failed:")
            print(result.stderr)
            
    except Exception as e:
        print(f"❌ Error running forecast: {e}")

def main():
    parser = argparse.ArgumentParser(description='Setup vendor mapping workflow')
    parser.add_argument('--client', required=True, help='Client ID')
    parser.add_argument('--example', action='store_true', help='Set up example mapping for bestself')
    parser.add_argument('--interactive', action='store_true', help='Interactive mapping mode')
    parser.add_argument('--detect-patterns', action='store_true', help='Run group pattern detection')
    parser.add_argument('--forecast', action='store_true', help='Generate group-based forecast')
    parser.add_argument('--full-workflow', action='store_true', help='Run complete workflow')
    
    args = parser.parse_args()
    
    if args.full_workflow:
        # Complete workflow
        print("🚀 RUNNING COMPLETE VENDOR MAPPING WORKFLOW")
        print("=" * 80)
        
        if args.client == 'bestself' and args.example:
            print("\n1️⃣ Setting up example mapping...")
            setup_bestself_example_mapping()
        else:
            print("\n1️⃣ Interactive mapping setup...")
            manager = VendorMappingManager()
            manager.interactive_mapping(args.client)
        
        print("\n2️⃣ Running pattern detection...")
        run_group_pattern_detection(args.client)
        
        print("\n3️⃣ Generating forecast...")
        generate_group_forecast(args.client)
        
    else:
        # Individual operations
        if args.example and args.client == 'bestself':
            setup_bestself_example_mapping()
        
        if args.interactive:
            manager = VendorMappingManager()
            manager.interactive_mapping(args.client)
        
        if args.detect_patterns:
            run_group_pattern_detection(args.client)
        
        if args.forecast:
            generate_group_forecast(args.client)

if __name__ == "__main__":
    main()