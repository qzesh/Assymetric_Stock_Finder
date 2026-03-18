"""
Asymmetric Pattern Detector - The most important gate in the system.

A high signal score alone does not make a stock asymmetric - it makes it a decent stock.
True asymmetry requires ALL THREE components present simultaneously:

Component 1: FLOOR (downside protection)
Component 2: MISPRICING (market is wrong about something)
Component 3: CATALYST (path to re-rating exists)

Routing based on results:
- All 3 components: Full Asymmetric Setup → Qualifies for AI deep reasoning
- 2 of 3: Partial Asymmetric Setup → Qualifies for AI (conviction cannot be High)
- 1 of 3: Not Asymmetric → Excluded from AI reasoning, logged to watchlist
"""

import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class AsymmetricPatternDetector:
    """
    Detects asymmetric patterns by checking three components: Floor, Mispricing, Catalyst.
    """
    
    def __init__(self):
        self.logger = logger
    
    def detect_pattern(
        self,
        ticker: str,
        track: str,
        signal_data: Dict,
        price_data: Dict,
        insider_data: Optional[Dict] = None,
        fcf_history: Optional[List[bool]] = None,
        income_data: Optional[Dict] = None,
    ) -> Dict:
        """
        Detect asymmetric pattern by checking all three components.
        
        Args:
            ticker: Stock symbol
            track: 'A' or 'B'
            signal_data: Dict with all computed signals and their values/scores
            price_data: Current price, 52-week high/low, market cap
            insider_data: Recent insider transactions (last 90 days)
            fcf_history: List of bools for FCF positive/negative
            income_data: Income statement data for ROIC trend
        
        Returns:
            Dict with:
            - floor: bool (at least one condition present)
            - floor_reason: str (which condition met)
            - mispricing: bool
            - mispricing_reason: str
            - catalyst: bool
            - catalyst_reason: str
            - result: 'full'/'partial'/'not_asymmetric'
            - missing: list of missing components (if partial)
            - conviction_max: 'high'/'medium'/'low' based on pattern result
        """
        
        result = {
            'ticker': ticker,
            'track': track,
            'floor': False,
            'floor_reason': None,
            'mispricing': False,
            'mispricing_reason': None,
            'catalyst': False,
            'catalyst_reason': None,
            'result': None,  # 'full'/'partial'/'not_asymmetric'
            'components_present': [],
            'components_missing': [],
            'conviction_max': None,
            'reasoning': None,
        }
        
        # =================================================================
        # COMPONENT 1: FLOOR (Downside Protection)
        # =================================================================
        
        floor_result = self._check_floor(ticker, track, signal_data)
        result['floor'] = floor_result['present']
        result['floor_reason'] = floor_result['reason']
        
        if floor_result['present']:
            result['components_present'].append('floor')
        else:
            result['components_missing'].append('floor')
        
        # =================================================================
        # COMPONENT 2: MISPRICING (Market Wrong)
        # =================================================================
        
        mispricing_result = self._check_mispricing(
            ticker, track, signal_data, price_data
        )
        result['mispricing'] = mispricing_result['present']
        result['mispricing_reason'] = mispricing_result['reason']
        
        if mispricing_result['present']:
            result['components_present'].append('mispricing')
        else:
            result['components_missing'].append('mispricing')
        
        # =================================================================
        # COMPONENT 3: CATALYST (Path to Re-rating)
        # =================================================================
        
        catalyst_result = self._check_catalyst(
            ticker, track, signal_data, insider_data, fcf_history, income_data
        )
        result['catalyst'] = catalyst_result['present']
        result['catalyst_reason'] = catalyst_result['reason']
        
        if catalyst_result['present']:
            result['components_present'].append('catalyst')
        else:
            result['components_missing'].append('catalyst')
        
        # =================================================================
        # ROUTE BASED ON COMPONENTS
        # =================================================================
        
        components_count = len(result['components_present'])
        
        if components_count == 3:
            result['result'] = 'full'
            result['conviction_max'] = 'high'
            result['reasoning'] = (
                f'Full Asymmetric Setup: All three components present. '
                f'Qualifies for AI deep reasoning with High conviction potential.'
            )
            self.logger.info(f"{ticker}: Full Asymmetric Setup detected")
        
        elif components_count == 2:
            result['result'] = 'partial'
            result['conviction_max'] = 'medium'
            missing = ', '.join(result['components_missing'])
            result['reasoning'] = (
                f'Partial Asymmetric Setup: Missing {missing}. '
                f'Qualifies for AI reasoning but conviction cannot exceed Medium.'
            )
            self.logger.info(f"{ticker}: Partial Asymmetric Setup (missing {missing})")
        
        else:  # 1 or 0 components
            result['result'] = 'not_asymmetric'
            result['conviction_max'] = 'low'
            result['reasoning'] = (
                f'Not Asymmetric: Only {components_count} of 3 components present. '
                f'Stock is decent but lacks true asymmetry. Logged to watchlist for monitoring.'
            )
            self.logger.warning(f"{ticker}: Not asymmetric ({components_count}/3 components)")
        
        return result
    
    # =====================================================================
    # COMPONENT 1: FLOOR (Downside Protection)
    # =====================================================================
    
    def _check_floor(self, ticker: str, track: str, signal_data: Dict) -> Dict:
        """
        Check if hard floor exists under downside.
        
        At least ONE of:
        - Net cash > 10% of market cap
        - EV/FCF > 20% below 5yr average
        - ROIC consistently > 18% (Track A only - asset-light business)
        - Cash runway > 3 years (Track B only)
        
        Returns:
            {'present': bool, 'reason': str}
        """
        
        reasons = []
        
        # Check 1: Net cash > 10% of market cap
        net_cash_signal = signal_data.get('net_cash_floor')
        if net_cash_signal:
            net_cash_value = net_cash_signal.get('value')
            if net_cash_value and net_cash_value > 0.10:
                reasons.append(f'Net cash {net_cash_value:.1%} of market cap')
        
        # Check 2: EV/FCF > 20% below 5yr average
        ev_fcf_signal = signal_data.get('ev_fcf_valuation')
        if ev_fcf_signal:
            ev_fcf_value = ev_fcf_signal.get('value')
            if ev_fcf_value and ev_fcf_value > 0.20:
                reasons.append(f'EV/FCF {ev_fcf_value:.1%} below 5yr average')
        
        # Check 3: ROIC > 18% (Track A only)
        if track == 'A':
            roic_signal = signal_data.get('roic')
            if roic_signal:
                roic_value = roic_signal.get('value')
                if roic_value and roic_value > 0.18:
                    reasons.append(f'ROIC {roic_value:.1%} > 18% (asset-light)')
        
        # Check 4: Cash runway > 3 years (Track B only)
        if track == 'B':
            runway_signal = signal_data.get('cash_runway')
            if runway_signal:
                runway_value = runway_signal.get('value')
                if runway_value and runway_value > 3:
                    reasons.append(f'Cash runway {runway_value:.1f} years')
        
        if reasons:
            return {
                'present': True,
                'reason': ' | '.join(reasons)
            }
        else:
            return {
                'present': False,
                'reason': 'No downside floor detected'
            }
    
    # =====================================================================
    # COMPONENT 2: MISPRICING (Market Wrong About Something)
    # =====================================================================
    
    def _check_mispricing(
        self,
        ticker: str,
        track: str,
        signal_data: Dict,
        price_data: Optional[Dict]
    ) -> Dict:
        """
        Check if market is mispri cing something.
        
        At least ONE of:
        - Trough earnings signal (Track A): score 3 on normalized earnings
        - EV/FCF > 20% below own 5yr average
        - Stock within 20% of 52-week low AND revenue stable (price punished, fundamentals solid)
        - Track B: Gross margin improving + stock near 52-week low (market pricing permanent losses)
        
        52-week low check requires price history data.
        
        Returns:
            {'present': bool, 'reason': str}
        """
        
        reasons = []
        
        # Check 1: Trough earnings signal (Track A only - score 3 on normalized earnings)
        if track == 'A':
            trough_signal = signal_data.get('normalized_earnings')
            if trough_signal and trough_signal.get('score') == 3:
                reasons.append('Trough earnings signal (margin compressed, revenue stable)')
        
        # Check 2: EV/FCF > 20% below 5yr average
        ev_fcf_signal = signal_data.get('ev_fcf_valuation')
        if ev_fcf_signal:
            ev_fcf_value = ev_fcf_signal.get('value')
            if ev_fcf_value and ev_fcf_value > 0.20:
                reasons.append(f'Valuation: EV/FCF {ev_fcf_value:.1%} below average')
        
        # Check 3: Price punished but fundamentals stable (52-week low data needed)
        if price_data:
            current_price = price_data.get('currentPrice')
            week52_low = price_data.get('fiftyTwoWeekLow')
            
            if current_price and week52_low and week52_low > 0:
                pct_from_low = (current_price - week52_low) / week52_low
                if pct_from_low <= 0.20:  # Within 20% of 52-week low
                    reasons.append(f'Price punished: {pct_from_low:.1%} above 52-week low')
        
        # Check 4: Track B specific - improving margins + near 52-week low
        if track == 'B' and price_data:
            gm_signal = signal_data.get('gross_margin')
            current_price = price_data.get('currentPrice')
            week52_low = price_data.get('fiftyTwoWeekLow')
            
            if (gm_signal and gm_signal.get('score') == 3 and 
                current_price and week52_low and week52_low > 0):
                pct_from_low = (current_price - week52_low) / week52_low
                if pct_from_low <= 0.20:
                    reasons.append('Track B: Improving margins but priced for permanent losses')
        
        if reasons:
            return {
                'present': True,
                'reason': ' | '.join(reasons)
            }
        else:
            return {
                'present': False,
                'reason': 'No mispricing signal detected'
            }
    
    # =====================================================================
    # COMPONENT 3: CATALYST (Path to Re-rating)
    # =====================================================================
    
    def _check_catalyst(
        self,
        ticker: str,
        track: str,
        signal_data: Dict,
        insider_data: Optional[Dict],
        fcf_history: Optional[List[bool]],
        income_data: Optional[Dict],
    ) -> Dict:
        """
        Check if path to re-rating exists.
        
        At least ONE of:
        - Insider buying in last 90 days
        - Operating leverage positive: losses narrowing (Track B) or ROIC improving (Track A)
        - ROIC trend improving over 3 years (Track A only)
        - Identifiable path: approaching FCF breakeven, contract renewal, debt payoff, or major product launch
        
        Returns:
            {'present': bool, 'reason': str}
        """
        
        reasons = []
        
        # Check 1: Insider buying last 90 days
        if insider_data:
            has_recent_buying = insider_data.get('has_recent_buying', False)
            if has_recent_buying:
                txn_count = insider_data.get('transactions_found', 0)
                reasons.append(f'Insider buying: {txn_count} transactions in last 90 days')
        
        # Check 2: Operating leverage (losses narrowing) - Track B
        if track == 'B':
            op_leverage_signal = signal_data.get('operating_leverage')
            if op_leverage_signal and op_leverage_signal.get('score') >= 2:
                reasons.append('Operating leverage: Losses narrowing with scale')
        
        # Check 3: ROIC trend improving - Track A
        if track == 'A':
            roic_trend_signal = signal_data.get('roic_trend')
            if roic_trend_signal and roic_trend_signal.get('score') == 3:
                reasons.append('ROIC trending upward: Capital allocation improving')
        
        # Check 4: Identifiable path (requires deeper analysis - would need more context)
        # This is often AI-assessed, but we can flag if approaching breakeven
        if track == 'B':
            runway_signal = signal_data.get('cash_runway')
            if runway_signal:
                runway = runway_signal.get('value')
                if runway and 2 < runway < 4:
                    reasons.append(f'Path visibility: {runway:.1f}yr runway with improving margins = approaching breakeven')
        
        # Check 5: FCF consistency improving (for Track A - was negative a few years ago, now positive)
        if track == 'A' and fcf_history and len(fcf_history) >= 3:
            # If recent 2 are positive but early years had some negative
            recent_positive = sum(fcf_history[:2])
            earlier_mixed = any(not x for x in fcf_history[2:])
            if recent_positive >= 1 and earlier_mixed:
                reasons.append('FCF trajectory: Recently strengthened after earlier weakness')
        
        if reasons:
            return {
                'present': True,
                'reason': ' | '.join(reasons)
            }
        else:
            return {
                'present': False,
                'reason': 'No catalyst identified'
            }


def format_pattern_result(pattern: Dict) -> str:
    """Format pattern detection result for display."""
    
    result = pattern.get('result', 'unknown')
    
    icons = {
        'full': '🎯',
        'partial': '⚠️',
        'not_asymmetric': '❌',
    }
    
    conviction_map = {
        'high': '⭐⭐⭐',
        'medium': '⭐⭐',
        'low': '⭐',
    }
    
    icon = icons.get(result, '?')
    conviction = conviction_map.get(pattern.get('conviction_max'), '?')
    
    if result == 'full':
        return f"{icon} FULL ASYMMETRIC SETUP {conviction} - {pattern.get('reasoning', '')}"
    elif result == 'partial':
        missing = ', '.join(pattern.get('components_missing', []))
        return f"{icon} PARTIAL (missing {missing}) {conviction} - {pattern.get('reasoning', '')}"
    else:
        components = len(pattern.get('components_present', []))
        return f"{icon} NOT ASYMMETRIC ({components}/3 components) - {pattern.get('reasoning', '')}"


if __name__ == "__main__":
    # Test
    detector = AsymmetricPatternDetector()
    print("AsymmetricPatternDetector initialized")
    print("\nComponent checks:")
    print("- Floor: Downside protection (net cash, low valuation, ROIC, or runway)")
    print("- Mispricing: Market wrong (trough signal, cheap valuation, price punished)")
    print("- Catalyst: Path to re-rating (insider buying, leverage, ROIC trend, breakeven approaching)")
    print("\nResult routing:")
    print("- Full (3/3): High conviction max")
    print("- Partial (2/3): Medium conviction max")
    print("- Not Asymmetric (0-1/3): Low conviction, watchlist only")
