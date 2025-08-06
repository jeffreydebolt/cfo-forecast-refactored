"""
Vendor Auto-Mapping System
Automatically maps obvious vendor patterns (AMAZON.*, SHOPIFY*, etc.) to display names.

TODO/TROUBLESHOOTING: 
- Will need client-specific mapping rules when someone wants different groupings
- May need confidence scoring for edge cases
- Consider adding override/exclusion rules for special cases
"""

import re
import logging
from datetime import datetime, UTC
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from supabase_client import supabase

logger = logging.getLogger(__name__)

@dataclass
class MappingRule:
    """Represents a vendor mapping rule"""
    pattern: str
    display_name: str
    description: str
    is_revenue: bool = True
    category: str = "Auto-Mapped Revenue"

@dataclass
class MappingLog:
    """Log entry for mapping actions"""
    client_id: str
    vendor_name: str
    display_name: Optional[str]
    action: str  # auto_mapped, needs_review, manual_override
    rule_matched: Optional[str]
    reason: Optional[str]
    timestamp: datetime

# TODO: Make this configurable per client when we hit edge cases
VENDOR_MAPPING_RULES = [
    # Payment processors with reference codes (HIGH CONFIDENCE)
    MappingRule(
        pattern=r'^AMAZON\.C[A-Z0-9]+$',
        display_name='Amazon Revenue',
        description='Amazon payments with reference codes',
        is_revenue=True,
        category='E-commerce Revenue'
    ),
    MappingRule(
        pattern=r'^AMAZON\.COM\.CA',
        display_name='Amazon CA Revenue', 
        description='Amazon Canada payments',
        is_revenue=True,
        category='E-commerce Revenue'
    ),
    MappingRule(
        pattern=r'^SHOPIFY',
        display_name='Shopify Revenue',
        description='Shopify payments (all variants)',
        is_revenue=True,
        category='E-commerce Revenue'
    ),
    MappingRule(
        pattern=r'^STRIPE',
        display_name='Stripe Revenue',
        description='Stripe payment processing',
        is_revenue=True,
        category='Payment Processing'
    ),
    MappingRule(
        pattern=r'^PAYPAL',
        display_name='PayPal Revenue',
        description='PayPal payments',
        is_revenue=True,
        category='Payment Processing'
    ),
    MappingRule(
        pattern=r'^SQUARE',
        display_name='Square Revenue',
        description='Square payment processing',
        is_revenue=True,
        category='Payment Processing'
    ),
    
    # Bank transfers and wire patterns
    MappingRule(
        pattern=r'^ACH.*DEPOSIT',
        display_name='ACH Deposits',
        description='ACH deposit transfers',
        is_revenue=True,
        category='Bank Transfers'
    ),
    MappingRule(
        pattern=r'^WIRE.*TRANSFER',
        display_name='Wire Transfers',
        description='Wire transfer payments',
        is_revenue=False,  # Could be either, default to expense 
        category='Bank Transfers'
    ),
    MappingRule(
        pattern=r'^Wise \(Wise\)',
        display_name='Wise Transfers',
        description='Wise international transfers',
        is_revenue=False,
        category='International Transfers'
    ),
    
    # Credit card payments (EXPENSES)
    MappingRule(
        pattern=r'^AMEX.*PAYMENT',
        display_name='American Express Payments',
        description='Amex credit card payments',
        is_revenue=False,
        category='Credit Card Payments'
    ),
    MappingRule(
        pattern=r'^CHASE.*CREDIT',
        display_name='Chase Credit Card Payments',
        description='Chase credit card payments',
        is_revenue=False,
        category='Credit Card Payments'
    ),
    
    # Other common patterns
    MappingRule(
        pattern=r'^GUSTO;',
        display_name='Gusto Payments',
        description='Gusto payroll and HR',
        is_revenue=False,
        category='Payroll & HR'
    ),
    MappingRule(
        pattern=r'^SHOPPAYINST AFRM;',
        display_name='Affirm Payments',
        description='Affirm buy-now-pay-later',
        is_revenue=True,
        category='Alternative Payments'
    ),
]

class VendorAutoMapper:
    """Handles automatic vendor mapping with logging"""
    
    def __init__(self):
        self.mapping_rules = VENDOR_MAPPING_RULES
    
    def find_matching_rule(self, vendor_name: str) -> Optional[MappingRule]:
        """Find first matching rule for vendor name"""
        for rule in self.mapping_rules:
            if re.match(rule.pattern, vendor_name, re.IGNORECASE):
                return rule
        return None
    
    def auto_map_vendor(self, vendor_name: str) -> Optional[str]:
        """Auto-map vendor if obvious pattern match found"""
        rule = self.find_matching_rule(vendor_name)
        return rule.display_name if rule else None
    
    def log_mapping_action(self, client_id: str, vendor_name: str, 
                          display_name: Optional[str], action: str,
                          rule_matched: Optional[str] = None,
                          reason: Optional[str] = None):
        """Log mapping action for review/troubleshooting later"""
        try:
            log_entry = {
                'client_id': client_id,
                'vendor_name': vendor_name,
                'display_name': display_name,
                'action': action,
                'rule_matched': rule_matched,
                'reason': reason,
                'timestamp': datetime.now(UTC).isoformat()
            }
            
            # TODO: Create mapping_log table when we need it
            # For now, just log to console
            logger.info(f"Mapping: {action} - {vendor_name} → {display_name} ({rule_matched})")
            
        except Exception as e:
            logger.error(f"Error logging mapping action: {e}")
    
    def create_vendor_mapping(self, vendor_name: str, display_name: str, 
                            client_id: str, rule: MappingRule) -> bool:
        """Create vendor mapping in database"""
        try:
            vendor_data = {
                'client_id': client_id,
                'vendor_name': vendor_name,
                'display_name': display_name,
                'is_revenue': rule.is_revenue,
                'category': rule.category,
                'forecast_method': 'pattern_detected'
            }
            
            result = supabase.table('vendors').insert(vendor_data).execute()
            
            if result.data:
                logger.info(f"✅ Created vendor mapping: {vendor_name} → {display_name}")
                return True
            else:
                logger.error(f"Failed to create vendor mapping for {vendor_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error creating vendor mapping for {vendor_name}: {e}")
            return False
    
    def vendor_exists(self, vendor_name: str, client_id: str) -> bool:
        """Check if vendor mapping already exists"""
        try:
            result = supabase.table('vendors').select('id').eq(
                'client_id', client_id
            ).eq(
                'vendor_name', vendor_name
            ).execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Error checking vendor existence: {e}")
            return False
    
    def process_new_vendor(self, vendor_name: str, client_id: str) -> bool:
        """Process new vendor: auto-map if possible, log action"""
        
        # Skip if already mapped
        if self.vendor_exists(vendor_name, client_id):
            return True
        
        # Try auto-mapping
        rule = self.find_matching_rule(vendor_name)
        
        if rule:
            # Auto-map obvious cases
            success = self.create_vendor_mapping(vendor_name, rule.display_name, client_id, rule)
            
            if success:
                # Log the auto-mapping
                self.log_mapping_action(
                    client_id=client_id,
                    vendor_name=vendor_name,
                    display_name=rule.display_name,
                    action="auto_mapped",
                    rule_matched=f"Pattern: {rule.pattern}",
                    reason=rule.description
                )
                print(f"✅ Auto-mapped: {vendor_name} → {rule.display_name}")
                return True
            else:
                logger.error(f"Failed to create mapping for {vendor_name}")
                return False
        else:
            # Log that it needs review
            self.log_mapping_action(
                client_id=client_id,
                vendor_name=vendor_name,
                display_name=None,
                action="needs_review",
                reason="No clear pattern match - requires manual mapping"
            )
            
            # Create unmapped vendor entry for manual review later
            try:
                vendor_data = {
                    'client_id': client_id,
                    'vendor_name': vendor_name,
                    'display_name': f'[UNMAPPED] {vendor_name}',  # Placeholder until manually mapped
                    'is_revenue': False,  # Default to expense until reviewed
                    'category': 'Unmapped',
                    'forecast_method': 'manual'
                }
                
                result = supabase.table('vendors').insert(vendor_data).execute()
                print(f"⚠️  Needs review: {vendor_name} (no pattern match)")
                return True
                
            except Exception as e:
                logger.error(f"Error creating unmapped vendor entry: {e}")
                return False
    
    def bulk_process_vendors(self, client_id: str) -> Dict[str, int]:
        """Process all unmapped vendors for a client"""
        try:
            # Get all transactions with unmapped vendors
            result = supabase.table('transactions').select(
                'vendor_name'
            ).eq(
                'client_id', client_id
            ).execute()
            
            # Get unique vendor names
            all_vendors = list(set(txn['vendor_name'] for txn in result.data))
            
            stats = {
                'processed': 0,
                'auto_mapped': 0,
                'needs_review': 0,
                'errors': 0
            }
            
            logger.info(f"Processing {len(all_vendors)} unique vendors for {client_id}")
            
            for vendor_name in all_vendors:
                try:
                    if not self.vendor_exists(vendor_name, client_id):
                        stats['processed'] += 1
                        
                        rule = self.find_matching_rule(vendor_name)
                        if rule:
                            success = self.create_vendor_mapping(vendor_name, rule.display_name, client_id, rule)
                            if success:
                                stats['auto_mapped'] += 1
                            else:
                                stats['errors'] += 1
                        else:
                            # Create unmapped entry
                            vendor_data = {
                                'client_id': client_id,
                                'vendor_name': vendor_name,
                                'display_name': f'[UNMAPPED] {vendor_name}',  # Placeholder until manually mapped
                                'is_revenue': False,  # Default to expense until reviewed
                                'forecast_method': 'manual'
                            }
                            supabase.table('vendors').insert(vendor_data).execute()
                            stats['needs_review'] += 1
                            
                except Exception as e:
                    logger.error(f"Error processing vendor {vendor_name}: {e}")
                    stats['errors'] += 1
            
            logger.info(f"Bulk processing complete: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error in bulk processing: {e}")
            return {'processed': 0, 'auto_mapped': 0, 'needs_review': 0, 'errors': 1}
    
    def get_unmapped_vendors(self, client_id: str) -> List[Dict[str, Any]]:
        """Get vendors that need manual review"""
        try:
            result = supabase.table('vendors').select(
                'vendor_name, created_at'
            ).eq(
                'client_id', client_id
            ).eq(
                'needs_review', True
            ).order('created_at', desc=True).execute()
            
            return result.data
            
        except Exception as e:
            logger.error(f"Error getting unmapped vendors: {e}")
            return []

    def add_custom_rule(self, pattern: str, display_name: str, description: str,
                       is_revenue: bool = True, category: str = "Custom") -> None:
        """Add custom mapping rule (for future client-specific needs)"""
        # TODO: Store custom rules per client in database
        custom_rule = MappingRule(
            pattern=pattern,
            display_name=display_name,
            description=description,
            is_revenue=is_revenue,
            category=category
        )
        
        self.mapping_rules.append(custom_rule)
        logger.info(f"Added custom mapping rule: {pattern} → {display_name}")

# Global instance for easy import
auto_mapper = VendorAutoMapper()