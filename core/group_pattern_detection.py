#!/usr/bin/env python3
"""
Pattern Detection on Logical Vendor Groups
Performs pattern detection on aggregated vendor groups instead of individual vendors.
"""

import logging
from datetime import datetime, timedelta, UTC
from typing import List, Dict, Any, Optional
from collections import Counter
import statistics
from supabase_client import supabase
from core.pattern_detection import (
    parse_date, analyze_transaction_history, detect_bi_weekly_pattern,
    detect_daily_pattern, calculate_bi_weekly_amount, calculate_daily_weekly_amount,
    calculate_monthly_amount, calculate_weekly_amount, calculate_trailing_average
)

logger = logging.getLogger(__name__)

class GroupPatternDetector:
    """Pattern detection on logical vendor groups."""
    
    def __init__(self):
        self.client_id = None
    
    def get_vendor_groups(self, client_id: str) -> List[Dict[str, Any]]:
        """Get all vendor groups for a client."""
        try:
            # Try to read from JSON config file first
            import json
            import os
            
            config_file = 'vendor_groups_config.json'
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                client_groups = config.get(client_id, {})
                groups = []
                
                for group_name, group_data in client_groups.items():
                    groups.append({
                        'group_name': group_name,
                        'vendor_display_names': group_data['vendor_display_names'],
                        'is_revenue': group_data.get('is_revenue', True),
                        'category': group_data.get('category', 'Revenue'),
                        'forecast_frequency': None,
                        'forecast_amount': 0.0,
                        'forecast_confidence': 0.0
                    })
                
                logger.info(f"Loaded {len(groups)} vendor groups from config file")
                return groups
            
            # Fallback to database if config file doesn't exist
            result = supabase.table('vendor_groups').select('*').eq(
                'client_id', client_id
            ).execute()
            return result.data
            
        except Exception as e:
            logger.warning(f"vendor_groups not available, falling back to individual vendors: {e}")
            return self._fallback_to_individual_vendors(client_id)
    
    def _fallback_to_individual_vendors(self, client_id: str) -> List[Dict[str, Any]]:
        """Fallback to individual vendor approach if groups table doesn't exist."""
        try:
            result = supabase.table('vendors').select(
                'display_name, is_revenue, category'
            ).eq('client_id', client_id).neq('display_name', None).execute()
            
            # Convert individual vendors to "groups" of one
            groups = []
            for vendor in result.data:
                groups.append({
                    'group_name': vendor['display_name'],
                    'vendor_display_names': [vendor['display_name']],
                    'is_revenue': vendor.get('is_revenue', True),
                    'category': vendor.get('category', 'Revenue'),
                    'forecast_frequency': None,
                    'forecast_amount': 0.0,
                    'forecast_confidence': 0.0
                })
            
            logger.info(f"Using fallback mode: {len(groups)} individual vendors as groups")
            return groups
            
        except Exception as e:
            logger.error(f"Error in fallback vendor detection: {e}")
            return []
    
    def get_group_transactions(self, group: Dict[str, Any], client_id: str, 
                             lookback_days: int = 365) -> List[Dict[str, Any]]:
        """Get all transactions for a vendor group."""
        vendor_display_names = group.get('vendor_display_names', [])
        if not vendor_display_names:
            return []
        
        try:
            # Calculate date range
            end_date = datetime.now(UTC)
            start_date = end_date - timedelta(days=lookback_days)
            
            all_transactions = []
            
            for display_name in vendor_display_names:
                # Get vendor names that map to this display name
                vendor_result = supabase.table('vendors').select('vendor_name').eq(
                    'client_id', client_id
                ).eq('display_name', display_name).execute()
                
                if not vendor_result.data:
                    continue
                
                vendor_names = [v['vendor_name'] for v in vendor_result.data]
                
                # Get transactions for these vendor names
                txn_result = supabase.table('transactions').select(
                    'transaction_date, amount, vendor_name'
                ).eq(
                    'client_id', client_id
                ).in_(
                    'vendor_name', vendor_names
                ).gte(
                    'transaction_date', start_date.isoformat()
                ).lte(
                    'transaction_date', end_date.isoformat()
                ).execute()
                
                all_transactions.extend(txn_result.data)
            
            logger.info(f"Found {len(all_transactions)} transactions for group '{group['group_name']}'")
            return all_transactions
            
        except Exception as e:
            logger.error(f"Error getting transactions for group {group['group_name']}: {e}")
            return []
    
    def classify_group_pattern(self, group: Dict[str, Any], client_id: str) -> Dict[str, Any]:
        """
        Classify vendor group based on aggregated transaction patterns.
        
        Args:
            group: Vendor group data
            client_id: Client ID
            
        Returns:
            Dict with classification results
        """
        group_name = group['group_name']
        transactions = self.get_group_transactions(group, client_id)
        
        if not transactions:
            return {
                'group_name': group_name,
                'frequency': 'irregular',
                'forecast_day': None,
                'forecast_amount': 0.0,
                'confidence': 0.0,
                'explanation': 'No transactions found',
                'transaction_count': 0
            }
        
        # Analyze aggregated transaction patterns
        stats = analyze_transaction_history(transactions)
        num_months = len(stats['months'])
        num_weeks = len(stats['weeks'])
        
        logger.info(f"Group '{group_name}': {len(transactions)} transactions, {num_months} months, {num_weeks} weeks")
        
        # Check for daily pattern first (like Shopify group)
        daily_result = detect_daily_pattern(transactions)
        
        if daily_result and daily_result['confidence'] >= 0.4:
            # Daily pattern detected - roll up to weekly
            frequency = 'daily_weekly'
            forecast_day = None
            confidence = daily_result['confidence']
            explanation = f"Daily pattern (group): {daily_result['explanation']}"
            
            # Calculate weekly amount from daily pattern
            forecast_amount = calculate_daily_weekly_amount(transactions, client_id)
            
        elif bi_weekly_result := detect_bi_weekly_pattern(transactions):
            if bi_weekly_result['confidence'] >= 0.6:
                # Strong bi-weekly pattern detected
                frequency = 'bi_weekly'
                forecast_day = bi_weekly_result['day_of_week']
                confidence = bi_weekly_result['confidence']
                explanation = f"Bi-weekly pattern (group): {bi_weekly_result['explanation']}"
                
                # Calculate amount based on bi-weekly pattern
                forecast_amount = calculate_bi_weekly_amount(transactions)
        
        elif num_months >= 6:  # MONTHLY_MIN_MONTHS
            # Monthly pattern detected
            frequency = 'monthly'
            forecast_day = stats['dom'].most_common(1)[0][0]
            confidence = min(num_months / 6, 1.0)
            explanation = f"Monthly pattern (group): pays on {forecast_day}th of month ({num_months} months)"
            
            # For monthly patterns, use appropriate amount calculation
            forecast_amount = calculate_monthly_amount(transactions, client_id)
            
        elif len(transactions) >= 4:
            # Weekly pattern detected  
            frequency = 'weekly'
            forecast_day = stats['dow'].most_common(1)[0][0]
            expected_weeks = 180 / 7  # LOOKBACK_DAYS
            confidence = min(num_weeks / expected_weeks, 1.0)
            
            # Day names for explanation
            day_names = {1: 'Monday', 2: 'Tuesday', 3: 'Wednesday', 4: 'Thursday', 
                        5: 'Friday', 6: 'Saturday', 7: 'Sunday'}
            explanation = f"Weekly pattern (group): pays on {day_names[forecast_day]}s ({num_weeks} weeks)"
            
            # For weekly patterns, use appropriate amount calculation
            forecast_amount = calculate_weekly_amount(transactions, client_id)
            
        else:
            # Irregular pattern
            frequency = 'irregular'
            if sum(stats['dom'].values()) >= 2:  # IRREGULAR_MIN_OCCURRENCES
                forecast_day = stats['dom'].most_common(1)[0][0]
                confidence = stats['dom'][forecast_day] / sum(stats['dom'].values())
                explanation = f"Irregular pattern (group): most often on {forecast_day}th ({confidence:.1%} of time)"
            else:
                forecast_day = None
                confidence = 0.0
                explanation = "Irregular pattern (group): no clear day preference"
                
            # For irregular patterns, use trailing average
            forecast_amount = calculate_trailing_average(transactions, client_id)
        
        logger.info(f"Group '{group_name}': {frequency}, Day: {forecast_day}, Amount: ${forecast_amount}, Confidence: {confidence:.2f}")
        
        return {
            'group_name': group_name,
            'frequency': frequency,
            'forecast_day': forecast_day,
            'forecast_amount': forecast_amount,
            'confidence': round(confidence, 2),
            'explanation': explanation,
            'months_active': num_months,
            'weeks_active': num_weeks,
            'transaction_count': len(transactions),
            'daily_analysis': daily_result if 'daily_result' in locals() else None,
            'bi_weekly_analysis': bi_weekly_result if 'bi_weekly_result' in locals() else None
        }
    
    def update_group_forecast_config(self, group_name: str, client_id: str, 
                                   pattern_result: Dict[str, Any]) -> bool:
        """Update vendor group forecast configuration."""
        try:
            update_data = {
                'forecast_frequency': pattern_result['frequency'],
                'forecast_day': pattern_result['forecast_day'],
                'forecast_amount': pattern_result['forecast_amount'],
                'forecast_confidence': pattern_result['confidence'],
                'forecast_method': 'pattern_detected',
                'updated_at': datetime.now(UTC).isoformat()
            }
            
            # Try to update vendor_groups table first
            try:
                result = supabase.table('vendor_groups').update(update_data).eq(
                    'client_id', client_id
                ).eq('group_name', group_name).execute()
                
                if result.data:
                    logger.info(f"Updated group forecast config for {group_name}: {pattern_result['explanation']}")
                    return True
                else:
                    # Fallback to updating individual vendors
                    return self._fallback_update_individual_vendors(group_name, client_id, update_data)
                    
            except Exception:
                # Fallback to individual vendor updates
                return self._fallback_update_individual_vendors(group_name, client_id, update_data)
                
        except Exception as e:
            logger.error(f"Error updating group config for {group_name}: {e}")
            return False
    
    def _fallback_update_individual_vendors(self, group_name: str, client_id: str, 
                                          update_data: Dict[str, Any]) -> bool:
        """Fallback to updating individual vendor records."""
        try:
            # In fallback mode, group_name is the same as display_name
            result = supabase.table('vendors').update(update_data).eq(
                'client_id', client_id
            ).eq('display_name', group_name).execute()
            
            if result.data:
                logger.info(f"Updated vendor forecast config for {group_name} (fallback mode)")
                return True
            else:
                logger.warning(f"No vendors updated for {group_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error in fallback update for {group_name}: {e}")
            return False
    
    def process_all_groups(self, client_id: str) -> Dict[str, Any]:
        """Process pattern detection for all vendor groups."""
        groups = self.get_vendor_groups(client_id)
        
        results = {
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'group_results': []
        }
        
        logger.info(f"Processing {len(groups)} vendor groups for pattern detection")
        
        for group in groups:
            group_name = group['group_name']
            
            try:
                logger.info(f"Processing {group_name}...")
                
                # Classify the group pattern
                pattern_result = self.classify_group_pattern(group, client_id)
                
                # Update the forecast configuration
                success = self.update_group_forecast_config(group_name, client_id, pattern_result)
                
                results['processed'] += 1
                if success:
                    results['successful'] += 1
                else:
                    results['failed'] += 1
                
                results['group_results'].append({
                    'group_name': group_name,
                    'success': success,
                    'pattern': pattern_result
                })
                
            except Exception as e:
                logger.error(f"Error processing group {group_name}: {e}")
                results['processed'] += 1
                results['failed'] += 1
        
        logger.info(f"Group pattern detection complete: {results['successful']}/{results['processed']} successful")
        return results

# Global instance for easy import
group_pattern_detector = GroupPatternDetector()