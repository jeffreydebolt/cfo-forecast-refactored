# Known Issues & Blockers

## Instructions
- Document all bugs, blockers, and problems
- Include reproduction steps when possible
- Track attempted solutions
- Update status as issues are resolved

## Issue Template
```markdown
### [ISSUE-XXX] - [Issue Title]
**Status**: [Open/In Progress/Blocked/Resolved]
**Severity**: [Critical/High/Medium/Low]
**Type**: [Bug/Performance/Security/Design Flaw]
**Reported**: [Date]
**Reporter**: [Who found it]

**Description**:
[Detailed description of the issue]

**Reproduction Steps**:
1. [Step 1]
2. [Step 2]
3. [Expected vs Actual result]

**Error Messages/Logs**:
```
[Paste relevant errors or logs]
```

**Attempted Solutions**:
1. [What was tried] - [Result]
2. [What was tried] - [Result]

**Proposed Solution**:
[How to fix it]

**Workaround**:
[Temporary solution if available]

**Related Files**:
- [file1.py]
- [file2.py]
```

## Current Issues

### [ISSUE-001] - Hardcoded Client ID Throughout Codebase
**Status**: Open  
**Severity**: High  
**Type**: Design Flaw  
**Reported**: 2025-01-28  
**Reporter**: Code Review  

**Description**:
The client ID "spyguy" is hardcoded in multiple files, making it impossible to use the system for multiple clients without code changes.

**Affected Files**:
- run_forecast.py (lines 23, 34, 88)
- ai_group_vendors.py (line 64)
- vendor_forecast.py (multiple locations)
- Most other Python files

**Attempted Solutions**:
1. None yet - needs systematic refactoring

**Proposed Solution**:
1. Create a configuration system
2. Pass client_id as parameter through all functions
3. Add client selection to CLI/UI

**Workaround**:
Currently requires manual code changes for different clients

---

### [ISSUE-002] - No Error Recovery for API Failures
**Status**: Open  
**Severity**: High  
**Type**: Bug  
**Reported**: 2025-01-28  
**Reporter**: Code Review  

**Description**:
OpenAI API calls have no retry logic or graceful degradation. System crashes if API is unavailable or rate limited.

**Error Messages/Logs**:
```
openai.error.RateLimitError: Rate limit exceeded
```

**Attempted Solutions**:
1. None yet

**Proposed Solution**:
1. Implement exponential backoff retry logic
2. Add fallback mechanisms for vendor classification
3. Cache API responses to reduce calls

**Workaround**:
Manual restart and hope for success

---

### [ISSUE-003] - Dashboard Performance Degradation
**Status**: Open  
**Severity**: Medium  
**Type**: Performance  
**Reported**: 2025-01-28  
**Reporter**: Code Review  

**Description**:
Streamlit dashboards load slowly when dealing with large numbers of vendors (>1000). No pagination or lazy loading implemented.

**Reproduction Steps**:
1. Run mapping_review.py dashboard
2. Load client with >1000 vendors
3. Experience 10+ second load times

**Attempted Solutions**:
1. None yet

**Proposed Solution**:
1. Implement pagination
2. Add caching for vendor data
3. Optimize database queries
4. Consider moving to more performant UI framework

---

### [ISSUE-004] - Duplicate Transaction Edge Cases
**Status**: Open  
**Severity**: Medium  
**Type**: Bug  
**Reported**: 2025-01-28  
**Reporter**: Code Review  

**Description**:
Duplicate detection logic may fail for transactions with identical date, amount, and vendor but legitimate duplicates (e.g., multiple identical purchases same day).

**Current Logic**:
Checks date + vendor + amount + client for uniqueness

**Attempted Solutions**:
1. None yet

**Proposed Solution**:
1. Add transaction description to duplicate check
2. Implement time-based windowing
3. Add manual override option

---

### [ISSUE-005] - No Database Migration System
**Status**: Open  
**Severity**: Medium  
**Type**: Design Flaw  
**Reported**: 2025-01-29  
**Reporter**: Documentation Review  

**Description**:
No system for managing database schema changes. Makes updates risky and hard to track.

**Proposed Solution**:
1. Implement Alembic or similar migration tool
2. Create initial migration from current schema
3. Document migration procedures

---

## Resolved Issues

### [ISSUE-000] - Example Resolved Issue
**Status**: Resolved  
**Severity**: Low  
**Type**: Bug  
**Reported**: 2025-01-01  
**Reporter**: Example  
**Resolved**: 2025-01-02  

**Description**:
Example of a resolved issue for reference.

**Resolution**:
Fixed by updating configuration in commit abc123.

---

## Blocked Issues

*None currently*

---

## Security Vulnerabilities

### [SEC-001] - Potential SQL Injection in Raw Queries
**Status**: Open  
**Severity**: Critical  
**Type**: Security  

**Description**:
Some database queries use string concatenation instead of parameterized queries.

**Affected Files**:
- Need full security audit to identify all instances

**Proposed Solution**:
1. Audit all database queries
2. Replace with parameterized queries
3. Add query validation layer

---

## Performance Bottlenecks

### [PERF-001] - Sequential Vendor Processing
**Status**: Open  
**Severity**: Medium  
**Type**: Performance  

**Description**:
Vendors are processed one at a time in run_forecast.py, making large batches very slow.

**Current Performance**:
- ~2 seconds per vendor
- 1000 vendors = ~33 minutes

**Proposed Solution**:
1. Implement parallel processing
2. Batch API calls where possible
3. Add progress reporting

---

## Known Limitations

1. **Single data source**: Only Mercury CSV imports supported
2. **No real-time updates**: Requires manual import/refresh
3. **Limited to 13-week forecasts**: No long-term projections
4. **No multi-currency support**: USD only
5. **No mobile support**: Dashboards not responsive