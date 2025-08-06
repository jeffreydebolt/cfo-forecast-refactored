"""
Mercury Bank CSV Importer V2
Handles newer Mercury bank transaction CSV format with extended columns.
"""

from typing import List
from .base import BaseTransactionImporter, ColumnMapping


class MercuryV2Importer(BaseTransactionImporter):
    """Importer for Mercury Bank CSV files (newer format)."""
    
    @property
    def format_name(self) -> str:
        return "Mercury Bank V2"
    
    @property
    def expected_headers(self) -> List[str]:
        return [
            "Date (UTC)",
            "Description", 
            "Amount",
            "Status",
            "Source Account",
            "Mercury Category"
        ]
    
    def get_default_mapping(self) -> ColumnMapping:
        return ColumnMapping(
            date_column="Date (UTC)",
            vendor_column="Description",
            amount_column="Amount",
            description_column="Bank Description",
            category_column="Mercury Category",
            date_format="%m-%d-%Y",  # Mercury uses MM-DD-YYYY format
            amount_multiplier=1.0  # Mercury shows negative for expenses
        )
    
    def _parse_row(self, row, mapping):
        """Override to check Mercury-specific Status column and extract reference/timestamp."""
        # Check status first - skip failed, blocked, or cancelled transactions
        status = row.get("Status", "").strip().lower()
        if status in ["failed", "blocked", "cancelled", "pending"]:
            return None  # Skip this transaction
        
        # Use the parent method for normal parsing
        transaction = super()._parse_row(row, mapping)
        
        if transaction:
            # Add Mercury-specific fields for better duplicate detection
            transaction.reference = row.get("Reference", "").strip()
            transaction.timestamp = row.get("Timestamp", "").strip()
        
        return transaction
    
    def _is_valid_transaction(self, transaction) -> bool:
        """Mercury-specific validation."""
        if not super()._is_valid_transaction(transaction):
            return False
        
        # Additional Mercury-specific validation can go here
        
        return True


if __name__ == "__main__":
    # Test Mercury V2 importer
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    importer = MercuryV2Importer("test_client")
    print(f"Format: {importer.format_name}")
    print(f"Headers: {importer.expected_headers}")
    print(f"Default mapping: {importer.get_default_mapping().to_dict()}")
    
    print("✅ Mercury V2 importer working!")