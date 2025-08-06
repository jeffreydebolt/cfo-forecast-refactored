# Development Setup Guide

## Prerequisites

### Required Software
- Python 3.8 or higher
- pip (Python package manager)
- Git
- A Supabase account
- An OpenAI API account

### Recommended Software
- pyenv (for Python version management)
- virtualenv or venv
- VS Code or PyCharm
- PostgreSQL client (for direct database access)

## Initial Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd cfo_forecast_refactored
```

### 2. Set Up Python Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip
```

### 3. Install Dependencies
```bash
# Install all requirements
pip install -r requirements.txt

# If requirements.txt doesn't exist, install manually:
pip install streamlit pandas numpy scikit-learn supabase openai python-dotenv
```

### 4. Environment Configuration
```bash
# Create .env file from example
cp .env.example .env

# Edit .env with your credentials
```

Your `.env` file should contain:
```
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# OpenAI Configuration
OPENAI_API_KEY=sk-your-api-key

# Application Configuration
DEFAULT_CLIENT_ID=spyguy
LOG_LEVEL=INFO
```

### 5. Database Setup

#### Option A: Using Existing Supabase Project
1. Get your Supabase URL and anon key from project settings
2. Add them to your `.env` file
3. Ensure you have the required tables (see Database Schema below)

#### Option B: Creating New Supabase Project
1. Create new project at https://supabase.com
2. Run the SQL migrations in `migrations/` directory (if available)
3. Or create tables manually using the schema below

### 6. Verify Setup
```bash
# Test Supabase connection
python -c "from supabase_client import supabase; print('Connected!' if supabase else 'Failed!')"

# Test OpenAI connection
python -c "from openai_client import openai_client; print('Connected!' if openai_client else 'Failed!')"
```

## Database Schema

### Required Tables

```sql
-- Clients table
CREATE TABLE clients (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Vendors table
CREATE TABLE vendors (
    id SERIAL PRIMARY KEY,
    client_id TEXT REFERENCES clients(id),
    vendor_name TEXT NOT NULL,
    display_name TEXT,
    category TEXT,
    vendor_group TEXT,
    group_locked BOOLEAN DEFAULT FALSE,
    review_needed BOOLEAN DEFAULT FALSE,
    forecast_method TEXT,
    forecast_frequency TEXT,
    forecast_day TEXT,
    forecast_amount DECIMAL(10,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Transactions table
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    client_id TEXT REFERENCES clients(id),
    transaction_date DATE NOT NULL,
    vendor_name TEXT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    description TEXT,
    category TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Forecasts table
CREATE TABLE forecasts (
    id SERIAL PRIMARY KEY,
    client_id TEXT REFERENCES clients(id),
    forecast_date DATE NOT NULL,
    vendor_name TEXT,
    amount DECIMAL(10,2),
    forecast_method TEXT,
    confidence_score DECIMAL(3,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_vendors_client_display ON vendors(client_id, display_name);
CREATE INDEX idx_transactions_client_date ON transactions(client_id, transaction_date);
CREATE INDEX idx_transactions_vendor ON transactions(client_id, vendor_name);
```

## Running the Application

### 1. Import Mercury CSV Data
```bash
# Update the file path and client_id in import_mercury_csv.py
python import_mercury_csv.py
```

### 2. Run AI Vendor Grouping
```bash
python ai_group_vendors.py
```

### 3. Generate Forecasts
```bash
python run_forecast.py
```

### 4. Launch Dashboard
```bash
# For vendor mapping review
streamlit run mapping_review.py

# Or use the launcher
python run_dashboard.py
```

## Development Workflow

### 1. Before Starting Work
```bash
# Activate virtual environment
source venv/bin/activate

# Pull latest changes
git pull origin main

# Check documentation for context
python main.py --context
```

### 2. During Development
```bash
# Add todos for your tasks
python main.py --add-todo "Implement new feature"

# Update progress regularly
python utils/progress_tracker.py update "Completed vendor grouping optimization"

# Check current status
python main.py --status
```

### 3. Before Committing
```bash
# Create snapshot of current state
python main.py --snapshot

# Run any tests (when implemented)
pytest

# Update documentation
# Manually update relevant files in docs/
```

## Troubleshooting

### Common Issues

#### 1. Supabase Connection Errors
```
Error: Invalid API key
```
**Solution**: Check your SUPABASE_KEY in .env file

#### 2. OpenAI Rate Limits
```
Error: Rate limit exceeded
```
**Solution**: Wait and retry, or implement caching

#### 3. Module Import Errors
```
Error: No module named 'supabase_client'
```
**Solution**: Ensure you're in the project root directory

#### 4. Streamlit Port Already in Use
```
Error: Port 8501 is already in use
```
**Solution**: Kill the process or use different port:
```bash
streamlit run app.py --server.port 8502
```

### Debug Mode
Enable detailed logging by setting in .env:
```
LOG_LEVEL=DEBUG
```

## IDE Configuration

### VS Code
Recommended extensions:
- Python
- Pylance
- Python Docstring Generator
- GitLens

Settings.json:
```json
{
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "editor.formatOnSave": true
}
```

### PyCharm
1. Set project interpreter to your virtual environment
2. Mark project root as Sources Root
3. Enable code inspections

## Additional Resources

- [Supabase Documentation](https://supabase.com/docs)
- [Streamlit Documentation](https://docs.streamlit.io)
- [OpenAI API Reference](https://platform.openai.com/docs)
- [Project Repository Wiki](https://github.com/your-repo/wiki)

## Support

For issues or questions:
1. Check ISSUES.md for known problems
2. Review logs in the console
3. Create detailed bug report with reproduction steps