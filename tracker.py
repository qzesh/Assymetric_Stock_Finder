"""
Track Router - Auto-detect evaluation track based on FCF history

Three routes exist:
- Track A: FCF positive in 4 or more of the last 5 years. Business generates real cash.
- Track A-Transition: FCF positive in years 1-4 but negative in most recent year. 
  Was a compounder, recently disrupted. Apply Track A signals but append transition 
  investigation to AI prompt.
- Track B: FCF negative in 3 or more of the last 5 years. Deliberately reinvesting 
  ahead of profitability.

The system auto-detects and routes - the investor never specifies manually.
"""

import logging
from typing import Dict, Optional, List, Tuple

logger = logging.getLogger(__name__)


class TrackRouter:
    """
    Routes a stock to the correct evaluation track (A, A-Transition, or B)
    based on 5-year FCF history.
    """
    
    def __init__(self):
        self.logger = logger
    
    def detect_track(
        self,
        ticker: str,
        fcf_history: List[Optional[float]],
        years: Optional[List[int]] = None
    ) -> Dict:
        """
        Auto-detect track based on FCF history.
        
        Args:
            ticker: Stock symbol
            fcf_history: List of FCF values, most recent first (e.g. [2024, 2023, 2022, 2021, 2020])
                        Values can be floats or None (missing data)
            years: Optional list of years corresponding to fcf_history
                  (e.g. [2024, 2023, 2022, 2021, 2020])
        
        Returns:
            Dict with:
            - track: 'A', 'A-Transition', or 'B'
            - conviction: 'high'/'medium'/'low' (based on data quality)
            - fcf_positive_count: How many of last 5 years had positive FCF
            - fcf_negative_count: How many of last 5 years had negative FCF
            - fcf_history_clean: Cleaned history (at least 3 years required)
            - reasoning: Plain English explanation
            - warning: Any data quality warnings
        """
        
        result = {
            'ticker': ticker,
            'track': None,
            'conviction': None,
            'fcf_positive_count': 0,
            'fcf_negative_count': 0,
            'fcf_data_quality': None,
            'fcf_history_clean': [],
            'recent_fcf_trend': None,
            'reasoning': None,
            'warning': None,
            'ai_prompt_append': None,  # For A-Transition track
        }
        
        # =================================================================
        # DATA QUALITY CHECK: Need at least 3 years of FCF data
        # =================================================================
        
        if not fcf_history or len(fcf_history) == 0:
            result['track'] = None
            result['conviction'] = 'low'
            result['warning'] = 'No FCF data available. Track cannot be determined.'
            self.logger.error(f"{ticker}: No FCF history provided")
            return result
        
        # Take last 5 years (or fewer if less available)
        fcf_window = fcf_history[:5]  # Most recent 5 (or fewer)
        
        # Filter out None values while tracking position
        clean_fcf = []
        valid_indices = []
        
        for i, fcf in enumerate(fcf_window):
            if fcf is not None:
                clean_fcf.append(fcf)
                valid_indices.append(i)
        
        result['fcf_history_clean'] = clean_fcf
        
        # Need at least 3 years of data
        if len(clean_fcf) < 3:
            result['track'] = None
            result['conviction'] = 'low'
            result['warning'] = f'Insufficient FCF history: only {len(clean_fcf)} years available. Need at least 3.'
            self.logger.warning(f"{ticker}: Insufficient FCF data ({len(clean_fcf)} years)")
            return result
        
        # =================================================================
        # CLASSIFY FCF YEARS AS POSITIVE OR NEGATIVE
        # =================================================================
        
        fcf_signs = []
        for fcf in clean_fcf:
            if fcf > 0:
                fcf_signs.append(True)  # Positive
                result['fcf_positive_count'] += 1
            else:
                fcf_signs.append(False)  # Negative or zero
                result['fcf_negative_count'] += 1
        
        # Data quality based on how many years we have
        num_years = len(clean_fcf)
        if num_years == 5:
            result['fcf_data_quality'] = 'excellent'
        elif num_years == 4:
            result['fcf_data_quality'] = 'good'
        elif num_years == 3:
            result['fcf_data_quality'] = 'minimal'
        
        # Check recent trend (most recent 2 years if available)
        if len(fcf_signs) >= 2:
            if fcf_signs[0] and fcf_signs[1]:
                result['recent_fcf_trend'] = 'strengthening'
            elif not fcf_signs[0] and not fcf_signs[1]:
                result['recent_fcf_trend'] = 'weakening'
            else:
                result['recent_fcf_trend'] = 'volatile'
        
        # =================================================================
        # TRACK A-TRANSITION: Was A, now negative in most recent year
        # CHECK THIS BEFORE TRACK A (most recent is negative, was positive before)
        # =================================================================
        
        if len(fcf_signs) >= 2:
            # Condition: Most recent year is negative, but had 4+ positive before
            # This means it WAS a Track A (4+/5 positive) but just turned negative
            if not fcf_signs[0] and result['fcf_positive_count'] >= 4:
                # Most recent is negative, but had 4+ positive (meaning 4 before this recent negative)
                result['track'] = 'A-Transition'
                result['conviction'] = 'medium'
                result['reasoning'] = (
                    f'Track A-Transition: Was a consistent FCF generator '
                    f'({result["fcf_positive_count"]}/5 positive across full period) '
                    f'but turned FCF negative in most recent year. '
                    f'Requires investigation into cause: capex cycle, acquisition integration, or deterioration.'
                )
                result['ai_prompt_append'] = (
                    'This company was a consistent FCF generator but turned FCF negative in its most recent '
                    'fiscal year. Before completing your analysis, search for the cause - acquisition integration, '
                    'one-time capex cycle, or genuine deterioration. State the cause explicitly and factor it into '
                    'your conviction and thesis_invalidators.'
                )
                self.logger.info(f"{ticker} routed to Track A-Transition (was positive, now negative)")
                return result
        
        # =================================================================
        # TRACK A: FCF positive in 4+ of last 5 years (and recent is not negative)
        # =================================================================
        
        if result['fcf_positive_count'] >= 4:
            result['track'] = 'A'
            result['conviction'] = 'high'
            result['reasoning'] = (
                f'Track A (Profitable Compounder): '
                f'FCF positive in {result["fcf_positive_count"]}/5 years. '
                f'Business generates real cash consistently.'
            )
            self.logger.info(f"{ticker} routed to Track A ({result['fcf_positive_count']}/5 FCF positive)")
            return result
        
        # =================================================================
        # TRACK B: FCF negative in 3+ of last 5 years
        # =================================================================
        
        if result['fcf_negative_count'] >= 3:
            result['track'] = 'B'
            result['conviction'] = 'high'
            result['reasoning'] = (
                f'Track B (Investment-Phase Compounder): '
                f'FCF negative in {result["fcf_negative_count"]}/5 years. '
                f'Deliberately reinvesting ahead of profitability.'
            )
            self.logger.info(f"{ticker} routed to Track B ({result['fcf_negative_count']}/5 FCF negative)")
            return result
        
        # =================================================================
        # AMBIGUOUS CASE: Don't fit cleanly into any track
        # (E.g., 2 positive, 3 negative = on the boundary)
        # =================================================================
        
        result['track'] = None
        result['conviction'] = 'low'
        result['warning'] = (
            f'Track ambiguous: {result["fcf_positive_count"]} positive, '
            f'{result["fcf_negative_count"]} negative years. '
            f'Does not meet threshold for Track A (4+) or Track B (3+). '
            f'Possibly transitioning or structurally declining.'
        )
        self.logger.warning(f"{ticker}: Track detection inconclusive")
        return result
    
    def detect_track_from_cashflow_data(
        self,
        ticker: str,
        cashflow_data: Dict,
        years_to_check: int = 5
    ) -> Dict:
        """
        Convenience method: Extract FCF from fetcher.py cashflow data and auto-detect track.
        
        Args:
            ticker: Stock symbol
            cashflow_data: Dict from fetcher.fetch_cashflow() with structure:
                {
                    'ticker': 'MSFT',
                    'years': [
                        {'year': 2024, 'freeCashflow': 123e9, ...},
                        {'year': 2023, 'freeCashflow': 120e9, ...},
                        ...
                    ]
                }
            years_to_check: Number of years to analyze (default 5)
        
        Returns:
            Same as detect_track()
        """
        
        if not cashflow_data or 'years' not in cashflow_data:
            return self.detect_track(ticker, [])
        
        years_list = cashflow_data['years']
        
        # Sort by year descending (most recent first)
        years_sorted = sorted(years_list, key=lambda x: x.get('year', 0), reverse=True)
        
        # Extract FCF values
        fcf_values = [
            year_data.get('freeCashflow')
            for year_data in years_sorted[:years_to_check]
        ]
        
        # Extract year numbers for reference
        year_numbers = [
            year_data.get('year')
            for year_data in years_sorted[:years_to_check]
        ]
        
        return self.detect_track(ticker, fcf_values, year_numbers)


# ==========================================================================
# HELPER FUNCTIONS
# ==========================================================================

def format_track_result(track_result: Dict) -> str:
    """Format track detection result for display."""
    
    track = track_result.get('track')
    conviction = track_result.get('conviction', 'unknown')
    reasoning = track_result.get('reasoning', 'Unknown')
    
    if not track:
        return f"⚠️  Track Detection Failed: {track_result.get('warning', 'Unknown reason')}"
    
    icon_map = {'A': '📊', 'A-Transition': '🔄', 'B': '📈'}
    icon = icon_map.get(track, '❓')
    
    return f"{icon} Track {track} ({conviction.upper()}) - {reasoning}"


if __name__ == "__main__":
    # Test cases
    router = TrackRouter()
    
    # Test 1: Track A (4 positive, 1 negative)
    result1 = router.detect_track(
        'MSFT',
        [100, 90, 85, 80, 75]  # All positive - 5/5 positive
    )
    print(result1['track'], "Expected: A", "✓" if result1['track'] == 'A' else "✗")
    
    # Test 2: Track A-Transition (negative recently, was positive)
    result2 = router.detect_track(
        'TEST_TRANS',
        [-10, 100, 90, 80, 70]  # Recent negative, 4 positive before
    )
    print(result2['track'], "Expected: A-Transition", "✓" if result2['track'] == 'A-Transition' else "✗")
    
    # Test 3: Track B (3+ negative)
    result3 = router.detect_track(
        'STARTUP',
        [-50, -40, -30, 100, 90]  # 3 negative, 2 positive
    )
    print(result3['track'], "Expected: B", "✓" if result3['track'] == 'B' else "✗")
    
    # Test 4: Insufficient data
    result4 = router.detect_track(
        'NEW_IPO',
        [100, 90]  # Only 2 years
    )
    print(result4['track'], "Expected: None", "✓" if result4['track'] is None else "✗")
    
    # Test 5: Ambiguous case
    result5 = router.detect_track(
        'AMBIG',
        [50, 40, -30, -40, -50]  # 2 positive, 3 negative - on boundary
    )
    print(result5['track'], "Expected: B", "✓" if result5['track'] == 'B' else "✗")
    
    print("\nFormatted output:")
    print(format_track_result(result1))
    print(format_track_result(result2))
    print(format_track_result(result3))
