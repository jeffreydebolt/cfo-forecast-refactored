import openai
import json
import logging
from typing import List, Dict, Any
import os
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_transaction_patterns(txns: List[Dict[str, Any]]) -> str:
    """
    Create a summary of transaction patterns for OpenAI analysis.
    """
    if not txns:
        return "No transactions available"
        
    # Sort transactions by date
    sorted_txns = sorted(txns, key=lambda x: x['date'])
    
    # Calculate basic statistics
    total_amount = sum(tx['amount'] for tx in txns)
    avg_amount = total_amount / len(txns)
    
    # Format transaction history with more context
    history = "\n".join([
        f"{tx['date']} - ${tx['amount']:.2f} " + 
        f"({'credit' if tx['amount'] > 0 else 'debit'})"
        for tx in sorted_txns
    ])
    
    summary = f"""
Transaction Summary:
- Total transactions: {len(txns)}
- Date range: {sorted_txns[0]['date']} to {sorted_txns[-1]['date']}
- Average amount: ${abs(avg_amount):.2f}
- Net flow: ${total_amount:.2f}

Detailed History:
{history}
"""
    return summary

def ask_openai_for_forecast_metadata(vendor_name, txns):
    """
    Use OpenAI to analyze transaction patterns and suggest forecast parameters.
    """
    if not txns:
        return {
            "forecast_method": "Manual",
            "frequency": "irregular",
            "notes": "No transactions available for analysis"
        }
        
    # Format transactions for analysis
    txn_data = []
    for tx in txns:
        txn_data.append({
            "date": tx["date"],
            "amount": float(tx["amount"])
        })
    
    # Create prompt
    prompt = f"""Analyze these transactions for vendor '{vendor_name}':
{json.dumps(txn_data, indent=2)}

Determine:
1. Best forecasting method (Fixed, Trailing30Avg, Trailing90Avg, or Manual)
2. Payment frequency (weekly, monthly, irregular)
3. Brief explanation of the pattern

Respond in JSON format with these keys:
- forecast_method
- frequency
- notes
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a financial analysis assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        
        result = json.loads(response.choices[0].message.content)
        return result
        
    except Exception as e:
        return {
            "forecast_method": "Manual",
            "frequency": "irregular",
            "notes": f"Error during AI analysis: {str(e)}"
        }

def suggest_transaction_aliases(vendor_name, known_vendor_names):
    """
    Use OpenAI to suggest which vendor names in the transactions table belong to the same company.
    
    Args:
        vendor_name: The vendor name to match against
        known_vendor_names: List of vendor names from transactions table
        
    Returns:
        List of matching vendor names
    """
    try:
        prompt = f"""
        A CFO assistant is trying to determine which of the following vendor names in the transactions table belong to the same company as "{vendor_name}".

        Return a list of matching vendor names (exact strings).

        Vendor options:
        {json.dumps(known_vendor_names, indent=2)}
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        
        matches = json.loads(response['choices'][0]['message']['content'])
        logger.info(f"Found {len(matches)} potential matches for {vendor_name}")
        return matches
        
    except Exception as e:
        logger.error(f"Error suggesting aliases for {vendor_name}: {str(e)}")
        return [] 