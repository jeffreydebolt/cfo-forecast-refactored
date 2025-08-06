#!/usr/bin/env python3
"""
Check the structure of forecast data to understand available keys.
"""

import json
from services.forecast_service import ForecastService

def check_forecast_structure():
    """Check what keys are available in the forecast data."""
    
    service = ForecastService()
    
    # Generate a simple forecast
    weekly_forecast = service.generate_weekly_forecast_summary('bestself', weeks_ahead=2)
    
    if weekly_forecast:
        print("📊 Weekly forecast structure:")
        print(f"Number of weeks: {len(weekly_forecast)}")
        
        if len(weekly_forecast) > 0:
            print("\nFirst week keys:")
            for key in weekly_forecast[0].keys():
                print(f"  - {key}: {type(weekly_forecast[0][key])}")
            
            print("\nFirst week data:")
            print(json.dumps(weekly_forecast[0], indent=2, default=str))
    else:
        print("No forecast data generated")

if __name__ == "__main__":
    check_forecast_structure()