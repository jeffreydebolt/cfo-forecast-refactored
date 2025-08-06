# CFO Forecast Refactor Blueprint

## Executive Summary

This blueprint outlines a comprehensive refactoring strategy for the CFO Forecast system that preserves your existing forecast logic and OpenAI integration while enhancing the architecture for multi-client support, scalability, and automation. The refactored system will maintain your current forecasting approach while making it more maintainable, extensible, and capable of handling multiple clients efficiently.

## Current Architecture Analysis

Based on the analysis of your codebase, the current system has several strengths:

1. **Sophisticated Forecasting Logic**: Your custom approach to vendor classification, pattern detection, and forecast generation is well-designed and effective.

2. **Intelligent OpenAI Integration**: You've effectively leveraged OpenAI for vendor normalization, pattern analysis, and forecast validation.

3. **Modular Components**: The system is already somewhat modular with separate scripts for different functions.

However, there are opportunities for improvement:

1. **Multi-Client Architecture**: The current system is primarily designed for a single client ("spyguy") with hardcoded references.

2. **Code Duplication**: Similar logic appears in multiple files.

3. **Configuration Management**: Configuration is scattered across files rather than centralized.

4. **Error Handling**: Error handling is inconsistent across modules.

## Refactoring Strategy

The refactoring will follow these guiding principles:

1. **Preserve Core Logic**: Maintain your existing forecast algorithms and OpenAI integration.
2. **Enhance Modularity**: Reorganize code into clear, reusable modules.
3. **Enable Multi-Client Support**: Redesign for efficient handling of multiple clients.
4. **Improve Maintainability**: Standardize patterns and reduce duplication.
5. **Enhance Automation**: Add capabilities for batch processing and scheduled runs.

## Proposed Architecture

### 1. Directory Structure

```
cfo_forecast/
├── core/                       # Core business logic
│   ├── __init__.py
│   ├── forecasting.py          # Forecasting algorithms
│   ├── classification.py       # Vendor classification
│   ├── pattern_detection.py    # Transaction pattern detection
│   └── validation.py           # Forecast validation
├── integrations/               # External integrations
│   ├── __init__.py
│   ├── openai_client.py        # OpenAI integration
│   ├── supabase_client.py      # Supabase integration
│   └── mercury_import.py       # Mercury CSV import
├── data/                       # Data access layer
│   ├── __init__.py
│   ├── repositories/           # Repository pattern implementations
│   │   ├── __init__.py
│   │   ├── transaction_repo.py # Transaction data access
│   │   ├── vendor_repo.py      # Vendor data access
│   │   ├── forecast_repo.py    # Forecast data access
│   │   └── client_repo.py      # Client data access
│   └── models/                 # Data models
│       ├── __init__.py
│       ├── transaction.py      # Transaction model
│       ├── vendor.py           # Vendor model
│       ├── forecast.py         # Forecast model
│       └── client.py           # Client model
├── services/                   # Business services
│   ├── __init__.py
│   ├── vendor_service.py       # Vendor management
│   ├── transaction_service.py  # Transaction management
│   ├── forecast_service.py     # Forecast generation
│   └── client_service.py       # Client management
├── ui/                         # User interfaces
│   ├── __init__.py
│   ├── dashboards/             # Streamlit dashboards
│   │   ├── __init__.py
│   │   ├── forecast_overview.py # Main forecast dashboard
│   │   ├── vendor_mapping.py   # Vendor mapping dashboard
│   │   └── variance_review.py  # Variance review dashboard
│   └── reports/                # Report generation
│       ├── __init__.py
│       ├── excel_export.py     # Excel report generation
│       └── pdf_export.py       # PDF report generation
├── utils/                      # Utility functions
│   ├── __init__.py
│   ├── logging.py              # Logging utilities
│   ├── config.py               # Configuration management
│   └── date_utils.py           # Date manipulation utilities
├── scripts/                    # Command-line scripts
│   ├── __init__.py
│   ├── import_transactions.py  # Import transactions
│   ├── run_forecast.py         # Run forecast pipeline
│   ├── setup_client.py         # Set up new client
│   └── batch_process.py        # Process multiple clients
└── tests/                      # Unit and integration tests
    ├── __init__.py
    ├── unit/                   # Unit tests
    └── integration/            # Integration tests
```

### 2. Core Modules

#### A. Data Models

```python
# cfo_forecast/data/models/client.py
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class Client:
    id: str
    name: str
    active: bool = True
    config: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Client':
        return cls(
            id=data['client_id'],
            name=data['client_name'],
            active=data.get('active', True),
            config=data.get('config', {})
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'client_id': self.id,
            'client_name': self.name,
            'active': self.active,
            'config': self.config or {}
        }
```

```python
# cfo_forecast/data/models/vendor.py
from dataclasses import dataclass
from typing import Optional, Dict, Any, List

@dataclass
class Vendor:
    id: str
    client_id: str
    vendor_name: str
    display_name: Optional[str] = None
    category: Optional[str] = None
    forecast_method: str = "manual"
    forecast_frequency: str = "irregular"
    forecast_day: Optional[int] = None
    forecast_amount: Optional[float] = None
    forecast_confidence: float = 0.0
    group_locked: bool = False
    review_needed: bool = False
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Vendor':
        return cls(
            id=data.get('id', ''),
            client_id=data['client_id'],
            vendor_name=data['vendor_name'],
            display_name=data.get('display_name'),
            category=data.get('category'),
            forecast_method=data.get('forecast_method', 'manual'),
            forecast_frequency=data.get('forecast_frequency', 'irregular'),
            forecast_day=data.get('forecast_day'),
            forecast_amount=data.get('forecast_amount'),
            forecast_confidence=data.get('forecast_confidence', 0.0),
            group_locked=data.get('group_locked', False),
            review_needed=data.get('review_needed', False)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'client_id': self.client_id,
            'vendor_name': self.vendor_name,
            'display_name': self.display_name,
            'category': self.category,
            'forecast_method': self.forecast_method,
            'forecast_frequency': self.forecast_frequency,
            'forecast_day': self.forecast_day,
            'forecast_amount': self.forecast_amount,
            'forecast_confidence': self.forecast_confidence,
            'group_locked': self.group_locked,
            'review_needed': self.review_needed
        }
```

#### B. Repositories

```python
# cfo_forecast/data/repositories/vendor_repo.py
from typing import List, Dict, Any, Optional
from ...data.models.vendor import Vendor
from ...integrations.supabase_client import supabase

class VendorRepository:
    def __init__(self):
        self.table = "vendors"
    
    def get_by_client(self, client_id: str) -> List[Vendor]:
        """Get all vendors for a client."""
        try:
            response = supabase.table(self.table) \
                .select("*") \
                .eq("client_id", client_id) \
                .execute()
            
            return [Vendor.from_dict(item) for item in response.data]
        except Exception as e:
            # Log error
            return []
    
    def get_by_display_name(self, display_name: str, client_id: str) -> List[Vendor]:
        """Get vendors by display name for a client."""
        try:
            response = supabase.table(self.table) \
                .select("*") \
                .eq("client_id", client_id) \
                .eq("display_name", display_name) \
                .execute()
            
            return [Vendor.from_dict(item) for item in response.data]
        except Exception as e:
            # Log error
            return []
    
    def update(self, vendor: Vendor) -> bool:
        """Update a vendor."""
        try:
            response = supabase.table(self.table) \
                .update(vendor.to_dict()) \
                .eq("id", vendor.id) \
                .execute()
            
            return len(response.data) > 0
        except Exception as e:
            # Log error
            return False
    
    def update_forecast_config(self, vendor_id: str, forecast_config: Dict[str, Any]) -> bool:
        """Update vendor forecast configuration."""
        try:
            response = supabase.table(self.table) \
                .update(forecast_config) \
                .eq("id", vendor_id) \
                .execute()
            
            return len(response.data) > 0
        except Exception as e:
            # Log error
            return False
```

#### C. Services

```python
# cfo_forecast/services/forecast_service.py
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from ..data.repositories.vendor_repo import VendorRepository
from ..data.repositories.transaction_repo import TransactionRepository
from ..core.classification import classify_vendor
from ..core.forecasting import compute_forecast
from ..core.validation import validate_forecast

class ForecastService:
    def __init__(self):
        self.vendor_repo = VendorRepository()
        self.transaction_repo = TransactionRepository()
    
    def process_vendor(self, display_name: str, client_id: str) -> Dict[str, Any]:
        """Process a single vendor through the forecasting pipeline."""
        try:
            # 1. Get transactions
            transactions = self.transaction_repo.get_by_display_name(
                display_name, client_id, lookback_days=365
            )
            
            if not transactions:
                return {
                    "display_name": display_name,
                    "status": "skipped",
                    "reason": "No transactions found"
                }
            
            # 2. Classify vendor
            classification = classify_vendor(transactions)
            
            # 3. Compute forecast
            forecast = compute_forecast(transactions, classification["classification"])
            
            # 4. Validate forecast
            validation = validate_forecast(display_name, transactions, forecast)
            
            # 5. Update vendor config
            vendors = self.vendor_repo.get_by_display_name(display_name, client_id)
            for vendor in vendors:
                vendor.forecast_method = forecast["method"]
                vendor.forecast_frequency = forecast["frequency"]
                vendor.forecast_day = forecast.get("payment_day")
                vendor.forecast_amount = forecast.get("forecast_amount")
                vendor.forecast_confidence = forecast["confidence"]
                self.vendor_repo.update(vendor)
            
            return {
                "display_name": display_name,
                "status": "success",
                "classification": classification,
                "forecast": forecast,
                "validation": validation
            }
            
        except Exception as e:
            # Log error
            return {
                "display_name": display_name,
                "status": "error",
                "error": str(e)
            }
    
    def process_client(self, client_id: str) -> Dict[str, Any]:
        """Process all vendors for a client."""
        vendors = self.vendor_repo.get_by_client(client_id)
        display_names = set(v.display_name for v in vendors if v.display_name)
        
        results = []
        for display_name in display_names:
            result = self.process_vendor(display_name, client_id)
            results.append(result)
        
        return {
            "client_id": client_id,
            "processed": len(results),
            "success": sum(1 for r in results if r["status"] == "success"),
            "skipped": sum(1 for r in results if r["status"] == "skipped"),
            "error": sum(1 for r in results if r["status"] == "error"),
            "results": results
        }
```

#### D. OpenAI Integration

```python
# cfo_forecast/integrations/openai_client.py
import os
import json
import logging
from typing import List, Dict, Any, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)

class OpenAIClient:
    def __init__(self, api_key: Optional[str] = None):
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
    
    def analyze_transaction_patterns(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze transaction patterns and suggest forecast parameters.
        
        Args:
            transactions: List of transactions with date and amount
            
        Returns:
            Dict with forecast parameters
        """
        if not transactions:
            return {
                "forecast_method": "Manual",
                "frequency": "irregular",
                "notes": "No transactions available for analysis"
            }
        
        # Format transactions for analysis
        txn_data = []
        for tx in transactions:
            txn_data.append({
                "date": tx["date"],
                "amount": float(tx["amount"])
            })
        
        # Create prompt
        prompt = f"""Analyze these transactions:
{json.dumps(txn_data, indent=2)}

Determine:
1. Best forecasting method (Fixed, Trailing30Avg, Trailing90Avg, or Manual)
2. Payment frequency (weekly, monthly, irregular)
3. Brief explanation of the pattern

Respond in JSON format with these keys:
- forecast_method
- frequency
- notes
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a financial analysis assistant."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            logger.error(f"Error in OpenAI analysis: {str(e)}")
            return {
                "forecast_method": "Manual",
                "frequency": "irregular",
                "notes": f"Error during AI analysis: {str(e)}"
            }
    
    def suggest_vendor_aliases(self, vendor_name: str, known_vendors: List[str]) -> List[str]:
        """
        Suggest which vendor names belong to the same company.
        
        Args:
            vendor_name: The vendor name to match against
            known_vendors: List of known vendor names
            
        Returns:
            List of matching vendor names
        """
        try:
            prompt = f"""
            A CFO assistant is trying to determine which of the following vendor names in the transactions table belong to the same company as "{vendor_name}".

            Return a list of matching vendor names (exact strings).

            Vendor options:
            {json.dumps(known_vendors, indent=2)}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}]
            )
            
            matches = json.loads(response.choices[0].message.content)
            logger.info(f"Found {len(matches)} potential matches for {vendor_name}")
            return matches
            
        except Exception as e:
            logger.error(f"Error suggesting aliases for {vendor_name}: {str(e)}")
            return []
```

### 3. Core Logic Preservation

The refactoring preserves your existing core logic by:

1. **Extracting and Isolating**: Moving your forecast algorithms into dedicated modules without changing their logic.

2. **Maintaining OpenAI Integration**: Keeping your OpenAI-based vendor grouping and forecast validation.

3. **Preserving Classification Logic**: Maintaining your vendor classification approach.

For example, your existing classification logic from `configure_forecast.py`:

```python
def classify_and_configure(display_name, txns, supabase):
    stats = analyze_display_history(txns)
    num_months = len(stats['months'])
    num_weeks = len(stats['weeks'])

    # 1) Monthly vs Irregular
    if num_months >= MONTHLY_MIN_MONTHS:
        freq = 'monthly'
        # modal day-of-month
        forecast_day = stats['dom'].most_common(1)[0][0]
        confidence = num_months / MONTHLY_MIN_MONTHS
    # (we leave weekly cutoff as-is, e.g. total txns >= 4)
    elif len(txns) >= 4:
        freq = 'weekly'
        # modal ISO weekday (1=Mon … 7=Sun)
        forecast_day = stats['dow'].most_common(1)[0][0]
        # confidence = weeks covered / expected weeks
        expected_weeks = LOOKBACK_DAYS / 7
        confidence = num_weeks / expected_weeks
    else:
        freq = 'irregular'
        # if at least IRREGULAR_MIN_OCCURRENCES, capture a modal day
        if sum(stats['dom'].values()) >= IRREGULAR_MIN_OCCURRENCES:
            forecast_day = stats['dom'].most_common(1)[0][0]
            confidence = stats['dom'][forecast_day] / sum(stats['dom'].values())
        else:
            forecast_day = None
            confidence = 0
```

Would be preserved in `classification.py` as:

```python
# cfo_forecast/core/classification.py
from collections import Counter
from datetime import datetime, timedelta, UTC
from typing import List, Dict, Any

LOOKBACK_DAYS = 180
MONTHLY_MIN_MONTHS = 6
IRREGULAR_MIN_OCCURRENCES = 2

def analyze_transaction_history(transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze transaction history to extract patterns.
    
    Args:
        transactions: List of transactions with date and amount
        
    Returns:
        Dict with analysis results
    """
    months = set()
    weeks = set()
    dom = Counter()
    dow = Counter()
    amounts = []

    for t in transactions:
        dt = datetime.fromisoformat(t['transaction_date'].replace("Z", "+00:00"))
        amounts.append(float(t['amount']))
        months.add(f"{dt.year}-{dt.month:02d}")
        iso_week = dt.isocalendar()[1]
        weeks.add(f"{dt.year}-W{iso_week:02d}")
        dom[dt.day] += 1
        dow[dt.isoweekday()] += 1

    return {
        'months': months,
        'weeks': weeks,
        'dom': dom,
        'dow': dow,
        'amounts': amounts
    }

def classify_vendor(transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Classify vendor based on transaction patterns.
    
    Args:
        transactions: List of transactions with date and amount
        
    Returns:
        Dict with classification details
    """
    if not transactions:
        return {
            "classification": "irregular",
            "confidence": 0.0,
            "explanation": "No transactions found"
        }
        
    stats = analyze_transaction_history(transactions)
    num_months = len(stats['months'])
    num_weeks = len(stats['weeks'])

    # Monthly vs Irregular
    if num_months >= MONTHLY_MIN_MONTHS:
        classification = 'monthly'
        # modal day-of-month
        forecast_day = stats['dom'].most_common(1)[0][0]
        confidence = num_months / MONTHLY_MIN_MONTHS
    # Weekly
    elif len(transactions) >= 4:
        classification = 'weekly'
        # modal ISO weekday (1=Mon … 7=Sun)
        forecast_day = stats['dow'].most_common(1)[0][0]
        # confidence = weeks covered / expected weeks
        expected_weeks = LOOKBACK_DAYS / 7
        confidence = num_weeks / expected_weeks
    else:
        classification = 'irregular'
        # if at least IRREGULAR_MIN_OCCURRENCES, capture a modal day
        if sum(stats['dom'].values()) >= IRREGULAR_MIN_OCCURRENCES:
            forecast_day = stats['dom'].most_common(1)[0][0]
            confidence = stats['dom'][forecast_day] / sum(stats['dom'].values())
        else:
            forecast_day = None
            confidence = 0
            
    return {
        "classification": classification,
        "forecast_day": forecast_day,
        "confidence": confidence,
        "months_active": num_months,
        "weeks_active": num_weeks
    }
```

### 4. Multi-Client Support

The refactored architecture supports multiple clients through:

1. **Client-Centric Data Model**: All data is associated with a client_id.

2. **Client Configuration**: Each client has its own configuration settings.

3. **Batch Processing**: Scripts can process multiple clients sequentially or in parallel.

```python
# cfo_forecast/scripts/batch_process.py
import argparse
import logging
from ..services.client_service import ClientService
from ..services.forecast_service import ForecastService

logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Batch process multiple clients')
    parser.add_argument('--all', action='store_true', help='Process all active clients')
    parser.add_argument('--client', type=str, help='Process specific client')
    args = parser.parse_args()
    
    client_service = ClientService()
    forecast_service = ForecastService()
    
    if args.all:
        # Process all active clients
        clients = client_service.get_active_clients()
        logger.info(f"Processing {len(clients)} active clients")
        
        for client in clients:
            logger.info(f"Processing client: {client.name} ({client.id})")
            result = forecast_service.process_client(client.id)
            logger.info(f"Processed {result['processed']} vendors: {result['success']} success, {result['error']} errors")
            
    elif args.client:
        # Process specific client
        client = client_service.get_client(args.client)
        if client:
            logger.info(f"Processing client: {client.name} ({client.id})")
            result = forecast_service.process_client(client.id)
            logger.info(f"Processed {result['processed']} vendors: {result['success']} success, {result['error']} errors")
        else:
            logger.error(f"Client not found: {args.client}")
    else:
        logger.error("No action specified. Use --all or --client")

if __name__ == "__main__":
    main()
```

### 5. Database Schema Updates

To support multi-client functionality, the database schema needs these updates:

```sql
-- Create clients table
CREATE TABLE clients (
    client_id TEXT PRIMARY KEY,
    client_name TEXT NOT NULL,
    active BOOLEAN DEFAULT TRUE,
    config JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add foreign key to vendors table
ALTER TABLE vendors 
ADD CONSTRAINT fk_client_id 
FOREIGN KEY (client_id) 
REFERENCES clients(client_id);

-- Add foreign key to transactions table
ALTER TABLE transactions 
ADD CONSTRAINT fk_client_id 
FOREIGN KEY (client_id) 
REFERENCES clients(client_id);

-- Create forecast_versions table for tracking forecast history
CREATE TABLE forecast_versions (
    id SERIAL PRIMARY KEY,
    client_id TEXT NOT NULL REFERENCES clients(client_id),
    version_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    start_week DATE NOT NULL,
    end_week DATE NOT NULL,
    status TEXT DEFAULT 'active',
    forecast_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(client_id, version_date)
);
```

### 6. User Interface Enhancements

The refactored system includes enhanced dashboards:

```python
# cfo_forecast/ui/dashboards/forecast_overview.py
import streamlit as st
import pandas as pd
from ...services.client_service import ClientService
from ...services.forecast_service import ForecastService

def main():
    st.title("Forecast Overview")
    
    # Client selector
    client_service = ClientService()
    clients = client_service.get_active_clients()
    client_options = {c.id: c.name for c in clients}
    
    selected_client = st.selectbox(
        "Select Client",
        options=list(client_options.keys()),
        format_func=lambda x: client_options[x]
    )
    
    if selected_client:
        # Display client forecast overview
        st.header(f"Forecast for {client_options[selected_client]}")
        
        # Weekly balance projection
        st.subheader("Weekly Cash Balance Projection")
        weeks_ahead = st.slider("Projection Period (Weeks)", 4, 24, 12)
        
        # Get projection data
        forecast_service = ForecastService()
        projection = forecast_service.get_weekly_projection(selected_client, weeks_ahead)
        
        # Display chart and data
        if projection:
            # Chart code here
            st.line_chart(projection)
            
            # Data table
            st.dataframe(projection)
        
        # Vendor forecast summary
        st.subheader("Vendor Forecast Summary")
        vendor_forecasts = forecast_service.get_vendor_forecasts(selected_client)
        
        if vendor_forecasts:
            st.dataframe(vendor_forecasts)
            
            # High variance vendors
            high_variance = [v for v in vendor_forecasts if v.get('confidence', 0) < 0.7]
            if high_variance:
                st.warning(f"{len(high_variance)} vendors have low confidence forecasts")
                st.dataframe(high_variance)

if __name__ == "__main__":
    main()
```

## Implementation Plan

### Phase 1: Foundation (Weeks 1-2)

1. **Set up new project structure**
   - Create directory structure
   - Set up configuration management
   - Implement logging

2. **Implement data models**
   - Create Client, Vendor, Transaction models
   - Implement repository pattern

3. **Extract core logic**
   - Move classification logic to dedicated module
   - Move forecasting logic to dedicated module
   - Move validation logic to dedicated module

### Phase 2: Multi-Client Support (Weeks 3-4)

1. **Update database schema**
   - Create clients table
   - Add foreign key constraints
   - Create forecast_versions table

2. **Implement client services**
   - Client management
   - Multi-client batch processing

3. **Update OpenAI integration**
   - Refactor to support multiple clients
   - Enhance error handling

### Phase 3: User Interface (Weeks 5-6)

1. **Enhance dashboards**
   - Add client selector
   - Improve visualization
   - Add forecast comparison

2. **Implement reporting**
   - Excel export
   - PDF export

### Phase 4: Testing and Migration (Weeks 7-8)

1. **Implement tests**
   - Unit tests
   - Integration tests

2. **Data migration**
   - Migrate existing data to new schema
   - Validate data integrity

3. **Deployment**
   - Set up CI/CD
   - Deploy to production

## Migration Strategy

To ensure a smooth transition:

1. **Parallel Operation**: Run both systems side-by-side initially.

2. **Incremental Migration**: Migrate one client at a time, starting with a test client.

3. **Validation**: Compare forecasts from both systems to ensure consistency.

4. **Rollback Plan**: Maintain ability to revert to the original system if needed.

## Conclusion

This refactoring blueprint preserves your valuable forecast logic and OpenAI integration while enhancing the architecture for multi-client support, scalability, and maintainability. The modular design allows for future extensions and improvements while ensuring that your current business logic continues to function as expected.

The implementation plan provides a structured approach to the refactoring, with clear phases and deliverables. By following this blueprint, you can transform your CFO Forecast system into a more robust, scalable, and maintainable solution without losing the sophisticated forecasting capabilities you've already developed.
