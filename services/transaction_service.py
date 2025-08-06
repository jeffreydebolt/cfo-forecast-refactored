#!/usr/bin/env python3
"""
Transaction Service
Handles database operations for transactions including imports and duplicate detection.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from supabase_client import supabase
from importers.base import TransactionData, ImportResult

logger = logging.getLogger(__name__)


class TransactionService:
    """Service for managing transaction data in the database."""
    
    def __init__(self):
        self.supabase = supabase
    
    def save_import_result(self, result: ImportResult, client_id: str) -> Dict[str, Any]:
        """Save imported transactions to database with auto-mapping."""
        if not result.success or not result.transactions:
            return {
                'success': False,
                'saved_count': 0,
                'duplicate_count': 0,
                'error': 'No valid transactions to save'
            }
        
        logger.info(f"Saving {len(result.transactions)} transactions for client {client_id}")
        
        # Import auto-mapper
        from core.vendor_auto_mapping import auto_mapper
        
        # Batch process for efficiency - get existing transactions once
        existing_transaction_ids = self._get_existing_transaction_ids(client_id)
        
        # Track unique vendors for auto-mapping
        unique_vendors = set()
        
        saved_count = 0
        duplicate_count = 0
        auto_mapped_count = 0
        errors = []
        batch_data = []
        
        for i, transaction in enumerate(result.transactions):
            try:
                # Convert transaction to database format
                transaction_data = self._transaction_to_db_format(transaction, client_id)
                
                # Check for duplicates using cached IDs
                if transaction_data['transaction_id'] in existing_transaction_ids:
                    duplicate_count += 1
                    logger.debug(f"Skipping duplicate: {transaction.vendor_name} on {transaction.date}")
                    continue
                
                # Track unique vendors for auto-mapping
                unique_vendors.add(transaction.vendor_name)
                
                batch_data.append(transaction_data)
                
                # Process in batches of 100 to avoid timeouts
                if len(batch_data) >= 100 or i == len(result.transactions) - 1:
                    batch_saved = self._save_batch(batch_data)
                    saved_count += batch_saved
                    batch_data = []
                    
                    # Show progress
                    if i > 0 and i % 200 == 0:
                        print(f"📊 Processed {i}/{len(result.transactions)} transactions...")
                    
            except Exception as e:
                error_msg = f"Error processing transaction {transaction.vendor_name}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        # Auto-map new vendors after importing transactions
        logger.info(f"🤖 Auto-mapping {len(unique_vendors)} unique vendors...")
        for vendor_name in unique_vendors:
            try:
                if auto_mapper.process_new_vendor(vendor_name, client_id):
                    auto_mapped_count += 1
            except Exception as e:
                logger.error(f"Error auto-mapping vendor {vendor_name}: {e}")
        
        logger.info(f"Import complete: {saved_count} saved, {duplicate_count} duplicates, {auto_mapped_count} auto-mapped, {len(errors)} errors")
        
        return {
            'success': len(errors) == 0 or saved_count > 0,
            'saved_count': saved_count,
            'duplicate_count': duplicate_count,
            'vendors_auto_mapped': auto_mapped_count,
            'errors': errors,
            'total_processed': len(result.transactions)
        }
    
    def _transaction_to_db_format(self, transaction: TransactionData, client_id: str) -> Dict[str, Any]:
        """Convert TransactionData to database format with client_id."""
        # Start with the base dictionary from TransactionData
        data = transaction.to_dict()
        
        # Add required database fields
        data.update({
            'client_id': client_id,
            'transaction_id': self._generate_transaction_id(transaction, client_id),
            'type': 'income' if transaction.amount > 0 else 'expense',
            'reference': '',  # Can be enhanced later
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        })
        
        return data
    
    def _generate_transaction_id(self, transaction: TransactionData, client_id: str) -> str:
        """Generate a unique transaction ID for duplicate detection."""
        # Create a hash based on key fields including reference and timestamp for better uniqueness
        import hashlib
        
        # Use timestamp if available (more precise than just date)
        time_component = transaction.timestamp if transaction.timestamp else transaction.date.strftime('%Y-%m-%d')
        
        # Include reference number for uniqueness (invoice IDs, payout IDs, etc.)
        reference_component = transaction.reference if transaction.reference else ""
        
        # Create comprehensive key for true duplicate detection
        key_string = f"{client_id}_{time_component}_{transaction.vendor_name}_{transaction.amount}_{reference_component}_{transaction.description[:50]}"
        
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_existing_transaction_ids(self, client_id: str) -> set:
        """Get all existing transaction IDs for a client to avoid duplicates."""
        try:
            result = self.supabase.table('transactions').select('transaction_id').eq(
                'client_id', client_id
            ).execute()
            
            return {row['transaction_id'] for row in result.data if row.get('transaction_id')}
            
        except Exception as e:
            logger.warning(f"Error fetching existing transaction IDs: {e}")
            return set()
    
    def _save_batch(self, batch_data: List[Dict[str, Any]]) -> int:
        """Save a batch of transactions to database."""
        if not batch_data:
            return 0
        
        try:
            result = self.supabase.table('transactions').insert(batch_data).execute()
            return len(result.data) if result.data else 0
            
        except Exception as e:
            # If batch fails, try individual inserts
            logger.warning(f"Batch insert failed, trying individual inserts: {e}")
            saved_count = 0
            
            for transaction_data in batch_data:
                try:
                    result = self.supabase.table('transactions').insert(transaction_data).execute()
                    if result.data:
                        saved_count += 1
                except Exception as individual_error:
                    logger.error(f"Failed to save individual transaction: {individual_error}")
            
            return saved_count
    
    def _is_duplicate(self, transaction_data: Dict[str, Any]) -> bool:
        """Check if transaction already exists in database (legacy method - use batch approach instead)."""
        try:
            # Check by transaction_id first (most efficient)
            existing = self.supabase.table('transactions').select('id').eq(
                'transaction_id', transaction_data['transaction_id']
            ).execute()
            
            if existing.data:
                return True
            
            # Fallback check by key fields if transaction_id doesn't exist
            existing = self.supabase.table('transactions').select('id').match({
                'client_id': transaction_data['client_id'],
                'transaction_date': transaction_data['transaction_date'],
                'vendor_name': transaction_data['vendor_name'],
                'amount': transaction_data['amount']
            }).execute()
            
            return len(existing.data) > 0
            
        except Exception as e:
            logger.warning(f"Error checking for duplicates: {e}")
            return False
    
    def get_transaction_stats(self, client_id: str) -> Dict[str, Any]:
        """Get transaction statistics for a client."""
        try:
            result = self.supabase.table('transactions').select(
                'transaction_date, amount'
            ).eq('client_id', client_id).execute()
            
            if not result.data:
                return {
                    'total_count': 0,
                    'date_range': None,
                    'total_income': 0,
                    'total_expenses': 0
                }
            
            transactions = result.data
            dates = [t['transaction_date'] for t in transactions]
            amounts = [float(t['amount']) for t in transactions]
            
            income_total = sum(amount for amount in amounts if amount > 0)
            expense_total = sum(amount for amount in amounts if amount < 0)
            
            return {
                'total_count': len(transactions),
                'date_range': {
                    'earliest': min(dates),
                    'latest': max(dates)
                },
                'total_income': income_total,
                'total_expenses': abs(expense_total)
            }
            
        except Exception as e:
            logger.error(f"Error getting transaction stats: {e}")
            return {
                'total_count': 0,
                'date_range': None,
                'total_income': 0,
                'total_expenses': 0,
                'error': str(e)
            }


# Singleton instance
_transaction_service = None

def get_transaction_service() -> TransactionService:
    """Get the singleton transaction service instance."""
    global _transaction_service
    if _transaction_service is None:
        _transaction_service = TransactionService()
    return _transaction_service