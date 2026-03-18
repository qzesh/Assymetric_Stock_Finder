"""
Signal Scoring Engine - Compute and score all signals for both tracks.

Track A signals (8): ROIC, ROIC trend, FCF consistency, reinvestment rate, 
                     trough earnings, EV/FCF cheapness, insider ownership, net cash floor
Track B signals (8): Gross margin level, revenue growth, R&D+capex, operating leverage,
                     gross profit growth, cash runway, insider ownership, debt structure

Every signal is scored 1-3:
- Score 3: Strong asymmetric signal
- Score 2: Neutral
- Score 1: Weak or negative

Minimum thresholds to pass signal-scoring gate:
- Track A: 16 out of 24 max score
- Track B: 14 out of 24 max score
"""

import logging
import statistics
from typing import Dict, Optional, List, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class SignalScorer:
    """
    Computes and scores all signals for Track A and Track B.
    
    Input: Financial data from fetcher.py + track assignment
    Output: JSON with all signal values + scores + total score
    """
    
    def __init__(self):
        self.logger = logger
    
    def score_track_a(
        self,
        ticker: str,
        income_data: Optional[Dict],
        balance_data: Optional[Dict],
        cashflow_data: Optional[Dict],
        quote_data: Optional[Dict],
        insider_data: Optional[Dict],
        price_history: Optional[Dict],
    ) -> Dict:
        """
        Score Track A (Profitable Compounder) signals.
        
        Args:
            ticker: Stock symbol
            income_data: Income statement from fetcher (list of years)
            balance_data: Balance sheet from fetcher
            cashflow_data: Cashflow statement from fetcher
            quote_data: Current quote info
            insider_data: Recent insider transactions
            price_history: Price data for valuation calculations
        
        Returns:
            Dict with signals, scores, and summary
        """
        
        result = {
            'ticker': ticker,
            'track': 'A',
            'signals': {},
            'total_score': 0,
            'max_score': 24,
            'pass_threshold': 16,
            'passes': False,
            'data_quality_issues': [],
            'warnings': [],
        }
        
        # Extract data from structures
        income_years = income_data.get('years', []) if income_data else []
        balance_years = balance_data.get('years', []) if balance_data else []
        cashflow_years = cashflow_data.get('years', []) if cashflow_data else []
        
        # =================================================================
        # SIGNAL 1: ROIC (Return on Invested Capital)
        # =================================================================
        
        roic_score = self._score_roic(ticker, income_years, balance_years)
        result['signals']['roic'] = roic_score
        
        # =================================================================
        # SIGNAL 2: ROIC TREND (5-year trajectory)
        # =================================================================
        
        roic_trend_score = self._score_roic_trend(ticker, income_years, balance_years)
        result['signals']['roic_trend'] = roic_trend_score
        
        # =================================================================
        # SIGNAL 3: FCF CONSISTENCY (positive in how many of last 5 years)
        # =================================================================
        
        fcf_consistency_score = self._score_fcf_consistency(ticker, cashflow_years)
        result['signals']['fcf_consistency'] = fcf_consistency_score
        
        # =================================================================
        # SIGNAL 4: REINVESTMENT RATE (% of earnings reinvested)
        # =================================================================
        
        reinvestment_score = self._score_reinvestment_rate(ticker, income_years, cashflow_years)
        result['signals']['reinvestment_rate'] = reinvestment_score
        
        # =================================================================
        # SIGNAL 5: NORMALIZED VS REPORTED EARNINGS (trough detection)
        # =================================================================
        
        trough_score = self._score_trough_earnings(ticker, income_years)
        result['signals']['normalized_earnings'] = trough_score
        
        # =================================================================
        # SIGNAL 6: EV/FCF VS OWN 5-YEAR AVERAGE (valuation cheapness)
        # =================================================================
        
        ev_fcf_score = self._score_ev_fcf_valuation(
            ticker, cashflow_years, quote_data, price_history
        )
        result['signals']['ev_fcf_valuation'] = ev_fcf_score
        
        # =================================================================
        # SIGNAL 7: INSIDER OWNERSHIP %
        # =================================================================
        
        insider_ownership_score = self._score_insider_ownership(ticker, insider_data)
        result['signals']['insider_ownership'] = insider_ownership_score
        
        # =================================================================
        # SIGNAL 8: NET CASH AS % OF MARKET CAP (downside floor)
        # =================================================================
        
        net_cash_score = self._score_net_cash_floor(
            ticker, balance_years, quote_data
        )
        result['signals']['net_cash_floor'] = net_cash_score
        
        # =================================================================
        # AGGREGATE SCORE
        # =================================================================
        
        total = sum(s['score'] for s in result['signals'].values() if s)
        result['total_score'] = total
        result['passes'] = total >= result['pass_threshold']
        
        if result['passes']:
            self.logger.info(f"{ticker} Track A: {total}/{result['max_score']} - PASSES")
        else:
            self.logger.warning(f"{ticker} Track A: {total}/{result['max_score']} - FAILS")
        
        return result
    
    def score_track_b(
        self,
        ticker: str,
        income_data: Optional[Dict],
        balance_data: Optional[Dict],
        cashflow_data: Optional[Dict],
        quote_data: Optional[Dict],
        insider_data: Optional[Dict],
    ) -> Dict:
        """
        Score Track B (Investment-Phase Compounder) signals.
        
        Similar interface to score_track_a but different signals.
        """
        
        result = {
            'ticker': ticker,
            'track': 'B',
            'signals': {},
            'total_score': 0,
            'max_score': 24,
            'pass_threshold': 14,
            'passes': False,
            'data_quality_issues': [],
            'warnings': [],
        }
        
        income_years = income_data.get('years', []) if income_data else []
        balance_years = balance_data.get('years', []) if balance_data else []
        cashflow_years = cashflow_data.get('years', []) if cashflow_data else []
        
        # =================================================================
        # SIGNAL 1: GROSS MARGIN LEVEL & TREND
        # =================================================================
        
        gross_margin_score = self._score_gross_margin(ticker, income_years)
        result['signals']['gross_margin'] = gross_margin_score
        
        # =================================================================
        # SIGNAL 2: REVENUE GROWTH (3-year CAGR)
        # =================================================================
        
        revenue_growth_score = self._score_revenue_growth(ticker, income_years)
        result['signals']['revenue_growth'] = revenue_growth_score
        
        # =================================================================
        # SIGNAL 3: R&D + CAPEX AS % OF LOSS
        # =================================================================
        
        rd_capex_score = self._score_rd_capex_loss(ticker, income_years, cashflow_years)
        result['signals']['rd_capex_loss'] = rd_capex_score
        
        # =================================================================
        # SIGNAL 4: OPERATING LEVERAGE TREND (losses narrowing with scale)
        # =================================================================
        
        op_leverage_score = self._score_operating_leverage(ticker, income_years)
        result['signals']['operating_leverage'] = op_leverage_score
        
        # =================================================================
        # SIGNAL 5: GROSS PROFIT VS REVENUE GROWTH
        # =================================================================
        
        gp_growth_score = self._score_gross_profit_growth(ticker, income_years)
        result['signals']['gross_profit_growth'] = gp_growth_score
        
        # =================================================================
        # SIGNAL 6: CASH RUNWAY (years at current burn)
        # =================================================================
        
        runway_score = self._score_cash_runway(
            ticker, cashflow_years, quote_data
        )
        result['signals']['cash_runway'] = runway_score
        
        # =================================================================
        # SIGNAL 7: INSIDER OWNERSHIP %
        # =================================================================
        
        insider_ownership_score = self._score_insider_ownership(ticker, insider_data)
        result['signals']['insider_ownership'] = insider_ownership_score
        
        # =================================================================
        # SIGNAL 8: DEBT STRUCTURE (equity-funded vs debt-funded losses)
        # =================================================================
        
        debt_structure_score = self._score_debt_structure(
            ticker, balance_years, income_years
        )
        result['signals']['debt_structure'] = debt_structure_score
        
        # =================================================================
        # AGGREGATE SCORE
        # =================================================================
        
        total = sum(s['score'] for s in result['signals'].values() if s)
        result['total_score'] = total
        result['passes'] = total >= result['pass_threshold']
        
        if result['passes']:
            self.logger.info(f"{ticker} Track B: {total}/{result['max_score']} - PASSES")
        else:
            self.logger.warning(f"{ticker} Track B: {total}/{result['max_score']} - FAILS")
        
        return result
    
    # =====================================================================
    # TRACK A SIGNAL SCORING METHODS
    # =====================================================================
    
    def _score_roic(self, ticker: str, income: List[Dict], balance: List[Dict]) -> Dict:
        """Score ROIC: > 20% (3), 12-20% (2), < 12% (1)"""
        
        if not income or not balance:
            return {'value': None, 'score': 2, 'reason': 'Missing data'}
        
        # ROIC = EBIT * (1 - tax rate) / Invested Capital
        # Simplified: Use most recent year EBIT / average assets
        
        most_recent_income = income[0]
        most_recent_balance = balance[0]
        
        ebit = most_recent_income.get('ebit')
        total_assets = most_recent_balance.get('totalAssets')
        
        if not ebit or not total_assets or total_assets == 0:
            return {'value': None, 'score': 2, 'reason': 'Insufficient financial data'}
        
        # Simplified ROIC approximation
        roic = ebit / total_assets if total_assets > 0 else None
        
        if roic is None:
            return {'value': None, 'score': 2, 'reason': 'Cannot calculate ROIC'}
        
        if roic > 0.20:
            return {'value': roic, 'score': 3, 'reason': f'ROIC {roic:.1%} > 20%'}
        elif roic >= 0.12:
            return {'value': roic, 'score': 2, 'reason': f'ROIC {roic:.1%} between 12-20%'}
        else:
            return {'value': roic, 'score': 1, 'reason': f'ROIC {roic:.1%} < 12%'}
    
    def _score_roic_trend(self, ticker: str, income: List[Dict], balance: List[Dict]) -> Dict:
        """Score ROIC trend: improving (3), stable (2), deteriorating (1)"""
        
        if len(income) < 3 or len(balance) < 3:
            return {'value': None, 'score': 2, 'reason': 'Need 3+ years for trend'}
        
        roics = []
        for i in range(min(3, len(income), len(balance))):
            ebit = income[i].get('ebit')
            assets = balance[i].get('totalAssets')
            if ebit and assets and assets > 0:
                roics.append(ebit / assets)
        
        if len(roics) < 2:
            return {'value': None, 'score': 2, 'reason': 'Insufficient years for trend'}
        
        # First vs most recent
        recent_roic = roics[0]
        older_roic = roics[-1]
        trend = recent_roic - older_roic
        
        if trend > 0.02:  # > 2% improvement
            return {'value': trend, 'score': 3, 'reason': f'ROIC improving ({trend:+.1%})'}
        elif abs(trend) <= 0.02:
            return {'value': trend, 'score': 2, 'reason': f'ROIC stable ({trend:+.1%})'}
        else:
            return {'value': trend, 'score': 1, 'reason': f'ROIC deteriorating ({trend:+.1%})'}
    
    def _score_fcf_consistency(self, ticker: str, cashflow: List[Dict]) -> Dict:
        """Score FCF consistency: 5/5 (3), 4/5 (2), 3+/5 (1)"""
        
        if not cashflow or len(cashflow) == 0:
            return {'value': None, 'score': 1, 'reason': 'No cashflow data'}
        
        fcf_positive = 0
        years_analyzed = 0
        
        for i, year_data in enumerate(cashflow):
            fcf = year_data.get('freeCashflow')
            if fcf is not None:
                if fcf > 0:
                    fcf_positive += 1
                years_analyzed += 1
                if years_analyzed >= 5:
                    break
        
        if years_analyzed == 0:
            return {'value': None, 'score': 1, 'reason': 'No FCF values available'}
        
        if fcf_positive == 5:
            return {'value': fcf_positive, 'score': 3, 'reason': f'FCF positive {fcf_positive}/{years_analyzed}'}
        elif fcf_positive == 4:
            return {'value': fcf_positive, 'score': 2, 'reason': f'FCF positive {fcf_positive}/{years_analyzed}'}
        else:
            return {'value': fcf_positive, 'score': 1, 'reason': f'FCF positive {fcf_positive}/{years_analyzed}'}
    
    def _score_reinvestment_rate(self, ticker: str, income: List[Dict], cashflow: List[Dict]) -> Dict:
        """Score reinvestment rate: > 40% (3), 20-40% (2), < 20% (1)"""
        
        if not income or not cashflow or len(income) == 0:
            return {'value': None, 'score': 2, 'reason': 'Missing income/cashflow data'}
        
        most_recent_income = income[0]
        most_recent_cf = cashflow[0] if cashflow else None
        
        net_income = most_recent_income.get('netIncome')
        fcf = most_recent_cf.get('freeCashflow') if most_recent_cf else None
        
        if net_income is None or net_income <= 0 or fcf is None:
            return {'value': None, 'score': 2, 'reason': 'Invalid net income/FCF for calculation'}
        
        # Reinvestment rate = 1 - (FCF / Net Income)
        # High reinvestment = low FCF relative to earnings
        reinvestment_rate = 1 - (fcf / net_income)
        
        if reinvestment_rate > 0.40:
            return {'value': reinvestment_rate, 'score': 3, 'reason': f'Reinvestment {reinvestment_rate:.1%}'}
        elif reinvestment_rate >= 0.20:
            return {'value': reinvestment_rate, 'score': 2, 'reason': f'Reinvestment {reinvestment_rate:.1%}'}
        else:
            return {'value': reinvestment_rate, 'score': 1, 'reason': f'Reinvestment {reinvestment_rate:.1%}'}
    
    def _score_trough_earnings(self, ticker: str, income: List[Dict]) -> Dict:
        """
        Score trough signal: BOTH conditions must be true:
        1. EBIT margin > 30% below 5yr average
        2. Revenue within 25% of 5yr average
        
        Score 3: Both true / Score 2: EBIT 15-30% below / Score 1: < 15% below
        """
        
        if len(income) < 3:
            return {'value': None, 'score': 2, 'reason': 'Need 3+ years of history'}
        
        revenues = []
        ebit_margins = []
        
        for year_data in income[:5]:
            revenue = year_data.get('totalRevenue')
            ebit = year_data.get('ebit')
            if revenue and ebit and revenue > 0:
                revenues.append(revenue)
                ebit_margins.append(ebit / revenue)
        
        if len(revenues) < 3:
            return {'value': None, 'score': 2, 'reason': 'Insufficient clean financial data'}
        
        most_recent_revenue = revenues[0]
        most_recent_margin = ebit_margins[0]
        
        avg_revenue = statistics.mean(revenues)
        avg_margin = statistics.mean(ebit_margins)
        
        # Check condition 1: EBIT margin compressed > 30%
        margin_compression = avg_margin - most_recent_margin
        margin_compressed = margin_compression > 0.30
        
        # Check condition 2: Revenue within 25% of average
        revenue_ratio = most_recent_revenue / avg_revenue
        revenue_stable = 0.75 <= revenue_ratio <= 1.25
        
        # Score based on margin compression (condition 2 must be true)
        if not revenue_stable:
            return {
                'value': f'margin_comp={margin_compression:.1%},rev_ratio={revenue_ratio:.1%}',
                'score': 1,
                'reason': 'Revenue not stable - possible structural decline not trough'
            }
        
        if margin_compression > 0.30:
            return {
                'value': f'margin_comp={margin_compression:.1%}',
                'score': 3,
                'reason': f'Trough signal: margin {margin_compression:.1%} below 5yr avg, revenue stable'
            }
        elif margin_compression > 0.15:
            return {
                'value': f'margin_comp={margin_compression:.1%}',
                'score': 2,
                'reason': f'Possible trough: margin {margin_compression:.1%} below 5yr avg'
            }
        else:
            return {
                'value': f'margin_comp={margin_compression:.1%}',
                'score': 1,
                'reason': f'No trough signal: margin only {margin_compression:.1%} below'
            }
    
    def _score_ev_fcf_valuation(
        self,
        ticker: str,
        cashflow: List[Dict],
        quote: Optional[Dict],
        price_history: Optional[Dict]
    ) -> Dict:
        """
        Score EV/FCF vs own 5-year average.
        > 30% below average (3), 10-30% below (2), at/above (1)
        """
        
        if not cashflow or not quote or not price_history:
            return {'value': None, 'score': 2, 'reason': 'Missing price or cashflow data'}
        
        fcf_values = []
        for year_data in cashflow[:5]:
            fcf = year_data.get('freeCashflow')
            if fcf and fcf > 0:
                fcf_values.append(fcf)
        
        if len(fcf_values) < 3:
            return {'value': None, 'score': 2, 'reason': 'Need 3+ years of positive FCF'}
        
        market_cap = quote.get('marketCap')
        if not market_cap or market_cap <= 0:
            return {'value': None, 'score': 2, 'reason': 'Invalid market cap'}
        
        # Current EV/FCF (using most recent FCF)
        current_fcf = fcf_values[0]
        current_ev_fcf = market_cap / current_fcf if current_fcf > 0 else None
        
        if not current_ev_fcf:
            return {'value': None, 'score': 2, 'reason': 'Cannot calculate current EV/FCF'}
        
        # Average historical EV/FCF (proxy: average FCF * historical market cap estimate)
        # Simplified: use average FCF
        avg_fcf = statistics.mean(fcf_values)
        avg_ev_fcf = market_cap / avg_fcf if avg_fcf > 0 else current_ev_fcf
        
        # Compare
        discount = 1 - (current_ev_fcf / avg_ev_fcf)
        
        if discount > 0.30:
            return {'value': discount, 'score': 3, 'reason': f'EV/FCF {discount:.1%} below 5yr avg'}
        elif discount > 0.10:
            return {'value': discount, 'score': 2, 'reason': f'EV/FCF {discount:.1%} below 5yr avg'}
        else:
            return {'value': discount, 'score': 1, 'reason': f'EV/FCF at or above 5yr avg'}
    
    def _score_insider_ownership(self, ticker: str, insider_data: Optional[Dict]) -> Dict:
        """Score insider ownership: > 15% (3), 5-15% (2), < 5% (1)"""
        
        # Note: FMP insider endpoint may not provide ownership % directly
        # This is a placeholder - would need additional data source
        
        return {
            'value': None,
            'score': 2,
            'reason': 'Insider ownership data not available (requires additional data source)'
        }
    
    def _score_net_cash_floor(self, ticker: str, balance: List[Dict], quote: Optional[Dict]) -> Dict:
        """Score net cash as % of market cap: > 15% (3), 0-15% (2), net debt (1)"""
        
        if not balance or not quote:
            return {'value': None, 'score': 2, 'reason': 'Missing balance sheet or quote data'}
        
        most_recent_balance = balance[0]
        cash = most_recent_balance.get('cash')
        total_debt = most_recent_balance.get('totalDebt')
        market_cap = quote.get('marketCap')
        
        if cash is None or total_debt is None or market_cap is None or market_cap <= 0:
            return {'value': None, 'score': 2, 'reason': 'Missing balance sheet components'}
        
        net_cash = cash - total_debt
        net_cash_pct = net_cash / market_cap
        
        if net_cash_pct > 0.15:
            return {'value': net_cash_pct, 'score': 3, 'reason': f'Net cash {net_cash_pct:.1%} of market cap'}
        elif net_cash_pct >= 0:
            return {'value': net_cash_pct, 'score': 2, 'reason': f'Net cash {net_cash_pct:.1%} of market cap'}
        else:
            return {'value': net_cash_pct, 'score': 1, 'reason': f'Net debt position {net_cash_pct:.1%}'}
    
    # =====================================================================
    # TRACK B SIGNAL SCORING METHODS
    # =====================================================================
    
    def _score_gross_margin(self, ticker: str, income: List[Dict]) -> Dict:
        """Score gross margin & trend: > 60% rising (3), 40-60% stable (2), falling (1)"""
        
        if len(income) < 2:
            return {'value': None, 'score': 2, 'reason': 'Need 2+ years for margin'}
        
        margins = []
        for year_data in income[:5]:
            revenue = year_data.get('totalRevenue')
            cogs = year_data.get('costOfRevenue')
            if revenue and cogs is not None:
                margins.append((revenue - cogs) / revenue)
        
        if len(margins) < 2:
            return {'value': None, 'score': 2, 'reason': 'Cannot calculate gross margin'}
        
        current_margin = margins[0]
        trend = margins[0] - margins[1] if len(margins) > 1 else 0
        
        if current_margin > 0.60 and trend > 0:
            return {'value': current_margin, 'score': 3, 'reason': f'GM {current_margin:.1%} > 60% and rising'}
        elif 0.40 <= current_margin <= 0.60 and abs(trend) <= 0.05:
            return {'value': current_margin, 'score': 2, 'reason': f'GM {current_margin:.1%} in range, stable'}
        else:
            return {'value': current_margin, 'score': 1, 'reason': f'GM {current_margin:.1%} < 40% or falling'}
    
    def _score_revenue_growth(self, ticker: str, income: List[Dict]) -> Dict:
        """Score 3-year revenue CAGR: > 30% (3), 15-30% (2), < 15% (1)"""
        
        if len(income) < 4:
            return {'value': None, 'score': 2, 'reason': 'Need 4 years for 3yr CAGR'}
        
        rev_3yr = income[0].get('totalRevenue')
        rev_base = income[3].get('totalRevenue')
        
        if not rev_3yr or not rev_base or rev_base <= 0:
            return {'value': None, 'score': 2, 'reason': 'Cannot calculate CAGR'}
        
        cagr = (rev_3yr / rev_base) ** (1/3) - 1
        
        if cagr > 0.30:
            return {'value': cagr, 'score': 3, 'reason': f'3yr CAGR {cagr:.1%} > 30%'}
        elif cagr >= 0.15:
            return {'value': cagr, 'score': 2, 'reason': f'3yr CAGR {cagr:.1%}'}
        else:
            return {'value': cagr, 'score': 1, 'reason': f'3yr CAGR {cagr:.1%} < 15%'}
    
    def _score_rd_capex_loss(self, ticker: str, income: List[Dict], cashflow: List[Dict]) -> Dict:
        """Score R&D + capex as % of loss: > 80% (3), 50-80% (2), < 50% (1)"""
        
        if len(income) < 1 or len(cashflow) < 1:
            return {'value': None, 'score': 2, 'reason': 'Missing income/cashflow'}
        
        net_income = income[0].get('netIncome')
        if not net_income or net_income >= 0:
            return {'value': None, 'score': 2, 'reason': 'Not a loss year'}
        
        loss = abs(net_income)
        capex = abs(cashflow[0].get('capitalExpenditure') or 0)
        # Note: R&D usually in operating expenses, would need additional parsing
        
        if loss <= 0:
            return {'value': None, 'score': 2, 'reason': 'Company is profitable'}
        
        investment_as_pct_loss = (capex / loss) if loss > 0 else 0
        
        if investment_as_pct_loss > 0.80:
            return {'value': investment_as_pct_loss, 'score': 3, 'reason': f'{investment_as_pct_loss:.0%} of loss is capex'}
        elif investment_as_pct_loss >= 0.50:
            return {'value': investment_as_pct_loss, 'score': 2, 'reason': f'{investment_as_pct_loss:.0%} of loss is capex'}
        else:
            return {'value': investment_as_pct_loss, 'score': 1, 'reason': f'{investment_as_pct_loss:.0%} - core bleeding'}
    
    def _score_operating_leverage(self, ticker: str, income: List[Dict]) -> Dict:
        """Score operating leverage: narrowing > 5%/yr (3), < 5%/yr (2), flat/wide (1)"""
        
        if len(income) < 3:
            return {'value': None, 'score': 2, 'reason': 'Need 3+ years'}
        
        losses_pct_revenue = []
        for year_data in income[:3]:
            net_income = year_data.get('netIncome')
            revenue = year_data.get('totalRevenue')
            if net_income is not None and revenue and revenue > 0:
                losses_pct_revenue.append(abs(net_income) / revenue if net_income < 0 else 0)
        
        if len(losses_pct_revenue) < 2:
            return {'value': None, 'score': 2, 'reason': 'Insufficient data'}
        
        trend = losses_pct_revenue[0] - losses_pct_revenue[-1]
        
        if trend > 0.05:
            return {'value': trend, 'score': 3, 'reason': f'Losses narrowing {trend:.1%}/yr'}
        elif trend >= 0:
            return {'value': trend, 'score': 2, 'reason': f'Losses narrowing {trend:.1%}/yr'}
        else:
            return {'value': trend, 'score': 1, 'reason': f'Losses widening {trend:.1%}/yr'}
    
    def _score_gross_profit_growth(self, ticker: str, income: List[Dict]) -> Dict:
        """Score GP growth vs revenue growth: GP faster (3), same (2), slower (1)"""
        
        if len(income) < 4:
            return {'value': None, 'score': 2, 'reason': 'Need 4+ years'}
        
        revenues = []
        gross_profits = []
        
        for year in income[:4]:
            rev = year.get('totalRevenue')
            cogs = year.get('costOfRevenue')
            if rev and cogs is not None:
                revenues.append(rev)
                gross_profits.append(rev - cogs)
        
        if len(revenues) < 2:
            return {'value': None, 'score': 2, 'reason': 'Cannot calculate'}
        
        # 3-year growth
        rev_growth = (revenues[0] / revenues[-1]) - 1
        gp_growth = (gross_profits[0] / gross_profits[-1]) - 1 if gross_profits[-1] != 0 else 0
        
        if gp_growth > rev_growth:
            return {'value': gp_growth - rev_growth, 'score': 3, 'reason': f'GP growth > revenue growth'}
        elif abs(gp_growth - rev_growth) < 0.05:
            return {'value': gp_growth - rev_growth, 'score': 2, 'reason': f'GP growth ≈ revenue growth'}
        else:
            return {'value': gp_growth - rev_growth, 'score': 1, 'reason': f'GP growth < revenue growth'}
    
    def _score_cash_runway(self, ticker: str, cashflow: List[Dict], quote: Optional[Dict]) -> Dict:
        """Score cash runway at current burn rate: > 4 years (3), 2-4 (2), < 2 (1)"""
        
        if not quote:
            return {'value': None, 'score': 2, 'reason': 'Missing quote data'}
        
        cash = quote.get('marketCap')  # Proxy for cash available
        if not cash or len(cashflow) < 1:
            return {'value': None, 'score': 2, 'reason': 'Missing cash/burn data'}
        
        burn_rate = abs(cashflow[0].get('operatingCashflow') or 0)
        if burn_rate <= 0:
            return {'value': None, 'score': 2, 'reason': 'Positive operating cashflow'}
        
        years_runway = cash / burn_rate if burn_rate > 0 else 999
        
        if years_runway > 4:
            return {'value': years_runway, 'score': 3, 'reason': f'{years_runway:.1f} years runway'}
        elif years_runway >= 2:
            return {'value': years_runway, 'score': 2, 'reason': f'{years_runway:.1f} years runway'}
        else:
            return {'value': years_runway, 'score': 1, 'reason': f'{years_runway:.1f} years runway - high dilution risk'}
    
    def _score_debt_structure(self, ticker: str, balance: List[Dict], income: List[Dict]) -> Dict:
        """
        Score debt structure: equity-funded losses (3), minimal debt (2), debt-funded (1)
        
        This is qualitative - would need more detailed debt breakdown + loss analysis
        """
        
        if not balance or not income:
            return {'value': None, 'score': 2, 'reason': 'Missing data'}
        
        net_income = income[0].get('netIncome')
        debt = balance[0].get('totalDebt')
        cash = balance[0].get('cash')
        
        if net_income is not None and net_income > 0:
            return {'value': None, 'score': 2, 'reason': 'Not loss-making'}
        
        if debt is None or cash is None:
            return {'value': None, 'score': 2, 'reason': 'Missing debt/cash data'}
        
        net_debt = debt - cash
        
        if net_debt <= 0:
            return {'value': net_debt, 'score': 3, 'reason': 'Equity-funded (net cash)'}
        elif debt < 50e9:  # Arbitrary small threshold
            return {'value': net_debt, 'score': 2, 'reason': 'Minimal debt'}
        else:
            return {'value': net_debt, 'score': 1, 'reason': f'Debt-funded: ${net_debt/1e9:.1f}B net debt'}


if __name__ == "__main__":
    # Quick test
    scorer = SignalScorer()
    print("SignalScorer initialized successfully")
    print("Track A: 8 signals, threshold 16/24")
    print("Track B: 8 signals, threshold 14/24")
