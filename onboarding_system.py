#!/usr/bin/env python3
"""
Cash Flow Forecasting System: Onboarding-Focused Approach
Replicates proven manual onboarding process for speed and accuracy
"""

import sys
sys.path.append('.')

from supabase_client import supabase
from datetime import datetime, date, timedelta
from collections import defaultdict, Counter
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import re
import statistics

@dataclass
class VendorActivity:
    """Basic vendor activity analysis"""
    vendor_name: str
    transaction_count: int
    total_volume: float
    first_transaction: date
    last_transaction: date
    is_regular: bool  # 2+ transactions in 12 months
    monthly_frequency: float

@dataclass
class GroupingSuggestion:
    """Vendor name grouping suggestion"""
    suggested_name: str
    vendor_variants: List[str]
    confidence: str  # high, medium, low
    reasoning: str
    total_transactions: int
    combined_volume: float

class OnboardingSystem:
    """Main onboarding system for new client setup"""
    
    def __init__(self):
        # Generic name normalization patterns (no business logic)
        self.name_patterns = {
            'remove_numbers': r'[0-9]+',
            'remove_special': r'[#*\-_]+',
            'common_suffixes': r'\s+(inc|llc|corp|ltd|co)\.?$',
            'payment_indicators': r'\s+(payment|pymt|transfer|trnsfr|payout)s?$'
        }
    
    def onboard_new_client(self, client_id: str) -> Dict[str, any]:
        """Complete onboarding process for a new client"""
        print(f"🚀 ONBOARDING NEW CLIENT: {client_id}")
        print("=" * 80)
        
        results = {}
        
        # Phase 1: Transaction Import & Analysis
        print("\n📊 PHASE 1: Transaction Import & Analysis")
        results['phase1'] = self.analyze_transaction_regularity(client_id)
        
        # Phase 2: Vendor Mapping & Grouping
        print("\n🗂️ PHASE 2: Vendor Mapping & Grouping") 
        results['phase2'] = self.suggest_vendor_groupings(results['phase1']['regular_vendors'])
        
        return results
    
    def analyze_transaction_regularity(self, client_id: str) -> Dict[str, any]:
        """Phase 1: Find vendors with regular activity worth forecasting"""
        
        # Get all transactions for client
        result = supabase.table('transactions').select('*').eq('client_id', client_id).execute()
        transactions = result.data
        
        print(f"📥 Imported {len(transactions)} transactions")
        
        # Group by vendor name
        vendor_data = defaultdict(list)
        for txn in transactions:
            vendor_name = txn['vendor_name']
            vendor_data[vendor_name].append(txn)
        
        # Analyze each vendor for regularity
        regular_vendors = []
        one_time_vendors = []
        
        cutoff_date = date.today() - timedelta(days=365)  # 12 months ago
        
        for vendor_name, txns in vendor_data.items():
            # Sort by date
            txns.sort(key=lambda x: x['transaction_date'])
            
            # Calculate activity metrics
            transaction_count = len(txns)
            total_volume = sum(abs(float(txn['amount'])) for txn in txns)
            
            first_date = datetime.fromisoformat(txns[0]['transaction_date']).date()
            last_date = datetime.fromisoformat(txns[-1]['transaction_date']).date()
            
            # Check if regular (2+ transactions in 12 months)
            recent_txns = [txn for txn in txns 
                          if datetime.fromisoformat(txn['transaction_date']).date() >= cutoff_date]
            
            is_regular = len(recent_txns) >= 2
            
            # Calculate monthly frequency
            date_span = (last_date - first_date).days
            months_span = max(1, date_span / 30)
            monthly_frequency = transaction_count / months_span
            
            vendor_activity = VendorActivity(
                vendor_name=vendor_name,
                transaction_count=transaction_count,
                total_volume=total_volume,
                first_transaction=first_date,
                last_transaction=last_date,
                is_regular=is_regular,
                monthly_frequency=monthly_frequency
            )
            
            if is_regular:
                regular_vendors.append(vendor_activity)
            else:
                one_time_vendors.append(vendor_activity)
        
        # Sort by transaction count and volume
        regular_vendors.sort(key=lambda x: (x.transaction_count, x.total_volume), reverse=True)
        one_time_vendors.sort(key=lambda x: x.total_volume, reverse=True)
        
        print(f"✅ Found {len(regular_vendors)} vendors with regular activity")
        print(f"📝 Found {len(one_time_vendors)} one-time vendors")
        
        # Show top regular vendors
        print(f"\n🔍 Top Regular Vendors:")
        for vendor in regular_vendors[:10]:
            print(f"  {vendor.vendor_name}: {vendor.transaction_count} txns, ${vendor.total_volume:,.0f} volume")
        
        return {
            'regular_vendors': regular_vendors,
            'one_time_vendors': one_time_vendors,
            'total_transactions': len(transactions),
            'analysis_date': date.today().isoformat()
        }
    
    def suggest_vendor_groupings(self, regular_vendors: List[VendorActivity]) -> Dict[str, any]:
        """Phase 2: Suggest groupings for regular vendors using name similarity"""
        
        print(f"🔍 Analyzing {len(regular_vendors)} regular vendors for grouping opportunities")
        
        # Create vendor name variations map
        vendor_names = [v.vendor_name for v in regular_vendors]
        name_similarity_groups = self._find_similar_names(vendor_names)
        
        suggestions = []
        
        # Generate grouping suggestions
        for base_name, variants in name_similarity_groups.items():
            if len(variants) >= 2:  # Only suggest if 2+ variants
                
                # Get vendor data for these variants
                variant_vendors = [v for v in regular_vendors if v.vendor_name in variants]
                
                # Calculate combined metrics
                total_transactions = sum(v.transaction_count for v in variant_vendors)
                combined_volume = sum(v.total_volume for v in variant_vendors)
                
                # Determine confidence based on name similarity
                confidence = self._calculate_grouping_confidence(variants)
                reasoning = self._generate_grouping_reasoning(variants, base_name)
                
                suggestion = GroupingSuggestion(
                    suggested_name=self._clean_suggested_name(base_name, variants),
                    vendor_variants=variants,
                    confidence=confidence,
                    reasoning=reasoning,
                    total_transactions=total_transactions,
                    combined_volume=combined_volume
                )
                
                suggestions.append(suggestion)
        
        # Sort by combined volume (most important first)
        suggestions.sort(key=lambda x: x.combined_volume, reverse=True)
        
        # Organize by confidence
        high_confidence = [s for s in suggestions if s.confidence == 'high']
        medium_confidence = [s for s in suggestions if s.confidence == 'medium']
        low_confidence = [s for s in suggestions if s.confidence == 'low']
        
        print(f"\n📋 Grouping Suggestions Generated:")
        print(f"  High Confidence: {len(high_confidence)} groups")
        print(f"  Medium Confidence: {len(medium_confidence)} groups")
        print(f"  Low Confidence: {len(low_confidence)} groups")
        
        # Print examples
        if high_confidence:
            print(f"\n✅ High Confidence Examples:")
            for suggestion in high_confidence[:3]:
                print(f"  {suggestion.suggested_name} ({len(suggestion.vendor_variants)} variants)")
                for variant in suggestion.vendor_variants[:3]:
                    print(f"    - {variant}")
                if len(suggestion.vendor_variants) > 3:
                    print(f"    - [{len(suggestion.vendor_variants)-3} more...]")
        
        return {
            'high_confidence': high_confidence,
            'medium_confidence': medium_confidence, 
            'low_confidence': low_confidence,
            'total_suggestions': len(suggestions),
            'ungrouped_vendors': len(regular_vendors) - sum(len(s.vendor_variants) for s in suggestions)
        }
    
    def _find_similar_names(self, vendor_names: List[str]) -> Dict[str, List[str]]:
        """Find vendors with similar names that might be the same entity"""
        similarity_groups = defaultdict(list)
        
        for name in vendor_names:
            # Normalize name for comparison
            normalized = self._normalize_name_for_comparison(name)
            
            # Group by normalized name
            similarity_groups[normalized].append(name)
        
        # Only return groups with 2+ names
        return {k: v for k, v in similarity_groups.items() if len(v) >= 2}
    
    def _normalize_name_for_comparison(self, name: str) -> str:
        """Normalize vendor name for similarity comparison"""
        normalized = name.lower().strip()
        
        # Remove common patterns
        for pattern_name, pattern in self.name_patterns.items():
            normalized = re.sub(pattern, '', normalized, flags=re.IGNORECASE)
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def _calculate_grouping_confidence(self, variants: List[str]) -> str:
        """Calculate confidence level for grouping suggestion"""
        
        # Check for exact matches after normalization
        normalized_variants = [self._normalize_name_for_comparison(v) for v in variants]
        unique_normalized = set(normalized_variants)
        
        if len(unique_normalized) == 1:
            return 'high'  # All normalize to same name
        
        # Check for strong patterns (same core name with numbers/suffixes)
        base_names = []
        for variant in variants:
            # Remove numbers and common suffixes to find core name
            core = re.sub(r'[0-9\s\-_#*]+', '', variant.lower())
            core = re.sub(r'(inc|llc|corp|ltd|payment|pymt).*$', '', core)
            base_names.append(core)
        
        unique_bases = set(base_names)
        
        if len(unique_bases) == 1 and len(unique_bases.pop()) >= 3:
            return 'high'  # Same core name, at least 3 chars
        elif len(unique_bases) <= 2:
            return 'medium'  # Similar core names
        else:
            return 'low'  # Very different names
    
    def _generate_grouping_reasoning(self, variants: List[str], base_name: str) -> str:
        """Generate human-readable reasoning for grouping"""
        
        if len(variants) == 2:
            return f"Two similar vendor names detected"
        else:
            return f"{len(variants)} similar vendor names detected"
    
    def _clean_suggested_name(self, base_name: str, variants: List[str]) -> str:
        """Generate clean suggested name for the group"""
        
        # Find the shortest, cleanest variant
        cleaned_variants = []
        
        for variant in variants:
            # Remove numbers and extra chars, but keep readability
            cleaned = re.sub(r'\s*[0-9]+\s*', ' ', variant)
            cleaned = re.sub(r'[#*\-_]+', ' ', cleaned)
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()
            cleaned_variants.append((len(cleaned), cleaned))
        
        # Sort by length (shortest first) and take the cleanest
        cleaned_variants.sort()
        
        return cleaned_variants[0][1].title()

def main():
    """Test the onboarding system"""
    system = OnboardingSystem()
    
    print("🚀 CASH FLOW ONBOARDING SYSTEM TEST")
    print("=" * 80)
    
    # Run onboarding for test client
    results = system.onboard_new_client('spyguy')
    
    # Summary
    print(f"\n📊 ONBOARDING SUMMARY")
    print("=" * 80)
    
    phase1 = results['phase1']
    phase2 = results['phase2']
    
    print(f"📥 Total Transactions: {phase1['total_transactions']}")
    print(f"✅ Regular Vendors: {len(phase1['regular_vendors'])}")
    print(f"📝 One-time Vendors: {len(phase1['one_time_vendors'])}")
    print(f"📋 Grouping Suggestions: {phase2['total_suggestions']}")
    print(f"🔗 Ungrouped Vendors: {phase2['ungrouped_vendors']}")
    
    print(f"\n🎯 Next Steps:")
    print(f"1. Review {len(phase2['high_confidence'])} high-confidence groupings")
    print(f"2. Review {len(phase2['medium_confidence'])} medium-confidence groupings")
    print(f"3. Proceed to Phase 3: Pattern Detection & Cadence Analysis")
    
    return results

if __name__ == "__main__":
    main()