import requests

COINGECKO_API_URL = "https://api.coingecko.com/api/v3"
BITCOIN_ID = "bitcoin"


def fetch_bitcoin_news():
    """
    Fetch recent news/status updates about Bitcoin from CoinGecko.
    Returns a list of dicts: [{"title": ..., "url": ...}, ...]
    """
    url = f"{COINGECKO_API_URL}/coins/{BITCOIN_ID}/status_updates"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        articles = []
        for item in data.get("status_updates", []):
            title = item.get("title") or item.get("description")
            url = item.get("article_url") or item.get("url") or ""
            if title:
                articles.append({"title": title, "url": url})
        return articles
    except Exception as e:
        print(f"Error fetching Bitcoin news from CoinGecko: {e}")
        print(f"Request URL: {url}")
        if 'resp' in locals():
            print(f"Response content: {resp.text}")
        return []
