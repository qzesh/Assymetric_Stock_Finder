import yfinance as yf

# These stocks pass market cap, exchange, and revenue growth filters
# Let's see their debt/equity values
test_stocks = ['NSTG', 'AKAM', 'JKHY', 'BOOM', 'SANA', 'INTA', 'FTNT', 'CRUS']

for ticker in test_stocks:
    try:
        info = yf.Ticker(ticker).info
        de = info.get('debtToEquity')
        mc = info.get('marketCap')
        rg = info.get('revenueGrowth')
        mc_str = f"${mc/1e9:.1f}B" if mc else "None"
        print(f"{ticker}: DE={de}, MC={mc_str}, RGrowth={rg}")
    except Exception as e:
        print(f"{ticker}: ERROR {e}")
