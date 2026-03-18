## 🚀 QUICKSTART GUIDE

Complete Halal Asymmetric Stock Finder - Ready to Deploy

###  1️⃣ Initial Setup (One-time)

```bash
# Navigate to project directory
cd "c:\Users\qurra\OneDrive\Desktop\Code\Assymetric_Stock_Finder"

# Activate virtual environment
.venv\Scripts\activate

# Install all required packages
pip install yfinance requests python-dotenv anthropic streamlit plotly pandas
```

### 2️⃣ API Configuration

Create/update `.env` file in the project root:

```
FMP_API_KEY=your_fmp_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

**Getting API Keys:**
- **yfinance**: No key needed ✓ (free)
- **FMP**: Sign up at https://financialmodelingprep.com (free tier: 250 calls/day)
- **Anthropic**: Get key from https://console.anthropic.com (pay-as-you-go, ~$0.50/month light usage)

### 3️⃣ Run Complete Pipeline

```bash
# Run full discovery (10-15 minutes on first run)
python discovery.py

# View results
python show_discovery_results.py
```

**Output:** `discovery_results.json` with top 5-10 candidates ranked by asymmetry score

### 4️⃣ Launch Interactive Dashboard

```bash
# Start Streamlit web interface
streamlit run streamlit_app.py
```

Opens at: **http://localhost:8502**

#### Dashboard Features:
- **📊 Dashboard Tab**: Top 5 candidates with summary statistics
- **📋 Top 5 Analysis**: Deep dive into each candidate
  - Halal compliance gates
  - Track analysis (A/B/A-Transition)
  - Signal scoring breakdown
  - Asymmetric pattern components
  - **🤖 Claude AI Analysis**: Plain English explanations
- **🔍 Search Tab**: Analyze ANY stock ticker
  - Type any stock symbol (MSFT, AAPL, JPM, etc.)
  - Get instant asymmetric pattern analysis
  - See halal screening results
  - View AI reasoning for investment decision

---

## � Managing Stock Universe (Quarterly)

The system screens a **static list of 30+ stocks** by design. This gives you:
- ✅ Reproducible, consistent results
- ✅ Control over which stocks are analyzed
- ✅ Ability to track performance of your watchlist

**Every 3 months:** Review and update the universe:

### Step 1: Open screener.py
```
c:\Users\qurra\OneDrive\Desktop\Code\Assymetric_Stock_Finder\screener.py
```

### Step 2: Find SAMPLE_UNIVERSE (around line 40)
```python
SAMPLE_UNIVERSE = [
    # Small software/SaaS stocks
    'NSTG', 'AKAM', 'JKHY', 'BOOM', 'VRNA', 'SANA', 'INTA', 'VEEV', 'MNST', 'FTNT',
    # etc...
]
```

### Step 3: Make Quarterly Updates
- **Remove:** Stocks that failed halal gates or degraded fundamentals
- **Add:** New stocks from your watchlist or research
- **Replace:** Dead/delisted companies with new candidates

**Example update (April 1):**
```python
# Remove OLDSTOCK (failed halal)
# Add MSFT, AAPL (new interests)
# Keep: INTA, CRUS, ACIW (performed well last quarter)
```

### Step 4: Save and re-run discovery
```bash
python discovery.py  # Screens updated universe
streamlit run streamlit_app.py  # View fresh results
```

**Note:** Universe stays static between quarters. This is intentional - you control what gets screened.

---

## �🔄 Automatic Updates (PythonAnywhere)

Want automated biweekly discovery runs with email updates? See **PYTHONANYWHERE_SETUP.md**

**Quick summary:**
1. Upload files to PythonAnywhere
2. Set up scheduled task (every 14 days)
3. Configure email credentials
4. Receive results automatically every 2 weeks

Example email includes:
- Top 5 candidates with scores
- Pattern types (Full/Partial/None)
- Halal compliance status
- Signal performance

### 📥 After Biweekly Scheduler Runs

Once PythonAnywhere scheduler has run (you'll get an email notification):

1. Go to **PythonAnywhere Files** → `halal_stock_finder` folder
2. Download `discovery_checkpoint.db` file
3. Replace your local copy:
   ```
   c:\Users\qurra\OneDrive\Desktop\Code\Assymetric_Stock_Finder\discovery_checkpoint.db
   ```
4. Launch dashboard to see latest results:
   ```bash
   streamlit run streamlit_app.py
   ```

Dashboard will now show the **latest biweekly candidates** instead of old results.

---

## 🎯 Basic Usage

### Option A: Manual Discovery Run
```bash
python discovery.py          # Scans 15 candidates (~10 min)
streamlit run streamlit_app.py  # View results in dashboard
```

### Option B: Analyze Single Stock
1. Open Streamlit dashboard
2. Click **🔍 Search Stock** tab
3. Enter ticker (e.g., TSLA, META, AMZN)
4. View instant analysis + Claude AI reasoning

### Option C: Automated (PythonAnywhere)
1. Follow **PYTHONANYWHERE_SETUP.md**
2. Results delivered to email every 2 weeks
3. Dashboard updates automatically

Opens at: **http://localhost:8501** 

Dashboard shows:
- Summary cards (top candidates)
- Full candidate table with filtering  
- Signal heatmaps (green/yellow/red)
- Individual candidate deep dives

### 5️⃣ AI Deep Reasoning (Optional)

```bash
# Analyze top 5 candidates with Claude AI
python test_ai_reasoner.py
```

Provides Claude-generated investment theses for top candidates

---

## 📊 Understanding the Pipeline

### Data Flow:
```
fetcher.py (yfinance + FMP)
    ↓
halal.py (4 gates: riba, debt, haram revenue, loss financing)
    ↓
tracker.py (classify: Track A / A-Transition / B)
    ↓
scorer.py (16 signals: evaluate track-specific opportunities)
    ↓
detector.py (3-component asymmetric pattern: floor + mispricing + catalyst)
    ↓
validation.py (single-stock 5-stage pipeline)
    ↓
screener.py (universe pre-filter: 2000 → 15 qualified candidates)
    ↓
discovery.py (validate all 15, rank by composite score)
    ↓
streamlit_app.py (interactive dashboard)
    ↓
ai_reasoner.py (Claude analysis of top 5)
```

### Key Concepts:

**Halal Compliance (4 Gates):**
1. **Gate 1**: No riba (interest-based) sectors (banks, conventional finance)
2. **Gate 2**: Total debt < 33% of market cap
3. **Gate 3**: Haram revenue < 5% (alcohol, tobacco, weapons, etc.)
4. **Gate 4**: Loss financing must be equity-funded (Track B only)

**Track Classification:**
- **Track A**: Profitable compounder (4+ of 5 years FCF positive)
- **Track A-Transition**: Was profitable, now struggling (watch for turnaround)
- **Track B**: Investment-phase growth (3+ of 5 years FCF negative)

**Asymmetric Pattern (3 Components):**
- **Floor**: Downside protection (net cash > 10% market cap OR EV/FCF cheap OR ROIC > 18%)
- **Mispricing**: Market wrong about company (valuation metrics significantly below average)
- **Catalyst**: Re-rating trigger (insider buying, operating leverage improving, ROIC trending up)

**Scoring:**
- Composite = 60% asymmetry + 40% signals
- Asymmetry: Full (3.0) → Partial (1.5) → None (0.0)
- Signals: 0-3.0 based on track-specific signal score / threshold

---

## 📁 File Structure

```
Assymetric_Stock_Finder/
├── fetcher.py                 # Data fetching (yfinance + FMP)
├── halal.py                   # Halal compliance gates
├── tracker.py                 # Track routing
├── scorer.py                  # Signal scoring engine
├── detector.py                # Asymmetric pattern detection
├── validation.py              # Single-stock 5-stage pipeline
├── screener.py                # Universe pre-screener
├── discovery.py               # Multi-stock discovery + ranking
├── ai_reasoner.py             # Claude AI analysis
├── streamlit_app.py           # Web dashboard
├── show_discovery_results.py  # Results loader/formatter
├── cache.db                   # SQLite cache (yfinance data, auto-managed)
├── discovery_checkpoint.db    # SQLite checkpoint (validation results)
├── discovery_results.json     # Top candidates ranked
└── screening_results.json     # Screener universe output
```

---

## 🎯 Example Output

```
================================================================================
✅ DISCOVERY RESULTS - TOP OPPORTUNITIES
================================================================================

✓ Found 10 qualifying candidates (halal + viable track)

#1. INTA | Score: 3.00
    Asymmetry: 3.0 (FULL)
    Signals: 16/24 (3.0)
    Track: A | Halal: UNVERIFIED
    Conviction: LOW

#2. CRUS | Score: 2.92
    Asymmetry: 3.0 (FULL)
    Signals: 15/24 (2.8)
    Track: A | Halal: UNVERIFIED
    Conviction: LOW

#3. ACIW | Score: 2.85
    Asymmetry: 3.0 (FULL)
    Signals: 14/24 (2.6)
    Track: A | Halal: UNVERIFIED
    Conviction: LOW
```

---

## ⚠️ Important Notes

### API Limitations:
- **FMP Free Tier**: 250 calls/day limit (screener, profile, segments, insider blocked at 403)
- **Workaround**: Switched to yfinance for sector & financial data (free, no throttling)
- **Anthropic**: Pay-per-token model (~$0.003 per 1K input tokens)

### Data Quality:
- Some stocks may have incomplete data (missing segments, insider data flagged as "unverified")
- These still pass through pipeline with "UNVERIFIED" status (analyst should review)
- Pipeline is designed to be forgiving - better to analyze with partial data than reject

### Performance:
- **First run**: 10-15 minutes (network requests to yfinance)
- **Subsequent runs**: 30 seconds (cached locally for 7 days)
- **Discovery on 15 candidates**: ~45 seconds (cached yfinance data)

### Customization:

**Change universe size:**
```python
# In screener.py, modify SAMPLE_UNIVERSE list
SAMPLE_UNIVERSE = ['TICKER1', 'TICKER2', ...]  # Add/remove tickers
```

**Change market cap range:**
```python
# In screener.py, adjust MARKET_CAP_MIN/MAX
MARKET_CAP_MIN = 500_000_000  # $500M
MARKET_CAP_MAX = 20_000_000_000  # $20B
```

**Adjust signal thresholds:**
```python
# In scorer.py, modify score_track_a() and score_track_b()
# Change condition thresholds for each signal
```

---

## 🐛 Common Issues & Fixes

**Issue:** "No API key found"
- **Fix:** Verify `.env` file exists in project root with `FMP_API_KEY` and `ANTHROPIC_API_KEY`

**Issue:** "ModuleNotFoundError: No module named 'yfinance'"
- **Fix:** Run `pip install yfinance requests python-dotenv anthropic streamlit plotly pandas`

**Issue:** "Cache database locked"
- **Fix:** Delete `cache.db` and restart (will rebuild cache on next run)

**Issue:** "No candidates found after screening"
- **Fix:** Check if SAMPLE_UNIVERSE has correct ticker symbols; expand market cap range

**Issue:** Streamlit "Module not found: _streamlit_components"
- **Fix:** Run `pip install --upgrade streamlit`

---

## 📖 For Developers

### Adding Custom Signal:
1. Add method to SignalScorer class in `scorer.py`
2. Call method from `score_track_a()` or `score_track_b()`
3. Return dict with `{score: 1-3, value: numeric, reason: str}`

### Adding Custom Halal Gate:
1. Add method to HalalGateEngine class in `halal.py`
2. Call from `evaluate_all_gates()` 
3. Return dict with `{status: pass/fail/unverified, reason: str}`

### Extending Discovery:
1. Modify `SAMPLE_UNIVERSE` and filters in `screener.py`
2. Update `DiscoveryWorkflow.discover()` to run additional stages
3. Add ranking criteria in `_rank_candidates()`

---

## 📞 Support

- **yfinance issues**: https://github.com/ranaroussi/yfinance
- **FMP API docs**: https://financialmodelingprep.com/developer/docs
- **Anthropic API docs**: https://docs.anthropic.com
- **Streamlit docs**: https://docs.streamlit.io

**Contact investment methodology:**
This system is based on Islamic-compliant value investing principles with asymmetric risk/reward focus. For questions on halal compliance, consult a Shariah advisor.

---

**Last Updated:** March 15, 2026
**Status:** ✅ Fully Operational (Steps 1-9 Complete)
