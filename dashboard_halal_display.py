"""
Dashboard Integration - Halal Status Display with Cache

Provides enhanced display functions for Streamlit dashboard showing:
- Halal status with cache age
- Claude AI review indicators
- Search with auto-verification
- Cache statistics
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Optional
from halal_cache import get_halal_cache


class DashboardHalalDisplay:
    """Display halal status in dashboard with cache indicators."""
    
    def __init__(self):
        self.cache = get_halal_cache()
    
    def display_halal_status_badge(self, halal_result: Dict, compact: bool = False) -> str:
        """
        Create HTML badge for halal status.
        
        Args:
            halal_result: Halal status dict from cache
            compact: Show compact version (for tables)
        
        Returns:
            HTML string for Streamlit display
        """
        status = halal_result.get('halal_status', 'unknown').upper()
        cached = halal_result.get('cached', False)
        cache_age = halal_result.get('cache_age_days', 0)
        has_claude = bool(halal_result.get('claude_review'))
        
        # Status colors
        if status == 'PASS':
            bg_color = '#10b981'
            text = 'PASS'
        elif status == 'FAIL':
            bg_color = '#ef4444'
            text = 'FAIL'
        else:
            bg_color = '#f59e0b'
            text = 'UNVERIFIED'
        
        # Cache indicator
        cache_text = ''
        if cached:
            cache_text = f' [cached {cache_age:.0f}d]'
        
        # Claude indicator
        claude_text = ''
        if has_claude:
            claude_text = ' (Claude ✓)'
        
        if compact:
            # Compact: just badge
            return f'<span style="background-color: {bg_color}; color: white; padding: 4px 8px; border-radius: 6px; font-weight: bold; font-size: 0.9rem;">{text}{cache_text}</span>'
        else:
            # Full: badge + details
            full_text = f'{text}{cache_text}{claude_text}'
            return f'<div style="background-color: {bg_color}; color: white; padding: 8px 12px; border-radius: 8px; font-weight: bold; margin: 5px 0;">{full_text}</div>'
    
    def display_halal_verdict(self, halal_result: Dict) -> str:
        """Display halal verdict text."""
        verdict = halal_result.get('halal_verdict', 'No verdict available')
        claude_review = halal_result.get('claude_review', '')
        
        text = f"**Verdict**: {verdict}\n"
        if claude_review:
            text += f"\n**Claude AI Review**: {claude_review}"
        
        return text
    
    def display_halal_gates_detail(self, halal_result: Dict):
        """Display detailed gate results in Streamlit."""
        gates = halal_result.get('gates', {})
        
        for gate_name, gate_result in gates.items():
            if gate_result:
                status = gate_result.get('status', 'unknown').upper()
                reason = gate_result.get('reason', '')
                
                # Color code by status
                if status == 'PASS':
                    col = st.columns([0.3, 1])[1]
                    col.success(f"**{gate_name}**: {reason}")
                elif status == 'FAIL':
                    col = st.columns([0.3, 1])[1]
                    col.error(f"**{gate_name}**: {reason}")
                else:
                    col = st.columns([0.3, 1])[1]
                    col.warning(f"**{gate_name}**: {reason}")
    
    def display_top_candidates_with_halal(self, candidates: List[Dict]):
        """Enhanced top 5 display with halal status and Claude verification."""
        st.markdown("### Top Candidates with Halal Status")
        st.write("Shows halal compliance with automatic Claude AI verification")
        
        for i, candidate in enumerate(candidates[:5], 1):
            ticker = candidate.get('ticker')
            
            # Get halal status from cache (with auto-refresh if expired)
            halal_result = self.cache.get_halal_status_with_cache(ticker)
            
            # Create columns for layout
            col1, col2, col3, col4, col5 = st.columns([0.5, 1.2, 1.5, 1.8, 1.5])
            
            with col1:
                st.markdown(f"### #{i}")
            
            with col2:
                st.markdown(f"### {ticker}")
            
            with col3:
                # Asymmetry pattern
                pattern = candidate.get('pattern', 'none').upper()
                if pattern == 'FULL':
                    st.markdown('<div class="full-asymmetric"><strong>Full Asymmetric</strong></div>', unsafe_allow_html=True)
                elif pattern == 'PARTIAL':
                    st.markdown('<div class="partial-asymmetric"><strong>Partial</strong></div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="not-asymmetric">No Pattern</div>', unsafe_allow_html=True)
            
            with col4:
                # Halal status badge
                badge_html = self.display_halal_status_badge(halal_result, compact=True)
                st.markdown(badge_html, unsafe_allow_html=True)
                
                # Cache and Claude status
                if halal_result.get('cached'):
                    st.caption(f"🔄 Cached {halal_result.get('cache_age_days', 0):.0f}d")
                else:
                    st.caption("✨ Fresh verified")
            
            with col5:
                if st.button("Details", key=f"top_detail_{ticker}"):
                    st.session_state.selected_ticker = ticker
                    st.session_state.show_halal_detail = True
                    st.rerun()
            
            st.divider()
    
    def display_search_and_verify(self):
        """Search box with halal status and Claude verification."""
        st.markdown("### Search & Verify Halal Status")
        st.write("Search for any stock to check halal compliance with Claude AI verification")
        
        ticker_input = st.text_input(
            "Enter stock ticker",
            placeholder="e.g., MSFT, AAPL, JPM",
            key="halal_search_input"
        )
        
        if ticker_input:
            ticker = ticker_input.upper().strip()
            
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                force_refresh = st.checkbox("Force re-check with Claude AI")
            
            with col2:
                if st.button("Check Halal Status", key=f"verify_{ticker}"):
                    st.session_state.verify_ticker = ticker
                    st.session_state.force_refresh = force_refresh
            
            # Display results if available
            if hasattr(st.session_state, 'verify_ticker') and st.session_state.verify_ticker == ticker:
                try:
                    with st.spinner(f"Checking halal status for {ticker}..."):
                        halal_result = self.cache.get_halal_status_with_cache(
                            ticker,
                            force_refresh=force_refresh
                        )
                    
                    # Display badge
                    st.markdown("#### Halal Status")
                    badge_html = self.display_halal_status_badge(halal_result, compact=False)
                    st.markdown(badge_html, unsafe_allow_html=True)
                    
                    # Display verdict
                    st.markdown(self.display_halal_verdict(halal_result))
                    
                    # Expandable gate details
                    with st.expander("Gate Details"):
                        self.display_halal_gates_detail(halal_result)
                    
                    # Cache information
                    with st.expander("Cache Info"):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            cached_label = "Yes" if halal_result.get('cached') else "No"
                            st.metric("From Cache", cached_label)
                        
                        with col2:
                            cache_age = halal_result.get('cache_age_days', 0)
                            st.metric("Cache Age", f"{cache_age:.1f} days")
                        
                        with col3:
                            claude_label = "Yes" if halal_result.get('claude_review') else "No"
                            st.metric("Claude Reviewed", claude_label)
                        
                        # Expiry info
                        if halal_result.get('cached'):
                            remaining_days = 30 - cache_age
                            st.info(f"Cache expires in {remaining_days:.0f} days. Will auto-refresh with Claude AI when expired.")
                
                except Exception as e:
                    st.error(f"Error checking {ticker}: {str(e)}")
    
    def display_cache_stats(self):
        """Show cache statistics in sidebar or separate section."""
        stats = self.cache.get_cache_stats()
        
        st.markdown("### Cache Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Cached", stats['total_cached'])
        
        with col2:
            st.metric("Fresh", stats['fresh_entries'])
        
        with col3:
            st.metric("Expired", stats['expired_entries'])
        
        with col4:
            st.metric("TTL", f"{stats['cache_ttl_days']} days")
        
        # Status distribution
        if stats.get('status_distribution'):
            st.markdown("#### Status Distribution (Fresh Only)")
            status_df = pd.DataFrame(
                list(stats['status_distribution'].items()),
                columns=['Status', 'Count']
            )
            st.bar_chart(status_df.set_index('Status')['Count'])
    
    def display_bulk_verify(self, tickers: List[str]):
        """Bulk verify halal status for multiple tickers."""
        st.markdown("### Bulk Halal Verification")
        
        if st.button("Verify All"):
            st.info(f"Verifying halal status for {len(tickers)} stocks...")
            
            results = self.cache.get_halal_status_batch(tickers)
            
            # Create results table
            table_data = []
            for ticker, result in results.items():
                table_data.append({
                    'Ticker': ticker,
                    'Status': result.get('halal_status', 'error').upper(),
                    'Cached': result.get('cached', False),
                    'Age (days)': round(result.get('cache_age_days', 0), 1),
                    'Verdict': result.get('halal_verdict', '')[:50]
                })
            
            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True)
            
            # Download results
            csv = df.to_csv(index=False)
            st.download_button(
                "Download Results (CSV)",
                csv,
                "halal_verification_results.csv",
                "text/csv"
            )


def display_halal_in_top_5(results: List[Dict]):
    """Quick function to add halal display to existing top 5 in streamlit app."""
    display = DashboardHalalDisplay()
    display.display_top_candidates_with_halal(results[:5])


def display_search_modal():
    """Quick function to add halal search to streamlit app."""
    display = DashboardHalalDisplay()
    display.display_search_and_verify()


def display_stats_sidebar():
    """Quick function to show cache stats in sidebar."""
    display = DashboardHalalDisplay()
    with st.sidebar:
        display.display_cache_stats()


if __name__ == "__main__":
    # Test display
    st.set_page_config(page_title="Halal Dashboard Test", layout="wide")
    
    display = DashboardHalalDisplay()
    
    st.title("Halal Status Dashboard - Test")
    
    # Test search
    display.display_search_and_verify()
    
    st.divider()
    
    # Test cache stats
    display.display_cache_stats()
