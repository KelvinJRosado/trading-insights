import requests

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
    except Exception as e:
        print(f"Error fetching Bitcoin news: {e}")
        return []
