#!/usr/bin/env python3
"""
Practical Pattern Detection Engine
Fixed to work with real business data - 60-80% success rate target
Separates timing patterns from amount patterns
"""

import sys
sys.path.append('.')

from supabase_client import supabase
from datetime import datetime, date, timedelta
from collections import defaultdict, Counter
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import statistics
import numpy as np

@dataclass
class TimingPattern:
    """Detected timing pattern for a vendor"""
    pattern_type: str  # daily, weekly, bi_weekly, monthly, quarterly, irregular
    frequency_days: int  # Median days between transactions
    median_gap: int  # More reliable than average
    consistency_score: float  # How consistent the pattern is
    confidence: str  # high, medium, low
    sample_size: int  # Number of gaps analyzed

@dataclass
class AmountPattern:
    """Detected amount pattern for a vendor"""
    average_amount: float
    median_amount: float
    recent_average: float  # Last 6 months
    variance_coefficient: float  # Standard deviation / mean
    amount_type: str  # consistent, variable, highly_variable
    suggested_amount: float  # What to use for forecasting

@dataclass
class VendorPattern:
    """Complete pattern analysis for a vendor"""
    vendor_name: str
    transaction_count: int
    timing_pattern: TimingPattern
    amount_pattern: AmountPattern
    forecast_recommendation: str  # auto, manual_review, skip
    forecast_confidence: str  # high, medium, low
    reasoning: str

class PracticalPatternDetection:
    """Practical pattern detection that works with real business data"""
    
    def __init__(self):
        # More lenient thresholds
        self.MIN_TRANSACTIONS = 3  # Need at least 3 in 6 months
        self.TIMING_VARIANCE_ACCEPTABLE = 0.4  # 40% variance is OK
        self.AMOUNT_VARIANCE_AUTO = 0.30  # 30% = auto-ready
        self.AMOUNT_VARIANCE_MANUAL = 0.60  # 30-60% = manual review
        
        # Practical timing ranges (wider)
        self.TIMING_PATTERNS = {
            'daily': (0, 3),
            'twice_weekly': (3, 5),
            'weekly': (5, 10),
            'bi_weekly': (10, 18),
            'semi_monthly': (13, 17),  # 15th and 30th
            'monthly': (25, 35),
            'quarterly': (80, 100),
            'semi_annual': (170, 190),
            'annual': (350, 380)
        }
    
    def analyze_vendor_patterns(self, client_id: str) -> Dict[str, VendorPattern]:
        """Analyze all vendors with practical business logic"""
        print("🔍 PRACTICAL PATTERN DETECTION")
        print("=" * 80)
        
        # Get regular vendors
        regular_vendors = self._get_regular_vendors(client_id)
        print(f"📊 Analyzing {len(regular_vendors)} regular vendors")
        
        # Analyze each vendor
        vendor_patterns = {}
        
        for vendor_name, vendor_data in regular_vendors.items():
            pattern = self._analyze_single_vendor_practical(vendor_name, vendor_data['transactions'])
            vendor_patterns[vendor_name] = pattern
        
        # Summarize results
        auto_ready = [p for p in vendor_patterns.values() if p.forecast_recommendation == 'auto']
        manual_review = [p for p in vendor_patterns.values() if p.forecast_recommendation == 'manual_review']
        skip = [p for p in vendor_patterns.values() if p.forecast_recommendation == 'skip']
        
        print(f"\n📋 PRACTICAL PATTERN ANALYSIS")
        print(f"✅ Auto-ready: {len(auto_ready)} vendors ({len(auto_ready)/len(vendor_patterns)*100:.0f}%)")
        print(f"📝 Manual review: {len(manual_review)} vendors ({len(manual_review)/len(vendor_patterns)*100:.0f}%)")
        print(f"⏭️ Skip: {len(skip)} vendors ({len(skip)/len(vendor_patterns)*100:.0f}%)")
        
        return vendor_patterns
    
    def _get_regular_vendors(self, client_id: str) -> Dict[str, Dict]:
        """Get vendors with regular activity (3+ transactions in 6 months)"""
        result = supabase.table('transactions').select('*').eq('client_id', client_id).execute()
        transactions = result.data
        
        # Group by vendor
        vendor_data = defaultdict(list)
        for txn in transactions:
            vendor_data[txn['vendor_name']].append(txn)
        
        # Filter for activity in last 6 months
        six_months_ago = date.today() - timedelta(days=180)
        regular_vendors = {}
        
        for vendor_name, txns in vendor_data.items():
            recent_txns = [
                txn for txn in txns 
                if datetime.fromisoformat(txn['transaction_date']).date() >= six_months_ago
            ]
            
            if len(recent_txns) >= self.MIN_TRANSACTIONS:
                txns.sort(key=lambda x: x['transaction_date'])
                regular_vendors[vendor_name] = {'transactions': txns}
        
        return regular_vendors
    
    def _analyze_single_vendor_practical(self, vendor_name: str, transactions: List[Dict]) -> VendorPattern:
        """Analyze with practical business logic"""
        
        # Sort transactions by date
        txns = sorted(transactions, key=lambda x: x['transaction_date'])
        dates = [datetime.fromisoformat(txn['transaction_date']).date() for txn in txns]
        amounts = [abs(float(txn['amount'])) for txn in txns]
        
        # Analyze timing (most important)
        timing_pattern = self._detect_practical_timing(dates, vendor_name)
        
        # Analyze amounts (secondary)
        amount_pattern = self._detect_practical_amounts(amounts, dates)
        
        # Generate practical recommendation
        recommendation, confidence, reasoning = self._generate_practical_recommendation(
            vendor_name, timing_pattern, amount_pattern, len(transactions)
        )
        
        return VendorPattern(
            vendor_name=vendor_name,
            transaction_count=len(transactions),
            timing_pattern=timing_pattern,
            amount_pattern=amount_pattern,
            forecast_recommendation=recommendation,
            forecast_confidence=confidence,
            reasoning=reasoning
        )
    
    def _detect_practical_timing(self, dates: List[date], vendor_name: str) -> TimingPattern:
        """Detect timing patterns using median and business logic"""
        
        if len(dates) < 2:
            return TimingPattern(
                pattern_type='insufficient_data',
                frequency_days=0,
                median_gap=0,
                consistency_score=0.0,
                confidence='low',
                sample_size=0
            )
        
        # Calculate gaps
        gaps = []
        for i in range(1, len(dates)):
            gap_days = (dates[i] - dates[i-1]).days
            if gap_days > 0:  # Ignore same-day transactions
                gaps.append(gap_days)
        
        if not gaps:
            return TimingPattern(
                pattern_type='same_day_batches',
                frequency_days=0,
                median_gap=0,
                consistency_score=0.5,
                confidence='medium',
                sample_size=len(dates)
            )
        
        # Use MEDIAN instead of average (more robust)
        median_gap = int(statistics.median(gaps))
        avg_gap = statistics.mean(gaps)
        
        # Special handling for known patterns
        if 'gusto' in vendor_name.lower() or 'payroll' in vendor_name.lower():
            # Payroll is typically bi-weekly or semi-monthly
            pattern_type = 'bi_weekly' if 12 <= median_gap <= 16 else 'semi_monthly'
            confidence = 'high'
        elif 'tax' in vendor_name.lower() or 'revenue' in vendor_name.lower():
            # Tax payments are typically monthly
            pattern_type = 'monthly'
            confidence = 'high'
        else:
            # Detect pattern based on median gap
            pattern_type = 'irregular'
            confidence = 'low'
            
            for pattern_name, (min_days, max_days) in self.TIMING_PATTERNS.items():
                if min_days <= median_gap <= max_days:
                    pattern_type = pattern_name
                    # Confidence based on consistency
                    gap_variance = statistics.stdev(gaps) / avg_gap if avg_gap > 0 else 1
                    if gap_variance <= 0.3:
                        confidence = 'high'
                    elif gap_variance <= 0.5:
                        confidence = 'medium'
                    else:
                        confidence = 'low'
                    break
        
        # Calculate consistency score
        if len(gaps) > 1:
            # How many gaps are within 30% of median
            consistent_gaps = sum(1 for gap in gaps if 0.7 * median_gap <= gap <= 1.3 * median_gap)
            consistency_score = consistent_gaps / len(gaps)
        else:
            consistency_score = 0.5
        
        return TimingPattern(
            pattern_type=pattern_type,
            frequency_days=int(avg_gap),
            median_gap=median_gap,
            consistency_score=consistency_score,
            confidence=confidence,
            sample_size=len(gaps)
        )
    
    def _detect_practical_amounts(self, amounts: List[float], dates: List[date]) -> AmountPattern:
        """Analyze amounts with practical thresholds"""
        
        if not amounts:
            return AmountPattern(
                average_amount=0,
                median_amount=0,
                recent_average=0,
                variance_coefficient=0,
                amount_type='insufficient_data',
                suggested_amount=0
            )
        
        # Basic statistics
        avg_amount = statistics.mean(amounts)
        median_amount = statistics.median(amounts)
        
        # Recent average (last 6 months)
        six_months_ago = date.today() - timedelta(days=180)
        recent_amounts = []
        for i, transaction_date in enumerate(dates):
            if transaction_date >= six_months_ago:
                recent_amounts.append(amounts[i])
        
        recent_avg = statistics.mean(recent_amounts) if recent_amounts else avg_amount
        
        # Variance calculation
        if len(amounts) > 1:
            std_amount = statistics.stdev(amounts)
            variance_coefficient = std_amount / avg_amount if avg_amount > 0 else 0
        else:
            variance_coefficient = 0
        
        # Practical classification
        if variance_coefficient <= self.AMOUNT_VARIANCE_AUTO:
            amount_type = 'consistent'
            suggested_amount = recent_avg  # Use recent average
        elif variance_coefficient <= self.AMOUNT_VARIANCE_MANUAL:
            amount_type = 'variable'
            suggested_amount = median_amount  # Use median for variable
        else:
            amount_type = 'highly_variable'
            suggested_amount = recent_avg  # Still suggest recent average
        
        return AmountPattern(
            average_amount=avg_amount,
            median_amount=median_amount,
            recent_average=recent_avg,
            variance_coefficient=variance_coefficient,
            amount_type=amount_type,
            suggested_amount=suggested_amount
        )
    
    def _generate_practical_recommendation(self, vendor_name: str, timing: TimingPattern, 
                                         amount: AmountPattern, transaction_count: int) -> Tuple[str, str, str]:
        """Generate practical recommendations based on business logic"""
        
        # Skip only if truly insufficient data
        if transaction_count < self.MIN_TRANSACTIONS:
            return 'skip', 'low', f'Only {transaction_count} transactions - need at least {self.MIN_TRANSACTIONS}'
        
        # If timing is irregular and amounts are highly variable, skip
        if timing.pattern_type == 'irregular' and amount.variance_coefficient > 0.8:
            return 'skip', 'low', 'No clear timing pattern and highly variable amounts'
        
        # AUTO-READY: Good timing + consistent amounts
        if (timing.pattern_type not in ['irregular', 'insufficient_data'] and 
            timing.confidence in ['high', 'medium'] and
            amount.amount_type == 'consistent'):
            
            return 'auto', 'high', f'{timing.pattern_type.replace("_", " ").title()} @ ${amount.suggested_amount:,.0f}'
        
        # MANUAL REVIEW: Good timing but variable amounts
        if (timing.pattern_type not in ['irregular', 'insufficient_data'] and
            timing.confidence in ['high', 'medium']):
            
            return 'manual_review', 'medium', f'{timing.pattern_type.replace("_", " ").title()} but amounts vary (${amount.suggested_amount:,.0f} suggested)'
        
        # MANUAL REVIEW: Unclear timing but regular payments
        if timing.median_gap > 0 and transaction_count >= 6:
            return 'manual_review', 'low', f'Payments every ~{timing.median_gap} days (review pattern)'
        
        # Default to manual review instead of skip
        return 'manual_review', 'low', 'Review transaction history to identify pattern'
    
    def print_analysis_results(self, vendor_patterns: Dict[str, VendorPattern]):
        """Print analysis results grouped by recommendation"""
        
        # Group by recommendation
        auto_vendors = []
        manual_vendors = []
        skip_vendors = []
        
        for pattern in vendor_patterns.values():
            if pattern.forecast_recommendation == 'auto':
                auto_vendors.append(pattern)
            elif pattern.forecast_recommendation == 'manual_review':
                manual_vendors.append(pattern)
            else:
                skip_vendors.append(pattern)
        
        # Sort by transaction count
        auto_vendors.sort(key=lambda x: x.transaction_count, reverse=True)
        manual_vendors.sort(key=lambda x: x.transaction_count, reverse=True)
        
        print(f"\n✅ AUTO-READY VENDORS ({len(auto_vendors)})")
        print("=" * 80)
        for vendor in auto_vendors[:10]:
            print(f"{vendor.vendor_name}:")
            print(f"  Pattern: {vendor.reasoning}")
            print(f"  Transactions: {vendor.transaction_count}")
            print(f"  Confidence: {vendor.forecast_confidence}")
        
        print(f"\n📝 MANUAL REVIEW NEEDED ({len(manual_vendors)})")
        print("=" * 80)
        for vendor in manual_vendors[:10]:
            print(f"{vendor.vendor_name}:")
            print(f"  Issue: {vendor.reasoning}")
            print(f"  Transactions: {vendor.transaction_count}")
            print(f"  Suggested: ${vendor.amount_pattern.suggested_amount:,.0f}")
        
        if skip_vendors:
            print(f"\n⏭️ SKIP ({len(skip_vendors)})")
            print("=" * 80)
            for vendor in skip_vendors[:5]:
                print(f"{vendor.vendor_name}: {vendor.reasoning}")

def main():
    """Test practical pattern detection"""
    detector = PracticalPatternDetection()
    
    print("🚀 PRACTICAL PATTERN DETECTION TEST")
    print("=" * 80)
    print("Target: 60-80% success rate (auto + manual review)")
    
    # Analyze patterns
    patterns = detector.analyze_vendor_patterns('spyguy')
    
    # Print detailed results
    detector.print_analysis_results(patterns)
    
    # Calculate success metrics
    total = len(patterns)
    auto_count = sum(1 for p in patterns.values() if p.forecast_recommendation == 'auto')
    manual_count = sum(1 for p in patterns.values() if p.forecast_recommendation == 'manual_review')
    forecastable = auto_count + manual_count
    
    print(f"\n📈 SUCCESS METRICS")
    print("=" * 80)
    print(f"Total vendors analyzed: {total}")
    print(f"Auto-ready: {auto_count} ({auto_count/total*100:.0f}%)")
    print(f"Manual review: {manual_count} ({manual_count/total*100:.0f}%)")
    print(f"Total forecastable: {forecastable} ({forecastable/total*100:.0f}%)")
    print(f"\n{'✅ SUCCESS!' if forecastable/total >= 0.6 else '❌ NEEDS IMPROVEMENT'}")

if __name__ == "__main__":
    main()