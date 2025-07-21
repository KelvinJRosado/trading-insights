from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QMenuBar, QAction, QApplication, QComboBox, QHBoxLayout
from PyQt5.QtCore import Qt
from .theme import set_dark_theme, set_light_theme
from plots.price_graph import PriceGraphWidget
from data.fetch_prices import get_prices_for_timeframe
from analysis.insights import get_trading_insights
from sklearn.linear_model import LinearRegression
import numpy as np

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Trading Insights - Bitcoin")
        self.resize(1000, 700)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Menu bar for theme switching
        menubar = QMenuBar(self)
        view_menu = menubar.addMenu("View")
        self.dark_action = QAction("Dark Mode", self, checkable=True, checked=True)
        self.light_action = QAction("Light Mode", self, checkable=True)
        view_menu.addAction(self.dark_action)
        view_menu.addAction(self.light_action)
        self.setMenuBar(menubar)
        self.dark_action.triggered.connect(self.set_dark_mode)
        self.light_action.triggered.connect(self.set_light_mode)

        # Timeframe selector
        timeframe_layout = QHBoxLayout()
        self.timeframe_combo = QComboBox(self)
        self.timeframe_combo.addItems(["1h", "24h", "7d"])
        self.timeframe_combo.setCurrentText("24h")
        self.timeframe_combo.currentTextChanged.connect(self.on_timeframe_changed)
        timeframe_label = QLabel("Timeframe:", self)
        timeframe_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        timeframe_layout.addWidget(timeframe_label)
        timeframe_layout.addWidget(self.timeframe_combo)
        self.layout.addLayout(timeframe_layout)

        # Price graph widget
        self.price_graph = PriceGraphWidget(self, dark_mode=True)
        self.layout.addWidget(self.price_graph)

        # Trading insights section
        self.insights_label = QLabel("[Trading Insights Placeholder]", self)
        self.insights_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.insights_label)

        # Suggestion section
        self.suggestion_label = QLabel("[Suggestion Placeholder]", self)
        self.suggestion_label.setAlignment(Qt.AlignCenter)
        self.suggestion_label.setWordWrap(True)
        self.layout.addWidget(self.suggestion_label)

        # Prediction section
        self.prediction_label = QLabel("[Prediction Placeholder]", self)
        self.prediction_label.setAlignment(Qt.AlignCenter)
        self.prediction_label.setWordWrap(True)
        self.layout.addWidget(self.prediction_label)

        set_dark_theme(self)
        self.load_price_data("24h")

    def set_dark_mode(self):
        self.dark_action.setChecked(True)
        self.light_action.setChecked(False)
        set_dark_theme(self)
        self.price_graph.set_theme(True)

    def set_light_mode(self):
        self.dark_action.setChecked(False)
        self.light_action.setChecked(True)
        set_light_theme(self)
        self.price_graph.set_theme(False)

    def load_price_data(self, timeframe="24h"):
        data = get_prices_for_timeframe(timeframe)
        self.price_graph.plot_prices(data, title=f"Bitcoin Price ({timeframe})")
        # Compute and display trading insights
        prices = [price for _, price in data]
        insights = get_trading_insights(prices)
        self.display_insights(insights)
        self.display_suggestion(insights)
        self.display_prediction(prices)

    def display_insights(self, insights):
        if not insights or insights['high'] is None or insights['low'] is None:
            self.insights_label.setText("No trading insights available.")
            return
        text = (
            f"<b>High:</b> {insights['high']:.2f} &nbsp; "
            f"<b>Low:</b> {insights['low']:.2f} &nbsp; "
            f"<b>RSI:</b> {insights['rsi_value']:.2f} ({insights['rsi_signal'].capitalize()}) &nbsp; "
            f"<b>MA:</b> {insights['ma_value']:.2f} ({insights['ma_signal'].capitalize()})"
        )
        self.insights_label.setText(text)

    def display_suggestion(self, insights):
        if not insights:
            self.suggestion_label.setText("")
            return
        # Generate plain English suggestion and reasoning
        rsi = insights.get('rsi_signal')
        ma = insights.get('ma_signal')
        rsi_val = insights.get('rsi_value')
        ma_val = insights.get('ma_value')
        suggestion = ""
        reason = ""
        if rsi == 'buy' or ma == 'buy':
            suggestion = "Consider buying."
            reason = "RSI indicates oversold (RSI < 30) or price has crossed above the moving average."
        elif rsi == 'sell' or ma == 'sell':
            suggestion = "Consider selling."
            reason = "RSI indicates overbought (RSI > 70) or price has crossed below the moving average."
        else:
            suggestion = "Hold or wait."
            reason = "No strong buy/sell signals from RSI or moving average."
        self.suggestion_label.setText(f"<b>Suggestion:</b> {suggestion}<br><b>Reasoning:</b> {reason}")

    def display_prediction(self, prices):
        if not prices or len(prices) < 2:
            self.prediction_label.setText("")
            return
        # Use simple linear regression to predict next price
        X = np.arange(len(prices)).reshape(-1, 1)
        y = np.array(prices)
        model = LinearRegression()
        model.fit(X, y)
        next_idx = np.array([[len(prices)]])
        predicted_price = model.predict(next_idx)[0]
        last_price = prices[-1]
        change = predicted_price - last_price
        pct_change = (change / last_price) * 100 if last_price != 0 else 0
        direction = "up" if change > 0 else "down" if change < 0 else "no change"
        self.prediction_label.setText(
            f"<b>Predicted next price:</b> ${predicted_price:,.2f} ({direction}, {pct_change:+.2f}%)"
        )

    def on_timeframe_changed(self, timeframe):
        self.load_price_data(timeframe)

# For standalone testing
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
