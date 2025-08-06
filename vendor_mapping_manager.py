#!/usr/bin/env python3
"""
Vendor Mapping Manager
Allows users to group multiple vendor display names into logical business entities.
"""

import argparse
import logging
from typing import Dict, List, Any, Optional
from supabase_client import supabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VendorMappingManager:
    """Manages logical vendor groupings for pattern detection and forecasting."""
    
    def __init__(self):
        self.client_id = None
    
    def get_unmapped_vendors(self, client_id: str) -> List[Dict[str, Any]]:
        """Get all vendor display names that haven't been grouped yet."""
        try:
            # Get all vendors for this client
            vendors_result = supabase.table('vendors').select(
                'display_name, vendor_name, is_revenue, category'
            ).eq('client_id', client_id).execute()
            
            # Get existing vendor group mappings
            groups_result = supabase.table('vendor_groups').select(
                'group_name, vendor_display_names'
            ).eq('client_id', client_id).execute()
            
            # Create set of already mapped vendors
            mapped_vendors = set()
            if groups_result.data:
                for group in groups_result.data:
                    vendor_names = group.get('vendor_display_names', [])
                    if isinstance(vendor_names, list):
                        mapped_vendors.update(vendor_names)
            
            # Return unmapped vendors
            unmapped = []
            for vendor in vendors_result.data:
                display_name = vendor['display_name']
                if display_name and display_name not in mapped_vendors:
                    unmapped.append(vendor)
            
            return unmapped
            
        except Exception as e:
            logger.error(f"Error getting unmapped vendors: {e}")
            return []
    
    def get_vendor_groups(self, client_id: str) -> List[Dict[str, Any]]:
        """Get all existing vendor groups for a client."""
        try:
            result = supabase.table('vendor_groups').select('*').eq(
                'client_id', client_id
            ).execute()
            return result.data
        except Exception as e:
            logger.error(f"Error getting vendor groups: {e}")
            return []
    
    def create_vendor_group(self, client_id: str, group_name: str, 
                          vendor_display_names: List[str], 
                          is_revenue: bool = True,
                          category: str = "Revenue") -> bool:
        """Create a new vendor group."""
        try:
            group_data = {
                'client_id': client_id,
                'group_name': group_name,
                'vendor_display_names': vendor_display_names,
                'is_revenue': is_revenue,
                'category': category,
                'forecast_frequency': None,  # Will be determined by pattern detection
                'forecast_amount': 0.0,
                'forecast_confidence': 0.0
            }
            
            result = supabase.table('vendor_groups').insert(group_data).execute()
            
            if result.data:
                logger.info(f"✅ Created vendor group: {group_name} with {len(vendor_display_names)} vendors")
                return True
            else:
                logger.error(f"Failed to create vendor group: {group_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error creating vendor group: {e}")
            return False
    
    def update_vendor_group(self, client_id: str, group_name: str, 
                          vendor_display_names: List[str]) -> bool:
        """Update an existing vendor group."""
        try:
            result = supabase.table('vendor_groups').update({
                'vendor_display_names': vendor_display_names
            }).eq('client_id', client_id).eq('group_name', group_name).execute()
            
            if result.data:
                logger.info(f"✅ Updated vendor group: {group_name}")
                return True
            else:
                logger.error(f"No vendor group found to update: {group_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating vendor group: {e}")
            return False
    
    def delete_vendor_group(self, client_id: str, group_name: str) -> bool:
        """Delete a vendor group."""
        try:
            result = supabase.table('vendor_groups').delete().eq(
                'client_id', client_id
            ).eq('group_name', group_name).execute()
            
            logger.info(f"✅ Deleted vendor group: {group_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting vendor group: {e}")
            return False
    
    def show_mapping_status(self, client_id: str):
        """Show current mapping status for a client."""
        print(f"\n📊 VENDOR MAPPING STATUS FOR {client_id.upper()}")
        print("=" * 80)
        
        # Show existing groups
        groups = self.get_vendor_groups(client_id)
        if groups:
            print(f"\n✅ EXISTING VENDOR GROUPS ({len(groups)}):")
            print("-" * 50)
            for group in groups:
                vendors = group.get('vendor_display_names', [])
                print(f"📁 {group['group_name']} ({len(vendors)} vendors)")
                for vendor in vendors:
                    print(f"   • {vendor}")
                print()
        
        # Show unmapped vendors
        unmapped = self.get_unmapped_vendors(client_id)
        if unmapped:
            print(f"⚠️  UNMAPPED VENDORS ({len(unmapped)}):")
            print("-" * 50)
            for vendor in unmapped:
                revenue_icon = "📈" if vendor.get('is_revenue') else "📉"
                print(f"{revenue_icon} {vendor['display_name']} ({vendor.get('category', 'Unknown')})")
        else:
            print("✅ All vendors are mapped to groups!")
        
        return len(unmapped)
    
    def interactive_mapping(self, client_id: str):
        """Interactive vendor mapping process."""
        print(f"\n🎯 INTERACTIVE VENDOR MAPPING FOR {client_id.upper()}")
        print("=" * 80)
        
        while True:
            unmapped_count = self.show_mapping_status(client_id)
            
            if unmapped_count == 0:
                print("\n🎉 All vendors are mapped! Mapping complete.")
                break
            
            print(f"\n📋 MAPPING OPTIONS:")
            print("1. Create new vendor group")
            print("2. Add vendors to existing group") 
            print("3. Delete vendor group")
            print("4. Exit")
            
            choice = input("\nSelect option (1-4): ").strip()
            
            if choice == "1":
                self.create_group_interactive(client_id)
            elif choice == "2":
                self.add_to_group_interactive(client_id)
            elif choice == "3":
                self.delete_group_interactive(client_id)
            elif choice == "4":
                break
            else:
                print("Invalid choice. Please select 1-4.")
    
    def create_group_interactive(self, client_id: str):
        """Interactive group creation."""
        unmapped = self.get_unmapped_vendors(client_id)
        if not unmapped:
            print("No unmapped vendors available.")
            return
        
        print(f"\n📝 CREATE NEW VENDOR GROUP")
        print("-" * 40)
        
        group_name = input("Enter group name (e.g., 'Shopify Revenue'): ").strip()
        if not group_name:
            print("Group name cannot be empty.")
            return
        
        print(f"\nAvailable unmapped vendors:")
        for i, vendor in enumerate(unmapped, 1):
            revenue_icon = "📈" if vendor.get('is_revenue') else "📉"
            print(f"{i:2d}. {revenue_icon} {vendor['display_name']}")
        
        selected_input = input("\nEnter vendor numbers to group (e.g., '1,3,5' or 'all'): ").strip()
        
        if selected_input.lower() == 'all':
            selected_vendors = [v['display_name'] for v in unmapped]
        else:
            try:
                indices = [int(x.strip()) - 1 for x in selected_input.split(',')]
                selected_vendors = [unmapped[i]['display_name'] for i in indices if 0 <= i < len(unmapped)]
            except (ValueError, IndexError):
                print("Invalid selection. Please use numbers separated by commas.")
                return
        
        if not selected_vendors:
            print("No vendors selected.")
            return
        
        # Determine if revenue or expense based on first vendor
        is_revenue = unmapped[0].get('is_revenue', True)
        category = input(f"Enter category (default: {'Revenue' if is_revenue else 'Expense'}): ").strip()
        if not category:
            category = 'Revenue' if is_revenue else 'Expense'
        
        if self.create_vendor_group(client_id, group_name, selected_vendors, is_revenue, category):
            print(f"✅ Created group '{group_name}' with {len(selected_vendors)} vendors")
        else:
            print(f"❌ Failed to create group '{group_name}'")
    
    def add_to_group_interactive(self, client_id: str):
        """Add vendors to existing group."""
        groups = self.get_vendor_groups(client_id)
        unmapped = self.get_unmapped_vendors(client_id)
        
        if not groups:
            print("No existing groups found.")
            return
        
        if not unmapped:
            print("No unmapped vendors to add.")
            return
        
        print(f"\n📁 SELECT GROUP TO ADD VENDORS TO:")
        for i, group in enumerate(groups, 1):
            print(f"{i:2d}. {group['group_name']} ({len(group.get('vendor_display_names', []))} vendors)")
        
        try:
            group_index = int(input("Select group number: ").strip()) - 1
            selected_group = groups[group_index]
        except (ValueError, IndexError):
            print("Invalid group selection.")
            return
        
        print(f"\nAvailable unmapped vendors:")
        for i, vendor in enumerate(unmapped, 1):
            revenue_icon = "📈" if vendor.get('is_revenue') else "📉"
            print(f"{i:2d}. {revenue_icon} {vendor['display_name']}")
        
        selected_input = input("\nEnter vendor numbers to add (e.g., '1,3,5'): ").strip()
        
        try:
            indices = [int(x.strip()) - 1 for x in selected_input.split(',')]
            new_vendors = [unmapped[i]['display_name'] for i in indices if 0 <= i < len(unmapped)]
        except (ValueError, IndexError):
            print("Invalid selection.")
            return
        
        if not new_vendors:
            print("No vendors selected.")
            return
        
        # Update the group with additional vendors
        current_vendors = selected_group.get('vendor_display_names', [])
        updated_vendors = current_vendors + new_vendors
        
        if self.update_vendor_group(client_id, selected_group['group_name'], updated_vendors):
            print(f"✅ Added {len(new_vendors)} vendors to '{selected_group['group_name']}'")
        else:
            print(f"❌ Failed to update group")
    
    def delete_group_interactive(self, client_id: str):
        """Delete a vendor group."""
        groups = self.get_vendor_groups(client_id)
        
        if not groups:
            print("No groups found to delete.")
            return
        
        print(f"\n🗑️  SELECT GROUP TO DELETE:")
        for i, group in enumerate(groups, 1):
            print(f"{i:2d}. {group['group_name']} ({len(group.get('vendor_display_names', []))} vendors)")
        
        try:
            group_index = int(input("Select group number to delete: ").strip()) - 1
            selected_group = groups[group_index]
        except (ValueError, IndexError):
            print("Invalid group selection.")
            return
        
        confirm = input(f"⚠️  Delete '{selected_group['group_name']}'? (yes/no): ").strip().lower()
        
        if confirm in ['yes', 'y']:
            if self.delete_vendor_group(client_id, selected_group['group_name']):
                print(f"✅ Deleted group '{selected_group['group_name']}'")
            else:
                print(f"❌ Failed to delete group")
        else:
            print("Delete cancelled.")

def main():
    parser = argparse.ArgumentParser(description='Manage vendor mappings and groupings')
    parser.add_argument('--client', required=True, help='Client ID')
    parser.add_argument('--interactive', action='store_true', help='Interactive mapping mode')
    parser.add_argument('--status', action='store_true', help='Show mapping status only')
    
    args = parser.parse_args()
    
    manager = VendorMappingManager()
    
    if args.status:
        manager.show_mapping_status(args.client)
    elif args.interactive:
        manager.interactive_mapping(args.client)
    else:
        print("Use --interactive for mapping or --status to view current state")

if __name__ == "__main__":
    main()