# CFO Forecast Tool - Context for Claude

## Project Overview
This is a CFO cash flow forecasting tool that helps predict future revenue and expenses based on historical transaction patterns.

## Critical Forecasting Logic
**READ FORECASTING_LOGIC_CORE_REQUIREMENTS.md FIRST** - This contains the definitive specification for how forecasting works.

Key points:
1. **Vendor Grouping First** - normalize and group vendors before any analysis
2. **Pattern Detection on Groups** - detect frequency (daily/weekly/bi-weekly/etc.) and timing (Mondays, 15th/30th, etc.)
3. **Individual Date Records** - generate forecast records for each specific date, not aggregated
4. **Group-Level Forecasting** - forecast vendor groups, not individual vendors

Example: Amazon deposits bi-weekly on Mondays at ~$42k per deposit.

## Current Architecture
- **Supabase Backend** - PostgreSQL database with transactions, vendors, forecasts tables
- **Python Services** - pattern detection, forecasting logic, data processing
- **Vendor Mapping** - vendors table maps raw vendor names to display names for grouping

## Key Files
- `FORECASTING_LOGIC_CORE_REQUIREMENTS.md` - Core forecasting specification
- `lean_forecasting/` - New lean forecasting implementation
- `services/forecast_service.py` - Main forecasting service
- `core/pattern_detection.py` - Pattern analysis logic

## Development Guidelines
- Always follow the forecasting logic specification
- Pattern detection must work on vendor groups, not individual vendors
- Generate individual date records for forecasts
- Use the existing vendor mapping system for grouping