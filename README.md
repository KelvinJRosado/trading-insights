# Trading Insights

A Python desktop application that analyzes current market conditions for cryptocurrency and provides insights into which coins might be good to invest in.

## Features
- Sleek, modern PyQt desktop GUI (dark mode by default, light mode option)
- Supports Bitcoin initially, designed for easy extension to other coins
- Fetches real-time and historical price data (CoinGecko API)
- Displays price graphs for 1h, 24h, and 7d timeframes (matplotlib)
- Shows technical indicators (moving averages, RSI, highs/lows)
- Provides basic buy/sell suggestions
- Displays relevant news articles from free sources

## Setup
1. Clone the repository
2. Create and activate a Python virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the App
To launch the Trading Insights desktop app:

1. Make sure your virtual environment is activated:
   ```bash
   source venv/bin/activate
   ```
2. Run the main window module:
   ```bash
   python -m ui.main_window
   ```

The app window should appear. You can select the price timeframe, view trading insights, and read the latest Bitcoin news.

## Development
- Frequent, small commits are encouraged
- Track progress in TODO.md

## License
MIT 