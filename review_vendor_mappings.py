#!/usr/bin/env python3
"""
Show current vendor mappings for review before forecasting.
"""

import sys
sys.path.append('.')

from lean_forecasting.temp_vendor_groups import temp_vendor_group_manager
from supabase_client import supabase

def show_current_vendor_mappings(client_id):
    """Show current vendor display name mappings for review."""
    print(f"📋 CURRENT VENDOR MAPPINGS FOR {client_id.upper()}")
    print("=" * 70)
    
    try:
        # Get all vendors with their display names
        result = supabase.table('vendors').select(
            'vendor_name, display_name'
        ).eq('client_id', client_id).execute()
        
        if not result.data:
            print("❌ No vendors found")
            return
        
        # Group by display name
        mappings = {}
        for vendor in result.data:
            display_name = vendor['display_name'] or 'UNMAPPED'
            vendor_name = vendor['vendor_name']
            
            if display_name not in mappings:
                mappings[display_name] = []
            mappings[display_name].append(vendor_name)
        
        print(f"Found {len(result.data)} vendor names mapped to {len(mappings)} display names:\n")
        
        for display_name, vendor_names in sorted(mappings.items()):
            print(f"📁 {display_name}")
            print(f"   └── {len(vendor_names)} vendor names:")
            for vendor_name in sorted(vendor_names)[:5]:  # Show first 5
                print(f"       • {vendor_name}")
            if len(vendor_names) > 5:
                print(f"       • ... and {len(vendor_names) - 5} more")
            print()
        
        return mappings
        
    except Exception as e:
        print(f"❌ Error getting vendor mappings: {e}")
        return {}

def show_suggested_vendor_groups(mappings):
    """Show suggested vendor groups for review."""
    print(f"💡 SUGGESTED VENDOR GROUPS FOR REVIEW:")
    print("=" * 70)
    
    # Filter to revenue-related display names
    revenue_mappings = {
        display_name: vendors 
        for display_name, vendors in mappings.items() 
        if 'Revenue' in display_name or 'BESTSELFCO' in display_name
    }
    
    if not revenue_mappings:
        print("❌ No revenue-related display names found")
        return
    
    print("These display names contain 'Revenue' or 'BESTSELFCO':")
    print()
    
    for display_name, vendor_names in sorted(revenue_mappings.items()):
        print(f"✅ {display_name} ({len(vendor_names)} vendors)")
    
    print(f"\n❓ PLEASE REVIEW:")
    print(f"1. Are these the correct revenue streams?")
    print(f"2. Should any be grouped together?")
    print(f"3. Should any be excluded from forecasting?")
    print(f"4. Are there any missing revenue streams?")

def main():
    """Main function."""
    client_id = 'bestself'
    
    # Show current mappings for review
    mappings = show_current_vendor_mappings(client_id)
    
    if mappings:
        show_suggested_vendor_groups(mappings)

if __name__ == "__main__":
    main()