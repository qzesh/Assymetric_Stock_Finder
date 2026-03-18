# 📱 How to Use the Halal Asymmetric Stock Finder App

Complete guide to using the Streamlit dashboard and analyzing stocks.

---

## 🚀 Quick Start

### Launch the App
```bash
cd "c:\Users\qurra\OneDrive\Desktop\Code\Assymetric_Stock_Finder"
streamlit run streamlit_app.py
```

Opens at: **http://localhost:8503**

---

## 📊 Dashboard Tab

**What you see:** Top 5 asymmetric opportunities ranked by score

### Key Metrics
| Metric | Meaning |
|--------|---------|
| **Score** | Composite (0-3.0 scale): 60% asymmetry + 40% signals |
| **Pattern** | FULL ✓ (3/3 components) / PARTIAL ◐ (2/3) / NONE ✗ (0-1/3) |
| **Track** | A (Profitable) / B (Growth) / A-Transition (Was A, now declining) |
| **Signals** | X/24 score (16+ = PASS for Track A, 14+ = PASS for Track B) |
| **Halal** | UNVERIFIED (needs review) / PASS (compliant) / FAIL (non-compliant) |

### Features
- **Summary Cards:** Total candidates, full/partial patterns, strong signals
- **Top 5 Table:** Ranked by score with sorting/filtering
- **Charts:**
  - Pattern distribution (pie chart)
  - Track distribution (bar chart)
- **Full Candidate List:** All results with detailed metrics

### Actions
- Click **Details** button on any candidate → See deep analysis

---

## 🔍 Search Stock Tab

**What it does:** Analyze ANY stock ticker instantly for asymmetric potential

### Step By Step

1. **Type Stock Ticker**
   - Example: MSFT, AAPL, TSLA, AMZN, etc.
   - Enter in search box

2. **Click "🔍 Analyze"** 
   - App will fetch data
   - Run validation (5 stages)
   - Generate analysis

3. **View Results:**

   **Metrics Bar (Top):**
   - Halal Status (🟢 Unverified / 🔴 Fail)
   - Track Type (A, B, A-Transition)
   - Signals Score (X/24)
   - Asymmetric Pattern (✅ Full / ⚠️ Partial / ❌ None)

   **Halal Screening Section:**
   - Green box = Passes halal gates
   - Red box = Fails one or more gates
   - Explains each gate result

   **Track Classification:**
   - A = Profitable company with strong FCF
   - B = High-growth company (investing heavily, negative FCF)
   - A-Transition = Was profitable, now declining (red flag)

   **Signal Analysis:**
   - Table of 16 signals
   - Each signal scored 1-3 (green/yellow/red)
   - Shows reason for each score

   **Asymmetric Pattern Analysis:**
   - 3 components checked:
     - **Floor** = Downside protection (2+ ways stock can't fall far)
     - **Mispricing** = Market is undervaluing the company
     - **Catalyst** = Trigger for re-rating when market fixes price
   - FULL (3/3) = High conviction
   - PARTIAL (2/3) = Medium conviction
   - None (0-1/3) = Lower conviction

   **AI Analysis (Layman Terms):**
   - Investment Thesis: Is it compelling? Why/why not?
   - Key Risks: Operational/financial risks
   - Catalyst Timeline: When might upside happen? (12-24 months typical)
   - Conviction Level: 1-10 score based ONLY on asymmetry
   - Recommendation: BUY/HOLD/PASS based ONLY on pattern quality

---

## 📋 Top 5 Analysis Tab

**What it does:** Deep dive into each of top 5 candidates from dashboard

### How to Use

1. Click **"📋 Top 5 Analysis"** in sidebar
2. Select candidate from dropdown (INTA, CRUS, ACIW, GTLB, TMDX)
3. View same detailed analysis as "Search Stock" tab

---

## 💡 Understanding the Analysis

### Asymmetric Pattern Explained

A stock has all 3 components = **FULL ASYMMETRIC** (best opportunity):

```
Example: $100 stock with FULL asymmetric pattern

Floor = Worst case scenario is $80 (20% downside)
  Due to: Book value, dividend yield, breakup value, etc.

Mispricing = Market has undervalued the company
  Reason: Market missing earnings recovery, sector rotation, etc.

Catalyst = Trigger for stock to go to $180 (80% upside)
  Timeline: 12-24 months
  Trigger: New product launch, management change, etc.

RISK/REWARD: Risk $20, make $80 = 4:1 ratio (EXCELLENT)
```

### Track Meanings

**Track A (Profitable Compounder)**
- ✅ Strong FCF generation (4+ positive years out of 5)
- ✅ Growing without excessive borrowing
- ✅ Reinvests profits into business
- ⚠️ Higher valuation expected

**Track B (Growth Investor)**
- 📈 Losing money or minimal profits
- 💰 Investing heavily in growth (R&D, capex)
- 📊 Metrics: Revenue growth, runway, margin expansion
- ⚠️ Riskier but higher upside potential

**Track A-Transition (Disruption Signal)**
- 🚨 Was profitable Track A, now FCF negative
- ⚠️ Could indicate: Disruption, poor execution, or temporary setback
- 🔍 Needs deep research before investing

### Signal Scoring

**Track A Signals (8):**
- ROIC (Return on invested capital)
- Trend (Is it improving?)
- FCF Consistency (How stable?)
- Reinvestment (Buying assets, not shareholders)
- Trough (Bottom of valuation cycle?)
- Valuation (EV/FCF cheap?)
- Insider Ownership (Skin in game?)
- Net Cash (Less debt = safer floor)

**Track B Signals (8):**
- Gross Margin (Unit economics)
- Revenue Growth (Is it accelerating?)
- R&D/Capex (Investing enough?)
- Leverage (Not overleveraged?)
- GP Growth (Gross profit expanding?)
- Runway (How long to profitability?)
- Insider Ownership (Founder committed?)
- Debt Structure (Friendly terms?)

**Scoring:**
- 🟢 **3** = Excellent (best quartile)
- 🟡 **2** = Good (middle quartiles)
- 🔴 **1** = Weak (bottom quartile)

---

## 🎯 Common Use Cases

### I want to find asymmetric opportunities
**→ Use Dashboard tab**
- See top 5 pre-screened candidates
- They've passed halal + have asymmetry
- Click Details for deep dive

### I know a stock and want to check it
**→ Use Search Stock tab**
- Type ticker (AMZN, NVDA, etc.)
- Get instant analysis
- See if it's asymmetric
- Check halal status separately

### I want to monitor specific stocks
**→ Use Search Stock tab repeatedly**
- Search each ticker you're interested in
- Get fresh analysis each time
- No need to run discovery.py

### I want AI's opinion
**→ Check AI Analysis section**
- Shows investment thesis (plain English)
- Lists actual financial risks
- Gives conviction level (1-10)
- Recommends BUY/HOLD/PASS
- **Note:** Recommendation based ONLY on asymmetry quality, not halal status

---

## ⚠️ Important Notes

### Halal Status vs. Asymmetry
- **Halal Status:** Separate screening (riba-free, <33% debt, etc.)
- **Asymmetry:** Investment opportunity analysis
- **You must decide:** Are you willing to invest in this particular stock given its halal status?

### What This App DOES
✅ Find asymmetric risk/reward opportunities  
✅ Score financial signals  
✅ Provide AI investment reasoning  
✅ Separate halal screening  
✅ Search any stock instantly  

### What This App DOES NOT DO
❌ Make investment decisions for you  
❌ Replace professional financial advice  
❌ Guarantee returns  
❌ Tell you whether to buy/hold/sell  
❌ Factor in portfolio diversification  

---

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| App won't launch | Run: `pip install --upgrade streamlit` |
| Stock not found | Verify ticker is correct (e.g., MSFT not MICROSFT) |
| No AI analysis | Check ANTHROPIC_API_KEY in .env file |
| Slow performance | First run caches data (7 days), subsequent runs are faster |
| Pattern says "NONE" | Stock doesn't have all 3 asymmetry components |

---

## 📚 Related Files

- **QUICKSTART.md** - Initial setup guide
- **PYTHONANYWHERE_SETUP.md** - Automated biweekly runs
- **API_SETUP.md** - How to get API keys
- **PROJECT_COMPLETION.md** - Full system documentation

---

## 🎓 Example Workflow

```
1. Open app: streamlit run streamlit_app.py

2. Check Dashboard
   → See INTA has score 3.00 with FULL asymmetry
   → Click Details

3. Review Analysis
   → Investment thesis looks good
   → Check halal status: UNVERIFIED
   
4. Research Further
   → Use Search Tab to verify specifics
   → Check halal compliance yourself (sector, debt, etc.)
   
5. Make Decision
   → If halal ✓ + asymmetry ✓ → Consider investing
   → If halal ✗ → Skip regardless of opportunity
   → If asymmetry weak → No conviction
```

---

**Happy investing! 🚀**
