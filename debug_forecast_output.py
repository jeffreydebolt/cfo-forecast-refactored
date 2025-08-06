"""
Debug script to analyze and visualize vendor forecast configurations.
"""

import logging
from supabase_client import supabase
from tabulate import tabulate
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_all_vendors() -> List[Dict[str, Any]]:
    """Fetch all vendors with their forecast configurations."""
    try:
        response = supabase.table('vendors').select('*').execute()
        return response.data
    except Exception as e:
        logger.error(f"Error fetching vendors: {str(e)}")
        return []

def format_vendor_row(vendor: Dict[str, Any]) -> List[Any]:
    """Format vendor data for tabular display."""
    return [
        vendor['vendor_name'],
        vendor.get('vendor_group', 'N/A'),
        vendor.get('forecast_method', 'N/A'),
        vendor.get('forecast_frequency', 'N/A'),
        vendor.get('forecast_day', 'N/A'),
        f"{vendor.get('forecast_confidence', 0):.2f}",
        '✓' if vendor.get('is_revenue', False) else '✗',
        '✓' if vendor.get('is_refund', False) else '✗',
        '🔒' if vendor.get('group_locked', False) else '🔓',
        vendor.get('forecast_notes', '')[:50] + '...' if vendor.get('forecast_notes', '') else 'N/A'
    ]

def analyze_forecast_configs():
    """Analyze and display vendor forecast configurations."""
    vendors = get_all_vendors()
    
    if not vendors:
        logger.error("No vendors found")
        return
        
    # Prepare data for display
    headers = ['Vendor Name', 'Group', 'Method', 'Frequency', 'Day', 
              'Confidence', 'Revenue', 'Refund', 'Locked', 'Notes']
    
    # Sort vendors by confidence (lowest first)
    vendors.sort(key=lambda x: x.get('forecast_confidence', 0))
    
    # Format rows
    rows = [format_vendor_row(v) for v in vendors]
    
    # Print summary statistics
    total = len(vendors)
    manual = sum(1 for v in vendors if v.get('forecast_method') == 'Manual')
    low_confidence = sum(1 for v in vendors if v.get('forecast_confidence', 0) < 0.5)
    locked = sum(1 for v in vendors if v.get('group_locked', False))
    
    print("\n=== Forecast Configuration Analysis ===\n")
    print(f"Total Vendors: {total}")
    print(f"Manual Method: {manual} ({manual/total*100:.1f}%)")
    print(f"Low Confidence (<0.5): {low_confidence} ({low_confidence/total*100:.1f}%)")
    print(f"Locked Configs: {locked} ({locked/total*100:.1f}%)")
    
    print("\n=== Vendors Requiring Review (Confidence < 0.5) ===\n")
    review_rows = [row for row, vendor in zip(rows, vendors) 
                  if vendor.get('forecast_confidence', 0) < 0.5]
    if review_rows:
        print(tabulate(review_rows, headers=headers, tablefmt='grid'))
    else:
        print("No vendors require review!")
    
    print("\n=== All Vendors ===\n")
    print(tabulate(rows, headers=headers, tablefmt='grid'))

if __name__ == "__main__":
    analyze_forecast_configs() 