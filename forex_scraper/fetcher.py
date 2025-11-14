"""Market data fetcher with Alpha Vantage (preferred) and a lightweight fallback.

This module provides MarketDataFetcher.get_latest_prices(pair, outputsize='compact')
which returns a pandas.DataFrame indexed by datetime with 'close' prices.

Pairs are expected in format 'EURUSD', 'GBPUSD', 'GOLDUSD' (gold). For GOLDUSD Alpha Vantage may
require different handling; the code will try a currency exchange endpoint and raise a helpful error
if an API key is missing.
"""
from typing import Optional
import os
import requests
import pandas as pd
import time


class MarketDataFetcher:
    def __init__(self, alpha_vantage_key: Optional[str] = None):
        self.av_key = alpha_vantage_key or os.environ.get('ALPHAVANTAGE_API_KEY')

    def _alpha_vantage_fx_daily(self, from_symbol: str, to_symbol: str, outputsize='compact'):
        url = 'https://www.alphavantage.co/query'
        params = {
            'function': 'FX_DAILY',
            'from_symbol': from_symbol,
            'to_symbol': to_symbol,
            'outputsize': outputsize,
            'apikey': self.av_key,
            'datatype': 'json'
        }
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        j = r.json()
        if 'Time Series FX (Daily)' not in j:
            raise RuntimeError('Alpha Vantage response missing expected data: ' + str(j))
        ts = j['Time Series FX (Daily)']
        records = []
        for dt, vals in ts.items():
            records.append({'date': pd.to_datetime(dt), 'close': float(vals['4. close'])})
        df = pd.DataFrame(records).set_index('date').sort_index()
        return df

    def _fallback_exchangerate(self, base: str, quote: str):
        # exchangerate.host provides free rates but only latest; we return only latest as fallback
        url = f'https://api.exchangerate.host/latest'
        params = {'base': base, 'symbols': quote}
        r = requests.get(url, params=params, timeout=20)
        r.raise_for_status()
        j = r.json()
        if 'rates' not in j or quote not in j['rates']:
            raise RuntimeError('Fallback rates not available')
        price = float(j['rates'][quote])
        df = pd.DataFrame([{'date': pd.Timestamp.utcnow(), 'close': price}]).set_index('date')
        return df

    def get_recent_prices(self, pair: str, outputsize='compact') -> pd.DataFrame:
        """Return recent prices DataFrame for pair like 'EURUSD' or 'GBPUSD' or 'GOLDUSD'.

        Raises RuntimeError with instructions if API key missing.
        """
        pair = pair.upper()
        # split into base/quote - GOLDUSD special-case
        if pair == 'GOLDUSD':
            # AlphaVantage does not have FX_DAILY for XAU/USD in all accounts; user should provide
            # an alternative data source or use paid metals API. Try AV currency exchange rate first.
            if not self.av_key:
                raise RuntimeError('Fetching GOLDUSD requires ALPHAVANTAGE_API_KEY set or a metals API. Set env var ALPHAVANTAGE_API_KEY and retry.')
            # AV may support symbol pair 'XAU' / 'USD' via FX_DAILY — try it
            return self._alpha_vantage_fx_daily('XAU', 'USD', outputsize=outputsize)

        base = pair[:3]
        quote = pair[3:6]

        if self.av_key:
            try:
                return self._alpha_vantage_fx_daily(base, quote, outputsize=outputsize)
            except Exception as e:
                # brief backoff and fallback
                time.sleep(1)
                try:
                    return self._fallback_exchangerate(base, quote)
                except Exception:
                    raise
        else:
            # fallback to exchangerate.host for latest rate
            return self._fallback_exchangerate(base, quote)
