import requests
import os

CRYPTOPANIC_API_URL = "https://cryptopanic.com/api/v1/posts/"


def fetch_bitcoin_news():
    """
    Fetch recent news articles about Bitcoin from CryptoPanic.
    Returns a list of dicts: [{"title": ..., "url": ...}, ...]
    """
    params = {
        "currencies": "BTC",
        "public": "true"
    }
    api_key = os.environ.get("CRYPTOPANIC_API_KEY")
    if api_key:
        params["auth_token"] = api_key
    try:
        resp = requests.get(CRYPTOPANIC_API_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        articles = []
        for item in data.get("results", []):
            title = item.get("title")
            url = item.get("url")
            if title and url:
                articles.append({"title": title, "url": url})
        return articles
    except requests.exceptions.HTTPError as e:
        print(f"CryptoPanic HTTP error: {e}")
        print(f"Request URL: {resp.url}")
        print(f"Response content: {resp.text}")
        return []
    except Exception as e:
        print(f"Error fetching Bitcoin news: {e}")
        return []
