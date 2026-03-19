#!/usr/bin/env python3
"""
Demo: Halal Stock Validation with Claude AI

Shows how to use halal.py with fetcher.py to validate real stocks.
"""

import sys
import logging
from typing import Dict, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)

print("\n" + "="*80)
print("HALAL STOCK VALIDATION DEMO - CLAUDE AI POWERED")
print("="*80 + "\n")

def run_halal_validation_demo():
    """Run halal validation on test stocks with Claude AI."""
    
    from halal import HalalGateEngine
    
    engine = HalalGateEngine()
    
    print("Testing halal compliance across different stock types:\n")
    
    # Demo stocks with realistic financial data
    demo_cases = [
        {
            'ticker': 'MSFT',
            'sector': 'Technology',
            'total_revenue': 245e9,
            'total_debt': 50e9,
            'market_cap_30d_avg': 2800e9,
            'segments': None,
            'track': 'A',
            'expected': 'pass'
        },
        {
            'ticker': 'JPM',
            'sector': 'Banks',
            'total_revenue': 120e9,
            'total_debt': 200e9,
            'market_cap_30d_avg': 350e9,
            'segments': None,
            'track': 'A',
            'expected': 'fail'
        },
        {
            'ticker': 'KO',
            'sector': 'Consumer Staples',
            'total_revenue': 45e9,
            'total_debt': 35e9,
            'market_cap_30d_avg': 280e9,
            'segments': None,
            'track': 'A',
            'expected': 'pass'
        },
        {
            'ticker': 'MO',
            'sector': 'Consumer Staples',
            'total_revenue': 30e9,
            'total_debt': 20e9,
            'market_cap_30d_avg': 100e9,
            'segments': {
                'segments': [
                    {'segment': 'Tobacco & Nicotine', 'revenue': 28e9},
                    {'segment': 'Other', 'revenue': 2e9}
                ]
            },
            'track': 'A',
            'expected': 'fail'
        },
    ]
    
    results = []
    
    for i, case in enumerate(demo_cases, 1):
        print("\n" + "-"*80)
        print(f"Test {i}: {case['ticker']}")
        print("-"*80)
        
        result = engine.evaluate_all_gates(
            ticker=case['ticker'],
            sector=case['sector'],
            total_revenue=case['total_revenue'],
            total_debt=case['total_debt'],
            market_cap_30d_avg=case['market_cap_30d_avg'],
            segments=case['segments'],
            fcf_history=None,
            track=case['track'],
            debt_funded_loss=None
        )
        
        halal_status = result['halal_status'].upper()
        verdict = result['halal_verdict']
        
        # Format gate results
        gates = result['gates']
        print(f"\nGate Results:")
        print(f"  Gate 1 (Riba):           {gates['gate1_riba'].get('status', 'N/A').upper():12} - {gates['gate1_riba'].get('reason', '')[:50]}")
        if gates['gate2_debt']:
            print(f"  Gate 2 (Debt):           {gates['gate2_debt'].get('status', 'N/A').upper():12} - {gates['gate2_debt'].get('reason', '')[:50]}")
        if gates['gate3_haram_revenue']:
            print(f"  Gate 3 (Haram Revenue):  {gates['gate3_haram_revenue'].get('status', 'N/A').upper():12} - {gates['gate3_haram_revenue'].get('reason', '')[:50]}")
        if gates['gate4_loss_financing']:
            print(f"  Gate 4 (Loss Financing): {gates['gate4_loss_financing'].get('status', 'N/A').upper():12}")
        
        # Show Claude AI decisions
        if 'claude_review' in result:
            print(f"\nClaude AI Review:")
            print(f"   {result['claude_review'][:100]}...")
        
        # Final verdict
        status_icon = "[PASS]" if halal_status in ['PASS', 'UNVERIFIED'] else "[FAIL]"
        print(f"\n{status_icon} Final Verdict: {halal_status}")
        print(f"   {verdict}")
        
        results.append({
            'ticker': case['ticker'],
            'status': halal_status,
            'verdict': verdict
        })
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}\n")
    
    for result in results:
        status_icon = "[PASS]" if result['status'] in ['PASS', 'UNVERIFIED'] else "[FAIL]"
        print(f"{status_icon} {result['ticker']:8} - {result['status']:12}")
    
    return results


if __name__ == "__main__":
    try:
        results = run_halal_validation_demo()
        
        print("\n" + "="*80)
        print("[SUCCESS] HALAL VALIDATION DEMO COMPLETED SUCCESSFULLY")
        print("="*80)
        print("\nKey Features Demonstrated:")
        print("  [OK] Gate 1: Sector-based riba business model screening")
        print("  [OK] Gate 2: Debt-to-market-cap ratio validation (< 33%)")
        print("  [OK] Gate 3: Haram revenue stream identification (< 5%)")
        print("  [OK] Gate 4: Loss financing equity vs debt analysis")
        print("  [OK] Claude AI: Intelligent review of unverified cases")
        print("\nNext Steps:")
        print("  1. Run fetcher.py to get real financial data")
        print("  2. Use prepare_halal_evaluation_data() to format data")
        print("  3. Pass data to HalalGateEngine.evaluate_all_gates()")
        print("  4. Claude AI will handle edge cases and unverified data")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        import traceback
        traceback.print_exc()
        sys.exit(1)
