#!/usr/bin/env python3
"""
Enhanced Pattern Detection System V2
Implements multi-level pattern detection with separated timing and amount analysis
"""

import sys
sys.path.append('.')

from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, date, timedelta
from dataclasses import dataclass
import numpy as np
from collections import Counter, defaultdict
import statistics

from database.forecast_db_manager import forecast_db
from lean_forecasting.vendor_classifier import vendor_classifier

@dataclass
class TimingPattern:
    """Represents timing pattern analysis results"""
    frequency: str  # daily, weekly, bi-weekly, monthly, quarterly, irregular
    confidence: float
    typical_day: Optional[str]  # Monday, 15th, etc
    timing_flexibility_days: int
    intervals: List[int]  # Days between transactions
    next_expected_date: Optional[date]

@dataclass
class AmountPattern:
    """Represents amount pattern analysis results"""
    pattern_type: str  # fixed, variable_range, increasing, decreasing, seasonal
    average: float
    median: float
    std_deviation: float
    range: Tuple[float, float]
    volatility: str  # low, medium, high
    confidence: float
    seasonal_factors: Optional[Dict[int, float]]  # month -> multiplier

@dataclass
class EnhancedPattern:
    """Combined pattern analysis with business context"""
    vendor_name: str
    vendor_classification: Any
    timing_pattern: TimingPattern
    amount_pattern: AmountPattern
    macro_pattern: Optional[Dict]  # Monthly/quarterly aggregates
    confidence_scores: Dict[str, float]
    forecast_method: str
    business_notes: str

class EnhancedPatternDetectorV2:
    """Advanced pattern detection with multi-level analysis"""
    
    def __init__(self):
        self.db = forecast_db
        
    def analyze_vendor_pattern(self, client_id: str, vendor_group_name: str,
                             display_names: List[str], 
                             lookback_months: int = 12) -> EnhancedPattern:
        """
        Perform comprehensive pattern analysis on a vendor group
        
        Args:
            client_id: Client identifier
            vendor_group_name: Name of vendor group
            display_names: List of display names in the group
            lookback_months: Months of history to analyze
            
        Returns:
            EnhancedPattern with complete analysis
        """
        print(f"\n🔍 Enhanced Pattern Analysis V2: {vendor_group_name}")
        print("=" * 80)
        
        # Step 1: Get vendor classification
        classification = vendor_classifier.classify_vendor(vendor_group_name)
        print(f"📊 Vendor Type: {classification.vendor_type} ({classification.confidence:.2f} confidence)")
        
        # Step 2: Get transaction history
        transactions = self._get_transaction_history(
            client_id, display_names, lookback_months
        )
        
        if not transactions:
            print("❌ No transaction history found")
            return self._create_default_pattern(vendor_group_name, classification)
        
        print(f"📈 Analyzing {len(transactions)} transactions")
        
        # Step 3: Separate timing and amount analysis
        timing_pattern = self._analyze_timing_pattern(transactions, classification)
        amount_pattern = self._analyze_amount_pattern(transactions, classification)
        
        # Step 4: Macro pattern analysis (monthly/quarterly)
        macro_pattern = self._analyze_macro_patterns(transactions)
        
        # Step 5: Calculate confidence scores
        confidence_scores = self._calculate_confidence_scores(
            timing_pattern, amount_pattern, macro_pattern, len(transactions)
        )
        
        # Step 6: Determine best forecast method
        forecast_method = self._select_forecast_method(
            classification, timing_pattern, amount_pattern, confidence_scores
        )
        
        # Step 7: Generate business notes
        business_notes = self._generate_business_notes(
            classification, timing_pattern, amount_pattern
        )
        
        return EnhancedPattern(
            vendor_name=vendor_group_name,
            vendor_classification=classification,
            timing_pattern=timing_pattern,
            amount_pattern=amount_pattern,
            macro_pattern=macro_pattern,
            confidence_scores=confidence_scores,
            forecast_method=forecast_method,
            business_notes=business_notes
        )
    
    def _get_transaction_history(self, client_id: str, display_names: List[str],
                               lookback_months: int) -> List[Dict]:
        """Get transaction history from database"""
        start_date = datetime.now().date() - timedelta(days=lookback_months * 30)
        
        # Get all transactions for the display names
        all_transactions = []
        
        # Use forecast_db to get transactions
        try:
            # Get vendor names from display names
            vendor_names = []
            for display_name in display_names:
                vendors = self.db.get_vendors_by_display_name(client_id, display_name)
                vendor_names.extend([v['vendor_name'] for v in vendors])
            
            if vendor_names:
                transactions = self.db.get_transactions_by_vendors(
                    client_id, vendor_names, start_date
                )
                all_transactions = [
                    {
                        'transaction_date': t['transaction_date'],
                        'amount': t['amount'],
                        'vendor_name': t['vendor_name']
                    }
                    for t in transactions
                ]
        except Exception as e:
            print(f"Error getting transaction history: {e}")
            return []
        
        # Sort by date
        all_transactions.sort(key=lambda x: x['transaction_date'])
        return all_transactions
    
    def _analyze_timing_pattern(self, transactions: List[Dict],
                              classification: Any) -> TimingPattern:
        """Analyze timing patterns independently of amounts"""
        print("\n⏰ Timing Pattern Analysis")
        
        # Get transaction dates
        dates = [datetime.fromisoformat(t['transaction_date']).date() 
                for t in transactions]
        
        if len(dates) < 2:
            return TimingPattern(
                frequency='insufficient_data',
                confidence=0.0,
                typical_day=None,
                timing_flexibility_days=classification.timing_flexibility_days,
                intervals=[],
                next_expected_date=None
            )
        
        # Calculate intervals between transactions
        intervals = []
        for i in range(1, len(dates)):
            interval = (dates[i] - dates[i-1]).days
            intervals.append(interval)
        
        # Detect frequency patterns
        frequency, confidence, typical_day = self._detect_frequency_pattern(
            dates, intervals, classification
        )
        
        # Calculate next expected date
        next_expected = self._calculate_next_expected_date(
            dates, frequency, typical_day
        )
        
        print(f"   Frequency: {frequency} ({confidence:.2f} confidence)")
        print(f"   Typical Day: {typical_day}")
        print(f"   Average Interval: {statistics.mean(intervals):.1f} days")
        
        return TimingPattern(
            frequency=frequency,
            confidence=confidence,
            typical_day=typical_day,
            timing_flexibility_days=classification.timing_flexibility_days,
            intervals=intervals,
            next_expected_date=next_expected
        )
    
    def _analyze_amount_pattern(self, transactions: List[Dict],
                              classification: Any) -> AmountPattern:
        """Analyze amount patterns independently of timing"""
        print("\n💰 Amount Pattern Analysis")
        
        # Get amounts
        amounts = [abs(float(t['amount'])) for t in transactions]
        
        if not amounts:
            return self._create_default_amount_pattern()
        
        # Basic statistics
        avg = statistics.mean(amounts)
        median = statistics.median(amounts)
        std_dev = statistics.stdev(amounts) if len(amounts) > 1 else 0
        
        # Determine pattern type and volatility
        cv = std_dev / avg if avg > 0 else 0  # Coefficient of variation
        
        if cv < 0.1:
            pattern_type = 'fixed'
            volatility = 'low'
        elif cv < 0.3:
            pattern_type = 'variable_range'
            volatility = 'medium'
        else:
            pattern_type = 'variable_range'
            volatility = 'high'
        
        # Check for trends
        if len(amounts) >= 6:
            trend = self._detect_amount_trend(amounts)
            if trend:
                pattern_type = trend
        
        # Check for seasonal patterns
        seasonal_factors = None
        if len(transactions) >= 12:
            seasonal_factors = self._detect_seasonal_pattern(transactions)
            if seasonal_factors:
                pattern_type = 'seasonal'
        
        print(f"   Pattern Type: {pattern_type}")
        print(f"   Average: ${avg:,.2f}")
        print(f"   Volatility: {volatility} (CV={cv:.2f})")
        print(f"   Range: ${min(amounts):,.2f} - ${max(amounts):,.2f}")
        
        return AmountPattern(
            pattern_type=pattern_type,
            average=avg,
            median=median,
            std_deviation=std_dev,
            range=(min(amounts), max(amounts)),
            volatility=volatility,
            confidence=self._calculate_amount_confidence(amounts, cv),
            seasonal_factors=seasonal_factors
        )
    
    def _detect_frequency_pattern(self, dates: List[date], intervals: List[int],
                                classification: Any) -> Tuple[str, float, Optional[str]]:
        """Detect timing frequency pattern with flexibility"""
        
        # Check for daily pattern (excluding weekends)
        weekdays = [d.weekday() for d in dates]
        if all(wd < 5 for wd in weekdays) and statistics.mean(intervals) < 3:
            return 'daily', 0.9, 'weekdays'
        
        # Check for weekly pattern
        weekly_check = self._check_weekly_pattern(dates, intervals)
        if weekly_check[0]:
            return 'weekly', weekly_check[1], weekly_check[2]
        
        # Check for bi-weekly pattern
        biweekly_check = self._check_biweekly_pattern(dates, intervals)
        if biweekly_check[0]:
            return 'bi-weekly', biweekly_check[1], biweekly_check[2]
        
        # Check for monthly pattern
        monthly_check = self._check_monthly_pattern(dates, intervals)
        if monthly_check[0]:
            return 'monthly', monthly_check[1], monthly_check[2]
        
        # Check for quarterly pattern
        if statistics.mean(intervals) > 75 and statistics.mean(intervals) < 105:
            return 'quarterly', 0.7, 'variable'
        
        # Check for "mostly regular" patterns based on business rules
        if classification.vendor_type in ['contractor_platform', 'professional_services']:
            # These often have irregular timing but predictable totals
            if 10 <= statistics.mean(intervals) <= 35:
                return 'monthly_irregular', 0.6, 'variable'
        
        return 'irregular', 0.3, None
    
    def _check_weekly_pattern(self, dates: List[date], 
                            intervals: List[int]) -> Tuple[bool, float, Optional[str]]:
        """Check for weekly pattern with tolerance"""
        avg_interval = statistics.mean(intervals)
        
        if 5 <= avg_interval <= 9:  # Weekly with tolerance
            # Find most common weekday
            weekdays = [d.strftime('%A') for d in dates]
            day_counts = Counter(weekdays)
            most_common_day = day_counts.most_common(1)[0][0]
            
            # Calculate confidence based on consistency
            consistency = day_counts[most_common_day] / len(dates)
            
            if consistency > 0.6:
                return True, consistency, most_common_day
        
        return False, 0.0, None
    
    def _check_biweekly_pattern(self, dates: List[date],
                               intervals: List[int]) -> Tuple[bool, float, Optional[str]]:
        """Check for bi-weekly pattern with tolerance"""
        avg_interval = statistics.mean(intervals)
        
        if 11 <= avg_interval <= 17:  # Bi-weekly with tolerance
            # Find most common weekday
            weekdays = [d.strftime('%A') for d in dates]
            day_counts = Counter(weekdays)
            most_common_day = day_counts.most_common(1)[0][0]
            
            # Check interval consistency
            biweekly_intervals = [i for i in intervals if 11 <= i <= 17]
            consistency = len(biweekly_intervals) / len(intervals) if intervals else 0
            
            if consistency > 0.6:
                return True, consistency, most_common_day
        
        return False, 0.0, None
    
    def _check_monthly_pattern(self, dates: List[date],
                              intervals: List[int]) -> Tuple[bool, float, Optional[str]]:
        """Check for monthly pattern with tolerance"""
        avg_interval = statistics.mean(intervals)
        
        if 25 <= avg_interval <= 35:  # Monthly with tolerance
            # Find most common day of month
            days_of_month = [d.day for d in dates]
            
            # Group similar days (e.g., 14, 15, 16 are all "mid-month")
            day_groups = defaultdict(int)
            for day in days_of_month:
                if day <= 5:
                    day_groups['early'] += 1
                elif day <= 10:
                    day_groups['early-mid'] += 1
                elif day <= 20:
                    day_groups['mid'] += 1
                elif day <= 25:
                    day_groups['late-mid'] += 1
                else:
                    day_groups['late'] += 1
            
            most_common_group = max(day_groups.items(), key=lambda x: x[1])
            consistency = most_common_group[1] / len(dates)
            
            if consistency > 0.5:
                # Find specific day within the group
                group_days = [d for d in days_of_month 
                            if self._get_day_group(d) == most_common_group[0]]
                typical_day = f"{int(statistics.median(group_days))}th"
                return True, consistency, typical_day
        
        return False, 0.0, None
    
    def _get_day_group(self, day: int) -> str:
        """Get day group for monthly pattern detection"""
        if day <= 5:
            return 'early'
        elif day <= 10:
            return 'early-mid'
        elif day <= 20:
            return 'mid'
        elif day <= 25:
            return 'late-mid'
        else:
            return 'late'
    
    def _detect_amount_trend(self, amounts: List[float]) -> Optional[str]:
        """Detect if amounts are trending up or down"""
        # Simple linear regression
        x = list(range(len(amounts)))
        y = amounts
        
        # Calculate slope
        n = len(amounts)
        xy_sum = sum(x[i] * y[i] for i in range(n))
        x_sum = sum(x)
        y_sum = sum(y)
        x_squared_sum = sum(xi ** 2 for xi in x)
        
        slope = (n * xy_sum - x_sum * y_sum) / (n * x_squared_sum - x_sum ** 2)
        
        # Determine if trend is significant
        avg_amount = statistics.mean(amounts)
        trend_strength = abs(slope) / avg_amount if avg_amount > 0 else 0
        
        if trend_strength > 0.05:  # 5% change per period
            return 'increasing' if slope > 0 else 'decreasing'
        
        return None
    
    def _detect_seasonal_pattern(self, transactions: List[Dict]) -> Optional[Dict[int, float]]:
        """Detect seasonal patterns in amounts"""
        # Group by month
        monthly_amounts = defaultdict(list)
        
        for t in transactions:
            date = datetime.fromisoformat(t['transaction_date'])
            month = date.month
            amount = abs(float(t['amount']))
            monthly_amounts[month].append(amount)
        
        # Need at least 6 months of data
        if len(monthly_amounts) < 6:
            return None
        
        # Calculate monthly averages
        monthly_avgs = {}
        for month, amounts in monthly_amounts.items():
            monthly_avgs[month] = statistics.mean(amounts)
        
        # Calculate overall average
        overall_avg = statistics.mean(monthly_avgs.values())
        
        # Calculate seasonal factors
        seasonal_factors = {}
        for month, avg in monthly_avgs.items():
            seasonal_factors[month] = avg / overall_avg if overall_avg > 0 else 1.0
        
        # Check if seasonal variation is significant
        factors = list(seasonal_factors.values())
        variation = max(factors) - min(factors)
        
        if variation > 0.3:  # 30% variation
            return seasonal_factors
        
        return None
    
    def _analyze_macro_patterns(self, transactions: List[Dict]) -> Dict:
        """Analyze patterns at monthly and quarterly levels"""
        print("\n📊 Macro Pattern Analysis")
        
        # Group by month
        monthly_totals = defaultdict(float)
        monthly_counts = defaultdict(int)
        
        for t in transactions:
            date = datetime.fromisoformat(t['transaction_date'])
            month_key = f"{date.year}-{date.month:02d}"
            amount = abs(float(t['amount']))
            monthly_totals[month_key] += amount
            monthly_counts[month_key] += 1
        
        # Calculate quarterly totals
        quarterly_totals = defaultdict(float)
        for month_key, total in monthly_totals.items():
            year, month = month_key.split('-')
            quarter = (int(month) - 1) // 3 + 1
            quarter_key = f"{year}-Q{quarter}"
            quarterly_totals[quarter_key] += total
        
        # Calculate statistics
        monthly_values = list(monthly_totals.values())
        quarterly_values = list(quarterly_totals.values())
        
        macro_pattern = {
            'monthly_average': statistics.mean(monthly_values) if monthly_values else 0,
            'monthly_median': statistics.median(monthly_values) if monthly_values else 0,
            'monthly_consistency': self._calculate_consistency(monthly_values),
            'quarterly_average': statistics.mean(quarterly_values) if quarterly_values else 0,
            'quarterly_consistency': self._calculate_consistency(quarterly_values),
            'monthly_totals': dict(monthly_totals),
            'quarterly_totals': dict(quarterly_totals)
        }
        
        print(f"   Monthly Average: ${macro_pattern['monthly_average']:,.2f}")
        print(f"   Monthly Consistency: {macro_pattern['monthly_consistency']:.2f}")
        print(f"   Quarterly Average: ${macro_pattern['quarterly_average']:,.2f}")
        
        return macro_pattern
    
    def _calculate_consistency(self, values: List[float]) -> float:
        """Calculate consistency score (0-1) for a series of values"""
        if not values or len(values) < 2:
            return 0.0
        
        avg = statistics.mean(values)
        if avg == 0:
            return 0.0
        
        std_dev = statistics.stdev(values)
        cv = std_dev / avg
        
        # Convert CV to consistency score (lower CV = higher consistency)
        consistency = max(0, 1 - cv)
        return consistency
    
    def _calculate_confidence_scores(self, timing_pattern: TimingPattern,
                                   amount_pattern: AmountPattern,
                                   macro_pattern: Dict,
                                   transaction_count: int) -> Dict[str, float]:
        """Calculate comprehensive confidence scores"""
        scores = {
            'timing_regularity': timing_pattern.confidence,
            'amount_predictability': amount_pattern.confidence,
            'macro_consistency': (macro_pattern['monthly_consistency'] + 
                                macro_pattern['quarterly_consistency']) / 2,
            'data_sufficiency': min(1.0, transaction_count / 24),  # 24 months = perfect
            'overall_forecastability': 0.0
        }
        
        # Calculate weighted overall score
        if timing_pattern.frequency != 'irregular':
            # Regular timing patterns
            scores['overall_forecastability'] = (
                scores['timing_regularity'] * 0.5 +
                scores['amount_predictability'] * 0.3 +
                scores['macro_consistency'] * 0.2
            )
        else:
            # Irregular timing - rely more on macro patterns
            scores['overall_forecastability'] = (
                scores['macro_consistency'] * 0.6 +
                scores['amount_predictability'] * 0.3 +
                scores['data_sufficiency'] * 0.1
            )
        
        return scores
    
    def _calculate_amount_confidence(self, amounts: List[float], cv: float) -> float:
        """Calculate confidence score for amount predictions"""
        if not amounts:
            return 0.0
        
        # Base confidence on coefficient of variation
        if cv < 0.1:
            base_confidence = 0.95
        elif cv < 0.3:
            base_confidence = 0.8
        elif cv < 0.5:
            base_confidence = 0.6
        else:
            base_confidence = 0.4
        
        # Adjust for data points
        data_factor = min(1.0, len(amounts) / 12)
        
        return base_confidence * data_factor
    
    def _select_forecast_method(self, classification: Any,
                              timing_pattern: TimingPattern,
                              amount_pattern: AmountPattern,
                              confidence_scores: Dict[str, float]) -> str:
        """Select the best forecasting method based on patterns"""
        
        # High confidence in both timing and amounts
        if (timing_pattern.confidence > 0.8 and 
            amount_pattern.confidence > 0.8):
            return 'precise_schedule'
        
        # Good timing, variable amounts
        elif (timing_pattern.confidence > 0.7 and 
              amount_pattern.volatility in ['medium', 'high']):
            return 'timing_with_range'
        
        # Poor timing, consistent amounts
        elif (timing_pattern.confidence < 0.5 and 
              amount_pattern.confidence > 0.7):
            return 'amount_based_projection'
        
        # Seasonal pattern detected
        elif amount_pattern.pattern_type == 'seasonal':
            return 'seasonal_forecast'
        
        # Trending pattern
        elif amount_pattern.pattern_type in ['increasing', 'decreasing']:
            return 'trend_projection'
        
        # Use macro patterns for irregular vendors
        elif confidence_scores['macro_consistency'] > 0.7:
            return 'macro_distribution'
        
        # Vendor-specific methods
        elif classification.vendor_type == 'contractor_platform':
            return 'contractor_aggregate'
        
        elif classification.vendor_type == 'inventory_supplier':
            return 'reorder_cycle'
        
        # Default to historical average
        else:
            return 'historical_average'
    
    def _generate_business_notes(self, classification: Any,
                               timing_pattern: TimingPattern,
                               amount_pattern: AmountPattern) -> str:
        """Generate human-readable business insights"""
        notes = []
        
        # Timing insights
        if timing_pattern.frequency != 'irregular':
            notes.append(f"Payments typically occur {timing_pattern.frequency}")
            if timing_pattern.typical_day:
                notes.append(f"usually on {timing_pattern.typical_day}")
        else:
            notes.append("Payment timing is irregular")
        
        # Amount insights
        if amount_pattern.volatility == 'low':
            notes.append("with consistent amounts")
        elif amount_pattern.volatility == 'medium':
            notes.append("with moderate amount variation")
        else:
            notes.append(f"with high variation (${amount_pattern.range[0]:,.0f}-${amount_pattern.range[1]:,.0f})")
        
        # Business context
        if classification.vendor_type == 'contractor_platform':
            notes.append("(typical for contractor payments)")
        elif classification.vendor_type == 'revenue_source':
            if amount_pattern.pattern_type == 'seasonal':
                notes.append("(shows seasonal revenue patterns)")
        
        return ". ".join(notes)
    
    def _calculate_next_expected_date(self, dates: List[date],
                                    frequency: str,
                                    typical_day: Optional[str]) -> Optional[date]:
        """Calculate next expected transaction date"""
        if not dates or frequency == 'irregular':
            return None
        
        last_date = dates[-1]
        
        if frequency == 'daily':
            # Next weekday
            next_date = last_date + timedelta(days=1)
            while next_date.weekday() >= 5:  # Skip weekends
                next_date += timedelta(days=1)
            return next_date
        
        elif frequency == 'weekly':
            return last_date + timedelta(weeks=1)
        
        elif frequency == 'bi-weekly':
            return last_date + timedelta(weeks=2)
        
        elif frequency == 'monthly':
            # Same day next month
            if last_date.month == 12:
                next_date = date(last_date.year + 1, 1, last_date.day)
            else:
                try:
                    next_date = date(last_date.year, last_date.month + 1, last_date.day)
                except ValueError:
                    # Handle end of month
                    next_date = date(last_date.year, last_date.month + 1, 1) - timedelta(days=1)
            return next_date
        
        elif frequency == 'quarterly':
            return last_date + timedelta(days=90)
        
        return None
    
    def _create_default_pattern(self, vendor_name: str,
                              classification: Any) -> EnhancedPattern:
        """Create default pattern when no data available"""
        return EnhancedPattern(
            vendor_name=vendor_name,
            vendor_classification=classification,
            timing_pattern=TimingPattern(
                frequency='no_data',
                confidence=0.0,
                typical_day=None,
                timing_flexibility_days=classification.timing_flexibility_days,
                intervals=[],
                next_expected_date=None
            ),
            amount_pattern=self._create_default_amount_pattern(),
            macro_pattern={},
            confidence_scores={
                'timing_regularity': 0.0,
                'amount_predictability': 0.0,
                'macro_consistency': 0.0,
                'data_sufficiency': 0.0,
                'overall_forecastability': 0.0
            },
            forecast_method='manual_required',
            business_notes='No transaction history available - manual input required'
        )
    
    def _create_default_amount_pattern(self) -> AmountPattern:
        """Create default amount pattern"""
        return AmountPattern(
            pattern_type='unknown',
            average=0.0,
            median=0.0,
            std_deviation=0.0,
            range=(0.0, 0.0),
            volatility='unknown',
            confidence=0.0,
            seasonal_factors=None
        )

# Singleton instance
enhanced_pattern_detector_v2 = EnhancedPatternDetectorV2()

def test_enhanced_detector():
    """Test the enhanced pattern detector"""
    print("🧪 Testing Enhanced Pattern Detector V2")
    print("=" * 80)
    
    # Test with a known vendor
    pattern = enhanced_pattern_detector_v2.analyze_vendor_pattern(
        client_id='bestself',
        vendor_group_name='Wise Transfers',
        display_names=['Wise Transfers']
    )
    
    print(f"\n📊 Pattern Analysis Complete")
    print(f"   Forecast Method: {pattern.forecast_method}")
    print(f"   Business Notes: {pattern.business_notes}")
    print(f"   Overall Confidence: {pattern.confidence_scores['overall_forecastability']:.2f}")

if __name__ == "__main__":
    test_enhanced_detector()