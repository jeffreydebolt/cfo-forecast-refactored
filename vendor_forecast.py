import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import logging
from datetime import datetime, timedelta, UTC
from collections import Counter, defaultdict
from typing import List, Dict, Any, Optional, Tuple
from supabase_client import supabase
import json
from openai_client import openai_client
from config.client_context import get_current_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def read_transactions_by_display_name(
    display_name: str,
    client_id: str = None,
    lookback_days: int = 180
) -> List[Dict[str, Any]]:
    """
    Read transactions for a display_name, aggregating all vendor_name variants.
    
    Args:
        display_name: The display_name to fetch transactions for
        client_id: The client ID (if None, uses current client)
        lookback_days: Number of days to look back
        
    Returns:
        List of transactions with date and amount
    """
    if client_id is None:
        client_id = get_current_client()
    
    try:
        # Get all vendor_name variants for this display_name
        vendor_resp = supabase.table("vendors") \
            .select("vendor_name") \
            .eq("client_id", client_id) \
            .eq("display_name", display_name) \
            .execute()
            
        vendor_names = [v["vendor_name"].split(';')[0].strip() for v in vendor_resp.data]  # Get the first part before semicolon
        if not vendor_names:
            logger.warning(f"No vendor names found for display_name: {display_name}")
            return []
            
        # Calculate cutoff date - use April 2025 as base date
        base_date = datetime(2025, 4, 29, tzinfo=UTC)  # Latest transaction date
        cutoff = (base_date - timedelta(days=lookback_days)).strftime('%Y-%m-%d')
        logger.info(f"Looking for transactions between {cutoff} and {base_date.strftime('%Y-%m-%d')}")
        logger.info(f"Looking for vendor names: {vendor_names}")
        
        # Get transactions - using ilike for case-insensitive partial matching
        all_txns = []
        for vendor_name in vendor_names:
            txns = supabase.table("transactions") \
                .select("transaction_date,amount") \
                .eq("client_id", client_id) \
                .ilike("vendor_name", f"%{vendor_name}%") \
                .filter("transaction_date", "gte", cutoff) \
                .filter("transaction_date", "lte", base_date.strftime('%Y-%m-%d')) \
                .execute().data
            all_txns.extend(txns)
            
        if all_txns:
            logger.info(f"Found {len(all_txns)} transactions")
            
        # Let's also check what transactions exist for this vendor without date filters
        total_txns = []
        for vendor_name in vendor_names:
            txns = supabase.table("transactions") \
                .select("transaction_date,amount") \
                .eq("client_id", client_id) \
                .ilike("vendor_name", f"%{vendor_name}%") \
                .execute().data
            total_txns.extend(txns)
            
        if total_txns:
            logger.info(f"Total transactions for this vendor: {len(total_txns)}")
            logger.info(f"Transaction dates: {sorted(set(tx['transaction_date'] for tx in total_txns))}")
            
        return sorted(all_txns, key=lambda x: x["transaction_date"])
        
    except Exception as e:
        logger.error(f"Error reading transactions for {display_name}: {str(e)}")
        return []

def classify_vendor(
    transactions: List[Dict[str, Any]],
    is_inventory: bool = False
) -> Dict[str, Any]:
    """
    Classify vendor based on transaction patterns.
    
    Args:
        transactions: List of transactions with date and amount
        is_inventory: Whether this is an inventory vendor
        
    Returns:
        Dict with classification details
    """
    try:
        if not transactions:
            return {
                "classification": "irregular",
                "confidence": 0.0,
                "months_active": 0,
                "explanation": "No transactions found"
            }
            
        # Group transactions by month
        months = set()
        for tx in transactions:
            date = datetime.fromisoformat(tx["transaction_date"].replace("Z", "+00:00"))
            months.add((date.year, date.month))
            
        num_months = len(months)
        
        # Determine classification
        if is_inventory:
            classification = "regular"
            confidence = 0.9
            explanation = "Inventory vendor - assumed regular"
        elif num_months >= 6:
            classification = "regular"
            confidence = 0.8
            explanation = f"Active in {num_months} of last 6 months"
        elif num_months >= 4:
            classification = "quasi-regular"
            confidence = 0.6
            explanation = f"Active in {num_months} of last 6 months - needs review"
        else:
            classification = "irregular"
            confidence = 0.4
            explanation = f"Active in only {num_months} of last 6 months"
            
        return {
            "classification": classification,
            "confidence": confidence,
            "months_active": num_months,
            "explanation": explanation
        }
        
    except Exception as e:
        logger.error(f"Error classifying vendor: {str(e)}")
        return {
            "classification": "irregular",
            "confidence": 0.0,
            "months_active": 0,
            "explanation": f"Error in classification: {str(e)}"
        }

def compute_forecast(
    transactions: List[Dict[str, Any]],
    classification: str
) -> Dict[str, Any]:
    """
    Compute forecast based on classification and transaction history.
    
    Args:
        transactions: List of transactions with date and amount
        classification: Vendor classification (regular/quasi-regular/irregular)
        
    Returns:
        Dict with forecast details
    """
    try:
        if not transactions:
            return {
                "method": "manual",
                "frequency": "irregular",
                "payment_day": None,
                "forecast_amount": None,
                "confidence": 0.0,
                "explanation": "No transactions to base forecast on"
            }
            
        # Convert dates and sort
        txns = []
        for tx in transactions:
            date = datetime.fromisoformat(tx["transaction_date"].replace("Z", "+00:00"))
            txns.append({
                "date": date,
                "amount": float(tx["amount"])
            })
        txns.sort(key=lambda x: x["date"])
        
        if classification == "regular":
            # Find modal payment day
            days = [t["date"].day for t in txns]
            payment_day = Counter(days).most_common(1)[0][0]
            
            # Calculate trailing averages
            now = datetime(2025, 4, 29, tzinfo=UTC)
            thirty_days = now - timedelta(days=30)
            ninety_days = now - timedelta(days=90)
            
            recent_30 = [t["amount"] for t in txns if t["date"].replace(tzinfo=UTC) >= thirty_days]
            recent_90 = [t["amount"] for t in txns if t["date"].replace(tzinfo=UTC) >= ninety_days]
            
            avg_30 = sum(recent_30) / len(recent_30) if recent_30 else None
            avg_90 = sum(recent_90) / len(recent_90) if recent_90 else None
            
            # Prefer 90-day if available, otherwise 30-day
            forecast_amount = avg_90 if avg_90 else avg_30
            
            return {
                "method": "trailing_avg",
                "frequency": "monthly",
                "payment_day": payment_day,
                "forecast_amount": round(forecast_amount, 2) if forecast_amount else None,
                "confidence": 0.8,
                "explanation": f"Monthly payment on day {payment_day}, based on {len(recent_90)} transactions"
            }
            
        elif classification == "quasi-regular":
            # Similar to regular but with lower confidence
            days = [t["date"].day for t in txns]
            payment_day = Counter(days).most_common(1)[0][0]
            
            now = datetime(2025, 4, 29, tzinfo=UTC)
            ninety_days = now - timedelta(days=90)
            recent_90 = [t["amount"] for t in txns if t["date"].replace(tzinfo=UTC) >= ninety_days]
            
            forecast_amount = sum(recent_90) / len(recent_90) if recent_90 else None
            
            return {
                "method": "trailing_avg",
                "frequency": "monthly",
                "payment_day": payment_day,
                "forecast_amount": round(forecast_amount, 2) if forecast_amount else None,
                "confidence": 0.6,
                "explanation": f"Quasi-regular monthly payment on day {payment_day}, needs review"
            }
            
        else:  # irregular
            # Mimic last 6 months of activity
            now = datetime(2025, 4, 29, tzinfo=UTC)
            six_months = now - timedelta(days=180)
            recent = [t for t in txns if t["date"].replace(tzinfo=UTC) >= six_months]
            
            if not recent:
                return {
                    "method": "manual",
                    "frequency": "irregular",
                    "payment_day": None,
                    "forecast_amount": None,
                    "confidence": 0.0,
                    "explanation": "No recent transactions to base forecast on"
                }
                
            # Group by month and calculate average
            monthly_avgs = defaultdict(list)
            for tx in recent:
                key = (tx["date"].year, tx["date"].month)
                monthly_avgs[key].append(tx["amount"])
                
            monthly_forecasts = {
                month: sum(amounts) / len(amounts)
                for month, amounts in monthly_avgs.items()
            }
            
            return {
                "method": "mimic",
                "frequency": "irregular",
                "payment_day": None,
                "forecast_amount": None,
                "monthly_forecasts": {
                    f"{year}-{month:02d}": round(amount, 2)
                    for (year, month), amount in monthly_forecasts.items()
                },
                "confidence": 0.4,
                "explanation": f"Mimicking last {len(monthly_forecasts)} months of activity"
            }
            
    except Exception as e:
        logger.error(f"Error computing forecast: {str(e)}")
        return {
            "method": "manual",
            "frequency": "irregular",
            "payment_day": None,
            "forecast_amount": None,
            "confidence": 0.0,
            "explanation": f"Error in forecast computation: {str(e)}"
        }

def update_vendor_config(
    display_name: str,
    forecast: Dict[str, Any],
    client_id: str = None
) -> bool:
    """
    Update vendor configuration in database.
    
    Args:
        display_name: The display_name to update
        forecast: Forecast details from compute_forecast
        client_id: The client ID (if None, uses current client)
        
    Returns:
        bool: Success status
    """
    if client_id is None:
        client_id = get_current_client()
    
    try:
        # Update all vendors with this display_name
        update_data = {
            "forecast_method": forecast["method"],
            "forecast_frequency": forecast["frequency"],
            "forecast_day": forecast.get("payment_day"),
            "forecast_amount": forecast.get("forecast_amount"),
            "forecast_confidence": forecast["confidence"],
            "forecast_notes": forecast["explanation"]
        }
        
        if "monthly_forecasts" in forecast:
            update_data["forecast_notes"] += f"\nMonthly forecasts: {json.dumps(forecast['monthly_forecasts'])}"
            
        resp = supabase.table("vendors") \
            .update(update_data) \
            .eq("client_id", client_id) \
            .eq("display_name", display_name) \
            .execute()
            
        return len(resp.data) > 0
        
    except Exception as e:
        logger.error(f"Error updating vendor config for {display_name}: {str(e)}")
        return False

def spot_check_forecast(
    display_name: str,
    transactions: List[Dict[str, Any]],
    forecast: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Use AI to spot-check forecast for edge cases.
    
    Args:
        display_name: The display_name to check
        transactions: List of transactions
        forecast: Forecast details from compute_forecast
        
    Returns:
        Dict with spot-check results
    """
    try:
        # Format transaction history (limit to most recent 100 transactions)
        sorted_txns = sorted(transactions, key=lambda x: x['transaction_date'], reverse=True)[:100]
        tx_history = "\n".join([
            f"{tx['transaction_date']} - ${float(tx['amount']):.2f}"
            for tx in sorted_txns
        ])
        
        prompt = f"""Review this vendor's forecast for potential issues:

Vendor: {display_name}

Transaction History (most recent 100 transactions):
{tx_history}

Current Forecast:
{json.dumps(forecast, indent=2)}

Return a JSON object with:
{{
    "needs_review": boolean,
    "confidence": float (0-1),
    "issues": [string],
    "suggested_override": boolean,
    "explanation": string
}}"""

        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        
        return json.loads(response.choices[0].message.content)
        
    except Exception as e:
        logger.error(f"Error spot-checking forecast: {str(e)}")
        return {
            "needs_review": True,
            "confidence": 0.0,
            "issues": [f"Error during spot check: {str(e)}"],
            "suggested_override": False,
            "explanation": f"Error during spot check: {str(e)}"
        } 