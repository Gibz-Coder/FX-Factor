"""Orchestrator to fetch market data, load recent news JSON, and produce a decision for given pairs."""
import argparse
import json
from forex_scraper.fetcher import MarketDataFetcher
from forex_scraper.analyzer import DecisionEngine
import pandas as pd
import os


def load_recent_news(path='data'):
    # find latest news file in data/
    if not os.path.isdir(path):
        return []
    files = [os.path.join(path, f) for f in os.listdir(path) if f.startswith('reuters_news') and f.endswith('.jsonl')]
    if not files:
        return []
    files.sort()
    latest = files[-1]
    items = []
    with open(latest, 'r', encoding='utf-8') as fh:
        for line in fh:
            try:
                items.append(json.loads(line))
            except Exception:
                continue
    return items


def main(args):
    pairs = [p.strip().upper() for p in args.pairs.split(',')]
    fetcher = MarketDataFetcher()
    engine = DecisionEngine()

    news_items = load_recent_news()

    for pair in pairs:
        try:
            df = fetcher.get_recent_prices(pair)
            prices = df['close'] if 'close' in df.columns else df.iloc[:, 0]
        except Exception as e:
            print(f'Could not fetch prices for {pair}: {e}')
            prices = pd.Series([])

        decision = engine.decide(news_items, prices)
        print(f'Pair {pair}: {decision["decision"]} (conf={decision["confidence"]:.2f}) -- {decision["reason"]}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--pairs', default='EURUSD,GBPUSD,GOLDUSD', help='Comma-separated pairs to analyze')
    args = parser.parse_args()
    main(args)
