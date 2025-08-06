import csv
import logging
import os
import sys
from datetime import datetime

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from supabase_client import supabase

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def export_mappings(output_path="data/vendor_mappings_review.csv"):
    """
    Export vendor mappings from Supabase to a CSV file.
    
    Args:
        output_path (str): Path where the CSV file will be saved
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Ensure data directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Fetch all vendor mappings
        logger.info("Fetching vendor mappings from Supabase...")
        resp = supabase.table("vendors")\
            .select("vendor_name,display_name,category,review_needed,group_locked")\
            .execute()
        
        if not resp.data:
            logger.warning("No vendor mappings found in the database")
            return False
            
        vendors = resp.data
        logger.info(f"Retrieved {len(vendors)} vendor mappings")

        # Write CSV
        logger.info(f"Writing mappings to {output_path}")
        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=vendors[0].keys())
            writer.writeheader()
            writer.writerows(vendors)
            
        logger.info(f"Successfully exported {len(vendors)} mappings to {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error exporting vendor mappings: {str(e)}")
        return False

if __name__ == "__main__":
    # Add timestamp to output filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"data/vendor_mappings_review_{timestamp}.csv"
    
    if export_mappings(output_path):
        print(f"\nExport completed successfully!")
        print(f"File saved to: {output_path}")
    else:
        print("\nExport failed. Check the logs for details.") 