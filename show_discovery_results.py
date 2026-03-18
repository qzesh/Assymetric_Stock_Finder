"""
Load and display discovery results from checkpoint database.
"""

import sqlite3
import json
from typing import List, Dict

def load_discovery_results(db_path: str = 'discovery_checkpoint.db') -> List[Dict]:
    """Load analysis results from checkpoint database and rank them."""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all analysis results
    cursor.execute('SELECT ticker, validation_result FROM analysis_results ORDER BY ticker')
    
    results = []
    for ticker, validation_json in cursor.fetchall():
        validation = json.loads(validation_json)
        
        # Skip if validation failed
        if validation.get('status') == 'error':
            continue
        
        # Extract key metrics - with safe defaults
        stages = validation.get('stages') or {}
        halal_gates = stages.get('halal_gates') or {}
        track_detection = stages.get('track_detection') or {}
        pattern_detection = stages.get('pattern_detection') or {}
        signal_scoring = stages.get('signal_scoring') or {}
        
        halal_status = halal_gates.get('halal_status', 'unknown')
        track = track_detection.get('track', 'unknown')
        pattern_type = pattern_detection.get('result', 'not_asymmetric')  # Use 'result' not 'pattern_type'
        signal_score = signal_scoring.get('total_score', 0)
        signal_threshold = signal_scoring.get('threshold', 16)
        conviction = validation.get('conviction', 'low')
        
        # Skip halal failures
        if halal_status == 'fail':
            continue
        
        # Calculate scoring
        asymmetry_scores = {'full': 3.0, 'partial': 1.5, 'not_asymmetric': 0.0}
        asymmetry_score = asymmetry_scores.get(pattern_type, 0.0)
        signal_normalized = min(3.0, (signal_score / signal_threshold) * 3.0) if signal_threshold > 0 else 0
        composite_score = (asymmetry_score * 0.60) + (signal_normalized * 0.40)
        
        results.append({
            'ticker': ticker,
            'asymmetry_score': asymmetry_score,
            'signal_score': signal_normalized,
            'signal_raw': signal_score,
            'composite_score': composite_score,
            'halal_status': halal_status,
            'track': track,
            'pattern': pattern_type,
            'conviction': conviction,
            'halal_verdict': validation.get('stages', {}).get('halal_gates', {}).get('halal_verdict', 'unknown'),
        })
    
    conn.close()
    
    # Sort by composite score
    results = sorted(results, key=lambda x: x['composite_score'], reverse=True)
    
    # Add ranks
    for i, r in enumerate(results, 1):
        r['rank'] = i
    
    return results


def format_discovery_summary(results: List[Dict]) -> str:
    """Format discovery results for display."""
    
    lines = [
        "\n" + "="*80,
        "✅ DISCOVERY RESULTS - TOP OPPORTUNITIES",
        "="*80,
        ""
    ]
    
    if not results:
        lines.append("❌ No qualifying candidates (all failed halal gates)")
        lines.append("="*80)
        return "\n".join(lines)
    
    lines.append(f"✓ Found {len(results)} qualifying candidates (halal + viable track)\n")
    
    # Show top 5
    for candidate in results[:5]:
        lines.extend([
            f"#{candidate['rank']}. {candidate['ticker']} | Score: {candidate['composite_score']:.2f}",
            f"    Asymmetry: {candidate['asymmetry_score']:.1f} ({candidate['pattern'].upper()})",
            f"    Signals: {candidate['signal_raw']}/24 ({candidate['signal_score']:.1f})",
            f"    Track: {candidate['track']} | Halal: {candidate['halal_status'].upper()}",
            f"    Conviction: {candidate['conviction'].upper()}",
            ""
        ])
    
    lines.append("="*80)
    return "\n".join(lines)


if __name__ == "__main__":
    results = load_discovery_results()
    print(format_discovery_summary(results))
    
    # Save results
    with open('discovery_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ Results saved to discovery_results.json ({len(results)} candidates)")
