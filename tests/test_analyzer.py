import pandas as pd
from forex_scraper.analyzer import price_momentum, DecisionEngine


def test_price_momentum_positive():
    s = pd.Series([1.0, 1.01, 1.02, 1.03, 1.04], index=pd.date_range('2025-01-01', periods=5))
    m = price_momentum(s, window=3)
    assert m > 0


def test_price_momentum_empty():
    s = pd.Series([], dtype=float)
    m = price_momentum(s)
    assert m == 0.0


def test_decision_engine_buy():
    # news strongly positive and momentum positive -> BUY
    engine = DecisionEngine(news_weight=0.7, momentum_weight=0.3)
    news = [{'text': 'Economy strong growth, positive data'}, {'text': 'Central bank hints at hawkish stance'}]
    prices = pd.Series([1.0, 1.02, 1.03, 1.04, 1.05], index=pd.date_range('2025-01-01', periods=5))
    res = engine.decide(news, prices)
    assert res['decision'] in ('BUY', 'HOLD')
