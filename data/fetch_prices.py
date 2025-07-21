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
    Fetch historical prices for a coin.
    :param days: Number of days of data (1 for 1d, 7 for 7d, etc.)
    :param interval: 'hourly' or 'daily'
    :param coin_id: CoinGecko coin id (e.g., 'bitcoin', 'ethereum')
    :return: List of (timestamp, price) tuples
    """
    url = f"{COINGECKO_API_URL}/coins/{coin_id}/market_chart"
    params = {"vs_currency": "usd", "days": days}
    if not api_key:
        params["interval"] = interval
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()["prices"]  # List of [timestamp, price]
        # Convert ms timestamps to datetime objects
        return [(datetime.fromtimestamp(ts/1000), price) for ts, price in data]
    except Exception as e:
        print(f"Error fetching historical prices: {e}")
        print(f"Request URL: {url}")
        print(f"Params: {params}")
        if 'resp' in locals():
            print(f"Response content: {resp.text}")
        return []


def get_prices_for_timeframe(timeframe: str, coin_id: str = "bitcoin"):
    """
    Get price data for a given timeframe: '1h', '24h', or '7d' for a given coin.
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
    else:
        raise ValueError("Unsupported timeframe. Use '1h', '24h', or '7d'.")
