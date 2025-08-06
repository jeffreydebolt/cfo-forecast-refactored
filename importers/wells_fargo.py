"""
Wells Fargo Bank CSV Importer
Handles Wells Fargo bank transaction CSV format.
"""

from typing import List
from .base import BaseTransactionImporter, ColumnMapping


class WellsFargoImporter(BaseTransactionImporter):
    """Importer for Wells Fargo CSV files."""
    
    @property
    def format_name(self) -> str:
        return "Wells Fargo"
    
    @property
    def expected_headers(self) -> List[str]:
        return [
            "Date",
            "Amount",
            "Check Number",
            "Description"
        ]
    
    def get_default_mapping(self) -> ColumnMapping:
        return ColumnMapping(
            date_column="Date",
            vendor_column="Description", 
            amount_column="Amount",
            description_column="Description",
            category_column=None,
            date_format="%m/%d/%Y",
            amount_multiplier=1.0  # Wells Fargo shows negative for expenses
        )


class WellsFargoBusinessImporter(BaseTransactionImporter):
    """Importer for Wells Fargo Business CSV files."""
    
    @property
    def format_name(self) -> str:
        return "Wells Fargo Business"
    
    @property
    def expected_headers(self) -> List[str]:
        return [
            "Date",
            "Amount", 
            "Description",
            "Memo",
            "Account Name"
        ]
    
    def get_default_mapping(self) -> ColumnMapping:
        return ColumnMapping(
            date_column="Date",
            vendor_column="Description",
            amount_column="Amount",
            description_column="Memo",
            category_column=None,
            date_format="%m/%d/%Y", 
            amount_multiplier=1.0
        )


if __name__ == "__main__":
    # Test Wells Fargo importers
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    importer = WellsFargoImporter("test_client")
    print(f"Format: {importer.format_name}")
    print(f"Headers: {importer.expected_headers}")
    print(f"Default mapping: {importer.get_default_mapping().to_dict()}")
    
    business_importer = WellsFargoBusinessImporter("test_client")
    print(f"Business Format: {business_importer.format_name}")
    print(f"Business Headers: {business_importer.expected_headers}")
    print(f"Business Default mapping: {business_importer.get_default_mapping().to_dict()}")
    
    print("✅ Wells Fargo importers working!")