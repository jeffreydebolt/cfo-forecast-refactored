"""
Create forecast_overrides table for manual forecast adjustments.
"""

from supabase_client import supabase
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_forecast_overrides_table():
    """Create the forecast_overrides table."""
    try:
        # Create table using raw SQL
        sql = """
        CREATE TABLE IF NOT EXISTS forecast_overrides (
            id BIGSERIAL PRIMARY KEY,
            client_id TEXT NOT NULL,
            vendor_display_name TEXT NOT NULL,
            override_date TIMESTAMP WITH TIME ZONE NOT NULL,
            original_amount DECIMAL(15,2) DEFAULT 0.00,
            override_amount DECIMAL(15,2) DEFAULT 0.00,
            override_type TEXT CHECK (override_type IN ('amount_change', 'date_shift', 'skip_occurrence', 'add_occurrence')) NOT NULL,
            new_date TIMESTAMP WITH TIME ZONE NULL,
            reason TEXT DEFAULT '',
            created_by TEXT DEFAULT 'system',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            
            -- Indexes for performance
            INDEX idx_forecast_overrides_client_date (client_id, override_date),
            INDEX idx_forecast_overrides_vendor (vendor_display_name),
            
            -- Constraints
            UNIQUE(client_id, vendor_display_name, override_date, override_type)
        );
        
        -- Add RLS policies
        ALTER TABLE forecast_overrides ENABLE ROW LEVEL SECURITY;
        
        -- Allow all operations (adjust based on your auth requirements)
        CREATE POLICY "Allow all operations on forecast_overrides" ON forecast_overrides
        FOR ALL USING (true) WITH CHECK (true);
        """
        
        result = supabase.rpc('exec_sql', {'sql': sql}).execute()
        logger.info("Created forecast_overrides table successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error creating forecast_overrides table: {e}")
        # Try simpler approach without advanced SQL features
        try:
            simple_sql = """
            CREATE TABLE IF NOT EXISTS forecast_overrides (
                id BIGSERIAL PRIMARY KEY,
                client_id TEXT NOT NULL,
                vendor_display_name TEXT NOT NULL,
                override_date TIMESTAMP WITH TIME ZONE NOT NULL,
                original_amount DECIMAL(15,2) DEFAULT 0.00,
                override_amount DECIMAL(15,2) DEFAULT 0.00,
                override_type TEXT NOT NULL,
                new_date TIMESTAMP WITH TIME ZONE NULL,
                reason TEXT DEFAULT '',
                created_by TEXT DEFAULT 'system',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """
            
            result = supabase.rpc('exec_sql', {'sql': simple_sql}).execute()
            logger.info("Created forecast_overrides table with simple schema")
            return True
            
        except Exception as e2:
            logger.error(f"Error with simple table creation: {e2}")
            return False

if __name__ == "__main__":
    success = create_forecast_overrides_table()
    if success:
        logger.info("✅ Forecast overrides table created successfully")
    else:
        logger.error("❌ Failed to create forecast overrides table")