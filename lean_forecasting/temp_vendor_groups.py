#!/usr/bin/env python3
"""
Temporary Vendor Group Manager - Using existing vendors table until we create proper schema.
This allows us to start testing the lean forecasting logic immediately.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from supabase_client import supabase

logger = logging.getLogger(__name__)

class TempVendorGroupManager:
    """Temporary vendor group management using existing vendors table."""
    
    def __init__(self):
        pass
    
    def create_vendor_group_from_display_names(self, client_id: str, group_name: str, 
                                             display_names: List[str]) -> Dict[str, Any]:
        """Create a logical vendor group from existing display names."""
        try:
            # Verify all display names exist for this client
            existing_vendors = []
            for display_name in display_names:
                result = supabase.table('vendors').select('display_name, vendor_name').eq(
                    'client_id', client_id
                ).eq(
                    'display_name', display_name
                ).execute()
                
                if result.data:
                    existing_vendors.extend(result.data)
                else:
                    logger.warning(f"Display name not found: {display_name}")
            
            if not existing_vendors:
                return {'success': False, 'error': 'No valid display names found'}
            
            # For now, we'll store the group info in a simple format
            # Later this will go into the proper vendor_groups table
            group_info = {
                'group_name': group_name,
                'client_id': client_id,
                'display_names': list(set([v['display_name'] for v in existing_vendors])),
                'vendor_names': list(set([v['vendor_name'] for v in existing_vendors])),
                'vendor_count': len(existing_vendors)
            }
            
            logger.info(f"✅ Created logical group: {group_name} with {len(existing_vendors)} vendors")
            return {'success': True, 'group_info': group_info}
            
        except Exception as e:
            logger.error(f"Error creating vendor group {group_name}: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_available_display_names(self, client_id: str) -> List[str]:
        """Get all available display names for a client."""
        try:
            result = supabase.table('vendors').select('display_name').eq(
                'client_id', client_id
            ).execute()
            
            # Get unique display names
            display_names = list(set([v['display_name'] for v in result.data if v['display_name']]))
            display_names.sort()
            
            return display_names
            
        except Exception as e:
            logger.error(f"Error getting display names for {client_id}: {e}")
            return []
    
    def get_vendor_group_transactions(self, client_id: str, display_names: List[str], 
                                    days_back: int = 90) -> List[Dict[str, Any]]:
        """Get all transactions for vendors with these display names."""
        try:
            # Get all vendor names that map to these display names
            all_vendor_names = []
            for display_name in display_names:
                vendor_result = supabase.table('vendors').select('vendor_name').eq(
                    'client_id', client_id
                ).eq(
                    'display_name', display_name
                ).execute()
                
                vendor_names = [v['vendor_name'] for v in vendor_result.data]
                all_vendor_names.extend(vendor_names)
            
            if not all_vendor_names:
                logger.warning(f"No vendor names found for display names: {display_names}")
                return []
            
            # Calculate date range
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days_back)
            
            # Get transactions for all vendor names
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
            
            logger.info(f"Found {len(txn_result.data)} transactions for group with {len(display_names)} display names")
            return txn_result.data
            
        except Exception as e:
            logger.error(f"Error getting transactions for display names {display_names}: {e}")
            return []
    
    def show_available_vendors(self, client_id: str):
        """Show all available vendors for grouping."""
        display_names = self.get_available_display_names(client_id)
        
        print(f"\n📊 AVAILABLE VENDORS FOR GROUPING - {client_id.upper()}")
        print("=" * 70)
        
        if not display_names:
            print("⚠️  No vendors found for this client")
            return
        
        print(f"Found {len(display_names)} unique display names:")
        
        for i, display_name in enumerate(display_names, 1):
            # Get transaction count for this display name
            try:
                txns = self.get_vendor_group_transactions(client_id, [display_name], 30)
                txn_count = len(txns)
                
                if txn_count > 0:
                    total_amount = sum(float(t['amount']) for t in txns)
                    print(f"{i:2d}. {display_name} ({txn_count} txns last 30 days, ${total_amount:,.2f} total)")
                else:
                    print(f"{i:2d}. {display_name} (no recent activity)")
            except:
                print(f"{i:2d}. {display_name} (unable to fetch activity)")
        
        print(f"\n💡 Use these display names to create vendor groups")
        print(f"💡 Example: create_bestself_groups() to create sample groups")
    
    def analyze_group_pattern(self, client_id: str, group_name: str, display_names: List[str]) -> Dict[str, Any]:
        """Simple pattern analysis for a vendor group."""
        try:
            # Get transactions for this group
            transactions = self.get_vendor_group_transactions(client_id, display_names, 90)
            
            if not transactions:
                return {
                    'group_name': group_name,
                    'pattern': 'No transactions found',
                    'frequency': 'irregular',
                    'confidence': 0.0
                }
            
            # Simple frequency analysis
            from collections import Counter
            import pandas as pd
            
            df = pd.DataFrame(transactions)
            df['transaction_date'] = pd.to_datetime(df['transaction_date'])
            
            # Count transactions per day of week (1=Monday, 7=Sunday)
            df['day_of_week'] = df['transaction_date'].dt.dayofweek + 1
            dow_counts = df['day_of_week'].value_counts()
            
            # Count transactions per day of month
            df['day_of_month'] = df['transaction_date'].dt.day
            dom_counts = df['day_of_month'].value_counts()
            
            # Simple pattern detection
            total_days = 90
            transaction_days = len(df['transaction_date'].dt.date.unique())
            daily_frequency = transaction_days / total_days
            
            if daily_frequency > 0.6:  # 60%+ of days have transactions
                pattern = 'daily'
                most_common_dow = dow_counts.index[0]
                day_names = {1: 'Monday', 2: 'Tuesday', 3: 'Wednesday', 4: 'Thursday', 
                           5: 'Friday', 6: 'Saturday', 7: 'Sunday'}
                details = f"Most active on {day_names[most_common_dow]}s"
            elif daily_frequency > 0.2:  # Weekly-ish pattern
                pattern = 'weekly'
                most_common_dow = dow_counts.index[0]
                day_names = {1: 'Monday', 2: 'Tuesday', 3: 'Wednesday', 4: 'Thursday', 
                           5: 'Friday', 6: 'Saturday', 7: 'Sunday'}
                details = f"Usually on {day_names[most_common_dow]}s"
            elif len(transactions) >= 3:  # Monthly-ish
                pattern = 'monthly'
                most_common_dom = dom_counts.index[0]
                details = f"Usually around the {most_common_dom}th of month"
            else:
                pattern = 'irregular'
                details = 'No clear pattern detected'
            
            avg_amount = df['amount'].mean()
            
            return {
                'group_name': group_name,
                'pattern': pattern,
                'details': details,
                'frequency': pattern,
                'confidence': min(daily_frequency * 2, 1.0),  # Simple confidence
                'transaction_count': len(transactions),
                'avg_amount': avg_amount,
                'date_range': f"{df['transaction_date'].min().date()} to {df['transaction_date'].max().date()}"
            }
            
        except Exception as e:
            logger.error(f"Error analyzing pattern for {group_name}: {e}")
            return {
                'group_name': group_name,
                'pattern': 'Error analyzing',
                'frequency': 'irregular',
                'confidence': 0.0,
                'error': str(e)
            }


# Global instance
temp_vendor_group_manager = TempVendorGroupManager()


def create_bestself_groups(client_id: str = 'bestself') -> List[Dict[str, Any]]:
    """Create sample vendor groups for BestSelf based on available data."""
    print(f"🧪 Creating BestSelf vendor groups for {client_id}...")
    
    # First, see what's available
    available = temp_vendor_group_manager.get_available_display_names(client_id)
    print(f"Available display names: {available[:10]}...")  # Show first 10
    
    # Define logical groups based on what we saw in the data
    sample_groups = [
        {
            'group_name': 'BestSelf Direct Revenue',
            'display_names': ['BESTSELFCO']  # Direct BestSelf sales
        },
        {
            'group_name': 'E-commerce Platform Revenue', 
            'display_names': ['Shopify Revenue', 'Stripe Revenue']  # Platform sales
        },
        {
            'group_name': 'Amazon Revenue',
            'display_names': ['Amazon Revenue']  # All Amazon variants
        },
        {
            'group_name': 'Payment Processing Fees',
            'display_names': ['Affirm Payments', 'Wire Fees']  # Processing costs
        }
    ]
    
    results = []
    for group_data in sample_groups:
        # Only include display names that actually exist
        valid_display_names = [dn for dn in group_data['display_names'] if dn in available]
        
        if valid_display_names:
            result = temp_vendor_group_manager.create_vendor_group_from_display_names(
                client_id=client_id,
                group_name=group_data['group_name'],
                display_names=valid_display_names
            )
            
            if result['success']:
                # Analyze the pattern
                pattern_analysis = temp_vendor_group_manager.analyze_group_pattern(
                    client_id, group_data['group_name'], valid_display_names
                )
                result['pattern_analysis'] = pattern_analysis
                
                print(f"✅ {group_data['group_name']}: {pattern_analysis['pattern']} - {pattern_analysis['details']}")
            else:
                print(f"❌ Failed: {group_data['group_name']} - {result.get('error')}")
                
            results.append(result)
        else:
            print(f"⚠️  Skipped: {group_data['group_name']} - no valid display names found")
    
    return results


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python temp_vendor_groups.py <client_id> [command]")
        print("Commands: show, create_bestself")
        sys.exit(1)
    
    client_id = sys.argv[1]
    command = sys.argv[2] if len(sys.argv) > 2 else 'show'
    
    if command == 'show':
        temp_vendor_group_manager.show_available_vendors(client_id)
    elif command == 'create_bestself':
        create_bestself_groups(client_id)
    else:
        print(f"Unknown command: {command}")