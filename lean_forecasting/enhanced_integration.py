#!/usr/bin/env python3
"""
Enhanced Integration - Bridge between enhanced system and existing infrastructure
"""

import sys
sys.path.append('.')

from typing import Dict, List, Any, Optional
from datetime import datetime, date, timedelta

from database.forecast_db_manager import forecast_db
from lean_forecasting.vendor_classifier import vendor_classifier
from lean_forecasting.group_pattern_detector import group_pattern_detector

class EnhancedIntegration:
    """Integration layer for enhanced forecasting with existing system"""
    
    def analyze_vendor_group_enhanced(self, client_id: str, vendor_group_name: str,
                                    display_names: List[str]) -> Dict[str, Any]:
        """
        Enhanced analysis that combines classification with existing pattern detection
        
        Args:
            client_id: Client identifier
            vendor_group_name: Name of vendor group
            display_names: List of display names in the group
            
        Returns:
            Enhanced analysis results
        """
        print(f"\n🔍 Enhanced Analysis: {vendor_group_name}")
        print("=" * 60)
        
        # Step 1: Get vendor classification
        classification = vendor_classifier.classify_vendor(vendor_group_name)
        print(f"📊 Vendor Type: {classification.vendor_type} ({classification.confidence:.2f} confidence)")
        print(f"   Expected Frequency: {classification.expected_frequency}")
        print(f"   Amount Variance: {classification.amount_variance}")
        print(f"   Business Rules: {classification.business_rules['forecast_method']}")
        
        # Step 2: Use existing pattern detector
        try:
            pattern_result = group_pattern_detector.analyze_vendor_group_pattern(
                client_id, vendor_group_name, display_names
            )
            print(f"📈 Pattern Analysis: {pattern_result['frequency']} (confidence: {pattern_result['frequency_confidence']:.2f})")
        except Exception as e:
            print(f"⚠️  Pattern analysis failed: {e}")
            # Create fallback pattern result
            pattern_result = {
                'frequency': 'irregular',
                'frequency_confidence': 0.0,
                'timing': 'irregular',
                'weighted_average': 0.0
            }
        
        # Step 3: Enhanced interpretation based on vendor type
        enhanced_result = self._interpret_with_business_logic(
            classification, pattern_result, vendor_group_name
        )
        
        return enhanced_result
    
    def _interpret_with_business_logic(self, classification: Any, 
                                     pattern_result: Dict[str, Any],
                                     vendor_group_name: str) -> Dict[str, Any]:
        """Apply business logic to improve pattern interpretation"""
        
        # Start with base pattern result
        enhanced = {
            'vendor_group_name': vendor_group_name,
            'classification': {
                'vendor_type': classification.vendor_type,
                'subtype': classification.subtype,
                'confidence': classification.confidence,
                'expected_frequency': classification.expected_frequency,
                'amount_variance': classification.amount_variance,
                'business_rules': classification.business_rules
            },
            'pattern_analysis': pattern_result.copy(),
            'enhanced_insights': [],
            'forecast_recommendations': {}
        }
        
        # Apply business logic enhancements
        vendor_type = classification.vendor_type
        frequency = pattern_result['frequency']
        confidence = pattern_result['frequency_confidence']
        amount = pattern_result['weighted_average']
        
        # Contractor Platform Logic (Wise, PayPal for contractors)
        if vendor_type == 'contractor_platform':
            if frequency == 'irregular' and amount == 0:
                enhanced['enhanced_insights'].append(
                    "Contractor platform with no clear pattern - likely needs manual forecasting"
                )
                enhanced['forecast_recommendations'] = {
                    'method': 'manual_range_estimate',
                    'suggested_frequency': 'bi-weekly_to_monthly',
                    'suggested_amount_range': (3000, 8000),
                    'notes': 'Contractor payments typically vary by project workload'
                }
            elif frequency == 'irregular' and amount > 0:
                # Use macro patterns for contractor payments
                enhanced['enhanced_insights'].append(
                    f"Contractor platform with irregular timing but ${amount:,.2f} average - use monthly aggregation"
                )
                enhanced['forecast_recommendations'] = {
                    'method': 'monthly_distribution',
                    'monthly_budget': amount * 4.33,  # Weekly to monthly conversion
                    'distribution': 'bi_weekly_payments',
                    'notes': 'Distribute monthly budget across bi-weekly payments'
                }
        
        # Professional Services Logic (Armbrust, Legal, Consulting)
        elif vendor_type == 'professional_services':
            if frequency == 'irregular' and amount == 0:
                enhanced['enhanced_insights'].append(
                    "Professional services with no pattern - typically project or retainer based"
                )
                enhanced['forecast_recommendations'] = {
                    'method': 'quarterly_estimate',
                    'suggested_frequency': 'monthly_to_quarterly',
                    'suggested_amount_range': (5000, 20000),
                    'notes': 'Professional services often bill monthly or per project milestone'
                }
            elif frequency in ['monthly', 'quarterly']:
                enhanced['enhanced_insights'].append(
                    f"Professional services showing {frequency} pattern - likely retainer or recurring billing"
                )
        
        # Revenue Source Logic (Amazon, Shopify, etc.)
        elif vendor_type == 'revenue_source':
            if frequency == 'irregular' and amount == 0:
                enhanced['enhanced_insights'].append(
                    "Revenue source with no clear pattern - may need seasonal analysis"
                )
                enhanced['forecast_recommendations'] = {
                    'method': 'seasonal_analysis',
                    'notes': 'Revenue streams often have seasonal patterns not captured in short-term analysis'
                }
            elif confidence > 0.7:
                enhanced['enhanced_insights'].append(
                    f"Strong {frequency} revenue pattern detected - reliable for forecasting"
                )
        
        # Financial Services Logic (Credit cards, banking)
        elif vendor_type == 'financial_services':
            if frequency == 'monthly' or 'month' in classification.expected_frequency:
                enhanced['enhanced_insights'].append(
                    "Financial services typically follow monthly billing cycles"
                )
                enhanced['forecast_recommendations'] = {
                    'method': 'fixed_monthly_schedule',
                    'timing': 'statement_date_plus_3_days',
                    'notes': 'Credit cards and financial services follow predictable monthly cycles'
                }
        
        # Apply confidence adjustments based on business context
        if vendor_type in ['contractor_platform', 'professional_services'] and frequency == 'irregular':
            # These vendor types are expected to be irregular, so don't penalize confidence
            enhanced['pattern_analysis']['adjusted_confidence'] = min(0.6, confidence + 0.3)
            enhanced['enhanced_insights'].append(
                "Irregular pattern is normal for this vendor type - confidence boosted"
            )
        
        # Generate overall recommendation
        enhanced['overall_recommendation'] = self._generate_overall_recommendation(
            classification, pattern_result, enhanced['enhanced_insights']
        )
        
        return enhanced
    
    def _generate_overall_recommendation(self, classification: Any,
                                       pattern_result: Dict[str, Any],
                                       insights: List[str]) -> Dict[str, Any]:
        """Generate overall forecasting recommendation"""
        
        vendor_type = classification.vendor_type
        frequency = pattern_result['frequency']
        confidence = pattern_result['frequency_confidence']
        amount = pattern_result['weighted_average']
        
        if confidence > 0.7 and amount > 0:
            return {
                'status': 'ready_for_automatic_forecasting',
                'confidence': 'high',
                'method': 'pattern_based',
                'notes': f"Strong {frequency} pattern with ${amount:,.2f} average"
            }
        
        elif confidence > 0.4 and amount > 0:
            return {
                'status': 'ready_with_monitoring',
                'confidence': 'medium',
                'method': 'pattern_based_with_manual_override',
                'notes': f"Moderate {frequency} pattern, recommend manual review"
            }
        
        elif amount > 0:
            return {
                'status': 'manual_forecasting_recommended',
                'confidence': 'low',
                'method': 'manual_estimates',
                'notes': f"No clear timing pattern but ${amount:,.2f} historical average available"
            }
        
        else:
            return {
                'status': 'manual_setup_required',
                'confidence': 'none',
                'method': 'manual_input',
                'notes': f"No historical data - manual setup required for {vendor_type} vendor"
            }
    
    def update_vendor_group_with_enhanced_analysis(self, client_id: str,
                                                 vendor_group_name: str,
                                                 display_names: List[str]) -> bool:
        """Update vendor group with enhanced analysis results"""
        try:
            # Get enhanced analysis
            enhanced_result = self.analyze_vendor_group_enhanced(
                client_id, vendor_group_name, display_names
            )
            
            # Extract data for database update
            classification = enhanced_result['classification']
            pattern = enhanced_result['pattern_analysis']
            recommendation = enhanced_result['overall_recommendation']
            
            # Update the vendor group in database
            update_data = {
                'pattern_frequency': pattern['frequency'],
                'pattern_timing': pattern.get('timing', 'unknown'),
                'pattern_confidence': pattern.get('adjusted_confidence', pattern['frequency_confidence']),
                'forecast_method': recommendation['method'],
                'weighted_average_amount': pattern['weighted_average'],
                'last_analyzed': date.today().isoformat()
            }
            
            # Use existing database methods
            # Note: forecast_db_manager would need an update_vendor_group method
            success = forecast_db.update_vendor_group_analysis(
                client_id, vendor_group_name, update_data
            )
            
            if success:
                print(f"✅ Updated {vendor_group_name} with enhanced analysis")
                print(f"   Status: {recommendation['status']}")
                print(f"   Method: {recommendation['method']}")
            
            return success
            
        except Exception as e:
            print(f"❌ Failed to update {vendor_group_name}: {e}")
            return False
    
    def generate_enhanced_forecasts_for_all_groups(self, client_id: str) -> Dict[str, Any]:
        """Run enhanced analysis for all vendor groups"""
        print(f"\n🏗️ Enhanced Analysis for All Groups: {client_id}")
        print("=" * 80)
        
        # Get all vendor groups
        vendor_groups = forecast_db.get_vendor_groups(client_id)
        
        results = {
            'client_id': client_id,
            'analysis_date': date.today().isoformat(),
            'vendor_groups': {},
            'summary': {
                'total_groups': len(vendor_groups),
                'ready_for_forecasting': 0,
                'need_manual_setup': 0,
                'need_monitoring': 0
            }
        }
        
        for vendor_group in vendor_groups:
            group_name = vendor_group['group_name']
            display_names = vendor_group['vendor_display_names']
            
            try:
                enhanced_result = self.analyze_vendor_group_enhanced(
                    client_id, group_name, display_names
                )
                
                results['vendor_groups'][group_name] = enhanced_result
                
                # Update summary counts
                recommendation = enhanced_result['overall_recommendation']
                if recommendation['status'] == 'ready_for_automatic_forecasting':
                    results['summary']['ready_for_forecasting'] += 1
                elif recommendation['status'] == 'manual_setup_required':
                    results['summary']['need_manual_setup'] += 1
                else:
                    results['summary']['need_monitoring'] += 1
                    
            except Exception as e:
                print(f"❌ Failed to analyze {group_name}: {e}")
                results['vendor_groups'][group_name] = {
                    'error': str(e),
                    'status': 'analysis_failed'
                }
        
        print(f"\n🎯 Enhanced Analysis Summary:")
        print(f"   Total Groups: {results['summary']['total_groups']}")
        print(f"   Ready for Forecasting: {results['summary']['ready_for_forecasting']}")
        print(f"   Need Manual Setup: {results['summary']['need_manual_setup']}")
        print(f"   Need Monitoring: {results['summary']['need_monitoring']}")
        
        return results

# Singleton instance
enhanced_integration = EnhancedIntegration()

def test_enhanced_integration():
    """Test the enhanced integration"""
    print("🧪 Testing Enhanced Integration")
    print("=" * 80)
    
    # Test specific problematic vendors
    test_vendors = [
        ('Wise Transfers', ['Wise Transfers']),
        ('Armbrust Expenses', ['Armbrust Expenses']),
        ('Contractor Payments', ['Wise Transfers']),
        ('Amazon Revenue', ['Amazon Revenue'])
    ]
    
    for vendor_name, display_names in test_vendors:
        try:
            result = enhanced_integration.analyze_vendor_group_enhanced(
                client_id='bestself',
                vendor_group_name=vendor_name, 
                display_names=display_names
            )
            
            print(f"\n✅ {vendor_name}:")
            print(f"   Type: {result['classification']['vendor_type']}")
            print(f"   Status: {result['overall_recommendation']['status']}")
            print(f"   Method: {result['overall_recommendation']['method']}")
            print(f"   Insights: {len(result['enhanced_insights'])} insights")
            
        except Exception as e:
            print(f"\n❌ {vendor_name}: {e}")

if __name__ == "__main__":
    test_enhanced_integration()