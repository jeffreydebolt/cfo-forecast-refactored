-- Cash Flow Forecast Database Schema
-- This schema supports the complete cash flow forecasting system

-- Forecast periods (weeks/months for display)
CREATE TABLE IF NOT EXISTS forecast_periods (
    id SERIAL PRIMARY KEY,
    client_id TEXT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    week_number INTEGER,
    period_type TEXT DEFAULT 'week', -- 'week' or 'month'
    is_locked BOOLEAN DEFAULT false, -- locked after reconciliation
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(client_id, start_date)
);

-- Vendor groups for forecasting (groups individual vendors)
CREATE TABLE IF NOT EXISTS vendor_groups (
    id SERIAL PRIMARY KEY,
    client_id TEXT NOT NULL,
    group_name TEXT NOT NULL,
    display_name TEXT NOT NULL,
    category TEXT, -- 'revenue', 'operating', 'financing'
    subcategory TEXT, -- 'core_capital', 'operating_revenue', 'cc', 'ops', 'ga', 'payroll', 'admin', 'distributions'
    is_inflow BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(client_id, group_name)
);

-- Vendor mappings to groups
CREATE TABLE IF NOT EXISTS vendor_group_mappings (
    id SERIAL PRIMARY KEY,
    client_id TEXT NOT NULL,
    vendor_name TEXT NOT NULL,
    vendor_group_id INTEGER REFERENCES vendor_groups(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(client_id, vendor_name)
);

-- Forecast rules for each vendor group
CREATE TABLE IF NOT EXISTS vendor_forecast_rules (
    id SERIAL PRIMARY KEY,
    client_id TEXT NOT NULL,
    vendor_group_id INTEGER REFERENCES vendor_groups(id) ON DELETE CASCADE,
    frequency TEXT NOT NULL, -- 'daily', 'weekly', 'bi-weekly', 'monthly', 'quarterly', 'irregular'
    timing_details JSONB, -- {'day_of_week': 'monday', 'days_of_month': [15, 30], etc.}
    amount_method TEXT DEFAULT 'weighted_average', -- 'weighted_average', 'manual', 'last_month_avg'
    base_amount DECIMAL(15,2),
    is_active BOOLEAN DEFAULT true,
    last_pattern_update TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(client_id, vendor_group_id)
);

-- Individual forecast records (one per date per vendor group)
CREATE TABLE IF NOT EXISTS forecast_records (
    id SERIAL PRIMARY KEY,
    client_id TEXT NOT NULL,
    forecast_date DATE NOT NULL,
    vendor_group_id INTEGER REFERENCES vendor_groups(id) ON DELETE CASCADE,
    forecasted_amount DECIMAL(15,2) NOT NULL,
    actual_amount DECIMAL(15,2), -- populated during reconciliation
    variance_amount DECIMAL(15,2), -- actual - forecasted
    pattern_type TEXT, -- 'daily', 'weekly', 'bi-weekly', etc.
    forecast_method TEXT DEFAULT 'system', -- 'system', 'manual'
    is_actual BOOLEAN DEFAULT false, -- true after reconciliation
    is_locked BOOLEAN DEFAULT false, -- locked after period reconciliation
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(client_id, forecast_date, vendor_group_id)
);

-- Beginning cash balances by period
CREATE TABLE IF NOT EXISTS cash_balances (
    id SERIAL PRIMARY KEY,
    client_id TEXT NOT NULL,
    balance_date DATE NOT NULL,
    beginning_balance DECIMAL(15,2) NOT NULL,
    ending_balance DECIMAL(15,2),
    is_actual BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(client_id, balance_date)
);

-- Reconciliation log
CREATE TABLE IF NOT EXISTS reconciliation_log (
    id SERIAL PRIMARY KEY,
    client_id TEXT NOT NULL,
    reconciliation_date DATE NOT NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    transactions_imported INTEGER DEFAULT 0,
    forecasts_updated INTEGER DEFAULT 0,
    variance_summary JSONB, -- summary stats
    performed_by TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_forecast_records_client_date ON forecast_records(client_id, forecast_date);
CREATE INDEX IF NOT EXISTS idx_forecast_records_vendor_group ON forecast_records(vendor_group_id);
CREATE INDEX IF NOT EXISTS idx_vendor_groups_client ON vendor_groups(client_id);
CREATE INDEX IF NOT EXISTS idx_vendor_mappings_client ON vendor_group_mappings(client_id);
CREATE INDEX IF NOT EXISTS idx_cash_balances_client_date ON cash_balances(client_id, balance_date);

-- Views for easier querying
CREATE OR REPLACE VIEW forecast_dashboard_view AS
SELECT 
    fr.client_id,
    fr.forecast_date,
    vg.group_name,
    vg.display_name,
    vg.category,
    vg.subcategory,
    vg.is_inflow,
    fr.forecasted_amount,
    fr.actual_amount,
    fr.variance_amount,
    fr.is_actual,
    fr.is_locked,
    fr.pattern_type,
    fr.forecast_method
FROM forecast_records fr
JOIN vendor_groups vg ON fr.vendor_group_id = vg.id
ORDER BY fr.forecast_date, vg.category, vg.subcategory;

-- Insert default categories for new clients
CREATE OR REPLACE FUNCTION create_default_vendor_groups(p_client_id TEXT) 
RETURNS void AS $$
BEGIN
    -- Revenue categories
    INSERT INTO vendor_groups (client_id, group_name, display_name, category, subcategory, is_inflow) VALUES
    (p_client_id, 'core_capital', 'Core Capital', 'revenue', 'core_capital', true),
    (p_client_id, 'operating_revenue', 'Operating Revenue', 'revenue', 'operating_revenue', true),
    
    -- Operating outflow categories  
    (p_client_id, 'cc_expenses', 'CC', 'operating', 'cc', false),
    (p_client_id, 'ops_expenses', 'Ops', 'operating', 'ops', false),
    (p_client_id, 'ga_expenses', 'G&A', 'operating', 'ga', false),
    (p_client_id, 'payroll_expenses', 'Payroll', 'operating', 'payroll', false),
    (p_client_id, 'admin_expenses', 'Admin', 'operating', 'admin', false),
    
    -- Financing categories
    (p_client_id, 'distributions', 'Distributions', 'financing', 'distributions', false),
    (p_client_id, 'equity_contributions', 'Equity Contrib.', 'financing', 'equity_contrib', true),
    (p_client_id, 'loan_proceeds', 'Loan Proceeds', 'financing', 'loan_proceeds', true),
    (p_client_id, 'loan_payments', 'Loan Payments', 'financing', 'loan_payments', false);
END;
$$ LANGUAGE plpgsql;