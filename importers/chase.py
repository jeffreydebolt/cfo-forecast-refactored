"""
Chase Bank CSV Importer
Handles Chase bank transaction CSV format.
"""

from typing import List
from .base import BaseTransactionImporter, ColumnMapping


class ChaseImporter(BaseTransactionImporter):
    """Importer for Chase Bank CSV files."""
    
    @property
    def format_name(self) -> str:
        return "Chase Bank"
    
    @property
    def expected_headers(self) -> List[str]:
        return [
            "Transaction Date",
            "Post Date", 
            "Description",
            "Category",
            "Type",
            "Amount"
        ]
    
    def get_default_mapping(self) -> ColumnMapping:
        return ColumnMapping(
            date_column="Transaction Date",
            vendor_column="Description",
            amount_column="Amount",
            description_column="Description",
            category_column="Category",
            date_format="%m/%d/%Y",
            amount_multiplier=1.0  # Chase shows negative for expenses
        )


class ChaseCreditImporter(BaseTransactionImporter):
    """Importer for Chase Credit Card CSV files."""
    
    @property
    def format_name(self) -> str:
        return "Chase Credit Card"
    
    @property
    def expected_headers(self) -> List[str]:
        return [
            "Transaction Date",
            "Post Date",
            "Description", 
            "Category",
            "Type",
            "Amount",
            "Memo"
        ]
    
    def get_default_mapping(self) -> ColumnMapping:
        return ColumnMapping(
            date_column="Transaction Date",
            vendor_column="Description",
            amount_column="Amount", 
            description_column="Memo",
            category_column="Category",
            date_format="%m/%d/%Y",
            amount_multiplier=-1.0  # Chase credit shows positive for expenses, we want negative
        )


if __name__ == "__main__":
    # Test Chase importers
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    # Test checking importer
    importer = ChaseImporter("test_client")
    print(f"Format: {importer.format_name}")
    print(f"Headers: {importer.expected_headers}")
    print(f"Default mapping: {importer.get_default_mapping().to_dict()}")
    
    # Test credit importer  
    credit_importer = ChaseCreditImporter("test_client")
    print(f"Credit Format: {credit_importer.format_name}")
    print(f"Credit Headers: {credit_importer.expected_headers}")
    print(f"Credit Default mapping: {credit_importer.get_default_mapping().to_dict()}")
    
    print("✅ Chase importers working!")