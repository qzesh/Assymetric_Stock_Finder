"""
Step 9: Streamlit Web UI

Purpose: Interactive dashboard for discovery results
Features:
- Summary cards (top candidates, stats)
- Full reasoning from AI layer
- Interactive tables with filtering
- Signal heatmaps (green/yellow/red)
- Detailed analysis pages
- Individual stock search
- Claude AI reasoning in layman terms

Run with: streamlit run streamlit_app.py
"""

import streamlit as st
import pandas as pd
import json
import sqlite3
import subprocess
import sys
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from validation import ValidationWorkflow
from halal_cache import HalalStatusCache

# Initialize halal cache for 30-day caching
halal_cache_manager = HalalStatusCache()

# Try to import AI reasoner (optional)
try:
    from ai_reasoner import AIReasoningEngine
    CLAUDE_AVAILABLE = True
except ImportError as e:
    print(f"❌ Failed to import AIReasoningEngine: {e}")
    CLAUDE_AVAILABLE = False
except ValueError as e:
    print(f"❌ API Key issue in AIReasoningEngine: {e}")
    CLAUDE_AVAILABLE = False
except Exception as e:
    print(f"❌ Unexpected error loading Claude: {e}")
    CLAUDE_AVAILABLE = False

# Page config
st.set_page_config(
    page_title="Halal Asymmetric Stock Finder",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="auto",  # Auto-collapse sidebar on mobile
    menu_items={
        'Get Help': 'https://github.com',
        'Report a bug': None,
        'About': "Asymmetric Stock Finder - Find halal stocks with upside potential"
    }
)

# PWA Support - Add manifest and service worker
st.markdown("""
<link rel="manifest" href="manifest.json">
<meta name="theme-color" content="#00a8ff">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Stock Finder">
<script>
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('service-worker.js').catch(err => console.log('SW registration failed:', err));
}
</script>
""", unsafe_allow_html=True)

# Modern Dark Theme CSS - Jet Black Edition
st.markdown("""
<style>
    /* Global Styles */
    :root {
        --primary-bg: #0a0e13;
        --secondary-bg: #121821;
        --tertiary-bg: #1a2332;
        --accent-blue: #00a8ff;
        --accent-purple: #7c3aed;
        --accent-green: #10b981;
        --accent-red: #ef4444;
        --text-primary: #ffffff;
        --text-secondary: #b0b8c1;
        --border-color: #1f2937;
    }
    
    /* Main Background - Pure Jet Black */
    .stApp {
        background: #0a0e13;
        color: #f0f1f3;
    }
    
    /* Container - Full Width Optimization */
    .main {
        max-width: 100%;
        padding: 0 !important;
    }
    
    /* Block Container */
    [data-testid="stForm"], 
    [data-testid="stVerticalBlock"] > [data-testid="column"] {
        width: 100% !important;
    }
    
    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    
    h1 {
        background: linear-gradient(135deg, #00a8ff 0%, #7c3aed 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem !important;
        margin-bottom: 0.3rem !important;
        padding: 20px 20px 0 20px !important;
    }
    
    h2 {
        color: #ffffff;
        padding: 20px 20px 0 20px !important;
        margin-top: 1.5rem !important;
        border-top: 2px solid #1f2937;
        padding-top: 1.5rem !important;
        padding-bottom: 0rem !important;
        font-size: 1.8rem !important;
    }
    
    h3 {
        color: #ffffff;
        font-size: 1.5rem !important;
    }
    
    h4 {
        color: #ffffff;
        font-size: 1.2rem !important;
    }
    
    p {
        font-size: 1.1rem !important;
        line-height: 1.6 !important;
    }
    
    span, li {
        font-size: 1rem !important;
    }
    
    /* Metric Cards - Large, Touch-Friendly */
    .metric-card {
        background: linear-gradient(135deg, #121821 0%, #1a2332 100%);
        padding: 24px;
        border-radius: 16px;
        color: #f0f1f3;
        border: 1px solid #1f2937;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }
    
    .metric-card:hover {
        border-color: #00a8ff;
        box-shadow: 0 12px 32px rgba(0, 168, 255, 0.2);
        transform: translateY(-4px);
        background: linear-gradient(135deg, #1a2332 0%, #212d3d 100%);
    }
    
    /* Metric values - Large text for mobile */
    [data-testid="stMetricContainer"] {
        background: linear-gradient(135deg, #121821 0%, #1a2332 100%);
        padding: 24px !important;
        border-radius: 16px !important;
        border: 1px solid #1f2937 !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
    }
    
    [data-testid="stMetricContainer"] label {
        font-size: 0.95rem !important;
        color: #b0b8c1 !important;
        margin-bottom: 8px !important;
    }
    
    [data-testid="stMetricContainer"] span {
        font-size: 1.8rem !important;
        color: #ffffff !important;
        font-weight: 700 !important;
    }
    
    /* Pattern Status Boxes - Enhanced for Mobile */
    .full-asymmetric {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(16, 185, 129, 0.08) 100%);
        color: #86efac;
        padding: 16px;
        border-radius: 12px;
        border-left: 5px solid #10b981;
        border: 1px solid rgba(16, 185, 129, 0.4);
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.1);
    }
    
    .partial-asymmetric {
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.2) 0%, rgba(245, 158, 11, 0.08) 100%);
        color: #fcd34d;
        padding: 16px;
        border-radius: 12px;
        border-left: 5px solid #f59e0b;
        border: 1px solid rgba(245, 158, 11, 0.4);
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 12px rgba(245, 158, 11, 0.1);
    }
    
    .not-asymmetric {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.2) 0%, rgba(239, 68, 68, 0.08) 100%);
        color: #fca5a5;
        padding: 16px;
        border-radius: 12px;
        border-left: 5px solid #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.4);
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 12px rgba(239, 68, 68, 0.1);
    }
    
    /* Divider */
    .streamlit-expanderHeader {
        background-color: #121821;
        border: 1px solid #1f2937;
        border-radius: 12px;
    }
    
    /* Data Tables - Jet Black */
    [data-testid="stDataFrame"] {
        background-color: #0a0e13 !important;
        border: 1px solid #1f2937 !important;
        border-radius: 12px !important;
        overflow: hidden;
    }
    
    /* Expanders */
    .streamlit-expanderHeader:hover {
        background-color: #1a2332;
        border-color: #00a8ff;
    }
    
    /* Info boxes */
    [role="alert"] {
        background: linear-gradient(135deg, rgba(0, 168, 255, 0.15) 0%, rgba(124, 58, 237, 0.15) 100%) !important;
        border: 1px solid rgba(0, 168, 255, 0.4) !important;
        border-radius: 12px !important;
        padding: 16px !important;
        color: #93c5fd !important;
        box-shadow: 0 4px 12px rgba(0, 168, 255, 0.1) !important;
    }
    
    /* Success boxes */
    .success-box {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(16, 185, 129, 0.05) 100%);
        border: 1px solid rgba(16, 185, 129, 0.4);
        border-radius: 12px;
        padding: 16px;
        color: #86efac;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.1);
    }
    
    /* Warning boxes */
    .warning-box {
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.15) 0%, rgba(245, 158, 11, 0.05) 100%);
        border: 1px solid rgba(245, 158, 11, 0.4);
        border-radius: 12px;
        padding: 16px;
        color: #fcd34d;
        box-shadow: 0 4px 12px rgba(245, 158, 11, 0.1);
    }
    
    /* Buttons - Larger for Touch */
    .stButton > button {
        background: linear-gradient(135deg, #0099ff 0%, #6366f1 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 14px 28px;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 6px 20px rgba(0, 168, 255, 0.3);
        width: 100% !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 30px rgba(0, 168, 255, 0.5);
        background: linear-gradient(135deg, #00b4ff 0%, #7c7fff 100%);
    }
    
    .stButton > button:active {
        transform: translateY(-1px);
    }
    
    /* Text colors */
    p, span, li {
        color: #e2e8f0;
        font-size: 1.1rem !important;
    }
    
    /* Captions */
    .stCaption {
        color: #94a3b8;
        font-size: 1rem !important;
    }
    
    /* Sidebar text and radio buttons */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0e13 0%, #121821 100%);
        border-right: 1px solid #1f2937;
    }
    
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] span {
        color: #e2e8f0;
        font-size: 1.1rem !important;
    }
    
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        font-size: 1.6rem !important;
        padding: 0 !important;
        margin: 8px 0 !important;
    }
    
    /* Radio buttons bigger */
    [data-testid="stRadio"] label {
        font-size: 1.1rem !important;
    }
    
    /* Links */
    a {
        color: #00a8ff;
        text-decoration: none;
        transition: color 0.2s ease;
    }
    
    a:hover {
        color: #7c3aed;
    }
    
    /* Divider */
    hr {
        border-color: #1f2937 !important;
    }
    
    /* Input Fields - Mobile Friendly */
    input[type="text"],
    input[type="number"],
    input[type="password"],
    textarea,
    select {
        background-color: #121821 !important;
        border: 1px solid #1f2937 !important;
        color: #ffffff !important;
        border-radius: 10px !important;
        padding: 12px !important;
        font-size: 1rem !important;
    }
    
    input[type="text"]:focus,
    input[type="number"]:focus,
    textarea:focus,
    select:focus {
        border-color: #00a8ff !important;
        box-shadow: 0 0 0 3px rgba(0, 168, 255, 0.1) !important;
        background-color: #121821 !important;
    }
    
    /* Mobile Responsiveness - Improved for App Feel */
    @media (max-width: 768px) {
        .stApp {
            background: #0a0e13;
        }
        
        h1 {
            font-size: 2.2rem !important;
            margin-bottom: 0.25rem !important;
            padding: 16px 16px 0 16px !important;
        }
        
        h2 {
            font-size: 1.6rem !important;
            padding: 16px 16px 0 16px !important;
            margin-top: 1.2rem !important;
        }
        
        h3 {
            font-size: 1.3rem !important;
            padding: 0 16px !important;
        }
        
        p {
            font-size: 1.05rem !important;
            padding: 0 16px !important;
            line-height: 1.6 !important;
        }
        
        /* Stack columns full width */
        [data-testid="column"] {
            width: 100% !important;
            max-width: 100% !important;
            padding: 8px !important;
        }
        
        /* Larger touch targets */
        button, input[type="button"], input[type="submit"] {
            padding: 14px 16px !important;
            font-size: 1.05rem !important;
            border-radius: 10px !important;
            min-height: 48px !important;
        }
        
        /* Input fields larger */
        input[type="text"], 
        input[type="number"],
        textarea, 
        select {
            font-size: 1.05rem !important;
            padding: 14px !important;
            min-height: 44px !important;
        }
        
        /* Table responsive */
        table {
            font-size: 0.95rem !important;
        }
        
        /* Metric cards full width */
        [data-testid="stMetricContainer"] {
            width: 100% !important;
            margin: 8px 0 !important;
        }
        
        /* Cards with proper spacing */
        .metric-card {
            padding: 16px !important;
            margin: 8px 0 !important;
            width: 100% !important;
        }
        
        /* Expanders full width */
        .streamlit-expanderHeader {
            border-radius: 10px !important;
        }
        
        /* Top padding for main content */
        [data-testid="stAppViewContainer"] {
            padding-top: 12px !important;
        }
        
        /* Sidebar text bigger on mobile */
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span {
            font-size: 1.1rem !important;
        }
    }
    
    @media (max-width: 480px) {
        h1 {
            font-size: 1.9rem !important;
            padding: 12px 12px 0 12px !important;
        }
        
        h2 {
            font-size: 1.4rem !important;
            padding: 12px 12px 0 12px !important;
            margin-top: 1rem !important;
        }
        
        h3 {
            font-size: 1.2rem !important;
            padding: 0 12px !important;
        }
        
        p {
            font-size: 1rem !important;
            padding: 0 12px !important;
            line-height: 1.5 !important;
        }
        
        /* Ultra-compact cards */
        .metric-card {
            padding: 12px !important;
            margin: 6px 0 !important;
            border-radius: 10px !important;
        }
        
        [data-testid="stMetricContainer"] {
            padding: 12px !important;
            margin: 4px 0 !important;
            border-radius: 10px !important;
        }
        
        [data-testid="stMetricContainer"] span {
            font-size: 1.5rem !important;
        }
        
        [data-testid="stMetricContainer"] label {
            font-size: 0.95rem !important;
        }
        
        /* Full width buttons */
        .stButton > button {
            width: 100% !important;
            padding: 12px 12px !important;
            font-size: 1rem !important;
            min-height: 44px !important;
        }
        
        /* Min column spacing */
        [data-testid="column"] {
            padding: 4px !important;
        }
        
        /* Sidebar narrower */
        [data-testid="stSidebar"] {
            width: 60% !important;
        }
    }
    
    /* Extra small phones */
    @media (max-width: 380px) {
        h1 {
            font-size: 1.7rem !important;
        }
        
        [data-testid="stMetricContainer"] span {
            font-size: 1.3rem !important;
        }
        
        .metric-card {
            padding: 10px !important;
        }
    }
</style>
""", unsafe_allow_html=True)


# =========================================================================
# DATA LOADING
# =========================================================================

@st.cache_data
def load_discovery_results():
    """Load discovery results from JSON."""
    try:
        with open('discovery_results.json') as f:
            return json.load(f)
    except FileNotFoundError:
        return None


@st.cache_data
def load_checkpoint_data(ticker):
    """Load full validation data from checkpoint database."""
    try:
        conn = sqlite3.connect('discovery_checkpoint.db')
        cursor = conn.cursor()
        cursor.execute('SELECT validation_result FROM analysis_results WHERE ticker = ?', (ticker,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return json.loads(result[0])
        return None
    except Exception as e:
        st.error(f"Error loading {ticker}: {str(e)}")
        return None


def get_cached_ai_analysis(ticker):
    """Get cached Claude AI analysis if valid (not expired)."""
    try:
        conn = sqlite3.connect('discovery_checkpoint.db')
        cursor = conn.cursor()
        
        # Query without expiry check in SQL - we'll check in Python
        cursor.execute('''
            SELECT ai_analysis, cached_at, expires_at FROM ai_analysis_cache 
            WHERE ticker = ?
        ''', (ticker,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            ai_analysis_text = result[0]
            cached_at = result[1]
            expires_at_str = result[2]
            
            # Check if cache is still valid (Python-side)
            try:
                expires_at = datetime.fromisoformat(expires_at_str)
                if expires_at > datetime.now():
                    return (ai_analysis_text, cached_at)
                else:
                    return (None, None)  # Cache expired
            except (ValueError, TypeError):
                return (None, None)  # Invalid date format
        
        return (None, None)
    except Exception as e:
        print(f"Error retrieving cached analysis for {ticker}: {e}")
        return (None, None)


def cache_ai_analysis(ticker, analysis_text):
    """Write Claude AI analysis to cache (14-day expiry)."""
    try:
        conn = sqlite3.connect('discovery_checkpoint.db')
        cursor = conn.cursor()
        
        # Ensure table exists (matching discovery.py schema)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_analysis_cache (
                ticker TEXT PRIMARY KEY,
                ai_analysis TEXT,
                cached_at TEXT,
                expires_at TEXT
            )
        ''')
        
        # Calculate expiry date in Python (14 days from now)
        now = datetime.now()
        expires_at = (now + timedelta(days=14)).isoformat()
        
        # Insert or replace the analysis with calculated dates
        cursor.execute('''
            INSERT OR REPLACE INTO ai_analysis_cache (ticker, ai_analysis, cached_at, expires_at)
            VALUES (?, ?, ?, ?)
        ''', (ticker, analysis_text, now.isoformat(), expires_at))
        
        conn.commit()
        conn.close()
        print(f"✅ Cached analysis for {ticker}")
        return True
    except Exception as e:
        print(f"❌ Failed to cache analysis for {ticker}: {e}")
        return False


def get_claude_analysis(ticker, validation_data, force_refresh=False):
    """
    Get Claude AI analysis with caching.
    Cache is valid for 14 days. Set force_refresh=True to bypass cache.
    """
    if not CLAUDE_AVAILABLE:
        st.warning(f"Claude not available - ANTHROPIC_API_KEY may not be set")
        return None, None
    
    # Check cache first (unless force_refresh is True)
    if not force_refresh:
        print(f"🔍 Checking cache for {ticker}...")
        cached_text, cached_at = get_cached_ai_analysis(ticker)
        if cached_text:
            print(f"✅ Found cached analysis for {ticker}")
            # Parse cached text
            try:
                analysis_json = json.loads(cached_text)
                return analysis_json, cached_at
            except json.JSONDecodeError:
                # Try to extract JSON from cached text
                import re
                json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', cached_text, re.DOTALL)
                if json_match:
                    try:
                        analysis_json = json.loads(json_match.group())
                        return analysis_json, cached_at
                    except json.JSONDecodeError:
                        pass
                
                # Return wrapped plaintext
                return {
                    'thesis': cached_text,
                    'risks': 'See analysis above',
                    'catalyst': 'See analysis above',
                    'conviction': 5,
                    'recommendation': 'HOLD'
                }, cached_at
    
    # If no valid cache or force_refresh, call Claude API
    try:
        print(f"🤖 Initializing Claude AI for {ticker}...")
        reasoner = AIReasoningEngine()
        print(f"🤖 Calling Claude API for {ticker}...")
        
        # Use the correct method from AIReasoningEngine
        result = reasoner.analyze_candidate(ticker, validation_data)
        print(f"🤖 Claude API response status: {result.get('status')}")
        
        if result.get('status') == 'success':
            analysis_text = result.get('ai_analysis', '')
            
            # Try to parse as JSON first
            try:
                analysis_json = json.loads(analysis_text)
                return analysis_json, None
            except json.JSONDecodeError:
                # If not valid JSON, try to extract from plain text response
                import re
                json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', analysis_text, re.DOTALL)
                if json_match:
                    try:
                        analysis_json = json.loads(json_match.group())
                        return analysis_json, None
                    except json.JSONDecodeError:
                        pass
                
                # If still no JSON, return plaintext wrapped in a dict
                return {
                    'thesis': analysis_text,
                    'risks': 'See analysis above',
                    'catalyst': 'See analysis above',
                    'conviction': 5,
                    'recommendation': 'HOLD'
                }, None
        else:
            error_msg = result.get('error', 'Unknown error')
            st.error(f"Claude API Error: {error_msg}")
            return None, None
    except Exception as e:
        st.error(f"Exception analyzing {ticker}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None


def run_discovery_workflow():
    """Run the discovery workflow by calling show_discovery_results.py script."""
    try:
        # Run the existing show_discovery_results.py script
        # This loads from discovery_checkpoint.db and saves to discovery_results.json
        result = subprocess.run(
            [sys.executable, 'show_discovery_results.py'],
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )
        
        if result.returncode != 0:
            error_msg = result.stderr or result.stdout or "Unknown error"
            return False, f"Script failed with return code {result.returncode}: {error_msg}"
        
        # Check if discovery_results.json was created/updated
        try:
            with open('discovery_results.json', 'r') as f:
                results = json.load(f)
            
            if not results:
                return False, "Results file is empty"
            
            return True, f"Discovery complete: {len(results)} candidates loaded from checkpoint database"
        
        except FileNotFoundError:
            return False, "Results file not created (discovery_checkpoint.db may be empty)"
        except json.JSONDecodeError:
            return False, "Results file is invalid JSON"
    
    except subprocess.TimeoutExpired:
        return False, "Discovery script timed out after 2 minutes"
    except Exception as e:
        import traceback
        error_msg = f"{str(e)}\n\n{traceback.format_exc()}"
        return False, error_msg


# =========================================================================
# PAGE: HOME / SUMMARY
# =========================================================================

def page_home():
    """Main dashboard with top candidates."""
    
    st.title("Halal Asymmetric Stock Finder")
    st.markdown("*Islamic-compliant value investing with asymmetric patterns*")
    
    # Load results
    results = load_discovery_results()
    
    if not results:
        st.error("No discovery results found. Run discovery.py first.")
        return
    
    # HELP SECTION
    with st.expander("What do these metrics mean?"):
        st.markdown("""
        ### Key Metrics Explained
        
        **Score (0-3.0 scale)**
        - Composite ranking = 60% Asymmetry Quality + 40% Signal Strength
        - Higher score = stronger investment opportunity
        
        **Asymmetric Pattern**
        - **Full Asymmetric**: 3+ components present (Floor + Mispricing + Catalyst)
        - **Partial Asymmetric**: 1-2 components present
        - **No Pattern**: Insufficient asymmetry
        
        **Signals (0-24 scale)**
        - 16 technical & fundamental signals evaluated
        - Higher count = more evidence supporting the pattern
        - Full pattern candidates typically have 18-24 signals
        
        **Track Type**
        - **Track A**: Clean companies (no interest-bearing debt, halal-friendly)
        - **Track B**: Modified structure (some interest-bearing debt, can be acceptable)
        - **Track A-Transition**: Moving toward cleaner structure
        
        **Halal Status**
        - **Pass**: Islamic screening gates approved
        - **Fail**: Interest-based debt or non-compliant structure
        
        ### Chart Meanings
        
        **Asymmetric Pattern Distribution (Pie Chart)**
        - Visual breakdown of how many candidates have Full/Partial/None patterns
        - Goal: Find companies with Full asymmetric potential
        
        **Track Distribution (Bar Chart)**
        - How many candidates fall into each halal track category
        - Shows compliance profile of screened universe
        """)
    
    st.divider()
    
    # SUMMARY METRICS & STATISTICS - FULL-WIDTH OPTIMIZED LAYOUT
    st.header("Discovery Summary")
    
    # Calculate metrics upfront
    total_candidates = len(results)
    full_asymmetric = sum(1 for r in results if r['pattern'] == 'full')
    partial_asymmetric = sum(1 for r in results if r['pattern'] == 'partial')
    passed_signals = sum(1 for r in results if r['signal_raw'] >= r.get('signal_threshold', 16))
    full_pct = (full_asymmetric / total_candidates * 100) if total_candidates > 0 else 0
    
    # Main layout: metrics + quick stats LEFT, charts CENTER
    left_col, center_col = st.columns([1, 1.2])
    
    with left_col:
        st.subheader("Key Metrics")
        
        # 2x2 metric grid
        metric_row1_col1, metric_row1_col2 = st.columns(2)
        with metric_row1_col1:
            st.metric("Total Candidates", total_candidates)
        with metric_row1_col2:
            st.metric("Full Asymmetric", full_asymmetric)
        
        metric_row2_col1, metric_row2_col2 = st.columns(2)
        with metric_row2_col1:
            st.metric("Partial Asymmetric", partial_asymmetric)
        with metric_row2_col2:
            st.metric("Strong Signals", passed_signals)
        
        st.markdown("<hr style='margin: 20px 0; border: none; border-top: 1px solid #1f2937;'>", unsafe_allow_html=True)
        
        # Quick stats - no emojis
        st.subheader("Insights", divider=False)
        st.markdown(f"""
        **Quality Rate**: {full_pct:.0f}% full patterns

        **Signal Coverage**: {passed_signals} stocks qualify

        **Conversion**: {full_asymmetric}/{total_candidates} candidates
        """)
    
    with center_col:
        st.subheader("Pattern Distribution", divider=False)
        
        # Pattern distribution pie chart - larger
        pattern_counts = {}
        for r in results:
            pattern = r['pattern'].upper()
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        
        fig_pattern = px.pie(
            values=list(pattern_counts.values()),
            names=['Full Asymmetric' if x == 'FULL' else 'Partial' if x == 'PARTIAL' else 'None' for x in pattern_counts.keys()],
            title="",
            color_discrete_map={'Full Asymmetric': '#10b981', 'Partial': '#f59e0b', 'None': '#ef4444'},
            hole=0.35
        )
        fig_pattern.update_layout(
            height=350,
            showlegend=True,
            legend=dict(x=0.7, y=0.5, font=dict(size=10)),
            font=dict(size=10),
            margin=dict(t=20, b=0, l=0, r=0)
        )
        st.plotly_chart(fig_pattern, use_container_width=True)
    
    st.divider()
    
    # TOP 5 CANDIDATES
    st.header("Top 5 Opportunities")
    
    st.write("Ranked by composite score (60% asymmetry quality + 40% signal strength)")
    
    with st.expander("What's this?"):
        st.info("**Top candidates** are ranked by how strong their asymmetric pattern is AND how many technical/fundamental signals confirm it. Aims for 3.0 score (perfect asymmetry + max signals).")
    
    for i, candidate in enumerate(results[:5], 1):
        col_rank, col_ticker, col_score, col_pattern = st.columns([0.5, 1, 1.5, 2])
        
        ticker = candidate['ticker']
        score = candidate['composite_score']
        pattern = candidate['pattern'].upper()
        track = candidate['track']
        
        # Get halal status from cache or re-evaluate with Claude (30-day cache)
        cached_halal = halal_cache_manager.get_cached_halal_status(ticker)
        if cached_halal:
            halal = cached_halal['halal_status'].upper()
            print(f"📦 Using cached halal status for {ticker}")
        else:
            # Fresh evaluation with Claude
            try:
                validator = ValidationWorkflow()
                validation = validator.validate_ticker(ticker)
                # Add null check before calling .get()
                if validation is None:
                    halal = 'UNVERIFIED'
                    print(f"⚠️ Validation returned None for {ticker}")
                else:
                    halal_gates = validation.get('stages', {}).get('halal_gates', {})
                    halal = halal_gates.get('halal_status', 'UNVERIFIED').upper()
                # Cache for 30 days
                halal_cache_manager.set_cached_halal_status(ticker, halal_gates)
                print(f"✅ Fresh halal evaluation cached for {ticker}")
            except Exception as e:
                # Fallback to JSON value
                halal = candidate['halal_status'].upper()
                print(f"⚠️ Using JSON halal for {ticker}: {e}")
        
        signals = f"{candidate['signal_raw']}/24"
        
        with col_rank:
            st.markdown(f"### #{i}")
        
        with col_ticker:
            st.markdown(f"### {ticker}")
        
        with col_score:
            st.markdown(f"**Score: {score:.2f}**")
            st.caption("(0-3.0 scale)")
        
        with col_pattern:
            if pattern == 'FULL':
                st.markdown(f'<div class="full-asymmetric"><strong>Full Asymmetric</strong></div>', unsafe_allow_html=True)
            elif pattern == 'PARTIAL':
                st.markdown(f'<div class="partial-asymmetric"><strong>Partial Asymmetric</strong></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="not-asymmetric">No Pattern</div>', unsafe_allow_html=True)
        
        # Detail row
        detail_col1, detail_col2, detail_col3, detail_btn = st.columns([1, 1, 1, 1.5])
        
        with detail_col1:
            st.caption(f"Signals: **{signals}**")
        
        with detail_col2:
            st.caption(f"Halal: **{halal}**")
        
        with detail_col3:
            st.caption(f"Score: {score:.2f}/3.0")
        
        with detail_btn:
            if st.button("Details", key=f"detail_{ticker}"):
                st.session_state.selected_detail_ticker = ticker
                st.rerun()
        
        st.divider()
    
    # FULL TABLE
    st.header("Full Candidate List")
    
    with st.expander("Column Definitions"):
        st.markdown("""
        | Column | Meaning |
        |--------|---------|
        | **Rank** | Position (1-10) based on composite score |
        | **Ticker** | Stock symbol |
        | **Score** | Composite score (0-3.0): 60% asymmetry + 40% signals |
        | **Asymmetry** | Raw asymmetry component (0-3.0) |
        | **Signals** | Number of confirming technical/fundamental signals (0-24) |
        | **Pattern** | Pattern type: FULL (3 parts), PARTIAL (1-2 parts), or NONE |
        | **Halal** | Islamic screening result: PASS or FAIL |
        | **Conviction** | Overall confidence level: low/medium/high |
        """)
    
    # Convert to DataFrame
    df = pd.DataFrame(results)
    df = df.sort_values('composite_score', ascending=False)
    
    # Update halal_status column with cached/fresh evaluations (30-day cache)
    for idx, row in df.iterrows():
        ticker = row['ticker']
        cached_halal = halal_cache_manager.get_cached_halal_status(ticker)
        if cached_halal:
            df.at[idx, 'halal_status'] = cached_halal['halal_status']
        else:
            try:
                validator = ValidationWorkflow()
                validation = validator.validate_ticker(ticker)
                # Add null check before calling .get()
                if validation is None:
                    print(f"⚠️ Validation returned None for {ticker}")
                else:
                    halal_gates = validation.get('stages', {}).get('halal_gates', {})
                    df.at[idx, 'halal_status'] = halal_gates.get('halal_status', 'UNVERIFIED')
                    halal_cache_manager.set_cached_halal_status(ticker, halal_gates)
            except Exception as e:
                print(f"⚠️ Failed to evaluate halal for {ticker}: {e}")
    
    # Format for display
    display_df = df[[
        'rank', 'ticker', 'composite_score', 'asymmetry_score', 
        'signal_raw', 'pattern', 'halal_status', 'conviction'
    ]].copy()
    
    display_df.columns = [
        'Rank', 'Ticker', 'Score', 'Asymmetry', 'Signals', 
        'Pattern', 'Halal', 'Conviction'
    ]
    
    # Color code
    def color_pattern(val):
        if val == 'full':
            return 'background-color: #d4edda'
        elif val == 'partial':
            return 'background-color: #fff3cd'
        else:
            return 'background-color: #f8d7da'
    
    styled_df = display_df.style.map(
        color_pattern, 
        subset=['Pattern']
    ).format({
        'Score': '{:.2f}',
        'Asymmetry': '{:.1f}',
        'Signals': '{:.0f}'
    })
    
    st.dataframe(styled_df, use_container_width=True)


# =========================================================================
# PAGE: CANDIDATE DETAIL
# =========================================================================

def page_candidate_detail(ticker):
    """Detailed analysis for a single candidate."""
    
    st.title(f"{ticker} - Detailed Analysis")
    
    # Load data
    validation = load_checkpoint_data(ticker)
    
    if not validation:
        st.error(f"Could not load data for {ticker}")
        return
    
    # Extract information
    stages = validation.get('stages', {})
    halal_gates = stages.get('halal_gates', {})
    track_detection = stages.get('track_detection', {})
    signal_scoring = stages.get('signal_scoring', {})
    pattern_detection = stages.get('pattern_detection', {})
    
    # SUMMARY
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Halal Status",
            halal_gates.get('halal_status', 'Unknown').upper()
        )
    
    with col2:
        st.metric(
            "Track",
            track_detection.get('track', 'Unknown')
        )
    
    with col3:
        signal_score = signal_scoring.get('total_score', 0)
        st.metric(
            "Signals",
            f"{signal_score}/24"
        )
    
    with col4:
        pattern = pattern_detection.get('result', 'unknown').upper()
        st.metric(
            "Pattern",
            pattern
        )
    
    st.divider()
    
    # HALAL GATES
    st.header("Halal Compliance Gates")
    
    halal_verdict = halal_gates.get('halal_verdict', 'Unknown')
    st.info(f"**Verdict:** {halal_verdict}")
    
    gates = halal_gates.get('gates', {})
    for gate_name, gate_result in gates.items():
        if gate_result:
            col1, col2, col3 = st.columns([1, 2, 3])
            
            with col1:
                status = "✓ PASS" if gate_result.get('passed') else "✗ FAIL"
                st.subheader(status)
            
            with col2:
                st.write(f"**{gate_result.get('gate', 'Unknown')}**")
            
            with col3:
                st.write(gate_result.get('reason', 'N/A'))
    
    st.divider()
    
    # TRACK ANALYSIS
    st.header("Track Analysis")
    
    track_reasoning = track_detection.get('reasoning', 'No reasoning available')
    st.write(track_reasoning)
    
    fcf_history = track_detection.get('fcf_history', [])
    if fcf_history:
        st.caption(f"FCF History (5y): {fcf_history}")
    
    st.divider()
    
    # SIGNALS
    st.header("Signal Analysis")
    
    st.write("16 technical & fundamental signals that confirm the asymmetric pattern")
    
    with st.expander("What are signals?"):
        st.info("**Signals** are technical indicators and fundamental metrics that validate the asymmetric thesis. Examples: momentum, earnings growth, insider buying, contrarian sentiment. More signals = stronger conviction.")
    
    signals = signal_scoring.get('signals', {})
    signal_threshold = signal_scoring.get('threshold', 16)
    
    if signals:
        signal_list = []
        for signal_name, signal_data in signals.items():
            signal_list.append({
                'Signal': signal_name.replace('_', ' ').title(),
                'Score': signal_data.get('score', 0),
                'Value': str(signal_data.get('value', 'N/A'))[:50],
                'Reason': signal_data.get('reason', 'N/A')[:100]
            })
        
        df_signals = pd.DataFrame(signal_list)
        st.dataframe(df_signals, use_container_width=True)
        
        total_signals = signal_scoring.get('total_score', 0)
        st.caption(f"**Total Score:** {total_signals}/{signal_threshold} signals confirmed")
        if total_signals >= signal_threshold:
            st.success(f"Passes signal threshold for strong conviction")
    
    st.divider()
    
    # PATTERN DETECTION
    st.header("Asymmetric Pattern Components")
    
    with st.expander("What do Floor/Mispricing/Catalyst mean?"):
        st.markdown("""
        **Floor (Downside Protection)**
        - What: A valuation or structural floor that limits downside risk
        - Example: Company has $X in net cash per share as floor value
        - Why it matters: Even if investment goes wrong, limited downside
        
        **Mispricing (Market Wrong)**
        - What: Evidence that the market has misprice the stock
        - Example: Stock trading at 5x earnings while peers trade at 20x
        - Why it matters: Upside potential if market realizes its mistake
        
        **Catalyst (Re-rating Trigger)**
        - What: An upcoming event/timeline that could trigger stock re-rating
        - Example: FDA approval, earnings surprise, new product launch
        - Why it matters: Gives market a reason to correct the mispricing
        """)
    
    pattern_result = pattern_detection.get('result', 'unknown').upper()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        floor_status = "✓ Present" if pattern_detection.get('floor') else "✗ Missing"
        st.metric("Floor", floor_status)
        if pattern_detection.get('floor_reason'):
            st.caption(pattern_detection.get('floor_reason'))
    
    with col2:
        mispricing_status = "✓ Present" if pattern_detection.get('mispricing') else "✗ Missing"
        st.metric("Mispricing", mispricing_status)
        if pattern_detection.get('mispricing_reason'):
            st.caption(pattern_detection.get('mispricing_reason'))
    
    with col3:
        catalyst_status = "✓ Present" if pattern_detection.get('catalyst') else "✗ Missing"
        st.metric("Catalyst", catalyst_status)
        if pattern_detection.get('catalyst_reason'):
            st.caption(pattern_detection.get('catalyst_reason'))
    
    # Color code the pattern result
    if pattern_result == 'FULL':
        st.success(f"FULL ASYMMETRIC PATTERN - All 3 components present. {pattern_detection.get('reasoning', '')}")
    elif pattern_result == 'PARTIAL':
        st.warning(f"PARTIAL ASYMMETRIC PATTERN - 1-2 components present. {pattern_detection.get('reasoning', '')}")
    else:
        st.info(f"NO ASYMMETRIC PATTERN - Insufficient components. {pattern_detection.get('reasoning', '')}")
    
    # AI REASONING (CLAUDE) - WITH CACHING
    st.header("Claude AI Analysis (Plain English)")
    
    # Cache control
    col_title, col_refresh = st.columns([4, 1])
    with col_refresh:
        if st.button("Refresh Analysis", use_container_width=True, key=f"refresh_{ticker}"):
            st.session_state[f"force_refresh_{ticker}"] = True
            st.rerun()
    
    force_refresh = st.session_state.get(f"force_refresh_{ticker}", False)
    
    with st.spinner("Getting Claude analysis..."):
        ai_analysis, cached_at = get_claude_analysis(ticker, validation, force_refresh=force_refresh)
    
    # Clear the force_refresh flag
    if force_refresh:
        st.session_state[f"force_refresh_{ticker}"] = False
    
    # Show cache status
    if cached_at:
        from datetime import datetime as dt
        cached_time = dt.fromisoformat(cached_at)
        age_mins = int((dt.now() - cached_time).total_seconds() / 60)
        st.caption(f"📦 Cached {age_mins} minutes ago (expires in 14 days)")
    elif ai_analysis:
        st.caption("✨ Fresh analysis from Claude API")
    
    if ai_analysis:
        # Display as formatted sections, not raw JSON
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader("Investment Thesis")
            st.write(ai_analysis.get('thesis', 'N/A'))
            
        with col2:
            recommendation = ai_analysis.get('recommendation', 'HOLD')
            if recommendation == 'BUY':
                st.success(recommendation)
            elif recommendation == 'SELL':
                st.error(recommendation)
            else:
                st.info(recommendation)
        
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Key Risks")
            st.write(ai_analysis.get('risks', 'N/A'))
        
        with col2:
            st.subheader("Catalyst & Timeline")
            st.write(ai_analysis.get('catalyst', 'N/A'))
        
        st.divider()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            conviction = ai_analysis.get('conviction', 0)
            st.metric("Conviction Level", f"{conviction}/10")
        with col2:
            st.metric("Confidence", f"{min(conviction * 10, 100)}%")
        with col3:
            rec = ai_analysis.get('recommendation', 'HOLD')
            st.metric("Recommendation", rec)
    else:
        st.info("💡 **Tip:** Set ANTHROPIC_API_KEY in .env file to enable AI explanations")


# =========================================================================
# PAGE: SEARCH STOCK
# =========================================================================

def page_search_stock():
    """Search and analyze individual stocks."""
    
    st.title("Search Individual Stock")
    
    st.markdown("""
    Enter a stock ticker to analyze if it has **asymmetric profit chances** 
    based on our Halal Islamic-compliant screening.
    """)
    
    with st.expander("How does individual stock analysis work?"):
        st.markdown("""
        When you search a stock, the system:
        1. **Fetches latest data** from yfinance (price, financials)
        2. **Screens halal gates** (interest-bearing debt, business model compliance)
        3. **Detects track** (Track A/B/A-Transition based on cash flow)
        4. **Scores signals** (16 technical/fundamental indicators)
        5. **Finds asymmetric patterns** (Floor + Mispricing + Catalyst)
        6. **Generates AI reasoning** (Claude explains in plain English)
        
        Results shown: Same analysis as dashboard candidates
        """)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        ticker_input = st.text_input(
            "Enter stock ticker (e.g., MSFT, AAPL, GOOGL):",
            placeholder="Type ticker here..."
        ).upper()
    
    with col2:
        search_button = st.button("Analyze", use_container_width=True)
    
    # Check for previously cached validation result
    cached_validation = st.session_state.get(f"search_cached_validation_{ticker_input}")
    
    if (search_button or cached_validation is not None) and ticker_input:
        with st.spinner(f"🔄 Analyzing {ticker_input}..."):
            try:
                # Use cached validation if available, otherwise fetch fresh
                if cached_validation is not None:
                    validation = cached_validation
                else:
                    # Run validation on the stock
                    validator = ValidationWorkflow()
                    validation = validator.validate_ticker(ticker_input)
                    # Cache the result for subsequent reruns
                    st.session_state[f"search_cached_validation_{ticker_input}"] = validation
                
                # Check if validation is None or invalid
                if validation is None:
                    st.error(f"❌ Failed to validate {ticker_input} - No data returned")
                    st.info("This may happen if the stock ticker is invalid or data is unavailable.")
                elif validation.get('status') == 'error':
                    st.error(f"Error: {validation.get('message', 'Could not fetch data')}")
                    st.info("Make sure the ticker is valid (e.g., MSFT, AAPL)")
                elif isinstance(validation, dict):
                    # Extract results
                    stages = validation.get('stages', {})
                    if stages is None:
                        stages = {}
                    halal_gates = stages.get('halal_gates', {})
                    track_detection = stages.get('track_detection', {})
                    signal_scoring = stages.get('signal_scoring', {})
                    pattern_detection = stages.get('pattern_detection', {})
                    
                    # SUMMARY METRICS
                    st.header(f"{ticker_input} Analysis")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        halal_status = halal_gates.get('halal_status', 'unknown').upper()
                        status_color = "🟢" if halal_status == "UNVERIFIED" else "🔴" if halal_status == "FAIL" else "🟡"
                        st.metric("Halal Status", f"{status_color} {halal_status}")
                    
                    with col2:
                        track = track_detection.get('track', 'Unknown')
                        st.metric("Track Type", track)
                    
                    with col3:
                        signal_score = signal_scoring.get('total_score', 0)
                        st.metric("Signals Score", f"{signal_score}/24")
                    
                    with col4:
                        pattern = pattern_detection.get('result', 'not_asymmetric').upper()
                        pattern_emoji = "✅" if pattern == "FULL" else "⚠️" if pattern == "PARTIAL" else "❌"
                        st.metric("Asymmetric Pattern", f"{pattern_emoji} {pattern}")
                    
                    st.divider()
                    
                    # HALAL VERDICT
                    st.header("Halal Screening")
                    
                    halal_verdict = halal_gates.get('halal_verdict', 'Unknown')
                    
                    if halal_gates.get('halal_status') == 'fail':
                        st.error(f"Does not pass Halal screening\n\nReason: {halal_verdict}")
                    else:
                        st.success(f"Passes Halal screening\n\n{halal_verdict}")
                    
                    # TRACK EXPLANATION
                    st.header("Track Classification")
                    
                    track_reasoning = track_detection.get('reasoning', 'No details available')
                    st.write(track_reasoning)
                    
                    if track == "A":
                        st.info("**Track A** = Profitable compounder with strong FCF generation")
                    elif track == "A-Transition":
                        st.warning("**Track A-Transition** = Was profitable, now struggling (potential disruption)")
                    elif track == "B":
                        st.info("**Track B** = High-growth investment (negative FCF but investing heavily)")
                    
                    st.divider()
                    
                    # SIGNALS
                    st.header("Key Signals")
                    
                    signals = signal_scoring.get('signals', {})
                    threshold = signal_scoring.get('threshold', 16)
                    
                    if signals:
                        signal_list = []
                        for signal_name, signal_data in signals.items():
                            score = signal_data.get('score', 0)
                            emoji = "🟢" if score == 3 else "🟡" if score == 2 else "🔴"
                            signal_list.append({
                                'Signal': signal_name.replace('_', ' ').title(),
                                'Score': f"{emoji} {score}/3",
                                'Reason': signal_data.get('reason', 'N/A')[:80]
                            })
                        
                        df_signals = pd.DataFrame(signal_list)
                        st.dataframe(df_signals, use_container_width=True, hide_index=True)
                        
                        st.caption(f"Total Score: {signal_score}/{threshold}")
                    
                    st.divider()
                    
                    # ASYMMETRIC PATTERN
                    st.header("Asymmetric Pattern Analysis")
                    
                    pattern_components = pattern_detection.get('components', {})
                    pattern_result = pattern_detection.get('result', 'not_asymmetric').upper()
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        floor_present = pattern_detection.get('floor', False)
                        st.metric("Floor (Downside Protection)", "Present" if floor_present else "Missing")
                    
                    with col2:
                        mispricing_present = pattern_detection.get('mispricing', False)
                        st.metric("Mispricing (Market Wrong)", "Present" if mispricing_present else "Missing")
                    
                    with col3:
                        catalyst_present = pattern_detection.get('catalyst', False)
                        st.metric("Catalyst (Re-rating Trigger)", "Present" if catalyst_present else "Missing")
                    
                    if pattern_result == "FULL":
                        st.success(f"FULL ASYMMETRIC PATTERN DETECTED\n\nAll 3 components present = High conviction opportunity")
                    elif pattern_result == "PARTIAL":
                        st.warning(f"PARTIAL ASYMMETRIC PATTERN\n\n2 of 3 components present = Medium conviction opportunity")
                    else:
                        st.info(f"NO ASYMMETRIC PATTERN\n\nFewer than 2 components = Lower conviction")
                    
                    st.divider()
                    
                    # CLAUDE AI ANALYSIS - OPT-IN WITH CACHING
                    st.header("AI Investment Analysis")
                    
                    # Check if cache exists
                    cached_text, cached_at = get_cached_ai_analysis(ticker_input)
                    has_valid_cache = cached_text is not None
                    
                    if has_valid_cache:
                        # Show cache status and refresh button
                        col_title, col_refresh = st.columns([4, 1])
                        with col_title:
                            from datetime import datetime as dt
                            cached_time = dt.fromisoformat(cached_at)
                            age_mins = int((dt.now() - cached_time).total_seconds() / 60)
                            st.caption(f"📦 Cached {age_mins} minutes ago (expires in 14 days)")
                        
                        with col_refresh:
                            if st.button("Refresh", use_container_width=True, key=f"search_refresh_{ticker_input}"):
                                # Clear cached validation so we fetch fresh data
                                st.session_state.pop(f"search_cached_validation_{ticker_input}", None)
                                st.session_state[f"search_run_analysis_{ticker_input}"] = True
                                st.rerun()
                        
                        # Parse and display cached analysis
                        try:
                            import re
                            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', cached_text, re.DOTALL)
                            if json_match:
                                ai_analysis = json.loads(json_match.group())
                            else:
                                ai_analysis = {
                                    'thesis': cached_text,
                                    'risks': 'See analysis above',
                                    'catalyst': 'See analysis above',
                                    'conviction': 5,
                                    'recommendation': 'HOLD'
                                }
                        except:
                            ai_analysis = {
                                'thesis': cached_text,
                                'risks': 'See analysis above',
                                'catalyst': 'See analysis above',
                                'conviction': 5,
                                'recommendation': 'HOLD'
                            }
                        
                        # Display analysis
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.subheader("Investment Thesis")
                            st.write(ai_analysis.get('thesis', 'N/A'))
                        with col2:
                            recommendation = ai_analysis.get('recommendation', 'HOLD')
                            if recommendation == 'BUY':
                                st.success(recommendation)
                            elif recommendation == 'SELL':
                                st.error(recommendation)
                            else:
                                st.info(recommendation)
                        
                        st.divider()
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.subheader("Key Risks")
                            st.write(ai_analysis.get('risks', 'N/A'))
                        with col2:
                            st.subheader("Catalyst & Timeline")
                            st.write(ai_analysis.get('catalyst', 'N/A'))
                        
                        st.divider()
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            conviction = ai_analysis.get('conviction', 0)
                            st.metric("Conviction Level", f"{conviction}/10")
                        with col2:
                            st.metric("Confidence", f"{min(conviction * 10, 100)}%")
                        with col3:
                            rec = ai_analysis.get('recommendation', 'HOLD')
                            st.metric("Recommendation", rec)
                    
                    else:
                        # No cache - show button to run analysis
                        st.info("Claude AI analysis not yet generated for this stock")
                        
                        if st.button("Run Claude Analysis", use_container_width=True, key=f"search_run_button_{ticker_input}"):
                            st.session_state[f"search_run_analysis_{ticker_input}"] = True
                            st.rerun()
                        
                        # If user clicked button, generate and cache analysis
                        if st.session_state.get(f"search_run_analysis_{ticker_input}", False):
                            with st.spinner("🔄 Generating Claude analysis (first time - this caches for 14 days)..."):
                                print(f"\n{'='*60}")
                                print(f"Starting Claude analysis for {ticker_input}")
                                print(f"{'='*60}")
                                ai_analysis, _ = get_claude_analysis(ticker_input, validation, force_refresh=True)
                                print(f"Analysis result: {type(ai_analysis)} - {ai_analysis is not None}")
                                print(f"{'='*60}\n")
                            
                            if ai_analysis:
                                # Cache the analysis text (convert to JSON string if dict)
                                analysis_text = json.dumps(ai_analysis) if isinstance(ai_analysis, dict) else str(ai_analysis)
                                cache_success = cache_ai_analysis(ticker_input, analysis_text)
                                
                                if cache_success:
                                    # Clear flag and rerun to show cached display
                                    st.session_state[f"search_run_analysis_{ticker_input}"] = False
                                    st.success("✅ Analysis generated and cached!")
                                    st.rerun()
                                else:
                                    st.error("⚠️ Analysis generated but failed to cache. Check console logs.")
                                    st.session_state[f"search_run_analysis_{ticker_input}"] = False
                            else:
                                st.error("❌ Failed to generate analysis. Check console logs for details.")
                                st.session_state[f"search_run_analysis_{ticker_input}"] = False
                    
            except Exception as e:
                st.error(f"❌ Error analyzing {ticker_input}: {str(e)}")
    
    elif search_button:
        st.warning("Please enter a stock ticker first")


# =========================================================================
# MAIN APP
# =========================================================================

def main():
    """Main app router."""
    
    # Initialize session state
    if 'selected_detail_ticker' not in st.session_state:
        st.session_state.selected_detail_ticker = None
    
    # If a detail page is selected, show it
    if st.session_state.selected_detail_ticker:
        st.sidebar.title("Navigation")
        if st.sidebar.button("Back to Dashboard"):
            st.session_state.selected_detail_ticker = None
            st.rerun()
        
        page_candidate_detail(st.session_state.selected_detail_ticker)
        return
    
    # Otherwise show dashboard
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Select Page",
        ["Dashboard", "Top 5 Analysis", "Search Stock"],
        label_visibility="collapsed"
    )
    
    if page == "Dashboard":
        page_home()
    
    elif page == "Top 5 Analysis":
        st.title("Top 5 Detailed Analysis")
        
        results = load_discovery_results()
        if results:
            selected_ticker = st.selectbox(
                "Select candidate:",
                [r['ticker'] for r in results[:5]]
            )
            
            page_candidate_detail(selected_ticker)
    
    elif page == "Search Stock":
        page_search_stock()
    
    # Discovery Update Section
    st.divider()
    st.markdown("### Update Stock Universe")
    st.markdown("Run discovery workflow to find new top 5 asymmetric opportunities")
    
    col_btn, col_info = st.columns([1, 2])
    
    with col_btn:
        if st.button("Run Discovery", use_container_width=True, key="run_discovery_btn"):
            with st.spinner("Running discovery workflow... This may take a few minutes"):
                success, message = run_discovery_workflow()
            
            if success:
                st.success(message)
                st.info("Dashboard updated! Refresh page to see new results.")
                # Clear cache to show updated results
                st.cache_data.clear()
            else:
                st.error("Discovery failed:")
                st.code(message, language="text")
    
    with col_info:
        st.info(
            "**What this does:**\n"
            "- Screens all stocks for asymmetric patterns\n"
            "- Validates halal compliance\n"
            "- Ranks by opportunity strength\n"
            "- Updates top 5 candidates"
        )
    
    # Footer
    st.divider()
    st.markdown("""
    ---
    **Halal Asymmetric Stock Finder** | Islamic-compliant value investing
    
    Built for ethical investors
    """)


if __name__ == "__main__":
    main()
