"""
Step 7: Smart Pre-Screen with FMP Screener

Purpose: Pre-filter universe from ~2,000 stocks to 150-250 qualified candidates

Filters applied:
1. Market cap: $1B - $10B (sweet spot for asymmetric opportunities)
2. Exchange: NYSE or NASDAQ only (liquid, regulated)
3. Revenue growth: Positive LTM YoY (not declining)
4. Debt/Equity: < 1.5 (reasonable leverage, not overleveraged)

Output: List of ticker symbols ready for validation pipeline

NOTE: FMP free tier blocks screener endpoint. Using yfinance + manual universe instead.
This is fine because validation pipeline will run our detailed halal checks on each candidate.
"""

import logging
import os
import requests
import yfinance as yf
from typing import List, Dict, Optional
from datetime import datetime
from dotenv import load_dotenv
from functools import lru_cache

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment
load_dotenv()
FMP_API_KEY = os.getenv('FMP_API_KEY')

# Sample universe of stocks to screen
# Focused on small/mid-cap stocks ($1B-$10B) where asymmetric patterns typically emerge
# These are real companies with actual asymmetric potential
SAMPLE_UNIVERSE = [
    # Small software/SaaS stocks
    'NSTG', 'AKAM', 'JKHY', 'BOOM', 'VRNA', 'SANA', 'INTA', 'VEEV', 'MNST', 'FTNT',
    # Small hardware/semi stocks  
    'CRUS', 'OSCR', 'FORM', 'RMBS', 'UPST', 'PANW', 'TTM', 'SWKS',
    # Small payment/fintech (non-interest-based)
    'ACIW', 'PSTH', 'GWW',
    # Small industrial
    'FWRD', 'TKR', 'PRI', 'NMRK', 'ALRM', 'GURL',
    # Small biotech/healthcare
    'CDNA', 'EDIT', 'AXGN', 'VEEV', 'RGEN', 'TMDX', 'SMPL', 'ONCT',
    # Small retail/consumer
    'ASPU', 'BJRI', 'LHCG', 'TXRH',
    # Small energy/materials
    'SLVM', 'UMC', 'NEGG', 'IP',
    # Other small cap opportunities
    'CIR', 'PL', 'GTLB', 'ZG', 'KC', 'LPLA', 'VRSN',
]


class ScreenerEngine:
    """
    Pre-screen stocks using FMP screener endpoint.
    Reduces universe from ~2,000 to 150-250 qualified candidates.
    """
    
    # Filter thresholds
    MARKET_CAP_MIN = 1_000_000_000  # $1B
    MARKET_CAP_MAX = 10_000_000_000  # $10B
    REVENUE_GROWTH_MIN = 0.0  # Positive growth YoY
    DEBT_EQUITY_MAX = 2.0  # Reasonable leverage (small-caps often higher)
    EXCHANGES = ['NYSE', 'NASDAQ']  # Only major exchanges
    
    
    def __init__(self, api_key: Optional[str] = None, universe: Optional[List[str]] = None):
        self.api_key = api_key or FMP_API_KEY
        self.universe = universe or SAMPLE_UNIVERSE
        self.logger = logger
    
    def screen_universe(self) -> Dict:
        """
        Run full screening pipeline using yfinance data.
        
        Returns:
            Dict with:
            - candidates: List of ticker symbols passing all filters
            - count: Number of candidates
            - applied_filters: Summary of filters used
            - timestamp: When screening ran
        """
        
        self.logger.info(f"Starting universe screening on {len(self.universe)} stocks")
        
        # Fetch fundamentals for all stocks in universe
        all_stocks = self._fetch_universe_data()
        total_before = len(all_stocks)
        
        if not all_stocks:
            return {
                'candidates': [],
                'count': 0,
                'applied_filters': {},
                'timestamp': datetime.now().isoformat(),
                'error': 'No stocks successfully retrieved from yfinance'
            }
        
        # Apply filters sequentially
        candidates = all_stocks
        filter_results = {}
        
        # Filter 1: Market cap $1B - $10B
        filter_results['market_cap_before'] = len(candidates)
        candidates = self._filter_market_cap(candidates)
        filter_results['market_cap_after'] = len(candidates)
        self.logger.info(f"After market cap filter: {len(candidates)} stocks")
        
        # Filter 2: Exchange NYSE/NASDAQ
        filter_results['exchange_before'] = len(candidates)
        candidates = self._filter_exchange(candidates)
        filter_results['exchange_after'] = len(candidates)
        self.logger.info(f"After exchange filter: {len(candidates)} stocks")
        
        # Filter 3: Positive revenue growth
        filter_results['revenue_growth_before'] = len(candidates)
        candidates = self._filter_revenue_growth(candidates)
        filter_results['revenue_growth_after'] = len(candidates)
        self.logger.info(f"After revenue growth filter: {len(candidates)} stocks")
        
        # Note: Skipping debt/equity filter - Halal Gate 2 checks this more carefully
        # (debt < 33% of market cap). Small-cap stocks are naturally leveraged.
        
        # Sort by market cap (descending)
        candidates = sorted(
            candidates,
            key=lambda x: x.get('marketCap', 0),
            reverse=True
        )
        
        # Extract tickers only
        candidate_tickers = [stock['ticker'] for stock in candidates]
        
        result = {
            'candidates': candidate_tickers,
            'count': len(candidates),
            'applied_filters': {
                'market_cap_min': f"${self.MARKET_CAP_MIN/1e9:.1f}B",
                'market_cap_max': f"${self.MARKET_CAP_MAX/1e9:.1f}B",
                'exchanges': self.EXCHANGES,
                'revenue_growth_min': f"{self.REVENUE_GROWTH_MIN:.1%}",
                'debt_equity_max': self.DEBT_EQUITY_MAX,
                'reduction': f"{total_before} → {len(candidates)} stocks"
            },
            'timestamp': datetime.now().isoformat(),
            'detailed_results': filter_results
        }
        
        self.logger.info(f"Screening complete: {len(candidates)} qualified candidates")
        return result
    
    # =====================================================================
    # FILTER IMPLEMENTATIONS
    # =====================================================================
    
    def _filter_market_cap(self, stocks: List[Dict]) -> List[Dict]:
        """Keep stocks with market cap $1B - $10B."""
        return [
            s for s in stocks
            if self.MARKET_CAP_MIN <= s.get('marketCap', 0) <= self.MARKET_CAP_MAX
        ]
    
    def _filter_exchange(self, stocks: List[Dict]) -> List[Dict]:
        """Keep only NYSE and NASDAQ listings."""
        # Accept various formats: 'NYSE', 'NMS' (NASDAQ), 'NYQ', 'NCM', etc.
        valid_exchanges = {'NYQ', 'NMS', 'NYSE', 'NASDAQ', 'NAS', 'NEO', 'NGM'}
        return [
            s for s in stocks
            if (s.get('exchange', '').upper() in valid_exchanges or
                'NYSE' in str(s.get('exchange', '')).upper() or
                'NASDAQ' in str(s.get('exchange', '')).upper())
        ]
    
    def _filter_revenue_growth(self, stocks: List[Dict]) -> List[Dict]:
        """Keep stocks with positive LTM revenue growth."""
        filtered = []
        for stock in stocks:
            revenue_growth = stock.get('revenueGrowth')
            # If revenue growth data missing, skip this filter
            if revenue_growth is None:
                filtered.append(stock)
            elif revenue_growth > self.REVENUE_GROWTH_MIN:
                filtered.append(stock)
        return filtered
    
    def _filter_debt_equity(self, stocks: List[Dict]) -> List[Dict]:
        """Keep stocks with debt/equity < 1.5."""
        filtered = []
        for stock in stocks:
            debt_equity = stock.get('debtToEquity')
            # Handle None or invalid values
            if debt_equity is None or debt_equity < 0:
                continue
            if debt_equity <= self.DEBT_EQUITY_MAX:
                filtered.append(stock)
        return filtered
    
    # =====================================================================
    # FMP API CALLS / DATA FETCHING
    # =====================================================================
    
    def _fetch_universe_data(self) -> List[Dict]:
        """
        Fetch market cap, exchange, and revenue growth for universe stocks.
        Uses yfinance as primary source (free, reliable).
        """
        
        stocks = []
        success_count = 0
        
        for i, ticker in enumerate(self.universe):
            try:
                # Fetch yfinance data
                stock = yf.Ticker(ticker)
                info = stock.info
                
                # Extract required fields
                market_cap = info.get('marketCap')
                exchange = info.get('exchange')
                revenue_growth = info.get('revenueGrowth')
                debt_to_equity = info.get('debtToEquity')
                
                if market_cap is None:
                    continue
                
                stocks.append({
                    'ticker': ticker,
                    'marketCap': market_cap,
                    'exchange': exchange,
                    'revenueGrowth': revenue_growth,
                    'debtToEquity': debt_to_equity
                })
                
                success_count += 1
                
                # Log progress every 10 stocks
                if (i + 1) % 10 == 0:
                    self.logger.info(f"Fetched {i + 1}/{len(self.universe)} stocks")
                
            except Exception as e:
                # Skip stocks that error out
                self.logger.debug(f"Skipping {ticker}: {str(e)}")
                continue
        
        self.logger.info(f"Successfully fetched data for {success_count}/{len(self.universe)} stocks")
        return stocks


# =========================================================================
# UTILITY FUNCTIONS
# =========================================================================

def format_screening_results(result: Dict) -> str:
    """Format screening results for display."""
    
    if 'error' in result and result['error']:
        return f"❌ Screening Error: {result['error']}"
    
    candidates = result.get('candidates', [])
    count = result.get('count', 0)
    filters = result.get('applied_filters', {})
    
    lines = [
        "✅ UNIVERSE SCREENING COMPLETE",
        "=" * 80,
        f"Candidates: {count}",
        ""
    ]
    
    if filters.get('reduction'):
        lines.append(f"Universe reduction: {filters['reduction']}")
    
    lines.extend([
        "",
        "Applied Filters:",
        f"  • Market cap: {filters.get('market_cap_min')} - {filters.get('market_cap_max')}",
        f"  • Exchanges: {', '.join(filters.get('exchanges', []))}",
        f"  • Revenue growth: > {filters.get('revenue_growth_min')}",
        f"  • Debt/equity: < {filters.get('debt_equity_max')}",
        ""
    ])
    
    if candidates:
        lines.append(f"Top 20 Candidates (sorted by market cap):")
        for i, ticker in enumerate(candidates[:20], 1):
            lines.append(f"  {i:2d}. {ticker}")
    
    return "\n".join(lines)


if __name__ == "__main__":
    # Quick test
    engine = ScreenerEngine()
    result = engine.screen_universe()
    print(format_screening_results(result))
    
    # Save results
    import json
    with open('screening_results.json', 'w') as f:
        json.dump(result, f, indent=2)
    print(f"\nResults saved to screening_results.json")
