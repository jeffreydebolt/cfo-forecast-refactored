#!/usr/bin/env python3
"""
Enhanced Forecast Generator
Implements multiple forecasting methods based on pattern types
"""

import sys
sys.path.append('.')

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date, timedelta
from dataclasses import dataclass
import numpy as np
from collections import defaultdict
import statistics
import random

from lean_forecasting.enhanced_pattern_detector_v2 import (
    EnhancedPattern, TimingPattern, AmountPattern, enhanced_pattern_detector_v2
)

@dataclass
class ForecastRecord:
    """Represents a single forecast entry"""
    vendor_name: str
    forecast_date: date
    forecast_amount: float
    confidence: float
    method: str
    amount_range: Optional[Tuple[float, float]]
    notes: str

class EnhancedForecastGenerator:
    """Generate forecasts using multiple methods based on pattern analysis"""
    
    def generate_forecasts(self, pattern: EnhancedPattern, 
                         start_date: Optional[date] = None,
                         weeks_ahead: int = 13) -> List[ForecastRecord]:
        """
        Generate forecasts based on enhanced pattern analysis
        
        Args:
            pattern: Enhanced pattern analysis results
            start_date: Start date for forecasts (default: today)
            weeks_ahead: Number of weeks to forecast
            
        Returns:
            List of forecast records
        """
        if start_date is None:
            start_date = date.today()
        
        end_date = start_date + timedelta(weeks=weeks_ahead)
        
        print(f"\n🔮 Generating Forecasts: {pattern.vendor_name}")
        print(f"   Method: {pattern.forecast_method}")
        print(f"   Period: {start_date} to {end_date}")
        
        # Route to appropriate forecast method
        method_map = {
            'precise_schedule': self._forecast_precise_schedule,
            'timing_with_range': self._forecast_timing_with_range,
            'amount_based_projection': self._forecast_amount_based,
            'seasonal_forecast': self._forecast_seasonal,
            'trend_projection': self._forecast_trend,
            'macro_distribution': self._forecast_macro_distribution,
            'contractor_aggregate': self._forecast_contractor_aggregate,
            'reorder_cycle': self._forecast_reorder_cycle,
            'historical_average': self._forecast_historical_average,
            'manual_required': self._forecast_manual_required
        }
        
        forecast_method = method_map.get(pattern.forecast_method, 
                                       self._forecast_historical_average)
        
        forecasts = forecast_method(pattern, start_date, end_date)
        
        print(f"   Generated {len(forecasts)} forecast records")
        
        # Show sample forecasts
        if forecasts:
            print("\n   Sample Forecasts:")
            for f in forecasts[:5]:
                range_str = f" (${f.amount_range[0]:,.0f}-${f.amount_range[1]:,.0f})" if f.amount_range else ""
                print(f"   {f.forecast_date}: ${f.forecast_amount:,.2f}{range_str} [{f.confidence:.0%}]")
            if len(forecasts) > 5:
                print(f"   ... and {len(forecasts) - 5} more")
        
        return forecasts
    
    def _forecast_precise_schedule(self, pattern: EnhancedPattern, 
                                 start_date: date, end_date: date) -> List[ForecastRecord]:
        """High confidence in both timing and amounts"""
        forecasts = []
        timing = pattern.timing_pattern
        amount = pattern.amount_pattern
        
        # Generate dates based on timing pattern
        forecast_dates = self._generate_dates_from_timing(
            timing, start_date, end_date
        )
        
        for forecast_date in forecast_dates:
            forecasts.append(ForecastRecord(
                vendor_name=pattern.vendor_name,
                forecast_date=forecast_date,
                forecast_amount=amount.average,
                confidence=min(timing.confidence, amount.confidence),
                method='precise_schedule',
                amount_range=None,
                notes=f"Regular {timing.frequency} payment"
            ))
        
        return forecasts
    
    def _forecast_timing_with_range(self, pattern: EnhancedPattern,
                                  start_date: date, end_date: date) -> List[ForecastRecord]:
        """Good timing pattern but variable amounts"""
        forecasts = []
        timing = pattern.timing_pattern
        amount = pattern.amount_pattern
        
        # Generate dates based on timing pattern
        forecast_dates = self._generate_dates_from_timing(
            timing, start_date, end_date
        )
        
        for forecast_date in forecast_dates:
            # Use range for variable amounts
            if amount.volatility == 'high':
                # For high volatility, use wider range
                range_multiplier = 1.5
            else:
                range_multiplier = 1.0
            
            amount_range = (
                max(0, amount.average - amount.std_deviation * range_multiplier),
                amount.average + amount.std_deviation * range_multiplier
            )
            
            forecasts.append(ForecastRecord(
                vendor_name=pattern.vendor_name,
                forecast_date=forecast_date,
                forecast_amount=amount.average,
                confidence=timing.confidence * 0.8,  # Reduce confidence for variable amounts
                method='timing_with_range',
                amount_range=amount_range,
                notes=f"{timing.frequency} payment with variable amount"
            ))
        
        return forecasts
    
    def _forecast_amount_based(self, pattern: EnhancedPattern,
                             start_date: date, end_date: date) -> List[ForecastRecord]:
        """Poor timing but consistent amounts - distribute evenly"""
        forecasts = []
        amount = pattern.amount_pattern
        
        # Estimate frequency from macro pattern
        if pattern.macro_pattern and pattern.macro_pattern['monthly_average'] > 0:
            monthly_count = pattern.macro_pattern['monthly_average'] / amount.average
            days_between = 30 / max(1, monthly_count)
        else:
            days_between = 30  # Default to monthly
        
        current_date = start_date
        while current_date <= end_date:
            forecasts.append(ForecastRecord(
                vendor_name=pattern.vendor_name,
                forecast_date=current_date,
                forecast_amount=amount.average,
                confidence=amount.confidence * 0.7,
                method='amount_based_projection',
                amount_range=None,
                notes="Distributed based on consistent amounts"
            ))
            current_date += timedelta(days=int(days_between))
        
        return forecasts
    
    def _forecast_seasonal(self, pattern: EnhancedPattern,
                         start_date: date, end_date: date) -> List[ForecastRecord]:
        """Apply seasonal adjustments to base forecast"""
        forecasts = []
        timing = pattern.timing_pattern
        amount = pattern.amount_pattern
        
        # Generate base dates
        if timing.frequency != 'irregular':
            forecast_dates = self._generate_dates_from_timing(
                timing, start_date, end_date
            )
        else:
            # Use monthly intervals for irregular timing
            forecast_dates = []
            current = start_date
            while current <= end_date:
                forecast_dates.append(current)
                current = self._add_month(current)
        
        for forecast_date in forecast_dates:
            # Apply seasonal factor
            month = forecast_date.month
            seasonal_factor = amount.seasonal_factors.get(month, 1.0) if amount.seasonal_factors else 1.0
            seasonal_amount = amount.average * seasonal_factor
            
            forecasts.append(ForecastRecord(
                vendor_name=pattern.vendor_name,
                forecast_date=forecast_date,
                forecast_amount=seasonal_amount,
                confidence=amount.confidence * 0.85,
                method='seasonal_forecast',
                amount_range=(seasonal_amount * 0.8, seasonal_amount * 1.2),
                notes=f"Seasonal adjustment: {seasonal_factor:.1f}x"
            ))
        
        return forecasts
    
    def _forecast_trend(self, pattern: EnhancedPattern,
                       start_date: date, end_date: date) -> List[ForecastRecord]:
        """Project trend into future"""
        forecasts = []
        timing = pattern.timing_pattern
        amount = pattern.amount_pattern
        
        # Calculate trend rate
        if amount.pattern_type == 'increasing':
            monthly_growth = 0.05  # 5% per month
        else:
            monthly_growth = -0.05  # -5% per month
        
        # Generate dates
        if timing.frequency != 'irregular':
            forecast_dates = self._generate_dates_from_timing(
                timing, start_date, end_date
            )
        else:
            # Use monthly for irregular
            forecast_dates = []
            current = start_date
            while current <= end_date:
                forecast_dates.append(current)
                current = self._add_month(current)
        
        # Start from latest known amount
        current_amount = amount.average
        
        for i, forecast_date in enumerate(forecast_dates):
            # Apply trend
            months_out = i * (30 / max(1, len(forecast_dates)))
            trend_factor = (1 + monthly_growth) ** months_out
            forecast_amount = current_amount * trend_factor
            
            forecasts.append(ForecastRecord(
                vendor_name=pattern.vendor_name,
                forecast_date=forecast_date,
                forecast_amount=forecast_amount,
                confidence=amount.confidence * (0.9 - i * 0.02),  # Confidence decreases over time
                method='trend_projection',
                amount_range=(forecast_amount * 0.85, forecast_amount * 1.15),
                notes=f"{amount.pattern_type.capitalize()} trend"
            ))
        
        return forecasts
    
    def _forecast_macro_distribution(self, pattern: EnhancedPattern,
                                   start_date: date, end_date: date) -> List[ForecastRecord]:
        """Use monthly/quarterly patterns for irregular vendors"""
        forecasts = []
        
        if not pattern.macro_pattern or pattern.macro_pattern['monthly_average'] == 0:
            return []
        
        # Get monthly average
        monthly_avg = pattern.macro_pattern['monthly_average']
        monthly_consistency = pattern.macro_pattern['monthly_consistency']
        
        # Distribute monthly amount across the month
        current_month = start_date.month
        current_year = start_date.year
        
        while date(current_year, current_month, 1) <= end_date:
            # Determine number of payments in month (based on historical patterns)
            if pattern.vendor_classification.vendor_type == 'contractor_platform':
                payments_per_month = 2  # Bi-weekly assumption
            else:
                payments_per_month = 1  # Monthly default
            
            amount_per_payment = monthly_avg / payments_per_month
            
            # Generate payment dates within month
            for i in range(payments_per_month):
                if payments_per_month == 1:
                    day = 15  # Mid-month
                else:
                    day = 1 + i * 15  # 1st and 15th
                
                try:
                    forecast_date = date(current_year, current_month, day)
                    if start_date <= forecast_date <= end_date:
                        forecasts.append(ForecastRecord(
                            vendor_name=pattern.vendor_name,
                            forecast_date=forecast_date,
                            forecast_amount=amount_per_payment,
                            confidence=monthly_consistency * 0.8,
                            method='macro_distribution',
                            amount_range=(amount_per_payment * 0.7, amount_per_payment * 1.3),
                            notes="Based on monthly patterns"
                        ))
                except ValueError:
                    # Handle invalid dates
                    pass
            
            # Move to next month
            if current_month == 12:
                current_month = 1
                current_year += 1
            else:
                current_month += 1
        
        return forecasts
    
    def _forecast_contractor_aggregate(self, pattern: EnhancedPattern,
                                     start_date: date, end_date: date) -> List[ForecastRecord]:
        """Special handling for contractor platforms"""
        forecasts = []
        
        # Use monthly totals to distribute bi-weekly
        if pattern.macro_pattern and pattern.macro_pattern['monthly_average'] > 0:
            monthly_total = pattern.macro_pattern['monthly_average']
            
            # Assume bi-weekly payments
            payment_amount = monthly_total / 2.17  # Average bi-weekly periods per month
            
            # Generate bi-weekly dates
            current_date = start_date
            # Find next Tuesday (common for contractor payments)
            while current_date.weekday() != 1:  # Tuesday
                current_date += timedelta(days=1)
            
            while current_date <= end_date:
                forecasts.append(ForecastRecord(
                    vendor_name=pattern.vendor_name,
                    forecast_date=current_date,
                    forecast_amount=payment_amount,
                    confidence=0.7,
                    method='contractor_aggregate',
                    amount_range=(payment_amount * 0.5, payment_amount * 1.5),
                    notes="Contractor payments (variable by period)"
                ))
                current_date += timedelta(weeks=2)
        
        return forecasts
    
    def _forecast_reorder_cycle(self, pattern: EnhancedPattern,
                              start_date: date, end_date: date) -> List[ForecastRecord]:
        """Inventory reorder cycle forecasting"""
        forecasts = []
        
        # Use quarterly patterns for inventory
        if pattern.macro_pattern and pattern.macro_pattern['quarterly_average'] > 0:
            quarterly_amount = pattern.macro_pattern['quarterly_average']
            
            # Assume one major order per quarter
            current_quarter_start = self._get_quarter_start(start_date)
            
            while current_quarter_start <= end_date:
                # Place order mid-quarter
                forecast_date = current_quarter_start + timedelta(days=45)
                
                if start_date <= forecast_date <= end_date:
                    forecasts.append(ForecastRecord(
                        vendor_name=pattern.vendor_name,
                        forecast_date=forecast_date,
                        forecast_amount=quarterly_amount,
                        confidence=0.6,
                        method='reorder_cycle',
                        amount_range=(quarterly_amount * 0.7, quarterly_amount * 1.3),
                        notes="Quarterly inventory reorder"
                    ))
                
                # Move to next quarter
                current_quarter_start = self._add_months(current_quarter_start, 3)
        
        return forecasts
    
    def _forecast_historical_average(self, pattern: EnhancedPattern,
                                   start_date: date, end_date: date) -> List[ForecastRecord]:
        """Fallback method using simple historical average"""
        forecasts = []
        
        # Use monthly average if available
        if pattern.macro_pattern and pattern.macro_pattern['monthly_average'] > 0:
            monthly_amount = pattern.macro_pattern['monthly_average']
            
            current_date = start_date
            while current_date <= end_date:
                # Mid-month forecast
                mid_month = date(current_date.year, current_date.month, 15)
                
                if start_date <= mid_month <= end_date:
                    forecasts.append(ForecastRecord(
                        vendor_name=pattern.vendor_name,
                        forecast_date=mid_month,
                        forecast_amount=monthly_amount,
                        confidence=0.5,
                        method='historical_average',
                        amount_range=(monthly_amount * 0.5, monthly_amount * 1.5),
                        notes="Based on historical monthly average"
                    ))
                
                current_date = self._add_month(current_date)
        
        return forecasts
    
    def _forecast_manual_required(self, pattern: EnhancedPattern,
                                start_date: date, end_date: date) -> List[ForecastRecord]:
        """No data available - return empty list"""
        return []
    
    def _generate_dates_from_timing(self, timing: TimingPattern,
                                  start_date: date, end_date: date) -> List[date]:
        """Generate forecast dates based on timing pattern"""
        dates = []
        
        if timing.next_expected_date and timing.next_expected_date >= start_date:
            current_date = timing.next_expected_date
        else:
            current_date = start_date
        
        if timing.frequency == 'daily':
            while current_date <= end_date:
                if current_date.weekday() < 5:  # Weekdays only
                    dates.append(current_date)
                current_date += timedelta(days=1)
        
        elif timing.frequency == 'weekly':
            # Find next occurrence of typical day
            if timing.typical_day:
                weekday_map = {
                    'Monday': 0, 'Tuesday': 1, 'Wednesday': 2,
                    'Thursday': 3, 'Friday': 4, 'Saturday': 5, 'Sunday': 6
                }
                target_weekday = weekday_map.get(timing.typical_day, 0)
                
                while current_date.weekday() != target_weekday:
                    current_date += timedelta(days=1)
            
            while current_date <= end_date:
                dates.append(current_date)
                current_date += timedelta(weeks=1)
        
        elif timing.frequency == 'bi-weekly':
            # Similar to weekly but every 2 weeks
            if timing.typical_day:
                weekday_map = {
                    'Monday': 0, 'Tuesday': 1, 'Wednesday': 2,
                    'Thursday': 3, 'Friday': 4, 'Saturday': 5, 'Sunday': 6
                }
                target_weekday = weekday_map.get(timing.typical_day, 0)
                
                while current_date.weekday() != target_weekday:
                    current_date += timedelta(days=1)
            
            while current_date <= end_date:
                dates.append(current_date)
                current_date += timedelta(weeks=2)
        
        elif timing.frequency == 'monthly':
            while current_date <= end_date:
                # Extract day from typical_day (e.g., "15th" -> 15)
                if timing.typical_day and 'th' in timing.typical_day:
                    try:
                        day = int(timing.typical_day.replace('th', ''))
                        forecast_date = date(current_date.year, current_date.month, day)
                    except:
                        forecast_date = date(current_date.year, current_date.month, 15)
                else:
                    forecast_date = date(current_date.year, current_date.month, 15)
                
                if start_date <= forecast_date <= end_date:
                    dates.append(forecast_date)
                
                current_date = self._add_month(current_date)
        
        elif timing.frequency == 'quarterly':
            while current_date <= end_date:
                dates.append(current_date)
                current_date = self._add_months(current_date, 3)
        
        elif timing.frequency == 'monthly_irregular':
            # Monthly but with some flexibility
            while current_date <= end_date:
                # Add some randomness ±5 days
                offset = random.randint(-5, 5)
                forecast_date = current_date + timedelta(days=offset)
                
                if start_date <= forecast_date <= end_date:
                    dates.append(forecast_date)
                
                current_date = self._add_month(current_date)
        
        return sorted(dates)
    
    def _add_month(self, date_obj: date) -> date:
        """Add one month to a date, handling edge cases"""
        if date_obj.month == 12:
            return date(date_obj.year + 1, 1, date_obj.day)
        else:
            try:
                return date(date_obj.year, date_obj.month + 1, date_obj.day)
            except ValueError:
                # Handle end of month
                return date(date_obj.year, date_obj.month + 1, 1) - timedelta(days=1)
    
    def _add_months(self, date_obj: date, months: int) -> date:
        """Add multiple months to a date"""
        result = date_obj
        for _ in range(months):
            result = self._add_month(result)
        return result
    
    def _get_quarter_start(self, date_obj: date) -> date:
        """Get the start date of the quarter containing the given date"""
        quarter = (date_obj.month - 1) // 3
        quarter_month = quarter * 3 + 1
        return date(date_obj.year, quarter_month, 1)
    
    def aggregate_weekly_forecasts(self, forecasts: List[ForecastRecord],
                                 start_date: date, weeks: int = 13) -> Dict[int, Dict[str, float]]:
        """Aggregate forecasts by week for dashboard display"""
        weekly_totals = {}
        
        for week_num in range(weeks):
            week_start = start_date + timedelta(weeks=week_num)
            week_end = week_start + timedelta(days=6)
            
            week_forecasts = [f for f in forecasts 
                            if week_start <= f.forecast_date <= week_end]
            
            weekly_totals[week_num] = {
                'total': sum(f.forecast_amount for f in week_forecasts),
                'count': len(week_forecasts),
                'confidence': statistics.mean([f.confidence for f in week_forecasts]) if week_forecasts else 0,
                'forecasts': week_forecasts
            }
        
        return weekly_totals

# Singleton instance
enhanced_forecast_generator = EnhancedForecastGenerator()

def test_forecast_generator():
    """Test the enhanced forecast generator"""
    print("🧪 Testing Enhanced Forecast Generator")
    print("=" * 80)
    
    # First get pattern analysis
    pattern = enhanced_pattern_detector_v2.analyze_vendor_pattern(
        client_id='bestself',
        vendor_group_name='Wise Transfers',
        display_names=['Wise Transfers']
    )
    
    # Generate forecasts
    forecasts = enhanced_forecast_generator.generate_forecasts(
        pattern=pattern,
        start_date=date(2025, 8, 4),
        weeks_ahead=13
    )
    
    # Aggregate by week
    weekly = enhanced_forecast_generator.aggregate_weekly_forecasts(
        forecasts, date(2025, 8, 4), 13
    )
    
    print("\n📅 Weekly Summary:")
    for week, data in weekly.items():
        if data['count'] > 0:
            print(f"   Week {week + 1}: ${data['total']:,.2f} ({data['count']} payments)")

if __name__ == "__main__":
    test_forecast_generator()