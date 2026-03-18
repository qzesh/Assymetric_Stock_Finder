# Halal Asymmetric Stock Finder

A sophisticated AI-powered investment discovery system that identifies halal stocks with asymmetric upside potential using financial analysis and Claude AI reasoning.

## Features

✨ **Core Capabilities**
- **Halal Screening**: 4-gate Islamic compliance system (riba, debt, haram revenue, financing)
- **Asymmetric Detection**: Identifies stocks with downside protection + mispricing + clear catalysts
- **Signal Scoring**: 16 technical & fundamental signals for validation
- **Track Routing**: Auto-classifies into Track A (clean) or Track B (modified)
- **AI Analysis**: Claude AI provides plain-English investment theses
- **Streamlit Dashboard**: Interactive web interface with mobile support

## Quick Start

### Prerequisites
- Python 3.10+
- API Keys (free/cheap):
  - [Anthropic Claude](https://console.anthropic.com) - AI analysis (~$0.04/month)
  - [Financial Modeling Prep](https://financialmodelingprep.com) - Financial data (free tier: 250 calls/day)

### Local Installation

```bash
# Clone repo
git clone https://github.com/YOUR_USERNAME/Assymetric_Stock_Finder.git
cd Assymetric_Stock_Finder

# Create virtual environment
python -m venv venv
source venv/Scripts/activate  # Windows
# or
source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Set up API keys
# Copy .streamlit/secrets.toml.example to .streamlit/secrets.toml
# Add your actual API keys

# Run the app
streamlit run streamlit_app.py
```

### Deploy to Streamlit Cloud

1. Push code to GitHub
2. Go to https://streamlit.io/cloud
3. Connect your GitHub repo
4. Add secrets in the web interface:
   - `ANTHROPIC_API_KEY`
   - `FMP_API_KEY`
5. Get your public URL

## Architecture

```
Assymetric_Stock_Finder/
├── fetcher.py           # Data collection (yfinance + FMP API)
├── halal.py             # Islamic compliance screening
├── tracker.py           # Track A/B routing
├── scorer.py            # Signal scoring (16 signals)
├── detector.py          # Asymmetric pattern detection
├── validation.py        # Single-stock validation pipeline
├── screener.py          # Pre-screen 2000+ candidates
├── discovery.py         # Multi-stock discovery workflow
├── ai_reasoner.py       # Claude AI analysis
├── streamlit_app.py     # Web dashboard
└── requirements.txt     # Python dependencies
```

## Usage

### Search Individual Stock
1. Open the Streamlit app
2. Go to "Search" tab
3. Enter ticker symbol (e.g., AAPL, TESLA)
4. View:
   - Halal screening status
   - Track classification
   - Signal scores
   - Asymmetric pattern analysis
   - Claude AI investment thesis

### Run Full Discovery
```bash
python discovery.py          # Screen all candidates, produces results
python show_discovery_results.py  # Display top 5-10 candidates
```

## Pricing

**Claude AI Analysis**
- Sonnet 4.6: ~$400 input / ~$1500 output tokens (per 1M)
- Typical analysis: ~380 input + 270 output = ~$0.005 per request
- Monthly cost (2x/week): ~$0.04

**Financial Data**
- yfinance: Free (no key needed)
- FMP: Free tier (250 calls/day)

**Hosting**
- Streamlit Cloud: Free
- Custom server: ~$5-10/month

## Key Metrics

- **Asymmetric Pattern**: Full (3 components) / Partial (2) / None (1)
- **Signal Score**: 0-24 scale (16+ = strong conviction)
- **Track Type**: A (clean), B (modified), A-Transition
- **Confidence**: Halal status + pattern quality

## Files

| File | Purpose |
|------|---------|
| `fetcher.py` | Unified data source (yfinance + FMP) |
| `halal.py` | 4-gate halal compliance |
| `tracker.py` | Track A/B classification |
| `scorer.py` | 16-signal scoring engine |
| `detector.py` | Asymmetric pattern detection |
| `validation.py` | End-to-end validation |
| `screener.py` | Pre-screen 2000+ candidates |
| `discovery.py` | Multi-stock discovery |
| `ai_reasoner.py` | Claude AI integration |
| `streamlit_app.py` | Web dashboard |

## Configuration

Create `.streamlit/secrets.toml`:
```toml
ANTHROPIC_API_KEY = "sk-ant-..."
FMP_API_KEY = "VV9l95p..."
```

## Mobile Support

App is fully responsive for iPhone/Android:
- Auto-collapsing sidebar
- Touch-friendly buttons
- Optimized font sizes
- Single-column layout on small screens

## Roadmap

- [ ] Advanced filtering/sorting
- [ ] Portfolio tracking
- [ ] Email alerts
- [ ] Historical backtest
- [ ] Additional data sources

## Support

See `API_SETUP.md`, `QUICKSTART.md`, `APP_USAGE.md` for detailed guides.

## License

Private use

---

**Built with**: Python • Streamlit • Anthropic Claude • yfinance • FMP API
