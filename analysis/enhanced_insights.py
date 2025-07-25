from typing import Dict, Any, List, Tuple, Optional
from .ml_indicators import generate_ml_trading_signals
from .indicators import moving_average, relative_strength_index
from data.fetch_prices import get_ohlcv_for_timeframe


def get_enhanced_trading_insights(coin_id: str = "bitcoin", timeframe: str = "7d") -> Dict[str, Any]:
    """
    Get comprehensive trading insights using OHLCV data and advanced ML algorithms.
    
    :param coin_id: CoinGecko coin ID
    :param timeframe: Data timeframe ('1h', '24h', '7d', '30d')
    :return: Dictionary with enhanced raw insights
    """
    try:
        # Fetch OHLCV data
        ohlcv_data = get_ohlcv_for_timeframe(timeframe, coin_id)
        
        if not ohlcv_data:
            return {
                'error': f'Failed to fetch OHLCV data for {coin_id}',
                'method': 'Enhanced ML Analysis',
                'data_available': False
            }
        
        # Extract price data for backward compatibility
        prices = [candle[4] for candle in ohlcv_data]  # close prices
        
        # Calculate traditional indicators for comparison
        high_price = max(prices) if prices else 0
        low_price = min(prices) if prices else 0
        
        # RSI and MA calculations
        rsi_values = relative_strength_index(prices, period=14)
        ma_values = moving_average(prices, 14)
        
        rsi_current = rsi_values[-1] if rsi_values and rsi_values[-1] is not None else None
        ma_current = ma_values[-1] if ma_values and ma_values[-1] is not None else None
        
        # Compile enhanced raw insights
        enhanced_insights = {
            'method': 'Enhanced ML Analysis',
            'data_available': True,
            'data_points': len(ohlcv_data),
            'timeframe': timeframe,
            'coin_id': coin_id,
            'high': high_price,
            'low': low_price,
            'rsi_value': rsi_current,
            'ma_value': ma_current,
            'ohlcv_array': ohlcv_data
        }
        
        return enhanced_insights
        
    except Exception as e:
        return {
            'error': f'Enhanced analysis failed: {str(e)}',
            'method': 'Enhanced ML Analysis',
            'data_available': False,
            'high': None,
            'low': None,
            'rsi_value': None,
            'ma_value': None,
            'ohlcv_array': []
        }


def format_ml_insights_for_advisor(insights: Dict[str, Any]) -> Dict[str, str]:
    """
    Format ML insights for the advisor system.
    
    :param insights: Enhanced insights dictionary
    :return: Formatted insights for advisor consumption
    """
    if insights.get('error'):
        return {
            'method': 'Enhanced ML Analysis',
            'short': 'Data unavailable',
            'medium': 'Cannot analyze',
            'long': 'Insufficient data',
            'buy': 'No',
            'sell': 'No',
            'suggestion': 'Hold - Data Error',
            'reason': insights['error']
        }
    
    ml_recommendation = insights.get('ml_recommendation', 'HOLD')
    ml_confidence = insights.get('ml_confidence', 0)
    technical_summary = insights.get('technical_summary', '')
    ml_signals = insights.get('ml_signals', {})
    
    # Generate timeframe-specific predictions
    short_term = generate_timeframe_prediction(ml_signals, 'short')
    medium_term = generate_timeframe_prediction(ml_signals, 'medium')
    long_term = generate_timeframe_prediction(ml_signals, 'long')
    
    # Generate buy/sell recommendations
    buy_recommendation = 'Yes' if ml_recommendation == 'BUY' else 'No'
    sell_recommendation = 'Yes' if ml_recommendation == 'SELL' else 'No'
    
    # Format suggestion with confidence
    confidence_text = f"{ml_confidence*100:.0f}% confidence" if ml_confidence > 0 else "Low confidence"
    
    if ml_recommendation == 'BUY':
        suggestion = f"<span style='color:#4caf50;'>ML Buy [{confidence_text}]</span>"
    elif ml_recommendation == 'SELL':
        suggestion = f"<span style='color:#e53935;'>ML Sell [{confidence_text}]</span>"
    else:
        suggestion = f"<span style='color:#ffb300;'>ML Hold [{confidence_text}]</span>"
    
    # Generate comprehensive reason
    reason = generate_ml_reasoning(insights)
    
    return {
        'method': 'Enhanced ML Analysis',
        'short': short_term,
        'medium': medium_term,
        'long': long_term,
        'buy': buy_recommendation,
        'sell': sell_recommendation,
        'suggestion': suggestion,
        'reason': reason
    }


def generate_timeframe_prediction(ml_signals: Dict[str, Any], timeframe: str) -> str:
    """Generate timeframe-specific predictions from ML signals"""
    
    # Extract key signals
    bollinger = ml_signals.get('bollinger_bands', {})
    macd = ml_signals.get('macd', {})
    stochastic = ml_signals.get('stochastic', {})
    volume = ml_signals.get('volume', {})
    ml_pred = ml_signals.get('ml_prediction', {})
    
    if timeframe == 'short':
        # Focus on momentum indicators for short term
        if macd.get('signal') == 'BUY':
            return "Bullish momentum detected"
        elif macd.get('signal') == 'SELL':
            return "Bearish momentum detected"
        elif stochastic.get('signal') == 'BUY':
            return "Oversold bounce expected"
        elif stochastic.get('signal') == 'SELL':
            return "Overbought correction likely"
        else:
            return "Sideways movement expected"
    
    elif timeframe == 'medium':
        # Focus on trend indicators for medium term
        if bollinger.get('signal') == 'BUY':
            return "Trend reversal to upside"
        elif bollinger.get('signal') == 'SELL':
            return "Trend reversal to downside"
        elif volume.get('signal') == 'BUY':
            return "Volume supporting uptrend"
        elif volume.get('signal') == 'SELL':
            return "Volume supporting downtrend"
        else:
            return "Consolidation phase"
    
    else:  # long term
        # Focus on ML predictions for long term
        ensemble_pred = ml_pred.get('ensemble', 0)
        if ensemble_pred > 0.05:
            return "ML models suggest growth"
        elif ensemble_pred < -0.05:
            return "ML models suggest decline"
        else:
            return "ML models neutral/uncertain"


def generate_ml_reasoning(insights: Dict[str, Any]) -> str:
    """Generate comprehensive reasoning from ML analysis"""
    
    if insights.get('error'):
        return insights['error']
    
    ml_signals = insights.get('ml_signals', {})
    ml_analysis = insights.get('ml_analysis', {})
    technical_summary = insights.get('technical_summary', '')
    
    reasoning_parts = []
    
    # Add ML model insights
    predictions = ml_analysis.get('predictions', {})
    model_scores = ml_analysis.get('model_scores', {})
    
    if predictions:
        ensemble_pred = predictions.get('ensemble', 0)
        best_model = max(model_scores.items(), key=lambda x: x[1].get('mean_cv_score', 0))[0] if model_scores else 'unknown'
        
        reasoning_parts.append(f"ML ensemble predicts {ensemble_pred*100:+.1f}% price change")
        if model_scores:
            best_score = model_scores[best_model].get('mean_cv_score', 0)
            reasoning_parts.append(f"Best model: {best_model} (R²={best_score:.2f})")
    
    # Add technical analysis summary
    if technical_summary:
        reasoning_parts.append(f"Technical: {technical_summary}")
    
    # Add data quality info
    data_points = insights.get('data_points', 0)
    reasoning_parts.append(f"Analysis based on {data_points} data points")
    
    return "; ".join(reasoning_parts) if reasoning_parts else "ML analysis completed with standard parameters"


def get_enhanced_method_insights(insights: Dict[str, Any], prices: List[float], method: str) -> Tuple[str, str, str, str, str, str, str]:
    """
    Enhanced method insights that integrates ML analysis with existing methods.
    This function bridges the new ML system with the existing advisor interface.
    
    :param insights: Traditional insights from get_trading_insights
    :param prices: Price data
    :param method: Analysis method name
    :return: (suggestion, reason, short_term, medium_term, long_term, buy, sell)
    """
    
    if method == "Enhanced ML Analysis":
        # Use the new ML system
        coin_id = "bitcoin"  # Default, should be passed as parameter in future
        timeframe = "7d"     # Default, should be passed as parameter in future
        
        enhanced_insights = get_enhanced_trading_insights(coin_id, timeframe)
        ml_formatted = format_ml_insights_for_advisor(enhanced_insights)
        
        return (
            ml_formatted['suggestion'],
            ml_formatted['reason'],
            ml_formatted['short'],
            ml_formatted['medium'],
            ml_formatted['long'],
            ml_formatted['buy'],
            ml_formatted['sell']
        )
    
    # For other methods, fall back to existing logic
    # This preserves backward compatibility
    return generate_fallback_method_insights(insights, prices, method)


def generate_fallback_method_insights(insights: Dict[str, Any], prices: List[float], method: str) -> Tuple[str, str, str, str, str, str, str]:
    """
    Generate insights using traditional methods (fallback for non-ML methods).
    This maintains the existing functionality while allowing ML integration.
    """
    
    # Default values
    suggestion = f"<span style='color:#ffb300;'>{method} Hold</span>"
    reason = f"{method} analysis completed"
    short = "Neutral"
    medium = "Neutral" 
    long = "Neutral"
    buy = "No"
    sell = "No"
    
    if not insights or not prices:
        return suggestion, f"{method}: Insufficient data", short, medium, long, buy, sell
    
    # Use traditional logic based on RSI and MA
    rsi_signal = insights.get('rsi_signal', 'hold')
    ma_signal = insights.get('ma_signal', 'hold')
    rsi_value = insights.get('rsi_value', 50)
    
    # Generate method-specific analysis
    if method == "Technical Analysis":
        if rsi_signal == 'buy' and ma_signal == 'buy':
            suggestion = f"<span style='color:#4caf50;'>Strong Buy</span>"
            reason = f"Both RSI ({rsi_value:.1f}) and MA confirm oversold conditions"
            short, medium, long = "Bullish reversal", "Upward trend likely", "Depends on fundamentals"
            buy, sell = "Yes", "No"
        elif rsi_signal == 'sell' and ma_signal == 'sell':
            suggestion = f"<span style='color:#e53935;'>Strong Sell</span>"
            reason = f"Both RSI ({rsi_value:.1f}) and MA indicate overbought conditions"
            short, medium, long = "Bearish reversal", "Downward trend likely", "Market correction expected"
            buy, sell = "No", "Yes"
        else:
            suggestion = f"<span style='color:#ffb300;'>Hold</span>"
            reason = f"Mixed signals: RSI={rsi_signal}, MA={ma_signal}"
            short, medium, long = "Range-bound", "Consolidation phase", "Awaiting breakout"
            buy, sell = "No", "No"
    
    elif method == "Momentum Model":
        if len(prices) >= 5:
            price_change = (prices[-1] - prices[-5]) / prices[-5] * 100 if prices[-5] != 0 else 0
            if price_change > 5:
                suggestion = f"<span style='color:#4caf50;'>Momentum Buy</span>"
                reason = f"Strong upward momentum: +{price_change:.1f}%"
                short, medium, long = "Continuation expected", "Strong uptrend", "Momentum-driven growth"
                buy, sell = "Yes", "No"
            elif price_change < -5:
                suggestion = f"<span style='color:#e53935;'>Momentum Sell</span>"
                reason = f"Strong downward momentum: {price_change:.1f}%"
                short, medium, long = "Further decline likely", "Downtrend continues", "Bearish momentum"
                buy, sell = "No", "Yes"
    
    return suggestion, reason, short, medium, long, buy, sell