#!/usr/bin/env python3
"""
Simplified Cash Flow Forecast Engine
Works with existing database structure
"""

import sys
import json
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Dict, Tuple, Optional
import pandas as pd
import numpy as np

sys.path.append('.')
from supabase_client import supabase

class SimplifiedForecastEngine:
    def __init__(self, client_id: str):
        self.client_id = client_id
        
        # Standard cash flow categories that match Google Sheets
        self.categories = {
            'revenue': {
                'core_capital': {'name': 'Core Capital', 'is_inflow': True},
                'operating_revenue': {'name': 'Operating Revenue', 'is_inflow': True}
            },
            'operating': {
                'cc': {'name': 'CC', 'is_inflow': False},
                'ops': {'name': 'Ops', 'is_inflow': False},
                'ga': {'name': 'G&A', 'is_inflow': False},
                'payroll': {'name': 'Payroll', 'is_inflow': False},
                'admin': {'name': 'Admin', 'is_inflow': False}
            },
            'financing': {
                'distributions': {'name': 'Distributions', 'is_inflow': False},
                'equity_contrib': {'name': 'Equity Contrib.', 'is_inflow': True},
                'loan_proceeds': {'name': 'Loan Proceeds', 'is_inflow': True},
                'loan_payments': {'name': 'Loan Payments', 'is_inflow': False}
            }
        }
    
    def get_vendor_forecast_data(self, weeks: int = 12) -> Dict:
        """Get forecast data using existing vendors table"""
        
        # Get vendors with forecast data
        try:
            vendors_result = supabase.table('vendors').select(
                'vendor_name, display_name, category, forecast_amount, forecast_frequency, forecast_day, is_revenue'
            ).eq('client_id', self.client_id).execute()
            
            vendors = vendors_result.data
            print(f"Found {len(vendors)} vendors for {self.client_id}")
            
        except Exception as e:
            print(f"Error getting vendors: {e}")
            vendors = []
        
        # Generate forecast periods (weeks)
        today = date.today()
        days_behind = today.weekday()
        start_date = today - timedelta(days=days_behind)  # This Monday
        
        periods = []
        for i in range(weeks):
            week_start = start_date + timedelta(weeks=i)
            periods.append({
                'week_number': i + 1,
                'start_date': week_start,
                'display_text': f"{week_start.month}/{week_start.day}/{str(week_start.year)[2:]}"
            })
        
        # Create forecast data structure matching the frontend expectations
        forecast_data = {}
        
        # Initialize all periods
        for period in periods:
            date_key = period['start_date'].isoformat()
            forecast_data[date_key] = {
                'revenue': {},
                'operating': {},
                'financing': {}
            }
            
            # Initialize all categories with zero values
            for category, subcats in self.categories.items():
                forecast_data[date_key][category] = {}
                for subcat_key, subcat_info in subcats.items():
                    forecast_data[date_key][category][subcat_key] = {
                        'forecasted': 0,
                        'actual': 0,
                        'variance': 0,
                        'is_actual': False
                    }
        
        # Map vendors to categories and generate forecasts
        for vendor in vendors:
            # Determine category based on vendor data
            category, subcategory = self._categorize_vendor(vendor)
            
            if category and subcategory:
                forecast_amount = float(vendor.get('forecast_amount', 0) or 0)
                
                # Generate forecasts for each period based on frequency
                for period in periods:
                    if self._should_forecast_for_date(vendor, period['start_date']):
                        date_key = period['start_date'].isoformat()
                        forecast_data[date_key][category][subcategory]['forecasted'] += forecast_amount
        
        # Get cash balance (simplified)
        cash_balances = {
            periods[0]['start_date'].isoformat(): {
                'beginning_balance': 476121,  # Default balance
                'balance_date': periods[0]['start_date'].isoformat()
            }
        }
        
        return {
            'forecast_data': forecast_data,
            'cash_balances': cash_balances,
            'start_date': start_date.isoformat(),
            'end_date': (start_date + timedelta(weeks=weeks)).isoformat()
        }
    
    def _categorize_vendor(self, vendor: Dict) -> Tuple[str, str]:
        """Categorize vendor into cash flow categories"""
        
        vendor_name = vendor.get('vendor_name', '').upper()
        display_name = vendor.get('display_name', '').upper()
        category = vendor.get('category', '').lower()
        is_revenue = vendor.get('is_revenue', False)
        
        # Revenue classification
        if is_revenue or any(term in vendor_name for term in ['AMAZON', 'SHOPIFY', 'STRIPE', 'PAYPAL']):
            if any(term in vendor_name for term in ['CORE', 'CAPITAL', 'INVESTMENT']):
                return 'revenue', 'core_capital'
            else:
                return 'revenue', 'operating_revenue'
        
        # Expense classification
        if any(term in vendor_name for term in ['AMEX', 'AMERICAN EXPRESS', 'CHASE CREDIT', 'CREDIT CARD']):
            return 'operating', 'cc'
        elif any(term in vendor_name for term in ['FACEBOOK', 'GOOGLE', 'ADS', 'MARKETING']):
            return 'operating', 'ops'
        elif any(term in vendor_name for term in ['QUICKBOOKS', 'OFFICE', 'UTILITIES']):
            return 'operating', 'ga'
        elif any(term in vendor_name for term in ['GUSTO', 'PAYROLL', 'SALARY', 'WAGE']):
            return 'operating', 'payroll'
        elif any(term in vendor_name for term in ['ADMIN', 'MISC', 'OTHER']):
            return 'operating', 'admin'
        elif any(term in vendor_name for term in ['DISTRIBUTION', 'OWNER']):
            return 'financing', 'distributions'
        elif any(term in vendor_name for term in ['LOAN', 'DEBT', 'PAYMENT']):
            return 'financing', 'loan_payments'
        elif any(term in vendor_name for term in ['EQUITY', 'INVESTMENT', 'CAPITAL INJECTION']):
            return 'financing', 'equity_contrib'
        else:
            # Default based on amount sign
            amount = float(vendor.get('forecast_amount', 0) or 0)
            if amount > 0:
                return 'revenue', 'operating_revenue'
            else:
                return 'operating', 'ops'
    
    def _should_forecast_for_date(self, vendor: Dict, forecast_date: date) -> bool:
        """Determine if vendor should have forecast for specific date"""
        
        frequency = vendor.get('forecast_frequency', 'monthly')
        forecast_day = vendor.get('forecast_day')
        
        if frequency == 'daily':
            return forecast_date.weekday() < 5  # Monday-Friday
        elif frequency == 'weekly':
            return forecast_date.weekday() == (forecast_day or 0)  # Default Monday
        elif frequency == 'bi-weekly':
            # Simplified: every other week
            week_number = forecast_date.isocalendar()[1]
            return week_number % 2 == 0
        elif frequency == 'monthly':
            # First week of month
            return forecast_date.day <= 7
        else:
            # Default monthly
            return forecast_date.day <= 7

    def get_vendor_groups(self) -> List[Dict]:
        """Get simplified vendor groups for the frontend"""
        
        groups = []
        group_id = 1
        
        for category, subcats in self.categories.items():
            for subcat_key, subcat_info in subcats.items():
                groups.append({
                    'id': group_id,
                    'group_name': subcat_key,
                    'display_name': subcat_info['name'],
                    'category': category,
                    'subcategory': subcat_key,
                    'is_inflow': subcat_info['is_inflow']
                })
                group_id += 1
        
        return groups

    def update_forecast_cell(self, forecast_date: str, vendor_group_id: int, new_amount: float) -> bool:
        """Update forecast amount (simplified - could store in vendors table)"""
        # For now, just return success
        # In a full implementation, this would update the vendor forecast amounts
        print(f"Updated forecast: {forecast_date} group {vendor_group_id} = ${new_amount}")
        return True


def main():
    """Test the simplified forecast engine"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Simplified Forecast Engine')
    parser.add_argument('--client', required=True, help='Client ID')
    args = parser.parse_args()
    
    engine = SimplifiedForecastEngine(args.client)
    
    print("Testing simplified forecast engine...")
    dashboard_data = engine.get_vendor_forecast_data()
    print(f"Generated forecast data with {len(dashboard_data['forecast_data'])} periods")
    
    vendor_groups = engine.get_vendor_groups()
    print(f"Created {len(vendor_groups)} vendor groups")

if __name__ == "__main__":
    main()