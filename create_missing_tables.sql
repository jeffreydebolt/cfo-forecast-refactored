-- Missing tables for integrated onboarding system
-- These complement the existing 7 tables

-- Track onboarding progress for each client
CREATE TABLE IF NOT EXISTS onboarding_status (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(50) NOT NULL,
    step VARCHAR(50) NOT NULL,
    data JSONB,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(client_id, step)
);

-- Track forecast accuracy over time
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

-- Client-specific settings and preferences
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

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_onboarding_status_client ON onboarding_status(client_id);
CREATE INDEX IF NOT EXISTS idx_forecast_variances_client_date ON forecast_variances(client_id, forecast_date);
CREATE INDEX IF NOT EXISTS idx_client_settings_client ON client_settings(client_id);