# Hardcoded Client ID References

## Summary
Found 20 files with hardcoded client_id values, primarily using 'spyguy' and 'bestself'. This needs to be refactored to use the ClientContext system.

## Files with Hardcoded Client IDs

### Using 'spyguy':
1. `weekly_pivot_analysis.py:218` - client_id = 'spyguy'
2. `analyze_week_transactions.py:214` - client_id = 'spyguy'
3. `analyze_mercury_patterns.py:23` - client_id = 'spyguy' (with comment about transaction storage)
4. `check_bestself_transactions.py:11` - client_id = 'spyguy' (BestSelf data stored under spyguy)
5. `analyze_sge_patterns.py:12` - client_id = 'spyguy'
6. `analyze_july_week.py:21` - client_id = 'spyguy' (BestSelf data stored under spyguy)
7. `comprehensive_forecast_analysis.py:11` - client_id = 'spyguy'
8. `search_amazon_patterns.py:13` - client_id = 'spyguy'
9. `recent_trends_analysis.py:12` - client_id = 'spyguy'
10. `comprehensive_weekly_analysis.py:260` - client_id = 'spyguy'

### Using 'bestself':
1. `export_forecast_csv.py:134` - client_id = sys.argv[1] if len(sys.argv) > 1 else 'bestself'
2. `debug_import.py:12` - client_id = "bestself"
3. `debug_duplicates.py:68` - client_id = "bestself"
4. `setup_vendor_mapping.py:17` - client_id = 'bestself'
5. `run_calendar_forecast.py:21` - parser.add_argument('--client-id', default='bestself')

### Default Parameters with 'spyguy':
1. `variance_review.py:16` - def export_variance_review_with_raw(client_id="spyguy")
2. `setup_forecast_config.py:13` - def get_transactions_for_vendor(..., client_id="spyguy", ...)
3. `deduplicate_transactions.py:9` - def deduplicate_transactions(client_id='spyguy', ...)
4. `vendor_breakdown.py:10` - def show_vendor_breakdown(client_id='spyguy', ...)
5. `add_missing_vendors.py:9` - def add_missing_vendors(client_id='spyguy', ...)
6. `update_vendor_rules.py:16` - def update_vendor_rules(client_id="spyguy")

## Refactoring Strategy

### Phase 1: Import ClientContext
All files should import and use the client context:
```python
from config.client_context import get_current_client

# Replace hardcoded values with:
client_id = get_current_client()
```

### Phase 2: Update Function Signatures
For functions with default client_id parameters:
```python
# OLD:
def some_function(client_id='spyguy'):
    ...

# NEW:
def some_function(client_id=None):
    if client_id is None:
        client_id = get_current_client()
    ...
```

### Phase 3: Update CLI Scripts
For scripts that are meant to be run directly:
```python
# Add argument parser
import argparse
from config.client_context import get_current_client, set_current_client

parser = argparse.ArgumentParser()
parser.add_argument('--client', help='Client ID to use')
args = parser.parse_args()

if args.client:
    set_current_client(args.client)
client_id = get_current_client()
```

### Phase 4: Handle Special Cases
Some files mention that "BestSelf data is stored under spyguy". This suggests there might be data migration or mapping issues that need to be addressed separately.

## Priority Files to Fix
1. Core analysis scripts (analyze_*.py)
2. Setup and configuration scripts
3. Debug and utility scripts
4. Export and reporting scripts

## Notes
- The ClientContext system already exists and is working
- Need to ensure all scripts can accept client as parameter
- Consider adding validation to prevent hardcoded clients in future