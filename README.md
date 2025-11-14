# Forex Market & News Scraper (Scrapy + Analysis)

Prototype project that scrapes market news and economic events, fetches market price data, computes simple sentiment and momentum signals, and outputs a high-probability trade decision (BUY/SELL/HOLD) with a confidence score.

Overview

- Scrapy spiders collect news headlines and economic calendar events.
- A market data fetcher obtains recent price data (Alpha Vantage recommended).
- Analyzer computes sentiment (VADER) and price momentum and combines them into a probability decision.

Quick start

1. Create and activate a Python virtual environment (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Set API keys (optional but recommended for market data and news API):

```powershell
$env:ALPHAVANTAGE_API_KEY = 'your_alpha_vantage_key'
$env:NEWSAPI_KEY = 'your_newsapi_key'   # optional
```

3. Run the news spider to collect articles (example):

```powershell
scrapy crawl reuters_news -o data/news.json
```

4. Run analysis for pairs (example):

```powershell
python run.py --pairs EURUSD,GBPUSD,GOLDUSD
```

Notes

- This is a prototype. Adjust spiders and rules to match target sites and more advanced models.
- If you don't have Alpha Vantage key, follow fallback instructions in `forex_scraper/fetcher.py`.

Files of interest

- `forex_scraper/spiders/reuters_news.py` - example news spider
- `forex_scraper/spiders/economic_calendar.py` - example calendar spider
- `forex_scraper/fetcher.py` - market data fetcher (Alpha Vantage + fallback)
- `forex_scraper/analyzer.py` - sentiment + momentum + decision logic
- `run.py` - orchestrator script
