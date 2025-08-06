import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from supabase_client import supabase
from forecast.configure_forecast import classify_and_configure, LOOKBACK_DAYS
from datetime import datetime, timedelta, UTC

def run():
    # fetch all display names
    vendors = supabase.table('vendors') \
        .select('display_name,vendor_name') \
        .eq('client_id', 'spyguy') \
        .execute().data

    # Group vendor_names by display_name
    display_to_vendors = {}
    for v in vendors:
        display_to_vendors.setdefault(v['display_name'], []).append(v['vendor_name'])

    for display_name, vendor_names in display_to_vendors.items():
        print(f"\nProcessing {display_name}...")
        
        # fetch last LOOKBACK_DAYS of transactions for this display_name
        cutoff = (datetime.now(UTC) - timedelta(days=LOOKBACK_DAYS)).isoformat()
        txns = supabase.table('transactions') \
            .select('transaction_date,amount') \
            .eq('client_id', 'spyguy') \
            .in_('vendor_name', vendor_names) \
            .gte('transaction_date', cutoff) \
            .execute().data

        classify_and_configure(display_name, txns, supabase)

    print("\n✅ Forecast config complete for all display names.")

if __name__ == '__main__':
    run() 