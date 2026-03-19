"""
Halal Status Cache Manager with Claude AI Verification

Features:
- 30-day halal status caching using SQLite
- Automatic Claude AI verification when cache expires
- Batch updates for efficiency
- Dashboard integration-ready
"""

import logging
import json
import sqlite3
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()


class HalalStatusCache:
    """
    SQLite cache for halal status results with 30-day expiry.
    Automatic Claude AI re-verification when cache expires.
    """
    
    def __init__(self, db_path: str = "cache.db"):
        self.db_path = db_path
        self.cache_ttl_days = 30  # Cache expires after 30 days
        self._init_db()
        self._import_halal_engine()
    
    def _import_halal_engine(self):
        """Lazy import halal engine to avoid circular dependencies."""
        try:
            from halal import HalalGateEngine
            self.halal_engine = HalalGateEngine()
            self.has_halal_engine = True
        except ImportError:
            logger.warning("HalalGateEngine not available")
            self.has_halal_engine = False
    
    def _init_db(self):
        """Initialize halal cache table if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS halal_status_cache (
                ticker TEXT PRIMARY KEY,
                halal_status TEXT NOT NULL,
                gates_json TEXT,
                first_failure TEXT,
                flags_json TEXT,
                halal_verdict TEXT,
                claude_review TEXT,
                cached_at REAL NOT NULL,
                expires_at REAL NOT NULL,
                created_at TEXT NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"Halal cache initialized: {self.db_path}")
    
    # =====================================================================
    # CACHE OPERATIONS
    # =====================================================================
    
    def get_cached_halal_status(self, ticker: str) -> Optional[Dict]:
        """
        Retrieve cached halal status if still fresh (< 30 days).
        Returns None if expired or missing.
        
        Args:
            ticker: Stock symbol
        
        Returns:
            Dict with cached halal status or None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT * FROM halal_status_cache WHERE ticker = ?',
            (ticker,)
        )
        result = cursor.fetchone()
        conn.close()
        
        if result:
            # Parse result
            (ticker_col, halal_status, gates_json, first_failure, flags_json,
             halal_verdict, claude_review, cached_at, expires_at, created_at) = result
            
            current_time = time.time()
            
            # Check if cache is still fresh
            if current_time < expires_at:
                days_old = (current_time - cached_at) / 86400
                logger.info(f"Cache hit: {ticker} halal status ({days_old:.1f} days old)")
                
                return {
                    'ticker': ticker,
                    'halal_status': halal_status,
                    'gates': json.loads(gates_json) if gates_json else None,
                    'first_failure': first_failure,
                    'flags': json.loads(flags_json) if flags_json else [],
                    'halal_verdict': halal_verdict,
                    'claude_review': claude_review,
                    'cached': True,
                    'cache_age_days': days_old,
                    'created_at': created_at
                }
            else:
                logger.info(f"Cache expired: {ticker} halal status (expires at {datetime.fromtimestamp(expires_at)})")
        
        return None
    
    def set_cached_halal_status(
        self,
        ticker: str,
        halal_result: Dict
    ):
        """
        Cache halal evaluation result for 30 days.
        
        Args:
            ticker: Stock symbol
            halal_result: Result from HalalGateEngine.evaluate_all_gates()
        """
        current_time = time.time()
        expires_at = current_time + (self.cache_ttl_days * 86400)
        created_at = datetime.now().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            '''INSERT OR REPLACE INTO halal_status_cache
               (ticker, halal_status, gates_json, first_failure, flags_json,
                halal_verdict, claude_review, cached_at, expires_at, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (
                ticker,
                halal_result.get('halal_status'),
                json.dumps(halal_result.get('gates')),
                halal_result.get('first_failure'),
                json.dumps(halal_result.get('flags', [])),
                halal_result.get('halal_verdict'),
                halal_result.get('claude_review'),
                current_time,
                expires_at,
                created_at
            )
        )
        
        conn.commit()
        conn.close()
        logger.info(f"Cached halal status for {ticker} (expires in {self.cache_ttl_days} days)")
    
    def clear_cache(self, ticker: str):
        """Delete cached halal status for a stock."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM halal_status_cache WHERE ticker = ?', (ticker,))
        conn.commit()
        conn.close()
        logger.info(f"Cleared halal cache for {ticker}")
    
    def clear_expired_cache(self):
        """Delete all expired halal cache entries."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        current_time = time.time()
        cursor.execute(
            'DELETE FROM halal_status_cache WHERE expires_at < ?',
            (current_time,)
        )
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        if deleted_count > 0:
            logger.info(f"Deleted {deleted_count} expired halal cache entries")
        
        return deleted_count
    
    # =====================================================================
    # INTEGRATION WITH FETCHER + HALAL ENGINE
    # =====================================================================
    
    def get_halal_status_with_cache(
        self,
        ticker: str,
        financial_data: Optional[Dict] = None,
        price_data: Optional[Dict] = None,
        force_refresh: bool = False
    ) -> Dict:
        """
        Get halal status with automatic cache + Claude AI verification.
        
        Strategy:
        1. Check cache - if fresh and valid, return cached result
        2. If cache expired, fetch fresh data and re-verify with Claude AI
        3. Update cache with result
        
        Args:
            ticker: Stock symbol
            financial_data: Optional financial data (if None, will fetch from fetcher)
            price_data: Optional price data (if None, will fetch from fetcher)
            force_refresh: Force re-evaluation even if cache is fresh
        
        Returns:
            Halal status dict with 'cached' flag indicating if from cache
        """
        
        # Step 1: Check cache
        if not force_refresh:
            cached_result = self.get_cached_halal_status(ticker)
            if cached_result:
                return cached_result
        
        # Step 2: Fetch fresh data if not provided
        if financial_data is None or price_data is None:
            try:
                from fetcher import get_full_stock_data
                logger.info(f"Fetching fresh data for {ticker}")
                stock_data = get_full_stock_data(ticker)
                financial_data = stock_data.get('financial', {})
                price_data = stock_data.get('price', {})
            except Exception as e:
                logger.error(f"Could not fetch data for {ticker}: {e}")
                # Return cached result if available, even if expired
                cached = self.get_cached_halal_status(ticker)
                if cached:
                    cached['cached'] = True
                    cached['note'] = 'Using expired cache due to fetch error'
                    return cached
                raise
        
        # Step 3: Prepare halal evaluation data
        try:
            from halal import prepare_halal_evaluation_data
            halal_eval_data = prepare_halal_evaluation_data(
                financial_data,
                price_data
            )
        except Exception as e:
            logger.error(f"Could not prepare halal data for {ticker}: {e}")
            raise
        
        # Step 4: Run halal gates with Claude AI
        if not self.has_halal_engine:
            self._import_halal_engine()
        
        if not self.has_halal_engine:
            logger.error("HalalGateEngine not available")
            raise RuntimeError("HalalGateEngine required for halal verification")
        
        logger.info(f"Running halal verification for {ticker} with Claude AI")
        halal_result = self.halal_engine.evaluate_all_gates(
            ticker=ticker,
            sector=halal_eval_data.get('sector'),
            total_revenue=halal_eval_data.get('total_revenue'),
            total_debt=halal_eval_data.get('total_debt'),
            market_cap_30d_avg=halal_eval_data.get('market_cap_30d_avg'),
            segments=halal_eval_data.get('segments'),
            fcf_history=None,
            track=None,
            debt_funded_loss=None
        )
        
        # Step 5: Cache the result
        self.set_cached_halal_status(ticker, halal_result)
        
        # Add cache indicators
        halal_result['cached'] = False
        halal_result['cache_age_days'] = 0
        
        return halal_result
    
    # =====================================================================
    # BATCH OPERATIONS (For Dashboard/Discovery)
    # =====================================================================
    
    def get_halal_status_batch(
        self,
        tickers: List[str],
        force_refresh: bool = False
    ) -> Dict[str, Dict]:
        """
        Get halal status for multiple tickers efficiently.
        Uses cache for fresh entries, Claude AI for expired ones.
        
        Args:
            tickers: List of stock symbols
            force_refresh: Force re-evaluation for all
        
        Returns:
            Dict mapping ticker -> halal_status_dict
        """
        results = {}
        
        for ticker in tickers:
            try:
                result = self.get_halal_status_with_cache(
                    ticker,
                    force_refresh=force_refresh
                )
                results[ticker] = result
            except Exception as e:
                logger.error(f"Error getting halal status for {ticker}: {e}")
                results[ticker] = {
                    'ticker': ticker,
                    'halal_status': 'error',
                    'error': str(e),
                    'cached': False
                }
        
        return results
    
    def get_cache_stats(self) -> Dict:
        """
        Get cache statistics for monitoring.
        
        Returns:
            Dict with cache size, hit count, expiry stats
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total cached entries
        cursor.execute('SELECT COUNT(*) FROM halal_status_cache')
        total_count = cursor.fetchone()[0]
        
        # Fresh entries (not expired)
        current_time = time.time()
        cursor.execute(
            'SELECT COUNT(*) FROM halal_status_cache WHERE expires_at > ?',
            (current_time,)
        )
        fresh_count = cursor.fetchone()[0]
        
        # Expired entries
        cursor.execute(
            'SELECT COUNT(*) FROM halal_status_cache WHERE expires_at <= ?',
            (current_time,)
        )
        expired_count = cursor.fetchone()[0]
        
        # Status distribution
        cursor.execute('''
            SELECT halal_status, COUNT(*) as count 
            FROM halal_status_cache 
            WHERE expires_at > ?
            GROUP BY halal_status
        ''', (current_time,))
        status_dist = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            'total_cached': total_count,
            'fresh_entries': fresh_count,
            'expired_entries': expired_count,
            'status_distribution': status_dist,
            'cache_ttl_days': self.cache_ttl_days
        }
    
    # =====================================================================
    # UTILITY METHODS
    # =====================================================================
    
    def format_for_display(self, halal_result: Dict) -> Dict:
        """Format halal result for dashboard display."""
        return {
            'Status': halal_result.get('halal_status', 'unknown').upper(),
            'Verdict': halal_result.get('halal_verdict', ''),
            'Cached': '✓' if halal_result.get('cached') else '✗fresh',
            'Age': f"{halal_result.get('cache_age_days', 0):.0f}d" if halal_result.get('cached') else 'new',
            'ClaudeReview': 'Yes' if halal_result.get('claude_review') else 'No'
        }


# Initialize singleton cache instance
_cache_instance = None

def get_halal_cache() -> HalalStatusCache:
    """Get or create the halal cache singleton."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = HalalStatusCache()
    return _cache_instance


if __name__ == "__main__":
    # Quick test
    cache = HalalStatusCache()
    
    print("Testing halal cache system...")
    print(f"Cache stats: {cache.get_cache_stats()}")
    print("\nCache ready for integration with dashboard and search!")
