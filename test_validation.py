"""
Test Script - Validate the end-to-end pipeline on known stocks

Test stocks:
- MSFT: Tech giant, should pass all halal gates, Track A, strong profitable compounder
- AAPL: Tech giant, should pass all halal gates, Track A, strong profitable compounder  
- JPM: Bank, should FAIL halal gates (riba business model)
"""

import json
from validation import ValidationWorkflow, format_validation_result


def run_validation_tests():
    """Run validation pipeline on test stocks."""
    
    workflow = ValidationWorkflow()
    
    test_tickers = ['MSFT', 'AAPL', 'JPM']
    results = {}
    
    print("=" * 80)
    print("HALAL ASYMMETRIC STOCK FINDER - VALIDATION PIPELINE TEST")
    print("=" * 80)
    print()
    
    for ticker in test_tickers:
        print(f"\n{'='*80}")
        print(f"Testing: {ticker}")
        print(f"{'='*80}")
        
        result = workflow.validate_ticker(ticker)
        results[ticker] = result
        
        # Print formatted result
        print(format_validation_result(result))
        print()
        
        # Print stage results
        if result.get('status') in ['complete', 'incomplete']:
            stages = result.get('stages', {})
            
            # Halal gates
            halal = stages.get('halal_gates')
            if halal:
                print(f"Halal Status: {halal.get('halal_status').upper()}")
                if halal.get('flags'):
                    print(f"  Flags: {', '.join(halal.get('flags', []))}")
            
            # Track detection
            track = stages.get('track_detection')
            if track:
                print(f"Track: {track.get('track')} ({track.get('conviction', 'unknown')} conviction)")
            
            # Signal scoring
            signals = stages.get('signal_scoring')
            if signals:
                total = signals.get('total_score', 0)
                max_score = signals.get('max_score', 24)
                threshold = signals.get('pass_threshold', 16)
                passes = signals.get('passes', False)
                print(f"Signal Score: {total}/{max_score} (threshold: {threshold}) - {'PASS' if passes else 'FAIL'}")
            
            # Pattern detection
            pattern = stages.get('pattern_detection')
            if pattern:
                print(f"Asymmetric Pattern: {pattern.get('result').upper()}")
                print(f"  Floor: {pattern.get('floor')} - {pattern.get('floor_reason')}")
                print(f"  Mispricing: {pattern.get('mispricing')} - {pattern.get('mispricing_reason')}")
                print(f"  Catalyst: {pattern.get('catalyst')} - {pattern.get('catalyst_reason')}")
                print(f"  Max Conviction: {pattern.get('conviction_max').upper()}")
        
        elif result.get('status') == 'error':
            print(f"Error: {result.get('error')}")
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    
    passed = sum(1 for r in results.values() if r.get('status') == 'complete')
    total = len(results)
    print(f"Completed: {passed}/{total}")
    
    print("\n")
    for ticker, result in results.items():
        status_icon = "✅" if result.get('status') == 'complete' else "❌"
        print(f"{status_icon} {ticker}: {result.get('final_verdict')}")
    
    return results


if __name__ == "__main__":
    results = run_validation_tests()
    
    # Save results to file
    with open('validation_test_results.json', 'w') as f:
        # Convert non-serializable objects
        json.dump(results, f, indent=2, default=str)
    
    print(f"\nResults saved to: validation_test_results.json")
