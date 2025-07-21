import requests
import os
from datetime import datetime, timedelta

COINGECKO_API_URL = "https://api.coingecko.com/api/v3"
BITCOIN_ID = "bitcoin"

HEADERS = {"User-Agent": "Mozilla/5.0"}
api_key = os.environ.get("COINGECKO_API_KEY")
if api_key:
    HEADERS["x-cg-pro-api-key"] = api_key


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
        return None


def fetch_historical_prices(days: int, interval: str = "hourly"):
    """
    Fetch historical prices for Bitcoin.
    :param days: Number of days of data (1 for 1d, 7 for 7d, etc.)
    :param interval: 'hourly' or 'daily'
    :return: List of (timestamp, price) tuples
    """
    url = f"{COINGECKO_API_URL}/coins/{BITCOIN_ID}/market_chart"
    params = {"vs_currency": "usd", "days": days, "interval": interval}
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()["prices"]  # List of [timestamp, price]
        # Convert ms timestamps to datetime objects
        return [(datetime.fromtimestamp(ts/1000), price) for ts, price in data]
    except Exception as e:
        print(f"Error fetching historical prices: {e}")
        return []


def get_prices_for_timeframe(timeframe: str):
    """
    Get price data for a given timeframe: '1h', '24h', or '7d'.
    :return: List of (datetime, price) tuples
    """
    if timeframe == "1h":
        # CoinGecko does not provide minute-level granularity for free, so fetch 1 day and slice last hour
        data = fetch_historical_prices(1, interval="hourly")
        if data:
            now = datetime.now()
            one_hour_ago = now - timedelta(hours=1)
            return [(dt, price) for dt, price in data if dt >= one_hour_ago]
        return []
    elif timeframe == "24h":
        return fetch_historical_prices(1, interval="hourly")
    elif timeframe == "7d":
        return fetch_historical_prices(7, interval="hourly")
    else:
        raise ValueError("Unsupported timeframe. Use '1h', '24h', or '7d'.")
