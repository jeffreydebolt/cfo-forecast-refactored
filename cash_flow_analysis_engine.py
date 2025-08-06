#!/usr/bin/env python3
"""
Cash Flow Forecasting Analysis Engine
Analyzes transaction patterns and presents findings for manual review and decision-making
"""

import sys
sys.path.append('.')

from supabase_client import supabase
from datetime import datetime, date, timedelta
from collections import defaultdict, Counter
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Tuple
import re
import statistics
import json

@dataclass
class PatternAnalysis:
    """Results of pattern analysis for a vendor"""
    pattern_type: str  # daily, weekly, bi-weekly, monthly, quarterly, irregular, dual_schedule
    confidence: float  # 0.0 to 1.0
    frequency_days: Optional[int]  # Most common gap in days
    amount_pattern: str  # fixed, variable, trending_up, trending_down, seasonal
    average_amount: float
    amount_volatility: float  # std dev / mean
    transaction_count: int
    date_range: Tuple[str, str]  # first and last transaction dates
    details: Dict[str, Any]  # Additional pattern-specific details

@dataclass
class VendorAnalysis:
    """Complete analysis results for a vendor"""
    vendor_name: str
    display_name: str
    business_category: str  # revenue, inventory, credit_cards, people, recurring_services, tax_payments
    pattern_analysis: PatternAnalysis
    recommendation: str  # accept, modify, manual, skip
    reasoning: str  # Why this recommendation
    transactions: List[Dict]  # Raw transaction data

class CashFlowAnalysisEngine:
    """Main analysis engine for cash flow forecasting"""
    
    def __init__(self):
        # E-commerce business patterns
        self.vendor_patterns = {
            'revenue_channels': [
                r'shopify.*payment', r'amazon.*payment', r'amazon.*marketplace', r'stripe',
                r'paypal.*transfer', r'square', r'etsy', r'ebay', r'faire', r'wholesale'
            ],
            'inventory': [
                r'inventory.*transfer', r'supplier', r'manufacturer', r'wholesale.*purchase',
                r'alibaba', r'dhgate', r'bright.*ideas', r'supply.*chain'
            ],
            'credit_cards': [
                r'chase.*credit', r'american.*express', r'amex', r'capital.*one', r'visa', 
                r'mastercard', r'discover', r'credit.*card'
            ],
            'people': [
                r'gusto', r'adp', r'payroll', r'owner.*pay', r'salary', r'wages',
                r'contractor', r'freelance'
            ],
            'recurring_services': [
                r'quickbooks', r'shopify.*subscription', r'amazon.*aws', r'google.*ads',
                r'facebook.*ads', r'software', r'saas', r'subscription'
            ],
            'tax_payments': [
                r'sales.*tax', r'state.*tax', r'irs', r'revenue', r'dept.*tax',
                r'michigan.*tax', r'ohio.*tax', r'florida.*tax'
            ],
            'financial_services': [
                r'wire.*fee', r'bank.*fee', r'wise', r'transfer.*fee', r'jpmorgan.*chase'
            ]
        }
    
    def analyze_client_patterns(self, client_id: str) -> Dict[str, VendorAnalysis]:
        """Main entry point - analyze all patterns for a client"""
        print(f"🔍 CASH FLOW ANALYSIS ENGINE")
        print(f"Client: {client_id}")
        print("=" * 80)
        
        # Step 1: Get all transactions
        transactions = self._get_client_transactions(client_id)
        print(f"📊 Analyzing {len(transactions)} transactions")
        
        # Step 2: Group and normalize vendor names
        vendor_groups = self._group_and_normalize_vendors(transactions)
        print(f"🏢 Found {len(vendor_groups)} vendor groups")
        
        # Step 3: Analyze each vendor group
        vendor_analyses = {}
        for display_name, vendor_data in vendor_groups.items():
            print(f"\n📈 Analyzing: {display_name}")
            analysis = self._analyze_vendor_group(display_name, vendor_data)
            vendor_analyses[display_name] = analysis
            
            # Print summary
            pattern = analysis.pattern_analysis
            print(f"  Category: {analysis.business_category}")
            print(f"  Pattern: {pattern.pattern_type} ({pattern.confidence:.0%} confidence)")
            print(f"  Amount: ${pattern.average_amount:,.2f} avg, {pattern.amount_pattern}")
            print(f"  Recommendation: {analysis.recommendation} - {analysis.reasoning}")
        
        return vendor_analyses
    
    def _get_client_transactions(self, client_id: str) -> List[Dict]:
        """Get all transactions for a client"""
        # Note: BestSelf data is stored under 'spyguy' client_id
        actual_client_id = 'spyguy' if client_id == 'bestself' else client_id
        
        result = supabase.table('transactions').select('*').eq('client_id', actual_client_id).execute()
        
        # Sort by date for pattern analysis
        transactions = sorted(result.data, key=lambda x: x['transaction_date'])
        return transactions
    
    def _group_and_normalize_vendors(self, transactions: List[Dict]) -> Dict[str, Dict]:
        """Group transactions by normalized vendor names using regex patterns"""
        
        # First, get existing vendor mappings
        vendor_mappings = {}
        if transactions:
            client_id = transactions[0]['client_id']
            result = supabase.table('vendors').select('vendor_name, display_name').eq('client_id', client_id).execute()
            vendor_mappings = {v['vendor_name']: v['display_name'] for v in result.data if v.get('display_name')}
        
        # Group transactions by vendor name
        raw_groups = defaultdict(list)
        for txn in transactions:
            vendor_name = txn.get('vendor_name', 'Unknown')
            raw_groups[vendor_name].append(txn)
        
        # Apply smart grouping using regex patterns and existing mappings
        normalized_groups = {}
        processed_vendors = set()
        
        for vendor_name, txns in raw_groups.items():
            if vendor_name in processed_vendors:
                continue
            
            # Use existing mapping if available
            if vendor_name in vendor_mappings:
                display_name = vendor_mappings[vendor_name]
            else:
                # Apply smart normalization
                display_name = self._normalize_vendor_name(vendor_name)
            
            # Group similar vendors together
            if display_name not in normalized_groups:
                normalized_groups[display_name] = {
                    'transactions': [],
                    'vendor_names': [],
                    'business_category': self._classify_business_category(display_name, vendor_name)
                }
            
            normalized_groups[display_name]['transactions'].extend(txns)
            normalized_groups[display_name]['vendor_names'].append(vendor_name)
            processed_vendors.add(vendor_name)
        
        return normalized_groups
    
    def _normalize_vendor_name(self, vendor_name: str) -> str:
        """Normalize vendor name using business logic"""
        name_lower = vendor_name.lower()
        
        # E-commerce revenue channels
        if any(re.search(pattern, name_lower) for pattern in self.vendor_patterns['revenue_channels']):
            if 'shopify' in name_lower:
                return 'Shopify Revenue'
            elif 'amazon' in name_lower:
                return 'Amazon Revenue'
            elif 'stripe' in name_lower:
                return 'Stripe Revenue'
            elif 'paypal' in name_lower:
                return 'PayPal Revenue'
            else:
                return 'Other Revenue'
        
        # Credit cards
        if any(re.search(pattern, name_lower) for pattern in self.vendor_patterns['credit_cards']):
            if 'chase' in name_lower:
                return 'Chase Credit Card'
            elif 'amex' in name_lower or 'american express' in name_lower:
                return 'American Express'
            elif 'capital one' in name_lower:
                return 'Capital One'
            else:
                return 'Credit Card Payment'
        
        # People costs
        if any(re.search(pattern, name_lower) for pattern in self.vendor_patterns['people']):
            if 'gusto' in name_lower:
                return 'Gusto Payroll'
            elif 'owner' in name_lower:
                return 'Owner Pay'
            else:
                return 'Payroll'
        
        # Tax payments
        if any(re.search(pattern, name_lower) for pattern in self.vendor_patterns['tax_payments']):
            return 'Sales Tax'
        
        # Financial services
        if any(re.search(pattern, name_lower) for pattern in self.vendor_patterns['financial_services']):
            if 'wise' in name_lower:
                return 'Wise Transfers'
            elif 'jpmorgan' in name_lower or 'chase' in name_lower:
                return 'Chase Bank'
            else:
                return 'Financial Services'
        
        # Inventory
        if any(re.search(pattern, name_lower) for pattern in self.vendor_patterns['inventory']):
            return 'Inventory/Suppliers'
        
        # Internal transfers
        if 'sge' in name_lower or 'mercury' in name_lower:
            if 'income' in name_lower:
                return 'Internal Revenue'
            elif 'inventory' in name_lower:
                return 'Inventory Transfers'
            elif 'opex' in name_lower:
                return 'OpEx Transfers'
            else:
                return 'Internal Transfers'
        
        # Default: clean up the name
        return self._clean_vendor_name(vendor_name)
    
    def _clean_vendor_name(self, vendor_name: str) -> str:
        """Clean up vendor name for display"""
        # Remove common prefixes/suffixes and clean up
        name = re.sub(r'^(CHECK\s+|ACH\s+|DEBIT\s+|CREDIT\s+)', '', vendor_name, flags=re.IGNORECASE)
        name = re.sub(r'\s*(PAYMENT|PYMT|TRANSFER|TRNSFR)\s*$', '', name, flags=re.IGNORECASE)
        name = re.sub(r'\s+', ' ', name).strip()
        
        return name.title() if name else vendor_name
    
    def _classify_business_category(self, display_name: str, vendor_name: str) -> str:
        """Classify vendor into business category"""
        name_lower = (display_name + ' ' + vendor_name).lower()
        
        for category, patterns in self.vendor_patterns.items():
            if any(re.search(pattern, name_lower) for pattern in patterns):
                return category
        
        return 'other'
    
    def _analyze_vendor_group(self, display_name: str, vendor_data: Dict) -> VendorAnalysis:
        """Analyze patterns for a single vendor group"""
        transactions = vendor_data['transactions']
        business_category = vendor_data['business_category']
        
        if len(transactions) < 2:
            # Not enough data for pattern analysis
            pattern = PatternAnalysis(
                pattern_type='insufficient_data',
                confidence=0.0,
                frequency_days=None,
                amount_pattern='unknown',
                average_amount=transactions[0]['amount'] if transactions else 0,
                amount_volatility=0.0,
                transaction_count=len(transactions),
                date_range=(transactions[0]['transaction_date'], transactions[0]['transaction_date']) if transactions else ('', ''),
                details={}
            )
            
            return VendorAnalysis(
                vendor_name=vendor_data['vendor_names'][0],
                display_name=display_name,
                business_category=business_category,
                pattern_analysis=pattern,
                recommendation='skip',
                reasoning='Insufficient transaction history',
                transactions=transactions
            )
        
        # Analyze timing patterns
        timing_analysis = self._analyze_timing_patterns(transactions)
        
        # Analyze amount patterns
        amount_analysis = self._analyze_amount_patterns(transactions)
        
        # Create pattern analysis
        pattern = PatternAnalysis(
            pattern_type=timing_analysis['pattern_type'],
            confidence=timing_analysis['confidence'],
            frequency_days=timing_analysis['frequency_days'],
            amount_pattern=amount_analysis['pattern_type'],
            average_amount=amount_analysis['average'],
            amount_volatility=amount_analysis['volatility'],
            transaction_count=len(transactions),
            date_range=(transactions[0]['transaction_date'], transactions[-1]['transaction_date']),
            details={
                'timing_details': timing_analysis,
                'amount_details': amount_analysis
            }
        )
        
        # Generate recommendation
        recommendation, reasoning = self._generate_recommendation(pattern, business_category, display_name)
        
        return VendorAnalysis(
            vendor_name=vendor_data['vendor_names'][0],
            display_name=display_name,
            business_category=business_category,
            pattern_analysis=pattern,
            recommendation=recommendation,
            reasoning=reasoning,
            transactions=transactions
        )
    
    def _analyze_timing_patterns(self, transactions: List[Dict]) -> Dict[str, Any]:
        """Analyze timing patterns in transactions"""
        if len(transactions) < 2:
            return {'pattern_type': 'insufficient_data', 'confidence': 0.0, 'frequency_days': None}
        
        # Calculate gaps between consecutive transactions
        gaps = []
        dates = []
        
        for i in range(1, len(transactions)):
            prev_date = datetime.fromisoformat(transactions[i-1]['transaction_date']).date()
            curr_date = datetime.fromisoformat(transactions[i]['transaction_date']).date()
            gap_days = (curr_date - prev_date).days
            gaps.append(gap_days)
            dates.append(curr_date)
        
        if not gaps:
            return {'pattern_type': 'insufficient_data', 'confidence': 0.0, 'frequency_days': None}
        
        # Analyze gap distribution
        gap_counter = Counter(gaps)
        most_common_gaps = gap_counter.most_common(3)
        
        # Check for daily transactions (group to weekly for analysis)
        if len(gaps) > 10 and statistics.median(gaps) <= 3:
            return self._analyze_daily_patterns(transactions)
        
        # Check for regular patterns
        total_gaps = len(gaps)
        if total_gaps < 3:
            return {'pattern_type': 'irregular', 'confidence': 0.0, 'frequency_days': None}
        
        most_common_gap, frequency = most_common_gaps[0]
        confidence = frequency / total_gaps
        
        # Classify pattern type
        if confidence >= 0.7:  # Strong pattern
            if most_common_gap <= 1:
                pattern_type = 'daily'
            elif 6 <= most_common_gap <= 8:
                pattern_type = 'weekly'
            elif 13 <= most_common_gap <= 16:
                pattern_type = 'bi-weekly'
            elif 28 <= most_common_gap <= 35:
                pattern_type = 'monthly'
            elif 85 <= most_common_gap <= 95:
                pattern_type = 'quarterly'
            else:
                pattern_type = 'custom_interval'
        elif confidence >= 0.4:  # Moderate pattern
            # Check for dual schedule patterns
            if len(most_common_gaps) >= 2:
                gap1, freq1 = most_common_gaps[0]
                gap2, freq2 = most_common_gaps[1]
                if freq1 + freq2 >= 0.6 * total_gaps:
                    pattern_type = 'dual_schedule'
                    confidence = (freq1 + freq2) / total_gaps
                else:
                    pattern_type = 'irregular'
            else:
                pattern_type = 'irregular'
        else:
            pattern_type = 'irregular'
        
        return {
            'pattern_type': pattern_type,
            'confidence': confidence,
            'frequency_days': most_common_gap,
            'gap_distribution': dict(gap_counter),
            'dual_schedule_gaps': [gap for gap, _ in most_common_gaps[:2]] if pattern_type == 'dual_schedule' else None
        }
    
    def _analyze_daily_patterns(self, transactions: List[Dict]) -> Dict[str, Any]:
        """Analyze daily transaction patterns by grouping to weekly"""
        # Group transactions by week
        weekly_groups = defaultdict(list)
        
        for txn in transactions:
            txn_date = datetime.fromisoformat(txn['transaction_date']).date()
            week_start = txn_date - timedelta(days=txn_date.weekday())  # Monday of the week
            weekly_groups[week_start].append(txn)
        
        if len(weekly_groups) < 3:
            return {'pattern_type': 'irregular', 'confidence': 0.0, 'frequency_days': None}
        
        # Check consistency of weekly activity
        weeks_with_activity = len(weekly_groups)
        total_weeks_in_range = len(weekly_groups)  # Simplified
        
        confidence = min(0.9, weeks_with_activity / max(total_weeks_in_range, 1))
        
        return {
            'pattern_type': 'daily',
            'confidence': confidence,
            'frequency_days': 1,
            'weekly_groups': len(weekly_groups),
            'transactions_per_week': len(transactions) / len(weekly_groups)
        }
    
    def _analyze_amount_patterns(self, transactions: List[Dict]) -> Dict[str, Any]:
        """Analyze amount patterns in transactions"""
        amounts = [float(txn['amount']) for txn in transactions]
        
        if not amounts:
            return {'pattern_type': 'unknown', 'average': 0, 'volatility': 0}
        
        avg_amount = statistics.mean(amounts)
        
        if len(amounts) == 1:
            return {'pattern_type': 'single', 'average': avg_amount, 'volatility': 0}
        
        std_dev = statistics.stdev(amounts)
        volatility = std_dev / abs(avg_amount) if avg_amount != 0 else 0
        
        # Classify amount pattern
        if volatility < 0.1:
            pattern_type = 'fixed'
        elif volatility < 0.3:
            pattern_type = 'low_variance'
        elif volatility < 0.6:
            pattern_type = 'moderate_variance'
        else:
            pattern_type = 'high_variance'
        
        # Check for trending
        if len(amounts) >= 5:
            # Simple trend analysis using first half vs second half
            mid = len(amounts) // 2
            first_half_avg = statistics.mean(amounts[:mid])
            second_half_avg = statistics.mean(amounts[mid:])
            
            if second_half_avg > first_half_avg * 1.2:
                pattern_type = 'trending_up'
            elif second_half_avg < first_half_avg * 0.8:
                pattern_type = 'trending_down'
        
        return {
            'pattern_type': pattern_type,
            'average': avg_amount,
            'volatility': volatility,
            'std_dev': std_dev,
            'min_amount': min(amounts),
            'max_amount': max(amounts),
            'median_amount': statistics.median(amounts)
        }
    
    def _generate_recommendation(self, pattern: PatternAnalysis, business_category: str, display_name: str) -> Tuple[str, str]:
        """Generate recommendation and reasoning for a vendor"""
        
        # Business logic filters
        if pattern.transaction_count < 3:
            return 'skip', 'Too few transactions for reliable forecasting'
        
        if business_category == 'tax_payments' and pattern.confidence < 0.5:
            return 'manual', 'Tax payments are irregular but important - set manual schedule'
        
        if business_category == 'revenue_channels':
            if pattern.confidence >= 0.7:
                return 'accept', f'Strong {pattern.pattern_type} revenue pattern - reliable for forecasting'
            elif pattern.confidence >= 0.4:
                return 'modify', f'Moderate revenue pattern - may need timing adjustments'
            else:
                return 'manual', 'Irregular revenue - set conservative estimates'
        
        if business_category == 'credit_cards':
            if pattern.confidence >= 0.6:
                return 'accept', f'Regular {pattern.pattern_type} credit card payments'
            else:
                return 'modify', 'Credit card payments vary - consider average monthly amount'
        
        if business_category == 'people':
            if 'payroll' in display_name.lower() or 'gusto' in display_name.lower():
                return 'accept', 'Payroll should be regular - accept or verify schedule'
            else:
                return 'manual', 'People costs need business context'
        
        # General pattern-based recommendations
        if pattern.confidence >= 0.8:
            return 'accept', f'Very reliable {pattern.pattern_type} pattern'
        elif pattern.confidence >= 0.6:
            return 'modify', f'Good {pattern.pattern_type} pattern but may need adjustments'
        elif pattern.confidence >= 0.3:
            return 'manual', f'Weak pattern detected - consider manual forecasting'
        else:
            return 'skip', 'No reliable pattern - one-off or too irregular'

def main():
    """Test the analysis engine"""
    engine = CashFlowAnalysisEngine()
    
    print("🚀 CASH FLOW ANALYSIS ENGINE TEST")
    print("=" * 80)
    
    # Analyze BestSelf patterns
    analyses = engine.analyze_client_patterns('bestself')
    
    # Summary
    print(f"\n📋 ANALYSIS SUMMARY")
    print("=" * 80)
    
    categories = defaultdict(list)
    recommendations = defaultdict(list)
    
    for display_name, analysis in analyses.items():
        categories[analysis.business_category].append(display_name)
        recommendations[analysis.recommendation].append(display_name)
    
    print(f"🏢 Business Categories:")
    for category, vendors in categories.items():
        print(f"  {category}: {len(vendors)} vendors")
    
    print(f"\n💡 Recommendations:")
    for rec, vendors in recommendations.items():
        print(f"  {rec}: {len(vendors)} vendors")
    
    return analyses

if __name__ == "__main__":
    main()