import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import json
import statistics
from datetime import datetime, timedelta, UTC
from collections import defaultdict
from supabase_client import supabase
from openai_client import openai_client
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def calculate_stats(transactions, period_days=180):
    """Calculate comprehensive statistics for transactions."""
    if not transactions:
        return None
    
    amounts = [t['amount'] for t in transactions]
    dates = [datetime.fromisoformat(t['transaction_date']) for t in transactions]
    
    try:
        # Basic statistics
        stats = {
            'mean': statistics.mean(amounts),
            'stddev': statistics.stdev(amounts) if len(amounts) > 1 else 0,
            'min': min(amounts),
            'max': max(amounts),
            'count': len(amounts),
            'date_range': (min(dates), max(dates))
        }
        
        # Monthly patterns
        months = defaultdict(list)
        for date, amount in zip(dates, amounts):
            key = (date.year, date.month)
            months[key].append(amount)
        
        # Calculate monthly averages
        monthly_avgs = {k: statistics.mean(v) for k, v in months.items()}
        
        # Detect seasonality (compare same month across years)
        seasonal_patterns = defaultdict(list)
        for (year, month), avg in monthly_avgs.items():
            seasonal_patterns[month].append(avg)
        
        # Calculate seasonal variation
        seasonal_variation = {}
        for month, values in seasonal_patterns.items():
            if len(values) > 1:
                seasonal_variation[month] = statistics.stdev(values) / statistics.mean(values)
        
        stats['monthly_averages'] = monthly_avgs
        stats['seasonal_variation'] = seasonal_variation
        
        return stats
    except statistics.StatisticsError:
        return None

def get_vendor_transactions(display_name, cutoff_date):
    """Get all transactions for a vendor's display name."""
    # First get all vendor names for this display name
    vendor_names = supabase.table('vendors') \
        .select('vendor_name') \
        .eq('client_id', 'spyguy') \
        .eq('display_name', display_name) \
        .execute().data
    
    if not vendor_names:
        return []

    # Then get transactions for all these vendor names
    all_transactions = []
    for v in vendor_names:
        txns = supabase.table('transactions') \
            .select('transaction_date,amount') \
            .eq('client_id', 'spyguy') \
            .eq('vendor_name', v['vendor_name']) \
            .gte('transaction_date', cutoff_date) \
            .execute().data
        all_transactions.extend(txns)
    
    return all_transactions

def suggest_forecast_method(stats, current_method):
    """Suggest appropriate forecast method based on transaction patterns."""
    if not stats:
        return 'Manual'
        
    # Check for strong seasonality
    seasonal = any(var > 0.3 for var in stats['seasonal_variation'].values())
    
    # Check for high variance
    high_variance = stats['stddev'] > 0.2 * abs(stats['mean'])
    
    # Check for regular monthly pattern
    monthly_regular = len(stats['monthly_averages']) >= 4
    
    if seasonal:
        return 'SeasonalAvg'
    elif monthly_regular and not high_variance:
        return 'Trailing90Avg'
    elif not monthly_regular and not high_variance:
        return 'Trailing30Avg'
    else:
        return 'Manual'

def run_forecast_variance_review():
    """Run comprehensive forecast variance review workflow."""
    # 1. Fetch vendors and their transactions
    vendors = supabase.table('vendors') \
        .select('display_name,forecast_amount,forecast_frequency,forecast_method') \
        .eq('client_id', 'spyguy') \
        .execute().data

    if not vendors:
        logger.info("No vendors found.")
        return

    logger.info(f"Analyzing {len(vendors)} vendors...")
    review_needed = []

    # Calculate stats for each vendor (use 365 days for seasonal analysis)
    cutoff = (datetime.now(UTC) - timedelta(days=365)).isoformat()
    for vendor in vendors:
        # Get transactions for this vendor
        txns = get_vendor_transactions(vendor['display_name'], cutoff)
        
        # Calculate comprehensive stats
        stats = calculate_stats(txns)
        if not stats:
            continue
            
        # Add stats to vendor record
        vendor.update({
            'transaction_stats': stats,
            'current_method': vendor['forecast_method']
        })
        
        # Check for review triggers
        needs_review = False
        review_reasons = []
        
        # Check for high variance
        if stats['stddev'] > 0.2 * abs(stats['mean']):
            needs_review = True
            review_reasons.append("high_variance")
            
        # Check for seasonal patterns
        if any(var > 0.3 for var in stats['seasonal_variation'].values()):
            needs_review = True
            review_reasons.append("seasonal_pattern")
            
        # Check if current method is appropriate
        suggested_method = suggest_forecast_method(stats, vendor['forecast_method'])
        if suggested_method != vendor['forecast_method']:
            needs_review = True
            review_reasons.append("method_mismatch")
            vendor['suggested_method'] = suggested_method
        
        if needs_review:
            vendor['review_reasons'] = review_reasons
            review_needed.append(vendor)

    if not review_needed:
        logger.info("No forecasts found for review.")
        return

    logger.info(f"Reviewing {len(review_needed)} forecasts...")

    # 2. Ask OpenAI to review
    prompt = f"""Analyze these vendors' forecast configurations and transaction patterns.
For each vendor, consider:
1. Transaction variance and seasonality
2. Current vs suggested forecast method
3. Forecast amount accuracy
4. Specific patterns or anomalies

Return a JSON array with adjustments in this format:
[{{
    "display_name": "vendor_name",
    "adjustment_type": "method|amount|both",
    "suggested_method": "Manual|Trailing30Avg|Trailing90Avg|SeasonalAvg",
    "amount_adjustment": "percentage_change or null",
    "confidence": 0.0-1.0,
    "explanation": "detailed explanation"
}}]

Data:
{json.dumps(review_needed, indent=2)}"""

    response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0
    )
    
    content = response.choices[0].message.content.strip()
    logger.info("\nOpenAI Response: %s", content)
    
    try:
        suggestions = json.loads(content)
        if not isinstance(suggestions, list):
            logger.error("Error: Expected JSON array response")
            return
    except json.JSONDecodeError:
        logger.error("Error: Invalid JSON response from OpenAI")
        return
    
    # 3. Apply suggestions
    updated = 0
    for suggestion in suggestions:
        logger.info(f"\nProcessing adjustment for {suggestion['display_name']}:")
        logger.info(f"  Type: {suggestion['adjustment_type']}")
        logger.info(f"  Explanation: {suggestion['explanation']}")
        
        update_data = {
            'forecast_notes': suggestion['explanation'],
            'review_needed': True,
            'forecast_confidence': suggestion['confidence']
        }
        
        if suggestion['adjustment_type'] in ['method', 'both']:
            update_data['forecast_method'] = suggestion['suggested_method']
            
        if suggestion['adjustment_type'] in ['amount', 'both'] and suggestion['amount_adjustment']:
            # Get current forecast amount
            vendor = next(v for v in vendors if v['display_name'] == suggestion['display_name'])
            current_amount = float(vendor['forecast_amount'] or 0)
            
            # Apply percentage adjustment
            adjustment = float(suggestion['amount_adjustment'].rstrip('%')) / 100
            update_data['forecast_amount'] = current_amount * (1 + adjustment)
        
        try:
            supabase.table('vendors') \
                .update(update_data) \
                .eq('display_name', suggestion['display_name']) \
                .eq('client_id', 'spyguy') \
                .execute()
            updated += 1
        except Exception as e:
            logger.error(f"Error updating {suggestion['display_name']}: {str(e)}")

    logger.info(f"\nUpdated {updated} forecast configurations.")

if __name__ == '__main__':
    run_forecast_variance_review() 