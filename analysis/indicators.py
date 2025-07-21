import numpy as np

def moving_average(prices, window):
    """
    Calculate the simple moving average (MA) for a list of prices.
    :param prices: List of float prices
    :param window: Window size (int)
    :return: List of MA values (same length as prices, with None for indices < window-1)
    """
    if len(prices) < window:
        return [None] * len(prices)
    ma = [None] * (window - 1)
    for i in range(window - 1, len(prices)):
        ma.append(np.mean(prices[i - window + 1:i + 1]))
    return ma

def exponential_moving_average(prices, window):
    """
    Calculate the exponential moving average (EMA) for a list of prices.
    :param prices: List of float prices
    :param window: Window size (int)
    :return: List of EMA values (same length as prices, with None for indices < window-1)
    """
    if len(prices) < window:
        return [None] * len(prices)
    ema = [None] * (window - 1)
    alpha = 2 / (window + 1)
    # Start EMA with the first window's mean
    prev_ema = np.mean(prices[:window])
    ema.append(prev_ema)
    for price in prices[window:]:
        prev_ema = alpha * price + (1 - alpha) * prev_ema
        ema.append(prev_ema)
    return ema

def relative_strength_index(prices, period=14):
    """
    Calculate the Relative Strength Index (RSI) for a list of prices.
    :param prices: List of float prices
    :param period: RSI period (int, default 14)
    :return: List of RSI values (same length as prices, with None for indices < period)
    """
    if len(prices) < period:
        return [None] * len(prices)
    rsi = [None] * period
    for i in range(period, len(prices)):
        window = prices[i - period + 1:i + 1]
        gains = [max(0, window[j] - window[j - 1]) for j in range(1, len(window))]
        losses = [max(0, window[j - 1] - window[j]) for j in range(1, len(window))]
        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)
        if avg_loss == 0:
            rsi.append(100)
        else:
            rs = avg_gain / avg_loss
            rsi.append(100 - (100 / (1 + rs)))
    return rsi
