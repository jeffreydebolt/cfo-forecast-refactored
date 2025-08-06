# Project Context

## Overview
The CFO Forecast Tool is an AI-powered financial forecasting system that automates cash flow projections for small businesses. It transforms manual spreadsheet-based forecasting into an automated system using pattern recognition and machine learning.

## Current State
- **Phase**: Initial Refactoring
- **Last Updated**: 2025-01-29
- **Active Client**: spyguy (hardcoded)
- **Data Source**: Mercury CSV exports only

## Architecture

### Core Components
1. **Data Import Layer**
   - `import_mercury_csv.py`: Handles Mercury bank CSV imports
   - Transaction deduplication logic
   - Data validation and normalization

2. **AI/ML Layer**
   - `ai_group_vendors.py`: OpenAI embeddings for vendor clustering
   - `openai_infer.py`: Vendor name normalization using GPT-4
   - Pattern detection algorithms

3. **Forecasting Engine**
   - `vendor_forecast.py`: Core forecasting logic
   - `run_forecast.py`: Main forecasting pipeline
   - Multiple forecasting methods (regular, irregular, manual)

4. **UI Layer**
   - `mapping_review.py`: Streamlit dashboard for vendor management
   - `forecast_overview.py`: Forecast visualization dashboard
   - `variance_review.py`: Variance analysis interface

5. **Data Layer**
   - Supabase (PostgreSQL) backend
   - Tables: clients, transactions, vendors, forecasts

### Tech Stack
- **Backend**: Python 3.8+
- **Database**: Supabase (PostgreSQL)
- **AI/ML**: OpenAI API (GPT-4, embeddings)
- **UI**: Streamlit
- **Data Processing**: Pandas, NumPy, scikit-learn

## Key Business Logic

### Vendor Classification
- **Regular**: Consistent frequency (weekly, bi-weekly, monthly)
- **Quasi-Regular**: Somewhat predictable patterns
- **Irregular**: No clear pattern, requires manual forecasting

### Forecasting Methods
1. **Pattern-Based**: For regular vendors with clear frequencies
2. **Average-Based**: For irregular vendors using historical averages
3. **Manual Override**: For special cases or known future changes

### Confidence Scoring
- Based on transaction history consistency
- Pattern detection accuracy
- Number of historical data points

## Current Limitations
1. Single client hardcoded ("spyguy")
2. Only Mercury CSV imports supported
3. No credit card integration
4. No inventory planning integration
5. Sequential processing (no parallelization)
6. No caching layer

## Maintenance Instructions
Update this file when:
- Major architectural decisions are made
- New components are added
- Business logic changes
- Integration points change
- Key limitations are addressed