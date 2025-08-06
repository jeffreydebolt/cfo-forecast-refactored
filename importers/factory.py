"""
Import Factory
Auto-detects CSV formats and provides the appropriate importer.
"""

import logging
from typing import List, Optional, Type
from .base import BaseTransactionImporter
from .mercury import MercuryImporter
from .mercury_v2 import MercuryV2Importer
from .chase import ChaseImporter, ChaseCreditImporter
from .wells_fargo import WellsFargoImporter, WellsFargoBusinessImporter

logger = logging.getLogger(__name__)


class ImporterFactory:
    """Factory for creating appropriate importers based on CSV format detection."""
    
    # Registry of all available importers
    AVAILABLE_IMPORTERS: List[Type[BaseTransactionImporter]] = [
        MercuryV2Importer,  # Put V2 first so it's checked before V1
        MercuryImporter,
        ChaseImporter,
        ChaseCreditImporter,
        WellsFargoImporter,
        WellsFargoBusinessImporter,
    ]
    
    @classmethod
    def detect_format(cls, csv_file_path: str, client_id: str) -> Optional[BaseTransactionImporter]:
        """
        Auto-detect the CSV format and return appropriate importer.
        
        Args:
            csv_file_path: Path to the CSV file
            client_id: Client ID for the importer
            
        Returns:
            BaseTransactionImporter instance or None if no format detected
        """
        logger.info(f"Detecting CSV format for: {csv_file_path}")
        
        for importer_class in cls.AVAILABLE_IMPORTERS:
            try:
                importer = importer_class(client_id)
                if importer.detect_format(csv_file_path):
                    logger.info(f"Detected format: {importer.format_name}")
                    return importer
            except Exception as e:
                logger.warning(f"Error testing {importer_class.__name__}: {e}")
                continue
        
        logger.warning("No matching format detected")
        return None
    
    @classmethod
    def get_importer_by_name(cls, format_name: str, client_id: str) -> Optional[BaseTransactionImporter]:
        """
        Get a specific importer by format name.
        
        Args:
            format_name: Name of the format (e.g., "Mercury Bank")
            client_id: Client ID for the importer
            
        Returns:
            BaseTransactionImporter instance or None if not found
        """
        for importer_class in cls.AVAILABLE_IMPORTERS:
            try:
                importer = importer_class(client_id)
                if importer.format_name.lower() == format_name.lower():
                    return importer
            except Exception as e:
                logger.warning(f"Error creating {importer_class.__name__}: {e}")
                continue
        
        return None
    
    @classmethod
    def list_available_formats(cls) -> List[str]:
        """
        Get list of all available format names.
        
        Returns:
            List of format names
        """
        formats = []
        for importer_class in cls.AVAILABLE_IMPORTERS:
            try:
                # Create a dummy instance to get the format name
                importer = importer_class("dummy")
                formats.append(importer.format_name)
            except Exception as e:
                logger.warning(f"Error getting format name for {importer_class.__name__}: {e}")
                continue
        
        return sorted(formats)
    
    @classmethod
    def preview_csv(cls, csv_file_path: str, client_id: str, format_name: str = None) -> dict:
        """
        Preview a CSV file with format detection or specific format.
        
        Args:
            csv_file_path: Path to the CSV file
            client_id: Client ID
            format_name: Specific format name (optional, auto-detects if None)
            
        Returns:
            Dictionary with preview data
        """
        try:
            if format_name:
                importer = cls.get_importer_by_name(format_name, client_id)
                if not importer:
                    return {'error': f'Unknown format: {format_name}'}
            else:
                importer = cls.detect_format(csv_file_path, client_id)
                if not importer:
                    return {'error': 'Could not detect CSV format'}
            
            preview = importer.preview_csv(csv_file_path)
            preview['available_formats'] = cls.list_available_formats()
            
            return preview
            
        except Exception as e:
            logger.error(f"Error previewing CSV: {e}")
            return {'error': str(e)}
    
    @classmethod
    def import_csv(cls, csv_file_path: str, client_id: str, format_name: str = None, mapping: dict = None):
        """
        Import a CSV file with format detection or specific format.
        
        Args:
            csv_file_path: Path to the CSV file
            client_id: Client ID
            format_name: Specific format name (optional, auto-detects if None)
            mapping: Custom column mapping dictionary (optional)
            
        Returns:
            ImportResult object
        """
        try:
            if format_name:
                importer = cls.get_importer_by_name(format_name, client_id)
                if not importer:
                    from .base import ImportResult
                    result = ImportResult()
                    result.add_error(f'Unknown format: {format_name}')
                    return result
            else:
                importer = cls.detect_format(csv_file_path, client_id)
                if not importer:
                    from .base import ImportResult
                    result = ImportResult()
                    result.add_error('Could not detect CSV format')
                    return result
            
            # Convert mapping dict to ColumnMapping if provided
            column_mapping = None
            if mapping:
                from .base import ColumnMapping
                column_mapping = ColumnMapping.from_dict(mapping)
            
            return importer.import_csv(csv_file_path, column_mapping)
            
        except Exception as e:
            logger.error(f"Error importing CSV: {e}")
            from .base import ImportResult
            result = ImportResult()
            result.add_error(str(e))
            return result


# Convenience functions for easy access
def detect_csv_format(csv_file_path: str, client_id: str) -> Optional[BaseTransactionImporter]:
    """Convenience function for format detection."""
    return ImporterFactory.detect_format(csv_file_path, client_id)

def import_csv_file(csv_file_path: str, client_id: str, format_name: str = None, mapping: dict = None):
    """Convenience function for CSV import."""
    return ImporterFactory.import_csv(csv_file_path, client_id, format_name, mapping)

def preview_csv_file(csv_file_path: str, client_id: str, format_name: str = None) -> dict:
    """Convenience function for CSV preview."""
    return ImporterFactory.preview_csv(csv_file_path, client_id, format_name)

def list_supported_formats() -> List[str]:
    """Convenience function to list supported formats."""
    return ImporterFactory.list_available_formats()


if __name__ == "__main__":
    # Test the factory
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    print("Available formats:")
    for fmt in list_supported_formats():
        print(f"  - {fmt}")
    
    # Test getting importer by name
    importer = ImporterFactory.get_importer_by_name("Mercury Bank", "test_client")
    if importer:
        print(f"\\nGot importer: {importer.format_name}")
        print(f"Expected headers: {importer.expected_headers}")
    
    print("\\n✅ Import factory working!")