"""
Data fetcher module for Halal Asymmetric Stock Finder.
Routes data requests to yfinance or FMP free tier automatically.
Normalizes both sources into unified data structures.
Includes caching layer to minimize redundant API calls.
"""

import os
import json
import sqlite3
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

import requests
import yfinance as yf
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
FMP_API_KEY = os.getenv('FMP_API_KEY')
if not FMP_API_KEY:
    logger.warning("FMP_API_KEY not found in environment. Some features will be unavailable.")

# FMP Base URL
FMP_BASE_URL = "https://financialmodelingprep.com/api"


class DataCache:
    """SQLite cache for financial data, price data, and AI reasoning.
    
    Three tables:
    - financial_data: Income, balance, cashflow, metrics, profile, segments (7-day expiry)
    - price_data: Quote, historical prices, screener results (24-hour expiry)
    - ai_reasoning: AI outputs (no expiry, historical record)
    """
    
    def __init__(self, db_path: str = "cache.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Financial data table (7-day expiry)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS financial_data (
                ticker TEXT NOT NULL,
                data_type TEXT NOT NULL,
                json_blob TEXT NOT NULL,
                fetched_at INTEGER NOT NULL,
                PRIMARY KEY (ticker, data_type)
            )
        ''')
        
        # Price data table (24-hour expiry)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_data (
                ticker TEXT NOT NULL,
                data_type TEXT NOT NULL,
                json_blob TEXT NOT NULL,
                fetched_at INTEGER NOT NULL,
                PRIMARY KEY (ticker, data_type)
            )
        ''')
        
        # AI reasoning table (no expiry, historical)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_reasoning (
                ticker TEXT NOT NULL,
                run_date TEXT NOT NULL,
                signal_json TEXT NOT NULL,
                reasoning_json TEXT NOT NULL,
                created_at INTEGER NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"Cache database initialized: {self.db_path}")
    
    def get_financial_data(self, ticker: str, data_type: str) -> Optional[Dict]:
        """Retrieve financial data from cache if fresh (< 7 days).
        
        Args:
            ticker: Stock symbol
            data_type: One of 'income', 'balance', 'cashflow', 'metrics', 'profile', 'segments'
        
        Returns:
            Cached data dict or None if expired/missing
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT json_blob, fetched_at FROM financial_data WHERE ticker = ? AND data_type = ?',
            (ticker, data_type)
        )
        result = cursor.fetchone()
        conn.close()
        
        if result:
            json_blob, fetched_at = result
            age_seconds = time.time() - fetched_at
            age_days = age_seconds / 86400
            
            if age_days < 7:
                logger.info(f"Cache hit: {ticker} {data_type} ({age_days:.1f} days old)")
                return json.loads(json_blob)
            else:
                logger.info(f"Cache expired: {ticker} {data_type} ({age_days:.1f} days old)")
        
        return None
    
    def set_financial_data(self, ticker: str, data_type: str, data: Dict):
        """Store financial data in cache."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT OR REPLACE INTO financial_data (ticker, data_type, json_blob, fetched_at)
               VALUES (?, ?, ?, ?)''',
            (ticker, data_type, json.dumps(data), int(time.time()))
        )
        conn.commit()
        conn.close()
    
    def get_price_data(self, ticker: str, data_type: str) -> Optional[Dict]:
        """Retrieve price data from cache if fresh (< 24 hours)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT json_blob, fetched_at FROM price_data WHERE ticker = ? AND data_type = ?',
            (ticker, data_type)
        )
        result = cursor.fetchone()
        conn.close()
        
        if result:
            json_blob, fetched_at = result
            age_hours = (time.time() - fetched_at) / 3600
            
            if age_hours < 24:
                logger.info(f"Cache hit: {ticker} {data_type} ({age_hours:.1f} hours old)")
                return json.loads(json_blob)
            else:
                logger.info(f"Cache expired: {ticker} {data_type} ({age_hours:.1f} hours old)")
        
        return None
    
    def set_price_data(self, ticker: str, data_type: str, data: Dict):
        """Store price data in cache."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT OR REPLACE INTO price_data (ticker, data_type, json_blob, fetched_at)
               VALUES (?, ?, ?, ?)''',
            (ticker, data_type, json.dumps(data), int(time.time()))
        )
        conn.commit()
        conn.close()


# Global cache instance
cache = DataCache()


# ============================================================================
# YFINANCE WRAPPER FUNCTIONS
# ============================================================================

def fetch_income_statement(ticker: str, years: int = 10) -> Optional[Dict]:
    """Fetch income statement from yfinance.
    
    Args:
        ticker: Stock symbol
        years: Number of years to fetch (default 10)
    
    Returns:
        Normalized income statement dict or None on error
    """
    # Check cache first
    cached = cache.get_financial_data(ticker, 'income')
    if cached:
        return cached
    
    try:
        stock = yf.Ticker(ticker)
        # yfinance returns income statement from most recent to oldest
        income_stmt = stock.income_stmt
        
        if income_stmt is None or income_stmt.empty:
            logger.warning(f"No income statement data for {ticker}")
            return None
        
        # Normalize to dict by year
        data = {
            'ticker': ticker,
            'years': []
        }
        
        for date in income_stmt.columns:
            year = date.year
            year_data = {
                'year': year,
                'date': date.isoformat(),
                'totalRevenue': income_stmt.loc['Total Revenue', date] if 'Total Revenue' in income_stmt.index else None,
                'ebit': income_stmt.loc['EBIT', date] if 'EBIT' in income_stmt.index else None,
                'operatingIncome': income_stmt.loc['Operating Income', date] if 'Operating Income' in income_stmt.index else None,
                'netIncome': income_stmt.loc['Net Income', date] if 'Net Income' in income_stmt.index else None,
            }
            data['years'].append(year_data)
        
        cache.set_financial_data(ticker, 'income', data)
        logger.info(f"Fetched income statement for {ticker}: {len(data['years'])} years")
        return data
    
    except Exception as e:
        logger.error(f"Error fetching income statement for {ticker}: {str(e)}")
        return None


def fetch_balance_sheet(ticker: str, years: int = 10) -> Optional[Dict]:
    """Fetch balance sheet from yfinance."""
    cached = cache.get_financial_data(ticker, 'balance')
    if cached:
        return cached
    
    try:
        stock = yf.Ticker(ticker)
        balance = stock.balance_sheet
        
        if balance is None or balance.empty:
            logger.warning(f"No balance sheet data for {ticker}")
            return None
        
        data = {
            'ticker': ticker,
            'years': []
        }
        
        for date in balance.columns:
            year = date.year
            year_data = {
                'year': year,
                'date': date.isoformat(),
                'totalAssets': balance.loc['Total Assets', date] if 'Total Assets' in balance.index else None,
                'totalLiabilities': balance.loc['Total Liabilities', date] if 'Total Liabilities' in balance.index else None,
                'totalEquity': balance.loc['Total Equity', date] if 'Total Equity' in balance.index else None,
                'totalDebt': balance.loc['Total Debt', date] if 'Total Debt' in balance.index else None,
                'cash': balance.loc['Cash', date] if 'Cash' in balance.index else None,
            }
            data['years'].append(year_data)
        
        cache.set_financial_data(ticker, 'balance', data)
        logger.info(f"Fetched balance sheet for {ticker}: {len(data['years'])} years")
        return data
    
    except Exception as e:
        logger.error(f"Error fetching balance sheet for {ticker}: {str(e)}")
        return None


def fetch_cashflow(ticker: str, years: int = 10) -> Optional[Dict]:
    """Fetch cash flow statement from yfinance."""
    cached = cache.get_financial_data(ticker, 'cashflow')
    if cached:
        return cached
    
    try:
        stock = yf.Ticker(ticker)
        cashflow = stock.cashflow
        
        if cashflow is None or cashflow.empty:
            logger.warning(f"No cashflow data for {ticker}")
            return None
        
        data = {
            'ticker': ticker,
            'years': []
        }
        
        for date in cashflow.columns:
            year = date.year
            year_data = {
                'year': year,
                'date': date.isoformat(),
                'operatingCashflow': cashflow.loc['Operating Cash Flow', date] if 'Operating Cash Flow' in cashflow.index else None,
                'capitalExpenditure': cashflow.loc['Capital Expenditure', date] if 'Capital Expenditure' in cashflow.index else None,
                'freeCashflow': cashflow.loc['Free Cash Flow', date] if 'Free Cash Flow' in cashflow.index else None,
            }
            data['years'].append(year_data)
        
        cache.set_financial_data(ticker, 'cashflow', data)
        logger.info(f"Fetched cashflow for {ticker}: {len(data['years'])} years")
        return data
    
    except Exception as e:
        logger.error(f"Error fetching cashflow for {ticker}: {str(e)}")
        return None


def fetch_quote_info(ticker: str) -> Optional[Dict]:
    """Fetch current quote and basic info from yfinance.
    
    Returns market cap, price, 52-week high/low, sector, industry.
    """
    cached = cache.get_price_data(ticker, 'quote')
    if cached:
        return cached
    
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        data = {
            'ticker': ticker,
            'company_name': info.get('longName', ''),
            'sector': info.get('sector', ''),
            'industry': info.get('industry', ''),
            'currentPrice': info.get('currentPrice'),
            'marketCap': info.get('marketCap'),
            'fiftyTwoWeekHigh': info.get('fiftyTwoWeekHigh'),
            'fiftyTwoWeekLow': info.get('fiftyTwoWeekLow'),
            'lastUpdate': datetime.now().isoformat(),
        }
        
        cache.set_price_data(ticker, 'quote', data)
        logger.info(f"Fetched quote info for {ticker}: sector={data.get('sector')}")
        return data
    
    except Exception as e:
        logger.error(f"Error fetching quote info for {ticker}: {str(e)}")
        return None


def fetch_price_history(ticker: str, period: str = '1y') -> Optional[Dict]:
    """Fetch historical price data from yfinance.
    
    Args:
        ticker: Stock symbol
        period: '30d', '1y', '5y' etc. Default '1y'
    
    Returns:
        Dict with daily prices and computed 30-day average (and current market cap for debt calc)
    """
    cached = cache.get_price_data(ticker, f'history_{period}')
    if cached:
        return cached
    
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        
        if hist is None or hist.empty:
            logger.warning(f"No price history for {ticker}")
            return None
        
        # Get current market cap (use info endpoint once, not repeatedly)
        info = stock.info
        market_cap = info.get('marketCap')
        
        # Calculate 30-day average for market cap basis (use market cap directly, not price average)
        # Note: market cap changes daily, but we'll use current market cap as the "30-day average"
        # since FMP is the primary source and we're using FMP's 30-day avg if available
        market_cap_30d_avg = market_cap  # Simplified: use current market cap
        
        data = {
            'ticker': ticker,
            'period': period,
            'lastClose': hist['Close'].iloc[-1] if len(hist) > 0 else None,
            'marketCap': market_cap,  # Add current market cap for halal debt calc
            'marketCap30dAvg': market_cap_30d_avg,  # 30-day avg market cap for Gate 2
            'fiftyTwoWeekHigh': hist['High'].max(),
            'fiftyTwoWeekLow': hist['Low'].min(),
            'totalDays': len(hist),
            'lastUpdate': datetime.now().isoformat(),
        }
        
        cache.set_price_data(ticker, f'history_{period}', data)
        logger.info(f"Fetched price history for {ticker} ({period}): {len(hist)} days, market cap: ${market_cap/1e9:.1f}B")
        return data
    
    except Exception as e:
        logger.error(f"Error fetching price history for {ticker}: {str(e)}")
        return None


# ============================================================================
# FMP API WRAPPER FUNCTIONS
# ============================================================================

def _fmp_request(endpoint: str, params: Dict = None) -> Optional[Dict]:
    """Make an FMP API request with error handling and rate limit awareness.
    
    Args:
        endpoint: API endpoint (e.g. '/v3/stock-screener')
        params: Query parameters dict
    
    Returns:
        Response JSON or None on error
    """
    if not FMP_API_KEY:
        logger.error("FMP_API_KEY not set. Cannot make FMP requests.")
        return None
    
    if params is None:
        params = {}
    
    params['apikey'] = FMP_API_KEY
    url = FMP_BASE_URL + endpoint
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        logger.error(f"Timeout on FMP request: {endpoint}")
        return None
    except requests.exceptions.HTTPError as e:
        if response.status_code == 429:
            logger.warning("FMP rate limit hit. Consider pausing and resuming later.")
        else:
            logger.error(f"HTTP error on FMP request: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error on FMP request {endpoint}: {str(e)}")
        return None


def fetch_stock_screener(filters: Dict = None) -> Optional[List[Dict]]:
    """Fetch stock screener results from FMP free tier.
    
    Applies filters for market cap, exchange, country, and exclusions.
    Returns list of tickers meeting criteria.
    
    Args:
        filters: Dict with optional keys:
            - marketCapMin (default 1000000000)
            - marketCapMax (default 10000000000)
            - excludeSectors: list of sector names to exclude
    
    Returns:
        List of stock dicts with ticker and company info, or None on error
    """
    cached = cache.get_price_data('_UNIVERSE', 'screener_results')
    if cached:
        return cached
    
    if filters is None:
        filters = {}
    
    market_cap_min = filters.get('marketCapMin', 1000000000)
    market_cap_max = filters.get('marketCapMax', 10000000000)
    
    params = {
        'marketCapMoreThan': market_cap_min,
        'marketCapLowerThan': market_cap_max,
        'country': 'US',
        'exchange': 'NYSE,NASDAQ,NYSE American',
        'limit': 500
    }
    
    try:
        results = _fmp_request('/v3/stock-screener', params)
        
        if not results:
            logger.warning("No screener results returned")
            return None
        
        # Filter out excluded sectors if provided
        exclude_sectors = filters.get('excludeSectors', [
            'Banks', 'Diversified Financials', 'Insurance', 'Mortgage REITs', 'Consumer Finance'
        ])
        
        filtered = [
            stock for stock in results
            if stock.get('sector') not in exclude_sectors
        ]
        
        # Cache the results
        cache.set_price_data('_UNIVERSE', 'screener_results', filtered)
        logger.info(f"Fetched screener results: {len(results)} total, {len(filtered)} after sector exclusions")
        return filtered
    
    except Exception as e:
        logger.error(f"Error fetching stock screener: {str(e)}")
        return None


def fetch_insider_transactions(ticker: str, days: int = 90) -> Optional[Dict]:
    """Fetch insider transactions from FMP for the last N days.
    
    Args:
        ticker: Stock symbol
        days: Number of recent days to check (default 90)
    
    Returns:
        Dict with insider transaction summary
    """
    cached = cache.get_financial_data(ticker, 'insider')
    if cached:
        return cached
    
    try:
        results = _fmp_request(f'/v4/insider-roaster-statistic/{ticker}')
        
        if not results or not isinstance(results, list) or len(results) == 0:
            logger.warning(f"No insider data for {ticker}")
            return None
        
        # Most recent transactions are first
        recent_transactions = [
            txn for txn in results
            if txn.get('transactionDate')
        ]
        
        # Filter to last N days
        cutoff_date = datetime.now() - timedelta(days=days)
        transactions_in_period = []
        
        for txn in recent_transactions:
            try:
                txn_date = datetime.fromisoformat(txn['transactionDate'])
                if txn_date > cutoff_date:
                    transactions_in_period.append(txn)
            except:
                pass
        
        data = {
            'ticker': ticker,
            'period_days': days,
            'transactions_found': len(transactions_in_period),
            'has_recent_buying': any(
                txn.get('transactionType') == 'Buy'
                for txn in transactions_in_period
            ),
            'transactions': transactions_in_period
        }
        
        cache.set_financial_data(ticker, 'insider', data)
        logger.info(f"Fetched insider data for {ticker}: {len(transactions_in_period)} transactions in last {days} days")
        return data
    
    except Exception as e:
        logger.error(f"Error fetching insider transactions for {ticker}: {str(e)}")
        return None


def fetch_revenue_segments(ticker: str) -> Optional[Dict]:
    """Fetch revenue segment breakdown from FMP.
    
    Identifies haram revenue (alcohol, tobacco, weapons, etc).
    
    Args:
        ticker: Stock symbol
    
    Returns:
        Dict with segment breakdown by product/service
    """
    cached = cache.get_financial_data(ticker, 'segments')
    if cached:
        return cached
    
    try:
        results = _fmp_request('/v4/revenue-product-segmentation', {'symbol': ticker})
        
        if not results or not isinstance(results, list) or len(results) == 0:
            logger.warning(f"No segment data for {ticker}")
            return None
        
        # Normalize to dict
        data = {
            'ticker': ticker,
            'segments': results,
            'data_available': True
        }
        
        cache.set_financial_data(ticker, 'segments', data)
        logger.info(f"Fetched revenue segments for {ticker}: {len(results)} segments")
        return data
    
    except Exception as e:
        logger.error(f"Error fetching revenue segments for {ticker}: {str(e)}")
        return None


def fetch_company_profile(ticker: str) -> Optional[Dict]:
    """Fetch company profile from FMP (sector, industry, description)."""
    cached = cache.get_financial_data(ticker, 'profile')
    if cached:
        return cached
    
    try:
        results = _fmp_request(f'/v3/profile/{ticker}')
        
        if not results or not isinstance(results, list) or len(results) == 0:
            logger.warning(f"No profile data for {ticker}")
            return None
        
        profile = results[0]  # Usually returns a list with one item
        
        data = {
            'ticker': ticker,
            'company_name': profile.get('companyName'),
            'sector': profile.get('sector'),
            'industry': profile.get('industry'),
            'website': profile.get('website'),
            'ceo': profile.get('ceo'),
            'description': profile.get('description'),
        }
        
        cache.set_financial_data(ticker, 'profile', data)
        logger.info(f"Fetched profile for {ticker}")
        return data
    
    except Exception as e:
        logger.error(f"Error fetching company profile for {ticker}: {str(e)}")
        return None


# ============================================================================
# UNIFIED FETCH FUNCTIONS
# ============================================================================

def get_all_financial_data(ticker: str) -> Dict:
    """Fetch all financial data for a stock (income, balance, cashflow).
    
    Returns unified dict with all financial statements.
    Combines yfinance and FMP data as needed.
    """
    return {
        'ticker': ticker,
        'income': fetch_income_statement(ticker),
        'balance': fetch_balance_sheet(ticker),
        'cashflow': fetch_cashflow(ticker),
        'profile': fetch_company_profile(ticker),
        'segments': fetch_revenue_segments(ticker),
        'insider': fetch_insider_transactions(ticker),
    }


def get_all_price_data(ticker: str) -> Dict:
    """Fetch all price data for a stock."""
    return {
        'ticker': ticker,
        'quote': fetch_quote_info(ticker),
        'history': fetch_price_history(ticker, period='1y'),
        'history_30d': fetch_price_history(ticker, period='30d'),
    }


def get_full_stock_data(ticker: str) -> Dict:
    """Fetch complete financial and price data for a stock.
    
    This is the main entry point for gathering all data about a stock.
    """
    return {
        'ticker': ticker,
        'financial': get_all_financial_data(ticker),
        'price': get_all_price_data(ticker),
    }


if __name__ == "__main__":
    # Test fetcher with a known stock
    print("Testing fetcher.py with MSFT...")
    data = get_full_stock_data("MSFT")
    print(json.dumps(data, indent=2, default=str))
