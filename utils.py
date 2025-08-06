from datetime import datetime, timedelta

def get_trailing_average(txns, days=90):
    """Calculate trailing average of transaction amounts over specified days."""
    if not txns:
        return 0
        
    cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
    recent_txns = [tx for tx in txns if tx['date'] >= cutoff_date]
    
    if not recent_txns:
        return 0
        
    return sum(float(tx['amount']) for tx in recent_txns) / len(recent_txns) 