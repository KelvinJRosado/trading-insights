from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QMenuBar, QAction, QApplication, QComboBox, QHBoxLayout, QTabWidget, QTabWidget, QWidget, QVBoxLayout, QFrame, QSizePolicy, QSpacerItem, QScrollArea, QTextBrowser, QToolBox, QSizePolicy
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
import hashlib
import json

# Global LLM response cache
llm_cache = {}

class LLMWorker(QThread):
    result_ready = pyqtSignal(int, str)
    def __init__(self, idx, persona, all_method_insights, coin_name, llm_outputs, parent=None):
        super().__init__(parent)
        self.idx = idx
        self.persona = persona
        self.all_method_insights = all_method_insights
        self.coin_name = coin_name
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
        # Create cache key based on persona, coin, and all method insights hash
        cache_key = hashlib.md5(
            f"{self.persona}|{self.coin_name}|{str(self.all_method_insights)}".encode()
        ).hexdigest()
        
        # Check cache first
        if cache_key in llm_cache:
            return llm_cache[cache_key]
        
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
        
        # Format all method insights for the prompt
        insights_text = f"The cryptocurrency you are analyzing is {self.coin_name}.\n\n"
        insights_text += "You have access to analysis from multiple methods. Here are the insights from each:\n\n"
        
        for i, method_data in enumerate(self.all_method_insights):
            insights_text += f"Method {i+1} - {method_data['method']}:\n"
            insights_text += f"- Short-term: {method_data['short']}\n"
            insights_text += f"- Medium-term: {method_data['medium']}\n" 
            insights_text += f"- Long-term: {method_data['long']}\n"
            insights_text += f"- Buy recommendation: {method_data['buy']}\n"
            insights_text += f"- Sell recommendation: {method_data['sell']}\n"
            insights_text += f"- Overall suggestion: {method_data['suggestion']}\n"
            insights_text += f"- Reasoning: {method_data['reason']}\n\n"
        
        prompt = (
            f"{personality}\n\n"
            f"{insights_text}"
            "Your goal is to help your client make the greatest gains, but your advice should reflect your unique personality. "
            f"Please analyze all these different methods' insights about {self.coin_name} and provide your consolidated recommendation in simple, friendly English for a non-expert investor. "
            "Make sure your suggestions reflect your personal advisory style and consider the consensus and differences between the methods."
        )
        try:
            response = await ollama.AsyncClient().generate(model='llama3.2:latest', prompt=prompt)
            result = response['response'].strip()
            # Cache the result
            llm_cache[cache_key] = result
            return result
        except Exception as e:
            return f"[LLM error: {e}]"

class ConsensusLLMWorker(QThread):
    result_ready = pyqtSignal(str)
    def __init__(self, advisor_outputs, coin_name, parent=None):
        super().__init__(parent)
        self.advisor_outputs = advisor_outputs
        self.coin_name = coin_name
    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(self.call_ollama())
        self.result_ready.emit(result)
    async def call_ollama(self):
        # Create cache key based on all advisor outputs and coin name
        cache_key = hashlib.md5(
            f"consensus|{self.coin_name}|{'|'.join(self.advisor_outputs)}".encode()
        ).hexdigest()
        
        # Check cache first
        if cache_key in llm_cache:
            return llm_cache[cache_key]
        
        prompt = (
            f"You are a panel of financial advisors analyzing {self.coin_name}. Here are the opinions of three advisors: "
            f"\n\nAdvisor 1: {self.advisor_outputs[0]}\n\nAdvisor 2: {self.advisor_outputs[1]}\n\nAdvisor 3: {self.advisor_outputs[2]}\n\n"
            f"Please summarize the consensus about {self.coin_name} in simple, friendly English for a non-expert investor, focusing on maximizing gains."
        )
        try:
            response = await ollama.AsyncClient().generate(model='llama3.2:latest', prompt=prompt)
            result = response['response'].strip()
            # Cache the result
            llm_cache[cache_key] = result
            return result
        except Exception as e:
            return f"[LLM error: {e}]"

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.llm_threads = []  # Store references to all running LLM threads
        self.setWindowTitle("Trading Insights - Bitcoin")
        self.resize(1200, 900)  # Larger default window size
        self.central_widget = QWidget()
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.central_widget)
        self.setCentralWidget(self.scroll_area)
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
        self.layout.addSpacing(30)

        # Coin and Timeframe selectors on same row
        controls_layout = QHBoxLayout()
        
        # Coin selector
        coin_label = QLabel("Crypto:", self)
        coin_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.coin_combo = QComboBox(self)
        self.coin_combo.addItems(["Bitcoin (BTC)", "Ethereum (ETH)", "Dogecoin (DOGE)", "Solana (SOL)", "XRP (XRP)"])
        self.coin_combo.setCurrentText("Bitcoin (BTC)")
        self.coin_combo.currentTextChanged.connect(self.on_coin_changed)
        controls_layout.addWidget(coin_label)
        controls_layout.addWidget(self.coin_combo)
        
        # Add some space between the dropdowns
        controls_layout.addSpacing(20)
        
        # Timeframe selector
        timeframe_label = QLabel("Timeframe:", self)
        timeframe_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.timeframe_combo = QComboBox(self)
        self.timeframe_combo.addItems(["1h", "24h", "7d"])
        self.timeframe_combo.setCurrentText("24h")
        self.timeframe_combo.currentTextChanged.connect(self.on_timeframe_changed)
        controls_layout.addWidget(timeframe_label)
        controls_layout.addWidget(self.timeframe_combo)
        
        # Add stretch to push everything to the left
        controls_layout.addStretch()
        
        self.layout.addLayout(controls_layout)
        self.selected_coin = "bitcoin"  # Internal id for API

        # Price graph widget (more space)
        self.price_graph = PriceGraphWidget(self, dark_mode=False)
        self.price_graph.setMinimumHeight(350)
        self.price_graph.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.layout.addWidget(self.price_graph, stretch=2)
        self.layout.addSpacing(20)

        # Divider below graph
        self.divider1 = QFrame()
        self.divider1.setFrameShape(QFrame.HLine)
        self.divider1.setFrameShadow(QFrame.Sunken)
        self.divider1.setStyleSheet("color: #888; background: #888; height: 2px;")
        self.layout.addWidget(self.divider1)

        # Trading insights section (collapsible, hidden by default)
        self.suggestion_toolboxes = []
        advisor_names = ["Conservative Carl", "Aggressive Alex", "Balanced Bailey"]
        self.suggestion_tabs = QTabWidget(self)
        self.suggestion_tabs.setTabPosition(QTabWidget.North)
        self.suggestion_tabs.setTabShape(QTabWidget.Rounded)
        self.suggestion_tabs.setMovable(False)
        self.suggestion_tabs.setUsesScrollButtons(False)
        self.suggestion_tabs.setDocumentMode(True)
        self.suggestion_tabs.setTabBarAutoHide(False)
        self.suggestion_tabs.setStyleSheet("""
            QTabBar::tab {
                min-width: 220px;
                min-height: 44px;
                font-size: 18px;
                padding: 12px 24px;
                font-weight: bold;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #fff;
                color: #000;
            }
            QTabBar::tab:!selected {
                background: #e0e4ea;
                color: #555;
            }
            QTabWidget::pane { border: none; }
        """)
        self.suggestion_widgets = []
        self.llm_widgets = []
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
            toolbox.setVisible(False)  # Hidden by default
            # Add a button to expand/collapse
            from PyQt5.QtWidgets import QPushButton
            toggle_btn = QPushButton("Show Trading Insights")
            toggle_btn.setCheckable(True)
            toggle_btn.setChecked(False)
            def make_toggle(tb=toolbox, btn=toggle_btn):
                def toggle():
                    tb.setVisible(btn.isChecked())
                    btn.setText("Hide Trading Insights" if btn.isChecked() else "Show Trading Insights")
                return toggle
            toggle_btn.clicked.connect(make_toggle())
            tab.layout.addWidget(toggle_btn)
            tab.layout.addWidget(toolbox)
            # LLM output area (QTextBrowser, large font)
            right_browser = QTextBrowser()
            right_browser.setOpenExternalLinks(True)
            right_browser.setReadOnly(True)
            right_browser.setStyleSheet("font-size: 16px; padding: 8px 0 8px 16px; background: transparent; border: none; color: inherit;")
            right_browser.setMinimumHeight(250)
            right_browser.setMaximumHeight(400)
            right_browser.setTextInteractionFlags(Qt.TextSelectableByMouse)
            right_browser.setMarkdown("<span style='color:inherit;'><i>Loading advisor explanation...</i></span>")
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

        # Consensus section (collapsible, hidden by default)
        self.consensus_toggle_btn = QPushButton("Show Consensus Insights")
        self.consensus_toggle_btn.setCheckable(True)
        self.consensus_toggle_btn.setChecked(False)
        self.consensus_toggle_btn.clicked.connect(self.toggle_consensus_insights)
        self.layout.addWidget(self.consensus_toggle_btn)
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
        # Pass selected coin to data fetcher
        data = get_prices_for_timeframe(timeframe, coin_id=self.selected_coin)
        self.price_graph.plot_prices(data, title=f"{self.coin_combo.currentText()} Price ({timeframe})")
        # Compute and display trading insights
        prices = [price for _, price in data]
        insights = get_trading_insights(prices)
        self.display_insights(insights)
        self.display_suggestions_and_consensus(insights, prices)
        self.display_prediction(prices)

    def display_insights(self, insights):
        # Set the insights text in the currently selected tab's label
        idx = self.suggestion_tabs.currentIndex()
        if idx < 0 or idx >= len(self.suggestion_widgets):
            return
        label = self.suggestion_widgets[idx]
        if not insights or insights['high'] is None or insights['low'] is None:
            label.setText("No trading insights available.")
            return
        # Add tooltips for each metric
        high = f'<span title="Highest price in the selected timeframe">High: {insights["high"]:.2f}</span>'
        low = f'<span title="Lowest price in the selected timeframe">Low: {insights["low"]:.2f}</span>'
        rsi = f'<span title="Relative Strength Index (momentum indicator, <30=oversold, >70=overbought)">RSI: {insights["rsi_value"]:.2f} ({insights["rsi_signal"].capitalize()})</span>'
        ma = f'<span title="Moving Average (average price over a window)">MA: {insights["ma_value"]:.2f} ({insights["ma_signal"].capitalize()})</span>'
        text = (
            f"{high} &nbsp; {low} &nbsp; {rsi} &nbsp; {ma}"
        )
        label.setText(text)

    def display_suggestions_and_consensus(self, insights, prices):
        advisor_names = ["Conservative Carl", "Aggressive Alex", "Balanced Bailey"]
        methods = ["Technical Analysis", "Momentum Model", "Simple ML"]
        
        # First, generate insights for all methods
        all_method_insights = []
        for method in methods:
            suggestion, reason, st, mt, lt, buy, sell = self._generate_method_insights(insights, prices, method)
            all_method_insights.append({
                'short': st, 'medium': mt, 'long': lt, 'buy': buy, 'sell': sell, 
                'suggestion': suggestion, 'reason': reason, 'method': method
            })
        
        # Display each method's insights in the respective advisor tab and start LLM workers
        self._cleanup_threads()  # Clean up finished threads before starting new ones
        self.llm_outputs = [None, None, None]  # Store LLM outputs for consensus
        
        for i, advisor_name in enumerate(advisor_names):
            # Show the individual method that was originally assigned to this tab
            method_data = all_method_insights[i]
            left_text = (
                f"<b>Method:</b> {method_data['method']}<br>"
                f"<b>Short-term:</b> {method_data['short']}<br>"
                f"<b>Medium-term:</b> {method_data['medium']}<br>"
                f"<b>Long-term:</b> {method_data['long']}<br>"
                f"<b>Buy now:</b> {method_data['buy']}<br>"
                f"<b>Sell now:</b> {method_data['sell']}<br>"
                f"<b>Suggestion:</b> {method_data['suggestion']}<br>"
                f"<b>Reasoning:</b> {method_data['reason']}"
            )
            self.suggestion_widgets[i].setText(left_text)
            self.llm_widgets[i].setMarkdown("<span style='color:inherit;'><i>Loading advisor explanation...</i></span>")
            
            # Pass ALL method insights to each advisor
            worker = LLMWorker(i, advisor_name, all_method_insights, self.coin_combo.currentText(), self.llm_outputs, self)
            worker.result_ready.connect(self.update_llm_tab)
            worker.finished.connect(lambda: self._cleanup_threads())
            self.llm_threads.append(worker)
            worker.start()
        consensus = self._generate_consensus(all_method_insights)
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
        self.consensus_label.setVisible(False)
        self.consensus_toggle_btn.setChecked(False)
        self.consensus_toggle_btn.setText("Show Consensus Insights")
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

    def on_coin_changed(self, coin_name):
        # Map display name to API id
        coin_map = {
            "Bitcoin (BTC)": "bitcoin", 
            "Ethereum (ETH)": "ethereum",
            "Dogecoin (DOGE)": "dogecoin",
            "Solana (SOL)": "solana", 
            "XRP (XRP)": "ripple"
        }
        self.selected_coin = coin_map.get(coin_name, "bitcoin")
        self.load_price_data(self.timeframe_combo.currentText())

    def update_llm_tab(self, idx, text):
        self.llm_widgets[idx].setMarkdown(text)
        # If all advisor outputs are ready, trigger consensus LLM
        if hasattr(self, 'llm_outputs') and all(self.llm_outputs) and getattr(self, 'consensus_llm_waiting', False):
            self.start_consensus_llm(self.llm_outputs)
            self.consensus_llm_waiting = False

    def update_llm_consensus(self, text):
        self.consensus_llm_label.setMarkdown(text)

    def toggle_consensus_insights(self):
        show = self.consensus_toggle_btn.isChecked()
        self.consensus_label.setVisible(show)
        self.consensus_toggle_btn.setText("Hide Consensus Insights" if show else "Show Consensus Insights")

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
        worker = ConsensusLLMWorker(advisor_outputs, self.coin_combo.currentText())
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
