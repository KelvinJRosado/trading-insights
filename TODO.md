# TODO List for Trading Insights

## Project Setup
- [x] Set up Python venv and initialize pip
- [x] Create project folder structure (ui/, data/, analysis/, plots/)
- [x] Create requirements.txt with pinned versions
- [x] Set up initial README.md

## Data Fetching
- [x] Implement fetch_prices.py to get Bitcoin price and historical data from CoinGecko
- [x] Implement fetch_news.py to get Bitcoin news from a free API

## Analysis & Indicators
- [x] Implement indicators.py for simple technical indicators (MA, RSI, etc.)
- [x] Implement insights.py for highs/lows and basic buy/sell suggestions

## UI Development
- [x] Set up main PyQt window (main_window.py)
- [x] Implement dark mode and light mode toggle (theme.py)
- [x] Integrate matplotlib price graph into PyQt UI (price_graph.py)
- [x] Add UI for selecting timeframes (1h, 24h, 7d, 30d)
- [x] Add section for trading insights
- [x] Add section for news articles

## Extensibility
- [x] Design code to support additional coins and timeframes
- [x] Make analysis module extensible for future ML models

## Testing & Polish
- [ ] Test all features and fix bugs
- [ ] Polish UI for professional look and usability
- [x] Update README.md with usage instructions

## Maintenance
- [x] Update TODO.md as tasks are completed 

## Future Improvements
- [ ] Add more advanced ML models or AI analysis methods
- [ ] Add more advisor personas or allow user-defined advisors
- [ ] Add more robust error handling and user feedback for API failures
- [ ] Add unit/integration tests for multi-coin, multi-timeframe, and AI analysis features
- [ ] Add support for additional news sources or asset types (optional/future) 