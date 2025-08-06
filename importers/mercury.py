"""
Mercury Bank CSV Importer
Handles Mercury bank transaction CSV format.
"""

from typing import List
from .base import BaseTransactionImporter, ColumnMapping


class MercuryImporter(BaseTransactionImporter):
    """Importer for Mercury Bank CSV files."""
    
    @property
    def format_name(self) -> str:
        return "Mercury Bank"
    
    @property
    def expected_headers(self) -> List[str]:
        return [
            "Date",
            "Description", 
            "Amount",
            "Status",
            "Account Name"
        ]
    
    def get_default_mapping(self) -> ColumnMapping:
        return ColumnMapping(
            date_column="Date",
            vendor_column="Description",
            amount_column="Amount",
            description_column="Description",
            category_column=None,
            date_format="%Y-%m-%d",
            amount_multiplier=1.0  # Mercury shows negative for expenses
        )
    
    def _is_valid_transaction(self, transaction) -> bool:
        """Mercury-specific validation."""
        if not super()._is_valid_transaction(transaction):
            return False
        
        # Skip pending transactions if we have status info
        # (This would need to be added to the base class if we want to use it)
        
        return True


if __name__ == "__main__":
    # Test Mercury importer
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    importer = MercuryImporter("test_client")
    print(f"Format: {importer.format_name}")
    print(f"Headers: {importer.expected_headers}")
    print(f"Default mapping: {importer.get_default_mapping().to_dict()}")
    
    print("✅ Mercury importer working!")