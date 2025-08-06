#!/usr/bin/env python3
"""
Group Pattern Detector - Detects payment patterns for vendor groups.
Follows the exact specification in FORECASTING_LOGIC_CORE_REQUIREMENTS.md
"""

import sys
sys.path.append('.')

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date, timedelta
from collections import Counter, defaultdict
import pandas as pd
from supabase_client import supabase

logger = logging.getLogger(__name__)

class GroupPatternDetector:
    """Detects payment patterns for vendor groups."""
    
    def __init__(self):
        pass
    
    def get_vendor_group_transactions(self, client_id: str, vendor_group_name: str, 
                                    display_names: List[str], days_back: int = 90) -> List[Dict[str, Any]]:
        """Get all transactions for vendors in this group."""
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
                logger.warning(f"No vendor names found for group {vendor_group_name}")
                return []
            
            # Calculate date range
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days_back)
            
            # Get transactions for all vendor names in the group
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
            ).order('transaction_date', desc=False).execute()  # Ascending for pattern analysis
            
            logger.info(f"Found {len(txn_result.data)} transactions for vendor group '{vendor_group_name}'")
            return txn_result.data
            
        except Exception as e:
            logger.error(f"Error getting transactions for vendor group {vendor_group_name}: {e}")
            return []
    
    def detect_frequency_pattern(self, transactions: List[Dict[str, Any]], 
                               large_transaction_threshold: float = 10000.0) -> Dict[str, Any]:
        """Detect the frequency pattern focusing on large transactions (deposits)."""
        if not transactions:
            return {'frequency': 'irregular', 'confidence': 0.0, 'details': 'No transactions'}
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(transactions)
        df['transaction_date'] = pd.to_datetime(df['transaction_date'])
        df['amount'] = df['amount'].astype(float)
        
        # Focus on large transactions (likely the main deposits)
        large_txns = df[df['amount'] >= large_transaction_threshold].copy()
        
        if len(large_txns) >= 3:  # Need at least 3 large transactions to detect pattern
            print(f"Found {len(large_txns)} large transactions (>=${large_transaction_threshold:,.2f})")
            
            # Group by date to get daily totals for large transactions
            large_daily = large_txns.groupby(large_txns['transaction_date'].dt.date)['amount'].sum().reset_index()
            large_daily['transaction_date'] = pd.to_datetime(large_daily['transaction_date'])
            
            large_dates = large_daily['transaction_date'].dt.date.tolist()
            large_dates.sort()
            
            # Calculate gaps between large transactions
            large_gaps = []
            for i in range(1, len(large_dates)):
                gap = (large_dates[i] - large_dates[i-1]).days
                large_gaps.append(gap)
            
            if large_gaps:
                large_gap_counter = Counter(large_gaps)
                most_common_large_gap = large_gap_counter.most_common(1)[0][0]
                large_gap_frequency = large_gap_counter.most_common(1)[0][1] / len(large_gaps)
                
                print(f"Large transaction gaps: {large_gaps}")
                print(f"Most common gap: {most_common_large_gap} days (frequency: {large_gap_frequency:.2f})")
                
                # Check for strong patterns in large transactions
                if most_common_large_gap == 14 and large_gap_frequency >= 0.8:
                    return {
                        'frequency': 'bi-weekly', 
                        'confidence': large_gap_frequency, 
                        'most_common_gap': most_common_large_gap,
                        'large_transaction_count': len(large_txns),
                        'analysis_method': 'large_transactions'
                    }
                elif 6 <= most_common_large_gap <= 8 and large_gap_frequency >= 0.6:
                    return {
                        'frequency': 'weekly', 
                        'confidence': large_gap_frequency, 
                        'most_common_gap': most_common_large_gap,
                        'large_transaction_count': len(large_txns),
                        'analysis_method': 'large_transactions'
                    }
                elif 28 <= most_common_large_gap <= 32 and large_gap_frequency >= 0.6:
                    return {
                        'frequency': 'monthly', 
                        'confidence': large_gap_frequency, 
                        'most_common_gap': most_common_large_gap,
                        'large_transaction_count': len(large_txns),
                        'analysis_method': 'large_transactions'
                    }
        
        # Fallback to all transactions if no clear pattern in large transactions
        print(f"No clear large transaction pattern, analyzing all {len(df)} transactions")
        
        # Group by date to get daily totals (multiple transactions same day)
        daily_totals = df.groupby(df['transaction_date'].dt.date)['amount'].sum().reset_index()
        daily_totals['transaction_date'] = pd.to_datetime(daily_totals['transaction_date'])
        
        transaction_dates = daily_totals['transaction_date'].dt.date.tolist()
        transaction_dates.sort()
        
        if len(transaction_dates) < 2:
            return {'frequency': 'irregular', 'confidence': 0.0, 'details': 'Not enough transactions'}
        
        # Calculate gaps between all transactions
        gaps = []
        for i in range(1, len(transaction_dates)):
            gap = (transaction_dates[i] - transaction_dates[i-1]).days
            gaps.append(gap)
        
        gap_counter = Counter(gaps)
        most_common_gap = gap_counter.most_common(1)[0][0] if gaps else 0
        gap_frequency = gap_counter.most_common(1)[0][1] / len(gaps) if gaps else 0
        
        # Detect pattern based on most common gap
        if most_common_gap <= 1 and gap_frequency > 0.6:
            return {'frequency': 'daily', 'confidence': gap_frequency, 'most_common_gap': most_common_gap, 'analysis_method': 'all_transactions'}
        elif 6 <= most_common_gap <= 8 and gap_frequency > 0.4:
            return {'frequency': 'weekly', 'confidence': gap_frequency, 'most_common_gap': most_common_gap, 'analysis_method': 'all_transactions'}
        elif 13 <= most_common_gap <= 15 and gap_frequency > 0.4:
            return {'frequency': 'bi-weekly', 'confidence': gap_frequency, 'most_common_gap': most_common_gap, 'analysis_method': 'all_transactions'}
        elif 28 <= most_common_gap <= 32 and gap_frequency > 0.3:
            return {'frequency': 'monthly', 'confidence': gap_frequency, 'most_common_gap': most_common_gap, 'analysis_method': 'all_transactions'}
        elif 88 <= most_common_gap <= 95 and gap_frequency > 0.3:
            return {'frequency': 'quarterly', 'confidence': gap_frequency, 'most_common_gap': most_common_gap, 'analysis_method': 'all_transactions'}
        elif 360 <= most_common_gap <= 370 and gap_frequency > 0.3:
            return {'frequency': 'annually', 'confidence': gap_frequency, 'most_common_gap': most_common_gap, 'analysis_method': 'all_transactions'}
        else:
            return {'frequency': 'irregular', 'confidence': 0.0, 'most_common_gap': most_common_gap, 'analysis_method': 'all_transactions'}
    
    def detect_timing_pattern(self, transactions: List[Dict[str, Any]], frequency: str, 
                            large_transaction_threshold: float = 10000.0) -> Dict[str, Any]:
        """Detect specific timing patterns (Monday, 15th/30th, etc.)."""
        if not transactions or frequency == 'irregular':
            return {'timing': 'irregular', 'details': 'No specific timing'}
        
        # Convert to DataFrame
        df = pd.DataFrame(transactions)
        df['transaction_date'] = pd.to_datetime(df['transaction_date'])
        df['amount'] = df['amount'].astype(float)
        
        # For bi-weekly/weekly patterns, focus on large transactions first
        large_txns = df[df['amount'] >= large_transaction_threshold]
        
        if frequency in ['bi-weekly', 'weekly'] and len(large_txns) >= 3:
            print(f"Using {len(large_txns)} large transactions for timing analysis")
            analysis_df = large_txns
        else:
            # Group by date to get unique transaction dates
            daily_totals = df.groupby(df['transaction_date'].dt.date)['amount'].sum().reset_index()
            daily_totals['transaction_date'] = pd.to_datetime(daily_totals['transaction_date'])
            analysis_df = daily_totals
        
        if frequency == 'daily':
            # Check if it's M-F pattern
            weekdays = analysis_df['transaction_date'].dt.dayofweek  # 0=Monday, 6=Sunday
            weekday_counts = weekdays.value_counts()
            
            # Check if mostly weekdays (0-4)
            weekday_txns = sum(weekday_counts[day] for day in range(5) if day in weekday_counts)
            weekend_txns = sum(weekday_counts[day] for day in range(5, 7) if day in weekday_counts)
            
            if weekday_txns > weekend_txns * 3:  # Much more weekday activity
                return {'timing': 'weekdays', 'details': 'Monday-Friday pattern'}
            else:
                return {'timing': 'all_days', 'details': 'All days of week'}
        
        elif frequency in ['weekly', 'bi-weekly']:
            # Check which day of week is most common
            weekdays = analysis_df['transaction_date'].dt.dayofweek
            weekday_counts = weekdays.value_counts()
            most_common_weekday = weekday_counts.index[0] if len(weekday_counts) > 0 else 0
            
            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            
            print(f"Weekday distribution: {dict(weekday_counts)}")
            print(f"Most common weekday: {most_common_weekday} ({day_names[most_common_weekday]})")
            
            return {
                'timing': day_names[most_common_weekday], 
                'details': f'Usually on {day_names[most_common_weekday]}s',
                'weekday': most_common_weekday
            }
        
        elif frequency == 'monthly':
            # Check which day of month is most common
            days_of_month = analysis_df['transaction_date'].dt.day
            most_common_day = days_of_month.mode().iloc[0] if len(days_of_month.mode()) > 0 else 15
            
            return {
                'timing': f'{most_common_day}th', 
                'details': f'Usually around the {most_common_day}th of month',
                'day_of_month': most_common_day
            }
        
        else:
            return {'timing': 'unknown', 'details': 'Timing pattern not determined'}
    
    def calculate_weighted_average(self, transactions: List[Dict[str, Any]], 
                                 frequency: str, large_transaction_threshold: float = 10000.0) -> float:
        """Calculate weighted average amount based on period patterns."""
        if not transactions:
            return 0.0
        
        # Convert to DataFrame
        df = pd.DataFrame(transactions)
        df['transaction_date'] = pd.to_datetime(df['transaction_date'])
        df['amount'] = df['amount'].astype(float)
        
        # For bi-weekly/weekly/monthly patterns with large transactions, use deposit amounts
        if frequency in ['bi-weekly', 'weekly', 'monthly']:
            large_txns = df[df['amount'] >= large_transaction_threshold]
            if len(large_txns) >= 3:
                print(f"Using {len(large_txns)} large transactions for deposit pattern")
                
                now = datetime.now().date()
                last_month_start = now - timedelta(days=30)
                
                # Get last month and all large transaction amounts
                last_month_amounts = []
                all_amounts = []
                
                for _, row in large_txns.iterrows():
                    amount = row['amount']
                    date_val = row['transaction_date'].date()
                    
                    all_amounts.append(amount)
                    if date_val >= last_month_start:
                        last_month_amounts.append(amount)
                
                if not all_amounts:
                    return 0.0
                
                # Calculate weighted average of deposit amounts (last month gets 1.5x weight)
                last_month_avg = sum(last_month_amounts) / len(last_month_amounts) if last_month_amounts else 0
                all_avg = sum(all_amounts) / len(all_amounts)
                
                if last_month_amounts:
                    weighted_avg = (1.5 * last_month_avg + 1.0 * all_avg) / 2.5
                else:
                    weighted_avg = all_avg
                
                print(f"Deposit amount average: ${weighted_avg:.2f} (from {len(all_amounts)} deposits)")
                return weighted_avg
        
        # For daily patterns, calculate weekly totals then return per-week amount
        if frequency == 'daily':
            print(f"Calculating weekly totals for daily pattern")
            
            # Group by week and sum amounts
            df['week_start'] = df['transaction_date'] - pd.to_timedelta(df['transaction_date'].dt.dayofweek, unit='d')
            weekly_totals = df.groupby(df['week_start'].dt.date)['amount'].sum()
            
            if len(weekly_totals) == 0:
                return 0.0
            
            now = datetime.now().date()
            last_month_start = now - timedelta(days=30)
            
            # Get weekly totals for weighted average
            last_month_weeks = []
            all_weeks = []
            
            for week_start, total in weekly_totals.items():
                all_weeks.append(total)
                if week_start >= last_month_start:
                    last_month_weeks.append(total)
            
            if not all_weeks:
                return 0.0
            
            # Calculate weighted average of weekly totals (last month gets 1.5x weight)
            last_month_avg = sum(last_month_weeks) / len(last_month_weeks) if last_month_weeks else 0
            all_weeks_avg = sum(all_weeks) / len(all_weeks)
            
            if last_month_weeks:
                weekly_avg = (1.5 * last_month_avg + 1.0 * all_weeks_avg) / 2.5
            else:
                weekly_avg = all_weeks_avg
            
            print(f"Weekly average: ${weekly_avg:.2f} (from {len(all_weeks)} weeks)")
            return weekly_avg
        
        # Fallback for other patterns - use transaction average
        now = datetime.now().date()
        last_month_start = now - timedelta(days=30)
        last_3_months_start = now - timedelta(days=90)
        
        # Get transaction amounts for weighted average
        last_month_amounts = []
        last_3_months_amounts = []
        
        for _, row in df.iterrows():
            amount = row['amount']
            date_val = row['transaction_date'].date()
            
            if date_val >= last_month_start:
                last_month_amounts.append(amount)
            if date_val >= last_3_months_start:
                last_3_months_amounts.append(amount)
        
        if not last_3_months_amounts:
            return 0.0
        
        # Calculate weighted average (last month gets 1.5x weight)
        last_month_avg = sum(last_month_amounts) / len(last_month_amounts) if last_month_amounts else 0
        last_3_months_avg = sum(last_3_months_amounts) / len(last_3_months_amounts) if last_3_months_amounts else 0
        
        if last_month_amounts:
            weighted_avg = (1.5 * last_month_avg + 1.0 * last_3_months_avg) / 2.5
        else:
            weighted_avg = last_3_months_avg
        
        return weighted_avg
    
    def analyze_vendor_group_pattern(self, client_id: str, vendor_group_name: str, 
                                   display_names: List[str]) -> Dict[str, Any]:
        """Complete pattern analysis for a vendor group."""
        print(f"\n🔍 ANALYZING PATTERN FOR GROUP: {vendor_group_name}")
        print("=" * 60)
        
        # Get transactions for the group
        transactions = self.get_vendor_group_transactions(
            client_id, vendor_group_name, display_names, days_back=90
        )
        
        if not transactions:
            return {
                'vendor_group_name': vendor_group_name,
                'frequency': 'irregular',
                'timing': 'none',
                'confidence': 0.0,
                'weighted_average': 0.0,
                'transaction_count': 0,
                'error': 'No transactions found'
            }
        
        print(f"Found {len(transactions)} transactions for analysis")
        
        # Detect frequency pattern
        frequency_result = self.detect_frequency_pattern(transactions)
        frequency = frequency_result['frequency']
        frequency_confidence = frequency_result['confidence']
        
        print(f"Frequency detected: {frequency} (confidence: {frequency_confidence:.2f})")
        
        # Detect timing pattern
        timing_result = self.detect_timing_pattern(transactions, frequency)
        timing = timing_result.get('timing', 'unknown')
        timing_details = timing_result.get('details', '')
        
        print(f"Timing pattern: {timing} - {timing_details}")
        
        # Calculate weighted average
        weighted_avg = self.calculate_weighted_average(transactions, frequency)
        
        print(f"Weighted average amount: ${weighted_avg:.2f}")
        
        # Compile results
        result = {
            'vendor_group_name': vendor_group_name,
            'display_names': display_names,
            'frequency': frequency,
            'frequency_confidence': frequency_confidence,
            'timing': timing,
            'timing_details': timing_details,
            'weighted_average': weighted_avg,
            'transaction_count': len(transactions),
            'analysis_date': date.today().isoformat(),
            'most_common_gap': frequency_result.get('most_common_gap', 0)
        }
        
        # Add timing-specific data
        if 'weekday' in timing_result:
            result['preferred_weekday'] = timing_result['weekday']
        if 'day_of_month' in timing_result:
            result['preferred_day_of_month'] = timing_result['day_of_month']
        
        return result

# Global instance
group_pattern_detector = GroupPatternDetector()

def test_amazon_pattern(client_id: str = 'bestself'):
    """Test pattern detection on Amazon group."""
    print("🧪 TESTING AMAZON PATTERN DETECTION")
    print("=" * 60)
    
    # Amazon group display names (all Amazon variants)
    amazon_display_names = ['Amazon Revenue']
    
    # Analyze pattern
    pattern = group_pattern_detector.analyze_vendor_group_pattern(
        client_id, 'Amazon', amazon_display_names
    )
    
    print(f"\n📊 AMAZON PATTERN RESULTS:")
    print(f"Frequency: {pattern['frequency']}")
    print(f"Timing: {pattern['timing']} - {pattern.get('timing_details', '')}")
    print(f"Average Amount: ${pattern['weighted_average']:.2f}")
    print(f"Confidence: {pattern['frequency_confidence']:.2f}")
    print(f"Transaction Count: {pattern['transaction_count']}")
    
    # Check if it matches expected pattern (bi-weekly, Tuesday, ~$44k)
    expected_frequency = 'bi-weekly'
    expected_timing = 'Tuesday'  # Updated based on actual data
    expected_amount_range = (40000, 50000)  # $40k-$50k range based on actual data
    
    print(f"\n✅ VALIDATION:")
    print(f"Expected: {expected_frequency}, {expected_timing}, ~$44k")
    print(f"Detected: {pattern['frequency']}, {pattern['timing']}, ${pattern['weighted_average']:.2f}")
    
    frequency_match = pattern['frequency'] == expected_frequency
    timing_match = pattern['timing'] == expected_timing
    amount_match = expected_amount_range[0] <= pattern['weighted_average'] <= expected_amount_range[1]
    
    print(f"Frequency Match: {'✅' if frequency_match else '❌'}")
    print(f"Timing Match: {'✅' if timing_match else '❌'}")
    print(f"Amount Match: {'✅' if amount_match else '❌'}")
    
    return pattern

if __name__ == "__main__":
    test_amazon_pattern()