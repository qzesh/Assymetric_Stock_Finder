"""
Step 8: Discovery Workflow

Purpose: Run complete validation on all screened candidates
Output: Ranked list of top opportunities by asymmetry conviction

Features:
- SQLite checkpointing for rate limit recovery
- Parallel processing where possible
- Comprehensive ranking (asymmetry score + signal strength)
- Top 5 candidates with full reasoning for AI layer
"""

import logging
import json
import sqlite3
import time
from typing import Dict, List, Optional
from datetime import datetime

from screener import ScreenerEngine, format_screening_results
from validation import ValidationWorkflow, format_validation_result

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DiscoveryWorkflow:
    """
    Multi-stock discovery pipeline with checkpointing and ranking.
    """
    
    def __init__(self, checkpoint_db: str = 'discovery_checkpoint.db'):
        self.checkpoint_db = checkpoint_db
        self.screener = ScreenerEngine()
        self.validator = ValidationWorkflow()
        self.logger = logger
        self._init_checkpoint_db()
    
    def _init_checkpoint_db(self):
        """Initialize SQLite checkpoint database."""
        conn = sqlite3.connect(self.checkpoint_db)
        cursor = conn.cursor()
        
        # Create checkpoint table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS discovery_runs (
                run_id TEXT PRIMARY KEY,
                started_at TEXT,
                completed_at TEXT,
                status TEXT
            )
        ''')
        
        # Create analysis results table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_results (
                ticker TEXT PRIMARY KEY,
                run_id TEXT,
                validation_result TEXT,
                asymmetry_score REAL,
                signal_score REAL,
                ranking_position INTEGER,
                analyzed_at TEXT
            )
        ''')
        
        # Create AI analysis cache table (NEW)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_analysis_cache (
                ticker TEXT PRIMARY KEY,
                ai_analysis TEXT,
                cached_at TEXT,
                expires_at TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        self.logger.info(f"Checkpoint database initialized: {self.checkpoint_db}")
    
    # =====================================================================
    # MAIN DISCOVERY WORKFLOW
    # =====================================================================
    
    def discover(self, run_id: Optional[str] = None) -> Dict:
        """
        Run complete discovery pipeline: screen → validate → rank.
        
        Returns:
            Dict with screener results, validation results, and top 5 candidates
        """
        
        if not run_id:
            run_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        self.logger.info(f"Starting discovery run: {run_id}")
        
        result = {
            'run_id': run_id,
            'started_at': datetime.now().isoformat(),
            'screening': None,
            'validation_results': {},
            'ranking': None,
            'top_5': [],
            'status': 'processing'
        }
        
        # ===================================================================
        # PHASE 1: SCREENING
        # ===================================================================
        
        self.logger.info("Phase 1: Screening universe")
        screening_result = self.screener.screen_universe()
        result['screening'] = screening_result
        
        candidates = screening_result.get('candidates', [])
        self.logger.info(f"Found {len(candidates)} qualified candidates")
        
        if not candidates:
            result['status'] = 'error'
            result['error'] = 'No candidates from screener'
            return result
        
        # ===================================================================
        # PHASE 2: VALIDATION (with checkpointing)
        # ===================================================================
        
        self.logger.info(f"Phase 2: Validating {len(candidates)} candidates")
        validation_results = self._validate_candidates(run_id, candidates)
        result['validation_results'] = validation_results
        
        # ===================================================================
        # PHASE 3: RANKING
        # ===================================================================
        
        self.logger.info("Phase 3: Ranking candidates")
        ranking = self._rank_candidates(validation_results)
        result['ranking'] = ranking
        
        # Extract top 5
        top_5 = [
            {
                'rank': entry['rank'],
                'ticker': entry['ticker'],
                'asymmetry_score': entry['asymmetry_score'],
                'signal_score': entry['signal_score'],
                'composite_score': entry['composite_score'],
                'halal_status': entry['halal_status'],
                'track': entry['track'],
                'pattern': entry['pattern'],
                'conviction': entry['conviction'],
            }
            for entry in ranking[:5]
        ]
        result['top_5'] = top_5
        
        # ===================================================================
        # PHASE 4: BATCH GENERATE CLAUDE AI ANALYSIS (CACHED)
        # ===================================================================
        
        self.logger.info("Phase 4: Batch generating Claude AI analysis for top 5")
        self._batch_generate_ai_analysis(ranking[:5], validation_results)
        
        result['completed_at'] = datetime.now().isoformat()
        result['status'] = 'complete'
        
        self.logger.info(f"Discovery complete. Top candidate: {ranking[0]['ticker'] if ranking else 'None'}")
        return result
    
    # =====================================================================
    # PHASE 2: VALIDATION WITH CHECKPOINTING
    # =====================================================================
    
    def _validate_candidates(self, run_id: str, candidates: List[str]) -> Dict:
        """
        Validate all candidates with SQLite checkpointing for rate limits.
        """
        
        results = {}
        
        for i, ticker in enumerate(candidates, 1):
            try:
                self.logger.info(f"[{i}/{len(candidates)}] Validating {ticker}")
                
                # Run validation
                validation = self.validator.validate_ticker(ticker)
                results[ticker] = validation
                
                # Save checkpoint
                self._save_checkpoint(run_id, ticker, validation)
                
                # Rate limiting - be gentle with yfinance
                if i < len(candidates):
                    time.sleep(0.5)
                
            except Exception as e:
                self.logger.error(f"Error validating {ticker}: {str(e)}")
                results[ticker] = {
                    'ticker': ticker,
                    'status': 'error',
                    'error': str(e)
                }
        
        return results
    
    def _save_checkpoint(self, run_id: str, ticker: str, validation_result: Dict):
        """Save validation result to checkpoint database."""
        try:
            conn = sqlite3.connect(self.checkpoint_db)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO analysis_results
                (ticker, run_id, validation_result, analyzed_at)
                VALUES (?, ?, ?, ?)
            ''', (
                ticker,
                run_id,
                json.dumps(validation_result),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            self.logger.error(f"Error saving checkpoint for {ticker}: {str(e)}")
    
    # =====================================================================
    # PHASE 4: BATCH CLAUDE AI ANALYSIS GENERATION & CACHING
    # =====================================================================
    
    def _batch_generate_ai_analysis(self, top_candidates: List[Dict], validation_results: Dict):
        """
        Batch generate Claude AI analysis for top candidates and cache results.
        Cache expires after 14 days.
        """
        try:
            from ai_reasoner import AIReasoningEngine
            reasoner = AIReasoningEngine()
            
            for candidate in top_candidates:
                ticker = candidate['ticker']
                
                # Check if valid cache exists (not expired)
                if self._has_valid_cache(ticker):
                    self.logger.info(f"{ticker}: Using cached AI analysis (valid for 14 days)")
                    continue
                
                # Generate new analysis
                try:
                    validation = validation_results.get(ticker, {})
                    result = reasoner.analyze_candidate(ticker, validation)
                    
                    if result.get('status') == 'success':
                        ai_analysis = result.get('ai_analysis', '')
                        self._cache_ai_analysis(ticker, ai_analysis)
                        self.logger.info(f"{ticker}: Claude analysis cached successfully")
                    else:
                        self.logger.warning(f"{ticker}: Claude analysis failed - {result.get('error')}")
                        
                except Exception as e:
                    self.logger.error(f"{ticker}: Error generating Claude analysis - {str(e)}")
                
                # Rate limit - be nice to Claude API
                time.sleep(1)
        
        except ImportError:
            self.logger.warning("AI reasoner not available - skipping Claude analysis caching")
    
    def _has_valid_cache(self, ticker: str) -> bool:
        """Check if valid (non-expired) cache exists for ticker."""
        try:
            conn = sqlite3.connect(self.checkpoint_db)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT expires_at FROM ai_analysis_cache 
                WHERE ticker = ? AND expires_at > datetime('now')
            ''', (ticker,))
            
            result = cursor.fetchone()
            conn.close()
            
            return result is not None
        except Exception as e:
            self.logger.error(f"Error checking cache for {ticker}: {str(e)}")
            return False
    
    def _cache_ai_analysis(self, ticker: str, ai_analysis: str):
        """Cache Claude AI analysis with 14-day expiration."""
        try:
            from datetime import timedelta
            conn = sqlite3.connect(self.checkpoint_db)
            cursor = conn.cursor()
            
            now = datetime.now()
            expires_at = (now + timedelta(days=14)).isoformat()
            
            cursor.execute('''
                INSERT OR REPLACE INTO ai_analysis_cache
                (ticker, ai_analysis, cached_at, expires_at)
                VALUES (?, ?, ?, ?)
            ''', (ticker, ai_analysis, now.isoformat(), expires_at))
            
            conn.commit()
            conn.close()
        except Exception as e:
            self.logger.error(f"Error caching analysis for {ticker}: {str(e)}")
    
    # =====================================================================
    # PHASE 3: RANKING
    # =====================================================================
    
    def _rank_candidates(self, validation_results: Dict) -> List[Dict]:
        """
        Rank candidates by composite score = asymmetry + signals.
        
        Asymmetry score tiers:
        - full: +3.0 (maximum upside)
        - partial: +1.5 (moderate upside)
        - not_asymmetric: +0.0 (no special pattern)
        
        Signal score: normalized to 0-3.0 scale
        """
        
        ranked = []
        
        for ticker, validation in validation_results.items():
            # Skip errors
            if validation.get('status') == 'error':
                continue
            
            # Extract key metrics
            halal_status = validation.get('stages', {}).get('halal_gates', {}).get('halal_status', 'unknown')
            track = validation.get('stages', {}).get('track_detection', {}).get('track', 'unknown')
            pattern_type = validation.get('stages', {}).get('pattern_detection', {}).get('result', 'not_asymmetric')
            signal_score = validation.get('stages', {}).get('signal_scoring', {}).get('total_score', 0)
            signal_threshold = validation.get('stages', {}).get('signal_scoring', {}).get('threshold', 16)
            conviction = validation.get('stages', {}).get('pattern_detection', {}).get('conviction_max', 'low')
            
            # Skip if halal failed
            if halal_status == 'fail':
                self.logger.info(f"{ticker}: Halal FAIL - skipping from ranking")
                continue
            
            # Calculate asymmetry score (0-3 scale)
            asymmetry_scores = {
                'full': 3.0,
                'partial': 1.5,
                'not_asymmetric': 0.0
            }
            asymmetry_score = asymmetry_scores.get(pattern_type, 0.0)
            
            # Normalize signal score (0-3 scale)
            signal_normalized = min(3.0, (signal_score / signal_threshold) * 3.0)
            
            # Composite score: 60% asymmetry, 40% signals
            composite_score = (asymmetry_score * 0.60) + (signal_normalized * 0.40)
            
            ranked.append({
                'rank': 0,  # Will be set after sorting
                'ticker': ticker,
                'asymmetry_score': asymmetry_score,
                'signal_score': signal_normalized,
                'signal_raw': signal_score,
                'composite_score': composite_score,
                'halal_status': halal_status,
                'pattern': pattern_type,
                'conviction': conviction,
                'validation': validation
            })
        
        # Sort by composite score (descending)
        ranked = sorted(ranked, key=lambda x: x['composite_score'], reverse=True)
        
        # Add ranks
        for i, entry in enumerate(ranked, 1):
            entry['rank'] = i
        
        return ranked


# =========================================================================
# FORMATTING & DISPLAY
# =========================================================================

def format_discovery_results(result: Dict) -> str:
    """Format discovery results for display."""
    
    lines = [
        "\n" + "="*80,
        "✅ DISCOVERY WORKFLOW COMPLETE",
        "="*80,
    ]
    
    # Summary
    screening = result.get('screening', {})
    lines.extend([
        "",
        f"Screening Results: {screening.get('count', 0)} candidates",
        f"  Range: {screening.get('applied_filters', {}).get('reduction', 'unknown')}",
    ])
    
    # Top 5
    top_5 = result.get('top_5', [])
    if top_5:
        lines.extend([
            "",
            "Top 5 Opportunities:",
            "-" * 80,
        ])
        
        for candidate in top_5:
            lines.extend([
                f"",
                f"#{candidate['rank']}. {candidate['ticker']} (Score: {candidate['composite_score']:.2f})",
                f"    Asymmetry: {candidate['asymmetry_score']:.1f} ({candidate['pattern'].upper()})",
                f"    Signals: {candidate['signal_score']:.1f} ({candidate['track']})",
                f"    Halal: {candidate['halal_status'].upper()} | Conviction: {candidate['conviction'].upper()}",
            ])
    
    lines.append("="*80)
    return "\n".join(lines)


if __name__ == "__main__":
    # Run full discovery
    workflow = DiscoveryWorkflow()
    result = workflow.discover()
    
    # Display results
    print(format_discovery_results(result))
    
    # Save full results
    with open('discovery_results.json', 'w') as f:
        # JSON-serialize the results (remove validation objects)
        clean_result = {
            'run_id': result['run_id'],
            'started_at': result['started_at'],
            'completed_at': result['completed_at'],
            'screening': result['screening'],
            'ranking': [
                {
                    k: v for k, v in entry.items()
                    if k != 'validation'
                } for entry in result.get('ranking', [])
            ],
            'top_5': result['top_5'],
            'status': result['status'],
        }
        json.dump(clean_result, f, indent=2)
    
    print(f"\nFull results saved to: discovery_results.json")
