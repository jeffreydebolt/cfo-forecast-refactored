import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import logging
from typing import List, Dict, Any
from supabase_client import supabase
from config.client_context import get_current_client
from vendor_forecast import (
    read_transactions_by_display_name,
    classify_vendor,
    compute_forecast,
    update_vendor_config,
    spot_check_forecast
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_all_display_names(client_id: str = None) -> List[str]:
    """Get all unique display names from vendors table."""
    if client_id is None:
        client_id = get_current_client()
    
    resp = supabase.table("vendors") \
        .select("display_name") \
        .eq("client_id", client_id) \
        .execute()
    return list(set(v["display_name"] for v in resp.data))

def process_vendor(
    display_name: str,
    client_id: str = None
) -> Dict[str, Any]:
    """Process a single vendor through the forecasting pipeline."""
    if client_id is None:
        client_id = get_current_client()
    
    try:
        logger.info(f"\nProcessing {display_name} for client {client_id}...")
        
        # 1. Read transactions with 365-day lookback
        transactions = read_transactions_by_display_name(display_name, client_id, lookback_days=365)
        if not transactions:
            logger.warning(f"No transactions found for {display_name}")
            return {
                "display_name": display_name,
                "status": "skipped",
                "reason": "No transactions found"
            }
            
        # 2. Classify vendor
        classification = classify_vendor(transactions)
        logger.info(f"Classification: {classification['classification']} ({classification['confidence']:.1f})")
        
        # 3. Compute forecast
        forecast = compute_forecast(transactions, classification["classification"])
        logger.info(f"Forecast: {forecast['method']} ({forecast['confidence']:.1f})")
        
        # 4. Spot check
        spot_check = spot_check_forecast(display_name, transactions, forecast)
        if spot_check["needs_review"]:
            logger.warning(f"⚠️ Needs review: {spot_check['explanation']}")
            if spot_check["issues"]:
                logger.warning("Issues found:")
                for issue in spot_check["issues"]:
                    logger.warning(f"  - {issue}")
                    
        # 5. Update config
        success = update_vendor_config(display_name, forecast, client_id)
        
        return {
            "display_name": display_name,
            "status": "success" if success else "failed",
            "classification": classification,
            "forecast": forecast,
            "spot_check": spot_check
        }
        
    except Exception as e:
        logger.error(f"Error processing {display_name}: {str(e)}")
        return {
            "display_name": display_name,
            "status": "error",
            "error": str(e)
        }

def main():
    """Run the forecasting pipeline for all vendors."""
    try:
        client_id = get_current_client()
        logger.info(f"Running forecast pipeline for client: {client_id}")
        
        # Get all display names
        display_names = get_all_display_names(client_id)
        logger.info(f"Found {len(display_names)} vendors to process")
        
        # Process each vendor
        results = []
        for display_name in display_names:
            result = process_vendor(display_name, client_id)
            results.append(result)
            
        # Print summary
        logger.info("\nForecasting Pipeline Summary:")
        logger.info("-" * 80)
        
        status_counts = {}
        for result in results:
            status = result["status"]
            status_counts[status] = status_counts.get(status, 0) + 1
            
        for status, count in status_counts.items():
            logger.info(f"{status}: {count}")
            
        # List vendors needing review
        needs_review = [
            r["display_name"] for r in results
            if r.get("spot_check", {}).get("needs_review", False)
        ]
        
        if needs_review:
            logger.info("\nVendors needing review:")
            for name in needs_review:
                logger.info(f"  - {name}")
                
        logger.info("\n✅ Forecasting pipeline complete")
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        raise

if __name__ == "__main__":
    main() 