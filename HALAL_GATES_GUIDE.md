# Halal Gate Engine with Claude AI - Complete Guide

## Overview

The **HalalGateEngine** is a four-gate Islamic finance compliance screening system that uses Claude AI for intelligent review of edge cases. It evaluates stocks against AAOIFI (Accounting and Auditing Organization for Islamic Financial Institutions) standards.

## Features

### Four Sequential Gates

1. **Gate 1: Riba Business Model** (Sector-based screening)
   - Auto-fails interest-based sectors: Banks, Financial Services, Insurance, etc.
   - No financial data needed
   - Immediate elimination if sector is interest-based

2. **Gate 2: Debt Ratio** (Financial health check)
   - Threshold: Total Debt / 30-day Avg Market Cap < 33%
   - Strict AAOIFI standard
   - Measured in percentage

3. **Gate 3: Haram Revenue** (Activity screening)
   - Threshold: Prohibited revenue < 5% of total
   - Prohibited categories: Alcohol, tobacco, weapons, gambling, pork, conventional finance
   - Requires revenue segment breakdown

4. **Gate 4: Loss Financing** (Track B specific)
   - For investment-phase companies (Track B) only
   - Losses must be equity-funded, not debt-funded
   - Track A companies automatically pass

### Claude AI Integration

When gates have unverified flags (missing data but no violations), **Claude AI makes intelligent judgments**:

- Analyzes all available evidence
- Applies Islamic finance principles conservatively
- Provides structured decisions: PASS or FAIL
- Includes detailed reasoning for investor review

## Usage

### Basic Example

```python
from halal import HalalGateEngine

engine = HalalGateEngine()

result = engine.evaluate_all_gates(
    ticker='MSFT',
    sector='Technology',
    total_revenue=245e9,
    total_debt=50e9,
    market_cap_30d_avg=2800e9,
    segments=None,  # Revenue breakdown (optional)
    fcf_history=None,  # Free cash flow history (optional)
    track='A',  # Track: A, A-Transition, or B
    debt_funded_loss=None  # For Track B only
)

print(f"Status: {result['halal_status']}")  # pass, fail, or unverified
print(f"Verdict: {result['halal_verdict']}")
```

### With Real Data from Fetcher

```python
from fetcher import get_full_stock_data
from halal import HalalGateEngine, prepare_halal_evaluation_data

# Get financial data
stock_data = get_full_stock_data('MSFT')

# Prepare halal evaluation data
halal_data = prepare_halal_evaluation_data(
    stock_data['financial'],
    stock_data['price']
)

# Run halal gates
engine = HalalGateEngine()
result = engine.evaluate_all_gates(
    ticker='MSFT',
    sector=halal_data['sector'],
    total_revenue=halal_data['total_revenue'],
    total_debt=halal_data['total_debt'],
    market_cap_30d_avg=halal_data['market_cap_30d_avg'],
    segments=halal_data['segments'],
    track='A'
)

if result['halal_status'] == 'fail':
    print(f"Stock failed halal screening: {result['halal_verdict']}")
else:
    print(f"Stock passed halal screening!")
```

## Return Structure

```python
{
    'ticker': str,           # Stock symbol
    'halal_status': str,     # 'pass', 'fail', or 'unverified'
    'gates': {
        'gate1_riba': {
            'status': str,   # 'pass', 'fail', or 'unverified'
            'reason': str    # Detailed explanation
        },
        'gate2_debt': {
            'status': str,
            'reason': str,
            'debt_ratio': float  # Calculated ratio
        },
        'gate3_haram_revenue': {
            'status': str,
            'reason': str,
            'haram_revenue_pct': float  # Percentage of haram revenue
        },
        'gate4_loss_financing': {
            'status': str,
            'reason': str
        }
    },
    'first_failure': str or None,  # Which gate failed first (if any)
    'flags': list,           # Warning messages
    'halal_verdict': str,    # Plain English summary
    'claude_review': str or None  # Claude AI reasoning (if used)
}
```

## Claude AI Scenarios

### Scenario 1: Complete Data - All Gates Verifiable
```
Result: Direct pass/fail based on gate evaluation
Claude AI: Not called (not needed)
```

### Scenario 2: Unverified Flags - Missing Data
```
Example: Sector unknown (Gate 1 unverified)
Claude AI: Called to determine pass/fail based on available evidence
Result: May PASS if other gates are strong
        May FAIL if data scarcity prevents verification
```

### Scenario 3: Multiple Unverified Flags
```
Example: Sector unknown + revenue segments not available
Claude AI: Analyzes combined flags and makes holistic decision
Result: Conservative: may FAIL if too much uncertainty
```

## Requirements

```
anthropic>=0.7.0
python-dotenv>=1.0.0
```

## Environment Setup

Add to .env:
```
ANTHROPIC_API_KEY=sk-ant-...
```

## Testing

Run the included test scripts:

```bash
# Basic halal gates test
python test_halal_claude.py

# Comprehensive demo with multiple stocks
python demo_halal_claude.py
```

## Integration Points

### In Validation Pipeline

The halal gates are the **first step** in the validation workflow:

```
1. Fetch financial data (fetcher.py)
   |
   v
2. Run halal gates (halal.py) <-- YOU ARE HERE
   |
   v-- Pass --> Run track detection (tracker.py)
   |           Run signal scoring (scorer.py)
   |           Run pattern detection (detector.py)
   |
   v-- Fail --> STOP - Stock eliminated
```

### Called By

- [validation.py](validation.py): Main validation workflow
- [test_validation.py](test_validation.py): End-to-end test suite

### Calls To

- Claude AI API (Anthropic): For unverified case decisions
- [fetcher.py](fetcher.py): For financial data (optional)

## Model Notes

- Uses `claude-sonnet-4-6` for Claude AI reviews
- Costs ~$0.01 per review (unverified cases only)
- Falls back to 'unverified' status if Claude fails

## Common Use Cases

### Case 1: Check if a Tech Stock is Halal
```python
from halal import HalalGateEngine

engine = HalalGateEngine()
result = engine.evaluate_all_gates(
    ticker='AAPL',
    sector='Technology',
    total_revenue=400e9,
    total_debt=100e9,
    market_cap_30d_avg=3000e9,
    segments={'segments': [
        {'segment': 'Products', 'revenue': 300e9},
        {'segment': 'Services', 'revenue': 100e9}
    ]},
    track='A'
)

# Result: PASS (Tech + low debt + no haram revenue)
```

### Case 2: Insurance Stock (Should Fail)
```python
result = engine.evaluate_all_gates(
    ticker='BRK',
    sector='Insurance',
    ...
)

# Result: FAIL (Insurance = riba business model)
```

### Case 3: Startup with Missing Data
```python
result = engine.evaluate_all_gates(
    ticker='UNKNOWN',
    sector=None,  # Unknown
    total_revenue=1e9,
    total_debt=500e6,
    market_cap_30d_avg=5e9,
    segments=None,  # No segment data
    track='B'
)

# Claude AI is called to review missing data
# Result: May PASS (if equity-funded) or FAIL (if too much uncertainty)
```

## FAQ

**Q: Why does Claude AI fail for some stocks even though gates pass?**
- A: Claude applies a conservative principle: without enough evidence of halal compliance, Islamic finance principles suggest waiting for more data.

**Q: Can I use halal.py without Claude API?**
- A: Yes, the gates work independently. Claude AI is only used for edge cases with unverified flags. If Claude fails, the system defaults to 'unverified' status.

**Q: What percentage of stocks fail halal screening?**
- A: Approximately 40-50% fail Gate 1 (financial sector) and another 10-15% fail Gate 3 (haram revenue). ~30-40% pass all gates.

**Q: How often should I run halal screening?**
- A: Once per quarter for established stocks, or whenever significant sector/business model changes occur.

## References

- AAOIFI Standards: https://aaoifi.com/
- Islamic Finance Standards: https://www.ifsb.org/
- Anthropic Claude API: https://docs.anthropic.com/

## Example Output

```
[PASS] MSFT - Technology stock with 1.8% debt ratio passes all gates
[FAIL] JPM - Banks sector fails Gate 1 (riba business model)
[FAIL] MO - Tobacco company with 93% haram revenue fails Gate 3
[PASS] KO - Consumer stock passes gates with Claude AI confirmation
```
