"""
Halal Compliance Framework - Four Sequential Gates

Every stock must pass all four gates in sequence. Failure at any gate is immediate elimination.
No further processing occurs for a failed stock.

Gate 1: Riba Business Model (sector-based, no financial data needed)
Gate 2: Debt Ratio (total debt / 30-day avg market cap < 33%)
Gate 3: Haram Revenue (prohibited activities < 5% of total revenue)
Gate 4: Loss Financing (Track B only - equity-funded losses, not debt-funded)
"""

import logging
import os
from typing import Dict, Optional, List, Tuple
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


# GATE 1: Riba Business Model Auto-Fail Sectors
RIBA_AUTO_FAIL_SECTORS = {
    'Banks',
    'Diversified Financials',
    'Financial Services',
    'Insurance',
    'Mortgage REITs',
    'Real Estate Investment Trusts',
    'Consumer Finance',
    'Finance',
    'Financial',
    'Capital Markets',
}

# GATE 3: Prohibited Revenue Categories (Haram)
PROHIBITED_REVENUE_KEYWORDS = {
    'alcohol',
    'beer',
    'liquor',
    'spirits',
    'wine',
    'tobacco',
    'cigarette',
    'cigar',
    'weapons',
    'ammunition',
    'defense',
    'arms',
    'gun',
    'missile',
    'bomb',
    'adult entertainment',
    'pornography',
    'casino',
    'gambling',
    'pork',
    'conventional finance',
    'interest-bearing',
    'interest income',
    'lending',
    'loan interest',
}


class HalalGateEngine:
    """
    Evaluates stocks against four halal compliance gates.
    Gates run in sequence. First failure stops processing.
    
    Returns structured halal_status (pass, fail, or unverified) + reasons.
    """
    
    def __init__(self):
        self.logger = logger
        self.api_key = ANTHROPIC_API_KEY
        self.client = None
        if HAS_ANTHROPIC and self.api_key:
            self.client = Anthropic()
    
    def evaluate_all_gates(
        self,
        ticker: str,
        sector: Optional[str],
        total_revenue: Optional[float],
        total_debt: Optional[float],
        market_cap_30d_avg: Optional[float],
        segments: Optional[Dict],
        fcf_history: Optional[List[bool]],
        track: Optional[str] = None,
        debt_funded_loss: Optional[bool] = None
    ) -> Dict:
        """
        Run all four halal gates in sequence.
        
        Args:
            ticker: Stock symbol
            sector: GICS sector from company profile
            total_revenue: Most recent year revenue
            total_debt: Total debt from balance sheet
            market_cap_30d_avg: 30-day average market cap
            segments: Revenue segment breakdown from FMP
            fcf_history: List of bools indicating FCF positive (Track B only)
            track: 'A', 'A-Transition', or 'B'
            debt_funded_loss: Boolean indicating if losses are debt-funded (Track B)
        
        Returns:
            Dict with:
            - halal_status: 'pass', 'fail', or 'unverified'
            - gates: List of gate results [gate1_result, gate2_result, gate3_result, gate4_result]
            - first_failure: Which gate failed first (or None)
            - flags: List of warning messages
            - halal_verdict: Plain English summary
        """
        
        results = {
            'ticker': ticker,
            'halal_status': None,  # Final: pass, fail, or unverified
            'gates': {
                'gate1_riba': None,
                'gate2_debt': None,
                'gate3_haram_revenue': None,
                'gate4_loss_financing': None,
            },
            'first_failure': None,
            'flags': [],
            'halal_verdict': None,
        }
        
        # =================================================================
        # GATE 1: RIBA BUSINESS MODEL (Sector-based auto-fail)
        # =================================================================
        gate1_result = self._gate1_riba_business_model(ticker, sector)
        results['gates']['gate1_riba'] = gate1_result
        
        if gate1_result['status'] == 'fail':
            results['halal_status'] = 'fail'
            results['first_failure'] = 'Gate 1: Riba Business Model'
            results['flags'].append(gate1_result['reason'])
            results['halal_verdict'] = f"HALAL FAIL - {gate1_result['reason']}"
            self.logger.warning(f"{ticker} failed Gate 1: {gate1_result['reason']}")
            return results
        elif gate1_result['status'] == 'unverified':
            # Sector data not available - mark flag but continue
            results['flags'].append(gate1_result['reason'])
            self.logger.info(f"{ticker} Gate 1 unverified (will continue)")
        
        # =================================================================
        # GATE 2: DEBT RATIO (< 33% of 30-day avg market cap)
        # =================================================================
        gate2_result = self._gate2_debt_ratio(
            ticker, total_debt, market_cap_30d_avg
        )
        results['gates']['gate2_debt'] = gate2_result
        
        if gate2_result['status'] == 'fail':
            results['halal_status'] = 'fail'
            results['first_failure'] = 'Gate 2: Debt Ratio'
            results['flags'].append(gate2_result['reason'])
            results['halal_verdict'] = f"HALAL FAIL - {gate2_result['reason']}"
            self.logger.warning(f"{ticker} failed Gate 2: {gate2_result['reason']}")
            return results
        elif gate2_result['status'] == 'unverified':
            results['flags'].append(gate2_result['reason'])
        
        # =================================================================
        # GATE 3: HARAM REVENUE (< 5% from prohibited sources)
        # =================================================================
        gate3_result = self._gate3_haram_revenue(
            ticker, total_revenue, segments
        )
        results['gates']['gate3_haram_revenue'] = gate3_result
        
        if gate3_result['status'] == 'fail':
            results['halal_status'] = 'fail'
            results['first_failure'] = 'Gate 3: Haram Revenue'
            results['flags'].append(gate3_result['reason'])
            results['halal_verdict'] = f"HALAL FAIL - {gate3_result['reason']}"
            self.logger.warning(f"{ticker} failed Gate 3: {gate3_result['reason']}")
            return results
        elif gate3_result['status'] == 'unverified':
            results['flags'].append(gate3_result['reason'])
        
        # =================================================================
        # GATE 4: LOSS FINANCING (Track B only - equity-funded losses)
        # =================================================================
        gate4_result = self._gate4_loss_financing(
            ticker, track, fcf_history, debt_funded_loss
        )
        results['gates']['gate4_loss_financing'] = gate4_result
        
        if gate4_result['status'] == 'fail':
            results['halal_status'] = 'fail'
            results['first_failure'] = 'Gate 4: Loss Financing'
            results['flags'].append(gate4_result['reason'])
            results['halal_verdict'] = f"HALAL FAIL - {gate4_result['reason']}"
            self.logger.warning(f"{ticker} failed Gate 4: {gate4_result['reason']}")
            return results
        elif gate4_result['status'] == 'unverified':
            results['flags'].append(gate4_result['reason'])
        
        # =================================================================
        # ALL GATES PASSED - CHECK FOR UNVERIFIED FLAGS
        # =================================================================
        
        # Check for unverified flags
        unverified_count = sum(
            1 for flag in results['flags']
            if 'Halal Unverified' in flag or 'Halal Review' in flag
        )
        
        if unverified_count > 0:
            # Use Claude AI to determine pass/fail for unverified cases
            self.logger.info(f"{ticker} has {unverified_count} unverified flag(s), using Claude AI for review")
            claude_decision = self._claude_halal_review(ticker, results['flags'], results['gates'])
            
            if claude_decision:
                results['halal_status'] = claude_decision['status']
                results['halal_verdict'] = claude_decision['verdict']
                results['claude_review'] = claude_decision['reasoning']
                self.logger.info(f"{ticker} Claude AI review: {claude_decision['status'].upper()}")
            else:
                # Fallback to unverified if Claude fails
                results['halal_status'] = 'unverified'
                results['halal_verdict'] = f"HALAL UNVERIFIED - {unverified_count} flag(s) require manual review"
                self.logger.warning(f"{ticker} passed all gates but has {unverified_count} unverified flag(s)")
        else:
            results['halal_status'] = 'pass'
            results['halal_verdict'] = "HALAL COMPLIANT ✓ All gates passed"
            self.logger.info(f"{ticker} passed all halal gates")
        
        return results
    
    # =====================================================================
    # GATE 1: RIBA BUSINESS MODEL
    # =====================================================================
    
    def _gate1_riba_business_model(self, ticker: str, sector: Optional[str]) -> Dict:
        """
        Gate 1: Auto-fail if sector indicates interest-based business model.
        
        No financial data needed - structural business model determines this.
        Failure is immediate and final.
        
        Args:
            ticker: Stock symbol
            sector: GICS sector from FMP company profile
        
        Returns:
            {'status': 'pass'/'fail'/'unverified', 'reason': str}
        """
        
        if not sector:
            return {
                'status': 'unverified',
                'reason': 'Sector data unavailable. Halal Unverified - investor reviews business model.'
            }
        
        sector_clean = sector.strip()
        
        # Check exact match against auto-fail list
        if sector_clean in RIBA_AUTO_FAIL_SECTORS:
            return {
                'status': 'fail',
                'reason': f'Sector "{sector_clean}" is structurally interest-based (riba). Auto-failed.'
            }
        
        # Check for partial matches
        sector_lower = sector_clean.lower()
        for fail_sector in RIBA_AUTO_FAIL_SECTORS:
            if fail_sector.lower() in sector_lower or sector_lower in fail_sector.lower():
                return {
                    'status': 'fail',
                    'reason': f'Sector "{sector_clean}" is structurally interest-based (riba). Auto-failed.'
                }
        
        # Passed Gate 1
        return {
            'status': 'pass',
            'reason': f'Sector "{sector_clean}" is not a riba-based business model.'
        }
    
    # =====================================================================
    # GATE 2: DEBT RATIO
    # =====================================================================
    
    def _gate2_debt_ratio(
        self,
        ticker: str,
        total_debt: Optional[float],
        market_cap_30d_avg: Optional[float]
    ) -> Dict:
        """
        Gate 2: Total debt / 30-day average market cap must be < 33%.
        Standard AAOIFI screen.
        
        Threshold: Strictly below 33% = pass. At or above 33% = fail.
        
        Args:
            ticker: Stock symbol
            total_debt: Total debt from most recent balance sheet
            market_cap_30d_avg: 30-day average market cap from price history
        
        Returns:
            {'status': 'pass'/'fail'/'unverified', 'reason': str, 'debt_ratio': float}
        """
        
        # Missing data - unverified
        if total_debt is None or market_cap_30d_avg is None:
            return {
                'status': 'unverified',
                'reason': 'Missing debt or market cap data. Halal Unverified - investor reviews.',
                'debt_ratio': None
            }
        
        # Both values are zero or near-zero
        if market_cap_30d_avg <= 0:
            return {
                'status': 'unverified',
                'reason': 'Market cap data invalid (zero or negative). Halal Unverified.',
                'debt_ratio': None
            }
        
        # Calculate debt ratio
        debt_ratio = total_debt / market_cap_30d_avg
        
        # Threshold: strictly below 33% = pass
        if debt_ratio < 0.33:
            return {
                'status': 'pass',
                'reason': f'Debt ratio {debt_ratio:.1%} is below 33% threshold.',
                'debt_ratio': debt_ratio
            }
        else:
            # At or above 33% = fail
            return {
                'status': 'fail',
                'reason': f'Debt ratio {debt_ratio:.1%} is at or above 33% threshold. Exceeds halal limit.',
                'debt_ratio': debt_ratio
            }
    
    # =====================================================================
    # GATE 3: HARAM REVENUE
    # =====================================================================
    
    def _gate3_haram_revenue(
        self,
        ticker: str,
        total_revenue: Optional[float],
        segments: Optional[Dict]
    ) -> Dict:
        """
        Gate 3: Revenue from prohibited activities must be < 5% of total revenue.
        
        Prohibited: alcohol, tobacco, weapons, adult entertainment, pork, conventional finance
        
        Three scenarios:
        1. Data clean and available: Apply 5% screen
        2. Data unavailable: Flag as 'Halal Unverified' (investor decides)
        3. Primary business is clearly haram: Auto-fail
        
        Args:
            ticker: Stock symbol
            total_revenue: Most recent year revenue
            segments: Revenue segment breakdown from FMP (Dict with 'segments' key)
        
        Returns:
            {'status': 'pass'/'fail'/'unverified', 'reason': str, 'haram_revenue_pct': float or None}
        """
        
        # No segment data available
        if not segments or not isinstance(segments, dict):
            return {
                'status': 'unverified',
                'reason': 'Revenue segment data unavailable. Halal Unverified - investor reviews segment revenue.',
                'haram_revenue_pct': None
            }
        
        segment_list = segments.get('segments', [])
        if not segment_list or len(segment_list) == 0:
            return {
                'status': 'unverified',
                'reason': 'No revenue segment breakdown found. Halal Unverified - investor reviews annual report.',
                'haram_revenue_pct': None
            }
        
        # Scan segments for haram categories
        haram_revenue = 0.0
        
        for segment in segment_list:
            segment_name = segment.get('segment', '') or segment.get('name', '')
            segment_revenue = segment.get('revenue', 0) or 0
            
            segment_name_lower = segment_name.lower()
            
            # Check if segment matches any prohibited category
            is_haram = any(
                keyword in segment_name_lower
                for keyword in PROHIBITED_REVENUE_KEYWORDS
            )
            
            if is_haram:
                haram_revenue += segment_revenue
                self.logger.debug(f"{ticker} segment '{segment_name}' identified as prohibited")
        
        # Avoid division by zero
        if not total_revenue or total_revenue <= 0:
            return {
                'status': 'unverified',
                'reason': 'Total revenue data invalid or zero. Halal Unverified.',
                'haram_revenue_pct': None
            }
        
        haram_pct = haram_revenue / total_revenue
        
        # Apply 5% threshold
        if haram_pct < 0.05:
            return {
                'status': 'pass',
                'reason': f'Haram revenue {haram_pct:.2%} is below 5% threshold.',
                'haram_revenue_pct': haram_pct
            }
        else:
            # At or above 5% fails
            return {
                'status': 'fail',
                'reason': f'Haram revenue {haram_pct:.2%} exceeds 5% threshold.',
                'haram_revenue_pct': haram_pct
            }
    
    # =====================================================================
    # GATE 4: LOSS FINANCING (TRACK B ONLY)
    # =====================================================================
    
    def _gate4_loss_financing(
        self,
        ticker: str,
        track: Optional[str],
        fcf_history: Optional[List[bool]],
        debt_funded_loss: Optional[bool]
    ) -> Dict:
        """
        Gate 4: For Track B (investment-phase) companies only.
        Losses must be equity-funded, not debt-funded.
        
        A company burning cash on a revolving credit facility fails this gate
        even if debt ratio is below 33%.
        
        Gate result:
        - Track A or A-Transition: Automatically pass (not applicable)
        - Track B + losses equity-funded: Pass
        - Track B + losses debt-funded: Fail
        - Track B + insufficient data: Unverified
        
        Args:
            ticker: Stock symbol
            track: 'A', 'A-Transition', or 'B'
            fcf_history: List of bools indicating FCF positive each year (not directly used but for context)
            debt_funded_loss: Boolean indicator if losses are being financed by debt
        
        Returns:
            {'status': 'pass'/'fail'/'unverified', 'reason': str}
        """
        
        # Gate 4 only applies to Track B
        if track != 'B':
            return {
                'status': 'pass',
                'reason': f'Gate 4 (Loss Financing) applies to Track B only. Track {track} automatically passes.'
            }
        
        # Track B: Check if losses are equity-funded or debt-funded
        if debt_funded_loss is None:
            return {
                'status': 'unverified',
                'reason': 'Debt structure unclear for Track B investment-phase company. Halal Review Required - investor checks debt facilities.',
                'loss_financing_method': None
            }
        
        if not debt_funded_loss:
            # Equity-funded losses = halal compliant
            return {
                'status': 'pass',
                'reason': 'Track B losses are equity-funded. Compliant with Gate 4.',
                'loss_financing_method': 'equity'
            }
        else:
            # Debt-funded losses = fails gate AND fails halal compliance
            return {
                'status': 'fail',
                'reason': 'Track B losses financed by debt (revolving credit facility). Exceeds halal framework.',
                'loss_financing_method': 'debt'
            }
    
    def _claude_halal_review(self, ticker: str, flags: List[str], gates: Dict) -> Optional[Dict]:
        """
        Use Claude AI to make a pass/fail determination for unverified halal cases.
        
        Args:
            ticker: Stock symbol
            flags: List of warning flags from gate evaluation
            gates: Dict of all gate results
            
        Returns:
            Dict with {'status': 'pass'/'fail', 'verdict': str, 'reasoning': str} or None if Claude unavailable
        """
        
        if not self.client:
            self.logger.warning(f"Claude AI unavailable for {ticker} halal review (API key or library missing). Returning unverified.")
            return None
        
        try:
            # Build context for Claude
            gate_summary = self._summarize_gates(gates)
            flags_text = '\n'.join([f"- {flag}" for flag in flags])
            
            prompt = f"""You are an expert Islamic finance advisor evaluating stock halal compliance.

Stock: {ticker}

GATE EVALUATION SUMMARY:
{gate_summary}

UNVERIFIED FLAGS REQUIRING REVIEW:
{flags_text}

Based on the gate results and these flags, determine if {ticker} should be considered HALAL COMPLIANT or NOT HALAL COMPLIANT.

Consider:
1. The stock has already passed the quantitative gates (debt ratio, revenue checks)
2. Unverified flags are due to missing data, not actual violations
3. Islamic finance principles prioritize transparency but allow reasonable business structures
4. When data is unavailable, a conservative but practical approach is to classify based on available evidence

Respond with EXACTLY this format:
DECISION: PASS
REASONING: Brief explanation in 1-2 sentences

OR

DECISION: FAIL
REASONING: Brief explanation in 1-2 sentences"""

            message = self.client.messages.create(
                model="claude-3-haiku-20250305",  # Fast and cost-effective
                max_tokens=150,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            response_text = message.content[0].text.strip()
            
            # Parse response with simple string matching
            if "DECISION: PASS" in response_text:
                decision = "pass"
            elif "DECISION: FAIL" in response_text:
                decision = "fail"
            else:
                self.logger.warning(f"Claude didn't reach a clear decision for {ticker}: {response_text}")
                return None
            
            # Extract reasoning
            lines = response_text.split('\n')
            reasoning = ""
            for i, line in enumerate(lines):
                if "REASONING:" in line:
                    reasoning = line.replace("REASONING:", "").strip()
                    # If reasoning spans multiple lines, capture them
                    if not reasoning and i + 1 < len(lines):
                        reasoning = lines[i + 1].strip()
                    break
            
            # Build verdict
            verdict = f"HALAL {'COMPLIANT' if decision == 'pass' else 'NON-COMPLIANT'} (Claude AI Review) - {reasoning}"
            
            return {
                'status': decision,
                'verdict': verdict,
                'reasoning': reasoning
            }
                
        except Exception as e:
            self.logger.error(f"Claude AI review failed for {ticker}: {str(e)}")
            return None
    
    def _summarize_gates(self, gates: Dict) -> str:
        """Summarize the gate evaluation results for Claude."""
        
        summary = []
        for gate_name, gate_result in gates.items():
            if gate_result:
                status = gate_result.get('status', 'unknown')
                reason = gate_result.get('reason', '')
                summary.append(f"{gate_name}: {status.upper()} - {reason}")
        
        return '\n'.join(summary) if summary else "No gates evaluated"


# HELPER FUNCTION: Extract halal-relevant data from fetcher output
# ==========================================================================

def prepare_halal_evaluation_data(
    financial_data: Dict,
    price_data: Dict,
    profile_data: Optional[Dict] = None
) -> Dict:
    """
    Extract and organize data from fetcher.py output into format needed by halal gates.
    
    Args:
        financial_data: From fetcher.get_all_financial_data()
        price_data: From fetcher.get_all_price_data()
        profile_data: From fetcher.fetch_company_profile()
    
    Returns:
        Dict with formatted data ready for halal gate evaluation
    """
    
    # Extract most recent year financial data
    total_revenue = None
    total_debt = None
    
    if financial_data.get('income'):
        income_years = financial_data['income'].get('years', [])
        if income_years:
            total_revenue = income_years[0].get('totalRevenue')
    
    if financial_data.get('balance'):
        balance_years = financial_data['balance'].get('years', [])
        if balance_years:
            total_debt = balance_years[0].get('totalDebt')
    
    # Extract market cap 30-day average
    market_cap_30d_avg = None
    if price_data.get('history_30d'):
        # Try to get the 30-day avg market cap, fall back to current market cap
        market_cap_30d_avg = price_data['history_30d'].get('marketCap30dAvg') or price_data['history_30d'].get('marketCap')
    
    # Also check quote for market cap if price history doesn't have it
    if not market_cap_30d_avg and price_data.get('quote'):
        market_cap_30d_avg = price_data['quote'].get('marketCap')
    
    # Extract sector - PRIORITY: quote > profile > financial_data.profile
    # (quote comes from yfinance which is most reliable)
    sector = None
    if price_data.get('quote'):
        sector = price_data['quote'].get('sector')
    
    if not sector:
        if profile_data:
            sector = profile_data.get('sector')
        elif financial_data.get('profile'):
            sector = financial_data['profile'].get('sector')
    
    # Extract segments
    segments = financial_data.get('segments')
    
    return {
        'total_revenue': total_revenue,
        'total_debt': total_debt,
        'market_cap_30d_avg': market_cap_30d_avg,
        'sector': sector,
        'segments': segments,
    }


if __name__ == "__main__":
    # Quick test
    engine = HalalGateEngine()
    
    # Test Gate 1: Should fail (Banks sector)
    result1 = engine.evaluate_all_gates(
        ticker='JPM',
        sector='Banks',
        total_revenue=100e9,
        total_debt=200e9,
        market_cap_30d_avg=400e9,
        segments=None,
        fcf_history=None,
        track='A'
    )
    print("Gate 1 Test (JPM - Banks):", result1['halal_status'], result1['halal_verdict'])
    
    # Test Gate 2: Should pass (debt < 33%)
    result2 = engine.evaluate_all_gates(
        ticker='MSFT',
        sector='Technology',
        total_revenue=200e9,
        total_debt=50e9,
        market_cap_30d_avg=2500e9,
        segments=None,
        fcf_history=None,
        track='A'
    )
    print("Gate 2 Test (MSFT - Tech):", result2['halal_status'], result2['halal_verdict'])
    
    # Test Gate 2: Should fail (debt >= 33%)
    result3 = engine.evaluate_all_gates(
        ticker='TEST',
        sector='Technology',
        total_revenue=100e9,
        total_debt=400e9,
        market_cap_30d_avg=1000e9,
        segments=None,
        fcf_history=None,
        track='A'
    )
    print("Gate 2 Fail Test (HIGH DEBT):", result3['halal_status'], result3['halal_verdict'])
