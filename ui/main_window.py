from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QMenuBar, QAction, QApplication, QComboBox, QHBoxLayout, QTabWidget, QTabWidget, QWidget, QVBoxLayout, QFrame, QSizePolicy, QSpacerItem
from PyQt5.QtCore import Qt
from .theme import set_dark_theme, set_light_theme
from plots.price_graph import PriceGraphWidget
from data.fetch_prices import get_prices_for_timeframe
from analysis.insights import get_trading_insights
from sklearn.linear_model import LinearRegression
import numpy as np
from collections import Counter

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

        # Add top spacer (larger)
        self.layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Fixed))

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

        # Divider below graph
        self.divider1 = QFrame()
        self.divider1.setFrameShape(QFrame.HLine)
        self.divider1.setFrameShadow(QFrame.Sunken)
        self.divider1.setStyleSheet("color: #888; background: #888; height: 2px;")
        self.layout.addWidget(self.divider1)

        # Trading insights section
        self.insights_label = QLabel("[Trading Insights Placeholder]", self)
        self.insights_label.setAlignment(Qt.AlignCenter)
        self.insights_label.setObjectName("insightsLabel")
        self.layout.addWidget(self.insights_label)

        # Divider below insights
        self.divider2 = QFrame()
        self.divider2.setFrameShape(QFrame.HLine)
        self.divider2.setFrameShadow(QFrame.Sunken)
        self.divider2.setStyleSheet("color: #888; background: #888; height: 2px;")
        self.layout.addWidget(self.divider2)

        # Suggestion section as tabs
        self.suggestion_tabs = QTabWidget(self)
        self.suggestion_tabs.setTabPosition(QTabWidget.North)
        self.suggestion_tabs.setTabShape(QTabWidget.Rounded)
        self.suggestion_tabs.setMovable(False)
        self.suggestion_tabs.setUsesScrollButtons(False)
        self.suggestion_tabs.setDocumentMode(True)
        self.suggestion_tabs.setStyleSheet("QTabBar::tab { min-width: 33%; padding: 10px; font-weight: bold; } QTabWidget::pane { border: none; }")
        self.suggestion_widgets = []
        for i, label in enumerate(["Technical Analysis", "Momentum Model", "Simple ML"]):
            tab = QWidget()
            tab.layout = QVBoxLayout(tab)
            label_widget = QLabel(f"[Suggestions for {label}]")
            label_widget.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            label_widget.setWordWrap(True)
            label_widget.setStyleSheet("font-size: 13px; padding: 8px 0 8px 8px;")
            tab.layout.addWidget(label_widget)
            self.suggestion_tabs.addTab(tab, label)
            self.suggestion_widgets.append(label_widget)
        self.suggestion_tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.layout.addWidget(self.suggestion_tabs)

        # Divider below tabs
        self.divider3 = QFrame()
        self.divider3.setFrameShape(QFrame.HLine)
        self.divider3.setFrameShadow(QFrame.Sunken)
        self.divider3.setStyleSheet("color: #888; background: #888; height: 2px;")
        self.layout.addWidget(self.divider3)

        # Consensus section
        self.consensus_label = QLabel("[Consensus Placeholder]", self)
        self.consensus_label.setAlignment(Qt.AlignCenter)
        self.consensus_label.setWordWrap(True)
        self.consensus_label.setObjectName("consensusLabel")
        self.layout.addWidget(self.consensus_label)

        # Prediction section
        self.prediction_label = QLabel("[Prediction Placeholder]", self)
        self.prediction_label.setAlignment(Qt.AlignCenter)
        self.prediction_label.setWordWrap(True)
        self.prediction_label.setObjectName("predictionLabel")
        self.layout.addWidget(self.prediction_label)

        # Set background color for main window
        self.central_widget.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #232b36, stop:1 #1e1e1e);")

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
        self.display_suggestions_and_consensus(insights, prices)
        self.display_prediction(prices)

    def display_insights(self, insights):
        if not insights or insights['high'] is None or insights['low'] is None:
            self.insights_label.setText("No trading insights available.")
            return
        # Add tooltips for each metric
        high = f'<span title="Highest price in the selected timeframe">High: {insights["high"]:.2f}</span>'
        low = f'<span title="Lowest price in the selected timeframe">Low: {insights["low"]:.2f}</span>'
        rsi = f'<span title="Relative Strength Index (momentum indicator, <30=oversold, >70=overbought)">RSI: {insights["rsi_value"]:.2f} ({insights["rsi_signal"].capitalize()})</span>'
        ma = f'<span title="Moving Average (average price over a window)">MA: {insights["ma_value"]:.2f} ({insights["ma_signal"].capitalize()})</span>'
        text = (
            f"{high} &nbsp; {low} &nbsp; {rsi} &nbsp; {ma}"
        )
        self.insights_label.setText(text)

    def display_suggestions_and_consensus(self, insights, prices):
        # Generate insights for each method
        # For now, use the same logic for all three as a placeholder
        methods = ["Technical Analysis", "Momentum Model", "Simple ML"]
        all_suggestions = []
        for i, method in enumerate(methods):
            # Placeholder: use the same insights for all
            suggestion, reason, st, mt, lt, buy, sell = self._generate_method_insights(insights, prices, method)
            # Add vertical separator and placeholder in tab content
            tab = self.suggestion_tabs.widget(i)
            # Remove old layout widgets if any
            while tab.layout.count() > 0:
                item = tab.layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()
            hbox = QHBoxLayout()
            left = QLabel(self.suggestion_widgets[i].text())
            left.setAlignment(Qt.AlignLeft | Qt.AlignTop)
            left.setWordWrap(True)
            left.setStyleSheet("font-size: 13px; padding: 8px 0 8px 8px;")
            vline = QFrame()
            vline.setFrameShape(QFrame.VLine)
            vline.setFrameShadow(QFrame.Sunken)
            vline.setStyleSheet("color: #888; background: #888; width: 2px;")
            right = QLabel("<i>Future content here</i>")
            right.setAlignment(Qt.AlignLeft | Qt.AlignTop)
            right.setWordWrap(True)
            right.setStyleSheet("font-size: 13px; padding: 8px 0 8px 16px;")
            hbox.addWidget(left, 2)
            hbox.addWidget(vline)
            hbox.addWidget(right, 1)
            tab.layout.addLayout(hbox)
            self.suggestion_widgets[i] = left
            all_suggestions.append({
                'short': st, 'medium': mt, 'long': lt, 'buy': buy, 'sell': sell, 'suggestion': suggestion
            })
        # Consensus logic: majority vote for buy/sell/hold, average for price changes
        consensus = self._generate_consensus(all_suggestions)
        self.consensus_label.setText(
            f"<b>Consensus Insights</b><br>"
            f"<b>Short-term:</b> {consensus['short']}<br>"
            f"<b>Medium-term:</b> {consensus['medium']}<br>"
            f"<b>Long-term:</b> {consensus['long']}<br>"
            f"<b>Buy now:</b> {consensus['buy']}<br>"
            f"<b>Sell now:</b> {consensus['sell']}<br>"
            f"<b>Overall Suggestion:</b> {consensus['suggestion']}"
        )

    def _generate_method_insights(self, insights, prices, method):
        # Placeholder logic: can be replaced with method-specific logic
        rsi = insights.get('rsi_signal')
        ma = insights.get('ma_signal')
        suggestion = ""
        reason = ""
        # Use text fallback for emojis if not supported
        emoji_buy = "[YES]" if rsi == 'buy' or ma == 'buy' else "[NO]"
        emoji_sell = "[YES]" if rsi == 'sell' or ma == 'sell' else "[NO]"
        if rsi == 'buy' or ma == 'buy':
            suggestion = f"<span style='color:#4caf50;'>Consider buying. {emoji_buy}</span>"
            reason = f"{method}: RSI indicates oversold (RSI < 30) or price has crossed above the moving average."
        elif rsi == 'sell' or ma == 'sell':
            suggestion = f"<span style='color:#e53935;'>Consider selling. {emoji_sell}</span>"
            reason = f"{method}: RSI indicates overbought (RSI > 70) or price has crossed below the moving average."
        else:
            suggestion = f"<span style='color:#ffb300;'>Hold or wait. [WAIT]</span>"
            reason = f"{method}: No strong buy/sell signals from RSI or moving average."
        # Short/medium/long-term price change (placeholder)
        st = "Likely small change"
        mt = "Likely moderate change"
        lt = "Trend unclear"
        buy = f"Yes {emoji_buy}" if rsi == 'buy' or ma == 'buy' else f"No [NO]"
        sell = f"Yes {emoji_sell}" if rsi == 'sell' or ma == 'sell' else f"No [NO]"
        return suggestion, reason, st, mt, lt, buy, sell

    def _generate_consensus(self, all_suggestions):
        # Majority vote for buy/sell, most common for other fields
        def most_common(lst):
            return Counter(lst).most_common(1)[0][0] if lst else ""
        consensus = {
            'short': most_common([s['short'] for s in all_suggestions]),
            'medium': most_common([s['medium'] for s in all_suggestions]),
            'long': most_common([s['long'] for s in all_suggestions]),
            'buy': most_common([s['buy'] for s in all_suggestions]),
            'sell': most_common([s['sell'] for s in all_suggestions]),
            'suggestion': most_common([s['suggestion'] for s in all_suggestions]),
        }
        # Add text fallback for consensus suggestion
        suggestion = consensus['suggestion']
        if 'buy' in suggestion.lower():
            suggestion = f"<span style='color:#4caf50;'>Consider buying. [YES]</span>"
        elif 'sell' in suggestion.lower():
            suggestion = f"<span style='color:#e53935;'>Consider selling. [NO]</span>"
        else:
            suggestion = f"<span style='color:#ffb300;'>Hold or wait. [WAIT]</span>"
        consensus['suggestion'] = suggestion
        return consensus

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
        # Clarify timeframe based on current selection
        timeframe = self.timeframe_combo.currentText()
        if timeframe == "1h":
            tf_label = "(next hour)"
        elif timeframe == "24h":
            tf_label = "(next day)"
        elif timeframe == "7d":
            tf_label = "(next week)"
        else:
            tf_label = ""
        self.prediction_label.setText(
            f"<b>Predicted next price {tf_label}:</b> ${predicted_price:,.2f} ({direction}, {pct_change:+.2f}%)"
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
