# FORECASTING LOGIC - CORE REQUIREMENTS

**CRITICAL: This is the definitive specification for how forecasting works. Never deviate from this logic.**

## Core Workflow

### 1. VENDOR GROUPING FIRST
- Normalize vendor names (e.g., amazon93029 → Amazon Revenue using regex)
- Group vendors together (e.g., "bestself" + "affirm" + "Shopify" → "E-commerce Revenue")
- User controls the groupings - system doesn't need to know business logic
- **ALL SUBSEQUENT STEPS WORK ON VENDOR GROUPS, NOT INDIVIDUAL VENDORS**

### 2. PATTERN DETECTION ON GROUPS
Once a vendor group is created, the system looks for:

**Frequency Detection:**
- daily
- weekly  
- bi-weekly
- monthly
- quarterly
- annually
- irregular (no pattern - use "others" placeholder)

**Specific Timing Detection:**
- If daily: is it M-F?
- If weekly: is it on Monday?
- If bi-weekly: is it on 15th and 30th? Or specific Mondays?
- If monthly: is it the 12th?
- If quarterly: specific months/dates?

**Example: Amazon Group**
- Frequency: bi-weekly
- Timing: Mondays
- Amount: ~$42k per deposit

### 3. FORECAST GENERATION
**Generate individual forecast records for each specific date:**

- If daily (M-F): create records for every weekday for 13+ weeks
- If weekly (Monday): create records for every Monday for 13+ weeks  
- If bi-weekly (Mondays): create records for every other Monday
- If bi-weekly (15th/30th): create records for 8/15, 8/30, 9/15, 9/30, etc.
- If monthly: create records for specific day each month
- If quarterly: create records for specific dates each quarter

**Each forecast record contains:**
- Date (specific date, not aggregated)
- Vendor Group (not individual vendor)
- Amount (forecasted amount)
- Pattern type (daily/weekly/bi-weekly/etc.)
- Forecast method (weighted_average/manual)

### 4. FORECASTING LOGIC
**Amount Calculation:**
- Default: weighted average of last 3 months + extra weight on last month
- Manual: user can override any forecast amount
- User can change logic anytime in UI

**Database Storage:**
- Store each forecast as individual database record for each date
- NOT aggregated, NOT daily averages
- Each record is for a specific date and vendor group

### 5. WEEKLY RECONCILIATION
- System receives actual activity weekly
- Updates future forecasts based on new patterns
- "Fixes" most recent week with actual data
- Rolling balance stays correct

## Example Implementation

**Amazon Vendor Group:**
```
Input: AMAZON.CXYZ123, AMAZON.CABC456, Amazon.com Services LLC
Group: "Amazon"
Pattern Detected: bi-weekly, Mondays, ~$42,000
Forecast Records Generated:
- 2025-08-04: Amazon, $42,000, bi-weekly
- 2025-08-18: Amazon, $42,000, bi-weekly  
- 2025-09-01: Amazon, $42,000, bi-weekly
- 2025-09-15: Amazon, $42,000, bi-weekly
```

**Shopify Vendor Group:**
```
Input: SHOPIFY, Shopify Revenue, STRIPE
Group: "E-commerce"
Pattern Detected: daily, M-F, ~$2,400/day
Forecast Records Generated:
- 2025-08-04: E-commerce, $2,400, daily
- 2025-08-05: E-commerce, $2,400, daily
- 2025-08-06: E-commerce, $2,400, daily
- 2025-08-07: E-commerce, $2,400, daily
- 2025-08-08: E-commerce, $2,400, daily
- 2025-08-11: E-commerce, $2,400, daily
- ... (continue for 13+ weeks of weekdays)
```

## CRITICAL RULES

1. **NEVER forecast individual vendor names** - always forecast vendor groups
2. **ALWAYS generate individual date records** - never aggregate or average
3. **Pattern detection works on the COMBINED GROUP data** - not individual vendors
4. **Forecasting amounts come from GROUP historical patterns** - not individual vendor patterns
5. **Each forecast record is for a specific date** - no weekly/monthly summaries
6. **User controls vendor groupings** - system executes the pattern detection and forecasting

## What NOT To Do

❌ Don't average all vendors into daily amounts  
❌ Don't forecast individual AMAZON.CXYZ vendors  
❌ Don't create weekly/monthly aggregate forecasts  
❌ Don't ignore the specific timing patterns (Mondays, 15th/30th, etc.)  
❌ Don't combine different vendor groups in pattern analysis  

## Success Criteria

✅ Amazon group shows bi-weekly Monday deposits of ~$42k  
✅ Each revenue stream forecasted separately by group  
✅ Individual date records generated for 13+ weeks  
✅ Patterns detected on combined group data  
✅ Forecasts stored as individual database records for each date