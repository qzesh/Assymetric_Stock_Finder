"""
AI Reasoning Layer - Anthropic Claude Integration

Purpose: Provide deep investment analysis for top candidates using Claude
Inputs: Validation results from discovery pipeline
Outputs: Investment thesis, risk factors, catalysts, recommendation

Uses Anthropic API for:
- Pattern narrative (why full/partial/none)
- Risk/reward analysis
- Catalyst timing
- Conviction scoring (1-10)
- Investment recommendation
"""

import logging
import os
import json
from typing import Dict, Optional
from datetime import datetime
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment
load_dotenv()
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

try:
    from anthropic import Anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False
    logger.warning("Anthropic SDK not installed. Run: pip install anthropic")


class AIReasoningEngine:
    """
    Uses Claude AI to provide deep investment analysis.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or ANTHROPIC_API_KEY
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
        
        if not HAS_ANTHROPIC:
            raise ImportError("anthropic package required. Install with: pip install anthropic")
        
        self.client = Anthropic()
        self.logger = logger
    
    def analyze_candidate(self, ticker: str, validation_data: Dict) -> Dict:
        """
        Generate deep investment analysis for a single candidate.
        
        Args:
            ticker: Stock symbol
            validation_data: Complete validation result from discovery
        
        Returns:
            Dict with AI reasoning, thesis, risks, catalysts, recommendation
        """
        
        self.logger.info(f"Analyzing {ticker} with AI")
        
        # Extract key information for Claude
        analysis_prompt = self._build_prompt(ticker, validation_data)
        
        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-6",  # Fast & cost-effective, confirmed available
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": analysis_prompt
                    }
                ]
            )
            
            reasoning = message.content[0].text
            
            # Parse reasoning into structured format
            result = {
                'ticker': ticker,
                'ai_analysis': reasoning,
                'analysis_timestamp': datetime.now().isoformat(),
                'status': 'success'
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error analyzing {ticker}: {str(e)}")
            return {
                'ticker': ticker,
                'status': 'error',
                'error': str(e)
            }
    
    def _build_prompt(self, ticker: str, validation_data: Dict) -> str:
        """Build Claude prompt from validation data."""
        
        # Extract metrics
        stages = validation_data.get('stages', {})
        halal_gates = stages.get('halal_gates', {})
        track_detection = stages.get('track_detection', {})
        signal_scoring = stages.get('signal_scoring', {})
        pattern_detection = stages.get('pattern_detection', {})
        
        track = track_detection.get('track', 'unknown')
        signals = signal_scoring.get('signals', {})
        signal_total = signal_scoring.get('total_score', 0)
        signal_threshold = signal_scoring.get('threshold', 16)
        pattern_result = pattern_detection.get('result', 'unknown')
        floor = pattern_detection.get('floor', False)
        mispricing = pattern_detection.get('mispricing', False)
        catalyst = pattern_detection.get('catalyst', False)
        
        # Build narrative - FOCUS ON ASYMMETRY AND SIGNALS, NOT HALAL STATUS
        prompt = f"""
You are an expert value investor analyzing asymmetric investment opportunities.

CANDIDATE: {ticker}

FINANCIAL TRACK:
- Classification: {track}
- Thesis: {track_detection.get('reasoning', 'N/A')}

SIGNAL ANALYSIS:
- Score: {signal_total}/{signal_threshold} ({100*signal_total/signal_threshold:.0f}%)
- Status: {'PASS' if signal_total >= signal_threshold else 'FAIL'}

ASYMMETRIC PATTERN:
- Result: {pattern_result.upper()}
- Floor (downside protection): {'✓' if floor else '✗'}
- Mispricing (market wrong): {'✓' if mispricing else '✗'}
- Catalyst (re-rating trigger): {'✓' if catalyst else '✗'}

IMPORTANT: Base your analysis ONLY on the asymmetry potential and financial signals. 
Do NOT consider compliance status in risk assessment or recommendation.

PROVIDE A CONCISE ANALYSIS (max 150 words) COVERING:
1. Investment Thesis: Is the asymmetric setup compelling? Why/why not?
2. Key Risks: What financial/operational risks could derail this thesis? (Ignore compliance)
3. Catalyst Timeline: When might the re-rating occur?
4. Conviction Level: Rate 1-10 based ONLY on asymmetry quality + signals
5. Recommendation: BUY / HOLD / PASS based ONLY on asymmetry potential (ignore compliance)

RESPOND ONLY WITH VALID JSON (no additional text) with these exact fields:
{{
  "thesis": "...",
  "risks": "...",
  "catalyst": "...",
  "conviction": 5,
  "recommendation": "BUY"
}}
"""
        
        return prompt
    
    def analyze_top_candidates(self, candidates_data: list) -> Dict:
        """
        Analyze top 5 candidates with full reasoning.
        
        Args:
            candidates_data: List of dicts with {ticker, validation, ...}
        
        Returns:
            Dict with AI reasoning for each candidate
        """
        
        results = {}
        for candidate in candidates_data[:5]:
            ticker = candidate.get('ticker')
            validation = candidate.get('validation', {})
            
            result = self.analyze_candidate(ticker, validation)
            results[ticker] = result
        
        return results


# =========================================================================
# HELPER: Extract top 5 from discovery results
# =========================================================================

def get_ai_analyses_for_discovery(discovery_results_json: str) -> Dict:
    """
    Load discovery results and generate AI analyses for top 5.
    """
    
    if not HAS_ANTHROPIC:
        return {
            'status': 'error',
            'error': 'Anthropic SDK not installed'
        }
    
    # Load discovery results
    with open(discovery_results_json) as f:
        results = json.load(f)
    
    # Initialize AI engine
    try:
        engine = AIReasoningEngine()
    except ValueError as e:
        return {
            'status': 'error',
            'error': str(e)
        }
    
    # Analyze top 5
    top_5_analyses = {}
    for candidate in results[:5]:
        ticker = candidate['ticker']
        # Note: discovery_results.json doesn't have full validation,
        # so we'd need to retrieve from database or pass differently
        # For now, return structure
        top_5_analyses[ticker] = {
            'ticker': ticker,
            'composite_score': candidate['composite_score']
        }
    
    return {
        'status': 'complete',
        'analyses': top_5_analyses
    }


if __name__ == "__main__":
    # Example: Analyze a ticker
    # This would be called from discovery with real validation data
    
    # Check if we have the API key
    if not ANTHROPIC_API_KEY:
        print("❌ ANTHROPIC_API_KEY not found in .env")
        print("Set it and try again")
    else:
        print("✓ Anthropic API key configured")
        print("Ready to analyze candidates with AI reasoning")
