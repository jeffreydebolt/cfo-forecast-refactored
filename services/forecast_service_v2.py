"""
Forecast Service V2
Integrates new pattern detection and database storage with existing functionality.
"""

import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional

# Import existing components
from supabase_client import supabase
from core.calendar_forecasting import CalendarForecaster, ForecastEvent
from core.forecast_overrides import ForecastOverrideManager

# Import new components
from lean_forecasting.group_pattern_detector import group_pattern_detector
from lean_forecasting.forecast_generator import forecast_generator
from database.forecast_db_manager import forecast_db

logger = logging.getLogger(__name__)

class ForecastServiceV2:
    """Enhanced forecast service with new pattern detection and database integration."""
    
    def __init__(self):
        self.forecaster = CalendarForecaster()
        self.override_manager = ForecastOverrideManager()
        self.pattern_detector = group_pattern_detector
        self.forecast_generator = forecast_generator
        self.db = forecast_db
    
    # VENDOR GROUP MANAGEMENT
    
    def get_or_create_vendor_groups(self, client_id: str) -> List[Dict[str, Any]]:
        """Get existing vendor groups or create from display names."""
        try:
            # Check if vendor groups exist in new table
            vendor_groups = self.db.get_vendor_groups(client_id)
            
            if vendor_groups:
                logger.info(f"Found {len(vendor_groups)} existing vendor groups")
                return vendor_groups
            
            # If no groups, create from existing display names
            logger.info("No vendor groups found, creating from display names...")
            
            # Get unique display names from vendors table
            result = supabase.table('vendors').select('display_name').eq(
                'client_id', client_id
            ).execute()
            
            if not result.data:
                logger.warning(f"No vendors found for client {client_id}")
                return []
            
            # Get unique display names
            display_names = list(set(v['display_name'] for v in result.data if v['display_name']))
            
            # Create a vendor group for each display name (user can merge later)
            created_groups = []
            for display_name in display_names:
                result = self.db.create_vendor_group(
                    client_id=client_id,
                    group_name=display_name,  # Use display name as initial group name
                    vendor_display_names=[display_name]
                )
                
                if result['success']:
                    created_groups.append(result['data'])
            
            logger.info(f"Created {len(created_groups)} vendor groups from display names")
            return created_groups
            
        except Exception as e:
            logger.error(f"Error managing vendor groups: {e}")
            return []
    
    # PATTERN DETECTION
    
    def detect_all_patterns(self, client_id: str) -> Dict[str, Any]:
        """Run pattern detection on all vendor groups."""
        try:
            vendor_groups = self.get_or_create_vendor_groups(client_id)
            
            if not vendor_groups:
                return {'processed': 0, 'successful': 0, 'results': []}
            
            results = []
            successful = 0
            
            for group in vendor_groups:
                group_name = group['group_name']
                display_names = group['vendor_display_names']
                
                logger.info(f"Analyzing pattern for group: {group_name}")
                
                # Run pattern analysis
                pattern_data = self.pattern_detector.analyze_vendor_group_pattern(
                    client_id, group_name, display_names
                )
                
                # Update vendor group with pattern data
                if pattern_data['frequency'] != 'irregular':
                    update_result = self.db.update_vendor_group_pattern(
                        client_id, group_name, pattern_data
                    )
                    
                    if update_result['success']:
                        successful += 1
                        
                    # Save pattern analysis for audit
                    self.db.save_pattern_analysis(client_id, group_name, pattern_data)
                
                results.append({
                    'group_name': group_name,
                    'display_names': display_names,
                    'pattern': pattern_data,
                    'status': 'success' if pattern_data['frequency'] != 'irregular' else 'skipped'
                })
            
            logger.info(f"Pattern detection complete: {successful}/{len(results)} groups processed")
            
            return {
                'processed': len(results),
                'successful': successful,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error in pattern detection: {e}")
            return {'processed': 0, 'successful': 0, 'error': str(e)}
    
    # FORECAST GENERATION
    
    def generate_all_forecasts(self, client_id: str, start_date: Optional[date] = None,
                             weeks_ahead: int = 13) -> Dict[str, Any]:
        """Generate forecasts for all vendor groups and store in database."""
        try:
            if start_date is None:
                start_date = date.today()
            
            # Get vendor groups with patterns
            vendor_groups = self.db.get_vendor_groups(client_id)
            
            active_groups = [g for g in vendor_groups if g.get('pattern_frequency') and 
                           g['pattern_frequency'] != 'irregular']
            
            if not active_groups:
                logger.warning("No vendor groups with valid patterns found")
                return {'generated': 0, 'groups': []}
            
            logger.info(f"Generating forecasts for {len(active_groups)} vendor groups")
            
            # Clear existing forecasts for this period (optional)
            if hasattr(self, 'clear_existing_forecasts') and self.clear_existing_forecasts:
                self.db.clear_forecasts(client_id, start_date=start_date)
            
            total_forecasts = 0
            group_results = []
            
            for group in active_groups:
                group_name = group['group_name']
                display_names = group['vendor_display_names']
                
                logger.info(f"Generating forecasts for: {group_name}")
                
                # Generate forecast records
                forecast_records = self.forecast_generator.generate_vendor_group_forecast(
                    client_id=client_id,
                    vendor_group_name=group_name,
                    display_names=display_names,
                    weeks_ahead=weeks_ahead,
                    start_date=start_date
                )
                
                if forecast_records:
                    # Store in database
                    result = self.db.create_forecasts(forecast_records)
                    
                    if result['success']:
                        count = result['count']
                        total_forecasts += count
                        
                        group_results.append({
                            'group_name': group_name,
                            'forecasts_generated': count,
                            'status': 'success'
                        })
                    else:
                        group_results.append({
                            'group_name': group_name,
                            'forecasts_generated': 0,
                            'status': 'error',
                            'error': result.get('error')
                        })
                else:
                    group_results.append({
                        'group_name': group_name,
                        'forecasts_generated': 0,
                        'status': 'skipped',
                        'reason': 'No pattern or zero amount'
                    })
            
            logger.info(f"Generated {total_forecasts} total forecast records")
            
            return {
                'generated': total_forecasts,
                'groups': group_results,
                'date_range': f"{start_date} to {start_date + timedelta(weeks=weeks_ahead)}"
            }
            
        except Exception as e:
            logger.error(f"Error generating forecasts: {e}")
            return {'generated': 0, 'error': str(e)}
    
    # FORECAST RETRIEVAL (For UI)
    
    def get_calendar_forecasts(self, client_id: str, start_date: date, end_date: date) -> List[ForecastEvent]:
        """Get forecasts from database and convert to calendar events for UI."""
        try:
            # Get forecasts from database
            forecasts = self.db.get_forecasts(client_id, start_date, end_date)
            
            if not forecasts:
                logger.info("No forecasts found in database")
                return []
            
            # Convert to ForecastEvent objects for existing UI
            events = []
            
            for forecast in forecasts:
                # Check for manual overrides
                override = self.override_manager.get_override(
                    vendor_name=forecast['vendor_group_name'],
                    date=forecast['forecast_date']
                )
                
                if override:
                    amount = override['amount']
                    is_override = True
                else:
                    amount = float(forecast['forecast_amount'])
                    is_override = forecast.get('is_manual_override', False)
                
                event = ForecastEvent(
                    date=datetime.strptime(forecast['forecast_date'], '%Y-%m-%d').date(),
                    vendor_name=forecast['vendor_group_name'],
                    amount=amount,
                    frequency=forecast['forecast_type'],
                    confidence=float(forecast.get('pattern_confidence', 0.0)),
                    is_override=is_override
                )
                
                events.append(event)
            
            logger.info(f"Retrieved {len(events)} forecast events")
            return events
            
        except Exception as e:
            logger.error(f"Error retrieving calendar forecasts: {e}")
            return []
    
    # MANUAL OVERRIDES
    
    def update_manual_forecast(self, client_id: str, vendor_group_name: str,
                             forecast_date: date, new_amount: float) -> Dict[str, Any]:
        """Update a forecast with manual override."""
        try:
            # Update in database
            result = self.db.update_forecast_manual(
                client_id, vendor_group_name, forecast_date, new_amount
            )
            
            if result['success']:
                # Also save in override manager for backward compatibility
                self.override_manager.save_override(
                    vendor_name=vendor_group_name,
                    date=forecast_date,
                    amount=new_amount
                )
                
                logger.info(f"Updated manual forecast for {vendor_group_name} on {forecast_date}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error updating manual forecast: {e}")
            return {'success': False, 'error': str(e)}
    
    # SUMMARY AND REPORTING
    
    def get_forecast_summary(self, client_id: str, start_date: date, end_date: date) -> Dict[str, Any]:
        """Get forecast summary for reporting."""
        return self.db.get_forecast_summary(client_id, start_date, end_date)
    
    # BACKWARD COMPATIBILITY
    
    def generate_calendar_forecast(self, client_id: str, start_date: Optional[datetime] = None,
                                 weeks_ahead: int = 13) -> List[ForecastEvent]:
        """Legacy method - generates forecasts and returns calendar events."""
        # Generate and store forecasts
        if start_date is None:
            start_date = date.today()
        else:
            start_date = start_date.date() if isinstance(start_date, datetime) else start_date
        
        self.generate_all_forecasts(client_id, start_date, weeks_ahead)
        
        # Return calendar events
        end_date = start_date + timedelta(weeks=weeks_ahead)
        return self.get_calendar_forecasts(client_id, start_date, end_date)

# Create global instance for backward compatibility
forecast_service_v2 = ForecastServiceV2()