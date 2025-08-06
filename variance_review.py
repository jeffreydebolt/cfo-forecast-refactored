import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import csv
from supabase_client import supabase
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def export_variance_review_with_raw(client_id="spyguy"):
    """
    Export vendor variance review data including both display_name and raw vendor_name.
    
    Args:
        client_id: The client ID to export data for
    """
    try:
        # 1) Pull flagged vendors with all metrics
        logger.info(f"Fetching vendor data for client {client_id}")
        resp = supabase.table("vendors") \
            .select("""
                vendor_name,
                display_name,
                vendor_group,
                amount_mean,
                amount_stddev,
                forecast_notes,
                review_needed
            """) \
            .eq("client_id", client_id) \
            .execute()
        vendors = resp.data
        
        if not vendors:
            logger.warning(f"No vendors found for client {client_id}")
            return
            
        # 2) Write out CSV with both raw + friendly names
        output_file = f"variance_review_{client_id}.csv"
        logger.info(f"Writing vendor data to {output_file}")
        
        with open(output_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "display_name",
                "vendor_name",
                "vendor_group",
                "amount_mean",
                "amount_stddev",
                "forecast_notes",
                "review_needed",
            ])
            writer.writeheader()
            for v in vendors:
                writer.writerow({
                    "display_name": v["display_name"],
                    "vendor_name": v["vendor_name"],
                    "vendor_group": v.get("vendor_group", ""),
                    "amount_mean": v.get("amount_mean", ""),
                    "amount_stddev": v.get("amount_stddev", ""),
                    "forecast_notes": v.get("forecast_notes", ""),
                    "review_needed": v.get("review_needed", False),
                })
                
        logger.info(f"Successfully exported review file: {output_file}")
        
    except Exception as e:
        logger.error(f"Error exporting variance review: {str(e)}")
        raise

if __name__ == "__main__":
    export_variance_review_with_raw() 