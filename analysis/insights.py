from .indicators import moving_average, relative_strength_index


def get_high_low(prices):
    """
    Return the highest and lowest price in the list.
    :param prices: List of float prices
    :return: (high, low)
    """
    if not prices:
        return None, None
    return max(prices), min(prices)


def basic_buy_sell_signals(prices, window=14):
    """
    Generate basic buy/sell signals based on MA and RSI.
    :param prices: List of float prices
    :param window: Window for MA/RSI
    :return: Dict with 'rsi_signal', 'ma_signal', and their values
    """
    ma = moving_average(prices, window)
    rsi = relative_strength_index(prices, period=window)
    signals = {}
    # RSI signal
    if rsi and rsi[-1] is not None:
        if rsi[-1] < 30:
            signals['rsi_signal'] = 'buy'
        elif rsi[-1] > 70:
            signals['rsi_signal'] = 'sell'
        else:
            signals['rsi_signal'] = 'hold'
        signals['rsi_value'] = rsi[-1]
    else:
        signals['rsi_signal'] = 'unknown'
        signals['rsi_value'] = None
    # MA signal (price crossing MA)
    if ma and ma[-2] is not None and len(prices) >= 2:
        prev_price, curr_price = prices[-2], prices[-1]
        prev_ma, curr_ma = ma[-2], ma[-1]
        if prev_price < prev_ma and curr_price > curr_ma:
            signals['ma_signal'] = 'buy'
        elif prev_price > prev_ma and curr_price < curr_ma:
            signals['ma_signal'] = 'sell'
        else:
            signals['ma_signal'] = 'hold'
        signals['ma_value'] = curr_ma
    else:
        signals['ma_signal'] = 'unknown'
        signals['ma_value'] = None
    return signals


def get_trading_insights(prices, ohlcv_array, window=14):
    """
    Aggregate trading insights: high, low, and raw indicator values.
    :param prices: List of float prices
    :param ohlcv_array: List of OHLCV tuples (timestamp, open, high, low, close, volume)
    :param window: Window for indicators
    :return: Dict of raw insights
    """
    high = max(prices) if prices else None
    low = min(prices) if prices else None
    ma = moving_average(prices, window)
    rsi = relative_strength_index(prices, period=window)
    return {
        'high': high,
        'low': low,
        'ma_value': ma[-1] if ma and ma[-1] is not None else None,
        'rsi_value': rsi[-1] if rsi and rsi[-1] is not None else None,
        'ohlcv_array': ohlcv_array
    }
