import csv
import logging
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from supabase_client import supabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_mappings():
    """Load mappings from CSV file."""
    mappings = {}
    with open('vendor_mapping_template.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            mappings[row['vendor_name']] = {
                'display_name': row['display_name'],
                'vendor_type': row['vendor_type'],
                'notes': row.get('notes', '')
            }
    return mappings

def apply_mappings():
    """Apply mappings to database."""
    mappings = load_mappings()
    
    # Get all vendors
    response = supabase.table('vendors') \
        .select('vendor_name,display_name,vendor_group') \
        .eq('client_id', 'spyguy') \
        .execute()
    
    if hasattr(response, 'error') and response.error:
        logger.error(f"Failed to fetch vendors: {response.error}")
        return
    
    vendors = response.data
    
    # Apply mappings
    for vendor in vendors:
        vendor_name = vendor['vendor_name']
        if vendor_name in mappings:
            mapping = mappings[vendor_name]
            logger.info(f"Updating {vendor_name} → {mapping['display_name']}")
            
            res = supabase.table('vendors') \
                .update({
                    'display_name': mapping['display_name'],
                    'vendor_group': mapping['vendor_type']
                }) \
                .eq('vendor_name', vendor_name) \
                .eq('client_id', 'spyguy') \
                .execute()
            
            if hasattr(res, 'error') and res.error:
                logger.error(f"Failed to update {vendor_name}: {res.error}")

if __name__ == '__main__':
    apply_mappings() 