# File Structure Refactoring Plan

## Current Issues
- 60+ Python files in root directory
- No clear module organization
- Difficult to understand project structure
- Mix of utility scripts, analysis scripts, and core functionality

## Proposed Structure

```
cfo_forecast_refactored/
├── src/                      # Core application code
│   ├── __init__.py
│   ├── api/                  # API layer (future FastAPI)
│   │   ├── __init__.py
│   │   └── endpoints/
│   ├── core/                 # Core business logic (already exists)
│   │   ├── __init__.py
│   │   ├── calendar_forecasting.py
│   │   ├── forecast_overrides.py
│   │   ├── group_pattern_detection.py
│   │   ├── pattern_detection.py
│   │   └── vendor_auto_mapping.py
│   ├── models/               # Data models (already exists)
│   │   └── __init__.py
│   ├── services/             # Business services (already exists)
│   │   ├── __init__.py
│   │   ├── forecast_service.py
│   │   └── transaction_service.py
│   ├── importers/            # CSV importers (already exists)
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── factory.py
│   │   └── [bank-specific importers]
│   ├── database/             # Database layer
│   │   ├── __init__.py
│   │   ├── supabase_client.py
│   │   └── migrations/
│   ├── ai/                   # AI/ML functionality
│   │   ├── __init__.py
│   │   ├── openai_client.py
│   │   └── vendor_classification.py
│   ├── utils/                # Utilities (already exists)
│   │   ├── __init__.py
│   │   └── progress_tracker.py
│   └── config/               # Configuration (already exists)
│       ├── __init__.py
│       └── client_context.py
├── scripts/                  # One-off scripts and analysis
│   ├── analysis/             # Analysis scripts
│   │   ├── analyze_all_clients.py
│   │   ├── analyze_july_week.py
│   │   ├── analyze_mercury_patterns.py
│   │   └── [other analysis scripts]
│   ├── setup/                # Setup and configuration scripts
│   │   ├── setup_by_display.py
│   │   ├── setup_forecast_config.py
│   │   └── [other setup scripts]
│   ├── debug/                # Debug and troubleshooting scripts
│   │   ├── debug_bestself_forecast.py
│   │   ├── debug_duplicates.py
│   │   └── [other debug scripts]
│   └── migration/            # Data migration scripts
│       ├── deduplicate_transactions.py
│       └── [other migration scripts]
├── web/                      # Web interface
│   ├── streamlit/            # Streamlit dashboards
│   │   ├── mapping_review.py
│   │   └── run_dashboard.py
│   └── static/               # Static files (HTML prototypes)
│       ├── prototype_dashboard.html
│       ├── prototype_import.html
│       └── prototype_weekly_view.html
├── tests/                    # Test suite
│   ├── __init__.py
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── docs/                     # Documentation (already exists)
├── sample_data/              # Sample data (already exists)
├── main.py                   # CLI entry point
├── requirements.txt          # Dependencies
├── .env.example              # Environment template
└── README.md                 # Project documentation
```

## Migration Steps

### Phase 1: Create Directory Structure
1. Create src/ directory and subdirectories
2. Create scripts/ directory and subdirectories
3. Create web/ directory and subdirectories
4. Create tests/ directory structure

### Phase 2: Move Core Components (Priority)
1. Move supabase_client.py → src/database/
2. Move openai_client.py → src/ai/
3. Move vendor-related logic → src/core/vendors/
4. Update all imports

### Phase 3: Move Scripts
1. Categorize all remaining .py files
2. Move analysis scripts → scripts/analysis/
3. Move setup scripts → scripts/setup/
4. Move debug scripts → scripts/debug/

### Phase 4: Update Imports
1. Update all import statements
2. Add proper __init__.py files
3. Test all functionality

### Phase 5: Clean Up
1. Remove any remaining files from root
2. Update documentation
3. Update main.py CLI commands

## Benefits
- Clear separation of concerns
- Easier to navigate codebase
- Better testability
- Cleaner root directory
- Logical grouping of functionality