#!/usr/bin/env python3
"""
Generate Enhanced Dashboard with Integration
Uses the enhanced integration system to create forecasts with business intelligence
"""

import sys
sys.path.append('.')

from database.forecast_db_manager import forecast_db
from lean_forecasting.enhanced_integration import enhanced_integration
from datetime import date, timedelta

def generate_enhanced_dashboard():
    """Generate dashboard using enhanced pattern recognition"""
    print("🚀 GENERATING ENHANCED DASHBOARD")
    print("=" * 60)
    
    client_id = 'bestself'
    start_date = date(2025, 8, 4)
    
    # Step 1: Run enhanced analysis for all vendor groups
    enhanced_results = enhanced_integration.generate_enhanced_forecasts_for_all_groups(client_id)
    
    # Step 2: Get forecast data
    end_date = start_date + timedelta(weeks=13)
    forecasts = forecast_db.get_forecasts(client_id, start_date, end_date)
    vendor_groups = forecast_db.get_vendor_groups(client_id)
    
    # Step 3: Build enhanced vendor categorization using results
    vendors_by_category = {
        'inflows': [],
        'cc': [],
        'people': [],
        'admin': []
    }
    
    print(f"\n📊 Enhanced Categorization:")
    
    for vendor_group in vendor_groups:
        group_name = vendor_group['group_name']
        
        # Get enhanced analysis if available
        enhanced_data = enhanced_results['vendor_groups'].get(group_name, {})
        
        if 'classification' in enhanced_data:
            classification = enhanced_data['classification']
            vendor_type = classification['vendor_type']
            pattern = enhanced_data['pattern_analysis']
            recommendation = enhanced_data['overall_recommendation']
            
            # Categorize based on vendor type and amount
            amount = pattern['weighted_average']
            
            if amount == 0:
                category = None  # Skip vendors with no data
            elif amount > 0:
                category = 'inflows'
            elif vendor_type == 'financial_services':
                category = 'cc'
            elif vendor_type in ['contractor_platform', 'professional_services', 'employee_payroll']:
                category = 'people'
            else:
                category = 'admin'
            
            if category:
                vendor_info = {
                    'name': group_name,
                    'type': f"{classification['vendor_type']} ({recommendation['confidence']})",
                    'frequency': pattern['frequency'],
                    'amount': amount,
                    'status': recommendation['status'],
                    'method': recommendation['method'],
                    'insights': len(enhanced_data.get('enhanced_insights', []))
                }
                vendors_by_category[category].append(vendor_info)
                
                # Enhanced status reporting
                status_icon = {
                    'ready_for_automatic_forecasting': '✅',
                    'ready_with_monitoring': '⚠️ ',
                    'manual_forecasting_recommended': '🔧',
                    'manual_setup_required': '❌'
                }.get(recommendation['status'], '❓')
                
                print(f"  {status_icon} {group_name} → {category}")
                print(f"     Type: {vendor_type}, Amount: ${amount:,.2f}")
                print(f"     Status: {recommendation['status']}")
                if enhanced_data.get('enhanced_insights'):
                    print(f"     Insights: {enhanced_data['enhanced_insights'][0]}")
    
    # Step 4: Generate dashboard data structure for existing dashboard
    dashboard_data = {
        'vendors_by_category': vendors_by_category,
        'enhanced_analysis': enhanced_results,
        'summary': {
            'total_vendors': sum(len(v) for v in vendors_by_category.values()),
            'ready_vendors': enhanced_results['summary']['ready_for_forecasting'],
            'manual_vendors': enhanced_results['summary']['need_manual_setup'],
            'monitoring_vendors': enhanced_results['summary']['need_monitoring']
        }
    }
    
    print(f"\n📋 Dashboard Summary:")
    print(f"  Total Active Vendors: {dashboard_data['summary']['total_vendors']}")
    print(f"  Ready for Forecasting: {dashboard_data['summary']['ready_vendors']}")
    print(f"  Need Manual Setup: {dashboard_data['summary']['manual_vendors']}")
    print(f"  Need Monitoring: {dashboard_data['summary']['monitoring_vendors']}")
    
    # Step 5: Create actionable recommendations
    recommendations = generate_actionable_recommendations(enhanced_results)
    
    print(f"\n🎯 Key Recommendations:")
    for rec in recommendations[:5]:  # Show top 5
        print(f"  • {rec}")
    
    return dashboard_data

def generate_actionable_recommendations(enhanced_results: dict) -> list:
    """Generate actionable recommendations from enhanced analysis"""
    recommendations = []
    
    for group_name, analysis in enhanced_results['vendor_groups'].items():
        if 'overall_recommendation' not in analysis:
            continue
            
        recommendation = analysis['overall_recommendation']
        status = recommendation['status']
        
        if status == 'manual_setup_required':
            classification = analysis.get('classification', {})
            vendor_type = classification.get('vendor_type', 'unknown')
            pattern = analysis.get('pattern_analysis', {})
            amount = pattern.get('weighted_average', 0)
            
            if vendor_type == 'contractor_platform' and amount != 0:
                recommendations.append(
                    f"Set up {group_name}: Use monthly budget of ${abs(amount) * 4.33:,.0f} "
                    f"distributed as bi-weekly contractor payments"
                )
            elif vendor_type == 'professional_services' and amount != 0:
                recommendations.append(
                    f"Set up {group_name}: Budget ${abs(amount):,.0f} monthly for legal/consulting services"
                )
            elif amount == 0:
                recommendations.append(
                    f"Add manual forecast for {group_name}: No historical data available"
                )
        
        elif status == 'ready_with_monitoring':
            recommendations.append(
                f"Monitor {group_name}: Pattern detected but needs validation"
            )
        
        # Add insights as recommendations
        insights = analysis.get('enhanced_insights', [])
        for insight in insights:
            if 'manual' in insight.lower() or 'setup' in insight.lower():
                recommendations.append(f"{group_name}: {insight}")
    
    return recommendations

def main():
    """Main execution"""
    dashboard_data = generate_enhanced_dashboard()
    
    print(f"\n✅ Enhanced Dashboard Generated Successfully!")
    print(f"📊 Use this data to:")
    print(f"   1. Update vendor forecasting methods")
    print(f"   2. Set manual budgets for irregular vendors") 
    print(f"   3. Monitor pattern changes over time")
    print(f"   4. Apply business logic to improve accuracy")
    
    return dashboard_data

if __name__ == "__main__":
    main()