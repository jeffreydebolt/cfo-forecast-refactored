#!/usr/bin/env python3
"""
Fix bestself Amazon vendor mappings by creating proper display name mappings.
"""

from supabase_client import supabase
import pandas as pd

def get_unmapped_amazon_vendors():
    """Get all Amazon vendor names that don't have proper mappings."""
    
    print("🔍 Finding unmapped Amazon vendors...")
    
    try:
        # Get all Amazon transaction vendor names
        response = supabase.table('transactions').select(
            'vendor_name, amount'
        ).eq('client_id', 'bestself').ilike('vendor_name', '%AMAZON%').execute()
        
        amazon_transactions = response.data
        
        # Calculate totals per vendor
        vendor_totals = {}
        for txn in amazon_transactions:
            vendor = txn['vendor_name']
            amount = float(txn['amount'])
            
            if vendor not in vendor_totals:
                vendor_totals[vendor] = {'total': 0, 'count': 0}
            vendor_totals[vendor]['total'] += amount
            vendor_totals[vendor]['count'] += 1
            
        # Get existing Amazon mappings
        response = supabase.table('vendors').select(
            'vendor_name'
        ).eq('client_id', 'bestself').ilike('vendor_name', '%AMAZON%').execute()
        
        mapped_vendors = set(v['vendor_name'] for v in response.data if v['vendor_name'])
        
        # Find unmapped ones
        unmapped = []
        for vendor_name, stats in vendor_totals.items():
            if vendor_name not in mapped_vendors:
                unmapped.append({
                    'vendor_name': vendor_name,
                    'total_amount': stats['total'],
                    'transaction_count': stats['count']
                })
        
        # Sort by total amount descending
        unmapped.sort(key=lambda x: x['total_amount'], reverse=True)
        
        print(f"Found {len(unmapped)} unmapped Amazon vendors")
        print(f"Total unmapped Amazon revenue: ${sum(v['total_amount'] for v in unmapped):,.2f}")
        
        return unmapped
        
    except Exception as e:
        print(f"❌ Error finding unmapped vendors: {e}")
        return []

def create_amazon_vendor_mappings(unmapped_vendors):
    """Create vendor mappings for Amazon vendors."""
    
    print("🔧 Creating Amazon vendor mappings...")
    
    created_count = 0
    total_revenue = 0
    
    for vendor in unmapped_vendors:
        vendor_name = vendor['vendor_name']
        amount = vendor['total_amount']
        count = vendor['transaction_count']
        
        try:
            # Create vendor mapping
            insert_data = {
                'vendor_name': vendor_name,
                'client_id': 'bestself',
                'display_name': 'Amazon Revenue',
                'category': 'E-commerce Revenue',
                'is_revenue': True,
                'is_refund': False,
                'forecast_method': 'pattern_detected',
                'review_needed': False
            }
            
            result = supabase.table('vendors').insert(insert_data).execute()
            
            if result.data:
                print(f"✅ Mapped {vendor_name}: ${amount:,.2f} ({count} transactions)")
                created_count += 1
                total_revenue += amount
            else:
                print(f"❌ Failed to map {vendor_name}")
                
        except Exception as e:
            print(f"❌ Error mapping {vendor_name}: {e}")
    
    print(f"\n✅ Created {created_count} Amazon vendor mappings")
    print(f"📊 Total Amazon revenue now mapped: ${total_revenue:,.2f}")
    
    return created_count

def check_other_missing_revenue_vendors():
    """Check for other high-value vendors that might be missing mappings."""
    
    print("🔍 Checking for other missing revenue vendors...")
    
    try:
        # Get all transactions grouped by vendor
        response = supabase.table('transactions').select(
            'vendor_name, amount'
        ).eq('client_id', 'bestself').execute()
        
        transactions = response.data
        
        # Calculate vendor totals
        vendor_totals = {}
        for txn in transactions:
            vendor = txn['vendor_name']
            if not vendor:
                continue
                
            amount = float(txn['amount'])
            
            if vendor not in vendor_totals:
                vendor_totals[vendor] = {'total': 0, 'count': 0}
            vendor_totals[vendor]['total'] += amount
            vendor_totals[vendor]['count'] += 1
        
        # Get existing vendor mappings
        response = supabase.table('vendors').select(
            'vendor_name'
        ).eq('client_id', 'bestself').execute()
        
        mapped_vendors = set(v['vendor_name'] for v in response.data if v['vendor_name'])
        
        # Find large unmapped vendors (>$1000 total)
        large_unmapped = []
        for vendor_name, stats in vendor_totals.items():
            if vendor_name not in mapped_vendors and stats['total'] > 1000:
                large_unmapped.append({
                    'vendor_name': vendor_name,
                    'total_amount': stats['total'],
                    'transaction_count': stats['count']
                })
        
        # Sort by amount
        large_unmapped.sort(key=lambda x: x['total_amount'], reverse=True)
        
        print(f"\n📊 OTHER LARGE UNMAPPED VENDORS (>${1000:,}+):")
        for vendor in large_unmapped[:10]:  # Top 10
            print(f"  {vendor['vendor_name']}: ${vendor['total_amount']:,.2f} ({vendor['transaction_count']} transactions)")
            
        return large_unmapped
        
    except Exception as e:
        print(f"❌ Error checking other vendors: {e}")
        return []

def main():
    """Main function to fix Amazon mappings."""
    
    print("🚀 Starting bestself Amazon vendor mapping fix...")
    print("=" * 60)
    
    # Get unmapped Amazon vendors
    unmapped_amazon = get_unmapped_amazon_vendors()
    
    if unmapped_amazon:
        print(f"\n📊 TOP 10 UNMAPPED AMAZON VENDORS:")
        for vendor in unmapped_amazon[:10]:
            print(f"  {vendor['vendor_name']}: ${vendor['total_amount']:,.2f} ({vendor['transaction_count']} transactions)")
        
        # Create mappings
        created = create_amazon_vendor_mappings(unmapped_amazon)
        
        if created > 0:
            print(f"\n✅ Successfully created {created} Amazon vendor mappings!")
            print("   Amazon revenue will now be included in forecasts.")
        else:
            print(f"\n❌ Failed to create Amazon vendor mappings.")
    else:
        print("✅ All Amazon vendors are already mapped!")
    
    # Check for other missing vendors
    other_unmapped = check_other_missing_revenue_vendors()
    
    print("\n" + "=" * 60)
    print("🔍 SUMMARY")
    print("=" * 60)
    
    if unmapped_amazon:
        total_amazon_revenue = sum(v['total_amount'] for v in unmapped_amazon)
        print(f"🎯 Fixed missing Amazon revenue: ${total_amazon_revenue:,.2f}")
        print("   This should significantly increase forecast amounts!")
    
    if other_unmapped:
        print(f"\n⚠️  Found {len(other_unmapped)} other large unmapped vendors")
        print("   Consider reviewing these for potential revenue sources")
    
    print("\n✅ Amazon mapping fix complete!")

if __name__ == "__main__":
    main()