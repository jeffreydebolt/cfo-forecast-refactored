#!/usr/bin/env python3
"""
Add missing major vendors to the vendors table.
"""

from supabase_client import supabase
from datetime import datetime

def add_missing_vendors(client_id='spyguy', dry_run=True):
    """Add the major missing vendors that are causing forecast discrepancies."""
    
    # Major missing vendors from your 7/21 week analysis
    missing_vendors = [
        {
            'vendor_name': 'SGE Income (Mercury Checking xx2167)',
            'display_name': 'Internal Revenue',
            'is_revenue': True,
            'category': 'Internal Transfers'
        },
        {
            'vendor_name': 'SHOPIFYPAYMENTS', 
            'display_name': 'Shopify',
            'is_revenue': True,
            'category': 'E-commerce Revenue'
        },
        {
            'vendor_name': 'PAYPAL',
            'display_name': 'PayPal', 
            'is_revenue': True,
            'category': 'Payment Processing'
        },
        {
            'vendor_name': 'STRIPE',
            'display_name': 'Stripe',
            'is_revenue': True, 
            'category': 'Payment Processing'
        },
        {
            'vendor_name': 'SGE Inventory (Mercury Checking xx1152)',
            'display_name': 'Inventory Transfers',
            'is_revenue': False,
            'category': 'Internal Transfers'
        },
        {
            'vendor_name': 'SGE OpEx (Mercury Checking xx7588)',
            'display_name': 'OpEx Transfers', 
            'is_revenue': False,
            'category': 'Internal Transfers'
        },
        {
            'vendor_name': 'SGE Owner Pay (Mercury Checking xx5366)',
            'display_name': 'Owner Pay',
            'is_revenue': False,
            'category': 'Owner Distributions'
        },
        {
            'vendor_name': 'Bright Ideas Supply Chain Solutions',
            'display_name': 'Suppliers',
            'is_revenue': False,
            'category': 'Suppliers'
        }
    ]
    
    print(f"🔧 Adding {len(missing_vendors)} missing vendors for client: {client_id}")
    
    if dry_run:
        print("\n🔬 DRY RUN - Would add these vendors:")
        for vendor in missing_vendors:
            revenue_type = "REVENUE" if vendor['is_revenue'] else "EXPENSE"
            print(f"  - {vendor['vendor_name']} -> {vendor['display_name']} [{revenue_type}]")
        print("\nTo actually add vendors, run with: dry_run=False")
        return
    
    # Add vendors to database
    added_count = 0
    
    for vendor in missing_vendors:
        try:
            vendor_data = {
                'client_id': client_id,
                'vendor_name': vendor['vendor_name'],
                'display_name': vendor['display_name'],
                'category': vendor['category'],
                'is_revenue': vendor['is_revenue'],
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            result = supabase.table('vendors').insert(vendor_data).execute()
            added_count += 1
            print(f"✅ Added: {vendor['display_name']}")
            
        except Exception as e:
            print(f"❌ Error adding {vendor['display_name']}: {e}")
    
    print(f"\n🎉 Successfully added {added_count}/{len(missing_vendors)} vendors")
    print("\n📈 Expected impact:")
    print("  - Monthly deposits should jump from $5k to ~$124k")
    print("  - Monthly withdrawals should increase from $37k to ~$115k") 
    print("  - Weekly forecasts should match your actual volumes")
    print("\n🔄 Next steps:")
    print("  1. Run: python3 run_forecast.py")
    print("  2. Run: python3 main.py --weekly-view")

if __name__ == "__main__":
    # First run in dry-run mode
    add_missing_vendors(dry_run=True)