#!/usr/bin/env python3
"""
Lean Vendor Group Management - Simple CRUD operations for vendor groups.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, date
from supabase_client import supabase

logger = logging.getLogger(__name__)

class VendorGroupManager:
    """Simple, lean vendor group management."""
    
    def __init__(self):
        pass
    
    def create_vendor_group(self, client_id: str, group_name: str, 
                          vendor_display_names: List[str],
                          forecast_method: str = "weighted_average") -> Dict[str, Any]:
        """Create a new vendor group."""
        try:
            group_data = {
                'client_id': client_id,
                'group_name': group_name,
                'vendor_display_names': vendor_display_names,
                'forecast_method': forecast_method,
                'is_active': True,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            result = supabase.table('vendor_groups').insert(group_data).execute()
            
            if result.data:
                logger.info(f"✅ Created vendor group: {group_name} with {len(vendor_display_names)} vendors")
                return {
                    'success': True,
                    'group_id': result.data[0]['id'],
                    'group_name': group_name,
                    'vendor_count': len(vendor_display_names)
                }
            else:
                logger.error(f"Failed to create vendor group: {group_name}")
                return {'success': False, 'error': 'Database insert failed'}
                
        except Exception as e:
            logger.error(f"Error creating vendor group {group_name}: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_vendor_groups(self, client_id: str) -> List[Dict[str, Any]]:
        """Get all vendor groups for a client."""
        try:
            result = supabase.table('vendor_groups').select('*').eq(
                'client_id', client_id
            ).eq(
                'is_active', True
            ).order('group_name').execute()
            
            return result.data
            
        except Exception as e:
            logger.error(f"Error getting vendor groups for {client_id}: {e}")
            return []
    
    def get_vendor_group(self, client_id: str, group_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific vendor group."""
        try:
            result = supabase.table('vendor_groups').select('*').eq(
                'client_id', client_id
            ).eq(
                'group_name', group_name
            ).eq(
                'is_active', True
            ).execute()
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error(f"Error getting vendor group {group_name}: {e}")
            return None
    
    def update_vendor_group(self, client_id: str, group_name: str, 
                          updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update a vendor group."""
        try:
            updates['updated_at'] = datetime.now().isoformat()
            
            result = supabase.table('vendor_groups').update(updates).eq(
                'client_id', client_id
            ).eq(
                'group_name', group_name
            ).execute()
            
            if result.data:
                logger.info(f"✅ Updated vendor group: {group_name}")
                return {'success': True, 'updated': len(result.data)}
            else:
                logger.warning(f"No vendor group found to update: {group_name}")
                return {'success': False, 'error': 'Group not found'}
                
        except Exception as e:
            logger.error(f"Error updating vendor group {group_name}: {e}")
            return {'success': False, 'error': str(e)}
    
    def delete_vendor_group(self, client_id: str, group_name: str) -> Dict[str, Any]:
        """Soft delete a vendor group (mark as inactive)."""
        try:
            result = supabase.table('vendor_groups').update({
                'is_active': False,
                'updated_at': datetime.now().isoformat()
            }).eq(
                'client_id', client_id
            ).eq(
                'group_name', group_name
            ).execute()
            
            if result.data:
                logger.info(f"✅ Deleted vendor group: {group_name}")
                return {'success': True}
            else:
                return {'success': False, 'error': 'Group not found'}
                
        except Exception as e:
            logger.error(f"Error deleting vendor group {group_name}: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_vendor_group_transactions(self, client_id: str, group_name: str, 
                                    days_back: int = 90) -> List[Dict[str, Any]]:
        """Get all transactions for vendors in this group."""
        try:
            # Get the vendor group
            group = self.get_vendor_group(client_id, group_name)
            if not group:
                logger.warning(f"Vendor group not found: {group_name}")
                return []
            
            vendor_display_names = group['vendor_display_names']
            if not vendor_display_names:
                logger.warning(f"No vendors in group: {group_name}")
                return []
            
            # Get all vendor names that map to these display names
            all_vendor_names = []
            for display_name in vendor_display_names:
                vendor_result = supabase.table('vendors').select('vendor_name').eq(
                    'client_id', client_id
                ).eq(
                    'display_name', display_name
                ).execute()
                
                vendor_names = [v['vendor_name'] for v in vendor_result.data]
                all_vendor_names.extend(vendor_names)
            
            if not all_vendor_names:
                logger.warning(f"No vendor names found for group {group_name}")
                return []
            
            # Calculate date range
            end_date = datetime.now().date()
            start_date = end_date - datetime.timedelta(days=days_back)
            
            # Get transactions for all vendor names in the group
            txn_result = supabase.table('transactions').select(
                'transaction_date, amount, vendor_name, description'
            ).eq(
                'client_id', client_id
            ).in_(
                'vendor_name', all_vendor_names
            ).gte(
                'transaction_date', start_date.isoformat()
            ).lte(
                'transaction_date', end_date.isoformat()
            ).order('transaction_date', desc=True).execute()
            
            logger.info(f"Found {len(txn_result.data)} transactions for vendor group '{group_name}'")
            return txn_result.data
            
        except Exception as e:
            logger.error(f"Error getting transactions for vendor group {group_name}: {e}")
            return []
    
    def show_group_status(self, client_id: str):
        """Show status of all vendor groups for a client."""
        groups = self.get_vendor_groups(client_id)
        
        print(f"\n📊 VENDOR GROUPS STATUS FOR {client_id.upper()}")
        print("=" * 70)
        
        if not groups:
            print("⚠️  No vendor groups found for this client")
            print("\n💡 Use create_vendor_group() to create your first group")
            return
        
        for group in groups:
            group_name = group['group_name']
            vendors = group.get('vendor_display_names', [])
            pattern = group.get('pattern_frequency', 'Not analyzed')
            method = group.get('forecast_method', 'weighted_average')
            
            print(f"\n📁 {group_name}")
            print(f"   Vendors: {len(vendors)} ({', '.join(vendors[:3])}{'...' if len(vendors) > 3 else ''})")
            print(f"   Pattern: {pattern}")
            print(f"   Method: {method}")
            
            # Get recent transaction count
            try:
                txns = self.get_vendor_group_transactions(client_id, group_name, 30)
                print(f"   Recent Activity: {len(txns)} transactions (last 30 days)")
            except:
                print(f"   Recent Activity: Unable to fetch")
        
        print(f"\n✅ Total: {len(groups)} vendor groups")


# Global instance for easy import
vendor_group_manager = VendorGroupManager()


def create_sample_vendor_groups(client_id: str):
    """Create sample vendor groups for testing."""
    print(f"🧪 Creating sample vendor groups for {client_id}...")
    
    sample_groups = [
        {
            'group_name': 'BestSelf Revenue',
            'vendor_display_names': ['BESTSELFCO', 'Shopify Revenue', 'Stripe Revenue'],
            'forecast_method': 'weighted_average'
        },
        {
            'group_name': 'Amazon Revenue', 
            'vendor_display_names': ['Amazon Revenue'],
            'forecast_method': 'weighted_average'
        },
        {
            'group_name': 'Payment Processing Fees',
            'vendor_display_names': ['Affirm Payments', 'Wire Fees'],
            'forecast_method': 'weighted_average'
        }
    ]
    
    results = []
    for group_data in sample_groups:
        result = vendor_group_manager.create_vendor_group(
            client_id=client_id,
            group_name=group_data['group_name'],
            vendor_display_names=group_data['vendor_display_names'],
            forecast_method=group_data['forecast_method']
        )
        results.append(result)
        
        if result['success']:
            print(f"✅ Created: {group_data['group_name']}")
        else:
            print(f"❌ Failed: {group_data['group_name']} - {result.get('error')}")
    
    return results


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python vendor_groups.py <client_id> [command]")
        print("Commands: status, create_samples")
        sys.exit(1)
    
    client_id = sys.argv[1]
    command = sys.argv[2] if len(sys.argv) > 2 else 'status'
    
    if command == 'status':
        vendor_group_manager.show_group_status(client_id)
    elif command == 'create_samples':
        create_sample_vendor_groups(client_id)
        vendor_group_manager.show_group_status(client_id)
    else:
        print(f"Unknown command: {command}")