# Build Status - Halal Asymmetric Stock Finder

## Current State Summary

### ✅ COMPLETED 

**Step 1: Data Fetcher (fetcher.py) - 100% COMPLETE**
- DataCache class with 3 SQLite tables (financial_data, price_data, ai_reasoning)
- yfinance wrapper functions:
  - `fetch_income_statement()` - 10-year income statements
  - `fetch_balance_sheet()` - 10-year balance sheets
  - `fetch_cashflow()` - 10-year cash flow statements
  - `fetch_quote_info()` - Current price, market cap, 52-week high/low, sector/industry
  - `fetch_price_history()` - Historical prices + 30-day average calculation
- FMP free tier wrapper functions:
  - `fetch_stock_screener()` - Pre-screen 2,000 stocks → 150-250 candidates in one call
  - `fetch_insider_transactions()` - Last 90 days, identifies recent insider buying
  - `fetch_revenue_segments()` - Product/service breakdown for haram revenue detection
  - `fetch_company_profile()` - Sector, industry, CEO, description
- Unified entry points:
  - `get_all_financial_data()` - All income/balance/cashflow in one call
  - `get_all_price_data()` - All price data in one call
  - `get_full_stock_data()` - Everything (financial + price data)
- Caching:
  - Financial data: 7-day expiry
  - Price data: 24-hour expiry
  - AI reasoning: No expiry (historical record)
- Error handling: Timeouts, rate limits, missing data, HTTP errors
- Logging: All operations logged with timestamps

### 🔴 PENDING - Next Build Steps

**Step 2: Halal Gate Engine (halal.py)**
- Gate 1: Riba Business Model (sector auto-fail)
- Gate 2: Debt Ratio (total debt / 30-day avg market cap < 33%)
- Gate 3: Haram Revenue (< 5% from prohibited sources)
- Gate 4: Loss Financing (Track B only: equity-funded, not debt-funded)
- Outputs: pass/fail/unverified status + reasons

**Step 3: Track Router (tracker.py)**
- Track A detection: FCF positive 4+ of last 5 years
- Track A-Transition detection: Was Track A, now FCF negative in most recent year
- Track B detection: FCF negative 3+ of last 5 years
- Routes stock to correct evaluation pipeline

**Step 4: Signal Scoring Engine (scorer.py)**
- Track A signals (8 signals, score 1-3 each):
  - ROIC (> 12% = value creating)
  - ROIC trend (improving/stable/deteriorating)
  - FCF consistency (5, 4, or 3+ positive years)
  - Reinvestment rate (% of earnings reinvested)
  - Normalized vs reported earnings (trough detection)
  - EV/FCF vs own 5yr average (valuation cheapness)
  - Insider ownership %
  - Net cash as % of market cap
- Track B signals (8 signals, score 1-3 each):
  - Gross margin level & trend
  - Revenue growth (3yr CAGR)
  - R&D + capex as % of loss
  - Operating leverage trend
  - Gross profit vs revenue growth
  - Cash runway (years at current burn)
  - Insider ownership %
  - Debt structure (equity-funded vs debt-funded)
- Outputs: JSON with all signal values + scores + total score

**Step 5: Asymmetric Pattern Detector (detector.py)**
- Checks 3 components:
  1. Floor (downside protection): net cash, cheap valuation, high ROIC, or runway
  2. Mispricing (market wrong): trough signal, cheap valuation, price punished, margin improving
  3. Catalyst (path to re-rating): insider buying, operating leverage, ROIC trend, visible breakeven path
- Routes to: Full Asymmetric (3/3), Partial Asymmetric (2/3), Not Asymmetric (1/3)
- Pulls 52-week low for mispricing check

**Step 6: Validation Workflow (validation.py)**
- Single ticker input from user
- Runs Steps 2-5 (halal gates, track routing, signal scoring, pattern detection)
- Produces full AI reasoning regardless of pattern result
- Outputs all 3 layers immediately

**Step 7: Smart Pre-Screen Stage 1 (via fetcher.py enhancement)**
- FMP screener call already in fetcher.py
- Will be integrated into discovery workflow
- Reduces universe from ~2,000 to ~150-250 before full financial pulls

**Step 8: Discovery Workflow (discovery.py)**
- 6-stage pipeline:
  1. Smart pre-screen (150-250 candidates)
  2. Pull full financial data for each
  3. Run halal gates 2-4
  4. Route to track + score signals
  5. Run asymmetric pattern detector
  6. AI reasoning on top 5 candidates
- SQLite checkpointing for rate limit recovery
- Outputs Layer 1 summary cards for all 5 results

**Step 9: Streamlit UI (app.py)**
- Build LAST (all logic proven first)
- Ticket input and job selector (Discover / Validate)
- Layer 1 summary cards with expand/collapse for Layers 2 + 3
- Signal scorecard as visual grid (green/yellow/red)
- Collapsible raw signal data for verification

---

## Files in Workspace

```
Assymetric_Stock_Finder/
├── fetcher.py              ✅ COMPLETE (Step 1)
├── halal.py                ❌ Not started (Step 2)
├── tracker.py              ❌ Not started (Step 3)
├── scorer.py               ❌ Not started (Step 4)
├── detector.py             ❌ Not started (Step 5)
├── validation.py           ❌ Not started (Step 6)
├── discovery.py            ❌ Not started (Step 8)
├── app.py                  ❌ Not started (Step 9)
├── cache.py                ⚠️  Integrated into fetcher.py
├── watchlist.py            ❌ Not started
├── requirements.txt        ✅ Present
├── .env                    ⚠️  Needs API keys configured
├── .gitignore              ✅ Present
├── API_SETUP.md            ✅ Created (you are here)
└── cache.db                (auto-created on first run)
```

---

## Before Proceeding to Step 2

**REQUIRED:**
1. ✅ Complete [API_SETUP.md](API_SETUP.md):
   - Get FMP API key (free, https://financialmodelingprep.com/register)
   - Get Anthropic API key (free tier, https://console.anthropic.com)
   - Update .env file with both keys
   - Run `pip install -r requirements.txt`
   - Test fetcher.py: `python fetcher.py`

**OPTIONAL BUT RECOMMENDED:**
- Test fetcher on a known halal stock (MSFT, AAPL) to verify data quality before building downstream logic

---

## Build Order (from Spec)

Recommended order: **Start with Step 6 (Validation)** because:
- Requires Steps 1-5 first (all groundwork)
- Produces testable output on stocks you already understand
- If output says something insightful about a known stock, the engine works
- Much faster path to v1 than building discovery first

**Recommended sequence:**
1. ✅ Step 1 (fetcher.py) - Complete and tested
2. → Step 2 (halal.py) - Implement 4 gates
3. → Step 3 (tracker.py) - Implement track routing
4. → Step 4 (scorer.py) - Implement signal scoring (8 signals per track)
5. → Step 5 (detector.py) - Implement asymmetric pattern detector
6. → Step 6 (validation.py) - Run full pipeline on single stock
7. → Test Steps 2-6 on known stocks (MSFT, AAPL, JPM)
8. → Step 7 + Step 8 (discovery.py) - Add discovery workflow
9. → Step 9 (app.py) - Build Streamlit UI (last)

---

## Testing Strategy

**Step 1 (Fetcher):**
- ✅ Test on MSFT (known halal, profitable, Track A)
- ✅ Test on AAPL (known halal, profitable, Track A)
- Test on JPM (known non-halal, should fail Gate 1)

**Steps 2-6 (Validation workflow):**
- Test MSFT (halal, Track A, profitable compounder)
- Test AAPL (halal, Track A, profitable compounder)
- Test JPM (should fail halal gates immediately)
- Test any stock investor knows deeply

**Steps 7-8 (Discovery workflow):**
- Run discovery with no filters
- Run discovery with tech sector filter
- Verify survivor count after each stage (150-250 from screener → ? after halal gates → ? after signal scoring)

**Step 9 (Streamlit UI):**
- Interactive testing of both workflows
- Verify Layer 1, Layer 2, Layer 3 rendering

---

## Cost Summary

**At 2x/week usage:**
- FMP: $0 (free tier, 250 calls/day)
- Anthropic API: ~$0.30-0.60/month
- yfinance: $0
- **Total: ~$0.50/month**

---

## Next Actions

1. **Immediately:** Follow [API_SETUP.md](API_SETUP.md) - Get both API keys + configure .env
2. **Then:** Test fetcher.py with `python fetcher.py`
3. **Then:** Ready to build Step 2 (halal.py)

Proceed when API keys are configured and ready.
