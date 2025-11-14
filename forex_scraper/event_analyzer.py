"""
Analyzes economic events and predicts probable market outcomes.

This module correlates historical event patterns with price movements.
For each event type (e.g., "CPI m/m"), we analyze:
- How often actual > forecast (bullish for that currency)
- Historical price volatility post-event
- Typical direction and magnitude of moves
"""

import json
from datetime import datetime, timedelta
from collections import defaultdict
import statistics


class EventOutcomeAnalyzer:
    """Analyzes historical outcomes of economic events."""
    
    def __init__(self):
        self.event_history = defaultdict(list)  # event_name -> [outcomes]
        self.currency_pairs = {
            'EUR': ['EURUSD', 'EURJPY', 'EURGBP'],
            'GBP': ['GBPUSD', 'GBPJPY', 'EURGBP'],
            'USD': ['EURUSD', 'GBPUSD', 'USDJPY'],
            'JPY': ['USDJPY', 'EURJPY', 'GBPJPY'],
            'AUD': ['AUDUSD'],
            'CNY': ['USDCNY'],
            'CHF': ['USDCHF'],
            'NZD': ['NZDUSD'],
            'GOLD': ['GOLDUSD'],  # Gold
        }
    
    def record_event_outcome(self, event_name, currency, forecast, actual, pair, 
                            price_before, price_after, timestamp=None):
        """
        Record the outcome of an economic event.
        
        Args:
            event_name: e.g., "CPI m/m", "Employment Change"
            currency: e.g., "USD", "EUR"
            forecast: Expected value
            actual: Actual released value
            pair: e.g., "EURUSD"
            price_before: Price before event
            price_after: Price after event (e.g., 30 min later)
            timestamp: Event time
        """
        timestamp = timestamp or datetime.now()
        
        # Calculate outcome direction
        try:
            forecast_num = float(str(forecast).rstrip('%'))
            actual_num = float(str(actual).rstrip('%'))
            beat_forecast = actual_num > forecast_num
        except (ValueError, AttributeError):
            beat_forecast = None
        
        # Calculate price movement
        try:
            before_num = float(price_before)
            after_num = float(price_after)
            price_move_pct = ((after_num - before_num) / before_num) * 100
        except (ValueError, TypeError):
            price_move_pct = None
        
        outcome = {
            'timestamp': timestamp,
            'currency': currency,
            'forecast': forecast,
            'actual': actual,
            'beat_forecast': beat_forecast,
            'pair': pair,
            'price_move_pct': price_move_pct,
            'volatility_increase': abs(price_move_pct) > 0.3 if price_move_pct else None,
        }
        
        self.event_history[event_name].append(outcome)
    
    def analyze_event_probability(self, event_name, currency, forecast, actual=None):
        """
        Analyze the probable outcome for an event (typically before it releases).
        
        Returns:
            {
                'event_type': 'CPI m/m',
                'currency': 'USD',
                'affected_pairs': ['EURUSD', 'GBPUSD', ...],
                'beat_forecast_prob': 0.62,  # likelihood actual > forecast
                'avg_price_move_pct': 0.35,  # average |move| post-event
                'typical_direction': 'up' | 'down' | 'mixed',
                'confidence': 0.7,  # confidence in prediction
                'sample_size': 12,
            }
        """
        if event_name not in self.event_history:
            return {
                'event_type': event_name,
                'currency': currency,
                'affected_pairs': self.currency_pairs.get(currency, []),
                'beat_forecast_prob': 0.5,  # No history: neutral
                'avg_price_move_pct': 0.25,  # Conservative estimate
                'typical_direction': 'mixed',
                'confidence': 0.3,
                'sample_size': 0,
                'note': 'No historical data available'
            }
        
        outcomes = self.event_history[event_name]
        sample_size = len(outcomes)
        
        if sample_size == 0:
            return {'confidence': 0, 'sample_size': 0}
        
        # Calculate beat forecast probability
        beats = sum(1 for o in outcomes if o['beat_forecast'] is True)
        beat_prob = beats / sample_size if sample_size > 0 else 0.5
        
        # Calculate average price move
        valid_moves = [o['price_move_pct'] for o in outcomes if o['price_move_pct'] is not None]
        avg_abs_move = statistics.mean(abs(m) for m in valid_moves) if valid_moves else 0.25
        
        # Determine direction (bullish/bearish for the currency)
        positive_moves = sum(1 for m in valid_moves if m > 0)
        if len(valid_moves) > 0:
            if positive_moves / len(valid_moves) > 0.6:
                typical_direction = 'up'
            elif positive_moves / len(valid_moves) < 0.4:
                typical_direction = 'down'
            else:
                typical_direction = 'mixed'
        else:
            typical_direction = 'mixed'
        
        # Confidence: higher with more samples
        confidence = min(0.9, 0.3 + (sample_size / 20) * 0.6)
        
        return {
            'event_type': event_name,
            'currency': currency,
            'affected_pairs': self.currency_pairs.get(currency, []),
            'beat_forecast_prob': round(beat_prob, 2),
            'avg_price_move_pct': round(avg_abs_move, 3),
            'typical_direction': typical_direction,
            'confidence': round(confidence, 2),
            'sample_size': sample_size,
            'recent_outcomes': outcomes[-3:],  # Last 3 occurrences
        }
    
    def predict_pair_movement(self, upcoming_event, current_sentiment, 
                             current_momentum, pair):
        """
        Predict the probable movement of a pair based on upcoming event.
        
        Args:
            upcoming_event: dict with 'name', 'currency', 'forecast', 'importance'
            current_sentiment: -1 to +1 (from analyzer)
            current_momentum: -1 to +1 (from price)
            pair: 'EURUSD', 'GBPUSD', 'GOLDUSD'
        
        Returns:
            {
                'pair': 'EURUSD',
                'probable_direction': 'up' | 'down' | 'volatile',
                'move_probability_up': 0.65,
                'move_probability_down': 0.35,
                'expected_volatility': 'high' | 'medium' | 'low',
                'risk_reward_ratio': 1.5,
                'recommendation': 'BUY' | 'SELL' | 'WAIT' | 'NEUTRAL',
                'confidence': 0.7,
            }
        """
        event_analysis = self.analyze_event_probability(
            upcoming_event['name'],
            upcoming_event['currency'],
            upcoming_event.get('forecast')
        )
        
        # Base probability from event history
        event_beat_prob = event_analysis.get('beat_forecast_prob', 0.5)
        
        # Adjust by current sentiment/momentum
        # If sentiment is bullish and event typically beats, boost BUY probability
        adjusted_up_prob = event_beat_prob * 0.5 + (current_sentiment + 1) / 2 * 0.3 + \
                          (current_momentum + 1) / 2 * 0.2
        adjusted_up_prob = min(1.0, max(0.0, adjusted_up_prob))
        adjusted_down_prob = 1.0 - adjusted_up_prob
        
        # Determine direction
        if adjusted_up_prob > 0.6:
            probable_direction = 'up'
        elif adjusted_down_prob > 0.6:
            probable_direction = 'down'
        else:
            probable_direction = 'volatile'
        
        # Volatility based on event importance and past moves
        event_importance = upcoming_event.get('importance', 'Low Impact Expected')
        avg_move = event_analysis.get('avg_price_move_pct', 0.25)
        
        if 'High' in event_importance and avg_move > 0.5:
            expected_volatility = 'high'
        elif avg_move > 0.3:
            expected_volatility = 'medium'
        else:
            expected_volatility = 'low'
        
        # Risk-reward calculation (simplified)
        if probable_direction == 'up':
            risk_reward = (abs(adjusted_up_prob - 0.5) * 2) / max(0.1, 1 - adjusted_up_prob)
        elif probable_direction == 'down':
            risk_reward = (abs(adjusted_down_prob - 0.5) * 2) / max(0.1, 1 - adjusted_down_prob)
        else:
            risk_reward = 1.0
        
        risk_reward = round(risk_reward, 2)
        
        # Recommendation
        confidence = event_analysis.get('confidence', 0.3)
        if probable_direction == 'up' and adjusted_up_prob > 0.65 and confidence > 0.5:
            recommendation = 'BUY'
        elif probable_direction == 'down' and adjusted_down_prob > 0.65 and confidence > 0.5:
            recommendation = 'SELL'
        elif expected_volatility == 'high' and confidence > 0.6:
            recommendation = 'WAIT'  # Wait for confirmation
        else:
            recommendation = 'NEUTRAL'
        
        return {
            'pair': pair,
            'probable_direction': probable_direction,
            'move_probability_up': round(adjusted_up_prob, 2),
            'move_probability_down': round(adjusted_down_prob, 2),
            'expected_volatility': expected_volatility,
            'risk_reward_ratio': risk_reward,
            'recommendation': recommendation,
            'confidence': round(confidence, 2),
            'event_analysis': event_analysis,
        }
    
    def save_history(self, filepath):
        """Save event history to JSON file for persistence."""
        data = {}
        for event_name, outcomes in self.event_history.items():
            data[event_name] = [
                {
                    'timestamp': o['timestamp'].isoformat() if isinstance(o['timestamp'], datetime) else str(o['timestamp']),
                    'currency': o['currency'],
                    'forecast': o['forecast'],
                    'actual': o['actual'],
                    'beat_forecast': o['beat_forecast'],
                    'pair': o['pair'],
                    'price_move_pct': o['price_move_pct'],
                    'volatility_increase': o['volatility_increase'],
                }
                for o in outcomes
            ]
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    def load_history(self, filepath):
        """Load event history from JSON file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for event_name, outcomes in data.items():
                for outcome in outcomes:
                    outcome['timestamp'] = datetime.fromisoformat(outcome['timestamp'])
                    self.event_history[event_name].append(outcome)
        except FileNotFoundError:
            pass  # No history file yet
