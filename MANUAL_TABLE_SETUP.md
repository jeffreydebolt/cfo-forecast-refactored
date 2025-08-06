# Manual Table Setup Instructions

Since we can't execute DDL directly through the Supabase client, you need to create these tables manually in your Supabase dashboard.

## Step 1: Go to Supabase Dashboard
1. Open your Supabase project dashboard
2. Go to **SQL Editor** (or **Table Editor**)

## Step 2: Create vendor_groups table

```sql
CREATE TABLE vendor_groups (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(255) NOT NULL,
    group_name VARCHAR(255) NOT NULL,
    vendor_display_names TEXT[] NOT NULL,
    pattern_frequency VARCHAR(20),
    pattern_days TEXT,
    pattern_confidence DECIMAL(5,4) DEFAULT 0.0,
    forecast_method VARCHAR(20) DEFAULT 'weighted_average',
    is_active BOOLEAN DEFAULT true,
    last_analyzed DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(client_id, group_name)
);
```

## Step 3: Test the vendor_groups table

Once created, test it with:

```bash
python3 lean_forecasting/vendor_groups.py bestself create_samples
```

## Step 4: Create remaining tables (if needed)

If the vendor_groups table works, you can create the others:

```sql
-- forecasts table
CREATE TABLE forecasts (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(255) NOT NULL,
    vendor_group_name VARCHAR(255) NOT NULL,
    forecast_date DATE NOT NULL,
    forecast_amount DECIMAL(15,2) NOT NULL,
    forecast_type VARCHAR(20) NOT NULL,
    forecast_method VARCHAR(20) NOT NULL,
    actual_amount DECIMAL(15,2),
    variance DECIMAL(15,2),
    is_locked BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(client_id, vendor_group_name, forecast_date)
);

-- pattern_analysis table  
CREATE TABLE pattern_analysis (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(255) NOT NULL,
    vendor_group_name VARCHAR(255) NOT NULL,
    analysis_date DATE NOT NULL,
    frequency_detected VARCHAR(20),
    specific_days TEXT,
    confidence_score DECIMAL(5,4),
    sample_size INTEGER,
    date_range_start DATE,
    date_range_end DATE,
    transactions_analyzed INTEGER,
    average_amount DECIMAL(15,2),
    explanation TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- actuals_import table
CREATE TABLE actuals_import (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(255) NOT NULL,
    import_date DATE NOT NULL,
    week_start_date DATE NOT NULL,
    week_end_date DATE NOT NULL,
    transactions_imported INTEGER,
    forecasts_updated INTEGER,
    new_patterns_detected INTEGER,
    status VARCHAR(20) DEFAULT 'completed',
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(client_id, week_start_date)
);
```

## Step 5: Create indexes (optional but recommended)

```sql
CREATE INDEX idx_vendor_groups_client ON vendor_groups(client_id);
CREATE INDEX idx_forecasts_client_date ON forecasts(client_id, forecast_date);
CREATE INDEX idx_forecasts_group_date ON forecasts(vendor_group_name, forecast_date);
```

## Step 6: Test everything

```bash
python3 lean_forecasting/vendor_groups.py bestself status
```