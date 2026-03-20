#!/usr/bin/env python3
"""
Update top 5 asymmetric stocks with latest halal status from Claude AI.
Refreshes halal verification and caches results.
"""

import json
import sys
from typing import List, Dict
from halal_cache import HalalStatusCache


def load_discovery_results(filepath: str = 'discovery_results.json') -> List[Dict]:
    """Load discovery results from JSON file."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"ERROR: {filepath} not found")
        return []


def update_top5_with_halal(filepath: str = 'discovery_results.json', 
                          force_refresh: bool = False,
                          top_n: int = 5) -> None:
    """
    Update top N stocks with latest halal status.
    
    Args:
        filepath: Path to discovery_results.json
        force_refresh: If True, force Claude AI re-verification (bypass cache)
        top_n: Number of top stocks to update
    """
    print(f"[UPDATE] Updating top {top_n} asymmetric stocks with halal status...\n")
    
    # Load current results
    results = load_discovery_results(filepath)
    if not results:
        print("[ERROR] No results to update")
        return
    
    # Get top N
    top_stocks = results[:top_n]
    print(f"[INFO] Found {len(top_stocks)} stocks to verify:")
    for stock in top_stocks:
        print(f"  [{stock['rank']}] {stock['ticker']} (asymmetry: {stock['asymmetry_score']})")
    print()
    
    # Initialize halal cache
    cache = HalalStatusCache()
    
    # Update each stock with halal status
    updated_count = 0
    for i, stock in enumerate(top_stocks, 1):
        ticker = stock['ticker']
        print(f"[{i}/{len(top_stocks)}] Verifying {ticker}...")
        
        try:
            # Get halal status with cache
            halal_result = cache.get_halal_status_with_cache(
                ticker, 
                force_refresh=force_refresh
            )
            
            if halal_result:
                # Update stock with halal information
                stock['halal_status'] = halal_result.get('halal_status', 'unverified')
                stock['halal_verdict'] = halal_result.get('halal_verdict', '')
                stock['halal_gates'] = halal_result.get('gates', {})
                stock['halal_flags'] = halal_result.get('flags', [])
                stock['halal_claude_review'] = halal_result.get('claude_review')
                
                # Display status
                status_text = {
                    'pass': '[PASS]',
                    'fail': '[FAIL]',
                    'unverified': '[UNVERIFIED]'
                }.get(halal_result.get('halal_status'), '[UNKNOWN]')
                
                cached_indicator = "(cached)" if halal_result.get('cached') else "(fresh)"
                print(f"   {status_text} {ticker}: {halal_result.get('halal_status').upper()} {cached_indicator}")
                print(f"      -> {halal_result.get('halal_verdict', '')[:80]}...")
                
                updated_count += 1
            else:
                print(f"   [SKIP] {ticker}: Failed to retrieve halal status")
        
        except Exception as e:
            print(f"   [ERROR] {ticker}: {str(e)}")
    
    # Save updated results
    try:
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n[SUCCESS] Updated {updated_count}/{len(top_stocks)} stocks")
        print(f"[SAVED] Results to: {filepath}")
        
        # Display cache stats
        stats = cache.get_cache_stats()
        print(f"\n[CACHE STATS]")
        print(f"   Total cached: {stats['total_cached']}")
        print(f"   Cache hits: {stats['cache_hits']}")
        print(f"   Expired items: {stats['expired_items']}")
        
    except Exception as e:
        print(f"\n[ERROR] Saving results: {str(e)}")
        sys.exit(1)


def display_updated_results(filepath: str = 'discovery_results.json') -> None:
    """Display the updated top 5 with halal status."""
    results = load_discovery_results(filepath)
    if not results:
        return
    
    print("\n" + "="*80)
    print("TOP 5 ASYMMETRIC STOCKS WITH HALAL STATUS")
    print("="*80)
    
    for stock in results[:5]:
        status_text = {
            'pass': '[PASS]',
            'fail': '[FAIL]',
            'unverified': '[UNVERIFIED]'
        }.get(stock.get('halal_status'), '[UNKNOWN]')
        
        print(f"\n#{stock['rank']} {stock['ticker']}")
        print(f"  Asymmetry Score: {stock['asymmetry_score']}")
        print(f"  Composite Score: {stock['composite_score']}")
        print(f"  {status_text} Halal Status: {stock.get('halal_status', 'unknown').upper()}")
        print(f"  Verdict: {stock.get('halal_verdict', 'N/A')}")
        
        # Show failed gates if any
        gates = stock.get('halal_gates', {})
        if gates:
            failed_gates = [g for g, info in gates.items() if info.get('status') == 'fail']
            if failed_gates:
                print(f"  Failed Gates: {', '.join(failed_gates)}")
        
        # Show flags if any
        flags = stock.get('halal_flags', [])
        if flags:
            print(f"  Flags: {', '.join(flags)}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Update top 5 asymmetric stocks with halal status'
    )
    parser.add_argument(
        '--force-refresh',
        action='store_true',
        help='Force Claude AI re-verification (bypass cache)'
    )
    parser.add_argument(
        '--top-n',
        type=int,
        default=5,
        help='Number of top stocks to update (default: 5)'
    )
    parser.add_argument(
        '--show-results',
        action='store_true',
        help='Display updated results after updating'
    )
    
    args = parser.parse_args()
    
    # Update top stocks with halal status
    update_top5_with_halal(
        force_refresh=args.force_refresh,
        top_n=args.top_n
    )
    
    # Display results if requested
    if args.show_results:
        display_updated_results()
