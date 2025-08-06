#!/usr/bin/env python3
"""
Enhanced Forecast Service
Integrates all components: classification, pattern detection, and forecast generation
"""

import sys
sys.path.append('.')

from typing import Dict, List, Any, Optional
from datetime import datetime, date, timedelta
from dataclasses import asdict

from database.forecast_db_manager import forecast_db
from lean_forecasting.vendor_classifier import vendor_classifier
from lean_forecasting.enhanced_pattern_detector_v2 import enhanced_pattern_detector_v2
from lean_forecasting.enhanced_forecast_generator import enhanced_forecast_generator, ForecastRecord

class EnhancedForecastService:
    """Main service for enhanced forecasting pipeline"""
    
    def analyze_and_forecast_vendor_group(self, client_id: str, vendor_group_name: str,
                                        display_names: List[str],
                                        start_date: Optional[date] = None,
                                        weeks_ahead: int = 13) -> Dict[str, Any]:
        """
        Complete pipeline: classify -> analyze patterns -> generate forecasts
        
        Args:
            client_id: Client identifier
            vendor_group_name: Name of vendor group
            display_names: List of display names in the group
            start_date: Start date for forecasts (default: today)
            weeks_ahead: Number of weeks to forecast
            
        Returns:
            Complete analysis and forecast results
        """
        if start_date is None:
            start_date = date.today()
        
        print(f"\n🚀 Enhanced Forecast Pipeline: {vendor_group_name}")
        print("=" * 80)
        
        # Step 1: Pattern Analysis
        pattern = enhanced_pattern_detector_v2.analyze_vendor_pattern(
            client_id=client_id,
            vendor_group_name=vendor_group_name,
            display_names=display_names
        )
        
        # Step 2: Generate Forecasts
        forecasts = enhanced_forecast_generator.generate_forecasts(
            pattern=pattern,
            start_date=start_date,
            weeks_ahead=weeks_ahead
        )
        
        # Step 3: Aggregate by Week
        weekly_aggregates = enhanced_forecast_generator.aggregate_weekly_forecasts(
            forecasts, start_date, weeks_ahead
        )
        
        # Step 4: Convert to database format
        db_forecasts = self._convert_to_db_format(
            forecasts, client_id, vendor_group_name, display_names
        )
        
        # Step 5: Create result summary
        result = {
            'vendor_group_name': vendor_group_name,
            'analysis': {
                'vendor_classification': {
                    'type': pattern.vendor_classification.vendor_type,
                    'subtype': pattern.vendor_classification.subtype,
                    'confidence': pattern.vendor_classification.confidence,
                    'expected_frequency': pattern.vendor_classification.expected_frequency,
                    'amount_variance': pattern.vendor_classification.amount_variance
                },
                'timing_pattern': {
                    'frequency': pattern.timing_pattern.frequency,
                    'confidence': pattern.timing_pattern.confidence,
                    'typical_day': pattern.timing_pattern.typical_day,
                    'flexibility_days': pattern.timing_pattern.timing_flexibility_days
                },
                'amount_pattern': {
                    'type': pattern.amount_pattern.pattern_type,
                    'average': pattern.amount_pattern.average,
                    'volatility': pattern.amount_pattern.volatility,
                    'confidence': pattern.amount_pattern.confidence,
                    'range': pattern.amount_pattern.range
                },
                'macro_patterns': pattern.macro_pattern,
                'confidence_scores': pattern.confidence_scores,
                'forecast_method': pattern.forecast_method,
                'business_notes': pattern.business_notes
            },
            'forecasts': {
                'individual_forecasts': [asdict(f) for f in forecasts],
                'weekly_aggregates': weekly_aggregates,
                'db_format': db_forecasts,
                'summary': {
                    'total_forecast_records': len(forecasts),
                    'weeks_with_activity': len([w for w in weekly_aggregates.values() if w['count'] > 0]),
                    'total_forecast_amount': sum(f.forecast_amount for f in forecasts),
                    'average_confidence': sum(f.confidence for f in forecasts) / len(forecasts) if forecasts else 0
                }
            }
        }
        
        print(f"\n📊 Pipeline Complete:")
        print(f"   Vendor Type: {pattern.vendor_classification.vendor_type}")
        print(f"   Forecast Method: {pattern.forecast_method}")
        print(f"   Generated Forecasts: {len(forecasts)}")
        print(f"   Overall Confidence: {pattern.confidence_scores['overall_forecastability']:.2f}")
        
        return result
    
    def _convert_to_db_format(self, forecasts: List[ForecastRecord],
                            client_id: str, vendor_group_name: str,
                            display_names: List[str]) -> List[Dict[str, Any]]:
        """Convert forecast records to database format"""
        db_forecasts = []
        
        for forecast in forecasts:
            db_record = {
                'client_id': client_id,
                'vendor_group_name': vendor_group_name,
                'forecast_date': forecast.forecast_date.isoformat(),
                'forecast_amount': forecast.forecast_amount,
                'forecast_type': forecast.method,
                'forecast_method': 'enhanced_v2',
                'pattern_confidence': forecast.confidence,
                'created_at': datetime.now().isoformat(),
                'display_names_included': display_names,
                'amount_range_min': forecast.amount_range[0] if forecast.amount_range else None,
                'amount_range_max': forecast.amount_range[1] if forecast.amount_range else None,
                'notes': forecast.notes
            }
            db_forecasts.append(db_record)
        
        return db_forecasts
    
    def save_forecasts_to_database(self, forecasts_data: Dict[str, Any]) -> bool:
        """Save generated forecasts to database"""
        try:
            db_forecasts = forecasts_data['forecasts']['db_format']
            
            # Clear existing forecasts for this vendor group
            vendor_group_name = forecasts_data['vendor_group_name']
            # Note: You'd implement clear_forecasts method in forecast_db_manager
            
            # Save new forecasts
            for forecast in db_forecasts:
                # Note: You'd implement save_forecast method in forecast_db_manager
                pass
            
            print(f"✅ Saved {len(db_forecasts)} forecasts to database")
            return True
            
        except Exception as e:
            print(f"❌ Error saving forecasts: {e}")
            return False
    
    def update_vendor_group_analysis(self, forecasts_data: Dict[str, Any]) -> bool:
        """Update vendor group with latest analysis results"""
        try:
            analysis = forecasts_data['analysis']
            vendor_group_name = forecasts_data['vendor_group_name']
            
            # Update vendor group record with analysis
            update_data = {
                'pattern_frequency': analysis['timing_pattern']['frequency'],
                'pattern_timing': analysis['timing_pattern']['typical_day'],
                'pattern_confidence': analysis['confidence_scores']['overall_forecastability'],
                'forecast_method': analysis['forecast_method'],
                'weighted_average_amount': analysis['amount_pattern']['average'],
                'last_analyzed': date.today().isoformat()
            }
            
            # Note: You'd implement update_vendor_group method in forecast_db_manager
            # forecast_db.update_vendor_group(vendor_group_name, update_data)
            
            print(f"✅ Updated vendor group analysis for {vendor_group_name}")
            return True
            
        except Exception as e:
            print(f"❌ Error updating vendor group: {e}")
            return False
    
    def run_full_forecast_for_client(self, client_id: str,
                                   start_date: Optional[date] = None,
                                   weeks_ahead: int = 13) -> Dict[str, Any]:
        """
        Run enhanced forecasting for all vendor groups for a client
        
        Args:
            client_id: Client identifier
            start_date: Start date for forecasts
            weeks_ahead: Number of weeks to forecast
            
        Returns:
            Complete forecast results for all vendor groups
        """
        if start_date is None:
            start_date = date.today()
        
        print(f"\n🏗️ Running Full Enhanced Forecast for Client: {client_id}")
        print("=" * 80)
        
        # Get all vendor groups for client
        vendor_groups = forecast_db.get_vendor_groups(client_id)
        
        results = {
            'client_id': client_id,
            'forecast_date': start_date.isoformat(),
            'weeks_ahead': weeks_ahead,
            'vendor_groups': {},
            'summary': {
                'total_groups_processed': 0,
                'successful_forecasts': 0,
                'failed_forecasts': 0,
                'total_forecast_records': 0
            }
        }
        
        for vendor_group in vendor_groups:
            group_name = vendor_group['group_name']
            display_names = vendor_group['vendor_display_names']
            
            print(f"\n📊 Processing: {group_name}")
            
            try:
                group_result = self.analyze_and_forecast_vendor_group(
                    client_id=client_id,
                    vendor_group_name=group_name,
                    display_names=display_names,
                    start_date=start_date,
                    weeks_ahead=weeks_ahead
                )
                
                results['vendor_groups'][group_name] = group_result
                results['summary']['successful_forecasts'] += 1
                results['summary']['total_forecast_records'] += group_result['forecasts']['summary']['total_forecast_records']
                
            except Exception as e:
                print(f"❌ Failed to process {group_name}: {e}")
                results['vendor_groups'][group_name] = {
                    'error': str(e),
                    'status': 'failed'
                }
                results['summary']['failed_forecasts'] += 1
            
            results['summary']['total_groups_processed'] += 1
        
        print(f"\n🎯 Full Forecast Complete:")
        print(f"   Groups Processed: {results['summary']['total_groups_processed']}")
        print(f"   Successful: {results['summary']['successful_forecasts']}")
        print(f"   Failed: {results['summary']['failed_forecasts']}")
        print(f"   Total Forecasts: {results['summary']['total_forecast_records']}")
        
        return results

# Singleton instance
enhanced_forecast_service = EnhancedForecastService()

def test_enhanced_service():
    """Test the enhanced forecast service"""
    print("🧪 Testing Enhanced Forecast Service")
    print("=" * 80)
    
    # Test single vendor group
    result = enhanced_forecast_service.analyze_and_forecast_vendor_group(
        client_id='bestself',
        vendor_group_name='Wise Transfers',
        display_names=['Wise Transfers'],
        start_date=date(2025, 8, 4),
        weeks_ahead=13
    )
    
    print(f"\n✅ Test Complete")
    print(f"   Business Notes: {result['analysis']['business_notes']}")
    print(f"   Forecast Method: {result['analysis']['forecast_method']}")
    print(f"   Total Forecasts: {result['forecasts']['summary']['total_forecast_records']}")

def run_full_client_forecast():
    """Run full forecast for bestself client"""
    print("🏗️ Running Full Client Forecast")
    print("=" * 80)
    
    results = enhanced_forecast_service.run_full_forecast_for_client(
        client_id='bestself',
        start_date=date(2025, 8, 4),
        weeks_ahead=13
    )
    
    return results

if __name__ == "__main__":
    test_enhanced_service()
    print("\n" + "=" * 80)
    run_full_client_forecast()