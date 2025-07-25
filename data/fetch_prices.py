import requests
import os
from datetime import datetime, timedelta

COINGECKO_API_URL = "https://api.coingecko.com/api/v3"
BITCOIN_ID = "bitcoin"

HEADERS = {"User-Agent": "Mozilla/5.0"}
api_key = os.environ.get("COINGECKO_API_KEY")
if api_key:
    HEADERS["x-cg-pro-api-key"] = api_key

# Simple in-memory cache for price data by timeframe
_price_cache = {}

def clear_cache():
    global _price_cache
    _price_cache = {}


def fetch_current_price():
    """Fetch the current price of Bitcoin in USD."""
    url = f"{COINGECKO_API_URL}/simple/price"
    params = {"ids": BITCOIN_ID, "vs_currencies": "usd"}
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        return resp.json()[BITCOIN_ID]["usd"]
    except Exception as e:
        print(f"Error fetching current price: {e}")
        print(f"Request URL: {url}")
        print(f"Params: {params}")
        if 'resp' in locals():
            print(f"Response content: {resp.text}")
        return None


def fetch_historical_prices(days: int, interval: str = "hourly", coin_id: str = "bitcoin"):
    """
    Fetch historical prices for a coin with fallback strategies.
    :param days: Number of days of data (1 for 1d, 7 for 7d, etc.)
    :param interval: 'hourly' or 'daily'
    :param coin_id: CoinGecko coin id (e.g., 'bitcoin', 'ethereum')
    :return: List of (timestamp, price) tuples
    """
    url = f"{COINGECKO_API_URL}/coins/{coin_id}/market_chart"
    
    # Try different parameter combinations based on API limitations
    attempts = []
    
    if days <= 1:
        attempts.append({"vs_currency": "usd", "days": days, "interval": "hourly"})
    elif days <= 7:
        attempts.append({"vs_currency": "usd", "days": days, "interval": "hourly"})
        attempts.append({"vs_currency": "usd", "days": days})  # Without interval
    else:
        # For longer periods, don't use interval parameter (API limitation)
        attempts.append({"vs_currency": "usd", "days": days})
        # Fallback to shorter period if long period fails
        attempts.append({"vs_currency": "usd", "days": 7})
        attempts.append({"vs_currency": "usd", "days": 1, "interval": "hourly"})
    
    for i, params in enumerate(attempts):
        try:
            if api_key:
                # Remove interval parameter if using API key
                params.pop("interval", None)
                
            resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            data = resp.json()["prices"]
            
            if data:  # Successfully got data
                result = [(datetime.fromtimestamp(ts/1000), price) for ts, price in data]
                if i > 0:  # Used fallback
                    print(f"Used fallback parameters for {coin_id}: {params}")
                return result
                
        except Exception as e:
            if i == len(attempts) - 1:  # Last attempt failed
                print(f"All attempts failed for {coin_id} ({days} days): {e}")
                print(f"Final URL: {url}")
                print(f"Final params: {params}")
                if 'resp' in locals():
                    print(f"Response: {resp.text}")
                return _generate_mock_data(days, coin_id)
            # Continue to next attempt
    
    return []


def _generate_mock_data(days: int, coin_id: str = "bitcoin"):
    """Generate mock price data as ultimate fallback"""
    print(f"Generating mock data for {coin_id} ({days} days)")
    
    # Base prices for different coins
    base_prices = {
        "bitcoin": 45000,
        "ethereum": 2500,
        "dogecoin": 0.08,
        "solana": 120,
        "ripple": 0.6
    }
    
    base_price = base_prices.get(coin_id, 45000)
    current_time = datetime.now()
    data_points = min(days * 24, 168)  # Limit to reasonable number of points
    
    mock_data = []
    for i in range(data_points):
        # Generate some realistic price variation (+/- 3%)
        import random
        variation = random.uniform(-0.03, 0.03)
        price = base_price * (1 + variation)
        timestamp = current_time - timedelta(hours=data_points - i)
        mock_data.append((timestamp, price))
    
    return mock_data


def get_prices_for_timeframe(timeframe: str, coin_id: str = "bitcoin"):
    """
    Get price data for a given timeframe: '1h', '24h', '7d', or '30d' for a given coin.
    :return: List of (datetime, price) tuples
    """
    cache_key = f"{coin_id}:{timeframe}"
    if cache_key in _price_cache:
        return _price_cache[cache_key]
    if timeframe == "1h":
        data = fetch_historical_prices(1, interval="hourly", coin_id=coin_id)
        if data:
            now = datetime.now()
            one_hour_ago = now - timedelta(hours=1)
            result = [(dt, price) for dt, price in data if dt >= one_hour_ago]
            _price_cache[cache_key] = result
            return result
        _price_cache[cache_key] = []
        return []
    elif timeframe == "24h":
        result = fetch_historical_prices(1, interval="hourly", coin_id=coin_id)
        _price_cache[cache_key] = result
        return result
    elif timeframe == "7d":
        result = fetch_historical_prices(7, interval="hourly", coin_id=coin_id)
        _price_cache[cache_key] = result
        return result
    elif timeframe == "30d":
        result = fetch_historical_prices(30, interval="daily", coin_id=coin_id)
        _price_cache[cache_key] = result
        return result
    else:
        raise ValueError("Unsupported timeframe. Use '1h', '24h', '7d', or '30d'.")


def fetch_ohlcv_data(days: int, coin_id: str = "bitcoin"):
    """
    Fetch OHLCV (Open, High, Low, Close, Volume) data from CoinGecko API.
    Falls back to market_chart endpoint if OHLC endpoint is unavailable.
    
    :param days: Number of days of data to fetch
    :param coin_id: CoinGecko coin id (e.g., 'bitcoin', 'ethereum')
    :return: List of OHLCV tuples (timestamp, open, high, low, close, volume) or None if failed
    """
    # Try OHLC endpoint first (for paid API users)
    ohlc_url = f"{COINGECKO_API_URL}/coins/{coin_id}/ohlc"
    market_chart_url = f"{COINGECKO_API_URL}/coins/{coin_id}/market_chart"
    
    # First attempt: Try OHLC endpoint
    try:
        params = {"vs_currency": "usd", "days": days}
        resp = requests.get(ohlc_url, params=params, headers=HEADERS, timeout=10)
        
        if resp.status_code == 200:
            ohlc_data = resp.json()
            if ohlc_data and len(ohlc_data) > 0:
                # OHLC data format: [[timestamp, open, high, low, close], ...]
                result = []
                for ohlc in ohlc_data:
                    if len(ohlc) >= 5:
                        timestamp = datetime.fromtimestamp(ohlc[0]/1000)
                        # Note: Volume data not available in OHLC endpoint, set to 0
                        result.append((timestamp, ohlc[1], ohlc[2], ohlc[3], ohlc[4], 0))
                print(f"Successfully fetched OHLC data for {coin_id}: {len(result)} data points")
                return result
    except Exception as e:
        print(f"OHLC endpoint failed for {coin_id}: {e}")
    
    # Fallback: Use market_chart endpoint to construct OHLCV data
    try:
        params = {"vs_currency": "usd", "days": days}
        resp = requests.get(market_chart_url, params=params, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        
        data = resp.json()
        prices = data.get("prices", [])
        volumes = data.get("total_volumes", [])
        
        if not prices:
            print(f"No price data available for {coin_id}")
            return None
        
        # Convert market_chart data to OHLCV format
        # Group by time periods to create OHLC data
        result = []
        volume_dict = {v[0]: v[1] for v in volumes} if volumes else {}
        
        # For market_chart data, we only have single price points
        # We'll use the price as close and estimate OHLC based on adjacent prices
        for i, (ts, price) in enumerate(prices):
            timestamp = datetime.fromtimestamp(ts/1000)
            volume = volume_dict.get(ts, 0)
            
            # Use price as close, estimate others based on local context
            close_price = price
            
            # Look at adjacent prices for OHLC estimation
            prev_price = prices[i-1][1] if i > 0 else price
            next_price = prices[i+1][1] if i < len(prices)-1 else price
            
            # Simple OHLC estimation from available data
            open_price = prev_price
            high_price = max(prev_price, price, next_price)
            low_price = min(prev_price, price, next_price)
            
            result.append((timestamp, open_price, high_price, low_price, close_price, volume))
        
        print(f"Successfully converted market_chart to OHLCV for {coin_id}: {len(result)} data points")
        return result
        
    except Exception as e:
        print(f"Error fetching OHLCV data for {coin_id}: {e}")
        return None


def get_ohlcv_for_timeframe(timeframe: str, coin_id: str = "bitcoin"):
    """
    Get OHLCV data for a given timeframe.
    :param timeframe: '1h', '24h', '7d', or '30d'
    :param coin_id: CoinGecko coin id
    :return: List of OHLCV tuples (timestamp, open, high, low, close, volume) or None if failed
    """
    cache_key = f"{coin_id}:ohlcv:{timeframe}"
    if cache_key in _price_cache:
        return _price_cache[cache_key]
    
    if timeframe == "1h":
        data = fetch_ohlcv_data(1, coin_id=coin_id)
        if data:
            now = datetime.now()
            one_hour_ago = now - timedelta(hours=1)
            result = [(ts, o, h, l, c, v) for ts, o, h, l, c, v in data if ts >= one_hour_ago]
            _price_cache[cache_key] = result
            return result
        return None
    elif timeframe == "24h":
        result = fetch_ohlcv_data(1, coin_id=coin_id)
        if result:
            _price_cache[cache_key] = result
        return result
    elif timeframe == "7d":
        result = fetch_ohlcv_data(7, coin_id=coin_id)
        if result:
            _price_cache[cache_key] = result
        return result
    elif timeframe == "30d":
        result = fetch_ohlcv_data(30, coin_id=coin_id)
        if result:
            _price_cache[cache_key] = result
        return result
    else:
        raise ValueError("Unsupported timeframe. Use '1h', '24h', '7d', or '30d'.")
