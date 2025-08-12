-- Create pattern_reviews table to store review progress and decisions
CREATE TABLE IF NOT EXISTS pattern_reviews (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    client_id TEXT NOT NULL,
    vendor_group TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending', -- pending, reviewed, skipped
    pattern_type TEXT,
    interval_days INTEGER,
    average_amount NUMERIC,
    next_date DATE,
    confidence INTEGER,
    total_transaction_value NUMERIC,
    transaction_count INTEGER,
    reviewed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(client_id, vendor_group)
);

-- Create index for faster queries
CREATE INDEX idx_pattern_reviews_client_status ON pattern_reviews(client_id, status);
CREATE INDEX idx_pattern_reviews_client_value ON pattern_reviews(client_id, total_transaction_value DESC);