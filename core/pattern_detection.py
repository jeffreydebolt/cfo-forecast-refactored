"""
Smart Pattern Detection System
Based on the original sophisticated logic with improvements for multi-client support and dynamic dates.
"""

from collections import Counter
from datetime import datetime, timedelta, UTC
import statistics
import logging
from typing import List, Dict, Any, Optional, Tuple
from supabase_client import supabase

logger = logging.getLogger(__name__)

# Configuration constants
LOOKBACK_DAYS = 180
MONTHLY_MIN_MONTHS = 6
IRREGULAR_MIN_OCCURRENCES = 2

def parse_date(date_str: str) -> datetime:
    """Parse date string to UTC datetime."""
    if isinstance(date_str, str):
        # Handle both ISO format and simple YYYY-MM-DD
        if 'T' in date_str:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        else:
            dt = datetime.fromisoformat(date_str + 'T00:00:00+00:00')
    else:
        dt = date_str
    
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt

def get_latest_transaction_date(client_id: str) -> datetime:
    """Get the latest transaction date for a client (fixes hardcoded April 2025 issue)."""
    try:
        result = supabase.table('transactions').select('transaction_date').eq(
            'client_id', client_id
        ).order('transaction_date', desc=True).limit(1).execute()
        
        if result.data:
            latest_date = parse_date(result.data[0]['transaction_date'])
            logger.info(f"Latest transaction date for {client_id}: {latest_date.strftime('%Y-%m-%d')}")
            return latest_date
        else:
            # Fallback to current date if no transactions
            return datetime.now(UTC)
            
    except Exception as e:
        logger.error(f"Error getting latest transaction date: {e}")
        return datetime.now(UTC)

def analyze_transaction_history(transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze transaction history to extract calendar patterns.
    
    Args:
        transactions: List of transactions with 'transaction_date' and 'amount'
        
    Returns:
        Dict with pattern analysis results:
        - months: Set of active months (YYYY-MM)
        - weeks: Set of active weeks (YYYY-Www) 
        - dom: Counter of day-of-month occurrences
        - dow: Counter of day-of-week occurrences (1=Mon, 7=Sun)
        - amounts: List of transaction amounts
    """
    months = set()
    weeks = set()
    dom = Counter()  # Day of month
    dow = Counter()  # Day of week
    amounts = []

    for txn in transactions:
        dt = parse_date(txn['transaction_date'])
        amounts.append(float(txn['amount']))
        
        # Track active months
        months.add(f"{dt.year}-{dt.month:02d}")
        
        # Track active weeks
        iso_year, iso_week, _ = dt.isocalendar()
        weeks.add(f"{iso_year}-W{iso_week:02d}")
        
        # Count day patterns
        dom[dt.day] += 1
        dow[dt.isoweekday()] += 1

    return {
        'months': months,
        'weeks': weeks,
        'dom': dom,
        'dow': dow,
        'amounts': amounts
    }

def classify_vendor_pattern(transactions: List[Dict[str, Any]], client_id: str) -> Dict[str, Any]:
    """
    Classify vendor based on transaction patterns with enhanced detection for daily, bi-weekly, weekly, and monthly patterns.
    
    Args:
        transactions: List of transactions with date and amount
        client_id: Client ID for dynamic date calculation
        
    Returns:
        Dict with classification results
    """
    if not transactions:
        return {
            'frequency': 'irregular',
            'forecast_day': None,
            'forecast_amount': 0.0,
            'confidence': 0.0,
            'explanation': 'No transactions found'
        }
    
    # Analyze transaction patterns
    stats = analyze_transaction_history(transactions)
    num_months = len(stats['months'])
    num_weeks = len(stats['weeks'])
    
    # Check for daily pattern first (like Shopify)
    daily_result = detect_daily_pattern(transactions)
    
    logger.info(f"Analysis: {len(transactions)} transactions, {num_months} months, {num_weeks} weeks")
    
    if daily_result and daily_result['confidence'] >= 0.4:
        # Daily pattern detected (like Shopify) - roll up to weekly
        frequency = 'daily_weekly'
        forecast_day = None  # Daily doesn't have specific day
        confidence = daily_result['confidence']
        explanation = daily_result['explanation']
        
        # Calculate weekly amount from daily pattern
        forecast_amount = calculate_daily_weekly_amount(transactions, client_id)
        
    elif bi_weekly_result := detect_bi_weekly_pattern(transactions):
        if bi_weekly_result['confidence'] >= 0.6:
            # Strong bi-weekly pattern detected
            frequency = 'bi_weekly'
            forecast_day = bi_weekly_result['day_of_week']
            confidence = bi_weekly_result['confidence']
            explanation = bi_weekly_result['explanation']
            
            # Calculate amount based on bi-weekly pattern
            forecast_amount = calculate_bi_weekly_amount(transactions)
    
    elif num_months >= MONTHLY_MIN_MONTHS:
        # Monthly pattern detected
        frequency = 'monthly'
        forecast_day = stats['dom'].most_common(1)[0][0]  # Most common day of month
        confidence = min(num_months / MONTHLY_MIN_MONTHS, 1.0)
        explanation = f"Monthly pattern: pays on {forecast_day}th of month ({num_months} months)"
        
        # For monthly patterns, use appropriate amount calculation
        forecast_amount = calculate_monthly_amount(transactions, client_id)
        
    elif len(transactions) >= 4:
        # Weekly pattern detected  
        frequency = 'weekly'
        forecast_day = stats['dow'].most_common(1)[0][0]  # Most common day of week
        expected_weeks = LOOKBACK_DAYS / 7
        confidence = min(num_weeks / expected_weeks, 1.0)
        
        # Day names for explanation
        day_names = {1: 'Monday', 2: 'Tuesday', 3: 'Wednesday', 4: 'Thursday', 
                    5: 'Friday', 6: 'Saturday', 7: 'Sunday'}
        explanation = f"Weekly pattern: pays on {day_names[forecast_day]}s ({num_weeks} weeks)"
        
        # For weekly patterns, use appropriate amount calculation
        forecast_amount = calculate_weekly_amount(transactions, client_id)
        
    else:
        # Irregular pattern
        frequency = 'irregular'
        if sum(stats['dom'].values()) >= IRREGULAR_MIN_OCCURRENCES:
            forecast_day = stats['dom'].most_common(1)[0][0]
            confidence = stats['dom'][forecast_day] / sum(stats['dom'].values())
            explanation = f"Irregular pattern: most often on {forecast_day}th ({confidence:.1%} of time)"
        else:
            forecast_day = None
            confidence = 0.0
            explanation = "Irregular pattern: no clear day preference"
            
        # For irregular patterns, use trailing average
        forecast_amount = calculate_trailing_average(transactions, client_id)
    
    logger.info(f"Pattern: {frequency}, Day: {forecast_day}, Amount: ${forecast_amount}, Confidence: {confidence:.2f}")
    
    return {
        'frequency': frequency,
        'forecast_day': forecast_day,
        'forecast_amount': forecast_amount,
        'confidence': round(confidence, 2),
        'explanation': explanation,
        'months_active': num_months,
        'weeks_active': num_weeks,
        'transaction_count': len(transactions),
        'daily_analysis': daily_result if 'daily_result' in locals() else None,
        'bi_weekly_analysis': bi_weekly_result if 'bi_weekly_result' in locals() else None
    }

def update_vendor_group_forecast_config(group_name: str, client_id: str, pattern_result: Dict[str, Any]) -> bool:
    """
    Update vendor GROUP forecast configuration in database (CORRECT WORKFLOW).
    
    Args:
        group_name: Vendor group name
        client_id: Client ID
        pattern_result: Results from classify_vendor_pattern
        
    Returns:
        bool: Success status
    """
    try:
        update_data = {
            'forecast_frequency': pattern_result['frequency'],
            'forecast_day': pattern_result['forecast_day'],
            'forecast_amount': pattern_result['forecast_amount'],
            'forecast_confidence': pattern_result['confidence'],
            'updated_at': datetime.now(UTC).isoformat()
        }
        
        result = supabase.table('vendor_groups').update(update_data).eq(
            'group_name', group_name
        ).eq(
            'client_id', client_id
        ).execute()
        
        if result.data:
            logger.info(f"Updated forecast config for vendor group {group_name}: {pattern_result['explanation']}")
            return True
        else:
            logger.warning(f"No vendor groups updated for {group_name}")
            return False
            
    except Exception as e:
        logger.error(f"Error updating vendor group config for {group_name}: {e}")
        return False

def update_vendor_forecast_config(display_name: str, client_id: str, pattern_result: Dict[str, Any]) -> bool:
    """
    Update vendor forecast configuration in database (LEGACY - for backward compatibility).
    
    Args:
        display_name: Vendor display name
        client_id: Client ID
        pattern_result: Results from classify_vendor_pattern
        
    Returns:
        bool: Success status
    """
    try:
        update_data = {
            'forecast_frequency': pattern_result['frequency'],
            'forecast_day': pattern_result['forecast_day'],
            'forecast_amount': pattern_result['forecast_amount'],
            'forecast_confidence': pattern_result['confidence'],
            'forecast_method': 'pattern_detected',  # Mark as auto-detected
            'updated_at': datetime.now(UTC).isoformat()
        }
        
        result = supabase.table('vendors').update(update_data).eq(
            'display_name', display_name
        ).eq(
            'client_id', client_id
        ).execute()
        
        if result.data:
            logger.info(f"Updated forecast config for {display_name}: {pattern_result['explanation']}")
            return True
        else:
            logger.warning(f"No vendors updated for {display_name}")
            return False
            
    except Exception as e:
        logger.error(f"Error updating vendor config for {display_name}: {e}")
        return False

def detect_bi_weekly_pattern(transactions: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Enhanced bi-weekly pattern detection for all payment processors and vendors.
    
    Args:
        transactions: List of transactions
        
    Returns:
        Dict with bi-weekly pattern info if detected, None otherwise
    """
    if len(transactions) < 6:  # Need at least 6 transactions for reliable bi-weekly detection
        return None
    
    # Sort transactions by date
    sorted_txns = sorted(transactions, key=lambda x: parse_date(x['transaction_date']))
    
    # Separate large and small transactions for better pattern detection
    amounts = [abs(float(txn['amount'])) for txn in sorted_txns]
    median_amount = statistics.median(amounts)
    
    # Consider "large" transactions as those significantly above median
    # This helps separate Amazon's $45k deposits from $500 fees
    large_threshold = median_amount * 2  # Transactions 2x+ median are "large"
    
    large_transactions = [txn for txn in sorted_txns if abs(float(txn['amount'])) >= large_threshold]
    small_transactions = [txn for txn in sorted_txns if abs(float(txn['amount'])) < large_threshold]
    
    # Try to detect bi-weekly pattern in large transactions first
    bi_weekly_result = _analyze_intervals_for_bi_weekly(large_transactions, "large")
    
    if bi_weekly_result and bi_weekly_result['confidence'] >= 0.6:
        logger.info(f"Detected bi-weekly pattern in LARGE transactions: {bi_weekly_result['explanation']}")
        return bi_weekly_result
    
    # If no strong pattern in large transactions, try all transactions
    bi_weekly_result = _analyze_intervals_for_bi_weekly(sorted_txns, "all")
    
    if bi_weekly_result and bi_weekly_result['confidence'] >= 0.6:
        logger.info(f"Detected bi-weekly pattern in ALL transactions: {bi_weekly_result['explanation']}")
        return bi_weekly_result
    
    logger.debug(f"No strong bi-weekly pattern detected. Large txns: {len(large_transactions)}, All txns: {len(sorted_txns)}")
    return None

def _analyze_intervals_for_bi_weekly(transactions: List[Dict[str, Any]], txn_type: str) -> Optional[Dict[str, Any]]:
    """Analyze intervals between transactions to detect bi-weekly patterns."""
    if len(transactions) < 4:
        return None
    
    # Calculate days between consecutive transactions
    intervals = []
    for i in range(1, len(transactions)):
        prev_date = parse_date(transactions[i-1]['transaction_date'])
        curr_date = parse_date(transactions[i]['transaction_date'])
        interval = (curr_date - prev_date).days
        intervals.append(interval)
    
    # Check for bi-weekly intervals (12-16 days, allowing variance)
    bi_weekly_intervals = [i for i in intervals if 12 <= i <= 16]
    
    # Check for monthly intervals that might be split bi-weekly cycles (25-35 days)
    monthly_intervals = [i for i in intervals if 25 <= i <= 35]
    
    # Bi-weekly confidence: percentage of intervals that are bi-weekly
    bi_weekly_confidence = len(bi_weekly_intervals) / len(intervals) if intervals else 0
    
    # Monthly split confidence: percentage that could be every-other bi-weekly cycle
    monthly_split_confidence = len(monthly_intervals) / len(intervals) if intervals else 0
    
    # Combined confidence for bi-weekly pattern
    total_confidence = bi_weekly_confidence + (monthly_split_confidence * 0.5)
    
    if total_confidence >= 0.6:  # 60% confidence threshold
        avg_interval = statistics.mean(bi_weekly_intervals + monthly_intervals)
        
        # Find the most common day of week
        stats = analyze_transaction_history(transactions)
        most_common_dow = stats['dow'].most_common(1)[0][0]
        
        day_names = {1: 'Monday', 2: 'Tuesday', 3: 'Wednesday', 4: 'Thursday', 
                    5: 'Friday', 6: 'Saturday', 7: 'Sunday'}
        
        return {
            'pattern_type': 'bi_weekly',
            'interval_days': avg_interval,
            'day_of_week': most_common_dow,
            'day_name': day_names[most_common_dow],
            'confidence': total_confidence,
            'transaction_type': txn_type,
            'bi_weekly_intervals': len(bi_weekly_intervals),
            'monthly_intervals': len(monthly_intervals),
            'explanation': f"Bi-weekly pattern ({txn_type}): every {avg_interval:.0f} days on {day_names[most_common_dow]}s ({total_confidence:.1%} confidence)"
        }
    
    return None

def detect_daily_pattern(transactions: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Detect daily patterns (like Shopify deposits) that should be aggregated weekly.
    
    Args:
        transactions: List of transactions
        
    Returns:
        Dict with daily pattern info if detected, None otherwise
    """
    if len(transactions) < 20:  # Need sufficient data for daily pattern detection
        return None
    
    # Sort transactions by date
    sorted_txns = sorted(transactions, key=lambda x: parse_date(x['transaction_date']))
    
    # Check date coverage - daily patterns should have frequent transactions
    if not sorted_txns:
        return None
        
    start_date = parse_date(sorted_txns[0]['transaction_date'])
    end_date = parse_date(sorted_txns[-1]['transaction_date'])
    total_days = (end_date - start_date).days + 1
    
    # Count unique transaction dates
    unique_dates = len(set(parse_date(txn['transaction_date']).date() for txn in sorted_txns))
    
    # Daily pattern should have transactions on at least 30% of days
    coverage = unique_dates / total_days if total_days > 0 else 0
    
    if coverage >= 0.3:  # 30% coverage indicates frequent/daily pattern
        # Calculate average weekly amount from recent data
        recent_weeks = min(12, len(sorted_txns) // 7)  # Last 12 weeks or available data
        
        if recent_weeks >= 4:  # Need at least 4 weeks for confidence
            confidence = min(coverage * 1.5, 1.0)  # Scale coverage to confidence
            
            explanation = f"Daily pattern: {unique_dates} transaction days over {total_days} days ({coverage:.1%} coverage)"
            
            return {
                'pattern_type': 'daily',
                'coverage': coverage,
                'unique_dates': unique_dates,
                'total_days': total_days,
                'confidence': confidence,
                'explanation': explanation
            }
    
    return None

def calculate_daily_weekly_amount(transactions: List[Dict[str, Any]], client_id: str) -> float:
    """Calculate weekly amount from daily pattern transactions."""
    if not transactions:
        return 0.0
    
    # Sort by date and use recent data
    sorted_txns = sorted(transactions, key=lambda x: parse_date(x['transaction_date']), reverse=True)
    
    # Use last 90 days for daily patterns to get current weekly average
    latest_date = parse_date(sorted_txns[0]['transaction_date'])
    ninety_days_ago = latest_date - timedelta(days=90)
    recent_txns = [txn for txn in sorted_txns if parse_date(txn['transaction_date']) >= ninety_days_ago]
    
    if not recent_txns:
        recent_txns = sorted_txns  # Fallback to all data
    
    # Calculate weekly totals from recent data
    weekly_totals = {}
    for txn in recent_txns:
        txn_date = parse_date(txn['transaction_date'])
        # Get ISO week year and week number
        year, week, _ = txn_date.isocalendar()
        week_key = f"{year}-W{week:02d}"
        
        if week_key not in weekly_totals:
            weekly_totals[week_key] = 0.0
        weekly_totals[week_key] += float(txn['amount'])
    
    if weekly_totals:
        # Average of recent weekly totals
        weekly_amounts = list(weekly_totals.values())
        avg_weekly = statistics.mean(weekly_amounts)
        forecast_amount = round(avg_weekly, 2)
        
        logger.info(f"Daily-weekly amount from {len(weekly_amounts)} recent weeks: ${forecast_amount}")
    else:
        # Fallback: total recent amount divided by weeks
        total_amount = sum(float(txn['amount']) for txn in recent_txns)
        days_span = (parse_date(recent_txns[0]['transaction_date']) - parse_date(recent_txns[-1]['transaction_date'])).days + 1
        weeks_span = max(1, days_span / 7)
        forecast_amount = round(total_amount / weeks_span, 2)
        
        logger.info(f"Daily-weekly amount from {len(recent_txns)} transactions over {weeks_span:.1f} weeks: ${forecast_amount}")
    
    return forecast_amount

def calculate_bi_weekly_amount(transactions: List[Dict[str, Any]]) -> float:
    """Calculate forecast amount for bi-weekly patterns using recent large transactions, excluding outliers."""
    if not transactions:
        return 0.0
    
    # Sort by date to get recent transactions first
    sorted_txns = sorted(transactions, key=lambda x: parse_date(x['transaction_date']), reverse=True)
    
    # Use last 6 months of data to avoid old outliers
    latest_date = parse_date(sorted_txns[0]['transaction_date'])
    six_months_ago = latest_date - timedelta(days=180)
    recent_txns = [txn for txn in sorted_txns if parse_date(txn['transaction_date']) >= six_months_ago]
    
    if not recent_txns:
        recent_txns = sorted_txns  # Fallback to all data
    
    amounts = [float(txn['amount']) for txn in recent_txns]
    median_amount = statistics.median([abs(amt) for amt in amounts])
    
    # Focus on large transactions for bi-weekly forecasts (like Amazon's $45k deposits)
    large_threshold = median_amount * 2
    large_amounts = [amt for amt in amounts if abs(amt) >= large_threshold]
    
    if large_amounts and len(large_amounts) >= 3:
        # Remove outliers using IQR method for more stable forecasts
        sorted_large = sorted(large_amounts)
        q1 = sorted_large[len(sorted_large)//4]
        q3 = sorted_large[3*len(sorted_large)//4]
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        # Filter out outliers (like Prime Day spikes)
        normal_amounts = [amt for amt in large_amounts if lower_bound <= amt <= upper_bound]
        
        if normal_amounts:
            forecast_amount = round(statistics.mean(normal_amounts), 2)
            logger.info(f"Bi-weekly amount from {len(normal_amounts)} normal large transactions (recent 6 months, outliers removed): ${forecast_amount}")
        else:
            # If all are outliers, use median of large amounts
            forecast_amount = round(statistics.median(large_amounts), 2)
            logger.info(f"Bi-weekly amount from median of {len(large_amounts)} large transactions (all outliers): ${forecast_amount}")
    elif large_amounts:
        # Use all large amounts if we have few data points
        forecast_amount = round(statistics.mean(large_amounts), 2)
        logger.info(f"Bi-weekly amount from {len(large_amounts)} large transactions (insufficient data for outlier removal): ${forecast_amount}")
    else:
        # Fallback to all transactions if no clear large ones
        forecast_amount = round(statistics.mean(amounts), 2)
        logger.info(f"Bi-weekly amount from all {len(amounts)} transactions: ${forecast_amount}")
    
    return forecast_amount

def calculate_monthly_amount(transactions: List[Dict[str, Any]], client_id: str) -> float:
    """Calculate forecast amount for monthly patterns using recent data."""
    # Use last 6 months of data for monthly patterns
    latest_date = get_latest_transaction_date(client_id)
    six_months_ago = latest_date - timedelta(days=180)
    
    recent_transactions = [
        txn for txn in transactions 
        if parse_date(txn['transaction_date']) >= six_months_ago
    ]
    
    if recent_transactions:
        amounts = [float(txn['amount']) for txn in recent_transactions]
        forecast_amount = round(statistics.mean(amounts), 2)
        logger.info(f"Monthly amount from {len(recent_transactions)} recent transactions: ${forecast_amount}")
    else:
        # Fallback to all transactions
        amounts = [float(txn['amount']) for txn in transactions]
        forecast_amount = round(statistics.mean(amounts), 2) if amounts else 0.0
        logger.info(f"Monthly amount from all {len(transactions)} transactions: ${forecast_amount}")
    
    return forecast_amount

def calculate_weekly_amount(transactions: List[Dict[str, Any]], client_id: str) -> float:
    """Calculate forecast amount for weekly patterns using recent data."""
    # Use last 3 months of data for weekly patterns
    latest_date = get_latest_transaction_date(client_id)
    three_months_ago = latest_date - timedelta(days=90)
    
    recent_transactions = [
        txn for txn in transactions 
        if parse_date(txn['transaction_date']) >= three_months_ago
    ]
    
    if recent_transactions:
        amounts = [float(txn['amount']) for txn in recent_transactions]
        forecast_amount = round(statistics.mean(amounts), 2)
        logger.info(f"Weekly amount from {len(recent_transactions)} recent transactions: ${forecast_amount}")
    else:
        # Fallback to all transactions
        amounts = [float(txn['amount']) for txn in transactions]
        forecast_amount = round(statistics.mean(amounts), 2) if amounts else 0.0
        logger.info(f"Weekly amount from all {len(transactions)} transactions: ${forecast_amount}")
    
    return forecast_amount

def calculate_trailing_average(transactions: List[Dict[str, Any]], client_id: str) -> float:
    """Calculate trailing 90-day average for irregular patterns."""
    latest_date = get_latest_transaction_date(client_id)
    trail_start = latest_date - timedelta(days=90)
    
    recent_transactions = [
        txn for txn in transactions 
        if parse_date(txn['transaction_date']) >= trail_start
    ]
    
    if recent_transactions:
        amounts = [float(txn['amount']) for txn in recent_transactions]
        forecast_amount = round(statistics.mean(amounts), 2)
        logger.info(f"Trailing average from {len(recent_transactions)} recent transactions: ${forecast_amount}")
    else:
        # Fallback to all transactions
        amounts = [float(txn['amount']) for txn in transactions]
        forecast_amount = round(statistics.mean(amounts), 2) if amounts else 0.0
        logger.info(f"Trailing average from all {len(transactions)} transactions: ${forecast_amount}")
    
    return forecast_amount