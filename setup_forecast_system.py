#!/usr/bin/env python3
"""
Setup script for Cash Flow Forecast System
Initializes database tables and creates sample data
"""

import sys
import os
from datetime import date, datetime, timedelta
import json

sys.path.append('.')
from supabase_client import supabase
from forecast_engine import ForecastEngine

def setup_database_tables():
    """Create all necessary database tables"""
    print("🗄️ Setting up database tables...")
    
    # Read and execute schema
    schema_path = 'database/forecast_schema.sql'
    try:
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        
        # Split into individual statements and execute
        statements = schema_sql.split(';')
        
        for statement in statements:
            statement = statement.strip()
            if statement and not statement.startswith('--'):
                try:
                    result = supabase.rpc('exec_sql', {'sql': statement}).execute()
                    print(f"✅ Executed: {statement[:50]}...")
                except Exception as e:
                    print(f"⚠️ Warning executing statement: {e}")
        
        print("✅ Database tables created successfully")
        return True
    except FileNotFoundError:
        print(f"❌ Schema file not found: {schema_path}")
        return False
    except Exception as e:
        print(f"❌ Error setting up tables: {e}")
        return False

def setup_client_default_groups(client_id: str):
    """Set up default vendor groups for a client"""
    print(f"👤 Setting up default vendor groups for client: {client_id}")
    
    default_groups = [
        # Revenue groups
        {
            'client_id': client_id,
            'group_name': 'core_capital',
            'display_name': 'Core Capital',
            'category': 'revenue',
            'subcategory': 'core_capital',
            'is_inflow': True
        },
        {
            'client_id': client_id,
            'group_name': 'operating_revenue',
            'display_name': 'Operating Revenue',
            'category': 'revenue',
            'subcategory': 'operating_revenue',
            'is_inflow': True
        },
        
        # Operating expense groups
        {
            'client_id': client_id,
            'group_name': 'cc_expenses',
            'display_name': 'CC',
            'category': 'operating',
            'subcategory': 'cc',
            'is_inflow': False
        },
        {
            'client_id': client_id,
            'group_name': 'ops_expenses',
            'display_name': 'Ops',
            'category': 'operating',
            'subcategory': 'ops',
            'is_inflow': False
        },
        {
            'client_id': client_id,
            'group_name': 'ga_expenses',
            'display_name': 'G&A',
            'category': 'operating',
            'subcategory': 'ga',
            'is_inflow': False
        },
        {
            'client_id': client_id,
            'group_name': 'payroll_expenses',
            'display_name': 'Payroll',
            'category': 'operating',
            'subcategory': 'payroll',
            'is_inflow': False
        },
        {
            'client_id': client_id,
            'group_name': 'admin_expenses',
            'display_name': 'Admin',
            'category': 'operating',
            'subcategory': 'admin',
            'is_inflow': False
        },
        
        # Financing groups
        {
            'client_id': client_id,
            'group_name': 'distributions',
            'display_name': 'Distributions',
            'category': 'financing',
            'subcategory': 'distributions',
            'is_inflow': False
        },
        {
            'client_id': client_id,
            'group_name': 'equity_contributions',
            'display_name': 'Equity Contrib.',
            'category': 'financing',
            'subcategory': 'equity_contrib',
            'is_inflow': True
        },
        {
            'client_id': client_id,
            'group_name': 'loan_proceeds',
            'display_name': 'Loan Proceeds',
            'category': 'financing',
            'subcategory': 'loan_proceeds',
            'is_inflow': True
        },
        {
            'client_id': client_id,
            'group_name': 'loan_payments',
            'display_name': 'Loan Payments',
            'category': 'financing',
            'subcategory': 'loan_payments',
            'is_inflow': False
        }
    ]
    
    try:
        result = supabase.table('vendor_groups').insert(default_groups).execute()
        print(f"✅ Created {len(result.data)} default vendor groups")
        return result.data
    except Exception as e:
        print(f"❌ Error creating vendor groups: {e}")
        return []

def create_sample_vendor_mappings(client_id: str, vendor_groups):
    """Create sample vendor mappings for demonstration"""
    print("🔗 Creating sample vendor mappings...")
    
    # Find group IDs
    group_map = {vg['group_name']: vg['id'] for vg in vendor_groups}
    
    sample_mappings = [
        # Revenue mappings
        {'vendor_name': 'AMAZON.COM SERVICES LLC', 'group_name': 'operating_revenue'},
        {'vendor_name': 'Amazon.com Svcs LLC', 'group_name': 'operating_revenue'},
        {'vendor_name': 'SHOPIFY PAYMENTS', 'group_name': 'operating_revenue'},
        {'vendor_name': 'STRIPE', 'group_name': 'operating_revenue'},
        {'vendor_name': 'AFFIRM', 'group_name': 'operating_revenue'},
        
        # Operating expense mappings
        {'vendor_name': 'AMERICAN EXPRESS', 'group_name': 'cc_expenses'},
        {'vendor_name': 'CHASE CREDIT CARD', 'group_name': 'cc_expenses'},
        {'vendor_name': 'Facebook', 'group_name': 'ops_expenses'},
        {'vendor_name': 'Google Ads', 'group_name': 'ops_expenses'},
        {'vendor_name': 'QUICKBOOKS', 'group_name': 'ga_expenses'},
        {'vendor_name': 'GUSTO', 'group_name': 'payroll_expenses'},
        
        # Financing mappings
        {'vendor_name': 'OWNER DISTRIBUTION', 'group_name': 'distributions'},
        {'vendor_name': 'CAPITAL INJECTION', 'group_name': 'equity_contributions'},
    ]
    
    mappings_to_insert = []
    for mapping in sample_mappings:
        if mapping['group_name'] in group_map:
            mappings_to_insert.append({
                'client_id': client_id,
                'vendor_name': mapping['vendor_name'],
                'vendor_group_id': group_map[mapping['group_name']]
            })
    
    try:
        result = supabase.table('vendor_group_mappings').insert(mappings_to_insert).execute()
        print(f"✅ Created {len(result.data)} sample vendor mappings")
        return result.data
    except Exception as e:
        print(f"❌ Error creating vendor mappings: {e}")
        return []

def create_initial_cash_balance(client_id: str, balance: float = 476121.0):
    """Create initial cash balance"""
    print(f"💰 Setting initial cash balance: ${balance:,.0f}")
    
    today = date.today()
    # Set balance for this Monday
    days_behind = today.weekday()
    monday = today - timedelta(days=days_behind)
    
    cash_balance = {
        'client_id': client_id,
        'balance_date': monday.isoformat(),
        'beginning_balance': balance,
        'is_actual': True
    }
    
    try:
        result = supabase.table('cash_balances').insert([cash_balance]).execute()
        print(f"✅ Set initial cash balance for {monday}")
        return result.data[0]
    except Exception as e:
        print(f"❌ Error setting cash balance: {e}")
        return None

def create_sample_forecast_rules(client_id: str, vendor_groups):
    """Create sample forecast rules for demonstration"""
    print("📊 Creating sample forecast rules...")
    
    # Find group IDs
    group_map = {vg['group_name']: vg['id'] for vg in vendor_groups}
    
    sample_rules = [
        {
            'group_name': 'core_capital',
            'frequency': 'weekly',
            'timing_details': {'day_of_week': 0},  # Monday
            'base_amount': 250000
        },
        {
            'group_name': 'operating_revenue',
            'frequency': 'daily',
            'timing_details': {'days_of_week': [0, 1, 2, 3, 4]},  # M-F
            'base_amount': 2400
        },
        {
            'group_name': 'cc_expenses',
            'frequency': 'bi-weekly',
            'timing_details': {'days_of_month': [15, 30]},
            'base_amount': -46655
        },
        {
            'group_name': 'ops_expenses',
            'frequency': 'weekly',
            'timing_details': {'day_of_week': 1},  # Tuesday
            'base_amount': -21431
        },
        {
            'group_name': 'ga_expenses',
            'frequency': 'monthly',
            'timing_details': {'day_of_month': 1},
            'base_amount': -3737
        },
        {
            'group_name': 'payroll_expenses',
            'frequency': 'bi-weekly',
            'timing_details': {'interval_weeks': 2, 'day_of_week': 4},  # Every other Friday
            'base_amount': -33208
        },
        {
            'group_name': 'admin_expenses',
            'frequency': 'irregular',
            'timing_details': {},
            'base_amount': -200
        },
        {
            'group_name': 'distributions',
            'frequency': 'monthly',
            'timing_details': {'day_of_month': 1},
            'base_amount': -200000
        }
    ]
    
    rules_to_insert = []
    for rule in sample_rules:
        if rule['group_name'] in group_map:
            rules_to_insert.append({
                'client_id': client_id,
                'vendor_group_id': group_map[rule['group_name']],
                'frequency': rule['frequency'],
                'timing_details': json.dumps(rule['timing_details']),
                'base_amount': rule['base_amount'],
                'amount_method': 'manual',
                'is_active': True
            })
    
    try:
        result = supabase.table('vendor_forecast_rules').insert(rules_to_insert).execute()
        print(f"✅ Created {len(result.data)} forecast rules")
        return result.data
    except Exception as e:
        print(f"❌ Error creating forecast rules: {e}")
        return []

def generate_initial_forecasts(client_id: str):
    """Generate initial forecast records"""
    print("🔮 Generating initial forecasts...")
    
    try:
        engine = ForecastEngine(client_id)
        forecasts = engine.generate_forecasts(weeks=12)
        success = engine.save_forecasts(forecasts)
        
        if success:
            print(f"✅ Generated {len(forecasts)} forecast records")
            return True
        else:
            print("❌ Failed to save forecasts")
            return False
    except Exception as e:
        print(f"❌ Error generating forecasts: {e}")
        return False

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Setup Cash Flow Forecast System')
    parser.add_argument('--client', required=True, help='Client ID to setup')
    parser.add_argument('--skip-tables', action='store_true', help='Skip table creation')
    parser.add_argument('--balance', type=float, default=476121.0, help='Initial cash balance')
    args = parser.parse_args()
    
    client_id = args.client
    
    print(f"🚀 Setting up Cash Flow Forecast System for client: {client_id}")
    print("=" * 60)
    
    # Step 1: Create database tables
    if not args.skip_tables:
        setup_success = setup_database_tables()
        if not setup_success:
            print("❌ Database setup failed. Exiting.")
            return False
    else:
        print("⏭️ Skipping table creation")
    
    # Step 2: Create default vendor groups
    vendor_groups = setup_client_default_groups(client_id)
    if not vendor_groups:
        print("❌ Failed to create vendor groups. Exiting.")
        return False
    
    # Step 3: Create sample vendor mappings
    create_sample_vendor_mappings(client_id, vendor_groups)
    
    # Step 4: Set initial cash balance
    create_initial_cash_balance(client_id, args.balance)
    
    # Step 5: Create sample forecast rules
    create_sample_forecast_rules(client_id, vendor_groups)
    
    # Step 6: Generate initial forecasts
    generate_initial_forecasts(client_id)
    
    print("\n" + "=" * 60)
    print("✅ SETUP COMPLETE!")
    print(f"\n🎯 Next steps:")
    print(f"1. Start the API server: cd api && python main.py")
    print(f"2. Start the frontend: cd cfo-forecast-app && npm run dev")
    print(f"3. Visit: http://localhost:3000/dashboard/{client_id}/forecast")
    print(f"4. Import Mercury CSV data via the reconciliation panel")
    print(f"5. Customize vendor groups and mappings as needed")
    
    return True

if __name__ == "__main__":
    main()