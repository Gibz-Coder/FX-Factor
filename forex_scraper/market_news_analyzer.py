"""
Market Outcome Analyzer for News

Analyzes news articles for currency pairs and predicts probable market effects:
- Sentiment analysis (VADER + keywords)
- Impact assessment
- Price direction probability
- Volatility forecasting
- Confidence scoring
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter
import re


class MarketNewsAnalyzer:
    """Analyze news and predict market outcomes."""
    
    def __init__(self, history_file='data/news_analysis_history.json'):
        self.history_file = Path(history_file)
        self.history = self.load_history()
        
        # Impact multipliers
        self.impact_multipliers = {
            'HIGH': 1.5,
            'MEDIUM': 1.0,
            'LOW': 0.5,
        }
        
        # Sentiment to direction mapping
        self.sentiment_map = {
            'BULLISH': {'direction': 'UP', 'base_prob': 0.70},
            'BEARISH': {'direction': 'DOWN', 'base_prob': 0.70},
            'NEUTRAL': {'direction': 'NEUTRAL', 'base_prob': 0.50},
        }
    
    def analyze_news_article(self, article):
        """Analyze a single news article."""
        try:
            pair = article.get('pair', 'UNKNOWN')
            title = article.get('title', '')
            summary = article.get('summary', '')
            sentiment = article.get('sentiment', 'NEUTRAL')
            impact = article.get('impact', 'LOW')
            
            # Calculate market effect
            effect = self.calculate_market_effect(title, summary, sentiment, impact)
            
            # Predict price movement
            prediction = self.predict_price_movement(pair, sentiment, impact, effect)
            
            # Add to history
            analysis = {
                'pair': pair,
                'title': title,
                'sentiment': sentiment,
                'impact': impact,
                'market_effect': effect,
                'prediction': prediction,
                'timestamp': datetime.now().isoformat(),
                'url': article.get('url', ''),
            }
            
            self.history.append(analysis)
            self.save_history()
            
            return analysis
        
        except Exception as e:
            print(f"Error analyzing article: {e}")
            return None
    
    def calculate_market_effect(self, title, summary, sentiment, impact):
        """Calculate the expected market effect."""
        text = (title + ' ' + summary).lower()
        
        # Economic indicators and their typical effects
        indicator_effects = {
            'strong': {'direction': 'UP', 'volatility': 'high'},
            'weak': {'direction': 'DOWN', 'volatility': 'high'},
            'better than expected': {'direction': 'UP', 'volatility': 'very_high'},
            'worse than expected': {'direction': 'DOWN', 'volatility': 'very_high'},
            'beats': {'direction': 'UP', 'volatility': 'high'},
            'misses': {'direction': 'DOWN', 'volatility': 'high'},
            'rate hike': {'direction': 'UP', 'volatility': 'very_high'},
            'rate cut': {'direction': 'DOWN', 'volatility': 'very_high'},
            'crisis': {'direction': 'VOLATILE', 'volatility': 'extreme'},
            'crisis lifted': {'direction': 'UP', 'volatility': 'very_high'},
        }
        
        detected_effect = None
        for indicator, effect in indicator_effects.items():
            if indicator in text:
                detected_effect = effect
                break
        
        if not detected_effect:
            detected_effect = {
                'direction': sentiment,
                'volatility': 'medium' if impact == 'HIGH' else ('low' if impact == 'LOW' else 'medium')
            }
        
        return detected_effect
    
    def predict_price_movement(self, pair, sentiment, impact, market_effect):
        """Predict probable price movement based on news."""
        
        # Base probability from sentiment
        sentiment_info = self.sentiment_map.get(sentiment, {'direction': 'NEUTRAL', 'base_prob': 0.50})
        base_prob = sentiment_info['base_prob']
        
        # Adjust for impact level
        impact_mult = self.impact_multipliers.get(impact, 1.0)
        adjusted_prob = min(0.95, base_prob * impact_mult)
        
        # Calculate volatility
        volatility_map = {
            'low': 0.5,
            'medium': 1.0,
            'high': 1.5,
            'very_high': 2.0,
            'extreme': 3.0,
        }
        volatility_multiplier = volatility_map.get(market_effect.get('volatility', 'medium'), 1.0)
        expected_volatility = 'high' if volatility_multiplier > 1.5 else ('medium' if volatility_multiplier > 0.8 else 'low')
        
        # Direction
        direction = market_effect.get('direction', sentiment)
        if direction not in ['UP', 'DOWN', 'NEUTRAL', 'VOLATILE']:
            direction = 'NEUTRAL'
        
        # Recommendation
        if adjusted_prob > 0.65 and direction in ['UP', 'DOWN']:
            recommendation = 'BUY' if direction == 'UP' else 'SELL'
            confidence = adjusted_prob
        else:
            recommendation = 'HOLD'
            confidence = adjusted_prob
        
        prediction = {
            'pair': pair,
            'direction': direction,
            'probability_up': adjusted_prob if direction == 'UP' else (1 - adjusted_prob),
            'probability_down': (1 - adjusted_prob) if direction == 'UP' else adjusted_prob,
            'expected_volatility': expected_volatility,
            'volatility_multiplier': volatility_multiplier,
            'recommendation': recommendation,
            'confidence': confidence,
            'impact_level': impact,
        }
        
        return prediction
    
    def analyze_batch(self, articles):
        """Analyze multiple articles and aggregate predictions."""
        analyses = [self.analyze_news_article(article) for article in articles]
        analyses = [a for a in analyses if a is not None]
        
        if not analyses:
            return None
        
        # Aggregate statistics
        pair = articles[0].get('pair', 'UNKNOWN')
        sentiments = [a['sentiment'] for a in analyses]
        impacts = [a['impact'] for a in analyses]
        directions = [a['prediction']['direction'] for a in analyses]
        
        # Count votes
        sentiment_votes = Counter(sentiments)
        direction_votes = Counter(directions)
        
        # Calculate aggregate prediction
        most_common_sentiment = sentiment_votes.most_common(1)[0][0] if sentiment_votes else 'NEUTRAL'
        most_common_direction = direction_votes.most_common(1)[0][0] if direction_votes else 'NEUTRAL'
        
        # Average metrics
        avg_confidence = sum(a['prediction']['confidence'] for a in analyses) / len(analyses)
        avg_volatility = sum(a['prediction']['volatility_multiplier'] for a in analyses) / len(analyses)
        
        aggregate = {
            'pair': pair,
            'total_articles': len(analyses),
            'sentiment_summary': dict(sentiment_votes),
            'dominant_sentiment': most_common_sentiment,
            'direction_summary': dict(direction_votes),
            'probable_direction': most_common_direction,
            'average_confidence': avg_confidence,
            'average_volatility_multiplier': avg_volatility,
            'high_impact_articles': len([a for a in analyses if a['impact'] == 'HIGH']),
            'medium_impact_articles': len([a for a in analyses if a['impact'] == 'MEDIUM']),
            'recommendation': self._aggregate_recommendation(analyses),
            'timestamp': datetime.now().isoformat(),
        }
        
        return aggregate
    
    def _aggregate_recommendation(self, analyses):
        """Aggregate recommendations from all analyses."""
        recommendations = Counter([a['prediction']['recommendation'] for a in analyses])
        
        if recommendations['BUY'] > recommendations['SELL']:
            return 'BUY'
        elif recommendations['SELL'] > recommendations['BUY']:
            return 'SELL'
        else:
            return 'HOLD'
    
    def get_pair_analysis(self, pair, hours=24):
        """Get aggregated analysis for a pair in the last N hours."""
        now = datetime.now()
        cutoff = now - timedelta(hours=hours)
        
        pair_analyses = [
            a for a in self.history
            if a.get('pair') == pair and 
            datetime.fromisoformat(a.get('timestamp', now.isoformat())) > cutoff
        ]
        
        if not pair_analyses:
            return None
        
        # Aggregate
        total = len(pair_analyses)
        buy_count = sum(1 for a in pair_analyses if a['prediction']['recommendation'] == 'BUY')
        sell_count = sum(1 for a in pair_analyses if a['prediction']['recommendation'] == 'SELL')
        hold_count = total - buy_count - sell_count
        
        avg_confidence = sum(a['prediction']['confidence'] for a in pair_analyses) / total
        
        return {
            'pair': pair,
            'hours': hours,
            'total_articles': total,
            'buy_signals': buy_count,
            'sell_signals': sell_count,
            'hold_signals': hold_count,
            'buy_percentage': (buy_count / total * 100) if total > 0 else 0,
            'sell_percentage': (sell_count / total * 100) if total > 0 else 0,
            'average_confidence': avg_confidence,
            'dominant_sentiment': Counter([a['sentiment'] for a in pair_analyses]).most_common(1)[0][0],
            'articles': pair_analyses[-5:],  # Last 5 articles
        }
    
    def load_history(self):
        """Load historical analyses."""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []

    def save_history(self):
        """Save analyses to file."""
        self.history_file.parent.mkdir(exist_ok=True)
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, indent=2, default=str)
    
    def get_latest_articles(self, pair=None, limit=10):
        """Get latest analyzed articles."""
        articles = self.history
        if pair:
            articles = [a for a in articles if a.get('pair') == pair]
        return sorted(articles, key=lambda x: x.get('timestamp', ''), reverse=True)[:limit]
