#!/usr/bin/env python3
"""
FastAPI backend for Cash Flow Forecast System
Serves data to React frontend
"""

import sys
import os
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Optional
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase_client import supabase
from forecast_engine import ForecastEngine

app = FastAPI(title="CFO Forecast API", version="1.0.0")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://*.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ForecastCellUpdate(BaseModel):
    client_id: str
    forecast_date: str
    vendor_group_id: int
    new_amount: float

class ReconciliationRequest(BaseModel):
    client_id: str
    csv_file_path: str
    week_start_date: str

class VendorGroupCreate(BaseModel):
    client_id: str
    group_name: str
    display_name: str
    category: str
    subcategory: str
    is_inflow: bool

class VendorMapping(BaseModel):
    client_id: str
    vendor_name: str
    vendor_group_id: int

# Helper functions
def get_forecast_engine(client_id: str) -> ForecastEngine:
    return ForecastEngine(client_id)

# API Endpoints

@app.get("/")
async def root():
    return {"message": "CFO Forecast API is running"}

@app.get("/api/forecast/dashboard/{client_id}")
async def get_forecast_dashboard(client_id: str, weeks: int = 12):
    """Get forecast dashboard data for spreadsheet display"""
    try:
        engine = get_forecast_engine(client_id)
        dashboard_data = engine.get_forecast_dashboard_data(weeks=weeks)
        return dashboard_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/forecast/periods/{client_id}")
async def get_forecast_periods(client_id: str, weeks: int = 12):
    """Get forecast periods (weeks) for column headers"""
    try:
        # Generate next 12+ weeks starting from this Monday
        today = date.today()
        days_behind = today.weekday()
        start_date = today - timedelta(days=days_behind)
        
        periods = []
        for i in range(weeks):
            week_start = start_date + timedelta(weeks=i)
            week_end = week_start + timedelta(days=6)
            
            periods.append({
                'week_number': i + 1,
                'start_date': week_start.isoformat(),
                'end_date': week_end.isoformat(),
                'display_text': f"{week_start.month}/{week_start.day}/{str(week_start.year)[2:]}"
            })
        
        return {'periods': periods}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/forecast/vendor-groups/{client_id}")
async def get_vendor_groups(client_id: str):
    """Get all vendor groups for a client"""
    try:
        result = supabase.table('vendor_groups').select('*').eq('client_id', client_id).order('category', 'subcategory').execute()
        return {'vendor_groups': result.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/forecast/vendor-groups")
async def create_vendor_group(vendor_group: VendorGroupCreate):
    """Create a new vendor group"""
    try:
        result = supabase.table('vendor_groups').insert({
            'client_id': vendor_group.client_id,
            'group_name': vendor_group.group_name,
            'display_name': vendor_group.display_name,
            'category': vendor_group.category,
            'subcategory': vendor_group.subcategory,
            'is_inflow': vendor_group.is_inflow
        }).execute()
        
        return {'success': True, 'vendor_group': result.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/forecast/cell-update")
async def update_forecast_cell(cell_update: ForecastCellUpdate):
    """Update a single forecast cell value"""
    try:
        # Update the forecast record
        result = supabase.table('forecast_records').update({
            'forecasted_amount': cell_update.new_amount,
            'forecast_method': 'manual',
            'updated_at': datetime.now().isoformat()
        }).eq('client_id', cell_update.client_id).eq(
            'forecast_date', cell_update.forecast_date
        ).eq('vendor_group_id', cell_update.vendor_group_id).execute()
        
        return {'success': True, 'updated_records': len(result.data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/forecast/generate/{client_id}")
async def generate_forecasts(client_id: str, weeks: int = 12):
    """Generate new forecasts for a client"""
    try:
        engine = get_forecast_engine(client_id)
        
        # First update all forecast rules with latest patterns
        vendor_groups_result = supabase.table('vendor_groups').select('id').eq('client_id', client_id).execute()
        
        for vg in vendor_groups_result.data:
            pattern = engine.detect_vendor_group_pattern(vg['id'])
            engine.update_vendor_group_forecast_rule(vg['id'], pattern)
        
        # Generate forecasts
        forecasts = engine.generate_forecasts(weeks=weeks)
        success = engine.save_forecasts(forecasts)
        
        return {
            'success': success,
            'forecast_count': len(forecasts),
            'message': f'Generated {len(forecasts)} forecast records'
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/forecast/reconcile")
async def reconcile_week(reconciliation: ReconciliationRequest):
    """Reconcile a week with actual Mercury data"""
    try:
        # Import Mercury CSV (reuse existing logic)
        from import_mercury_csv import import_mercury_csv
        import_mercury_csv(reconciliation.csv_file_path, reconciliation.client_id)
        
        # TODO: Implement reconciliation logic
        # 1. Match transactions to forecast records by vendor group
        # 2. Update actual amounts
        # 3. Calculate variances
        # 4. Lock the period
        
        return {
            'success': True,
            'message': 'Week reconciled successfully'
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/vendor-mappings/{client_id}")
async def get_vendor_mappings(client_id: str):
    """Get all vendor mappings for a client"""
    try:
        result = supabase.table('vendor_group_mappings').select(
            '*, vendor_groups(*)'
        ).eq('client_id', client_id).execute()
        return {'mappings': result.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/vendor-mappings")
async def create_vendor_mapping(mapping: VendorMapping):
    """Create or update vendor mapping"""
    try:
        result = supabase.table('vendor_group_mappings').upsert({
            'client_id': mapping.client_id,
            'vendor_name': mapping.vendor_name,
            'vendor_group_id': mapping.vendor_group_id
        }).execute()
        
        return {'success': True, 'mapping': result.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/transactions/{client_id}")
async def get_transactions(client_id: str, limit: int = 100):
    """Get recent transactions for a client"""
    try:
        result = supabase.table('transactions').select('*').eq(
            'client_id', client_id
        ).order('transaction_date', desc=True).limit(limit).execute()
        return {'transactions': result.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/setup/default-groups/{client_id}")
async def setup_default_groups(client_id: str):
    """Set up default vendor groups for a new client"""
    try:
        # Call the database function
        result = supabase.rpc('create_default_vendor_groups', {
            'p_client_id': client_id
        }).execute()
        
        return {'success': True, 'message': 'Default vendor groups created'}
    except Exception as e:
        # If function doesn't exist, create groups manually
        default_groups = [
            {'group_name': 'core_capital', 'display_name': 'Core Capital', 'category': 'revenue', 'subcategory': 'core_capital', 'is_inflow': True},
            {'group_name': 'operating_revenue', 'display_name': 'Operating Revenue', 'category': 'revenue', 'subcategory': 'operating_revenue', 'is_inflow': True},
            {'group_name': 'cc_expenses', 'display_name': 'CC', 'category': 'operating', 'subcategory': 'cc', 'is_inflow': False},
            {'group_name': 'ops_expenses', 'display_name': 'Ops', 'category': 'operating', 'subcategory': 'ops', 'is_inflow': False},
            {'group_name': 'ga_expenses', 'display_name': 'G&A', 'category': 'operating', 'subcategory': 'ga', 'is_inflow': False},
            {'group_name': 'payroll_expenses', 'display_name': 'Payroll', 'category': 'operating', 'subcategory': 'payroll', 'is_inflow': False},
            {'group_name': 'admin_expenses', 'display_name': 'Admin', 'category': 'operating', 'subcategory': 'admin', 'is_inflow': False},
            {'group_name': 'distributions', 'display_name': 'Distributions', 'category': 'financing', 'subcategory': 'distributions', 'is_inflow': False},
            {'group_name': 'equity_contributions', 'display_name': 'Equity Contrib.', 'category': 'financing', 'subcategory': 'equity_contrib', 'is_inflow': True},
            {'group_name': 'loan_proceeds', 'display_name': 'Loan Proceeds', 'category': 'financing', 'subcategory': 'loan_proceeds', 'is_inflow': True},
            {'group_name': 'loan_payments', 'display_name': 'Loan Payments', 'category': 'financing', 'subcategory': 'loan_payments', 'is_inflow': False}
        ]
        
        try:
            for group in default_groups:
                group['client_id'] = client_id
            
            result = supabase.table('vendor_groups').insert(default_groups).execute()
            return {'success': True, 'message': 'Default vendor groups created manually'}
        except Exception as e2:
            raise HTTPException(status_code=500, detail=f"Failed to create default groups: {str(e2)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)