from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QMenuBar, QAction, QApplication, QComboBox, QHBoxLayout, QTabWidget, QTabWidget, QWidget, QVBoxLayout, QFrame, QSizePolicy, QSpacerItem, QScrollArea, QTextBrowser, QToolBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from .theme import set_dark_theme, set_light_theme
from plots.price_graph import PriceGraphWidget
from data.fetch_prices import get_prices_for_timeframe
from analysis.insights import get_trading_insights
from sklearn.linear_model import LinearRegression
import numpy as np
from collections import Counter
import ollama
import asyncio

class LLMWorker(QThread):
    result_ready = pyqtSignal(int, str)
    def __init__(self, idx, persona, insights, llm_outputs, parent=None):
        super().__init__(parent)
        self.idx = idx
        self.persona = persona
        self.insights = insights
        self.llm_outputs = llm_outputs
    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(self.call_ollama())
        self.llm_outputs[self.idx] = result
        self.result_ready.emit(self.idx, result)
        # If all outputs are ready, trigger consensus LLM
        if all(self.llm_outputs):
            self.parent().start_consensus_llm(self.llm_outputs)
    async def call_ollama(self):
        # Inject advisor personality into the prompt
        if self.persona == "Conservative Carl":
            personality = (
                "You are Conservative Carl, a financial advisor who always prioritizes minimizing risk, playing it safe, and steady, reliable growth. "
                "You prefer to avoid big risks and focus on protecting your client's capital, even if it means missing out on some gains. "
                "Your advice should reflect a cautious, risk-averse approach."
            )
        elif self.persona == "Aggressive Alex":
            personality = (
                "You are Aggressive Alex, a financial advisor who is focused on maximizing gains, taking calculated risks, and making bold moves. "
                "You are not afraid to recommend aggressive strategies if you believe the potential reward is high. "
                "Your advice should reflect a risk-tolerant, growth-seeking approach."
            )
        elif self.persona == "Balanced Bailey":
            personality = (
                "You are Balanced Bailey, a financial advisor who carefully weighs both risk and reward. "
                "You seek a balanced approach, recommending strategies that offer growth while also managing risk. "
                "Your advice should reflect a moderate, well-rounded perspective."
            )
        else:
            personality = f"You are {self.persona}, a financial advisor."
        prompt = (
            f"{personality}\n\n"
            "Your goal is to help your client make the greatest gains, but your advice should reflect your unique personality. "
            f"Here are the trading insights: {self.insights}. "
            "Please explain these insights in simple, friendly English for a non-expert investor, and make sure your suggestions reflect your personal style."
        )
        try:
            response = await ollama.AsyncClient().generate(model='llama3.2:latest', prompt=prompt)
            return response['response'].strip()
        except Exception as e:
            return f"[LLM error: {e}]"

class ConsensusLLMWorker(QThread):
    result_ready = pyqtSignal(str)
    def __init__(self, advisor_outputs, parent=None):
        super().__init__(parent)
        self.advisor_outputs = advisor_outputs
    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(self.call_ollama())
        self.result_ready.emit(result)
    async def call_ollama(self):
        prompt = (
            "You are a panel of financial advisors. Here are the opinions of three advisors: "
            f"\n\nAdvisor 1: {self.advisor_outputs[0]}\n\nAdvisor 2: {self.advisor_outputs[1]}\n\nAdvisor 3: {self.advisor_outputs[2]}\n\n"
            "Please summarize the consensus in simple, friendly English for a non-expert investor, focusing on maximizing gains."
        )
        try:
            response = await ollama.AsyncClient().generate(model='llama3.2:latest', prompt=prompt)
            return response['response'].strip()
        except Exception as e:
            return f"[LLM error: {e}]"

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.llm_threads = []  # Store references to all running LLM threads
        self.setWindowTitle("Trading Insights - Bitcoin")
        self.resize(1000, 700)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Menu bar for theme switching (remove dark mode)
        menubar = QMenuBar(self)
        view_menu = menubar.addMenu("View")
        self.light_action = QAction("Light Mode", self, checkable=True, checked=True)
        view_menu.addAction(self.light_action)
        self.setMenuBar(menubar)
        self.light_action.setChecked(True)
        self.light_action.setEnabled(False)

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
        self.price_graph = PriceGraphWidget(self, dark_mode=False)
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
        self.insights_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.layout.addWidget(self.insights_label)

        # Divider below insights
        self.divider2 = QFrame()
        self.divider2.setFrameShape(QFrame.HLine)
        self.divider2.setFrameShadow(QFrame.Sunken)
        self.divider2.setStyleSheet("color: #888; background: #888; height: 2px;")
        self.layout.addWidget(self.divider2)

        # Suggestion section as tabs
        advisor_names = ["Conservative Carl", "Aggressive Alex", "Balanced Bailey"]
        self.suggestion_tabs = QTabWidget(self)
        self.suggestion_tabs.setTabPosition(QTabWidget.North)
        self.suggestion_tabs.setTabShape(QTabWidget.Rounded)
        self.suggestion_tabs.setMovable(False)
        self.suggestion_tabs.setUsesScrollButtons(False)
        self.suggestion_tabs.setDocumentMode(True)
        self.suggestion_tabs.setStyleSheet("QTabBar::tab { min-width: 33%; padding: 10px; font-weight: bold; } QTabWidget::pane { border: none; }")
        self.suggestion_widgets = []
        self.llm_widgets = []
        self.suggestion_toolboxes = [] # Store toolboxes for each tab
        for i, label in enumerate(advisor_names):
            tab = QWidget()
            tab.layout = QVBoxLayout(tab)
            # Collapsible insights section
            toolbox = QToolBox()
            insights_widget = QWidget()
            insights_layout = QVBoxLayout(insights_widget)
            left_label = QLabel(f"[Suggestions for {label}]")
            left_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
            left_label.setWordWrap(True)
            left_label.setStyleSheet("font-size: 13px; padding: 8px 0 8px 8px;")
            left_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            insights_layout.addWidget(left_label)
            toolbox.addItem(insights_widget, "Show Trading Insights")
            toolbox.setCurrentIndex(-1)  # Minimized by default
            # LLM output area (QTextBrowser, large font)
            right_browser = QTextBrowser()
            right_browser.setOpenExternalLinks(True)
            right_browser.setReadOnly(True)
            right_browser.setStyleSheet("font-size: 16px; padding: 8px 0 8px 16px; background: transparent; border: none; color: inherit;")
            right_browser.setMaximumHeight(400)
            right_browser.setTextInteractionFlags(Qt.TextSelectableByMouse)
            right_browser.setMarkdown("<span style='color:inherit;'><i>Loading advisor explanation...</i></span>")
            # Layout: insights (collapsible) above, LLM output below
            tab.layout.addWidget(toolbox)
            tab.layout.addWidget(right_browser, stretch=1)
            self.suggestion_tabs.addTab(tab, label)
            self.suggestion_widgets.append(left_label)
            self.llm_widgets.append(right_browser)
            self.suggestion_toolboxes.append(toolbox)
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
        self.consensus_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.layout.addWidget(self.consensus_label)

        # Prediction section
        self.prediction_label = QLabel("[Prediction Placeholder]", self)
        self.prediction_label.setAlignment(Qt.AlignCenter)
        self.prediction_label.setWordWrap(True)
        self.prediction_label.setObjectName("predictionLabel")
        self.prediction_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.layout.addWidget(self.prediction_label)

        # Set background color for main window
        self.central_widget.setStyleSheet("background: #faf9f6;")

        set_light_theme(self)
        self.load_price_data("24h")

    def set_dark_mode(self):
        pass  # No-op

    def set_light_mode(self):
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
        advisor_names = ["Conservative Carl", "Aggressive Alex", "Balanced Bailey"]
        methods = ["Technical Analysis", "Momentum Model", "Simple ML"]
        all_suggestions = []
        self._cleanup_threads()  # Clean up finished threads before starting new ones
        self.llm_outputs = [None, None, None]  # Store LLM outputs for consensus
        for i, method in enumerate(methods):
            suggestion, reason, st, mt, lt, buy, sell = self._generate_method_insights(insights, prices, method)
            left_text = (
                f"<b>Short-term:</b> {st}<br>"
                f"<b>Medium-term:</b> {mt}<br>"
                f"<b>Long-term:</b> {lt}<br>"
                f"<b>Buy now:</b> {buy}<br>"
                f"<b>Sell now:</b> {sell}<br>"
                f"<b>Suggestion:</b> {suggestion}<br>"
                f"<b>Reasoning:</b> {reason}"
            )
            self.suggestion_widgets[i].setText(left_text)
            self.llm_widgets[i].setMarkdown("<span style='color:inherit;'><i>Loading advisor explanation...</i></span>")
            all_suggestions.append({
                'short': st, 'medium': mt, 'long': lt, 'buy': buy, 'sell': sell, 'suggestion': suggestion,
                'reason': reason, 'advisor': advisor_names[i], 'method': method
            })
            persona = advisor_names[i]
            insights_str = left_text.replace('<br>', '\n').replace('<b>', '').replace('</b>', '')
            worker = LLMWorker(i, persona, insights_str, self.llm_outputs, self)
            worker.result_ready.connect(self.update_llm_tab)
            worker.finished.connect(lambda: self._cleanup_threads())
            self.llm_threads.append(worker)
            worker.start()
        consensus = self._generate_consensus(all_suggestions)
        consensus_left = (
            f"<b>Consensus Insights</b><br>"
            f"<b>Short-term:</b> {consensus['short']}<br>"
            f"<b>Medium-term:</b> {consensus['medium']}<br>"
            f"<b>Long-term:</b> {consensus['long']}<br>"
            f"<b>Buy now:</b> {consensus['buy']}<br>"
            f"<b>Sell now:</b> {consensus['sell']}<br>"
            f"<b>Overall Suggestion:</b> {consensus['suggestion']}"
        )
        self.consensus_label.setText(consensus_left)
        # Consensus LLM output as QTextBrowser
        self.consensus_llm_label = getattr(self, 'consensus_llm_label', None)
        if not self.consensus_llm_label:
            self.consensus_llm_label = QTextBrowser()
            self.consensus_llm_label.setOpenExternalLinks(True)
            self.consensus_llm_label.setReadOnly(True)
            self.consensus_llm_label.setStyleSheet("font-size: 16px; padding: 8px 0 8px 16px; background: transparent; border: none; color: inherit;")
            self.consensus_llm_label.setMaximumHeight(400)
            self.consensus_llm_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            self.consensus_llm_label.setMarkdown("<span style='color:inherit;'><i>Loading consensus explanation...</i></span>")
            self.layout.insertWidget(self.layout.indexOf(self.consensus_label) + 1, self.consensus_llm_label)
        else:
            self.consensus_llm_label.setMarkdown("<span style='color:inherit;'><i>Loading consensus explanation...</i></span>")
        self.consensus_llm_waiting = True

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

    def update_llm_tab(self, idx, text):
        self.llm_widgets[idx].setMarkdown(text)
        # If all advisor outputs are ready, trigger consensus LLM
        if hasattr(self, 'llm_outputs') and all(self.llm_outputs) and getattr(self, 'consensus_llm_waiting', False):
            self.start_consensus_llm(self.llm_outputs)
            self.consensus_llm_waiting = False

    def update_llm_consensus(self, text):
        self.consensus_llm_label.setMarkdown(text)

    def _cleanup_threads(self):
        # Remove finished threads from the list
        self.llm_threads = [t for t in self.llm_threads if t.isRunning()]

    def closeEvent(self, event):
        # Gracefully stop all running threads
        for thread in self.llm_threads:
            thread.quit()
            thread.wait()
        event.accept()

    def start_consensus_llm(self, advisor_outputs):
        worker = ConsensusLLMWorker(advisor_outputs)
        worker.result_ready.connect(self.update_llm_consensus)
        worker.finished.connect(lambda: self._cleanup_threads())
        self.llm_threads.append(worker)
        worker.start()

# For standalone testing
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
