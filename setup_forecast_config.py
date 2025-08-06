from forecast.openai_infer import ask_openai_for_forecast_metadata
from supabase_client import supabase
from datetime import datetime, timedelta
import logging
import re
from forecast.assign_method import detect_frequency
from forecast.utils import get_trailing_average

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_transactions_for_vendor(vendor_name, client_id="spyguy", vendor_group=None):
    """Get transactions for a vendor with smart lookback period"""
    # Dynamic lookback: 90 days for fast-moving vendors, 365 for others
    if vendor_group in ['Gusto Payments', 'Stripe Transactions', 'Shopify Payments']:
        days = 90
    else:
        days = 365

    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    response = supabase.table('transactions') \
        .select('transaction_date, amount') \
        .eq('vendor_name', vendor_name) \
        .eq('client_id', client_id) \
        .gte('transaction_date', start_date.isoformat()) \
        .lte('transaction_date', end_date.isoformat()) \
        .order('transaction_date') \
        .execute()

    return [
        {'date': tx['transaction_date'], 'amount': float(tx['amount'])}
        for tx in response.data
    ] if response.data else []

def update_vendor_config(vendor_name, method, frequency, payment_day, notes, source):
    """Update vendor configuration in the database"""
    try:
        response = supabase.table('vendors').update({
            'forecast_method': method,
            'forecast_frequency': frequency,
            'forecast_day': payment_day,
            'forecast_notes': notes,
            'forecast_source': source
        }).eq('vendor_name', vendor_name).execute()
        
        if response.error:
            logger.error(f"Error updating vendor config: {response.error}")
            return False
        return True
    except Exception as e:
        logger.error(f"Exception updating vendor config: {str(e)}")
        return False

def configure_forecast_for_vendor(vendor):
    """Configure forecast settings for a vendor"""
    try:
        # Get transactions with vendor group context
        txns = get_transactions_for_vendor(
            vendor_name=vendor['vendor_name'], 
            vendor_group=vendor.get('vendor_group')
        )
        
        if not txns or len(txns) < 3:
            # Use OpenAI for sparse data
            meta = ask_openai_for_forecast_metadata(vendor['vendor_name'], txns)
            source = "OpenAI"
        else:
            # Try pattern detection first
            frequency, forecast_day = detect_frequency(txns)
            if frequency == 'monthly':
                method = 'Trailing90Avg'
                meta = {
                    'forecast_method': method,
                    'frequency': frequency,
                    'payment_day': forecast_day,
                    'notes': f"Activity detected in {len(txns)} transactions over past 6 months"
                }
                source = "Pattern"
            else:
                # Fallback to OpenAI
                meta = ask_openai_for_forecast_metadata(vendor['vendor_name'], txns)
                source = "OpenAI"

        success = update_vendor_config(
            vendor['vendor_name'],
            method=meta['forecast_method'],
            frequency=meta['frequency'],
            payment_day=meta['payment_day'],
            notes=meta['notes'],
            source=source
        )
        
        if success:
            logger.info(f"✅ {vendor['vendor_name']} → {meta['forecast_method']} ({meta['frequency']}) via {source}")
        else:
            logger.error(f"❌ Failed to update config for {vendor['vendor_name']}")
            
        return success
    except Exception as e:
        logger.error(f"Error configuring forecast for vendor {vendor['vendor_name']}: {str(e)}")
        return False 