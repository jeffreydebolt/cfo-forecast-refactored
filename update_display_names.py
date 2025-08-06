import csv
import logging
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from supabase_client import supabase

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

CSV_PATH = 'variance_review_spyguy.csv'  # Using the CSV we generated earlier

def str_to_bool(s):
    return str(s).strip().lower() in ('true', '1', 'yes')

def main():
    try:
        with open(CSV_PATH, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                vendor_name = row['vendor_name']
                new_display = row['fix to'].strip() if row.get('fix to') else row['vendor_group']
                review_needed = str_to_bool(row.get('review_needed', False))

                # Special handling for GUSTO transactions
                if 'GUSTO' in vendor_name:
                    new_display = 'Gusto'
                    review_needed = False

                logger.info(f"Updating {vendor_name} → {new_display} (review_needed={review_needed})")
                
                res = supabase.table('vendors') \
                    .update({
                        'display_name': new_display,
                        'review_needed': review_needed
                    }) \
                    .eq('vendor_name', vendor_name) \
                    .eq('client_id', 'spyguy') \
                    .execute()
                
                if hasattr(res, 'error') and res.error:
                    logger.error(f"❌ Failed to update {vendor_name}: {res.error}")
                else:
                    logger.info(f"✅ Updated {vendor_name} → {new_display} (review_needed={review_needed})")

    except Exception as e:
        logger.error(f"Error processing CSV: {str(e)}")
        raise

if __name__ == '__main__':
    main() 