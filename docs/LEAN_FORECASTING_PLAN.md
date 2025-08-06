# Lean Cash Flow Forecasting System - Master Plan

## **Vision: Simple, Accurate, Sustainable**

Build a lean forecasting system that actually works - no statistical complexity, just simple pattern recognition and individual forecast records that can be easily updated and maintained.

---

## **Core Requirements (User's Vision)**

### **Pattern Detection Logic:**
1. **Frequency Detection**: Daily, Weekly, Bi-weekly, Monthly, Quarterly, Annual, or Irregular
2. **Specific Timing Detection**: 
   - Daily: M-F or 7 days?
   - Weekly: Monday? Friday? 
   - Bi-weekly: 15th & 30th? Every other Friday?
   - Monthly: 12th? Last day of month?
3. **Irregular = "Others"**: No forecast, just placeholder for one-time estimates

### **Forecasting Process:**
1. **Individual Date Records**: Store forecast for each specific date (8/15, 8/30, 9/15, etc.)
2. **Weighted Average**: Last 3 months + extra weight on last month
3. **Manual Override**: User can change any forecast amount in UI
4. **13+ Week Projection**: Generate specific dates 13+ weeks out

### **Weekly Reconciliation:**
1. **Import Actuals**: Load actual transactions each week
2. **Update Future Forecasts**: Adjust based on new patterns
3. **Lock Past Weeks**: Replace forecasts with actual data
4. **Rolling Balance**: Always accurate current position

---

## **Database-First Architecture (Most Sustainable)**

### **Core Tables Design:**

```sql
-- 1. VENDOR GROUPS - The foundation
CREATE TABLE vendor_groups (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(255) NOT NULL,
    group_name VARCHAR(255) NOT NULL,
    vendor_display_names TEXT[] NOT NULL, -- ['Amazon Revenue', 'Affirm', 'Shopify']
    
    -- Pattern Detection Results
    pattern_frequency VARCHAR(20), -- 'daily', 'weekly', 'biweekly', 'monthly', 'irregular'
    pattern_days TEXT, -- 'M-F', 'Monday', '15,30', '12', 'last_day', etc.
    pattern_confidence DECIMAL(5,4) DEFAULT 0.0,
    
    -- Forecasting Method
    forecast_method VARCHAR(20) DEFAULT 'weighted_average', -- 'weighted_average', 'manual'
    
    -- Metadata
    is_active BOOLEAN DEFAULT true,
    last_analyzed DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(client_id, group_name)
);

-- 2. INDIVIDUAL FORECASTS - The heart of the system
CREATE TABLE forecasts (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(255) NOT NULL,
    vendor_group_name VARCHAR(255) NOT NULL,
    forecast_date DATE NOT NULL,
    
    -- Forecast Data
    forecast_amount DECIMAL(15,2) NOT NULL,
    forecast_type VARCHAR(20) NOT NULL, -- 'daily', 'weekly', 'biweekly', 'monthly'
    forecast_method VARCHAR(20) NOT NULL, -- 'weighted_average', 'manual'
    
    -- Actual Data (filled in during reconciliation)
    actual_amount DECIMAL(15,2), -- NULL until actuals loaded
    variance DECIMAL(15,2), -- actual - forecast
    is_locked BOOLEAN DEFAULT false, -- true once actuals are final
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(client_id, vendor_group_name, forecast_date),
    
    -- Foreign key to vendor_groups
    CONSTRAINT fk_vendor_group 
        FOREIGN KEY (client_id, vendor_group_name) 
        REFERENCES vendor_groups(client_id, group_name)
);

-- 3. PATTERN ANALYSIS - Audit trail of what system detected
CREATE TABLE pattern_analysis (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(255) NOT NULL,
    vendor_group_name VARCHAR(255) NOT NULL,
    analysis_date DATE NOT NULL,
    
    -- Analysis Results
    frequency_detected VARCHAR(20), -- 'daily', 'weekly', etc.
    specific_days TEXT, -- 'M-F', 'Monday', '15,30', etc.
    confidence_score DECIMAL(5,4),
    sample_size INTEGER, -- number of transactions analyzed
    date_range_start DATE,
    date_range_end DATE,
    
    -- Raw Data
    transactions_analyzed INTEGER,
    average_amount DECIMAL(15,2),
    explanation TEXT,
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- 4. ACTUALS IMPORT LOG - Track what's been imported
CREATE TABLE actuals_import (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(255) NOT NULL,
    import_date DATE NOT NULL,
    week_start_date DATE NOT NULL,
    week_end_date DATE NOT NULL,
    
    -- Import Results
    transactions_imported INTEGER,
    forecasts_updated INTEGER,
    new_patterns_detected INTEGER,
    
    -- Status
    status VARCHAR(20) DEFAULT 'completed', -- 'completed', 'failed', 'partial'
    notes TEXT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(client_id, week_start_date)
);
```

### **Indexes for Performance:**
```sql
CREATE INDEX idx_vendor_groups_client ON vendor_groups(client_id);
CREATE INDEX idx_forecasts_client_date ON forecasts(client_id, forecast_date);
CREATE INDEX idx_forecasts_group_date ON forecasts(vendor_group_name, forecast_date);
CREATE INDEX idx_forecasts_unlocked ON forecasts(client_id, is_locked) WHERE is_locked = false;
```

---

## **Implementation Phases (Lean & Nimble)**

### **Phase 1: Foundation (Week 1)**
- ✅ Create database tables
- ✅ Basic vendor group CRUD operations  
- ✅ Test data insertion/retrieval
- ✅ Simple CLI commands for testing

**Success Criteria**: Can create vendor groups and store them

### **Phase 2: Simple Pattern Detection (Week 2)**
- ✅ Implement basic frequency detection (daily/weekly only)
- ✅ Simple specific day detection (M-F, Monday, etc.)
- ✅ Store results in pattern_analysis table
- ✅ CLI command to run pattern detection

**Success Criteria**: Can detect "BestSelf Revenue happens daily M-F"

### **Phase 3: Forecast Generation (Week 3)**
- ✅ Generate individual forecast records for 13+ weeks
- ✅ Implement weighted average calculation
- ✅ Populate forecasts table with specific dates
- ✅ CLI command to generate forecasts

**Success Criteria**: Can generate forecasts for 8/5, 8/6, 8/7, etc.

### **Phase 4: Weekly Reconciliation (Week 4)**
- ✅ Import actual transaction data
- ✅ Match actuals to forecasts by date/vendor group
- ✅ Calculate variances and lock past weeks
- ✅ Update rolling balance calculations

**Success Criteria**: Can import weekly actuals and update forecasts

### **Phase 5: Basic UI (Week 5)**
- ✅ 13-week forecast view (table format)
- ✅ Show forecast vs actual with variances
- ✅ Manual override capability (edit individual forecasts)
- ✅ Rolling cash balance projection

**Success Criteria**: User can view and edit 13-week forecast

### **Phase 6: Enhanced Patterns (Week 6)**
- ✅ Add bi-weekly pattern detection (15th/30th)
- ✅ Add monthly pattern detection (12th, last day, etc.)
- ✅ Improve confidence scoring
- ✅ Handle irregular patterns ("Others" bucket)

**Success Criteria**: Can detect all pattern types accurately

### **Phase 7: Advanced Forecasting (Week 7)**
- ✅ Implement proper weighted averages (last month heavier)
- ✅ Seasonal adjustments (optional)
- ✅ Pattern drift detection (when patterns change)
- ✅ Forecast accuracy reporting

**Success Criteria**: Forecasts are accurate and adapt to changes

### **Phase 8: Production Ready (Week 8)**
- ✅ Error handling and validation
- ✅ Performance optimization
- ✅ Automated weekly imports
- ✅ User documentation

**Success Criteria**: System runs reliably without manual intervention

---

## **Key Design Principles**

### **1. Lean Architecture**
- **Individual forecast records** = simple queries, easy updates
- **No complex statistical analysis** = just count transactions and detect patterns
- **Database-driven logic** = less code, more data integrity

### **2. Nimble Development**
- **Start with daily/weekly only** = get something working fast
- **Add complexity gradually** = bi-weekly, monthly, etc.
- **Test with real data early** = catch problems immediately

### **3. Strong Foundation**
- **Proper foreign keys** = data integrity
- **Audit trails** = pattern_analysis table tracks what system detected
- **Manual override capability** = user can fix any forecast
- **Actual vs forecast tracking** = system learns and improves

---

## **Success Metrics**

### **Technical Metrics:**
- **Pattern Detection Accuracy**: >90% of patterns correctly identified
- **Forecast Accuracy**: <20% variance between forecast and actual
- **Performance**: <2 seconds to generate 13-week forecast
- **Reliability**: >99% uptime for automated weekly imports

### **User Metrics:**
- **Time to Generate Forecast**: <30 seconds from vendor group creation
- **Time to Update Forecast**: <5 seconds to edit any amount
- **Cash Position Accuracy**: Rolling balance always reflects current reality
- **User Adoption**: CFO uses this instead of spreadsheets

---

## **Risk Mitigation**

### **Technical Risks:**
- **Database Performance**: Proper indexing, regular maintenance
- **Pattern Detection Fails**: Manual override capability as backup
- **Data Import Issues**: Comprehensive error handling and logging

### **Business Risks:**
- **Pattern Changes**: System detects and adapts automatically  
- **Manual Overrides**: Full audit trail of all changes
- **User Training**: Simple UI that mirrors existing spreadsheet workflows

---

## **Next Steps**

1. **Create database tables** (Phase 1)
2. **Build basic vendor group operations**
3. **Test with BestSelf data** 
4. **Implement simple daily pattern detection**
5. **Generate first 13-week forecast**

**Let's start with Phase 1 - creating the database foundation.**