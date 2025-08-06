"""
Base classes for transaction import system.
Provides a framework for importing CSV files from any bank format.
"""

import csv
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class TransactionData:
    """Standardized transaction data structure."""
    date: datetime
    vendor_name: str
    amount: float
    description: str = ""
    category: str = ""
    account_type: str = ""
    reference: str = ""  # Reference number, invoice ID, payout ID, etc.
    timestamp: str = ""  # Full timestamp including time (for duplicate detection)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database insertion."""
        return {
            'transaction_date': self.date.strftime('%Y-%m-%d'),
            'vendor_name': self.vendor_name,
            'amount': self.amount,
            'description': self.description,
            'reference': self.reference  # Now included for better duplicate detection
            # Note: 'category' field removed as it doesn't exist in database schema
            # Database has these additional fields that are handled by TransactionService:
            # - client_id, transaction_id, type, created_at, updated_at
        }


@dataclass
class ColumnMapping:
    """Defines how CSV columns map to transaction fields."""
    date_column: str
    vendor_column: str  
    amount_column: str
    description_column: Optional[str] = None
    category_column: Optional[str] = None
    
    # Date parsing format
    date_format: str = "%Y-%m-%d"
    
    # Amount handling
    amount_multiplier: float = 1.0  # Use -1 for banks that show expenses as positive
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'date_column': self.date_column,
            'vendor_column': self.vendor_column,
            'amount_column': self.amount_column,
            'description_column': self.description_column,
            'category_column': self.category_column,
            'date_format': self.date_format,
            'amount_multiplier': self.amount_multiplier
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ColumnMapping':
        """Create from dictionary."""
        return cls(**data)


class ImportResult:
    """Result of an import operation."""
    
    def __init__(self):
        self.success = True
        self.transactions: List[TransactionData] = []
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.skipped_rows: List[Dict[str, Any]] = []
        self.duplicates_found = 0
        
    def add_transaction(self, transaction: TransactionData):
        """Add a successfully parsed transaction."""
        self.transactions.append(transaction)
    
    def add_error(self, error: str, row_data: Dict[str, Any] = None):
        """Add an error message."""
        self.errors.append(error)
        if row_data:
            self.skipped_rows.append(row_data)
        self.success = False
    
    def add_warning(self, warning: str):
        """Add a warning message."""
        self.warnings.append(warning)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get import summary."""
        return {
            'success': self.success,
            'transactions_imported': len(self.transactions),
            'errors': len(self.errors),
            'warnings': len(self.warnings),
            'skipped_rows': len(self.skipped_rows),
            'duplicates_found': self.duplicates_found
        }


class BaseTransactionImporter(ABC):
    """
    Abstract base class for transaction importers.
    Each bank format should have its own importer that inherits from this.
    """
    
    def __init__(self, client_id: str):
        self.client_id = client_id
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
    
    @property
    @abstractmethod
    def format_name(self) -> str:
        """Human-readable name for this format (e.g., 'Chase Bank')."""
        pass
    
    @property
    @abstractmethod
    def expected_headers(self) -> List[str]:
        """List of expected column headers that identify this format."""
        pass
    
    @abstractmethod
    def get_default_mapping(self) -> ColumnMapping:
        """Get the default column mapping for this bank format."""
        pass
    
    def detect_format(self, csv_file_path: str) -> bool:
        """
        Detect if the CSV file matches this importer's format.
        
        Args:
            csv_file_path: Path to the CSV file
            
        Returns:
            bool: True if this importer can handle the file
        """
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                # Try different encodings if UTF-8 fails
                try:
                    reader = csv.reader(file)
                    header_row = next(reader)
                except UnicodeDecodeError:
                    file.seek(0)
                    file = open(csv_file_path, 'r', encoding='latin-1')
                    reader = csv.reader(file)
                    header_row = next(reader)
                
                # Normalize headers (strip whitespace, convert to lowercase)
                normalized_headers = [h.strip().lower() for h in header_row]
                expected_normalized = [h.lower() for h in self.expected_headers]
                
                # Check if most expected headers are present
                matches = sum(1 for h in expected_normalized if h in normalized_headers)
                match_ratio = matches / len(expected_normalized)
                
                self.logger.debug(f"Format detection for {self.format_name}: {matches}/{len(expected_normalized)} headers matched ({match_ratio:.2%})")
                
                return match_ratio >= 0.7  # At least 70% of headers must match
                
        except Exception as e:
            self.logger.error(f"Error detecting format: {e}")
            return False
    
    def preview_csv(self, csv_file_path: str, max_rows: int = 5) -> Dict[str, Any]:
        """
        Preview the CSV file structure.
        
        Args:
            csv_file_path: Path to the CSV file
            max_rows: Maximum number of data rows to return
            
        Returns:
            dict: Preview data including headers and sample rows
        """
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                preview_data = {
                    'headers': reader.fieldnames,
                    'sample_rows': [],
                    'total_rows': 0,
                    'format_detected': self.format_name,
                    'default_mapping': self.get_default_mapping().to_dict()
                }
                
                # Read sample rows
                for i, row in enumerate(reader):
                    if i < max_rows:
                        preview_data['sample_rows'].append(dict(row))
                    preview_data['total_rows'] = i + 1
                
                return preview_data
                
        except Exception as e:
            self.logger.error(f"Error previewing CSV: {e}")
            raise ImportError(f"Could not preview CSV file: {e}")
    
    def import_csv(self, csv_file_path: str, mapping: ColumnMapping = None) -> ImportResult:
        """
        Import transactions from CSV file.
        
        Args:
            csv_file_path: Path to the CSV file
            mapping: Custom column mapping (uses default if None)
            
        Returns:
            ImportResult: Results of the import operation
        """
        if mapping is None:
            mapping = self.get_default_mapping()
        
        result = ImportResult()
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row_num, row in enumerate(reader, start=2):  # Start at 2 because row 1 is headers
                    try:
                        transaction = self._parse_row(row, mapping)
                        if transaction:
                            if self._is_valid_transaction(transaction):
                                result.add_transaction(transaction)
                            else:
                                result.add_warning(f"Row {row_num}: Transaction validation failed")
                        else:
                            result.add_warning(f"Row {row_num}: Could not parse transaction")
                            
                    except Exception as e:
                        result.add_error(f"Row {row_num}: {str(e)}", row)
                
                self.logger.info(f"Import completed: {len(result.transactions)} transactions, {len(result.errors)} errors")
                
        except Exception as e:
            result.add_error(f"Failed to read CSV file: {str(e)}")
        
        return result
    
    def _parse_row(self, row: Dict[str, str], mapping: ColumnMapping) -> Optional[TransactionData]:
        """
        Parse a single CSV row into a TransactionData object.
        
        Args:
            row: Dictionary representing a CSV row
            mapping: Column mapping configuration
            
        Returns:
            TransactionData or None if parsing failed
        """
        try:
            # Parse date
            date_str = row.get(mapping.date_column, '').strip()
            if not date_str:
                return None
            
            transaction_date = datetime.strptime(date_str, mapping.date_format)
            
            # Parse vendor name
            vendor_name = row.get(mapping.vendor_column, '').strip()
            if not vendor_name:
                return None
            
            # Parse amount
            amount_str = row.get(mapping.amount_column, '').strip()
            if not amount_str:
                return None
            
            # Clean amount string (remove commas, dollar signs, etc.)
            amount_clean = amount_str.replace(',', '').replace('$', '').replace('(', '-').replace(')', '')
            amount = float(amount_clean) * mapping.amount_multiplier
            
            # Parse optional fields
            description = row.get(mapping.description_column, '').strip() if mapping.description_column else vendor_name
            category = row.get(mapping.category_column, '').strip() if mapping.category_column else ''
            
            return TransactionData(
                date=transaction_date,
                vendor_name=vendor_name,
                amount=amount,
                description=description,
                category=category
            )
            
        except (ValueError, TypeError) as e:
            self.logger.error(f"Error parsing row: {e}, Row data: {row}")
            return None
    
    def _is_valid_transaction(self, transaction: TransactionData) -> bool:
        """
        Validate a parsed transaction.
        
        Args:
            transaction: Transaction to validate
            
        Returns:
            bool: True if transaction is valid
        """
        # Basic validation rules
        if not transaction.vendor_name:
            return False
        
        if transaction.amount == 0:
            return False
        
        # Date should be reasonable (not too far in future/past)
        now = datetime.now()
        if transaction.date > now or transaction.date.year < 1990:
            return False
        
        return True
    
    def save_mapping(self, mapping: ColumnMapping, mapping_name: str = None) -> bool:
        """
        Save a column mapping configuration for reuse.
        
        Args:
            mapping: Column mapping to save
            mapping_name: Name for this mapping (defaults to format name)
            
        Returns:
            bool: True if saved successfully
        """
        try:
            if mapping_name is None:
                mapping_name = self.format_name
            
            # Create mappings directory if it doesn't exist
            mappings_dir = Path("config/column_mappings")
            mappings_dir.mkdir(parents=True, exist_ok=True)
            
            # Save mapping as JSON
            mapping_file = mappings_dir / f"{mapping_name.lower().replace(' ', '_')}.json"
            
            import json
            with open(mapping_file, 'w') as f:
                json.dump(mapping.to_dict(), f, indent=2)
            
            self.logger.info(f"Saved column mapping: {mapping_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving mapping: {e}")
            return False
    
    def load_mapping(self, mapping_name: str) -> Optional[ColumnMapping]:
        """
        Load a saved column mapping configuration.
        
        Args:
            mapping_name: Name of the mapping to load
            
        Returns:
            ColumnMapping or None if not found
        """
        try:
            mappings_dir = Path("config/column_mappings")
            mapping_file = mappings_dir / f"{mapping_name.lower().replace(' ', '_')}.json"
            
            if mapping_file.exists():
                import json
                with open(mapping_file, 'r') as f:
                    data = json.load(f)
                return ColumnMapping.from_dict(data)
            
        except Exception as e:
            self.logger.error(f"Error loading mapping: {e}")
        
        return None


if __name__ == "__main__":
    # Test the base classes
    logging.basicConfig(level=logging.DEBUG)
    
    # Test TransactionData
    transaction = TransactionData(
        date=datetime.now(),
        vendor_name="Test Vendor",
        amount=-123.45,
        description="Test transaction"
    )
    
    print(f"Transaction: {transaction}")
    print(f"As dict: {transaction.to_dict()}")
    
    # Test ColumnMapping
    mapping = ColumnMapping(
        date_column="Date",
        vendor_column="Description", 
        amount_column="Amount",
        date_format="%m/%d/%Y"
    )
    
    print(f"Mapping: {mapping}")
    print(f"As dict: {mapping.to_dict()}")
    
    print("✅ Base classes working!")