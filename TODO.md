# TODO List for Trading Insights

## Project Setup
- [ ] Set up Python venv and initialize pip
- [ ] Create project folder structure (ui/, data/, analysis/, plots/)
- [ ] Create requirements.txt with pinned versions
- [ ] Set up initial README.md

## Data Fetching
- [ ] Implement fetch_prices.py to get Bitcoin price and historical data from CoinGecko
- [ ] Implement fetch_news.py to get Bitcoin news from a free API

## Analysis & Indicators
- [ ] Implement indicators.py for simple technical indicators (MA, RSI, etc.)
- [ ] Implement insights.py for highs/lows and basic buy/sell suggestions

## UI Development
- [ ] Set up main PyQt window (main_window.py)
- [ ] Implement dark mode and light mode toggle (theme.py)
- [ ] Integrate matplotlib price graph into PyQt UI (price_graph.py)
- [ ] Add UI for selecting timeframes (1h, 24h, 7d)
- [ ] Add section for trading insights
- [ ] Add section for news articles

## Extensibility
- [ ] Design code to support additional coins and timeframes
- [ ] Make analysis module extensible for future ML models

## Testing & Polish
- [ ] Test all features and fix bugs
- [ ] Polish UI for professional look and usability
- [ ] Update README.md with usage instructions

## Maintenance
- [ ] Update TODO.md as tasks are completed 