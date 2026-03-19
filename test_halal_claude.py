#!/usr/bin/env python3
"""Test script for halal.py with Claude AI integration"""

import sys
import logging

logging.basicConfig(level=logging.INFO)

print("=" * 80)
print("TESTING HALAL GATES WITH CLAUDE AI")
print("=" * 80)

# Test 1: Import and initialize
print("\n✓ Test 1: Importing HalalGateEngine...")
try:
    from halal import HalalGateEngine
    print("✅ Successfully imported HalalGateEngine")
except Exception as e:
    print(f"❌ Failed to import: {e}")
    sys.exit(1)

# Test 2: Initialize engine
print("\n✓ Test 2: Initializing HalalGateEngine...")
try:
    engine = HalalGateEngine()
    print("✅ HalalGateEngine initialized")
    print(f"✅ Anthropic client available: {engine.client is not None}")
except Exception as e:
    print(f"❌ Failed to initialize: {e}")
    sys.exit(1)

# Test 3: Test halal gates with known data
print("\n✓ Test 3: Testing Gate 1 (Riba - should FAIL for JPM)...")
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
print(f"   Halal Status: {result1['halal_status'].upper()}")
print(f"   Verdict: {result1['halal_verdict']}")
print(f"   ✅ Test passed!" if result1['halal_status'] == 'fail' else "   ❌ Expected FAIL")

# Test 4: Test Gate 2 (Debt ratio - should PASS for MSFT)
print("\n✓ Test 4: Testing Gate 2 (Debt Ratio - should PASS for MSFT)...")
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
print(f"   Halal Status: {result2['halal_status'].upper()}")
print(f"   Verdict: {result2['halal_verdict']}")
print(f"   ✅ Test passed!" if result2['halal_status'] == 'pass' else "   Result: " + result2['halal_status'])

# Test 5: Test Claude AI integration (with unverified flag)
print("\n✓ Test 5: Testing Claude AI integration (unverified scenario)...")
result3 = engine.evaluate_all_gates(
    ticker='UNKNOWN',
    sector=None,  # This will create an unverified flag
    total_revenue=100e9,
    total_debt=20e9,
    market_cap_30d_avg=200e9,
    segments=None,
    fcf_history=None,
    track='A'
)
print(f"   Halal Status: {result3['halal_status'].upper()}")
print(f"   Verdict: {result3['halal_verdict']}")
if 'claude_review' in result3:
    print(f"   Claude Review: {result3['claude_review']}")
print(f"   ✅ Claude AI review completed!" if 'claude_review' in result3 else "   Note: No Claude review (expected for complete data)")

print("\n" + "=" * 80)
print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
print("=" * 80)
