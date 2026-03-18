# PythonAnywhere Setup Guide - Biweekly Automation

Complete step-by-step guide to setting up automated stock discovery on PythonAnywhere with biweekly runs and email notifications.

---

## Prerequisites

- Active PythonAnywhere subscription (you already have this)
- Gmail account (required for email notifications)
- API keys: FMP_API_KEY and ANTHROPIC_API_KEY (optional)

---

## ⚡ Quick Summary

1. Get Gmail app password
2. Update .env with email credentials
3. Upload files to PythonAnywhere
4. Install Python packages
5. Set up biweekly scheduler (every 14 days)
6. Test it works
7. Verify task is running

**Total time:** 20-30 minutes

---

## Step 1️⃣: Get Gmail App Password

Email notifications require a special app password. Here's how:

1. Go to [myaccount.google.com](https://myaccount.google.com)
2. Click **Security** (left sidebar)
3. Turn on **2-Step Verification** (if not already enabled)
4. Return to Security page
5. Click **App passwords**
6. Select:
   - Phone type: **Windows PC**
   - App: **Mail**
7. Google generates a **16-character password**
8. Save this password - you'll use it in Step 2

**Example App Password:** `abcd efgh ijkl mnop` (with spaces)

---

## Step 2️⃣: Update .env File with All API Keys and Email Configuration

Edit your `.env` file with all three configurations:

```
# FMP API Key (from https://financialmodelingprep.com)
FMP_API_KEY=VV9l95pSH8OEgulyriv1wYl3Eu4gir97

# Anthropic Claude API Key (from https://console.anthropic.com)
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxxxxx

# Email configuration (for biweekly discovery notifications)
EMAIL_USER=your_gmail@gmail.com
EMAIL_PASSWORD=abcd efgh ijkl mnop
RECIPIENT_EMAIL=where_emails_go@gmail.com
```

**How to fill in:**
1. `FMP_API_KEY` = Your FMP API key (already provided)
2. `ANTHROPIC_API_KEY` = Your Claude API key (already provided)
3. `EMAIL_USER` = Your Gmail address (e.g., `john@gmail.com`)
4. `EMAIL_PASSWORD` = 16-character app password from Step 1
5. `RECIPIENT_EMAIL` = Where to send discovery results (can be same as EMAIL_USER)

---

## Step 3️⃣: Prepare Files for Upload

You need these **9 files** ready to upload:

```
✓ fetcher.py
✓ halal.py
✓ tracker.py
✓ scorer.py
✓ detector.py
✓ validation.py
✓ discovery.py
✓ scheduled_discovery.py
✓ .env (with email config from Step 2)
```

All files are in: `c:\Users\qurra\OneDrive\Desktop\Code\Assymetric_Stock_Finder\`

---

## Step 4️⃣: Upload to PythonAnywhere

1. Go to [pythonanywhere.com](https://pythonanywhere.com) → Login
2. Click **Files** (top menu)
3. You're in `/home/your_username/` directory
4. Click **New folder** → Name it: `halal_stock_finder`
5. Double-click the new folder to enter it
6. **Upload all 9 files** into this folder

**Final structure should look like:**
```
/home/your_username/halal_stock_finder/
├── fetcher.py
├── halal.py
├── tracker.py
├── scorer.py
├── detector.py
├── validation.py
├── discovery.py
├── scheduled_discovery.py
└── .env
```

---

## Step 5️⃣: Install Python Packages

1. Click **Bash console** (top menu in PythonAnywhere)
2. Run these commands **one at a time**:

```bash
cd /home/your_username/halal_stock_finder
```

```bash
python3 -m venv venv
```

```bash
source venv/bin/activate
```

```bash
pip install yfinance requests python-dotenv anthropic pandas plotly
```

**Verify installation** (should show no errors):
```bash
python3 -c "import yfinance; print('✓ Setup Complete')"
```

---

## Step 6️⃣: Set Up Biweekly Scheduler

**Important:** PythonAnywhere only offers **daily** and **hourly** scheduled tasks, NOT biweekly. The solution is to create a **daily task** that only runs on fixed biweekly dates (15th and 28th).

1. Click **Tasks** (top menu in PythonAnywhere)
2. Click **Create a new scheduled task**
3. Fill in the form with these exact fields *(see screenshot below for reference)*:

   **Line 1 - Frequency dropdown:** Select **"Daily"**
   
   **Line 2 - Time (HH:MM):** Enter **09:00** (9 AM UTC)
   
   **Line 3 - Command:** Copy-paste exactly:
   ```
   /home/your_username/halal_stock_finder/venv/bin/python3 /home/your_username/halal_stock_finder/scheduled_discovery.py
   ```
   
   **Line 4 - Optional description:**
   ```
   Halal Stock Finder Biweekly Discovery (runs on 15th and 28th)
   ```

4. Click **Create** ✓

**How the Biweekly Logic Works:**
The `scheduled_discovery.py` script has built-in logic that checks the date and only runs discovery on **fixed dates each month**:
- **15th of every month** (mid-month check)
- **28th of every month** (end-month check)

Other days, it logs: "Not a scheduled discovery day (today is day X/month Y) - skipping"

**Why fixed dates?**
- Predictable: You always know when discovery runs
- Consistent: Same dates every month without variation
- Easy to track: Just remember 15th and 28th

---

## Step 7️⃣: Test It Works (IMPORTANT!)

1. Go to **Bash console**
2. Run these commands:

```bash
cd /home/your_username/halal_stock_finder
source venv/bin/activate
python3 scheduled_discovery.py
```

**Expected output:**
```
============================================================
🚀 Starting scheduled discovery run
Time: 2026-03-15 09:00:00
============================================================

✓ Discovery completed: 10 candidates found
✓ Email sent to your_email@gmail.com
✓ Scheduled discovery completed successfully
```

**Check your email** - You should receive a result email with:
- Top 5 candidates with scores
- Pattern types (Full/Partial/None)
- Track classification
- Signal scores
- Halal status

**If no email:** Check email credentials in .env file

---

## Step 8️⃣: Verify Task Is Running

1. Go to **Tasks** page
2. Find your scheduled task in the list
3. Check status - should show:
   - **Status:** Enabled ✓ (toggle switch ON)
   - **Last run:** X minutes ago (after you tested)
   - **Next run:** In X days

✅ You're done! The scheduler will run automatically every 14 days at 9:00 AM.

---

## 📊 What Happens Every 14 Days

The scheduler automatically:
1. Runs complete stock discovery pipeline
2. Validates 15 candidates against halal gates
3. Scores signals and detects asymmetric patterns
4. Saves results to database
5. Generates summary email
6. Sends email to RECIPIENT_EMAIL

**No manual work needed!**

---

## 📧 Email Format

You'll receive an email with:

```
Subject: 🏆 Halal Stock Finder - Biweekly Update (2026-03-29)

Contents:
- Top 5 Opportunities table
  - Rank | Ticker | Score | Pattern | Track | Signals | Halal Status
- Summary statistics
  - Total candidates, full/partial asymmetric counts
- Timestamp of run date
```

---

## � About discovery_checkpoint.db

You may see a `discovery_checkpoint.db` file created on PythonAnywhere after the first run. **This file is important and needs to be synced back to your local repo.**

**What it does:**
- Stores validation results from each discovery run on the cloud
- Prevents re-validating the same tickers if the task restarts
- Speeds up subsequent biweekly runs by caching previous analyses

**What to do with it:**
1. After each discovery run (15th and 28th), **download** `discovery_checkpoint.db` from PythonAnywhere
2. Replace the one in your local repo at: `c:\Users\qurra\OneDrive\Desktop\Code\Assymetric_Stock_Finder\discovery_checkpoint.db`
3. This keeps your local and cloud databases in sync
4. Next time you run discovery locally (testing or updates), it will have the cloud's cache

**How to download from PythonAnywhere:**
1. Go to **Files** (top menu)
2. Navigate to `/home/your_username/halal_stock_finder/`
3. Click on `discovery_checkpoint.db` 
4. Choose **Download** button
5. Save it to your local repo folder

---

## 🔄 Quarterly Universe Updates (Manual Step)

**Every 3 months (quarterly), you should update the universe of stocks.**

Why? Markets change, some stocks graduate to non-halal status, new opportunities emerge.

### How to Update Quarterly:

1. **On your local machine**, edit `screener.py`:
   - Open: `c:\Users\qurra\OneDrive\Desktop\Code\Assymetric_Stock_Finder\screener.py`
   - Find the `SAMPLE_UNIVERSE` list (around line 30)
   - Update the list with 50+ stocks you want to screen
   - Example:
     ```python
     SAMPLE_UNIVERSE = [
         'INTA', 'CRUS', 'ACIW', 'GTLB',  # Keep top performers
         'NEW1', 'NEW2', 'NEW3',            # Add new candidates
         # Remove stocks that no longer fit criteria
     ]
     ```

2. **Test locally:**
   ```bash
   python screener.py  # Make sure new stocks work
   ```

3. **Upload updated `screener.py` to PythonAnywhere:**
   - Go to Files on PythonAnywhere
   - Navigate to `/home/your_username/halal_stock_finder/`
   - Delete old `screener.py`
   - Upload new `screener.py`

4. **Scheduler will automatically use the new list** on the next discovery run

**Timing:** 
- Month 1 (Jan): Initial setup
- Month 4 (Apr): First quarterly update
- Month 7 (Jul): Second quarterly update  
- Month 10 (Oct): Third quarterly update

---

## �🔍 Monitor Task Execution

### View Task Logs
```bash
cd /home/your_username/halal_stock_finder
tail -f scheduled_discovery.log
```

### Check Task Status
1. Go to **Tasks** page
2. Click on your scheduled task
3. View execution details and any errors

### Download Latest Results
1. Go to **Files**
2. Navigate to `halal_stock_finder` folder
3. Download `discovery_checkpoint.db`
4. This contains all validation data from last run

---

## ❓ Troubleshooting

### Issue: "Email not sending"
**Solution:**
- Verify Gmail 2FA is enabled
- Verify app password is exactly 16 characters (with spaces)
- Check EMAIL_USER and RECIPIENT_EMAIL are valid
- Test manually: `python3 scheduled_discovery.py`

### Issue: "Task not running"
**Solution:**
- Check task is **enabled** (toggle switch ON)
- Verify command path is exactly correct
- Check that .venv folder exists with Python packages
- Run test manually to see error

### Issue: "Python module not found"
**Solution:**
```bash
source venv/bin/activate
pip install --upgrade yfinance requests python-dotenv anthropic pandas plotly
```

### Issue: "FMP API errors"
**Solution:**
- FMP has 250 calls/day limit on free tier
- Check FMP_API_KEY is valid
- If limit exceeded, wait until next day
- yfinance works as fallback (always free)

### Issue: "No results in email"
**Solution:**
- Check discovery completed successfully
- Check RECIPIENT_EMAIL in .env
- Check spam folder for email
- Run test manually to debug: `python3 scheduled_discovery.py`

---

## 🎯 Advanced Options

### Change Frequency (Not Biweekly)

**For weekly (every 7 days):**
- Edit task
- Change frequency: Every N days = **7**

**For monthly (every 30 days):**
- Edit task
- Change frequency: Every N days = **30**

**For daily (every 1 day):**
- Edit task
- Change frequency: Every N days = **1**

### Change Start Time

If 9:00 AM doesn't work for you:
- Edit task
- Change **Start Time** to preferred hour (e.g., 6:00 AM, 3:00 PM)
- Must be 24-hour format (09:00, 15:00, etc.)

### Multiple Email Recipients

Modify scheduled_discovery.py line where EMAIL is sent to add multiple recipients:
```python
'to_email': os.environ.get('RECIPIENT_EMAIL').split(',')
```

Then in .env:
```
RECIPIENT_EMAIL=email1@gmail.com,email2@gmail.com,email3@gmail.com
```

---

## 📚 Related Files

- **APP_USAGE.md** - How to use the Streamlit dashboard
- **QUICKSTART.md** - Initial local setup
- **API_SETUP.md** - Getting API keys
- **PROJECT_COMPLETION.md** - Full system docs

---

## ✅ Checklist

- [ ] Created Gmail app password
- [ ] Updated .env with email config
- [ ] Uploaded all 9 files to PythonAnywhere
- [ ] Installed Python packages with pip
- [ ] Created scheduled task (every 14 days)
- [ ] Tested with manual run
- [ ] Received test email successfully
- [ ] Task shows as enabled in Tasks page
- [ ] Set to run every 14 days starting at 9:00 AM

**Once all checked:** You're ready! System will run automatically. ✅

---

**Need help?** Check the logs in Bash console or review the troubleshooting section above.

Happy automating! 🚀

