#!/usr/bin/env python3
"""
Enhanced Pattern Detector with timing overrides and user-defined grouping.
"""

import sys
sys.path.append('.')

from typing import Dict, List, Any, Optional
from datetime import datetime, date
import pandas as pd
import numpy as np
from supabase_client import supabase
import logging

logger = logging.getLogger(__name__)

class EnhancedPatternDetector:
    """Enhanced pattern detection with vendor-specific overrides and user grouping."""
    
    def __init__(self):
        # Vendor-specific timing overrides
        self.timing_overrides = {
            'Amazon Revenue': {
                'detected_day': 'Tuesday',
                'preferred_day': 'Monday',
                'reason': 'User preference - forecast on Monday instead of actual Tuesday deposits'
            }
        }
        
        # User-defined vendor groupings
        self.user_defined_groups = {
            'E-commerce Revenue': {
                'display_names': ['BestSelf Revenue', 'Affirm Payments', 'Shopify Revenue'],
                'description': 'Combined e-commerce revenue streams',
                'is_revenue': True
            },
            'Amazon Deposits': {
                'display_names': ['Amazon Revenue'],
                'description': 'Amazon marketplace deposits',
                'is_revenue': True
            },
            'Payment Processing': {
                'display_names': ['Stripe Revenue', 'PayPal Revenue'],
                'description': 'Payment processor revenues',
                'is_revenue': True
            },
            'Contractor Payments': {
                'display_names': ['Wise Transfers'],
                'description': 'International contractor payments',
                'is_revenue': False
            },
            'Credit Card Payments': {
                'display_names': ['American Express Payments'],
                'description': 'Credit card payment expenses',
                'is_revenue': False
            }
        }
    
    def get_user_defined_groups(self, client_id: str) -> List[Dict[str, Any]]:
        """Get user-defined vendor groups for a client."""
        groups = []
        
        for group_name, config in self.user_defined_groups.items():
            groups.append({
                'client_id': client_id,
                'group_name': group_name,
                'vendor_display_names': config['display_names'],
                'description': config['description'],
                'is_revenue': config['is_revenue'],
                'is_user_defined': True
            })
        
        return groups
    
    def analyze_vendor_group_pattern_enhanced(self, client_id: str, group_name: str, 
                                            display_names: List[str]) -> Dict[str, Any]:
        """Enhanced pattern analysis with timing overrides."""
        try:
            logger.info(f"🔍 ENHANCED ANALYSIS FOR GROUP: {group_name}")
            logger.info("=" * 60)
            
            # Get transactions for all display names in the group
            all_transactions = []
            
            for display_name in display_names:
                # Get vendor names for this display name
                vendor_result = supabase.table('vendors').select('vendor_name').eq(
                    'client_id', client_id
                ).eq(
                    'display_name', display_name
                ).execute()
                
                if vendor_result.data:
                    vendor_names = [v['vendor_name'] for v in vendor_result.data]
                    
                    # Get transactions for these vendors
                    txn_result = supabase.table('transactions').select(
                        'transaction_date, amount, vendor_name'
                    ).eq(
                        'client_id', client_id
                    ).in_(
                        'vendor_name', vendor_names
                    ).execute()
                    
                    all_transactions.extend(txn_result.data)
            
            if not all_transactions:
                logger.warning(f"No transactions found for group {group_name}")
                return {
                    'frequency': 'irregular',
                    'frequency_confidence': 0.0,
                    'timing': 'irregular',
                    'weighted_average': 0.0,
                    'explanation': f'No transactions found for {group_name}'
                }
            
            logger.info(f"Found {len(all_transactions)} transactions for analysis")
            
            # Convert to DataFrame
            df = pd.DataFrame(all_transactions)
            df['transaction_date'] = pd.to_datetime(df['transaction_date'])
            df['amount'] = df['amount'].astype(float)
            df = df.sort_values('transaction_date')
            
            # Run pattern analysis
            pattern_result = self._detect_pattern_with_overrides(df, group_name)
            
            return pattern_result
            
        except Exception as e:
            logger.error(f"Error in enhanced pattern analysis: {e}")
            return {
                'frequency': 'irregular',
                'frequency_confidence': 0.0,
                'timing': 'irregular',
                'weighted_average': 0.0,
                'explanation': f'Error analyzing {group_name}: {str(e)}'
            }
    
    def _detect_pattern_with_overrides(self, df: pd.DataFrame, group_name: str) -> Dict[str, Any]:
        """Detect pattern with timing overrides applied."""
        
        # Step 1: Detect frequency pattern (same as before)
        large_threshold = 10000.0
        large_txns = df[df['amount'] >= large_threshold]
        
        if len(large_txns) >= 3:
            logger.info(f"Found {len(large_txns)} large transactions (>=${large_threshold:,.2f})")
            
            # Calculate gaps between large transactions
            gaps = []
            for i in range(1, len(large_txns)):
                gap = (large_txns.iloc[i]['transaction_date'] - large_txns.iloc[i-1]['transaction_date']).days
                gaps.append(gap)
            
            if gaps:
                logger.info(f"Large transaction gaps: {gaps}")
                most_common_gap = max(set(gaps), key=gaps.count)
                gap_consistency = gaps.count(most_common_gap) / len(gaps)
                
                logger.info(f"Most common gap: {most_common_gap} days (frequency: {gap_consistency:.2f})")
                
                # Determine frequency
                if most_common_gap == 14 and gap_consistency >= 0.7:
                    frequency = 'bi-weekly'
                    confidence = gap_consistency
                elif most_common_gap == 7 and gap_consistency >= 0.7:
                    frequency = 'weekly'
                    confidence = gap_consistency
                elif 28 <= most_common_gap <= 35 and gap_consistency >= 0.6:
                    frequency = 'monthly'
                    confidence = gap_consistency
                else:
                    frequency = 'irregular'
                    confidence = 0.0
        else:
            # Analyze all transactions for daily/weekly patterns
            logger.info(f"No clear large transaction pattern, analyzing all {len(df)} transactions")
            
            # Daily pattern detection
            df['weekday'] = df['transaction_date'].dt.weekday
            weekday_counts = df['weekday'].value_counts()
            
            # Check for weekday pattern (Mon-Fri)
            weekday_total = sum(weekday_counts.get(i, 0) for i in range(5))  # Mon-Fri
            weekend_total = sum(weekday_counts.get(i, 0) for i in range(5, 7))  # Sat-Sun
            
            if weekday_total > 0:
                weekday_ratio = weekday_total / (weekday_total + weekend_total)
                
                if weekday_ratio >= 0.8:
                    frequency = 'daily'
                    confidence = min(weekday_ratio, 0.9)
                elif len(set(df['transaction_date'].dt.date)) >= 3:
                    # Check for weekly pattern
                    df['week'] = df['transaction_date'].dt.isocalendar().week
                    weekly_counts = df.groupby('week').size()
                    if len(weekly_counts) >= 3 and weekly_counts.std() / weekly_counts.mean() < 0.5:
                        frequency = 'weekly'
                        confidence = min(0.8, 1.0 - (weekly_counts.std() / weekly_counts.mean()))
                    else:
                        frequency = 'irregular'
                        confidence = 0.0
                else:
                    frequency = 'irregular'
                    confidence = 0.0
            else:
                frequency = 'irregular'
                confidence = 0.0
        
        logger.info(f"Frequency detected: {frequency} (confidence: {confidence:.2f})")
        
        # Step 2: Detect timing with overrides
        timing_result = self._detect_timing_with_overrides(df, frequency, group_name)
        
        # Step 3: Calculate weighted average
        weighted_avg = self._calculate_weighted_average(df, frequency)
        
        logger.info(f"Weighted average amount: ${weighted_avg:,.2f}")
        
        return {
            'frequency': frequency,
            'frequency_confidence': confidence,
            'timing': timing_result['timing'],
            'timing_override': timing_result.get('override', False),
            'weighted_average': weighted_avg,
            'explanation': timing_result.get('explanation', ''),
            'transaction_count': len(df),
            'large_transaction_count': len(df[df['amount'] >= 10000.0])
        }
    
    def _detect_timing_with_overrides(self, df: pd.DataFrame, frequency: str, group_name: str) -> Dict[str, Any]:
        """Detect timing pattern with vendor-specific overrides."""
        
        # Check if this group has a timing override
        if group_name in self.timing_overrides:
            override_config = self.timing_overrides[group_name]
            logger.info(f"⚠️  Applying timing override for {group_name}")
            logger.info(f"   Detected: {override_config['detected_day']}")
            logger.info(f"   Override: {override_config['preferred_day']}")
            logger.info(f"   Reason: {override_config['reason']}")
            
            return {
                'timing': override_config['preferred_day'],
                'override': True,
                'explanation': f"Override: {override_config['reason']}",
                'detected_timing': override_config['detected_day']
            }
        
        # Default timing detection
        if frequency in ['bi-weekly', 'weekly']:
            # Analyze weekday patterns for large transactions
            large_txns = df[df['amount'] >= 10000.0] if len(df[df['amount'] >= 10000.0]) >= 3 else df
            
            if len(large_txns) > 0:
                weekday_counts = large_txns['transaction_date'].dt.weekday.value_counts()
                most_common_weekday = weekday_counts.index[0]
                
                weekday_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                timing = weekday_names[most_common_weekday]
                
                logger.info(f"Most common weekday: {most_common_weekday} ({timing})")
                return {
                    'timing': f"{timing} - Usually on {timing}s",
                    'override': False,
                    'explanation': f"Most transactions occur on {timing}s"
                }
        
        elif frequency == 'daily':
            # Check if it's weekdays only
            weekday_counts = df['transaction_date'].dt.weekday.value_counts()
            weekday_total = sum(weekday_counts.get(i, 0) for i in range(5))
            total_txns = len(df)
            
            if weekday_total / total_txns >= 0.8:
                return {
                    'timing': 'weekdays - Monday-Friday pattern',
                    'override': False,
                    'explanation': 'Transactions occur primarily on weekdays'
                }
        
        elif frequency == 'monthly':
            # Find most common day of month
            day_counts = df['transaction_date'].dt.day.value_counts()
            most_common_day = day_counts.index[0]
            
            return {
                'timing': f'{most_common_day}th - Usually around the {most_common_day}th of month',
                'override': False,
                'explanation': f'Most transactions occur around the {most_common_day}th of the month'
            }
        
        return {
            'timing': 'irregular - No specific timing',
            'override': False,
            'explanation': 'No clear timing pattern detected'
        }
    
    def _calculate_weighted_average(self, df: pd.DataFrame, frequency: str) -> float:
        """Calculate weighted average based on frequency."""
        
        if frequency == 'daily':
            # For daily patterns, calculate weekly totals
            df['week'] = df['transaction_date'].dt.isocalendar().week
            df['year'] = df['transaction_date'].dt.year
            weekly_groups = df.groupby(['year', 'week'])['amount'].sum()
            
            if len(weekly_groups) >= 3:
                # Weight recent weeks more heavily
                weights = np.linspace(0.5, 1.0, len(weekly_groups))
                weighted_avg = np.average(weekly_groups, weights=weights)
                logger.info(f"Calculating weekly totals for daily pattern")
                logger.info(f"Weekly average: ${weighted_avg:.2f} (from {len(weekly_groups)} weeks)")
                return weighted_avg
        
        elif frequency in ['bi-weekly', 'weekly', 'monthly']:
            # Use large transactions if available
            large_txns = df[df['amount'] >= 10000.0]
            
            if len(large_txns) >= 3:
                amounts = large_txns['amount'].values
                weights = np.linspace(0.5, 1.0, len(amounts))
                weighted_avg = np.average(amounts, weights=weights)
                logger.info(f"Using {len(large_txns)} large transactions for deposit pattern")
                logger.info(f"Deposit amount average: ${weighted_avg:.2f} (from {len(large_txns)} deposits)")
                return weighted_avg
        
        # Default: simple weighted average of all transactions
        amounts = df['amount'].values
        if len(amounts) > 0:
            weights = np.linspace(0.5, 1.0, len(amounts))
            return np.average(amounts, weights=weights)
        
        return 0.0

# Create global instance
enhanced_pattern_detector = EnhancedPatternDetector()