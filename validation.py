"""
Validation Workflow - Complete end-to-end pipeline for single-stock analysis.

Input: User provides a ticker
Output: Full analysis with halal gates, track detection, signal scoring, pattern detection, and AI-ready structured data

Flow:
1. Fetch all financial data for ticker (via fetcher.py)
2. Run all 4 halal gates in sequence (halal.py)
3. If passes halal, auto-detect track (tracker.py)
4. Score all applicable signals (scorer.py)
5. Detect asymmetric pattern (detector.py)
6. Generate structured output ready for AI reasoning

IMPORTANT: Produces full analysis REGARDLESS of pattern result.
Investor brought this ticker intentionally and deserves the complete picture.
"""

import logging
import json
from typing import Dict, Optional
from datetime import datetime

# Import all the pipeline stages
from fetcher import get_full_stock_data
from halal import HalalGateEngine, prepare_halal_evaluation_data
from tracker import TrackRouter
from scorer import SignalScorer
from detector import AsymmetricPatternDetector

logger = logging.getLogger(__name__)


class ValidationWorkflow:
    """End-to-end validation pipeline for a single ticker."""
    
    def __init__(self):
        self.halal_engine = HalalGateEngine()
        self.track_router = TrackRouter()
        self.signal_scorer = SignalScorer()
        self.pattern_detector = AsymmetricPatternDetector()
        self.logger = logger
    
    def validate_ticker(self, ticker: str) -> Dict:
        """
        Run complete validation workflow on a single ticker.
        
        Args:
            ticker: Stock symbol (e.g. 'MSFT')
        
        Returns:
            Complete analysis dict with all stages + results
        """
        
        self.logger.info(f"Starting validation for {ticker}")
        
        result = {
            'ticker': ticker,
            'timestamp': datetime.now().isoformat(),
            'status': 'processing',
            'error': None,
            'stages': {
                'data_fetch': None,
                'halal_gates': None,
                'track_detection': None,
                'signal_scoring': None,
                'pattern_detection': None,
            },
            'final_verdict': None,
        }
        
        # ===================================================================
        # STAGE 1: FETCH ALL DATA
        # ===================================================================
        
        self.logger.info(f"{ticker}: Stage 1 - Fetching data")
        try:
            stock_data = get_full_stock_data(ticker)
            result['stages']['data_fetch'] = {
                'status': 'success',
                'timestamp': datetime.now().isoformat(),
            }
        except Exception as e:
            result['status'] = 'error'
            result['error'] = f'Data fetch failed: {str(e)}'
            self.logger.error(f"{ticker}: Data fetch error: {str(e)}")
            return result
        
        # Extract data structures for easier access
        financial_data = stock_data.get('financial', {})
        price_data = stock_data.get('price', {})
        
        # ===================================================================
        # STAGE 2: RUN HALAL GATES
        # ===================================================================
        
        self.logger.info(f"{ticker}: Stage 2 - Halal gates")
        
        # Extract halal evaluation data
        halal_eval_data = prepare_halal_evaluation_data(
            financial_data, 
            price_data
        )
        
        # Note: Gate 4 (loss financing) needs additional context
        # For now, we'll pass None for debt_funded_loss (will be flagged as unverified if Track B)
        
        halal_result = self.halal_engine.evaluate_all_gates(
            ticker=ticker,
            sector=halal_eval_data.get('sector'),
            total_revenue=halal_eval_data.get('total_revenue'),
            total_debt=halal_eval_data.get('total_debt'),
            market_cap_30d_avg=halal_eval_data.get('market_cap_30d_avg'),
            segments=halal_eval_data.get('segments'),
            fcf_history=None,  # Will be extracted from track routing
            track=None,  # Will set this after track detection
            debt_funded_loss=None,
        )
        
        result['stages']['halal_gates'] = halal_result
        
        # If halal FAILS (not pass/unverified), stop here
        if halal_result['halal_status'] == 'fail':
            result['status'] = 'complete'
            result['final_verdict'] = f"ANALYSIS HALTED: Stock failed halal compliance gate. {halal_result['halal_verdict']}"
            self.logger.warning(f"{ticker}: Halal gate failure - terminating validation")
            return result
        
        # ===================================================================
        # STAGE 3: DETECT TRACK
        # ===================================================================
        
        self.logger.info(f"{ticker}: Stage 3 - Track detection")
        
        # Extract cashflow data for track detection
        cashflow_data = financial_data.get('cashflow')
        
        track_result = self.track_router.detect_track_from_cashflow_data(
            ticker, cashflow_data
        )
        result['stages']['track_detection'] = track_result
        track = track_result.get('track')
        
        # If track detection fails, we can't proceed
        if not track:
            result['status'] = 'incomplete'
            result['final_verdict'] = f"Cannot determine track: {track_result.get('warning', 'Unknown reason')}"
            self.logger.warning(f"{ticker}: Track detection failed")
            return result
        
        # Re-run halal gates with track-specific checks (Gate 4)
        # Update the halal result with track info
        halal_result['gates']['gate4_loss_financing'] = \
            self.halal_engine._gate4_loss_financing(ticker, track, track_result.get('fcf_history_clean'), None)
        
        result['stages']['halal_gates'] = halal_result
        
        # ===================================================================
        # STAGE 4: SCORE SIGNALS
        # ===================================================================
        
        self.logger.info(f"{ticker}: Stage 4 - Signal scoring")
        
        # Extract financial data components
        income_data = financial_data.get('income')
        balance_data = financial_data.get('balance')
        quote_data = price_data.get('quote')
        insider_data = financial_data.get('insider')
        price_history = price_data.get('history')
        
        # Score based on track
        if track == 'A' or track == 'A-Transition':
            signal_result = self.signal_scorer.score_track_a(
                ticker=ticker,
                income_data=income_data,
                balance_data=balance_data,
                cashflow_data=cashflow_data,
                quote_data=quote_data,
                insider_data=insider_data,
                price_history=price_history,
            )
        else:  # Track B
            signal_result = self.signal_scorer.score_track_b(
                ticker=ticker,
                income_data=income_data,
                balance_data=balance_data,
                cashflow_data=cashflow_data,
                quote_data=quote_data,
                insider_data=insider_data,
            )
        
        result['stages']['signal_scoring'] = signal_result
        
        # If signal score doesn't meet minimum threshold, note it
        if not signal_result['passes']:
            self.logger.warning(
                f"{ticker}: Signal score {signal_result['total_score']}/{signal_result['max_score']} "
                f"below threshold {signal_result['pass_threshold']}"
            )
        
        # ===================================================================
        # STAGE 5: DETECT ASYMMETRIC PATTERN
        # ===================================================================
        
        self.logger.info(f"{ticker}: Stage 5 - Pattern detection")
        
        pattern_result = self.pattern_detector.detect_pattern(
            ticker=ticker,
            track=track,
            signal_data=signal_result.get('signals', {}),
            price_data=quote_data,
            insider_data=insider_data,
            fcf_history=track_result.get('fcf_history_clean'),
            income_data=income_data,
        )
        
        result['stages']['pattern_detection'] = pattern_result
        
        # Extract conviction level from pattern detection
        result['conviction'] = pattern_result.get('conviction_max', 'low')
        
        # ===================================================================
        # GENERATE FINAL VERDICT
        # ===================================================================
        
        # AI-ready structured data for next step
        ai_input = self._prepare_ai_input(
            ticker=ticker,
            track=track,
            halal_result=halal_result,
            signal_result=signal_result,
            pattern_result=pattern_result,
            price_data=quote_data,
        )
        
        result['ai_input'] = ai_input
        result['status'] = 'complete'
        
        # Generate plain English verdict
        verdict_parts = [
            f"TICKER: {ticker} | TRACK: {track} | HALAL: {halal_result['halal_status'].upper()}",
            f"SIGNALS: {signal_result['total_score']}/{signal_result['max_score']} "
            f"({'PASS' if signal_result['passes'] else 'FAIL'})",
            f"PATTERN: {pattern_result['result'].upper()} | MAX CONVICTION: {pattern_result['conviction_max'].upper()}",
        ]
        
        result['final_verdict'] = ' | '.join(verdict_parts)
        
        self.logger.info(f"{ticker}: Validation complete - {result['final_verdict']}")
        return result
    
    def _prepare_ai_input(
        self,
        ticker: str,
        track: str,
        halal_result: Dict,
        signal_result: Dict,
        pattern_result: Dict,
        price_data: Optional[Dict]
    ) -> Dict:
        """
        Prepare structured input for AI reasoning stage.
        
        This is what gets passed to Claude for deep analysis.
        """
        
        return {
            'ticker': ticker,
            'track': track,
            'halal_status': halal_result.get('halal_status'),
            'halal_flags': halal_result.get('flags', []),
            'signals': signal_result.get('signals', {}),
            'total_score': signal_result.get('total_score'),
            'signal_pass': signal_result.get('passes'),
            'pattern_result': pattern_result.get('result'),
            'pattern_components': {
                'floor': pattern_result.get('floor'),
                'floor_reason': pattern_result.get('floor_reason'),
                'mispricing': pattern_result.get('mispricing'),
                'mispricing_reason': pattern_result.get('mispricing_reason'),
                'catalyst': pattern_result.get('catalyst'),
                'catalyst_reason': pattern_result.get('catalyst_reason'),
            },
            'conviction_max': pattern_result.get('conviction_max'),
            'current_price': price_data.get('currentPrice') if price_data else None,
            'market_cap': price_data.get('marketCap') if price_data else None,
        }


def format_validation_result(result: Dict) -> str:
    """Format validation result for human-readable output."""
    
    ticker = result.get('ticker')
    status = result.get('status')
    
    if status == 'error':
        return f"❌ {ticker}: {result.get('error', 'Unknown error')}"
    
    final_verdict = result.get('final_verdict', 'Unknown')
    return f"✅ {ticker}: {final_verdict}"


if __name__ == "__main__":
    # Quick test initialization
    workflow = ValidationWorkflow()
    print("ValidationWorkflow initialized successfully")
    print("\nStages:")
    print("1. Data Fetch (via fetcher.py)")
    print("2. Halal Gates (4 sequential gates)")
    print("3. Track Detection (A, A-Transition, or B)")
    print("4. Signal Scoring (8 signals per track)")
    print("5. Pattern Detection (Floor, Mispricing, Catalyst)")
    print("\nOutputs structured JSON ready for AI reasoning")
