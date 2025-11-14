from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import pandas as pd
import numpy as np
from typing import List, Dict, Any


class NewsSentiment:
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()

    def score(self, text: str) -> float:
        if not text:
            return 0.0
        s = self.analyzer.polarity_scores(text)
        return s['compound']


def price_momentum(prices: pd.Series, window: int = 5) -> float:
    """Compute a normalized momentum score between -1 and 1 using percent change over window."""
    if prices.empty or len(prices) < 2:
        return 0.0
    returns = prices.pct_change().dropna()
    if returns.empty:
        return 0.0
    # use mean return over window
    recent = returns.tail(window)
    mean = recent.mean()
    # cap to reasonable bounds
    score = float(np.tanh(mean * 100))
    return score


class DecisionEngine:
    """Combine sentiment and momentum into a simple decision with confidence.

    Contract:
    - Inputs: list of news dicts [{'text':..., 'sentiment':...}], prices pd.Series (close)
    - Output: dict {decision: 'BUY'|'SELL'|'HOLD', confidence: 0..1, reason: str}
    """

    def __init__(self, news_weight: float = 0.6, momentum_weight: float = 0.4):
        self.news_weight = news_weight
        self.momentum_weight = momentum_weight
        self.sentiment = NewsSentiment()

    def decide(self, news_items: List[Dict[str, Any]], prices: pd.Series) -> Dict[str, Any]:
        # aggregate news sentiment (compound mean)
        sentiments = []
        for n in news_items:
            text = n.get('text') or n.get('summary') or n.get('title') or ''
            s = n.get('sentiment')
            if s is None:
                s = self.sentiment.score(text)
            sentiments.append(s)
        news_score = float(pd.Series(sentiments).mean()) if sentiments else 0.0

        mom = price_momentum(prices)

        combined = self.news_weight * news_score + self.momentum_weight * mom

        # map combined score to decision and confidence
        threshold_buy = 0.15
        threshold_sell = -0.15

        if combined >= threshold_buy:
            decision = 'BUY'
            confidence = min(1.0, (combined - threshold_buy) / (1.0 - threshold_buy))
        elif combined <= threshold_sell:
            decision = 'SELL'
            confidence = min(1.0, (threshold_sell - combined) / (1.0 - threshold_sell))
        else:
            decision = 'HOLD'
            confidence = 1.0 - (abs(combined) / threshold_buy) if threshold_buy != 0 else 0.0

        reason = f'combined={combined:.3f}, news={news_score:.3f}, momentum={mom:.3f}'
        return {'decision': decision, 'confidence': float(np.clip(confidence, 0.0, 1.0)), 'reason': reason}
