#!/usr/bin/env python3
"""
Smart Vendor Grouping Algorithm
Phase 1: Analyze raw vendor data and suggest meaningful business groupings
"""

import sys
sys.path.append('.')

from supabase_client import supabase
from datetime import datetime, date
from collections import defaultdict, Counter
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import re
import statistics

@dataclass
class GroupingSuggestion:
    """A suggestion to group vendors together"""
    group_name: str
    display_name: str
    vendors: List[Dict]  # Raw vendor data
    confidence: str  # high, medium, low
    reasoning: str
    total_monthly_amount: float
    transaction_count: int
    business_category: str

class SmartVendorGrouping:
    """Analyzes raw vendor data and suggests meaningful business groupings"""
    
    def __init__(self):
        # Business grouping patterns for e-commerce
        self.grouping_patterns = {
            'payroll_services': {
                'patterns': [r'gusto.*', r'adp.*', r'paychex.*', r'payroll.*'],
                'display_name': 'Payroll Services',
                'business_category': 'payroll',
                'confidence': 'high',
                'reasoning': 'All payroll service providers should be grouped together'
            },
            'credit_cards': {
                'patterns': [r'chase.*credit', r'amex.*', r'american.*express', r'capital.*one.*', r'visa.*', r'mastercard.*'],
                'display_name': 'Credit Cards',
                'business_category': 'credit_cards',
                'confidence': 'high',
                'reasoning': 'Credit card payments from same institution should be grouped'
            },
            'state_sales_tax': {
                'patterns': [r'.*sales.*tax.*', r'.*dept.*revenue.*', r'.*state.*tax.*', r'.*dept.*taxation.*', r'.*tax.*pymt.*'],
                'display_name': 'Sales Tax',
                'business_category': 'tax_payments',
                'confidence': 'medium',
                'reasoning': 'State sales tax payments - review if you need state-by-state tracking'
            },
            'shopify_payments': {
                'patterns': [r'shopify.*payment.*', r'shopify.*transfer.*', r'shopify.*payout.*'],
                'display_name': 'Shopify Revenue',
                'business_category': 'revenue',
                'confidence': 'high',
                'reasoning': 'Different Shopify payout types should be grouped as revenue'
            },
            'stripe_payments': {
                'patterns': [r'stripe.*transfer.*', r'stripe.*payment.*', r'stripe.*payout.*'],
                'display_name': 'Stripe Revenue',
                'business_category': 'revenue',
                'confidence': 'high',
                'reasoning': 'Stripe payment processing revenue'
            },
            'amazon_marketplace': {
                'patterns': [r'amazon.*payment.*', r'amazon.*settlement.*', r'amazon.*marketplace.*'],
                'display_name': 'Amazon Revenue',
                'business_category': 'revenue',
                'confidence': 'high',
                'reasoning': 'Amazon marketplace payments and settlements'
            },
            'paypal_revenue': {
                'patterns': [r'paypal.*transfer.*', r'paypal.*payment.*', r'paypal.*revenue.*'],
                'display_name': 'PayPal Revenue',
                'business_category': 'revenue',
                'confidence': 'high',
                'reasoning': 'PayPal payment processing revenue'
            },
            'bank_fees': {
                'patterns': [r'.*bank.*fee.*', r'.*wire.*fee.*', r'.*transfer.*fee.*', r'.*ach.*fee.*'],
                'display_name': 'Bank Fees',
                'business_category': 'bank_fees',
                'confidence': 'high',
                'reasoning': 'Banking and transfer fees should be grouped'
            },
            'software_subscriptions': {
                'patterns': [r'.*software.*', r'.*saas.*', r'.*subscription.*', r'.*monthly.*service.*'],
                'display_name': 'Software & SaaS',
                'business_category': 'software',
                'confidence': 'medium',
                'reasoning': 'Software subscriptions and SaaS services'
            },
            'marketing_advertising': {
                'patterns': [r'google.*ads.*', r'facebook.*ads.*', r'.*marketing.*', r'.*advertising.*'],
                'display_name': 'Marketing & Advertising',
                'business_category': 'marketing',
                'confidence': 'medium',
                'reasoning': 'Marketing and advertising expenses'
            },
            'inventory_suppliers': {
                'patterns': [r'.*supplier.*', r'.*inventory.*', r'.*wholesale.*', r'.*manufacturer.*'],
                'display_name': 'Inventory & Suppliers',
                'business_category': 'inventory',
                'confidence': 'medium',
                'reasoning': 'Inventory purchases and supplier payments'
            }
        }
    
    def analyze_and_suggest_groupings(self, client_id: str) -> Dict[str, List[GroupingSuggestion]]:
        """Main entry point - analyze vendors and suggest groupings"""
        print("🔍 SMART VENDOR GROUPING ANALYSIS")
        print("=" * 80)
        
        # Get raw vendor data
        vendor_data = self._get_vendor_transaction_data(client_id)
        print(f"📊 Analyzing {len(vendor_data)} individual vendors")
        
        # Generate grouping suggestions
        suggestions = self._generate_grouping_suggestions(vendor_data)
        
        # Organize by confidence level
        organized_suggestions = {
            'high_confidence': [],
            'medium_confidence': [], 
            'low_confidence': []
        }
        
        for suggestion in suggestions:
            organized_suggestions[f"{suggestion.confidence}_confidence"].append(suggestion)
        
        # Print summary
        print(f"\n📋 GROUPING ANALYSIS COMPLETE")
        print(f"Found {len(vendor_data)} individual vendors → Suggested {len(suggestions)} business groups")
        print(f"High Confidence: {len(organized_suggestions['high_confidence'])} groups")
        print(f"Medium Confidence: {len(organized_suggestions['medium_confidence'])} groups")
        print(f"Low Confidence: {len(organized_suggestions['low_confidence'])} groups")
        
        return organized_suggestions
    
    def _get_vendor_transaction_data(self, client_id: str) -> Dict[str, Dict]:
        """Get transaction data grouped by vendor name"""
        result = supabase.table('transactions').select('*').eq('client_id', client_id).execute()
        transactions = result.data
        
        # Group by vendor name
        vendor_data = defaultdict(lambda: {'transactions': [], 'total_amount': 0, 'monthly_amount': 0})
        
        for txn in transactions:
            vendor_name = txn['vendor_name']
            amount = float(txn['amount'])
            
            vendor_data[vendor_name]['transactions'].append(txn)
            vendor_data[vendor_name]['total_amount'] += amount
        
        # Calculate monthly amounts (rough estimate)
        for vendor_name, data in vendor_data.items():
            txn_count = len(data['transactions'])
            if txn_count > 0:
                # Estimate monthly amount based on transaction frequency
                date_range_days = self._calculate_date_range_days(data['transactions'])
                months_covered = max(1, date_range_days / 30)
                data['monthly_amount'] = abs(data['total_amount']) / months_covered
                data['vendor_name'] = vendor_name
        
        return dict(vendor_data)
    
    def _calculate_date_range_days(self, transactions: List[Dict]) -> int:
        """Calculate the date range covered by transactions"""
        if len(transactions) < 2:
            return 30  # Default to 1 month
        
        dates = [datetime.fromisoformat(txn['transaction_date']).date() for txn in transactions]
        date_range = (max(dates) - min(dates)).days
        return max(30, date_range)  # Minimum 1 month
    
    def _generate_grouping_suggestions(self, vendor_data: Dict[str, Dict]) -> List[GroupingSuggestion]:
        """Generate grouping suggestions based on patterns"""
        suggestions = []
        used_vendors = set()
        
        # Apply pattern-based grouping
        for group_key, group_config in self.grouping_patterns.items():
            matching_vendors = []
            
            for vendor_name, data in vendor_data.items():
                if vendor_name in used_vendors:
                    continue
                
                # Check if vendor matches any pattern
                vendor_lower = vendor_name.lower()
                for pattern in group_config['patterns']:
                    if re.search(pattern, vendor_lower):
                        matching_vendors.append({
                            'vendor_name': vendor_name,
                            'monthly_amount': data['monthly_amount'],
                            'transaction_count': len(data['transactions']),
                            'total_amount': data['total_amount']
                        })
                        used_vendors.add(vendor_name)
                        break
            
            # Create suggestion if we found matches
            if len(matching_vendors) >= 2:  # Only suggest grouping if 2+ vendors
                total_monthly = sum(v['monthly_amount'] for v in matching_vendors)
                total_transactions = sum(v['transaction_count'] for v in matching_vendors)
                
                suggestion = GroupingSuggestion(
                    group_name=group_key,
                    display_name=group_config['display_name'],
                    vendors=matching_vendors,
                    confidence=group_config['confidence'],
                    reasoning=group_config['reasoning'],
                    total_monthly_amount=total_monthly,
                    transaction_count=total_transactions,
                    business_category=group_config['business_category']
                )
                suggestions.append(suggestion)
        
        # Handle similar vendor names (like multiple Gusto accounts)
        remaining_vendors = {k: v for k, v in vendor_data.items() if k not in used_vendors}
        similar_name_groups = self._find_similar_name_groups(remaining_vendors)
        
        for group_name, vendors in similar_name_groups.items():
            if len(vendors) >= 2:
                vendor_list = []
                for vendor_name in vendors:
                    data = vendor_data[vendor_name]
                    vendor_list.append({
                        'vendor_name': vendor_name,
                        'monthly_amount': data['monthly_amount'],
                        'transaction_count': len(data['transactions']),
                        'total_amount': data['total_amount']
                    })
                    used_vendors.add(vendor_name)
                
                total_monthly = sum(v['monthly_amount'] for v in vendor_list)
                total_transactions = sum(v['transaction_count'] for v in vendor_list)
                
                suggestion = GroupingSuggestion(
                    group_name=f"similar_{group_name}",
                    display_name=f"{group_name.title()} Services",
                    vendors=vendor_list,
                    confidence='medium',
                    reasoning=f"Similar vendor names suggest same business entity",
                    total_monthly_amount=total_monthly,
                    transaction_count=total_transactions,
                    business_category='similar_names'
                )
                suggestions.append(suggestion)
        
        # Sort by total monthly amount (largest first)
        suggestions.sort(key=lambda x: x.total_monthly_amount, reverse=True)
        
        return suggestions
    
    def _find_similar_name_groups(self, vendor_data: Dict[str, Dict]) -> Dict[str, List[str]]:
        """Find vendors with similar names that might be the same business"""
        groups = defaultdict(list)
        
        for vendor_name in vendor_data.keys():
            # Extract base name (remove numbers, special chars)
            base_name = re.sub(r'[0-9\-_\s]+', '', vendor_name.lower())
            
            # Only group if base name is meaningful (3+ chars)
            if len(base_name) >= 3:
                groups[base_name].append(vendor_name)
        
        # Only return groups with 2+ vendors
        return {k: v for k, v in groups.items() if len(v) >= 2}
    
    def print_grouping_suggestions(self, suggestions: Dict[str, List[GroupingSuggestion]]):
        """Print formatted grouping suggestions"""
        print(f"\n📋 GROUPING SUGGESTIONS")
        print("=" * 80)
        
        # High confidence suggestions
        if suggestions['high_confidence']:
            print(f"\n✅ High Confidence Suggestions (Accept All | Review Individually)")
            for suggestion in suggestions['high_confidence']:
                print(f"├── {suggestion.display_name} ({len(suggestion.vendors)} vendors)")
                for vendor in suggestion.vendors[:3]:  # Show first 3
                    print(f"│   ├── {vendor['vendor_name']} - ${vendor['monthly_amount']:,.0f}/month ({vendor['transaction_count']} transactions)")
                if len(suggestion.vendors) > 3:
                    print(f"│   └── [{len(suggestion.vendors)-3} more vendors...]")
                print(f"│   → Combined: ${suggestion.total_monthly_amount:,.0f}/month")
                print(f"│   → Reasoning: {suggestion.reasoning}")
                print(f"│")
        
        # Medium confidence suggestions
        if suggestions['medium_confidence']:
            print(f"\n⚠️ Medium Confidence Suggestions (Review Required)")
            for suggestion in suggestions['medium_confidence']:
                print(f"└── {suggestion.display_name} ({len(suggestion.vendors)} vendors)")
                for vendor in suggestion.vendors[:5]:  # Show first 5
                    print(f"    ├── {vendor['vendor_name']} - ${vendor['monthly_amount']:,.0f}/month")
                if len(suggestion.vendors) > 5:
                    print(f"    └── [{len(suggestion.vendors)-5} more vendors...]")
                print(f"    → Combined: ${suggestion.total_monthly_amount:,.0f}/month")
                print(f"    → Decision: ✅ Group as \"{suggestion.display_name}\" | Keep Separate | Custom Name: _____")
                print()
        
        # Low confidence / optional groupings
        if suggestions['low_confidence']:
            print(f"\n🤔 Consider Grouping (Optional)")
            for suggestion in suggestions['low_confidence']:
                print(f"├── {suggestion.display_name} ({len(suggestion.vendors)} vendors under ${suggestion.total_monthly_amount:,.0f}/month total)")

def main():
    """Test the smart vendor grouping"""
    grouping = SmartVendorGrouping()
    
    print("🔍 SMART VENDOR GROUPING TEST")
    print("=" * 80)
    
    # Analyze vendor groupings
    suggestions = grouping.analyze_and_suggest_groupings('spyguy')
    
    # Print formatted suggestions
    grouping.print_grouping_suggestions(suggestions)
    
    # Summary stats
    total_groups = sum(len(groups) for groups in suggestions.values())
    total_vendors = sum(len(suggestion.vendors) for groups in suggestions.values() for suggestion in groups)
    total_monthly = sum(suggestion.total_monthly_amount for groups in suggestions.values() for suggestion in groups)
    
    print(f"\n📊 SUMMARY")
    print(f"Suggested {total_groups} business groups covering {total_vendors} vendors")
    print(f"Total monthly amount: ${total_monthly:,.0f}")
    print(f"Ready for Phase 2: Business Entity Analysis")
    
    return suggestions

if __name__ == "__main__":
    main()