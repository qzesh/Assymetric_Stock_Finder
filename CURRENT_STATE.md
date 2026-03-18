# Halal Asymmetric Stock Finder - Current Build State

## 📊 Project Status

### ✅ Step 1: Data Fetcher Module (Complete)
**File:** `fetcher.py` (500+ lines, fully functional)

**What's Done:**
- SQLite cache system (financial_data, price_data, ai_reasoning tables)
- yfinance integration (income statements, balance sheets, cashflow, quotes, price history)
- FMP free tier integration (screener, insider transactions, revenue segments, company profiles)
- Unified data structures normalized from both sources
- Full error handling, retries, rate limit awareness
- Logging system for monitoring data quality

**Can Already Do:**
```python
from fetcher import get_full_stock_data
data = get_full_stock_data("MSFT")
# Returns: {financial: {...}, price: {...}} with all statements + quotes
```

---

## 🔴 Steps 2-9: Still to Build

| Step | Module | Purpose | Status |
|------|--------|---------|--------|
| 2 | halal.py | 4 halal compliance gates | ❌ Not started |
| 3 | tracker.py | Track A / A-Transition / B routing | ❌ Not started |
| 4 | scorer.py | 8-signal scoring engine | ❌ Not started |
| 5 | detector.py | Asymmetric pattern detector | ❌ Not started |
| 6 | validation.py | Single-stock validation workflow | ❌ Not started |
| 8 | discovery.py | Multi-stock discovery workflow (6 stages) | ❌ Not started |
| 9 | app.py | Streamlit web UI (build last) | ❌ Not started |

---

## 📋 Immediate Next Steps (DO THIS FIRST)

### 1. **Get API Keys** (5-10 minutes)
Follow the detailed guide in [API_SETUP.md](API_SETUP.md):

**FMP_API_KEY:**
- Go to https://financialmodelingprep.com/register
- Sign up (free, no credit card)
- Copy your API key from Dashboard
- 250 calls/day limit (enough for 2x/week usage)

**ANTHROPIC_API_KEY:**
- Go to https://console.anthropic.com
- Sign up with email + password (free account)
- Add a credit card for payment (only charged for usage)
- Create API key in "API Keys" section
- Cost: ~$0.50/month at 2x/week usage

### 2. **Update .env File** (30 seconds)
```bash
# Edit .env in your project folder
FMP_API_KEY=abc123defg456hij789klmno
ANTHROPIC_API_KEY=sk-ant-v1-xyz789...
```

### 3. **Install Dependencies** (1-2 minutes)
```bash
pip install -r requirements.txt
```

### 4. **Test Fetcher** (2-3 minutes)
```bash
python fetcher.py
```
Should return full JSON of MSFT financial data (income, balance, cashflow, quotes, etc).

---

## 📁 File Overview

```
Assymetric_Stock_Finder/
│
├── 📋 API_SETUP.md                    ← READ THIS FIRST (step-by-step API guide)
├── 📋 BUILD_STATUS.md                 ← Detailed build progress + testing strategy
├── 📕 README.md                       ← Original project README
│
├── ✅ fetcher.py                      ← Step 1: Data fetching (COMPLETE)
│                                        Handles yfinance + FMP API calls
│                                        Caches results to SQLite
│
├── ❌ halal.py                        ← Step 2: Halal gates (TO BUILD)
├── ❌ tracker.py                      ← Step 3: Track routing (TO BUILD)
├── ❌ scorer.py                       ← Step 4: Signal scoring (TO BUILD)
├── ❌ detector.py                     ← Step 5: Pattern detection (TO BUILD)
├── ❌ validation.py                   ← Step 6: Single-stock validation (TO BUILD)
├── ❌ discovery.py                    ← Step 8: Multi-stock discovery (TO BUILD)
├── ❌ app.py                          ← Step 9: Streamlit UI (TO BUILD LAST)
│
├── ⚙️ .env                            ← Configuration (API keys - update with yours)
├── 📄 requirements.txt                ← Python dependencies (all listed)
├── 📄 .gitignore                      ← Git ignore rules (.env is excluded)
│
└── 🔄 cache.db                        ← Auto-created (SQLite cache, ~100KB)
```

---

## 🎯 Architecture Overview (From Spec)

**Two Jobs:**
1. **Discovery** - Find new halal stocks with asymmetric upside via pre-screen + signals + AI
2. **Validation** - Stress-test your own stock picks

**Two Evaluation Tracks:**
- **Track A** - Profitable compounders (FCF positive 4+ of last 5 years)
- **Track B** - Investment-phase compounders (FCF negative 3+ of last 5 years, reinvesting)

**Four Halal Gates:**
1. Riba model (auto-fail: Banks, Finance, Insurance)
2. Debt ratio < 33% (30-day avg market cap basis)
3. Haram revenue < 5% (alcohol, tobacco, weapons, etc)
4. Loss financing = equity-funded (Track B only)

**Asymmetric Pattern (All 3 Required):**
1. **Floor** - Downside protection (net cash, cheap valuation, high ROIC)
2. **Mispricing** - Market is wrong (trough signal, punished fundamentals)
3. **Catalyst** - Path to re-rating (insider buying, operating leverage, breakeven approaching)

**Signal Scoring:**
- Track A: 8 signals × 3-point scale = 24 max score (need 16+ to pass)
- Track B: 8 signals × 3-point scale = 24 max score (need 14+ to pass)

**AI Layer:**
- Claude (Sonnet 4.5 for testing, Opus 4.5 for final decisions)
- Web search enabled (recent earnings calls + news)
- 11-field structured JSON output
- Web search enabled (earnings calls + recent news)

---

## 💰 Cost Summary

| Service  | Price | Details |
|----------|-------|---------|
| FMP Free | $0 | 250 API calls/day (sufficient for 2x/week) |
| Anthropic | $0.30-0.60/month | Claude API (2x/week AI reasoning) |
| yfinance | $0 | Unlimited, no API key |
| **Total** | **~$0.50/month** | Essentially free for personal use |

---

## ✅ What You Need to Do NOW

1. **Read:** [API_SETUP.md](API_SETUP.md) (5 min)
2. **Register:** FMP free API + Anthropic API (10 min)
3. **Configure:** Update `.env` with your keys (30 sec)
4. **Install:** `pip install -r requirements.txt` (2 min)
5. **Test:** `python fetcher.py` (3 min)

**Total: 20 minutes to get ready.**

Once done, you can:
- ✅ Fetch financial data for any stock automatically
- →  Build Steps 2-6 (validation workflow)
- →  Test on stocks you know well (MSFT, AAPL, your portfolio holdings)

---

## 🚀 Ready to Start?

1. **First priority:** Follow [API_SETUP.md](API_SETUP.md)
2. **Reference:** [BUILD_STATUS.md](BUILD_STATUS.md) for detailed build path
3. **Data:** Check out fetcher.py - all data pulling is done (Steps 2-5 build on top of this)

Questions? Check the specification document for signal explanations, calculation logic, or output formats.
