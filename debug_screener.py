import yfinance as yf

# Test a few stocks to see their exchange values
test_tickers = ['DDOG', 'OKTA', 'ZM', 'CRWD', 'PSTG', 'SQ']
for ticker in test_tickers:
    try:
        info = yf.Ticker(ticker).info
        exchange = info.get("exchange")
        market_cap = info.get("marketCap")
        print(f"{ticker}: exchange='{exchange}' ({type(exchange).__name__}), market_cap={market_cap}")
    except Exception as e:
        print(f"{ticker}: ERROR - {e}")
