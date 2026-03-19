# Halal Status Dashboard Integration - Complete Guide

## Overview

This guide shows how to integrate halal status caching with Claude AI verification into the Streamlit dashboard.

**Two new modules**:
1. **halal_cache.py** - Manages 30-day halal status cache with auto-verification
2. **dashboard_halal_display.py** - Streamlit UI components for displaying halal status

## Features

### Caching Strategy
- **Cache TTL**: 30 days for each stock
- **Auto-Verification**: Claude AI re-verifies when cache expires
- **Smart Updates**: Batch operations for efficiency
- **Fallback**: Returns expired cache if API fails

### Dashboard Integration
- ✅ Show halal status in top 5 candidates list
- ✅ Add halal status to search results
- ✅ Individual stock verification with Claude AI
- ✅ Bulk verification for batch processing
- ✅ Cache statistics and monitoring
- ✅ Download verification results as CSV

## Quick Integration

### Step 1: Import Required Modules

Add to your `streamlit_app.py`:

```python
from halal_cache import get_halal_cache
from dashboard_halal_display import (
    DashboardHalalDisplay,
    display_halal_in_top_5,
    display_search_modal,
    display_stats_sidebar
)
```

### Step 2: Use in Top 5 Display

Replace the existing top 5 display section with:

```python
# In your streamlit app, in the "Top 5 Candidates" section
display = DashboardHalalDisplay()
display.display_top_candidates_with_halal(results[:5])
```

Or use the quick function:

```python
display_halal_in_top_5(results)
```

**What this shows**:
- Ranking & ticker
- Asymmetric pattern badge
- **Halal status badge** (PASS/FAIL/UNVERIFIED)
- **Cache age** if cached
- **"Fresh verified"** if just checked
- Details button

### Step 3: Add Search Section

Add new section for halal search:

```python
st.header("Halal Status Search")
display = DashboardHalalDisplay()
display.display_search_and_verify()
```

**Features**:
- Ticker search box
- "Force re-check" toggle
- Halal status badge
- Verdict display
- Expandable gate details
- Cache expiry information
- Auto-refresh timing

### Step 4: Add Cache Stats (Optional)

Add to sidebar or main page:

```python
# In sidebar
with st.sidebar:
    st.markdown("---")
    display = DashboardHalalDisplay()
    display.display_cache_stats()

# Or main page
display.display_cache_stats()
```

**Shows**:
- Total cached stocks
- Fresh entries (< 30 days)
- Expired entries
- Status distribution (PASS/FAIL/UNVERIFIED)
- Cache TTL configuration

## Code Examples

### Example 1: Add to Existing Top 5

```python
# Before your existing top 5 loop
st.header("Top 5 Opportunities")
st.write("Ranked by composite score (60% asymmetry quality + 40% signal strength)")

# NEW: Use halal display instead of simple list
from dashboard_halal_display import display_halal_in_top_5
display_halal_in_top_5(results)
```

### Example 2: Add Search Tab

```python
# Add new tab for search
tab1, tab2, tab3 = st.tabs(["Dashboard", "Search", "Analysis"])

with tab1:
    st.header("Discovery Summary")
    # ... existing dashboard code ...

with tab2:
    st.header("Halal Status Search")
    from dashboard_halal_display import display_search_modal
    display_search_modal()

with tab3:
    st.header("Analysis")
    # ... rest of analysis ...
```

### Example 3: Bulk Verification

```python
# For batch processing
all_tickers = [r['ticker'] for r in results]

display = DashboardHalalDisplay()
display.display_bulk_verify(all_tickers)
```

## How Caching Works

### First Time Checking MSFT

```
User searches: MSFT
  ↓
Cache check: Not found
  ↓
Fetch financial data
  ↓
Run halal gates (4 gates)
  ↓
Claude AI review (if needed)
  ↓
Store in cache with 30-day expiry
  ↓
Display: "✨ Fresh verified"
```

### Checking MSFT After 15 Days

```
User searches: MSFT
  ↓
Cache check: Found & fresh (15 days old)
  ↓
Return cached result
  ↓
Display: "🔄 Cached 15d"
  ↓
No API call needed
```

### Checking MSFT After 30 Days

```
User searches: MSFT
  ↓
Cache check: Expired (30+ days)
  ↓
Auto-refresh triggered
  ↓
Fetch fresh data
  ↓
Run halal gates + Claude AI
  ↓
Update cache (new 30-day expiry)
  ↓
Display: "✨ Fresh verified"
```

## Database Structure

The halal cache uses SQLite table: `halal_status_cache`

```sql
CREATE TABLE halal_status_cache (
    ticker TEXT PRIMARY KEY,
    halal_status TEXT NOT NULL,              -- 'pass', 'fail', 'unverified'
    gates_json TEXT,                         -- Full gate results as JSON
    first_failure TEXT,                      -- Which gate failed first
    flags_json TEXT,                         -- Warning flags
    halal_verdict TEXT,                      -- Human-readable verdict
    claude_review TEXT,                      -- Claude AI reasoning
    cached_at REAL NOT NULL,                 -- Cache creation time (unix)
    expires_at REAL NOT NULL,                -- Expiry time (unix)
    created_at TEXT NOT NULL                 -- ISO timestamp
)
```

## API & Cost

### Claude AI Calls
- **Only for unverified edge cases** (missing sector/revenue data)
- **Cost per call**: ~$0.01
- **Frequency**: Once per 30 days per stock
- **Total monthly cost** (100 stocks checked): ~$0.33

### Performance
- **Cache hit** (< 30 days): Instant
- **Cache miss** (> 30 days): ~3-5 seconds (includes API calls)
- **Batch operation** (50 stocks): ~30-60 seconds

## Configuration

### Change Cache TTL

Modify cache expiry in `halal_cache.py`:

```python
class HalalStatusCache:
    def __init__(self, db_path: str = "cache.db"):
        self.cache_ttl_days = 30  # <-- Change this to e.g., 14, 60, 90
```

### Use Separate Database

```python
# Use different cache file for testing
cache = HalalStatusCache(db_path="cache_test.db")
```

### Force Refresh All

```python
# Clear expired cache
cache.clear_expired_cache()

# Clear specific ticker
cache.clear_cache("MSFT")

# Force re-verification
halal_result = cache.get_halal_status_with_cache(
    "MSFT",
    force_refresh=True  # <-- Bypass cache
)
```

## Monitoring & Debugging

### Check Cache Health

```python
from halal_cache import get_halal_cache

cache = get_halal_cache()
stats = cache.get_cache_stats()

print(f"Cached stocks: {stats['total_cached']}")
print(f"Fresh: {stats['fresh_entries']}")
print(f"Expired: {stats['expired_entries']}")
print(f"Status dist: {stats['status_distribution']}")
```

### View Cached Entry

```python
result = cache.get_cached_halal_status("MSFT")
print(f"Status: {result['halal_status']}")
print(f"Verdict: {result['halal_verdict']}")
print(f"Age: {result['cache_age_days']} days")
```

### Clear All Cache

```python
# Delete all cache entries
import sqlite3
conn = sqlite3.connect("cache.db")
cursor = conn.cursor()
cursor.execute("DELETE FROM halal_status_cache")
conn.commit()
conn.close()
```

## Troubleshooting

### "HalalGateEngine not available"

**Cause**: Anthropic SDK not installed or API key missing

**Solution**:
```bash
pip install anthropic
# Add to .env:
ANTHROPIC_API_KEY=sk-ant-...
```

### Cache not updating after 30 days

**Cause**: `force_refresh` not set

**Solution**:
```python
result = cache.get_halal_status_with_cache(ticker, force_refresh=True)
```

### Claude AI returns "error" status

**Cause**: API limit or network issue

**Solution**: Falls back to existing cache (with warning)

### Empty cache stats

**Cause**: No stocks checked yet

**Solution**: Search for a stock or run bulk verification first

## Integration Checklist

- [ ] Copy `halal_cache.py` to project
- [ ] Copy `dashboard_halal_display.py` to project
- [ ] Update `streamlit_app.py` to import new modules
- [ ] Replace top 5 display with halal version
- [ ] Add search section
- [ ] Add cache stats (optional)
- [ ] Test with sample tickers: MSFT, JPM, AAPL
- [ ] Verify Anthropic API key in .env
- [ ] Deploy to production

## Example: Complete Modified Dashboard Section

```python
import streamlit as st
from dashboard_halal_display import DashboardHalalDisplay

st.header("Discovery Results")

# Initialize display
display = DashboardHalalDisplay()

# Show summary metrics
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Candidates", len(results))
with col2:
    st.metric("Full Asymmetric", sum(1 for r in results if r['pattern']=='full'))
with col3:
    st.metric("Top 5 Avg Score", f"{sum(r['score'] for r in results[:5])/5:.2f}")
with col4:
    st.metric("Halal Pass Rate", f"{sum(1 for r in results if r['halal_status']=='pass') / len(results) * 100:.0f}%")

st.divider()

# Top 5 with halal status
display.display_top_candidates_with_halal(results)

st.divider()

# Search & verify
display.display_search_and_verify()

st.divider()

# Cache statistics
display.display_cache_stats()
```

## Support & Monitoring

### Logs

Check logs for cache operations:
```
Cache hit: MSFT halal status (15.2 days old)
Cache expired: MSFT halal status (expires at 2026-04-19)
Cached halal status for MSFT (expires in 30 days)
Claude AI review: MSFT → PASS
```

### Performance Metrics

- Average cache hit time: < 100ms
- Average fresh check time: 3-5 seconds
- Monthly API cost: < $1 (for 100+ stocks)
- Storage: ~500 bytes per cached stock

---

## Next Steps

1. **Integrate into streamlit_app.py**
2. **Test with sample tickers**
3. **Monitor cache stats** over time
4. **Adjust TTL** based on your needs
5. **Add notifications** when cache expires
6. **Consider batch updates** via scheduled tasks

See [HALAL_GATES_GUIDE.md](HALAL_GATES_GUIDE.md) for halal gate details.
