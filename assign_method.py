from datetime import datetime, timedelta
from collections import defaultdict
from statistics import mean, stdev
import logging

logger = logging.getLogger(__name__)

def detect_frequency(transactions):
    """
    Detect if a vendor has regular monthly activity based on transaction history.
    Returns tuple of (frequency, forecast_day)
    """
    if not transactions or len(transactions) < 3:
        logger.info("Not enough transactions to detect pattern")
        return 'irregular', None

    today = datetime.today()
    six_months_ago = today - timedelta(days=180)
    
    # Filter last 180 days
    recent_txns = [t for t in transactions if t['date'] >= six_months_ago]
    if len(recent_txns) < 3:
        logger.info("Less than 3 transactions in past 6 months")
        return 'irregular', None

    # Bucket by (year, month)
    months_seen = defaultdict(list)
    for txn in recent_txns:
        key = (txn['date'].year, txn['date'].month)
        months_seen[key].append(txn['date'])

    # Check for regular monthly pattern
    if len(months_seen) >= 3:
        # Calculate average weekday (Mon=0, Sun=6)
        all_days = [d.weekday() for days in months_seen.values() for d in days]
        avg_weekday = round(sum(all_days) / len(all_days))
        logger.info(f"Detected monthly pattern with average day {avg_weekday}")
        return 'monthly', avg_weekday

    logger.info("No clear monthly pattern detected")
    return 'irregular', None

def estimate_payment_day(transactions):
    """Estimate the day of month for payments based on transaction history"""
    if not transactions:
        return None
        
    # Get all days of month from transactions
    days = [t['date'].day for t in transactions]
    
    # Use mode (most common day) if available, otherwise average
    if days:
        from statistics import mode
        try:
            return mode(days)
        except:
            return round(sum(days) / len(days))
    return None

def get_forecast_method(frequency, transactions):
    """Determine the appropriate forecast method based on frequency and data"""
    if frequency == 'monthly':
        return 'Trailing90Avg'
    elif frequency == 'weekly':
        return 'Trailing30Avg'
    else:
        return 'Manual'

def infer_forecast_method(vendor_name, txns):
    if len(txns) < 3:
        return 'Manual'
    frequency, forecast_day = detect_frequency(txns)
    if frequency == 'monthly':
        return 'Trailing90Avg'
    elif frequency in ['weekly', 'daily']:
        return 'Trailing30Avg'
    return 'Manual' 