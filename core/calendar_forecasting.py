"""
Calendar-Based Forecasting Engine
Generates actual calendar dates for predictions instead of static weekly buckets.
"""

import logging
from datetime import datetime, timedelta, UTC
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
import calendar
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ForecastEvent:
    """Represents a single forecast event on a specific date."""
    date: datetime
    vendor_display_name: str
    amount: float
    event_type: str  # 'recurring', 'override', 'one_time'
    frequency: str   # 'monthly', 'weekly', 'bi_weekly', 'daily'
    confidence: float
    source: str      # 'pattern_detected', 'manual_override', 'manual_entry'

class CalendarForecaster:
    """Generates calendar-based forecasts using vendor patterns and overrides."""
    
    def __init__(self):
        self.events = []
        
    def generate_monthly_events(
        self, 
        display_name: str, 
        amount: float, 
        day_of_month: int, 
        start_date: datetime, 
        end_date: datetime,
        confidence: float = 1.0
    ) -> List[ForecastEvent]:
        """Generate monthly recurring events on specific day of month."""
        events = []
        current_date = start_date.replace(day=1)  # Start at beginning of month
        
        while current_date <= end_date:
            try:
                # Handle month-end dates (e.g., if day_of_month=31 but Feb only has 28)
                max_day = calendar.monthrange(current_date.year, current_date.month)[1]
                actual_day = min(day_of_month, max_day)
                
                event_date = current_date.replace(day=actual_day)
                
                if start_date <= event_date <= end_date:
                    events.append(ForecastEvent(
                        date=event_date,
                        vendor_display_name=display_name,
                        amount=amount,
                        event_type='recurring',
                        frequency='monthly',
                        confidence=confidence,
                        source='pattern_detected'
                    ))
                
                # Move to next month
                if current_date.month == 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=1)
                else:
                    current_date = current_date.replace(month=current_date.month + 1)
                    
            except ValueError as e:
                logger.warning(f"Date calculation error for {display_name}: {e}")
                break
        
        logger.info(f"Generated {len(events)} monthly events for {display_name} on day {day_of_month}")
        return events
    
    def generate_weekly_events(
        self, 
        display_name: str, 
        amount: float, 
        day_of_week: int, 
        start_date: datetime, 
        end_date: datetime,
        confidence: float = 1.0
    ) -> List[ForecastEvent]:
        """Generate weekly recurring events on specific day of week."""
        events = []
        
        # Find first occurrence of the target weekday
        days_ahead = day_of_week - start_date.isoweekday()
        if days_ahead < 0:
            days_ahead += 7
        
        current_date = start_date + timedelta(days=days_ahead)
        
        while current_date <= end_date:
            events.append(ForecastEvent(
                date=current_date,
                vendor_display_name=display_name,
                amount=amount,
                event_type='recurring',
                frequency='weekly',
                confidence=confidence,
                source='pattern_detected'
            ))
            
            current_date += timedelta(days=7)
        
        day_names = {1: 'Monday', 2: 'Tuesday', 3: 'Wednesday', 4: 'Thursday', 
                    5: 'Friday', 6: 'Saturday', 7: 'Sunday'}
        logger.info(f"Generated {len(events)} weekly events for {display_name} on {day_names[day_of_week]}s")
        return events
    
    def generate_bi_weekly_events(
        self, 
        display_name: str, 
        amount: float, 
        day_of_week: int, 
        start_date: datetime, 
        end_date: datetime,
        reference_date: Optional[datetime] = None,
        confidence: float = 1.0
    ) -> List[ForecastEvent]:
        """Generate bi-weekly recurring events (every 2 weeks on specific day)."""
        events = []
        
        if reference_date:
            # Use reference date to maintain the bi-weekly cycle
            current_date = reference_date
            # Find next occurrence after start_date
            while current_date < start_date:
                current_date += timedelta(days=14)
        else:
            # Find first occurrence of the target weekday
            days_ahead = day_of_week - start_date.isoweekday()
            if days_ahead < 0:
                days_ahead += 7
            current_date = start_date + timedelta(days=days_ahead)
        
        while current_date <= end_date:
            if current_date >= start_date:
                events.append(ForecastEvent(
                    date=current_date,
                    vendor_display_name=display_name,
                    amount=amount,
                    event_type='recurring',
                    frequency='bi_weekly',
                    confidence=confidence,
                    source='pattern_detected'
                ))
            
            current_date += timedelta(days=14)
        
        day_names = {1: 'Monday', 2: 'Tuesday', 3: 'Wednesday', 4: 'Thursday', 
                    5: 'Friday', 6: 'Saturday', 7: 'Sunday'}
        logger.info(f"Generated {len(events)} bi-weekly events for {display_name} on {day_names[day_of_week]}s")
        return events
    
    def generate_daily_events(
        self, 
        display_name: str, 
        amount: float, 
        start_date: datetime, 
        end_date: datetime,
        weekdays_only: bool = True,
        confidence: float = 1.0
    ) -> List[ForecastEvent]:
        """Generate daily recurring events."""
        events = []
        current_date = start_date
        
        while current_date <= end_date:
            # Skip weekends if weekdays_only is True
            if not weekdays_only or current_date.isoweekday() <= 5:
                events.append(ForecastEvent(
                    date=current_date,
                    vendor_display_name=display_name,
                    amount=amount,
                    event_type='recurring',
                    frequency='daily',
                    confidence=confidence,
                    source='pattern_detected'
                ))
            
            current_date += timedelta(days=1)
        
        frequency_desc = "weekdays" if weekdays_only else "daily"
        logger.info(f"Generated {len(events)} {frequency_desc} events for {display_name}")
        return events
    
    def generate_forecast_events(
        self, 
        vendors: List[Dict[str, Any]], 
        start_date: datetime, 
        end_date: datetime
    ) -> List[ForecastEvent]:
        """
        Generate all forecast events for a list of vendors.
        
        Args:
            vendors: List of vendor configs with forecast parameters
            start_date: Forecast start date
            end_date: Forecast end date
            
        Returns:
            List of ForecastEvent objects
        """
        all_events = []
        
        for vendor in vendors:
            display_name = vendor.get('display_name')
            frequency = vendor.get('forecast_frequency', 'irregular')
            amount = vendor.get('forecast_amount', 0)
            day = vendor.get('forecast_day')
            confidence = vendor.get('forecast_confidence', 0.0)
            
            if not display_name or not amount or frequency == 'irregular':
                continue
            
            logger.info(f"Generating events for {display_name}: {frequency}, day {day}, ${amount}")
            
            try:
                if frequency == 'monthly' and day:
                    events = self.generate_monthly_events(
                        display_name, amount, day, start_date, end_date, confidence
                    )
                elif frequency == 'weekly' and day:
                    events = self.generate_weekly_events(
                        display_name, amount, day, start_date, end_date, confidence
                    )
                elif frequency == 'bi_weekly' and day:
                    events = self.generate_bi_weekly_events(
                        display_name, amount, day, start_date, end_date, confidence=confidence
                    )
                elif frequency == 'daily':
                    events = self.generate_daily_events(
                        display_name, amount, start_date, end_date, confidence=confidence
                    )
                elif frequency == 'daily_weekly':
                    # For daily patterns like Shopify, generate weekly summary events
                    events = self.generate_weekly_events(
                        display_name, amount, 1, start_date, end_date, confidence=confidence  # Default to Monday
                    )
                else:
                    logger.warning(f"Skipping {display_name}: unsupported frequency {frequency} or missing day")
                    continue
                    
                all_events.extend(events)
                
            except Exception as e:
                logger.error(f"Error generating events for {display_name}: {e}")
                continue
        
        # Sort events by date
        all_events.sort(key=lambda x: x.date)
        logger.info(f"Generated {len(all_events)} total forecast events")
        return all_events
    
    def events_to_weekly_summary(
        self, 
        events: List[ForecastEvent], 
        start_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Convert events into weekly summary format for display.
        
        Args:
            events: List of ForecastEvent objects
            start_date: Start date for weekly periods
            
        Returns:
            List of weekly summary dictionaries
        """
        # Group events by week
        weekly_events = defaultdict(list)
        
        for event in events:
            # Calculate which week this event belongs to
            days_diff = (event.date - start_date).days
            week_number = days_diff // 7
            weekly_events[week_number].append(event)
        
        # Create weekly summaries
        weekly_summaries = []
        current_week_start = start_date
        
        # Generate summaries for each week
        max_weeks = 13  # Default to 13 weeks
        if weekly_events:
            max_weeks = max(max_weeks, max(weekly_events.keys()) + 1)
        
        for week_num in range(max_weeks):
            week_start = current_week_start + timedelta(days=week_num * 7)
            week_end = week_start + timedelta(days=6)
            
            week_events = weekly_events.get(week_num, [])
            
            total_deposits = sum(e.amount for e in week_events if e.amount > 0)
            total_withdrawals = abs(sum(e.amount for e in week_events if e.amount < 0))
            net_movement = total_deposits - total_withdrawals
            
            weekly_summaries.append({
                'week_number': week_num + 1,
                'start_date': week_start,
                'end_date': week_end,
                'period_str': f"{week_start.strftime('%m/%d')} - {week_end.strftime('%m/%d')}",
                'deposits': total_deposits,
                'withdrawals': total_withdrawals,
                'net_movement': net_movement,
                'events': week_events,
                'event_count': len(week_events)
            })
        
        return weekly_summaries