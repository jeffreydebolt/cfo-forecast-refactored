import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from supabase_client import supabase
import logging
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def update_vendor_rules(client_id="spyguy"):
    """
    Update vendor display names based on new rules.
    """
    try:
        # Define vendor patterns and their display names
        vendor_rules = [
            # State Sales Tax
            {
                "patterns": [
                    r'.*NJ S&U WEB PMT.*',
                    r'.*STATEOF MICHIGAN.*SUW TAXES.*',
                    r'.*COMP OF MARYLAND.*DIR DB RAD.*',
                    r'.*OHIO.*SALES.*TAX.*',
                    r'.*NC DEPT REVENUE.*',
                    r'.*STATE TAX.*',
                    r'.*DEPT OF REVENUE.*',
                    r'.*Check Deposit From Idaho State treasurer.*',
                    r'.*8021OHIOTAXSALES.*',
                    r'.*OH SSTPTAX.*'
                ],
                "display_name": "State Sales Tax",
                "vendor_group": "Tax"
            },
            # Gusto
            {
                "patterns": [
                    r'.*GUSTO.*FEE.*',
                    r'.*GUSTO.*NET.*'
                ],
                "display_name": "Gusto",
                "vendor_group": "Payroll"
            },
            # Chase
            {
                "patterns": [
                    r'.*CHASE CREDIT CRD.*',
                    r'.*CHASE.*EPA[Y]?.*',
                    r'.*CHASE.*RETRY PYMT.*'
                ],
                "display_name": "Chase",
                "vendor_group": "Credit Card"
            },
            # SBA
            {
                "patterns": [
                    r'.*SBA EIDL LOAN.*'
                ],
                "display_name": "SBA",
                "vendor_group": "Loan"
            },
            # Shoppay/Affirm
            {
                "patterns": [
                    r'.*SHOPPAYINST.*',
                    r'.*AFRM.*AutoPay.*',
                    r'.*AFFIRM INC.*PAYMENTS.*'
                ],
                "display_name": "Shoppay",
                "vendor_group": "Payment Processor"
            },
            # Owner Distributions
            {
                "patterns": [
                    r'.*AMEX EPAYMENT.*ACH PMT.*Allen Walton.*',
                    r'.*CHASE CREDIT CRD.*RETRY PYMT.*EDWARD ALLEN WALTON.*',
                    r'.*EDWARD ALLEN WALTON.*',
                    r'.*Edward Walton.*'
                ],
                "display_name": "Owner Distributions",
                "vendor_group": "Owner"
            },
            # SpyGuy
            {
                "patterns": [
                    r'.*SpyGuy.*',
                    r'.*SPYGUY.*'
                ],
                "display_name": "SpyGuy",
                "vendor_group": "Business"
            },
            # SG Electronics
            {
                "patterns": [
                    r'.*SG ELECTRONICS LLC.*',
                    r'.*SG Electronics LLC.*'
                ],
                "display_name": "SG Electronics LLC",
                "vendor_group": "Business"
            }
        ]
        
        # Update vendors based on patterns
        for rule in vendor_rules:
            for pattern in rule["patterns"]:
                logger.info(f"Updating vendors matching pattern: {pattern}")
                resp = supabase.table("vendors") \
                    .update({
                        "display_name": rule["display_name"],
                        "vendor_group": rule["vendor_group"],
                        "group_locked": True,
                        "review_needed": False
                    }) \
                    .eq("client_id", client_id) \
                    .ilike("vendor_name", pattern) \
                    .execute()
                
                if resp.data:
                    logger.info(f"Updated {len(resp.data)} vendors to {rule['display_name']}")
        
        logger.info("Vendor rules update completed")
        
    except Exception as e:
        logger.error(f"Error updating vendor rules: {str(e)}")
        raise

if __name__ == "__main__":
    update_vendor_rules() 