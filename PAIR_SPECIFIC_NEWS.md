# Pair-Specific Market News Scraper & Dashboard Update

## Overview

Your Forex scraper has been enhanced with **real-time, pair-specific market news scraping** and a **redesigned dashboard** with direct ForexFactory navigation. The system now:

✅ Scrapes news specific to each trading pair (EURUSD, GBPUSD, GOLDUSD, etc.)  
✅ Analyzes sentiment and probable market effects  
✅ Displays pair-specific news with impact assessment  
✅ Provides ForexFactory direct links in sidebar  
✅ Refreshes market news every 10 minutes  
✅ Stores historical analyses for correlation studies

---

## New Components

### 1. **Pair-Specific News Spider** (`forex_scraper/spiders/market_news.py`)

**What it does:**

- Scrapes news from ForexFactory market pages (e.g., `/market/goldusd`)
- Accepts a `pair` parameter to target specific currencies
- Extracts articles with metadata (title, summary, date, sentiment)
- Detects sentiment (BULLISH, BEARISH, NEUTRAL) using keyword matching
- Classifies impact level (HIGH, MEDIUM, LOW)

**Supported Pairs:**

```python
EURUSD, GBPUSD, USDJPY, GOLDUSD, AUDUSD, NZDUSD, USDCAD, USDCHF, CRUDE, NATGAS
```

**Usage:**

```bash
# Scrape Gold market news
scrapy crawl market_news -a pair=GOLDUSD

# Scrape EUR market news
scrapy crawl market_news -a pair=EURUSD

# Output saved to: data/market_news_goldusd.jsonl
```

**Output Format:**

```json
{
  "pair": "GOLDUSD",
  "title": "Fed Powell: Inflation Concerns Ease",
  "summary": "Federal Reserve Chair Powell indicated...",
  "sentiment": "BULLISH",
  "impact": "HIGH",
  "date": "2025-11-14 14:30",
  "timestamp": "2025-11-14T14:30:45.123456",
  "source": "ForexFactory Market",
  "url": "https://..."
}
```

---

### 2. **Market News Analyzer** (`forex_scraper/market_news_analyzer.py`)

**What it does:**

- Analyzes sentiment + impact to predict market effects
- Calculates probability of price UP/DOWN movement
- Determines expected volatility level
- Recommends BUY/SELL/HOLD based on news analysis
- Aggregates multiple articles for comprehensive outlook
- Persists historical analyses for pattern matching

**Key Methods:**

```python
# Analyze single article
analysis = analyzer.analyze_news_article(article)
# Returns: {pair, sentiment, impact, market_effect, prediction, recommendation}

# Batch analysis
aggregate = analyzer.analyze_batch(articles)
# Returns: sentiment_summary, probable_direction, avg_confidence, recommendation

# Get pair analysis (last 24 hours)
summary = analyzer.get_pair_analysis('GOLDUSD', hours=24)
# Returns: buy_signals, sell_signals, articles, avg_confidence
```

**Market Effect Predictions:**

```python
{
  'direction': 'UP',          # UP, DOWN, NEUTRAL, VOLATILE
  'volatility': 'high',       # low, medium, high, very_high, extreme
  'probability_up': 0.70,
  'probability_down': 0.30,
  'recommendation': 'BUY',
  'confidence': 0.75
}
```

---

### 3. **Enhanced Dashboard** (`dashboard.py`)

**New Features:**

✨ **Pair Selector (Sidebar)**

- Dropdown to select any available pair
- Default: GOLDUSD
- Updates all sections in real-time

✨ **ForexFactory Direct Links**

- Each pair links to its market page
- One-click navigation: `https://www.forexfactory.com/market/goldusd`

✨ **Pair-Specific News Section**

- Shows only news for selected pair
- Metrics: Total Articles, Bullish Count, Bearish Count, High Impact
- Displays top 5 market-moving articles with:
  - Sentiment indicator (🟢 BULLISH / 🔴 BEARISH / 🟡 NEUTRAL)
  - Impact badge (🔴 HIGH / 🟡 MEDIUM / ⚪ LOW)
  - Article summary (300 char preview)
  - Publication date

✨ **Pair Analysis Summary**

- Sentiment breakdown per pair
- BUY/SELL/HOLD recommendation
- Volatility assessment
- High-impact article count

✨ **Trading Signals**

- Shows all monitored pairs with ⭐ highlighting selected pair
- Color-coded signals and sentiment scores

✨ **Upcoming Events**

- Calendar filtered by selected impact + currency
- Economic events affecting all pairs

---

## Real-Time News Refresh Schedule

The scheduler (`scheduler.py`) now runs 4 background jobs:

| Task                     | Interval   | Details                             |
| ------------------------ | ---------- | ----------------------------------- |
| Economic Calendar        | 30 min     | Fetches latest events               |
| General News             | 15 min     | Reuters-style headlines             |
| **Market-Specific News** | **10 min** | **GOLDUSD, EURUSD, GBPUSD, USDJPY** |
| Prices                   | 5 min      | Latest OHLC data                    |

**Monitored Pairs for News Refresh:**

```python
['GOLDUSD', 'EURUSD', 'GBPUSD', 'USDJPY']
```

To add more pairs, edit `scheduler.py` line ~40:

```python
pairs_to_monitor = ['GOLDUSD', 'EURUSD', 'GBPUSD', 'USDJPY']
```

---

## How to Use

### 1. Start Production Mode (Dashboard + Scheduler)

```bash
cd d:\PythonProject\web_scraper
python start_app.py
```

This starts:

- ✅ Streamlit dashboard on `http://localhost:8501`
- ✅ Background scheduler (auto-refreshes all data)
- ✅ Market-specific news scraper (every 10 min for each pair)

### 2. Manual Market News Scrape

```bash
# Scrape single pair
scrapy crawl market_news -a pair=GOLDUSD -o data/market_news_goldusd.jsonl

# Or use the scheduler
python scheduler.py
```

### 3. View Dashboard

1. Open `http://localhost:8501`
2. Select pair from sidebar (e.g., "GOLDUSD")
3. Click market link: `https://www.forexfactory.com/market/goldusd`
4. See real-time news, sentiment, and market recommendations

### 4. Access Market Analysis Data

```python
from forex_scraper.market_news_analyzer import MarketNewsAnalyzer

analyzer = MarketNewsAnalyzer()
analysis = analyzer.get_pair_analysis('GOLDUSD', hours=24)
# Check: buy_signals, sell_signals, average_confidence, dominant_sentiment
```

---

## Sentiment & Impact Scoring

### Sentiment Detection (Keyword-Based)

**BULLISH** signals:

- "surge, rally, gain, rise, strong, positive, optimism, recovery, strength"

**BEARISH** signals:

- "crash, fall, decline, weak, negative, pressure, drop, weakness"

### Impact Scoring

**HIGH Impact** (triggered if ≥2 keywords):

- "fed, ecb, interest rate, fomc, gdp, inflation, emergency, major, breaking"

**MEDIUM Impact** (1+ keywords):

- "data, report, release, announcement, update"

---

## File Storage & History

**Data Files:**

- `data/market_news_goldusd.jsonl` - Gold market news (auto-refreshed)
- `data/market_news_eurusd.jsonl` - EUR market news (auto-refreshed)
- `data/news_analysis_history.json` - Historical analyses with predictions
- `logs/scheduler.log` - Background job logs

**Analysis History:**
Each analysis stored with timestamp for correlation studies:

```json
{
  "pair": "GOLDUSD",
  "sentiment": "BULLISH",
  "impact": "HIGH",
  "prediction": {
    "direction": "UP",
    "probability_up": 0.7,
    "recommendation": "BUY",
    "confidence": 0.75
  },
  "timestamp": "2025-11-14T14:35:00"
}
```

---

## Customization

### Add New Trading Pairs

**In `scheduler.py` (auto-refresh):**

```python
pairs_to_monitor = ['GOLDUSD', 'EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD']
```

**In `market_news.py` (spider URLs):**

```python
pair_urls = {
    'AUDUSD': 'https://www.forexfactory.com/market/audusd',
    'NZDUSD': 'https://www.forexfactory.com/market/nzdusd',
    # ...
}
```

### Adjust Sentiment Keywords

Edit `market_news.py` lines ~140-160:

```python
bullish_keywords = [
    'surge', 'rally', 'gain', 'rise', # Add more here
]
```

### Change Refresh Intervals

Edit `scheduler.py` lines ~60-90:

```python
IntervalTrigger(minutes=10)  # Change from 10 to 5, 15, 30, etc.
```

---

## Docker Deployment to Proxmox

The updated system includes:

- ✅ `Dockerfile` - Builds image with all new dependencies
- ✅ `docker-compose.yml` - Runs with volumes for data/logs
- ✅ `PROXMOX.md` - Step-by-step deployment guide

```bash
# Build image
docker compose build

# Run on Proxmox
docker compose up -d

# View logs
docker logs -f forex_dashboard
```

---

## Troubleshooting

### No news appearing?

1. Check `logs/scheduler.log` for errors
2. Manually run spider: `scrapy crawl market_news -a pair=GOLDUSD`
3. Ensure ForexFactory is accessible

### Sentiment not detecting correctly?

- Check article titles in `data/market_news_*.jsonl`
- Review keyword lists in `market_news_analyzer.py`
- Adjust thresholds if needed

### Dashboard not updating?

- Click "🔄 Refresh" button
- Check if scheduler is running: `Get-Process python`
- Restart with: `python start_app.py`

---

## Architecture Diagram

```
┌─────────────────────────────────────────┐
│      ForexFactory Market Pages          │
│  (e.g., /market/goldusd, /market/eurusd)│
└────────────────┬────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────┐
│    Market News Spider (Playwright)      │
│  (forex_scraper/spiders/market_news.py) │
│                                         │
│  • Scrape articles with sentiment       │
│  • Classify impact level                │
│  • Save to JSONL per pair               │
└────────────────┬────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────┐
│     Market News Analyzer                │
│  (forex_scraper/market_news_analyzer.py)│
│                                         │
│  • Predict market effects               │
│  • Calculate probability (UP/DOWN)      │
│  • Generate BUY/SELL/HOLD               │
│  • Store historical analyses            │
└────────────────┬────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────┐
│      Streamlit Dashboard                │
│         (dashboard.py)                  │
│                                         │
│  • Pair selector with FF links          │
│  • Sentiment breakdown                  │
│  • Trading recommendations              │
│  • Real-time metrics                    │
└─────────────────────────────────────────┘
                 ↑
                 │
         ┌───────┴───────┐
         │               │
    Scheduler       User Refresh
   (10 min)        (manual click)
```

---

## Summary

Your Forex scraper now has **production-ready pair-specific news analysis** with:

- 🎯 Real-time market news per pair (GOLDUSD, EURUSD, etc.)
- 📊 Sentiment + impact analysis
- 🔮 Market effect predictions
- 🚀 Automatic 10-minute refresh
- 📱 Interactive dashboard with pair navigation
- 🐳 Docker ready for Proxmox deployment

**Next Steps:**

1. Run: `python start_app.py`
2. Open: `http://localhost:8501`
3. Select pair from sidebar
4. View real-time news and recommendations
5. Deploy to Proxmox using Docker (see `PROXMOX.md`)
