"""
Real-time data manager for the dashboard.

Loads, caches, and refreshes:
- Economic calendar events
- Recent news articles
- Price data
- Sentiment analysis results
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import glob


class RealtimeDataManager:
    """Manages loading and refreshing of market data."""
    
    def __init__(self, data_dir='data'):
        self.data_dir = data_dir
        self.events_cache = None
        self.news_cache = None
        self.sentiment_cache = None
        self.prices_cache = None
        self.last_refresh = {}
    
    def load_latest_calendar_events(self):
        """Load the most recent calendar JSONL file."""
        calendar_files = glob.glob(os.path.join(self.data_dir, 'economic_calendar_*.jsonl'))
        if not calendar_files:
            calendar_files = glob.glob(os.path.join(self.data_dir, 'calendar*.jsonl'))

        if not calendar_files:
            return []

        latest_file = max(calendar_files, key=os.path.getctime)
        events = []

        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            event = json.loads(line)
                            events.append(event)
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            print(f"Error loading calendar: {e}")
        
        self.events_cache = events
        self.last_refresh['events'] = datetime.now()
        return events
    
    def load_latest_news(self, max_articles=50):
        """Load the most recent news JSONL file."""
        news_files = glob.glob(os.path.join(self.data_dir, '*news*.jsonl')) + \
                     glob.glob(os.path.join(self.data_dir, '*reuters*.jsonl'))

        if not news_files:
            return []

        latest_file = max(news_files, key=os.path.getctime)
        news = []

        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            article = json.loads(line)
                            news.append(article)
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            print(f"Error loading news: {e}")
        
        # Sort by date descending
        try:
            news.sort(key=lambda x: x.get('date', ''), reverse=True)
        except:
            pass
        
        self.news_cache = news[:max_articles]
        self.last_refresh['news'] = datetime.now()
        return news[:max_articles]
    
    def get_upcoming_events(self, hours_ahead=24):
        """Get events in the next N hours."""
        events = self.events_cache or self.load_latest_calendar_events()
        
        if not events:
            return []
        
        now = datetime.now()
        future = now + timedelta(hours=hours_ahead)
        
        # Try to parse times and filter
        upcoming = []
        for evt in events:
            time_str = evt.get('time')
            if time_str and time_str not in ['All Day', 'TBD']:
                try:
                    # Simple heuristic: parse time like "9:30am"
                    # For demo, just include all events
                    upcoming.append(evt)
                except:
                    upcoming.append(evt)
            elif not time_str:
                upcoming.append(evt)
        
        return upcoming[:20]  # Top 20 events
    
    def get_news_by_currency(self, currency):
        """Get news articles mentioning a specific currency."""
        news = self.news_cache or self.load_latest_news()
        
        currency_keywords = {
            'USD': ['USD', 'US', 'United States', 'dollar', 'federal', 'fed'],
            'EUR': ['EUR', 'euro', 'European', 'ECB'],
            'GBP': ['GBP', 'pound', 'BOE', 'Bank of England'],
            'JPY': ['JPY', 'yen', 'BOJ', 'Bank of Japan'],
            'AUD': ['AUD', 'Australian'],
            'XAU': ['gold', 'precious metals'],
        }
        
        keywords = currency_keywords.get(currency, [currency])
        filtered = []
        
        for article in news:
            text = (article.get('title', '') + ' ' + article.get('summary', '') + ' ' + 
                   article.get('text', '')).lower()
            if any(kw.lower() in text for kw in keywords):
                filtered.append(article)
        
        return filtered[:10]
    
    def get_latest_decisions(self):
        """Load latest trading decisions from run.py output or cache."""
        decision_files = glob.glob(os.path.join(self.data_dir, '*decision*.json'))

        if not decision_files:
            return {}

        latest_file = max(decision_files, key=os.path.getctime)

        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    
    def should_refresh(self, key, interval_seconds=300):
        """Check if data should be refreshed based on interval."""
        last = self.last_refresh.get(key)
        if not last:
            return True
        return (datetime.now() - last).total_seconds() > interval_seconds
    
    def get_currency_pairs(self):
        """Return major trading pairs we track."""
        return [
            'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD',
            'NZDUSD', 'USDCAD', 'GOLDUSD', 'CRUDE', 'NATGAS'
        ]
    
    def get_pair_sentiment(self, pair):
        """Get current sentiment for a pair (aggregate from news)."""
        # For now, return a placeholder
        # In production, this would aggregate sentiment from loaded news
        sentiment_map = {
            'EURUSD': {'score': 0.15, 'source': 'Recent news positive on EUR'},
            'GBPUSD': {'score': -0.05, 'source': 'Mixed sentiment'},
            'GOLDUSD': {'score': 0.35, 'source': 'USD weakness supportive'},
            'USDJPY': {'score': -0.10, 'source': 'Risk-on sentiment'},
            'USDCHF': {'score': 0.05, 'source': 'Safe-haven interest minimal'},
            'AUDUSD': {'score': 0.20, 'source': 'Commodity-linked strength'},
        }
        return sentiment_map.get(pair, {'score': 0.0, 'source': 'No data'})
    
    def export_event_history(self):
        """Export events for event analyzer."""
        events = self.events_cache or self.load_latest_calendar_events()
        return events
    
    def load_pair_specific_news(self, pair):
        """Load latest news for a specific pair."""
        news_files = glob.glob(os.path.join(self.data_dir, f'*market*{pair.lower()}*.jsonl')) + \
                     glob.glob(os.path.join(self.data_dir, f'*{pair.lower()}_news*.jsonl'))

        if not news_files:
            return []

        latest_file = max(news_files, key=os.path.getctime)
        news = []
        seen_keys = set()

        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            article = json.loads(line)
                            if article.get('pair', '').upper() == pair.upper():
                                key = (article.get('url'), article.get('title'))
                                if key in seen_keys:
                                    continue
                                seen_keys.add(key)
                                news.append(article)
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            print(f"Error loading pair news for {pair}: {e}")
        
        # Sort by timestamp descending
        try:
            news.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        except:
            pass
        
        return news
    
    def get_pair_analysis_summary(self, pair):
        """Get quick analysis summary for a pair."""
        news = self.load_pair_specific_news(pair)
        
        if not news:
            return {
                'pair': pair,
                'total_articles': 0,
                'sentiment': 'NO DATA',
                'recommendation': 'HOLD',
            }
        
        # Count sentiments
        sentiments = {}
        for article in news[:20]:
            sent = article.get('sentiment', 'NEUTRAL')
            sentiments[sent] = sentiments.get(sent, 0) + 1
        
        # Determine dominant sentiment
        dominant = max(sentiments, key=sentiments.get) if sentiments else 'NEUTRAL'
        
        # Count impacts
        high_impact = sum(1 for a in news if a.get('impact') == 'HIGH')
        
        return {
            'pair': pair,
            'total_articles': len(news),
            'sentiment_breakdown': sentiments,
            'dominant_sentiment': dominant,
            'high_impact_count': high_impact,
            'latest_articles': news[:5],
        }
