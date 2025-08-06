import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from datetime import datetime, timedelta, UTC
from collections import Counter
from supabase_client import supabase

# ─── CONFIG ─────────────────────────────────────────────────────────────
LOOKBACK = 180                # days
MIN_MONTHLY = 6               # months of activity → "monthly"
# ────────────────────────────────────────────────────────────────────────

def parse_date(date_str):
    """Parse date string to UTC datetime."""
    dt = datetime.fromisoformat(date_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt

# 1) Load mapping vendor_name → display_name once
mapping = supabase.table("vendors") \
    .select("vendor_name,display_name") \
    .eq("client_id", "spyguy") \
    .execute().data

vendor_to_display = {}
for r in mapping:
    vendor_to_display.setdefault(r["display_name"], []).append(r["vendor_name"])

# 2) For each display_name:
for display, raw_names in vendor_to_display.items():
    print(f"Processing {display}...")
    
    # 2a) pull txns in last LOOKBACK days for any of the raw_names
    cutoff = (datetime.now(UTC) - timedelta(days=LOOKBACK)).isoformat()
    txns = supabase.table("transactions") \
        .select("transaction_date,amount") \
        .eq("client_id", "spyguy") \
        .in_("vendor_name", raw_names) \
        .gte("transaction_date", cutoff) \
        .execute().data

    if not txns:
        print(f"  No transactions found")
        continue

    # 2b) group by year-month
    months = set((parse_date(t["transaction_date"]).year,
                  parse_date(t["transaction_date"]).month)
                 for t in txns)

    # 2c) decide frequency and day
    if len(months) >= MIN_MONTHLY:
        freq = "monthly"
        # most common day of month (integer)
        day = Counter(parse_date(t["transaction_date"]).day for t in txns) \
                  .most_common(1)[0][0]
    elif len(txns) >= 4:
        freq = "weekly"
        # most common weekday number (1=Monday, 7=Sunday)
        day = Counter(parse_date(t["transaction_date"]).isoweekday() for t in txns) \
                  .most_common(1)[0][0]
    else:
        freq = "irregular"
        day = None

    # 2d) 90-day trailing average
    avg_amt = 0
    recent_cut = datetime.now(UTC) - timedelta(days=90)
    recent = [t["amount"] for t in txns
              if parse_date(t["transaction_date"]) >= recent_cut]
    if recent:
        avg_amt = round(sum(recent)/len(recent), 2)

    print(f"  Frequency: {freq}, Day: {day}, Avg Amount: {avg_amt}")
    print(f"  Months active: {len(months)}, Total transactions: {len(txns)}")

    # 3) write it back
    supabase.table("vendors") \
      .update({
          "forecast_frequency": freq,
          "forecast_day": day,
          "forecast_amount": avg_amt
      }) \
      .eq("display_name", display) \
      .eq("client_id", "spyguy") \
      .execute()

print("\nDone: forecast config updated for", len(vendor_to_display), "display_names.") 