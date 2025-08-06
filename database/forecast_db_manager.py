#!/usr/bin/env python3
"""
Forecast Database Manager - CRUD operations for forecast tables.
"""

import sys
sys.path.append('.')

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, date
from supabase_client import supabase

logger = logging.getLogger(__name__)

class ForecastDBManager:
    """Manages database operations for forecasting."""
    
    def __init__(self):
        pass
    
    # VENDOR GROUPS CRUD
    
    def create_vendor_group(self, client_id: str, group_name: str,
                          vendor_display_names: List[str], pattern_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a new vendor group with optional pattern data."""
        try:
            group_data = {
                'client_id': client_id,
                'group_name': group_name,
                'vendor_display_names': vendor_display_names,
                'is_active': True,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # Add pattern data if provided
            if pattern_data:
                group_data.update({
                    'pattern_frequency': pattern_data.get('frequency'),
                    'pattern_timing': pattern_data.get('timing'),
                    'pattern_confidence': pattern_data.get('confidence', 0.0),
                    'forecast_method': pattern_data.get('forecast_method', 'weighted_average'),
                    'weighted_average_amount': pattern_data.get('weighted_average', 0.0),
                    'last_analyzed': date.today().isoformat()
                })
            
            result = supabase.table('vendor_groups').insert(group_data).execute()
            
            if result.data:
                logger.info(f"✅ Created vendor group: {group_name}")
                return {'success': True, 'data': result.data[0]}
            else:
                logger.error(f"Failed to create vendor group: {group_name}")
                return {'success': False, 'error': 'Database insert failed'}
                
        except Exception as e:
            logger.error(f"Error creating vendor group {group_name}: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_vendor_groups(self, client_id: str, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all vendor groups for a client."""
        try:
            query = supabase.table('vendor_groups').select('*').eq('client_id', client_id)
            
            if active_only:
                query = query.eq('is_active', True)
            
            result = query.order('group_name').execute()
            return result.data
            
        except Exception as e:
            logger.error(f"Error getting vendor groups for {client_id}: {e}")
            return []
    
    def update_vendor_group_pattern(self, client_id: str, group_name: str, 
                                  pattern_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update pattern analysis data for a vendor group."""
        try:
            update_data = {
                'pattern_frequency': pattern_data.get('frequency'),
                'pattern_timing': pattern_data.get('timing'),
                'pattern_confidence': pattern_data.get('confidence', 0.0),
                'weighted_average_amount': pattern_data.get('weighted_average', 0.0),
                'last_analyzed': date.today().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            result = supabase.table('vendor_groups').update(update_data).eq(
                'client_id', client_id
            ).eq('group_name', group_name).execute()
            
            if result.data:
                logger.info(f"✅ Updated pattern for vendor group: {group_name}")
                return {'success': True, 'data': result.data[0]}
            else:
                return {'success': False, 'error': 'Group not found'}
                
        except Exception as e:
            logger.error(f"Error updating vendor group pattern {group_name}: {e}")
            return {'success': False, 'error': str(e)}
    
    # FORECASTS CRUD
    
    def create_forecasts(self, forecasts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create multiple forecast records."""
        try:
            # Prepare forecast data
            forecast_data = []
            for forecast in forecasts:
                record = {
                    'client_id': forecast['client_id'],
                    'vendor_group_name': forecast['vendor_group_name'],
                    'forecast_date': forecast['forecast_date'].isoformat() if isinstance(forecast['forecast_date'], date) else forecast['forecast_date'],
                    'forecast_amount': forecast['forecast_amount'],
                    'forecast_type': forecast['forecast_type'],
                    'forecast_method': forecast.get('forecast_method', 'weighted_average'),
                    'pattern_confidence': forecast.get('pattern_confidence', 0.0),
                    'is_manual_override': forecast.get('is_manual_override', False),
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
                forecast_data.append(record)
            
            # Use upsert to handle duplicates
            result = supabase.table('forecasts').upsert(forecast_data).execute()
            
            if result.data:
                logger.info(f"✅ Created/updated {len(result.data)} forecast records")
                return {'success': True, 'count': len(result.data)}
            else:
                logger.error("Failed to create forecast records")
                return {'success': False, 'error': 'Database insert failed'}
                
        except Exception as e:
            logger.error(f"Error creating forecasts: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_forecasts(self, client_id: str, start_date: Optional[date] = None, 
                     end_date: Optional[date] = None, vendor_group_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get forecasts with optional filters."""
        try:
            query = supabase.table('forecasts').select('*').eq('client_id', client_id)
            
            if start_date:
                query = query.gte('forecast_date', start_date.isoformat())
            if end_date:
                query = query.lte('forecast_date', end_date.isoformat())
            if vendor_group_name:
                query = query.eq('vendor_group_name', vendor_group_name)
            
            result = query.order('forecast_date').execute()
            return result.data
            
        except Exception as e:
            logger.error(f"Error getting forecasts for {client_id}: {e}")
            return []
    
    def update_forecast_manual(self, client_id: str, vendor_group_name: str, 
                             forecast_date: date, new_amount: float) -> Dict[str, Any]:
        """Manually override a forecast amount."""
        try:
            update_data = {
                'forecast_amount': new_amount,
                'is_manual_override': True,
                'forecast_method': 'manual',
                'updated_at': datetime.now().isoformat()
            }
            
            result = supabase.table('forecasts').update(update_data).eq(
                'client_id', client_id
            ).eq('vendor_group_name', vendor_group_name).eq(
                'forecast_date', forecast_date.isoformat()
            ).execute()
            
            if result.data:
                logger.info(f"✅ Updated manual forecast for {vendor_group_name} on {forecast_date}")
                return {'success': True, 'data': result.data[0]}
            else:
                return {'success': False, 'error': 'Forecast not found'}
                
        except Exception as e:
            logger.error(f"Error updating manual forecast: {e}")
            return {'success': False, 'error': str(e)}
    
    # PATTERN ANALYSIS CRUD
    
    def save_pattern_analysis(self, client_id: str, vendor_group_name: str,
                            pattern_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save pattern analysis results for audit trail."""
        try:
            analysis_data = {
                'client_id': client_id,
                'vendor_group_name': vendor_group_name,
                'analysis_date': date.today().isoformat(),
                'frequency_detected': pattern_data.get('frequency'),
                'timing_detected': pattern_data.get('timing'),
                'confidence_score': pattern_data.get('confidence', 0.0),
                'sample_size': pattern_data.get('transaction_count', 0),
                'date_range_start': pattern_data.get('date_range_start'),
                'date_range_end': pattern_data.get('date_range_end'),
                'transactions_analyzed': pattern_data.get('transaction_count', 0),
                'average_amount': pattern_data.get('weighted_average', 0.0),
                'explanation': pattern_data.get('explanation', ''),
                'large_transaction_count': pattern_data.get('large_transaction_count', 0),
                'analysis_method': pattern_data.get('analysis_method', 'automated'),
                'created_at': datetime.now().isoformat()
            }
            
            result = supabase.table('pattern_analysis').insert(analysis_data).execute()
            
            if result.data:
                logger.info(f"✅ Saved pattern analysis for {vendor_group_name}")
                return {'success': True, 'data': result.data[0]}
            else:
                return {'success': False, 'error': 'Database insert failed'}
                
        except Exception as e:
            logger.error(f"Error saving pattern analysis: {e}")
            return {'success': False, 'error': str(e)}
    
    # UTILITY METHODS
    
    def clear_forecasts(self, client_id: str, vendor_group_name: Optional[str] = None,
                       start_date: Optional[date] = None) -> Dict[str, Any]:
        """Clear existing forecasts (for regeneration)."""
        try:
            query = supabase.table('forecasts').delete().eq('client_id', client_id)
            
            if vendor_group_name:
                query = query.eq('vendor_group_name', vendor_group_name)
            if start_date:
                query = query.gte('forecast_date', start_date.isoformat())
            
            result = query.execute()
            
            logger.info(f"✅ Cleared forecasts for {client_id}")
            return {'success': True}
            
        except Exception as e:
            logger.error(f"Error clearing forecasts: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_forecast_summary(self, client_id: str, start_date: date, end_date: date) -> Dict[str, Any]:
        """Get forecast summary for a date range."""
        try:
            forecasts = self.get_forecasts(client_id, start_date, end_date)
            
            if not forecasts:
                return {'total_amount': 0, 'forecast_count': 0, 'vendor_groups': []}
            
            total_amount = sum(float(f['forecast_amount']) for f in forecasts)
            vendor_groups = list(set(f['vendor_group_name'] for f in forecasts))
            
            # Group by vendor
            by_vendor = {}
            for forecast in forecasts:
                vendor = forecast['vendor_group_name']
                if vendor not in by_vendor:
                    by_vendor[vendor] = 0
                by_vendor[vendor] += float(forecast['forecast_amount'])
            
            return {
                'total_amount': total_amount,
                'forecast_count': len(forecasts),
                'vendor_groups': vendor_groups,
                'by_vendor': by_vendor,
                'date_range': f"{start_date} to {end_date}"
            }
            
        except Exception as e:
            logger.error(f"Error getting forecast summary: {e}")
            return {'error': str(e)}

# Global instance
forecast_db = ForecastDBManager()