# CFO Forecast - Mercury Transaction Import

## Setup
1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables in `.env`:
```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

## CSV Import Process

### File Structure
Place Mercury CSV exports in the following structure:
```
Clients/
  └── ClientName/
      └── mercury_MMMYY.csv
```
Example: `Clients/Spyguy/mercury_apr22.csv`

### Running the Import
1. Update the `CLIENT_ID` and `CSV_PATH` variables in `import_mercury_csv.py`
2. Run the import:
```bash
python3 import_mercury_csv.py
```

### Features
- Imports transactions from Mercury CSV exports
- Skips duplicate transactions based on date, vendor, amount, and client
- Logs import progress and results
- Automatically categorizes transactions as Revenue/Expense based on amount
- Only imports completed transactions

### Verification
Check imported data in Supabase:
```sql
select * from transactions where client_id = 'client_name';
```

# CFO Forecast Supabase

## Getting Started

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables in `.env`:
```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

## Review & Update Vendor Mappings

The vendor mapping dashboard allows you to review and update vendor display names and categories.

1. Export current mappings:
```bash
python3 scripts/export_vendor_mappings.py
```
This creates a timestamped CSV file in the `data` directory.

2. Launch the review dashboard:
```bash
streamlit run dashboard/mapping_review.py
```

The dashboard provides:
- Filtering by category and review status
- Inline editing of display names and categories
- Automatic saving of changes
- Logging of all operations

## Debugging

All operations are logged with timestamps. Check the console output for:
- Export/import operations
- Supabase updates
- Error messages

## Data Structure

The vendor mappings include:
- `vendor_name`: Original name from transactions
- `display_name`: Friendly name for display
- `category`: Transaction category
- `review_needed`: Flag for manual review
- `group_locked`: Prevent automatic grouping 