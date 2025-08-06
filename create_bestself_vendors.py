#!/usr/bin/env python3
"""
Create vendor mappings for the bestself client based on transaction analysis.
"""

from supabase_client import supabase
from datetime import datetime

def create_bestself_vendors():
    """Create vendor mappings for major bestself vendors."""
    
    # Major vendors based on transaction analysis
    vendors = [
        {
            'vendor_name': 'SHOPIFY',
            'display_name': 'Shopify Revenue',
            'is_revenue': True,
            'category': 'E-commerce Revenue',
            'forecast_method': 'trailing_avg',
            'forecast_frequency': 'daily'
        },
        {
            'vendor_name': 'BESTSELFCO',
            'display_name': 'BestSelf Revenue',
            'is_revenue': True,
            'category': 'Primary Revenue',
            'forecast_method': 'trailing_avg',
            'forecast_frequency': 'daily'
        },
        {
            'vendor_name': 'SHOPPAYINST AFRM',
            'display_name': 'Affirm Payments',
            'is_revenue': True,
            'category': 'Payment Processing',
            'forecast_method': 'trailing_avg',
            'forecast_frequency': 'daily'
        },
        {
            'vendor_name': 'STRIPE',
            'display_name': 'Stripe Revenue',
            'is_revenue': True,
            'category': 'Payment Processing',
            'forecast_method': 'trailing_avg',
            'forecast_frequency': 'daily'
        },
        {
            'vendor_name': 'Armbrust Holdings LLC',
            'display_name': 'Armbrust Expenses',
            'is_revenue': False,
            'category': 'Operating Expenses',
            'forecast_method': 'trailing_avg',
            'forecast_frequency': 'weekly'
        },
        {
            'vendor_name': 'Wise (Wise)',
            'display_name': 'Wise Transfers',
            'is_revenue': False,
            'category': 'International Transfers',
            'forecast_method': 'trailing_avg',
            'forecast_frequency': 'weekly'
        },
        {
            'vendor_name': 'TikTok Inc',
            'display_name': 'TikTok Revenue',
            'is_revenue': True,
            'category': 'Social Commerce',
            'forecast_method': 'trailing_avg',
            'forecast_frequency': 'daily'
        },
        {
            'vendor_name': 'FAIRE WHOLESALE',
            'display_name': 'Faire Revenue',
            'is_revenue': True,
            'category': 'Wholesale Revenue',
            'forecast_method': 'trailing_avg',
            'forecast_frequency': 'weekly'
        },
        {
            'vendor_name': 'Intl. Wire Fee',
            'display_name': 'Wire Fees',
            'is_revenue': False,
            'category': 'Banking Fees',
            'forecast_method': 'trailing_avg',
            'forecast_frequency': 'monthly'
        }
    ]
    
    print(f"🔧 Creating {len(vendors)} vendor mappings for bestself client...")
    
    added_count = 0
    
    for vendor in vendors:
        try:
            vendor_data = {
                'client_id': 'bestself',
                'vendor_name': vendor['vendor_name'],
                'display_name': vendor['display_name'],
                'category': vendor['category'],
                'is_revenue': vendor['is_revenue'],
                'forecast_method': vendor['forecast_method'],
                'forecast_frequency': vendor['forecast_frequency'],
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            result = supabase.table('vendors').insert(vendor_data).execute()
            added_count += 1
            revenue_type = "REVENUE" if vendor['is_revenue'] else "EXPENSE"
            print(f"✅ Added: {vendor['display_name']} [{revenue_type}]")
            
        except Exception as e:
            print(f"❌ Error adding {vendor['display_name']}: {e}")
    
    print(f"\n🎉 Successfully added {added_count}/{len(vendors)} vendors")
    print(f"\n🔄 Next steps:")
    print(f"  1. Run: python3 run_forecast.py")
    print(f"  2. Run: python3 main.py --weekly-view")

if __name__ == "__main__":
    create_bestself_vendors()