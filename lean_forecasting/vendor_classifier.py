#!/usr/bin/env python3
"""
Vendor Classification System
Provides semantic understanding of vendor types and expected payment patterns
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import re

@dataclass
class VendorClassification:
    """Represents a vendor's classification and expected patterns"""
    vendor_type: str
    subtype: Optional[str]
    expected_frequency: str
    amount_variance: str
    timing_flexibility_days: int
    business_rules: Dict[str, any]
    confidence: float

class VendorClassifier:
    """Classifies vendors based on name patterns and provides business logic"""
    
    # Vendor type definitions with pattern matching
    VENDOR_PATTERNS = {
        'contractor_platform': {
            'patterns': ['wise', 'paypal', 'upwork', 'fiverr', 'contractor', 'freelance'],
            'subtypes': {
                'international': ['wise', 'transferwise'],
                'domestic': ['paypal', 'venmo', 'zelle'],
                'marketplace': ['upwork', 'fiverr', 'toptal']
            }
        },
        'revenue_source': {
            'patterns': ['shopify', 'amazon', 'stripe', 'square', 'paypal.*revenue', 
                        'sales', 'revenue', 'income', 'shopee', 'etsy', 'ebay',
                        'tiktok.*shop', 'faire', 'wholesale'],
            'subtypes': {
                'ecommerce': ['shopify', 'amazon', 'etsy', 'ebay'],
                'payment_processor': ['stripe', 'square', 'paypal'],
                'marketplace': ['faire', 'wholesale', 'tiktok']
            }
        },
        'financial_services': {
            'patterns': ['bank.*fee', 'wire.*fee', 'credit.*card', 'amex', 'american.*express',
                        'chase', 'capital.*one', 'visa', 'mastercard', 'interest', 'loan'],
            'subtypes': {
                'credit_card': ['amex', 'american.*express', 'chase', 'capital.*one'],
                'banking': ['bank.*fee', 'wire.*fee', 'ach.*fee'],
                'lending': ['loan', 'interest', 'financing']
            }
        },
        'inventory_supplier': {
            'patterns': ['supplier', 'manufacturer', 'wholesale', 'inventory', 
                        'materials', 'packaging', 'fulfillment'],
            'subtypes': {
                'manufacturer': ['manufacturer', 'factory', 'production'],
                'materials': ['materials', 'supplies', 'packaging'],
                'fulfillment': ['fulfillment', '3pl', 'warehouse']
            }
        },
        'professional_services': {
            'patterns': ['legal', 'accounting', 'cpa', 'bookkeep', 'consult',
                        'agency', 'marketing', 'design', 'development', 'armbrust'],
            'subtypes': {
                'legal': ['legal', 'law.*firm', 'attorney'],
                'accounting': ['accounting', 'cpa', 'bookkeep', 'tax'],
                'consulting': ['consult', 'advisory', 'strategy'],
                'creative': ['design', 'marketing', 'agency', 'creative']
            }
        },
        'utilities': {
            'patterns': ['electric', 'gas', 'water', 'internet', 'phone', 'cellular',
                        'utilities', 'telecom', 'comcast', 'at&t', 'verizon'],
            'subtypes': {
                'essential': ['electric', 'gas', 'water'],
                'communication': ['internet', 'phone', 'cellular', 'telecom']
            }
        },
        'real_estate': {
            'patterns': ['rent', 'lease', 'mortgage', 'property', 'landlord', 'realty'],
            'subtypes': {
                'rent': ['rent', 'lease', 'landlord'],
                'ownership': ['mortgage', 'property.*tax', 'hoa']
            }
        },
        'employee_payroll': {
            'patterns': ['payroll', 'salary', 'wages', 'adp', 'gusto', 'paychex',
                        'employee', 'staff', 'team.*member'],
            'subtypes': {
                'service': ['adp', 'gusto', 'paychex'],
                'direct': ['salary', 'wages', 'payroll']
            }
        }
    }
    
    # Business rules for each vendor type
    BUSINESS_RULES = {
        'contractor_platform': {
            'expected_frequency': 'bi-weekly_to_monthly',
            'amount_variance': 'high_acceptable',
            'timing_flexibility': 3,
            'forecast_method': 'range_projection',
            'aggregation_level': 'monthly',
            'notes': 'Contractor payments vary based on work completed'
        },
        'revenue_source': {
            'expected_frequency': 'weekly_to_bi-weekly',
            'amount_variance': 'seasonal_acceptable',
            'timing_flexibility': 2,
            'forecast_method': 'seasonal_weighted_average',
            'aggregation_level': 'weekly',
            'notes': 'Revenue patterns often have seasonal variations'
        },
        'financial_services': {
            'expected_frequency': 'monthly',
            'amount_variance': 'low_to_moderate',
            'timing_flexibility': 5,
            'forecast_method': 'historical_average',
            'aggregation_level': 'monthly',
            'notes': 'Financial charges usually follow statement cycles'
        },
        'inventory_supplier': {
            'expected_frequency': 'irregular_to_monthly',
            'amount_variance': 'high_acceptable',
            'timing_flexibility': 7,
            'forecast_method': 'reorder_point_model',
            'aggregation_level': 'quarterly',
            'notes': 'Inventory purchases depend on sales velocity and stock levels'
        },
        'professional_services': {
            'expected_frequency': 'monthly_to_quarterly',
            'amount_variance': 'project_based',
            'timing_flexibility': 10,
            'forecast_method': 'contract_schedule',
            'aggregation_level': 'quarterly',
            'notes': 'Professional services often bill on project milestones'
        },
        'utilities': {
            'expected_frequency': 'monthly',
            'amount_variance': 'seasonal_moderate',
            'timing_flexibility': 5,
            'forecast_method': 'seasonal_average',
            'aggregation_level': 'monthly',
            'notes': 'Utility bills follow regular monthly cycles with seasonal variance'
        },
        'real_estate': {
            'expected_frequency': 'monthly',
            'amount_variance': 'fixed',
            'timing_flexibility': 5,
            'forecast_method': 'fixed_schedule',
            'aggregation_level': 'monthly',
            'notes': 'Rent/mortgage payments are typically fixed monthly amounts'
        },
        'employee_payroll': {
            'expected_frequency': 'bi-weekly_or_semi-monthly',
            'amount_variance': 'low',
            'timing_flexibility': 0,
            'forecast_method': 'fixed_schedule',
            'aggregation_level': 'pay_period',
            'notes': 'Payroll follows strict schedules with minimal variance'
        }
    }
    
    def classify_vendor(self, vendor_name: str, 
                       transaction_history: Optional[List[Dict]] = None) -> VendorClassification:
        """
        Classify a vendor based on name patterns and transaction history
        
        Args:
            vendor_name: Name of the vendor
            transaction_history: Optional list of historical transactions
            
        Returns:
            VendorClassification with type, expected patterns, and business rules
        """
        vendor_lower = vendor_name.lower()
        best_match = None
        best_confidence = 0.0
        
        # Check each vendor type
        subtype = None  # Initialize subtype
        for vendor_type, type_info in self.VENDOR_PATTERNS.items():
            for pattern in type_info['patterns']:
                if re.search(pattern, vendor_lower):
                    # Calculate confidence based on pattern match strength
                    pattern_confidence = self._calculate_pattern_confidence(
                        pattern, vendor_lower
                    )
                    
                    if pattern_confidence > best_confidence:
                        best_confidence = pattern_confidence
                        best_match = vendor_type
                        
                        # Find subtype
                        subtype = None
                        for sub_name, sub_patterns in type_info.get('subtypes', {}).items():
                            for sub_pattern in sub_patterns:
                                if re.search(sub_pattern, vendor_lower):
                                    subtype = sub_name
                                    break
        
        # Default to 'uncategorized' if no match
        if not best_match:
            best_match = 'uncategorized'
            best_confidence = 0.0
            
        # Get business rules
        rules = self.BUSINESS_RULES.get(best_match, self._get_default_rules())
        
        return VendorClassification(
            vendor_type=best_match,
            subtype=subtype,
            expected_frequency=rules['expected_frequency'],
            amount_variance=rules['amount_variance'],
            timing_flexibility_days=rules['timing_flexibility'],
            business_rules=rules,
            confidence=best_confidence
        )
    
    def _calculate_pattern_confidence(self, pattern: str, vendor_name: str) -> float:
        """Calculate confidence score for pattern match"""
        # Exact match = 1.0
        if pattern == vendor_name:
            return 1.0
        
        # Full word match = 0.9
        if re.search(r'\b' + pattern + r'\b', vendor_name):
            return 0.9
        
        # Partial match = 0.7
        if pattern in vendor_name:
            return 0.7
        
        # Regex match = 0.6
        return 0.6
    
    def _get_default_rules(self) -> Dict:
        """Get default business rules for uncategorized vendors"""
        return {
            'expected_frequency': 'irregular',
            'amount_variance': 'unknown',
            'timing_flexibility': 7,
            'forecast_method': 'historical_average',
            'aggregation_level': 'monthly',
            'notes': 'Uncategorized vendor - using conservative defaults'
        }
    
    def get_forecast_recommendations(self, classification: VendorClassification,
                                   pattern_analysis: Dict) -> Dict:
        """
        Get specific forecasting recommendations based on classification and patterns
        
        Args:
            classification: Vendor classification
            pattern_analysis: Results from pattern analysis
            
        Returns:
            Dictionary with forecast method recommendations
        """
        recommendations = {
            'primary_method': classification.business_rules['forecast_method'],
            'aggregation_level': classification.business_rules['aggregation_level'],
            'confidence_threshold': 0.6,
            'fallback_methods': []
        }
        
        # Adjust based on pattern analysis results
        if pattern_analysis.get('timing_confidence', 0) > 0.8:
            recommendations['use_timing_pattern'] = True
        else:
            recommendations['use_timing_pattern'] = False
            recommendations['fallback_methods'].append('quarterly_average')
        
        if pattern_analysis.get('amount_volatility', 'low') == 'high':
            recommendations['use_range_forecast'] = True
            recommendations['amount_range'] = pattern_analysis.get('amount_range', (0, 0))
        
        # Special handling for specific vendor types
        if classification.vendor_type == 'contractor_platform':
            recommendations['forecast_as_range'] = True
            recommendations['show_monthly_total'] = True
            
        elif classification.vendor_type == 'inventory_supplier':
            recommendations['consider_reorder_cycle'] = True
            recommendations['check_dependency_patterns'] = True
            
        return recommendations

# Singleton instance
vendor_classifier = VendorClassifier()

def test_classifier():
    """Test the vendor classifier with examples"""
    test_vendors = [
        "Wise Transfers",
        "Amazon Revenue", 
        "American Express Payments",
        "Armbrust Legal Services",
        "Lavery Innovations Consulting",
        "Shopify Sales",
        "Electric Company",
        "Office Rent",
        "ADP Payroll"
    ]
    
    print("🧪 Testing Vendor Classifier")
    print("=" * 80)
    
    for vendor in test_vendors:
        classification = vendor_classifier.classify_vendor(vendor)
        print(f"\n📊 {vendor}")
        print(f"   Type: {classification.vendor_type}")
        if classification.subtype:
            print(f"   Subtype: {classification.subtype}")
        print(f"   Expected Frequency: {classification.expected_frequency}")
        print(f"   Amount Variance: {classification.amount_variance}")
        print(f"   Timing Flexibility: ±{classification.timing_flexibility_days} days")
        print(f"   Forecast Method: {classification.business_rules['forecast_method']}")
        print(f"   Confidence: {classification.confidence:.2f}")

if __name__ == "__main__":
    test_classifier()