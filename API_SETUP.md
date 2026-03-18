# API Setup Guide - Halal Asymmetric Stock Finder

## Overview
This application requires **two free API keys**, plus one library (yfinance) that needs no setup.

- **FMP_API_KEY** - Financial Modeling Prep (free tier, 250 calls/day)
- **ANTHROPIC_API_KEY** - Claude AI (pay-as-you-go, ~$0.50/month at 2x/week usage)
- **yfinance** - No API key required, built into Python

---

## Step 1: Get FMP API Key (Free Tier)

### Registration
1. Go to **https://financialmodelingprep.com/register**
2. Click "Sign up" and complete the registration form
   - Email: Use any email address
   - Password: Choose a secure password
   - No credit card required

### Get Your API Key
1. Log in to https://financialmodelingprep.com
2. Go to **Dashboard** or **Account Settings**
3. Look for **"API Key"** section (usually in the left sidebar or top menu)
4. Copy your **API key** (it's a long alphanumeric string like: `abc123defg456hij789`)

### Verify Your Key Works
Your free tier includes:
- **250 API calls per day**
- Access to stock screener, company profiles, insider transactions, revenue segments
- Perfect for 2x/week usage (each discovery run uses ~20-30 calls)

Save this key - you'll add it to `.env` in **Step 3**.

---

## Step 2: Get Anthropic API Key (Pay-As-You-Go)

### Registration
1. Go to **https://console.anthropic.com**
2. Click **"Sign up"** at the top right
3. Complete registration with:
   - Email address
   - Password
   - Phone number (for verification)

### Add Payment Method
1. After registration, go to **Billing** (left sidebar)
2. Click **"Add Payment Method"**
3. Enter your credit card details
   - No charges until you actually use the API
   - You'll only be charged for tokens consumed (~$0.50/month at 2x/week usage)

### Get Your API Key
1. Go to **API Keys** section (left sidebar or top menu)
2. Click **"Create Key"**
3. Give it a name like `halal-stock-finder`
4. Copy the key immediately (you can only see it once)
   - It looks like: `sk-ant-v1-abc123...`

### Optional: Set Usage Limits
1. In **Billing**, click **"Usage Limits"**
2. Set a monthly limit (e.g., $10) to prevent surprises
3. This is optional but recommended for safety

Save this key - you'll add it to `.env` in **Step 3**.

---

## Step 3: Configure Your .env File

### 1. Open your `.env` file
In the project folder, you should find `.env`. Open it in any text editor.

### 2. Replace placeholder values with your actual keys

**BEFORE:**
```
FMP_API_KEY=your_fmp_free_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
```

**AFTER (example with fake keys):**
```
FMP_API_KEY=abc123defg456hij789klmno
ANTHROPIC_API_KEY=sk-ant-v1-abcd1234efgh5678ijkl9012mnopqrst
```

### 3. Save the file
- **Important:** Do NOT commit `.env` to git (it's in `.gitignore` for security)
- Never share your `.env` file or upload it to GitHub

---

## Step 4: Install Python Dependencies

### 1. Open terminal/command prompt
Navigate to your project folder:
```bash
cd c:\Users\qurra\OneDrive\Desktop\Code\Assymetric_Stock_Finder
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

This installs:
- `anthropic` - Claude AI library
- `requests` - HTTP requests for FMP API
- `python-dotenv` - Load .env variables
- `yfinance` - Yahoo Finance data (no API key needed)
- `streamlit` - Web UI (for later)

---

## Step 5: Test Your Setup

### 1. Test yfinance (no API key needed)
```bash
python -c "import yfinance as yf; print(yf.Ticker('MSFT').info['sector'])"
```
**Expected output:** `Technology` (if working correctly)

### 2. Test FMP API
```bash
python -c "import requests, os; from dotenv import load_dotenv; load_dotenv(); key = os.getenv('FMP_API_KEY'); r = requests.get(f'https://financialmodelingprep.com/api/v3/quote/MSFT?apikey={key}'); print(f'Status: {r.status_code}')"
```
**Expected output:** `Status: 200` (if API key is valid)

### 3. Test Anthropic API
```bash
python -c "from anthropic import Anthropic; print('Anthropic client initialized successfully')"
```
**Expected output:** `Anthropic client initialized successfully`

---

## Step 6: Run Fetcher Test

```bash
python fetcher.py
```

This will:
1. Test fetching income statement, balance sheet, cashflow for MSFT
2. Fetch quote info and price history
3. Fetch FMP data (profile, insider transactions, segments)
4. Output everything as JSON
5. Cache results for future runs

**Expected:** Full JSON output with MSFT financial data (will take 30-60 seconds)

---

## Troubleshooting

### "FMP_API_KEY not found in environment"
- **Cause:** .env file not being read
- **Fix:** Make sure `.env` file is in the project root folder, not in a subfolder

### "API key invalid" or "401 Unauthorized"
- **Cause:** Incorrect API key in .env
- **Fix:** Copy your FMP API key again from the FMP dashboard (it's case-sensitive)

### "Rate limit exceeded" (429 error)
- **Cause:** You've made more than 250 FMP API calls today
- **Fix:** Wait until tomorrow (limit resets daily). The app will auto-retry.

### "Connection timeout"
- **Cause:** Internet connection issue or FMP/Anthropic servers temporarily down
- **Fix:** Wait 30 seconds and try again. Check your internet connection.

### "yfinance data not returning"
- **Cause:** Yahoo Finance site temporarily down or changed
- **Fix:** Wait a few hours. yfinance is unofficial - Yahoo occasionally breaks it. Community usually fixes within days.

---

## Cost Summary

| Service       | Cost              | Details                                                |
|---------------|-------------------|--------------------------------------------------------|
| **FMP (Free)** | $0                | 250 calls/day. Sufficient for 2x/week discovery runs   |
| **Anthropic**  | ~$0.30-0.60/month | Claude API at 2x/week usage                            |
| **yfinance**   | $0                | No API key, no cost, unlimited calls                   |
| **Total**      | ~$0.50/month      | Essentially free for personal use                      |

---

## Next Steps

1. ✅ Get FMP API key
2. ✅ Get Anthropic API key
3. ✅ Configure .env file
4. ✅ Install dependencies
5. ✅ Run fetcher.py test
6. → Ready to build the rest of the application!

Questions? Check the main specification document or the project README.md.
