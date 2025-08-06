-- Create Forecast Database Tables
-- Execute these in Supabase SQL Editor

-- 1. vendor_groups table - stores vendor group definitions and patterns
CREATE TABLE IF NOT EXISTS vendor_groups (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(255) NOT NULL,
    group_name VARCHAR(255) NOT NULL,
    vendor_display_names TEXT[] NOT NULL,
    pattern_frequency VARCHAR(20),
    pattern_timing VARCHAR(50),
    pattern_confidence DECIMAL(5,4) DEFAULT 0.0,
    forecast_method VARCHAR(20) DEFAULT 'weighted_average',
    weighted_average_amount DECIMAL(15,2) DEFAULT 0.0,
    is_active BOOLEAN DEFAULT true,
    last_analyzed DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(client_id, group_name)
);

-- 2. forecasts table - stores individual forecast records for each date
CREATE TABLE IF NOT EXISTS forecasts (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(255) NOT NULL,
    vendor_group_name VARCHAR(255) NOT NULL,
    forecast_date DATE NOT NULL,
    forecast_amount DECIMAL(15,2) NOT NULL,
    forecast_type VARCHAR(20) NOT NULL, -- daily, weekly, bi-weekly, monthly
    forecast_method VARCHAR(20) NOT NULL, -- weighted_average, manual
    pattern_confidence DECIMAL(5,4) DEFAULT 0.0,
    actual_amount DECIMAL(15,2),
    variance DECIMAL(15,2),
    is_locked BOOLEAN DEFAULT false,
    is_manual_override BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(client_id, vendor_group_name, forecast_date)
);

-- 3. pattern_analysis table - audit trail of pattern detection
CREATE TABLE IF NOT EXISTS pattern_analysis (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(255) NOT NULL,
    vendor_group_name VARCHAR(255) NOT NULL,
    analysis_date DATE NOT NULL,
    frequency_detected VARCHAR(20),
    timing_detected VARCHAR(50),
    confidence_score DECIMAL(5,4),
    sample_size INTEGER,
    date_range_start DATE,
    date_range_end DATE,
    transactions_analyzed INTEGER,
    average_amount DECIMAL(15,2),
    explanation TEXT,
    large_transaction_count INTEGER DEFAULT 0,
    analysis_method VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 4. actuals_import table - tracks weekly actual imports for reconciliation
CREATE TABLE IF NOT EXISTS actuals_import (
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

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_vendor_groups_client ON vendor_groups(client_id);
CREATE INDEX IF NOT EXISTS idx_vendor_groups_active ON vendor_groups(client_id, is_active);

CREATE INDEX IF NOT EXISTS idx_forecasts_client_date ON forecasts(client_id, forecast_date);
CREATE INDEX IF NOT EXISTS idx_forecasts_group_date ON forecasts(vendor_group_name, forecast_date);
CREATE INDEX IF NOT EXISTS idx_forecasts_client_group ON forecasts(client_id, vendor_group_name);

CREATE INDEX IF NOT EXISTS idx_pattern_analysis_client ON pattern_analysis(client_id);
CREATE INDEX IF NOT EXISTS idx_pattern_analysis_group ON pattern_analysis(vendor_group_name);

CREATE INDEX IF NOT EXISTS idx_actuals_import_client ON actuals_import(client_id);
CREATE INDEX IF NOT EXISTS idx_actuals_import_week ON actuals_import(week_start_date);

-- Add some helpful comments
COMMENT ON TABLE vendor_groups IS 'Stores vendor group definitions and detected patterns';
COMMENT ON TABLE forecasts IS 'Individual forecast records for each date and vendor group';
COMMENT ON TABLE pattern_analysis IS 'Audit trail of pattern detection analysis';
COMMENT ON TABLE actuals_import IS 'Tracks weekly reconciliation imports';

COMMENT ON COLUMN vendor_groups.vendor_display_names IS 'Array of display names included in this group';
COMMENT ON COLUMN vendor_groups.pattern_frequency IS 'daily, weekly, bi-weekly, monthly, etc.';
COMMENT ON COLUMN vendor_groups.pattern_timing IS 'Mondays, Tuesdays, weekdays, etc.';

COMMENT ON COLUMN forecasts.forecast_type IS 'The pattern frequency used for this forecast';
COMMENT ON COLUMN forecasts.is_manual_override IS 'True if user manually set this forecast amount';
COMMENT ON COLUMN forecasts.variance IS 'Actual amount - forecast amount (populated after reconciliation)';