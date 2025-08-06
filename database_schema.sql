-- Database Schema for Integrated Onboarding System
-- These tables store persistent data across onboarding and weekly updates

-- Vendor Mappings: Store user's grouping decisions
CREATE TABLE IF NOT EXISTS vendor_mappings (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(50) NOT NULL,
    group_name VARCHAR(100) NOT NULL,  -- e.g., "Amex Payments"
    vendor_name VARCHAR(100) NOT NULL,  -- e.g., "AMEX EPAYMENT"
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(client_id, vendor_name)  -- Each vendor can only belong to one group
);

-- Pattern Results: Store pattern detection outcomes
CREATE TABLE IF NOT EXISTS pattern_results (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(50) NOT NULL,
    vendor_group VARCHAR(100) NOT NULL,
    pattern_type VARCHAR(50),  -- weekly, bi_weekly, monthly, etc.
    frequency_days INTEGER,
    median_gap_days INTEGER,
    amount_variance DECIMAL(5,2),
    forecast_recommendation VARCHAR(20),  -- auto, manual_review, skip
    confidence VARCHAR(10),  -- high, medium, low
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(client_id, vendor_group)
);

-- Forecast Configurations: Store manual forecast setup
CREATE TABLE IF NOT EXISTS forecast_configs (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(50) NOT NULL,
    vendor_group VARCHAR(100) NOT NULL,
    forecast_frequency VARCHAR(20),  -- weekly, monthly, custom
    forecast_amount DECIMAL(10,2),
    custom_day_of_week INTEGER,  -- 0-6 for weekly patterns
    custom_day_of_month INTEGER,  -- 1-31 for monthly patterns
    is_active BOOLEAN DEFAULT TRUE,
    is_manual_override BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(client_id, vendor_group)
);

-- Onboarding Status: Track progress through onboarding
CREATE TABLE IF NOT EXISTS onboarding_status (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(50) NOT NULL,
    step VARCHAR(50) NOT NULL,  -- import_complete, grouping_complete, etc.
    data JSONB,  -- Step-specific data
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(client_id, step)
);

-- Forecast Variances: Track accuracy for continuous improvement
CREATE TABLE IF NOT EXISTS forecast_variances (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(50) NOT NULL,
    vendor_group VARCHAR(100) NOT NULL,
    forecast_date DATE NOT NULL,
    forecast_amount DECIMAL(10,2),
    actual_amount DECIMAL(10,2),
    variance_amount DECIMAL(10,2),
    variance_percentage DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Client Settings: Store client-specific preferences
CREATE TABLE IF NOT EXISTS client_settings (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(50) NOT NULL UNIQUE,
    beginning_cash_balance DECIMAL(10,2) DEFAULT 50000,
    low_cash_threshold DECIMAL(10,2) DEFAULT 20000,
    forecast_horizon_weeks INTEGER DEFAULT 13,
    auto_adjust_patterns BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_vendor_mappings_client ON vendor_mappings(client_id);
CREATE INDEX idx_pattern_results_client ON pattern_results(client_id);
CREATE INDEX idx_forecast_configs_client ON forecast_configs(client_id);
CREATE INDEX idx_forecast_variances_client_date ON forecast_variances(client_id, forecast_date);

-- Sample data to show structure
/*
-- Vendor Mappings Example
INSERT INTO vendor_mappings (client_id, group_name, vendor_name) VALUES
('spyguy', 'Amex Payments', 'AMEX EPAYMENT'),
('spyguy', 'Amex Payments', 'Amex'),
('spyguy', 'State Sales Tax', 'VA DEPT TAXATION'),
('spyguy', 'State Sales Tax', 'NC DEPT REVENUE');

-- Pattern Results Example
INSERT INTO pattern_results (client_id, vendor_group, pattern_type, frequency_days, forecast_recommendation, confidence) VALUES
('spyguy', 'Amex Payments', 'monthly', 30, 'auto', 'high'),
('spyguy', 'Stripe Revenue', 'daily', 1, 'manual_review', 'medium');

-- Forecast Config Example
INSERT INTO forecast_configs (client_id, vendor_group, forecast_frequency, forecast_amount, is_manual_override) VALUES
('spyguy', 'Gusto Payroll', 'bi_weekly', 5000.00, TRUE),
('spyguy', 'State Sales Tax', 'monthly', 1500.00, TRUE);
*/