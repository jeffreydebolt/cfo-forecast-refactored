#!/usr/bin/env python3
"""
Pattern Detection Engine - Phase 3
Analyzes regular vendors for timing patterns and amount consistency
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
    pattern_type: str  # daily, weekly, bi_weekly, monthly, quarterly
    frequency_days: int  # Average days between transactions
    day_of_week: Optional[int] = None  # 0=Monday, 6=Sunday
    day_of_month: Optional[int] = None  # 1-31
    confidence: float = 0.0  # Mathematical confidence 0-1
    consistency_score: float = 0.0  # How consistent the pattern is

@dataclass
class AmountPattern:
    """Detected amount pattern for a vendor"""
    average_amount: float
    median_amount: float
    variance_coefficient: float  # Standard deviation / mean
    amount_type: str  # consistent, variable, seasonal
    confidence: float = 0.0

@dataclass
class VendorPattern:
    """Complete pattern analysis for a vendor"""
    vendor_name: str
    transaction_count: int
    timing_pattern: TimingPattern
    amount_pattern: AmountPattern
    forecast_recommendation: str  # auto, manual, skip
    reasoning: str

class PatternDetectionEngine:
    """Analyzes vendor transaction patterns for forecasting"""
    
    def __init__(self):
        # Thresholds for pattern classification
        self.CONSISTENCY_THRESHOLD = 0.15  # 15% variance threshold
        self.MIN_TRANSACTIONS = 3  # Minimum transactions for pattern detection
        self.CONFIDENCE_THRESHOLD = 0.6  # Minimum confidence for auto-forecasting
    
    def analyze_vendor_patterns(self, client_id: str) -> Dict[str, VendorPattern]:
        """Main entry point - analyze all regular vendors for patterns"""
        print("🔍 PATTERN DETECTION ENGINE")
        print("=" * 80)
        
        # Get regular vendors from onboarding
        regular_vendors = self._get_regular_vendors(client_id)
        print(f"📊 Analyzing patterns for {len(regular_vendors)} regular vendors")
        
        # Analyze each vendor
        vendor_patterns = {}
        
        for vendor_name, vendor_data in regular_vendors.items():
            pattern = self._analyze_single_vendor(vendor_name, vendor_data['transactions'])
            vendor_patterns[vendor_name] = pattern
        
        # Classify by forecast recommendation
        auto_vendors = [p for p in vendor_patterns.values() if p.forecast_recommendation == 'auto']
        manual_vendors = [p for p in vendor_patterns.values() if p.forecast_recommendation == 'manual']
        skip_vendors = [p for p in vendor_patterns.values() if p.forecast_recommendation == 'skip']
        
        print(f"\n📋 PATTERN ANALYSIS COMPLETE")
        print(f"✅ Auto-forecast ready: {len(auto_vendors)} vendors")
        print(f"⚠️ Manual review needed: {len(manual_vendors)} vendors")
        print(f"⏭️ Skip forecasting: {len(skip_vendors)} vendors")
        
        return vendor_patterns
    
    def _get_regular_vendors(self, client_id: str) -> Dict[str, Dict]:
        """Get vendors with regular activity (2+ transactions in 12 months)"""
        result = supabase.table('transactions').select('*').eq('client_id', client_id).execute()
        transactions = result.data
        
        # Group by vendor name
        vendor_data = defaultdict(list)
        for txn in transactions:
            vendor_data[txn['vendor_name']].append(txn)
        
        # Filter for regular vendors (2+ transactions in last 12 months)
        cutoff_date = date.today() - timedelta(days=365)
        regular_vendors = {}
        
        for vendor_name, txns in vendor_data.items():
            # Check for recent activity
            recent_txns = [
                txn for txn in txns 
                if datetime.fromisoformat(txn['transaction_date']).date() >= cutoff_date
            ]
            
            if len(recent_txns) >= 2:
                # Sort by date
                txns.sort(key=lambda x: x['transaction_date'])
                regular_vendors[vendor_name] = {'transactions': txns}
        
        return regular_vendors
    
    def _analyze_single_vendor(self, vendor_name: str, transactions: List[Dict]) -> VendorPattern:
        """Analyze patterns for a single vendor"""
        
        # Extract transaction data
        dates = [datetime.fromisoformat(txn['transaction_date']).date() for txn in transactions]
        amounts = [abs(float(txn['amount'])) for txn in transactions]
        
        # Analyze timing patterns
        timing_pattern = self._detect_timing_pattern(dates)
        
        # Analyze amount patterns
        amount_pattern = self._detect_amount_pattern(amounts)
        
        # Generate forecast recommendation
        recommendation, reasoning = self._generate_recommendation(
            vendor_name, timing_pattern, amount_pattern, len(transactions)
        )
        
        return VendorPattern(
            vendor_name=vendor_name,
            transaction_count=len(transactions),
            timing_pattern=timing_pattern,
            amount_pattern=amount_pattern,
            forecast_recommendation=recommendation,
            reasoning=reasoning
        )
    
    def _detect_timing_pattern(self, dates: List[date]) -> TimingPattern:
        """Detect timing patterns in transaction dates"""
        if len(dates) < 2:
            return TimingPattern(
                pattern_type='insufficient_data',
                frequency_days=0,
                confidence=0.0,
                consistency_score=0.0
            )
        
        # Calculate gaps between consecutive transactions
        gaps = []
        for i in range(1, len(dates)):
            gap_days = (dates[i] - dates[i-1]).days
            gaps.append(gap_days)
        
        if not gaps:
            return TimingPattern(
                pattern_type='single_transaction',
                frequency_days=0,
                confidence=0.0,
                consistency_score=0.0
            )
        
        # Analyze gap patterns
        avg_gap = statistics.mean(gaps)
        median_gap = statistics.median(gaps)
        gap_std = statistics.stdev(gaps) if len(gaps) > 1 else 0
        
        # Calculate consistency (lower coefficient of variation = more consistent)
        consistency_score = 1 - (gap_std / avg_gap) if avg_gap > 0 else 0
        consistency_score = max(0, min(1, consistency_score))
        
        # Classify pattern type based on average gap
        if avg_gap <= 2:
            pattern_type = 'daily'
        elif 6 <= avg_gap <= 8:
            pattern_type = 'weekly'
        elif 13 <= avg_gap <= 15:
            pattern_type = 'bi_weekly'
        elif 28 <= avg_gap <= 32:
            pattern_type = 'monthly'
        elif 85 <= avg_gap <= 95:
            pattern_type = 'quarterly'
        else:
            pattern_type = 'irregular'
        
        # Calculate confidence based on consistency and sample size
        confidence = consistency_score * min(1.0, len(gaps) / 5)  # More samples = higher confidence
        
        # Detect day-of-week patterns for weekly/bi-weekly
        day_of_week = None
        if pattern_type in ['weekly', 'bi_weekly'] and len(dates) >= 3:
            weekdays = [d.weekday() for d in dates]
            most_common_day = Counter(weekdays).most_common(1)[0][0]
            if Counter(weekdays)[most_common_day] / len(weekdays) >= 0.6:  # 60% consistency
                day_of_week = most_common_day
        
        # Detect day-of-month patterns for monthly
        day_of_month = None
        if pattern_type == 'monthly' and len(dates) >= 3:
            month_days = [d.day for d in dates]
            most_common_day = Counter(month_days).most_common(1)[0][0]
            if Counter(month_days)[most_common_day] / len(month_days) >= 0.6:  # 60% consistency
                day_of_month = most_common_day
        
        return TimingPattern(
            pattern_type=pattern_type,
            frequency_days=int(avg_gap),
            day_of_week=day_of_week,
            day_of_month=day_of_month,
            confidence=confidence,
            consistency_score=consistency_score
        )
    
    def _detect_amount_pattern(self, amounts: List[float]) -> AmountPattern:
        """Detect amount patterns in transaction amounts"""
        if not amounts:
            return AmountPattern(
                average_amount=0,
                median_amount=0,
                variance_coefficient=0,
                amount_type='insufficient_data',
                confidence=0.0
            )
        
        avg_amount = statistics.mean(amounts)
        median_amount = statistics.median(amounts)
        std_amount = statistics.stdev(amounts) if len(amounts) > 1 else 0
        
        # Calculate coefficient of variation (std / mean)
        variance_coefficient = std_amount / avg_amount if avg_amount > 0 else 0
        
        # Classify amount consistency
        if variance_coefficient <= self.CONSISTENCY_THRESHOLD:
            amount_type = 'consistent'
            confidence = 0.9  # High confidence for consistent amounts
        elif variance_coefficient <= 0.5:
            amount_type = 'variable'
            confidence = 0.6  # Medium confidence
        else:
            amount_type = 'highly_variable'
            confidence = 0.3  # Low confidence
        
        # Adjust confidence based on sample size
        confidence *= min(1.0, len(amounts) / 5)
        
        return AmountPattern(
            average_amount=avg_amount,
            median_amount=median_amount,
            variance_coefficient=variance_coefficient,
            amount_type=amount_type,
            confidence=confidence
        )
    
    def _generate_recommendation(self, vendor_name: str, timing: TimingPattern, 
                               amount: AmountPattern, transaction_count: int) -> Tuple[str, str]:
        """Generate forecast recommendation based on patterns"""
        
        # Skip if insufficient data
        if transaction_count < self.MIN_TRANSACTIONS:
            return 'skip', f'Only {transaction_count} transactions - insufficient data'
        
        # Skip if both timing and amount patterns are unreliable
        if timing.confidence < 0.3 and amount.confidence < 0.3:
            return 'skip', 'Irregular timing and highly variable amounts'
        
        # Auto-forecast if both patterns are reliable
        if (timing.confidence >= self.CONFIDENCE_THRESHOLD and 
            amount.confidence >= self.CONFIDENCE_THRESHOLD and
            timing.pattern_type != 'irregular'):
            return 'auto', f'{timing.pattern_type.title()} pattern with {amount.amount_type} amounts'
        
        # Manual review for mixed reliability
        reasons = []
        if timing.confidence < self.CONFIDENCE_THRESHOLD:
            reasons.append('irregular timing')
        if amount.confidence < self.CONFIDENCE_THRESHOLD:
            reasons.append('variable amounts')
        if timing.pattern_type == 'irregular':
            reasons.append('no clear frequency pattern')
        
        return 'manual', f'Review needed: {", ".join(reasons)}'
    
    def print_pattern_analysis(self, vendor_patterns: Dict[str, VendorPattern]):
        """Print formatted pattern analysis results"""
        
        # Group by recommendation
        auto_vendors = [p for p in vendor_patterns.values() if p.forecast_recommendation == 'auto']
        manual_vendors = [p for p in vendor_patterns.values() if p.forecast_recommendation == 'manual']
        skip_vendors = [p for p in vendor_patterns.values() if p.forecast_recommendation == 'skip']
        
        print(f"\n📊 PATTERN ANALYSIS RESULTS")
        print("=" * 80)
        
        # Auto-forecast ready vendors
        if auto_vendors:
            print(f"\n✅ AUTO-FORECAST READY ({len(auto_vendors)} vendors)")
            for vendor in sorted(auto_vendors, key=lambda x: x.transaction_count, reverse=True):
                timing = vendor.timing_pattern
                amount = vendor.amount_pattern
                print(f"├── {vendor.vendor_name}")
                print(f"│   ├── Pattern: {timing.pattern_type} every {timing.frequency_days} days")
                print(f"│   ├── Amount: ${amount.average_amount:,.0f} ({amount.amount_type})")
                print(f"│   └── Confidence: {timing.confidence:.1%} timing, {amount.confidence:.1%} amount")
        
        # Manual review needed
        if manual_vendors:
            print(f"\n⚠️ MANUAL REVIEW NEEDED ({len(manual_vendors)} vendors)")
            for vendor in sorted(manual_vendors, key=lambda x: x.transaction_count, reverse=True):
                print(f"├── {vendor.vendor_name}")
                print(f"│   └── {vendor.reasoning}")
        
        # Skip forecasting
        if skip_vendors:
            print(f"\n⏭️ SKIP FORECASTING ({len(skip_vendors)} vendors)")
            for vendor in sorted(skip_vendors, key=lambda x: x.transaction_count, reverse=True):
                print(f"├── {vendor.vendor_name}: {vendor.reasoning}")

def main():
    """Test the pattern detection engine"""
    engine = PatternDetectionEngine()
    
    print("🔍 PATTERN DETECTION ENGINE TEST")
    print("=" * 80)
    
    # Analyze vendor patterns
    patterns = engine.analyze_vendor_patterns('spyguy')
    
    # Print detailed analysis
    engine.print_pattern_analysis(patterns)
    
    # Summary statistics
    auto_count = sum(1 for p in patterns.values() if p.forecast_recommendation == 'auto')
    manual_count = sum(1 for p in patterns.values() if p.forecast_recommendation == 'manual')
    skip_count = sum(1 for p in patterns.values() if p.forecast_recommendation == 'skip')
    
    print(f"\n📈 FORECASTING READINESS")
    print(f"Ready for auto-forecasting: {auto_count}/{len(patterns)} vendors")
    print(f"Need manual setup: {manual_count}/{len(patterns)} vendors")
    print(f"Skip forecasting: {skip_count}/{len(patterns)} vendors")
    print(f"Next: Generate forecasts for auto-ready vendors")
    
    return patterns

if __name__ == "__main__":
    main()