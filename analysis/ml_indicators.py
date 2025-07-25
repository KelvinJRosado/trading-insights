import numpy as np
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
import warnings
warnings.filterwarnings('ignore')


def bollinger_bands(prices: List[float], window: int = 20, std_dev: int = 2) -> Tuple[List[float], List[float], List[float]]:
    """
    Calculate Bollinger Bands: upper band, middle band (SMA), lower band.
    
    :param prices: List of prices
    :param window: Moving average window
    :param std_dev: Standard deviation multiplier
    :return: (upper_band, middle_band, lower_band)
    """
    if len(prices) < window:
        return ([None] * len(prices), [None] * len(prices), [None] * len(prices))
    
    upper_band = [None] * (window - 1)
    middle_band = [None] * (window - 1)
    lower_band = [None] * (window - 1)
    
    for i in range(window - 1, len(prices)):
        window_prices = prices[i - window + 1:i + 1]
        mean = np.mean(window_prices)
        std = np.std(window_prices)
        
        middle_band.append(mean)
        upper_band.append(mean + (std_dev * std))
        lower_band.append(mean - (std_dev * std))
    
    return upper_band, middle_band, lower_band


def macd(prices: List[float], fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> Tuple[List[float], List[float], List[float]]:
    """
    Calculate MACD (Moving Average Convergence Divergence).
    
    :param prices: List of prices
    :param fast_period: Fast EMA period
    :param slow_period: Slow EMA period
    :param signal_period: Signal line EMA period
    :return: (macd_line, signal_line, histogram)
    """
    if len(prices) < slow_period:
        return ([None] * len(prices), [None] * len(prices), [None] * len(prices))
    
    # Calculate EMAs
    fast_ema = exponential_moving_average(prices, fast_period)
    slow_ema = exponential_moving_average(prices, slow_period)
    
    # Calculate MACD line
    macd_line = []
    for i in range(len(prices)):
        if fast_ema[i] is not None and slow_ema[i] is not None:
            macd_line.append(fast_ema[i] - slow_ema[i])
        else:
            macd_line.append(None)
    
    # Calculate signal line (EMA of MACD line)
    macd_values = [x for x in macd_line if x is not None]
    if len(macd_values) < signal_period:
        signal_line = [None] * len(prices)
        histogram = [None] * len(prices)
    else:
        signal_ema = exponential_moving_average(macd_values, signal_period)
        # Align signal line with original data
        signal_line = [None] * (len(prices) - len(signal_ema)) + signal_ema
        
        # Calculate histogram
        histogram = []
        for i in range(len(prices)):
            if macd_line[i] is not None and signal_line[i] is not None:
                histogram.append(macd_line[i] - signal_line[i])
            else:
                histogram.append(None)
    
    return macd_line, signal_line, histogram


def exponential_moving_average(prices: List[float], window: int) -> List[float]:
    """Calculate Exponential Moving Average"""
    if len(prices) < window:
        return [None] * len(prices)
    
    ema = [None] * (window - 1)
    alpha = 2 / (window + 1)
    
    # Start with SMA for first value
    first_ema = sum(prices[:window]) / window
    ema.append(first_ema)
    
    # Calculate EMA for remaining values
    for i in range(window, len(prices)):
        ema.append(alpha * prices[i] + (1 - alpha) * ema[-1])
    
    return ema


def stochastic_oscillator(ohlc_data: List[Tuple], k_period: int = 14, d_period: int = 3) -> Tuple[List[float], List[float]]:
    """
    Calculate Stochastic Oscillator (%K and %D).
    
    :param ohlc_data: List of (timestamp, open, high, low, close, volume) tuples
    :param k_period: Period for %K calculation
    :param d_period: Period for %D (moving average of %K)
    :return: (%K values, %D values)
    """
    if len(ohlc_data) < k_period:
        return ([None] * len(ohlc_data), [None] * len(ohlc_data))
    
    k_values = [None] * (k_period - 1)
    
    for i in range(k_period - 1, len(ohlc_data)):
        # Get k_period window
        window = ohlc_data[i - k_period + 1:i + 1]
        
        # Extract high, low, close values
        highs = [candle[2] for candle in window]  # high prices
        lows = [candle[3] for candle in window]   # low prices
        current_close = ohlc_data[i][4]           # current close
        
        highest_high = max(highs)
        lowest_low = min(lows)
        
        if highest_high == lowest_low:
            k_values.append(50)  # Avoid division by zero
        else:
            k_value = ((current_close - lowest_low) / (highest_high - lowest_low)) * 100
            k_values.append(k_value)
    
    # Calculate %D (moving average of %K)
    k_numeric = [x for x in k_values if x is not None]
    if len(k_numeric) < d_period:
        d_values = [None] * len(ohlc_data)
    else:
        d_values = [None] * (len(k_values) - len(k_numeric))
        for i in range(d_period - 1, len(k_numeric)):
            d_values.append(sum(k_numeric[i - d_period + 1:i + 1]) / d_period)
        
        # Pad to match original length
        while len(d_values) < len(ohlc_data):
            d_values.append(None)
    
    return k_values, d_values


def volume_indicators(ohlc_data: List[Tuple]) -> Dict[str, Any]:
    """
    Calculate volume-based indicators.
    
    :param ohlc_data: List of (timestamp, open, high, low, close, volume) tuples
    :return: Dictionary with volume indicators
    """
    if not ohlc_data:
        return {}
    
    volumes = [candle[5] for candle in ohlc_data]
    prices = [candle[4] for candle in ohlc_data]  # close prices
    
    # Volume Moving Average
    window = min(20, len(volumes))
    volume_ma = []
    for i in range(len(volumes)):
        if i < window - 1:
            volume_ma.append(None)
        else:
            volume_ma.append(sum(volumes[i - window + 1:i + 1]) / window)
    
    # On-Balance Volume (OBV)
    obv = [0]
    for i in range(1, len(ohlc_data)):
        if prices[i] > prices[i-1]:
            obv.append(obv[-1] + volumes[i])
        elif prices[i] < prices[i-1]:
            obv.append(obv[-1] - volumes[i])
        else:
            obv.append(obv[-1])
    
    # Volume Price Trend (VPT)
    vpt = [0]
    for i in range(1, len(ohlc_data)):
        if prices[i-1] != 0:
            price_change_pct = (prices[i] - prices[i-1]) / prices[i-1]
            vpt.append(vpt[-1] + (volumes[i] * price_change_pct))
        else:
            vpt.append(vpt[-1])
    
    return {
        'volume_ma': volume_ma,
        'obv': obv,
        'vpt': vpt,
        'avg_volume': sum(volumes) / len(volumes) if volumes else 0,
        'volume_trend': 'increasing' if volumes[-5:] and sum(volumes[-5:]) > sum(volumes[-10:-5]) else 'decreasing'
    }


def advanced_ml_analysis(ohlc_data: List[Tuple], lookback_periods: int = 50) -> Dict[str, Any]:
    """
    Perform advanced ML analysis using multiple algorithms.
    
    :param ohlc_data: List of (timestamp, open, high, low, close, volume) tuples
    :param lookback_periods: Number of periods to use for feature engineering
    :return: Dictionary with ML analysis results
    """
    if len(ohlc_data) < lookback_periods:
        return {
            'error': f'Insufficient data for ML analysis. Need at least {lookback_periods} data points, got {len(ohlc_data)}',
            'predictions': {},
            'feature_importance': {},
            'model_scores': {}
        }
    
    try:
        # Extract features from OHLCV data
        features = extract_ml_features(ohlc_data, lookback_periods)
        
        if features is None or len(features) < 10:
            return {
                'error': 'Failed to extract sufficient features for ML analysis',
                'predictions': {},
                'feature_importance': {},
                'model_scores': {}
            }
        
        # Prepare target variable (next period price change)
        targets = []
        closes = [candle[4] for candle in ohlc_data]
        
        for i in range(len(features)):
            if i + lookback_periods + 1 < len(closes):
                current_price = closes[i + lookback_periods]
                next_price = closes[i + lookback_periods + 1]
                price_change = (next_price - current_price) / current_price
                targets.append(price_change)
            else:
                targets.append(0)  # Placeholder for last values
        
        # Remove last few samples that don't have future data
        valid_samples = min(len(features), len(targets) - 1)
        X = np.array(features[:valid_samples])
        y = np.array(targets[:valid_samples])
        
        if len(X) < 5:
            return {
                'error': 'Insufficient valid samples for ML training',
                'predictions': {},
                'feature_importance': {},
                'model_scores': {}
            }
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Train multiple ML models
        models = {
            'random_forest': RandomForestRegressor(n_estimators=50, random_state=42, max_depth=10),
            'gradient_boosting': GradientBoostingRegressor(n_estimators=50, random_state=42, max_depth=6),
            'linear_regression': LinearRegression(),
            'ridge': Ridge(alpha=1.0),
            'svr': SVR(kernel='rbf', C=1.0, gamma='scale')
        }
        
        predictions = {}
        model_scores = {}
        feature_importance = {}
        
        for name, model in models.items():
            try:
                # Cross-validation score
                cv_scores = cross_val_score(model, X_scaled, y, cv=min(3, len(X)//2), scoring='r2')
                model_scores[name] = {
                    'mean_cv_score': np.mean(cv_scores),
                    'std_cv_score': np.std(cv_scores)
                }
                
                # Fit model and make prediction
                model.fit(X_scaled, y)
                
                # Predict next price change
                if len(features) > 0:
                    last_features = np.array(features[-1]).reshape(1, -1)
                    last_features_scaled = scaler.transform(last_features)
                    pred = model.predict(last_features_scaled)[0]
                    predictions[name] = pred
                    
                    # Feature importance (for tree-based models)
                    if hasattr(model, 'feature_importances_'):
                        feature_importance[name] = model.feature_importances_.tolist()
                
            except Exception as e:
                print(f"Error training {name} model: {e}")
                predictions[name] = 0
                model_scores[name] = {'mean_cv_score': 0, 'std_cv_score': 0}
        
        # Ensemble prediction (average of all models)
        if predictions:
            ensemble_pred = np.mean(list(predictions.values()))
            predictions['ensemble'] = ensemble_pred
        
        return {
            'predictions': predictions,
            'feature_importance': feature_importance,
            'model_scores': model_scores,
            'sample_size': len(X),
            'feature_count': X.shape[1] if len(X) > 0 else 0
        }
        
    except Exception as e:
        return {
            'error': f'ML analysis failed: {str(e)}',
            'predictions': {},
            'feature_importance': {},
            'model_scores': {}
        }


def extract_ml_features(ohlc_data: List[Tuple], lookback: int) -> Optional[List[List[float]]]:
    """
    Extract ML features from OHLCV data.
    
    :param ohlc_data: List of (timestamp, open, high, low, close, volume) tuples
    :param lookback: Number of lookback periods
    :return: List of feature vectors
    """
    try:
        closes = [candle[4] for candle in ohlc_data]
        highs = [candle[2] for candle in ohlc_data]
        lows = [candle[3] for candle in ohlc_data]
        volumes = [candle[5] for candle in ohlc_data]
        
        features = []
        
        for i in range(lookback, len(ohlc_data)):
            feature_vector = []
            
            # Price-based features
            window_closes = closes[i-lookback:i]
            window_highs = highs[i-lookback:i]
            window_lows = lows[i-lookback:i]
            window_volumes = volumes[i-lookback:i]
            
            # Basic price statistics
            feature_vector.extend([
                np.mean(window_closes),
                np.std(window_closes),
                np.max(window_highs),
                np.min(window_lows),
                closes[i-1] / np.mean(window_closes) if np.mean(window_closes) != 0 else 1,  # Price to MA ratio
            ])
            
            # Price changes and momentum
            if len(window_closes) >= 2:
                returns = [(window_closes[j] - window_closes[j-1]) / window_closes[j-1] 
                          for j in range(1, len(window_closes)) if window_closes[j-1] != 0]
                if returns:
                    feature_vector.extend([
                        np.mean(returns),
                        np.std(returns),
                        np.max(returns),
                        np.min(returns)
                    ])
                else:
                    feature_vector.extend([0, 0, 0, 0])
            else:
                feature_vector.extend([0, 0, 0, 0])
            
            # Volume features
            feature_vector.extend([
                np.mean(window_volumes),
                np.std(window_volumes),
                volumes[i-1] / np.mean(window_volumes) if np.mean(window_volumes) != 0 else 1,  # Volume ratio
            ])
            
            # Technical indicators as features
            if i >= 20:  # Need enough data for indicators
                rsi_window = closes[i-14:i]
                if len(rsi_window) >= 14:
                    # Simple RSI calculation
                    gains = [max(0, rsi_window[j] - rsi_window[j-1]) for j in range(1, len(rsi_window))]
                    losses = [max(0, rsi_window[j-1] - rsi_window[j]) for j in range(1, len(rsi_window))]
                    avg_gain = np.mean(gains) if gains else 0
                    avg_loss = np.mean(losses) if losses else 0
                    rsi = 50 if avg_loss == 0 else 100 - (100 / (1 + avg_gain / avg_loss))
                    feature_vector.append(rsi)
                else:
                    feature_vector.append(50)
            else:
                feature_vector.append(50)
            
            features.append(feature_vector)
        
        return features
        
    except Exception as e:
        print(f"Error extracting ML features: {e}")
        return None


def generate_ml_trading_signals(ohlc_data: List[Tuple]) -> Dict[str, Any]:
    """
    Generate comprehensive trading signals using ML and technical analysis.
    
    :param ohlc_data: List of (timestamp, open, high, low, close, volume) tuples
    :return: Dictionary with trading signals and analysis
    """
    if not ohlc_data or len(ohlc_data) < 20:
        return {
            'error': 'Insufficient data for signal generation',
            'signals': {},
            'confidence': 0,
            'recommendation': 'HOLD'
        }
    
    try:
        closes = [candle[4] for candle in ohlc_data]
        
        # Technical indicators
        bb_upper, bb_middle, bb_lower = bollinger_bands(closes)
        macd_line, signal_line, histogram = macd(closes)
        k_values, d_values = stochastic_oscillator(ohlc_data)
        volume_data = volume_indicators(ohlc_data)
        
        # ML analysis
        ml_results = advanced_ml_analysis(ohlc_data)
        
        # Generate signals
        signals = {
            'bollinger_bands': analyze_bollinger_signals(closes, bb_upper, bb_middle, bb_lower),
            'macd': analyze_macd_signals(macd_line, signal_line, histogram),
            'stochastic': analyze_stochastic_signals(k_values, d_values),
            'volume': analyze_volume_signals(volume_data, closes),
            'ml_prediction': ml_results.get('predictions', {})
        }
        
        # Calculate overall confidence and recommendation
        confidence, recommendation = calculate_overall_signal(signals, ml_results)
        
        return {
            'signals': signals,
            'ml_analysis': ml_results,
            'confidence': confidence,
            'recommendation': recommendation,
            'technical_summary': generate_technical_summary(signals)
        }
        
    except Exception as e:
        return {
            'error': f'Signal generation failed: {str(e)}',
            'signals': {},
            'confidence': 0,
            'recommendation': 'HOLD'
        }


def analyze_bollinger_signals(closes: List[float], upper: List[float], middle: List[float], lower: List[float]) -> Dict[str, Any]:
    """Analyze Bollinger Bands signals"""
    if not all([closes, upper, middle, lower]) or len(closes) < 2:
        return {'signal': 'HOLD', 'strength': 0, 'reason': 'Insufficient data'}
    
    current_price = closes[-1]
    current_upper = upper[-1]
    current_lower = lower[-1]
    current_middle = middle[-1]
    
    if None in [current_upper, current_lower, current_middle]:
        return {'signal': 'HOLD', 'strength': 0, 'reason': 'Insufficient historical data'}
    
    # Signal logic
    if current_price <= current_lower:
        return {'signal': 'BUY', 'strength': 0.8, 'reason': 'Price touching lower Bollinger Band (oversold)'}
    elif current_price >= current_upper:
        return {'signal': 'SELL', 'strength': 0.8, 'reason': 'Price touching upper Bollinger Band (overbought)'}
    elif current_price > current_middle:
        return {'signal': 'HOLD', 'strength': 0.3, 'reason': 'Price above middle band (bullish bias)'}
    else:
        return {'signal': 'HOLD', 'strength': 0.3, 'reason': 'Price below middle band (bearish bias)'}


def analyze_macd_signals(macd_line: List[float], signal_line: List[float], histogram: List[float]) -> Dict[str, Any]:
    """Analyze MACD signals"""
    if not all([macd_line, signal_line, histogram]) or len(macd_line) < 2:
        return {'signal': 'HOLD', 'strength': 0, 'reason': 'Insufficient MACD data'}
    
    current_macd = macd_line[-1]
    current_signal = signal_line[-1]
    prev_macd = macd_line[-2]
    prev_signal = signal_line[-2]
    
    if None in [current_macd, current_signal, prev_macd, prev_signal]:
        return {'signal': 'HOLD', 'strength': 0, 'reason': 'Insufficient MACD historical data'}
    
    # Bullish crossover
    if prev_macd <= prev_signal and current_macd > current_signal:
        return {'signal': 'BUY', 'strength': 0.7, 'reason': 'MACD bullish crossover'}
    # Bearish crossover
    elif prev_macd >= prev_signal and current_macd < current_signal:
        return {'signal': 'SELL', 'strength': 0.7, 'reason': 'MACD bearish crossover'}
    # Above signal line
    elif current_macd > current_signal:
        return {'signal': 'HOLD', 'strength': 0.4, 'reason': 'MACD above signal line (bullish momentum)'}
    # Below signal line
    else:
        return {'signal': 'HOLD', 'strength': 0.4, 'reason': 'MACD below signal line (bearish momentum)'}


def analyze_stochastic_signals(k_values: List[float], d_values: List[float]) -> Dict[str, Any]:
    """Analyze Stochastic Oscillator signals"""
    if not k_values or not d_values or len(k_values) < 2:
        return {'signal': 'HOLD', 'strength': 0, 'reason': 'Insufficient stochastic data'}
    
    current_k = k_values[-1]
    current_d = d_values[-1]
    
    if None in [current_k, current_d]:
        return {'signal': 'HOLD', 'strength': 0, 'reason': 'Insufficient stochastic historical data'}
    
    # Oversold condition
    if current_k < 20 and current_d < 20:
        return {'signal': 'BUY', 'strength': 0.6, 'reason': 'Stochastic oversold condition'}
    # Overbought condition
    elif current_k > 80 and current_d > 80:
        return {'signal': 'SELL', 'strength': 0.6, 'reason': 'Stochastic overbought condition'}
    else:
        return {'signal': 'HOLD', 'strength': 0.2, 'reason': f'Stochastic neutral (%K: {current_k:.1f}, %D: {current_d:.1f})'}


def analyze_volume_signals(volume_data: Dict[str, Any], closes: List[float]) -> Dict[str, Any]:
    """Analyze volume-based signals"""
    if not volume_data or not closes:
        return {'signal': 'HOLD', 'strength': 0, 'reason': 'No volume data available'}
    
    volume_trend = volume_data.get('volume_trend', 'unknown')
    
    # Price and volume trend confirmation
    if len(closes) >= 5:
        price_trend = 'increasing' if closes[-1] > closes[-5] else 'decreasing'
        
        if price_trend == 'increasing' and volume_trend == 'increasing':
            return {'signal': 'BUY', 'strength': 0.5, 'reason': 'Rising price with increasing volume'}
        elif price_trend == 'decreasing' and volume_trend == 'increasing':
            return {'signal': 'SELL', 'strength': 0.5, 'reason': 'Falling price with increasing volume'}
        else:
            return {'signal': 'HOLD', 'strength': 0.2, 'reason': f'Price {price_trend}, volume {volume_trend}'}
    
    return {'signal': 'HOLD', 'strength': 0.1, 'reason': 'Insufficient price data for volume analysis'}


def calculate_overall_signal(signals: Dict[str, Any], ml_results: Dict[str, Any]) -> Tuple[float, str]:
    """Calculate overall trading signal and confidence"""
    buy_score = 0
    sell_score = 0
    total_weight = 0
    
    # Weight different signal types
    weights = {
        'bollinger_bands': 0.25,
        'macd': 0.25,
        'stochastic': 0.20,
        'volume': 0.15,
        'ml_prediction': 0.15
    }
    
    for signal_type, weight in weights.items():
        if signal_type in signals:
            signal_data = signals[signal_type]
            
            if signal_type == 'ml_prediction':
                # Handle ML predictions
                ensemble_pred = signal_data.get('ensemble', 0)
                if ensemble_pred > 0.02:  # 2% positive change threshold
                    buy_score += weight * abs(ensemble_pred) * 50
                elif ensemble_pred < -0.02:  # 2% negative change threshold
                    sell_score += weight * abs(ensemble_pred) * 50
                total_weight += weight
            else:
                # Handle technical indicators
                if isinstance(signal_data, dict) and 'signal' in signal_data:
                    strength = signal_data.get('strength', 0)
                    if signal_data['signal'] == 'BUY':
                        buy_score += weight * strength
                    elif signal_data['signal'] == 'SELL':
                        sell_score += weight * strength
                    total_weight += weight
    
    # Calculate confidence and recommendation
    if total_weight > 0:
        buy_score = buy_score / total_weight
        sell_score = sell_score / total_weight
        
        confidence = max(buy_score, sell_score)
        
        if buy_score > sell_score and buy_score > 0.4:
            recommendation = 'BUY'
        elif sell_score > buy_score and sell_score > 0.4:
            recommendation = 'SELL'
        else:
            recommendation = 'HOLD'
            confidence = min(confidence, 0.3)  # Lower confidence for hold signals
    else:
        confidence = 0
        recommendation = 'HOLD'
    
    return min(confidence, 1.0), recommendation


def generate_technical_summary(signals: Dict[str, Any]) -> str:
    """Generate a human-readable technical analysis summary"""
    summary_parts = []
    
    for signal_type, signal_data in signals.items():
        if signal_type == 'ml_prediction':
            continue  # Skip ML predictions in technical summary
            
        if isinstance(signal_data, dict) and 'reason' in signal_data:
            summary_parts.append(f"{signal_type.title()}: {signal_data['reason']}")
    
    return "; ".join(summary_parts) if summary_parts else "No technical signals available"