#!/usr/bin/env python3
"""
Pure Name-Based Grouping - NO BUSINESS LOGIC
Only groups vendors with similar names, no assumptions about what they do
"""

import sys
sys.path.append('.')

from supabase_client import supabase
from datetime import datetime, date
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Set
import re
from difflib import SequenceMatcher

@dataclass
class NameGroup:
    """Group of vendors with similar names"""
    base_name: str
    vendor_names: List[str]
    similarity_score: float
    total_transactions: int
    total_volume: float

class PureNameGrouping:
    """Groups vendors ONLY by name similarity - no business logic"""
    
    def __init__(self):
        # Only technical cleaning patterns - NO business terms
        self.technical_patterns = {
            'remove_numbers': r'\d+',
            'remove_punctuation': r'[^\w\s]',
            'normalize_whitespace': r'\s+'
        }
    
    def find_name_groups(self, client_id: str) -> List[NameGroup]:
        """Find vendors that might be the same entity based on name similarity"""
        print("🔍 PURE NAME GROUPING ANALYSIS")
        print("=" * 80)
        
        # Get all vendors
        result = supabase.table('transactions').select('vendor_name, amount').eq('client_id', client_id).execute()
        transactions = result.data
        
        # Count transactions per vendor
        vendor_stats = defaultdict(lambda: {'count': 0, 'total': 0})
        for txn in transactions:
            vendor_name = txn['vendor_name']
            vendor_stats[vendor_name]['count'] += 1
            vendor_stats[vendor_name]['total'] += abs(float(txn['amount']))
        
        vendor_names = list(vendor_stats.keys())
        print(f"📊 Analyzing {len(vendor_names)} unique vendor names")
        
        # Find similar names
        groups = self._cluster_similar_names(vendor_names)
        
        # Create NameGroup objects
        name_groups = []
        for base_name, similar_names in groups.items():
            if len(similar_names) >= 2:  # Only suggest groups with 2+ vendors
                total_txns = sum(vendor_stats[name]['count'] for name in similar_names)
                total_volume = sum(vendor_stats[name]['total'] for name in similar_names)
                
                # Calculate average similarity score
                scores = []
                for i in range(len(similar_names)):
                    for j in range(i+1, len(similar_names)):
                        score = self._name_similarity(similar_names[i], similar_names[j])
                        scores.append(score)
                avg_score = sum(scores) / len(scores) if scores else 0.0
                
                group = NameGroup(
                    base_name=base_name,
                    vendor_names=similar_names,
                    similarity_score=avg_score,
                    total_transactions=total_txns,
                    total_volume=total_volume
                )
                name_groups.append(group)
        
        # Sort by volume (most important first)
        name_groups.sort(key=lambda x: x.total_volume, reverse=True)
        
        print(f"\n✅ Found {len(name_groups)} potential groupings")
        return name_groups
    
    def _cluster_similar_names(self, vendor_names: List[str]) -> Dict[str, List[str]]:
        """Cluster vendors with similar names"""
        clusters = {}
        used = set()
        
        for i, name1 in enumerate(vendor_names):
            if name1 in used:
                continue
                
            # Start a new cluster
            cluster = [name1]
            used.add(name1)
            
            # Find all similar names
            for j, name2 in enumerate(vendor_names[i+1:], i+1):
                if name2 in used:
                    continue
                    
                similarity = self._name_similarity(name1, name2)
                if similarity >= 0.7:  # 70% similarity threshold
                    cluster.append(name2)
                    used.add(name2)
            
            if len(cluster) >= 2:
                # Use shortest name as base
                base_name = min(cluster, key=len)
                clusters[base_name] = cluster
        
        return clusters
    
    def _name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two names (0-1)"""
        # Basic normalization
        norm1 = self._normalize_for_comparison(name1)
        norm2 = self._normalize_for_comparison(name2)
        
        # If normalized names are identical
        if norm1 == norm2:
            return 1.0
        
        # Check if one is substring of other
        if norm1 in norm2 or norm2 in norm1:
            return 0.9
        
        # Use sequence matcher for fuzzy matching
        return SequenceMatcher(None, norm1, norm2).ratio()
    
    def _normalize_for_comparison(self, name: str) -> str:
        """Normalize name for comparison - NO business logic"""
        normalized = name.lower().strip()
        
        # Remove numbers
        normalized = re.sub(self.technical_patterns['remove_numbers'], '', normalized)
        
        # Remove punctuation
        normalized = re.sub(self.technical_patterns['remove_punctuation'], ' ', normalized)
        
        # Normalize whitespace
        normalized = re.sub(self.technical_patterns['normalize_whitespace'], ' ', normalized)
        
        return normalized.strip()
    
    def print_grouping_suggestions(self, groups: List[NameGroup]):
        """Print grouping suggestions"""
        print("\n📋 NAME-BASED GROUPING SUGGESTIONS")
        print("(No business assumptions - only name similarity)")
        print("=" * 80)
        
        for i, group in enumerate(groups):
            print(f"\n🔗 Group {i+1}: {group.base_name}")
            print(f"   Similarity: {group.similarity_score:.1%}")
            print(f"   Combined: {group.total_transactions} transactions, ${group.total_volume:,.0f}")
            print("   Vendors:")
            for vendor in group.vendor_names:
                print(f"   - {vendor}")

def main():
    """Test pure name grouping"""
    grouper = PureNameGrouping()
    
    # Find name groups
    groups = grouper.find_name_groups('spyguy')
    
    # Print suggestions
    grouper.print_grouping_suggestions(groups)
    
    print("\n🎯 These are ONLY name-based suggestions")
    print("Users must decide if these represent the same business entity")

if __name__ == "__main__":
    main()