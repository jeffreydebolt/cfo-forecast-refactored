import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import datetime
from collections import defaultdict
from supabase_client import supabase

def normalize_vendor_name(vendor_name: str) -> str:
    """Normalize vendor names to group related transactions."""
    if not vendor_name:
        return vendor_name
    
    # Convert to uppercase for consistent matching
    name = vendor_name.upper()
    
    # Credit card payments
    if any(s in name for s in ["AMEX", "CHASE", "CAPITAL ONE", "CREDIT CRD", "JPMORGAN"]):
        return "Credit Card Payments"
    
    # State tax payments
    if any(s in name for s in ["TAX", "TAXATION", "REVENUE", "DEPT", "SSTPTAX"]):
        return "State Tax Payments"
    
    # Internal transfers
    if any(s in name for s in ["TRANSFER", "TRNSFR", "MERCURY", "AUTO-TRANSFER"]):
        return "Internal Transfers"
    
    # Payment processors
    if any(s in name for s in ["STRIPE", "PAYPAL", "SHOPIFY", "AFRM", "SHOPPAYINST"]):
        return "Payment Processor Transfers"
    
    return vendor_name

def fetch_monthly_counts_by_display(client_id: str, months: int = 6):
    """
    Returns dict[display_name] = list of month-keys (YYYY-MM) in which at least one txn occurred.
    """
    today = datetime.date.today().replace(day=1)
    # start at beginning of month N months ago
    start_month = (today - datetime.timedelta(days=months*30)).replace(day=1)

    # First get vendor name to display name mapping
    resp = supabase.table("vendors") \
        .select("vendor_name, display_name") \
        .eq("client_id", client_id) \
        .execute()
    vendor_map = {v["vendor_name"]: v["display_name"] for v in resp.data}

    # pull transactions
    resp = supabase.table("transactions") \
        .select("transaction_date, amount, vendor_name") \
        .eq("client_id", client_id) \
        .gte("transaction_date", start_month.isoformat()) \
        .order("transaction_date") \
        .execute()
    records = resp.data

    # build month buckets
    counts = defaultdict(set)  # display_name -> set of "YYYY-MM"
    for tx in records:
        # First try to get display name from vendor map
        display = vendor_map.get(tx["vendor_name"])
        # If no display name, use normalized vendor name
        if not display:
            display = normalize_vendor_name(tx["vendor_name"])
        # If still no display name, use original vendor name
        if not display:
            display = tx["vendor_name"]
            
        month_key = tx["transaction_date"][:7]  # "2025-04"
        counts[display].add(month_key)

    # convert to sorted lists
    return {d: sorted(list(months)) for d, months in counts.items()}


def classify_display_pattern(display_name: str,
                             months_with_activity: list,
                             category: str) -> str:
    """
    Returns one of: "regular", "irregular", "manual"
    Rules:
      - if category contains "inventory" → manual
      - if tx in >= months months → regular
      - else irregular
    """
    # manual override for inventory
    if "inventory" in (category or "").lower():
        return "manual"
    # count months
    m = len(months_with_activity)
    # regular = at least one tx per month in last 4 months
    if m >= 4:
        return "regular"
    # irregular otherwise
    return "irregular"


def analyze_display_patterns(client_id: str):
    six_months = fetch_monthly_counts_by_display(client_id, months=6)
    # you'll need to fetch each display_name's category from vendors table
    resp = supabase.table("vendors") \
        .select("display_name, category") \
        .eq("client_id", client_id) \
        .execute()
    vendor_defs = {v["display_name"]: v["category"] for v in resp.data}

    results = {}
    for display, months in six_months.items():
        cat = vendor_defs.get(display, "")
        pattern = classify_display_pattern(display, months, cat)
        results[display] = {
            "months_active": months,
            "pattern": pattern
        }

    return results


if __name__ == "__main__":
    print("\nAnalyzing transaction patterns...")
    for d, info in analyze_display_patterns("spyguy").items():
        print(f"{d:30} | active in {len(info['months_active'])}/6 mo → {info['pattern']}") 