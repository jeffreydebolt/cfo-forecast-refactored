import logging
from typing import Dict, List, Tuple
import re
from supabase_client import supabase

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define vendor rules as (pattern, display_name, review_needed)
VENDOR_RULES: List[Tuple[str, str, bool]] = [
    # Payment Processors
    (r'.*STRIPE.*', 'Stripe', False),
    (r'.*PAYPAL.*', 'PayPal', False),
    (r'.*SHOPIFY.*', 'Shopify', False),
    (r'.*SHOPPAY.*', 'ShopPay', False),
    
    # Payroll
    (r'.*GUSTO.*', 'Gusto', False),
    
    # Sales Tax
    (r'.*SALES.*TAX.*', 'Sales Tax', False),
    (r'.*TAX.*PYMT.*', 'Sales Tax', False),
    (r'.*DEPT.*REVENUE.*', 'Sales Tax', False),
    (r'.*DEPT.*TAXATION.*', 'Sales Tax', False),
    
    # Loans
    (r'.*LOAN.*', 'Loan', True),
    (r'.*SBA.*', 'Loan', True),
    
    # Bank Transfers
    (r'.*TRANSFER.*', 'Bank Transfer', False),
    (r'.*MERCURY.*', 'Mercury', False),
    
    # AMEX (all AMEX transactions)
    (r'.*AMEX.*', 'American Express', False),
    
    # Default business transactions
    (r'.*SG ELECTRONICS.*', 'SG Electronics LLC', False),
]

def apply_vendor_rules():
    """Apply vendor rules to update display names in the database."""
    try:
        # Get all vendors for the client
        response = supabase.table('vendors') \
            .select('vendor_name,display_name,review_needed') \
            .eq('client_id', 'spyguy') \
            .execute()
        
        if hasattr(response, 'error') and response.error:
            logger.error(f"Failed to fetch vendors: {response.error}")
            return
        
        vendors = response.data
        updates = []
        
        for vendor in vendors:
            vendor_name = vendor['vendor_name']
            current_display = vendor['display_name']
            
            # Find matching rule
            new_display = None
            review_needed = None
            
            for pattern, display, needs_review in VENDOR_RULES:
                if re.search(pattern, vendor_name, re.IGNORECASE):
                    new_display = display
                    review_needed = needs_review
                    break
            
            # If no rule matches, keep current display name
            if new_display is None:
                new_display = current_display
                review_needed = vendor.get('review_needed', True)
            
            # Only update if there's a change
            if new_display != current_display or review_needed != vendor.get('review_needed'):
                updates.append({
                    'vendor_name': vendor_name,
                    'display_name': new_display,
                    'review_needed': review_needed
                })
                logger.info(f"Will update {vendor_name} → {new_display} (review_needed={review_needed})")
        
        # Apply updates in batches
        for update in updates:
            res = supabase.table('vendors') \
                .update({
                    'display_name': update['display_name'],
                    'review_needed': update['review_needed']
                }) \
                .eq('vendor_name', update['vendor_name']) \
                .eq('client_id', 'spyguy') \
                .execute()
            
            if hasattr(res, 'error') and res.error:
                logger.error(f"Failed to update {update['vendor_name']}: {res.error}")
            else:
                logger.info(f"✅ Updated {update['vendor_name']} → {update['display_name']}")
                
    except Exception as e:
        logger.error(f"Error applying vendor rules: {str(e)}")
        raise

if __name__ == '__main__':
    apply_vendor_rules() 