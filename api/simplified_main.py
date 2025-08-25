#!/usr/bin/env python3
"""
Simplified FastAPI backend for Cash Flow Forecast System
Works with existing Supabase database structure
"""

import sys
import os
from datetime import date, datetime, timedelta
from typing import List, Dict, Optional

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from supabase_client import supabase
from simplified_forecast_engine import SimplifiedForecastEngine

app = FastAPI(title="CFO Forecast API (Simplified)", version="1.0.0")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://*.vercel.app", "*"],
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

# API Endpoints

@app.get("/")
async def root():
    return {"message": "CFO Forecast API (Simplified) is running"}

@app.get("/api/forecast/dashboard/{client_id}")
async def get_forecast_dashboard(client_id: str, weeks: int = 12):
    """Get forecast dashboard data for spreadsheet display"""
    try:
        engine = SimplifiedForecastEngine(client_id)
        dashboard_data = engine.get_vendor_forecast_data(weeks=weeks)
        return dashboard_data
    except Exception as e:
        print(f"Dashboard error: {e}")
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
        engine = SimplifiedForecastEngine(client_id)
        vendor_groups = engine.get_vendor_groups()
        return {'vendor_groups': vendor_groups}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/forecast/cell-update")
async def update_forecast_cell(cell_update: ForecastCellUpdate):
    """Update a single forecast cell value"""
    try:
        engine = SimplifiedForecastEngine(cell_update.client_id)
        success = engine.update_forecast_cell(
            cell_update.forecast_date,
            cell_update.vendor_group_id,
            cell_update.new_amount
        )
        return {'success': success, 'message': 'Forecast updated'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/forecast/generate/{client_id}")
async def generate_forecasts(client_id: str, weeks: int = 12):
    """Generate new forecasts for a client"""
    try:
        engine = SimplifiedForecastEngine(client_id)
        dashboard_data = engine.get_vendor_forecast_data(weeks=weeks)
        
        return {
            'success': True,
            'forecast_count': len(dashboard_data['forecast_data']),
            'message': f'Generated forecast for {weeks} weeks'
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/vendor-mappings/{client_id}")
async def get_vendor_mappings(client_id: str):
    """Get all vendors for a client (using existing vendors table)"""
    try:
        result = supabase.table('vendors').select('*').eq('client_id', client_id).execute()
        return {'mappings': result.data}
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
    """Set up default vendor groups (using existing vendors table structure)"""
    try:
        # Check if we already have vendors for this client
        result = supabase.table('vendors').select('*').eq('client_id', client_id).limit(5).execute()
        
        return {
            'success': True, 
            'message': f'Found {len(result.data)} existing vendors for {client_id}',
            'vendors': result.data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Simplified CFO Forecast API...")
    print("📊 Dashboard: http://localhost:3000/dashboard/BestSelf/forecast")
    print("🔧 API Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)