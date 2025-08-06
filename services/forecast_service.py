"""
Forecast Service
Orchestrates the complete forecasting pipeline using pattern detection and calendar-based forecasting.
"""

import logging
from datetime import datetime, timedelta, UTC
from typing import List, Dict, Any, Optional
from supabase_client import supabase
from core.pattern_detection import classify_vendor_pattern, update_vendor_forecast_config, update_vendor_group_forecast_config
from core.calendar_forecasting import CalendarForecaster, ForecastEvent
from core.forecast_overrides import ForecastOverrideManager

logger = logging.getLogger(__name__)

class ForecastService:
    """Main service for generating and managing forecasts."""
    
    def __init__(self):
        self.forecaster = CalendarForecaster()
        self.override_manager = ForecastOverrideManager()
    
    def get_vendor_group_transactions(self, group_name: str, client_id: str, 
                                    lookback_days: int = 365) -> List[Dict[str, Any]]:
        """Get transactions for ALL vendors in a vendor group (CORRECT WORKFLOW)."""
        try:
            # Calculate date range dynamically
            end_date = datetime.now(UTC)
            start_date = end_date - timedelta(days=lookback_days)
            
            # Get the vendor group and its display names
            group_result = supabase.table('vendor_groups').select(
                'vendor_display_names'
            ).eq(
                'client_id', client_id
            ).eq(
                'group_name', group_name
            ).execute()
            
            if not group_result.data or not group_result.data[0].get('vendor_display_names'):
                logger.warning(f"No vendor group found or empty: {group_name}")
                return []
            
            display_names = group_result.data[0]['vendor_display_names']
            logger.info(f"Vendor group '{group_name}' contains {len(display_names)} display names: {display_names}")
            
            # Get all vendor names that map to ALL these display names
            all_vendor_names = []
            for display_name in display_names:
                vendor_result = supabase.table('vendors').select('vendor_name').eq(
                    'client_id', client_id
                ).eq(
                    'display_name', display_name
                ).execute()
                
                vendor_names = [v['vendor_name'] for v in vendor_result.data]
                all_vendor_names.extend(vendor_names)
                logger.debug(f"Display name '{display_name}' maps to {len(vendor_names)} vendor names")
            
            if not all_vendor_names:
                logger.warning(f"No vendor names found for group {group_name}")
                return []
            
            logger.info(f"Group '{group_name}' maps to {len(all_vendor_names)} total vendor names")
            
            # Get transactions for ALL vendor names in the group
            txn_result = supabase.table('transactions').select(
                'transaction_date, amount, vendor_name'
            ).eq(
                'client_id', client_id
            ).in_(
                'vendor_name', all_vendor_names
            ).gte(
                'transaction_date', start_date.strftime('%Y-%m-%d')
            ).lte(
                'transaction_date', end_date.strftime('%Y-%m-%d')
            ).execute()
            
            logger.info(f"Found {len(txn_result.data)} transactions for vendor group '{group_name}'")
            return txn_result.data
            
        except Exception as e:
            logger.error(f"Error getting transactions for vendor group {group_name}: {e}")
            return []

    def get_vendor_transactions(self, display_name: str, client_id: str, 
                              lookback_days: int = 365) -> List[Dict[str, Any]]:
        """Get transactions for a vendor display name (LEGACY - for backward compatibility)."""
        try:
            # Calculate date range dynamically
            end_date = datetime.now(UTC)
            start_date = end_date - timedelta(days=lookback_days)
            
            # Get all vendor names that map to this display name
            vendor_result = supabase.table('vendors').select('vendor_name').eq(
                'client_id', client_id
            ).eq(
                'display_name', display_name
            ).execute()
            
            if not vendor_result.data:
                logger.warning(f"No vendors found for display name: {display_name}")
                return []
            
            vendor_names = [v['vendor_name'] for v in vendor_result.data]
            
            # Get transactions for all these vendor names
            txn_result = supabase.table('transactions').select(
                'transaction_date, amount, vendor_name'
            ).eq(
                'client_id', client_id
            ).in_(
                'vendor_name', vendor_names
            ).gte(
                'transaction_date', start_date.strftime('%Y-%m-%d')
            ).lte(
                'transaction_date', end_date.strftime('%Y-%m-%d')
            ).execute()
            
            logger.info(f"Found {len(txn_result.data)} transactions for {display_name}")
            return txn_result.data
            
        except Exception as e:
            logger.error(f"Error getting transactions for {display_name}: {e}")
            return []
    
    def detect_and_update_vendor_group_patterns(self, client_id: str) -> Dict[str, Any]:
        """Run pattern detection on vendor GROUPS (CORRECT WORKFLOW)."""
        try:
            # Get all vendor groups for this client
            group_result = supabase.table('vendor_groups').select(
                'group_name, vendor_display_names, is_revenue, category'
            ).eq(
                'client_id', client_id
            ).execute()
            
            if not group_result.data:
                logger.warning(f"No vendor groups found for client {client_id}")
                return {'processed': 0, 'results': []}
            
            logger.info(f"Processing {len(group_result.data)} vendor groups for pattern detection")
            
            results = []
            
            for group in group_result.data:
                group_name = group['group_name']
                logger.info(f"Processing vendor group: {group_name}...")
                
                # Get ALL transactions for this vendor group
                transactions = self.get_vendor_group_transactions(group_name, client_id)
                
                if not transactions:
                    results.append({
                        'group_name': group_name,
                        'status': 'skipped',
                        'reason': 'No transactions found'
                    })
                    continue
                
                # Run pattern detection on the consolidated group transactions
                pattern_result = classify_vendor_pattern(transactions, client_id)
                
                # Update vendor GROUP forecast configuration 
                success = update_vendor_group_forecast_config(group_name, client_id, pattern_result)
                
                results.append({
                    'group_name': group_name,
                    'status': 'success' if success else 'error',
                    'pattern': pattern_result,
                    'transaction_count': len(transactions),
                    'display_names': group['vendor_display_names']
                })
            
            successful = sum(1 for r in results if r['status'] == 'success')
            logger.info(f"Vendor group pattern detection complete: {successful}/{len(results)} groups processed successfully")
            
            return {
                'processed': len(results),
                'successful': successful,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error in vendor group pattern detection: {e}")
            return {'processed': 0, 'successful': 0, 'error': str(e)}

    def detect_and_update_vendor_patterns(self, client_id: str) -> Dict[str, Any]:
        """Run pattern detection on all vendors for a client (LEGACY - for backward compatibility)."""
        try:
            # Get all vendors with display names for this client
            vendor_result = supabase.table('vendors').select(
                'display_name'
            ).eq(
                'client_id', client_id
            ).neq(
                'display_name', None
            ).execute()
            
            if not vendor_result.data:
                logger.warning(f"No vendors found for client {client_id}")
                return {'processed': 0, 'results': []}
            
            # Get unique display names
            display_names = list(set(v['display_name'] for v in vendor_result.data if v['display_name']))
            logger.info(f"Processing {len(display_names)} vendors for pattern detection")
            
            results = []
            
            for display_name in display_names:
                logger.info(f"Processing {display_name}...")
                
                # Get transactions
                transactions = self.get_vendor_transactions(display_name, client_id)
                
                if not transactions:
                    results.append({
                        'display_name': display_name,
                        'status': 'skipped',
                        'reason': 'No transactions found'
                    })
                    continue
                
                # Run pattern detection
                pattern_result = classify_vendor_pattern(transactions, client_id)
                
                # Update vendor forecast configuration
                success = update_vendor_forecast_config(display_name, client_id, pattern_result)
                
                results.append({
                    'display_name': display_name,
                    'status': 'success' if success else 'error',
                    'pattern': pattern_result,
                    'transaction_count': len(transactions)
                })
            
            successful = sum(1 for r in results if r['status'] == 'success')
            logger.info(f"Pattern detection complete: {successful}/{len(results)} vendors processed successfully")
            
            return {
                'processed': len(results),
                'successful': successful,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error in pattern detection: {e}")
            return {'processed': 0, 'successful': 0, 'error': str(e)}
    
    def get_vendor_group_forecast_configs(self, client_id: str) -> List[Dict[str, Any]]:
        """Get forecast configurations for all vendor GROUPS (CORRECT WORKFLOW)."""
        try:
            result = supabase.table('vendor_groups').select(
                'group_name, forecast_frequency, forecast_day, forecast_amount, forecast_confidence, is_revenue, category'
            ).eq(
                'client_id', client_id
            ).neq(
                'forecast_frequency', 'irregular'
            ).neq(
                'forecast_frequency', None
            ).execute()
            
            logger.info(f"Found {len(result.data)} vendor groups with forecast configs")
            return result.data
            
        except Exception as e:
            logger.error(f"Error getting vendor group configs: {e}")
            return []

    def get_vendor_forecast_configs(self, client_id: str) -> List[Dict[str, Any]]:
        """Get forecast configurations for all vendors."""
        try:
            result = supabase.table('vendors').select(
                'display_name, forecast_frequency, forecast_day, forecast_amount, forecast_confidence'
            ).eq(
                'client_id', client_id
            ).neq(
                'display_name', None
            ).neq(
                'forecast_frequency', 'irregular'
            ).execute()
            
            # Group by display name and take the first config for each
            configs = {}
            for vendor in result.data:
                display_name = vendor['display_name']
                if display_name not in configs:
                    configs[display_name] = vendor
            
            return list(configs.values())
            
        except Exception as e:
            logger.error(f"Error getting vendor configs: {e}")
            return []
    
    def generate_vendor_group_calendar_forecast(self, client_id: str, 
                                              start_date: Optional[datetime] = None,
                                              weeks_ahead: int = 13) -> List[ForecastEvent]:
        """Generate calendar-based forecast events using vendor GROUPS (CORRECT WORKFLOW)."""
        try:
            if not start_date:
                start_date = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
            
            end_date = start_date + timedelta(days=weeks_ahead * 7)
            
            logger.info(f"Generating vendor group forecast from {start_date.date()} to {end_date.date()}")
            
            # Get vendor GROUP forecast configurations
            group_configs = self.get_vendor_group_forecast_configs(client_id)
            
            if not group_configs:
                logger.warning(f"No vendor group configurations found for client {client_id}")
                return []
            
            logger.info(f"Found {len(group_configs)} vendor groups with forecast configs")
            
            # Convert group configs to format expected by calendar forecaster
            # Need to use group_name as the "display_name" for now
            adapted_configs = []
            for config in group_configs:
                adapted_config = {
                    'display_name': config['group_name'],  # Use group name as display name
                    'forecast_frequency': config['forecast_frequency'],
                    'forecast_day': config['forecast_day'],
                    'forecast_amount': config['forecast_amount'],
                    'forecast_confidence': config['forecast_confidence']
                }
                adapted_configs.append(adapted_config)
            
            # Generate forecast events
            events = self.forecaster.generate_forecast_events(adapted_configs, start_date, end_date)
            
            # Apply any manual overrides (need to update this to work with group names)
            events_with_overrides = self.override_manager.apply_overrides_to_events(events, client_id)
            
            logger.info(f"Generated {len(events_with_overrides)} forecast events from vendor groups")
            return events_with_overrides
            
        except Exception as e:
            logger.error(f"Error generating vendor group calendar forecast: {e}")
            return []

    def generate_calendar_forecast(self, client_id: str, 
                                 start_date: Optional[datetime] = None,
                                 weeks_ahead: int = 13) -> List[ForecastEvent]:
        """Generate calendar-based forecast events (LEGACY - for backward compatibility)."""
        try:
            if not start_date:
                start_date = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
            
            end_date = start_date + timedelta(days=weeks_ahead * 7)
            
            logger.info(f"Generating forecast from {start_date.date()} to {end_date.date()}")
            
            # Get vendor forecast configurations
            vendor_configs = self.get_vendor_forecast_configs(client_id)
            
            if not vendor_configs:
                logger.warning(f"No vendor configurations found for client {client_id}")
                return []
            
            logger.info(f"Found {len(vendor_configs)} vendors with forecast configs")
            
            # Generate forecast events
            events = self.forecaster.generate_forecast_events(vendor_configs, start_date, end_date)
            
            # Apply any manual overrides
            events_with_overrides = self.override_manager.apply_overrides_to_events(events, client_id)
            
            logger.info(f"Generated {len(events_with_overrides)} forecast events")
            return events_with_overrides
            
        except Exception as e:
            logger.error(f"Error generating calendar forecast: {e}")
            return []
    
    def generate_weekly_forecast_summary(self, client_id: str,
                                       start_date: Optional[datetime] = None,
                                       weeks_ahead: int = 13) -> List[Dict[str, Any]]:
        """Generate weekly forecast summary with cash flow projections."""
        try:
            # Generate forecast events
            events = self.generate_calendar_forecast(client_id, start_date, weeks_ahead)
            
            if not events:
                logger.warning("No forecast events generated")
                return []
            
            # Convert to weekly summary
            if not start_date:
                start_date = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
            
            weekly_summary = self.forecaster.events_to_weekly_summary(events, start_date)
            
            logger.info(f"Generated {len(weekly_summary)} weeks of forecast summary")
            return weekly_summary
            
        except Exception as e:
            logger.error(f"Error generating weekly forecast summary: {e}")
            return []

    def generate_vendor_group_weekly_forecast_summary(self, client_id: str,
                                                    start_date: Optional[datetime] = None,
                                                    weeks_ahead: int = 13) -> List[Dict[str, Any]]:
        """Generate weekly forecast summary using vendor GROUPS (CORRECT WORKFLOW)."""
        try:
            # Generate vendor group forecast events
            events = self.generate_vendor_group_calendar_forecast(client_id, start_date, weeks_ahead)
            
            if not events:
                logger.warning("No vendor group forecast events generated")
                return []
            
            # Convert to weekly summary
            if not start_date:
                start_date = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
            
            weekly_summary = self.forecaster.events_to_weekly_summary(events, start_date)
            
            logger.info(f"Generated {len(weekly_summary)} weeks of vendor group forecast summary")
            return weekly_summary
            
        except Exception as e:
            logger.error(f"Error generating vendor group weekly forecast summary: {e}")
            return []
    
    def run_vendor_group_forecast_pipeline(self, client_id: str) -> Dict[str, Any]:
        """Run the complete VENDOR GROUP forecast pipeline (CORRECT WORKFLOW)."""
        try:
            logger.info(f"Starting vendor group forecast pipeline for client {client_id}")
            start_time = datetime.now()
            
            # Step 1: Vendor GROUP pattern detection and configuration update
            logger.info("Step 1: Running vendor group pattern detection...")
            pattern_results = self.detect_and_update_vendor_group_patterns(client_id)
            
            # Step 2: Generate calendar forecast using vendor groups
            logger.info("Step 2: Generating vendor group calendar forecast...")
            weekly_forecast = self.generate_vendor_group_weekly_forecast_summary(client_id)
            
            # Step 3: Calculate summary statistics
            total_deposits = sum(week['deposits'] for week in weekly_forecast)
            total_withdrawals = sum(week['withdrawals'] for week in weekly_forecast)
            net_movement = total_deposits - total_withdrawals
            
            duration = (datetime.now() - start_time).total_seconds()
            
            result = {
                'client_id': client_id,
                'status': 'success',
                'duration_seconds': round(duration, 2),
                'workflow': 'vendor_groups',
                'pattern_detection': pattern_results,
                'forecast_summary': {
                    'weeks_generated': len(weekly_forecast),
                    'total_deposits': round(total_deposits, 2),
                    'total_withdrawals': round(total_withdrawals, 2),
                    'net_movement': round(net_movement, 2)
                },
                'weekly_forecast': weekly_forecast
            }
            
            logger.info(f"Vendor group forecast pipeline complete in {duration:.2f}s")
            logger.info(f"Generated {len(weekly_forecast)} weeks: ${total_deposits:,.0f} deposits, ${total_withdrawals:,.0f} withdrawals")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in vendor group forecast pipeline: {e}")
            return {
                'client_id': client_id,
                'status': 'error',
                'workflow': 'vendor_groups',
                'error': str(e)
            }

    def run_full_forecast_pipeline(self, client_id: str) -> Dict[str, Any]:
        """Run the complete forecast pipeline: pattern detection + calendar generation (LEGACY)."""
        try:
            logger.info(f"Starting full forecast pipeline for client {client_id}")
            start_time = datetime.now()
            
            # Step 1: Pattern detection and vendor configuration update
            logger.info("Step 1: Running pattern detection...")
            pattern_results = self.detect_and_update_vendor_patterns(client_id)
            
            # Step 2: Generate calendar forecast
            logger.info("Step 2: Generating calendar forecast...")
            weekly_forecast = self.generate_weekly_forecast_summary(client_id)
            
            # Step 3: Calculate summary statistics
            total_deposits = sum(week['deposits'] for week in weekly_forecast)
            total_withdrawals = sum(week['withdrawals'] for week in weekly_forecast)
            net_movement = total_deposits - total_withdrawals
            
            duration = (datetime.now() - start_time).total_seconds()
            
            result = {
                'client_id': client_id,
                'status': 'success',
                'duration_seconds': round(duration, 2),
                'workflow': 'individual_vendors',
                'pattern_detection': pattern_results,
                'forecast_summary': {
                    'weeks_generated': len(weekly_forecast),
                    'total_deposits': round(total_deposits, 2),
                    'total_withdrawals': round(total_withdrawals, 2),
                    'net_movement': round(net_movement, 2)
                },
                'weekly_forecast': weekly_forecast
            }
            
            logger.info(f"Forecast pipeline complete in {duration:.2f}s")
            logger.info(f"Generated {len(weekly_forecast)} weeks: ${total_deposits:,.0f} deposits, ${total_withdrawals:,.0f} withdrawals")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in forecast pipeline: {e}")
            return {
                'client_id': client_id,
                'status': 'error',
                'workflow': 'individual_vendors',
                'error': str(e)
            }
    
    def create_manual_override(self, client_id: str, vendor_display_name: str,
                             override_type: str, target_date: datetime,
                             new_amount: Optional[float] = None,
                             new_date: Optional[datetime] = None,
                             reason: str = "") -> bool:
        """Create a manual override for a forecast."""
        try:
            if override_type == 'amount_change' and new_amount is not None:
                return self.override_manager.create_amount_override(
                    client_id, vendor_display_name, target_date, new_amount, reason
                )
            elif override_type == 'date_shift' and new_date is not None:
                return self.override_manager.create_date_shift_override(
                    client_id, vendor_display_name, target_date, new_date, reason
                )
            elif override_type == 'skip_occurrence':
                return self.override_manager.create_skip_override(
                    client_id, vendor_display_name, target_date, reason
                )
            else:
                logger.error(f"Invalid override type or missing parameters: {override_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error creating override: {e}")
            return False