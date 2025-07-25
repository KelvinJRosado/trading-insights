from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QMenuBar, QAction, QApplication, QComboBox, QHBoxLayout, QTabWidget, QTabWidget, QWidget, QVBoxLayout, QFrame, QSizePolicy, QSpacerItem, QScrollArea, QTextBrowser, QToolBox, QSizePolicy, QPushButton
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from .theme import set_dark_theme, set_light_theme
from plots.price_graph import PriceGraphWidget
from data.fetch_prices import get_prices_for_timeframe, get_ohlcv_for_timeframe
from analysis.insights import get_trading_insights
from analysis.enhanced_insights import get_enhanced_trading_insights
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
        
        # Format all method insights for the prompt (raw values only)
        insights_text = f"The cryptocurrency you are analyzing is {self.coin_name}.\n\n"
        insights_text += "You have access to raw indicator values from multiple methods. Here are the raw values from each method:\n\n"
        
        for i, method_data in enumerate(self.all_method_insights):
            insights_text += f"Method {i+1} - {method_data['method']}:\n"
            insights_text += f"- High: {method_data.get('high', 'N/A')}\n"
            insights_text += f"- Low: {method_data.get('low', 'N/A')}\n"
            insights_text += f"- RSI: {method_data.get('rsi_value', 'N/A')}\n"
            insights_text += f"- MA: {method_data.get('ma_value', 'N/A')}\n"
            insights_text += f"- OHLCV array: {len(method_data.get('ohlcv_array', []))} data points\n\n"
        
        prompt = (
            f"{personality}\n\n"
            f"{insights_text}"
            "Your goal is to help your client make the greatest gains, but your advice should reflect your unique personality. "
            f"Please analyze all these different methods' raw indicator values about {self.coin_name} and provide your consolidated recommendation in simple, friendly English for a non-expert investor. "
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
        self.timeframe_combo.addItems(["1h", "24h", "7d", "30d"])
        self.timeframe_combo.setCurrentText("7d")
        self.timeframe_combo.currentTextChanged.connect(self.on_timeframe_changed)
        controls_layout.addWidget(timeframe_label)
        controls_layout.addWidget(self.timeframe_combo)
        
        # Add stretch to push everything to the left
        controls_layout.addStretch()
        
        self.layout.addLayout(controls_layout)
        self.selected_coin = "bitcoin"  # Internal id for API

        # Price chart section (collapsible)
        self.chart_toggle_btn = QPushButton("Hide Price Chart")
        self.chart_toggle_btn.setCheckable(True)
        self.chart_toggle_btn.setChecked(True)  # Expanded by default
        self.chart_toggle_btn.clicked.connect(self.toggle_price_chart)
        self.layout.addWidget(self.chart_toggle_btn)
        
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

        # Advisor analysis section (collapsible)  
        self.advisors_toggle_btn = QPushButton("Hide Advisor Analysis")
        self.advisors_toggle_btn.setCheckable(True)
        self.advisors_toggle_btn.setChecked(True)  # Expanded by default
        self.advisors_toggle_btn.clicked.connect(self.toggle_advisor_section)
        self.layout.addWidget(self.advisors_toggle_btn)

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
            # Remove the QToolBox and toggle button for trading insights
            # Only add the LLM output area
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
            self.llm_widgets.append(right_browser)
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

        # Prediction section (collapsible)
        self.prediction_toggle_btn = QPushButton("Hide Price Prediction")
        self.prediction_toggle_btn.setCheckable(True)
        self.prediction_toggle_btn.setChecked(True)  # Expanded by default
        self.prediction_toggle_btn.clicked.connect(self.toggle_prediction_section)
        self.layout.addWidget(self.prediction_toggle_btn)
        
        self.prediction_label = QLabel("[Prediction Placeholder]", self)
        self.prediction_label.setAlignment(Qt.AlignCenter)
        self.prediction_label.setWordWrap(True)
        self.prediction_label.setObjectName("predictionLabel")
        self.prediction_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.layout.addWidget(self.prediction_label)

        # Set background color for main window
        self.central_widget.setStyleSheet("background: #faf9f6;")

        set_light_theme(self)
        self.load_price_data("7d")

    def set_dark_mode(self):
        pass  # No-op

    def set_light_mode(self):
        set_light_theme(self)
        self.price_graph.set_theme(False)

    def load_chart_data(self, timeframe="7d"):
        """Load and display chart data for the selected timeframe (visual only)"""
        data = get_prices_for_timeframe(timeframe, coin_id=self.selected_coin)
        self.price_graph.plot_prices(data, title=f"{self.coin_combo.currentText()} Price ({timeframe})")
    
    def load_insights_data(self):
        """Load and calculate insights using the best available data"""
        # Try to get longer-term data for better insights, with multiple fallbacks
        insights_data = None
        timeframes = ["30d", "7d", "24h"]
        for timeframe in timeframes:
            try:
                insights_data = get_ohlcv_for_timeframe(timeframe, coin_id=self.selected_coin)
                if insights_data and len(insights_data) >= 10:
                    break
            except Exception as e:
                print(f"Failed to fetch {timeframe} data: {e}")
                continue
        if not insights_data:
            print("Warning: Using mock data for insights calculation")
        prices = [candle[4] for candle in insights_data] if insights_data else []
        if len(prices) < 5:
            print("Insufficient data for analysis")
            return
        # Use get_trading_insights for technical, get_enhanced_trading_insights for ML
        insights = get_trading_insights(prices, insights_data)
        enhanced_ml_insights = get_enhanced_trading_insights(self.selected_coin, "7d")  # Use 7d for ML by default
        # self.display_insights(insights)  # REMOVE THIS LINE
        self.display_suggestions_and_consensus(insights, prices, enhanced_ml_insights)
        self.display_prediction(prices)

    # Remove the display_insights method entirely

    def display_suggestions_and_consensus(self, insights, prices, enhanced_ml_insights=None):
        advisor_names = ["Conservative Carl", "Aggressive Alex", "Balanced Bailey"]
        methods = ["Technical Analysis", "Enhanced ML Analysis", "Momentum Model", "Llama Analysis"]
        all_method_insights = []
        for method in methods:
            if method == "Enhanced ML Analysis" and enhanced_ml_insights is not None:
                # Pass only raw values for advisors
                all_method_insights.append({
                    'method': method,
                    'high': enhanced_ml_insights.get('high'),
                    'low': enhanced_ml_insights.get('low'),
                    'rsi_value': enhanced_ml_insights.get('rsi_value'),
                    'ma_value': enhanced_ml_insights.get('ma_value'),
                    'ohlcv_array': enhanced_ml_insights.get('ohlcv_array'),
                })
            else:
                all_method_insights.append({
                    'method': method,
                    'high': insights.get('high'),
                    'low': insights.get('low'),
                    'rsi_value': insights.get('rsi_value'),
                    'ma_value': insights.get('ma_value'),
                    'ohlcv_array': insights.get('ohlcv_array'),
                })
        # Display each method's raw insights in the respective advisor tab
        for i, advisor_name in enumerate(advisor_names):
            method_data = all_method_insights[i]
            left_text = (
                f"<b>Method:</b> {method_data['method']}<br>"
                f"<b>High:</b> {method_data['high']}<br>"
                f"<b>Low:</b> {method_data['low']}<br>"
                f"<b>RSI:</b> {method_data['rsi_value']}<br>"
                f"<b>MA:</b> {method_data['ma_value']}<br>"
                f"<b>OHLCV array:</b> {len(method_data['ohlcv_array'])} data points<br>"
            )
            self.llm_widgets[i].setMarkdown("<span style='color:inherit;'><i>Loading advisor explanation...</i></span>")
        # Consensus and LLM logic can be updated similarly if needed
        
        # Display each method's insights in the respective advisor tab and start LLM workers
        self._cleanup_threads()  # Clean up finished threads before starting new ones
        self.llm_outputs = [None, None, None]  # Store LLM outputs for consensus
        
        for i, advisor_name in enumerate(advisor_names):
            # Show the individual method that was originally assigned to this tab
            method_data = all_method_insights[i]
            left_text = (
                f"<b>Method:</b> {method_data['method']}<br>"
                f"<b>High:</b> {method_data['high']}<br>"
                f"<b>Low:</b> {method_data['low']}<br>"
                f"<b>RSI:</b> {method_data['rsi_value']}<br>"
                f"<b>MA:</b> {method_data['ma_value']}<br>"
                f"<b>OHLCV array:</b> {len(method_data['ohlcv_array'])} data points<br>"
            )
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
            f"<b>High:</b> {consensus['high']:.2f}<br>"
            f"<b>Low:</b> {consensus['low']:.2f}<br>"
            f"<b>RSI:</b> {consensus['rsi_value']:.2f}<br>"
            f"<b>MA:</b> {consensus['ma_value']:.2f}<br>"
            f"<b>OHLCV array:</b> {len(consensus['ohlcv_array'])} data points<br>"
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
        """Generate insights using four truly different analysis methods"""
        
        if method == "Technical Analysis":
            return self._technical_analysis_method(insights, prices)
        elif method == "Momentum Model":
            return self._momentum_analysis_method(insights, prices)
        elif method == "Simple ML":
            return self._ml_analysis_method(insights, prices)
        elif method == "Llama Analysis":
            return self._llama_analysis_method(insights, prices)
        else:
            # Fallback
            return "Hold", "Unknown method", "Uncertain", "Uncertain", "Uncertain", "No", "No"
    
    def _technical_analysis_method(self, insights, prices):
        """Traditional technical analysis using RSI and MA"""
        rsi = insights.get('rsi_signal', 'unknown')
        rsi_val = insights.get('rsi_value') or 50.0  # Default to 50 if None
        ma = insights.get('ma_signal', 'unknown')
        ma_val = insights.get('ma_value') or (sum(prices[-14:]) / len(prices[-14:]) if len(prices) >= 14 else prices[-1] if prices else 0)
        
        # Technical analysis is strict about thresholds
        if rsi == 'buy' and ma == 'buy':
            suggestion = f"<span style='color:#4caf50;'>Strong Buy [BUY]</span>"
            reason = f"Both RSI ({rsi_val:.1f}) and MA confirm oversold conditions with upward momentum"
            st, mt, lt = "Bullish reversal", "Upward trend likely", "Depends on fundamentals"
            buy, sell = "Yes [YES]", "No [NO]"
        elif rsi == 'sell' and ma == 'sell':
            suggestion = f"<span style='color:#e53935;'>Strong Sell [SELL]</span>"
            reason = f"Both RSI ({rsi_val:.1f}) and MA indicate overbought with downward momentum"
            st, mt, lt = "Bearish reversal", "Downward trend likely", "Market correction expected"
            buy, sell = "No [NO]", "Yes [YES]"
        elif rsi == 'buy' or ma == 'buy':
            suggestion = f"<span style='color:#81c784;'>Cautious Buy [BUY]</span>"
            reason = f"Mixed signals: RSI={rsi}, MA={ma}. One indicator suggests buying opportunity"
            st, mt, lt = "Possible uptick", "Sideways with upside bias", "Neutral to positive"
            buy, sell = "Yes [YES]", "No [NO]"
        elif rsi == 'sell' or ma == 'sell':
            suggestion = f"<span style='color:#ffab91;'>Cautious Sell [SELL]</span>"
            reason = f"Mixed signals: RSI={rsi}, MA={ma}. One indicator suggests selling"
            st, mt, lt = "Possible dip", "Sideways with downside risk", "Neutral to negative"
            buy, sell = "No [NO]", "Yes [YES]"
        else:
            suggestion = f"<span style='color:#ffb300;'>Hold [HOLD]</span>"
            reason = f"RSI ({rsi_val:.1f}) and MA in neutral zone - no clear technical signals"
            st, mt, lt = "Range-bound", "Consolidation phase", "Awaiting breakout"
            buy, sell = "No [NO]", "No [NO]"
        
        return suggestion, reason, st, mt, lt, buy, sell
    
    def _momentum_analysis_method(self, insights, prices):
        """Momentum-based analysis focusing on price velocity and acceleration"""
        if len(prices) < 10:
            return "Hold", "Insufficient data", "Unknown", "Unknown", "Unknown", "No", "No"
        
        # Calculate price momentum metrics
        recent_prices = prices[-10:]  # Last 10 periods
        price_change_5d = (prices[-1] - prices[-6]) / prices[-6] * 100 if len(prices) >= 6 and prices[-6] != 0 else 0
        price_change_2d = (prices[-1] - prices[-3]) / prices[-3] * 100 if len(prices) >= 3 and prices[-3] != 0 else 0
        
        # Momentum acceleration (change in momentum)
        momentum_recent = price_change_2d
        momentum_older = (prices[-5] - prices[-10]) / prices[-10] * 100 if len(prices) >= 10 and prices[-10] != 0 else 0
        momentum_acceleration = momentum_recent - momentum_older
        
        # Volatility (as risk measure)
        volatility = np.std(recent_prices) / np.mean(recent_prices) * 100 if len(recent_prices) > 1 else 0
        
        # Momentum-based decision logic
        if price_change_5d > 5 and momentum_acceleration > 0:
            suggestion = f"<span style='color:#4caf50;'>Momentum Buy [STRONG]</span>"
            reason = f"Strong upward momentum: +{price_change_5d:.1f}% with accelerating trend"
            st, mt, lt = "Continuation expected", "Strong uptrend", "Momentum-driven growth"
            buy, sell = "Yes [YES]", "No [NO]"
        elif price_change_5d < -5 and momentum_acceleration < 0:
            suggestion = f"<span style='color:#e53935;'>Momentum Sell [STRONG]</span>"
            reason = f"Strong downward momentum: {price_change_5d:.1f}% with accelerating decline"
            st, mt, lt = "Further decline likely", "Downtrend continues", "Bearish momentum"
            buy, sell = "No [NO]", "Yes [YES]"
        elif price_change_2d > 2:
            suggestion = f"<span style='color:#81c784;'>Momentum Buy [MODERATE]</span>"
            reason = f"Recent upward momentum: +{price_change_2d:.1f}% in short term"
            st, mt, lt = "Short-term bullish", "Monitor for continuation", "Depends on sustained momentum"
            buy, sell = "Yes [YES]", "No [NO]"
        elif price_change_2d < -2:
            suggestion = f"<span style='color:#ffab91;'>Momentum Sell [MODERATE]</span>"
            reason = f"Recent downward momentum: {price_change_2d:.1f}% suggests weakness"
            st, mt, lt = "Short-term bearish", "Watch for reversal", "Risk of continued decline"
            buy, sell = "No [NO]", "Yes [YES]"
        else:
            suggestion = f"<span style='color:#ffb300;'>Momentum Hold [WAIT]</span>"
            reason = f"Low momentum ({price_change_2d:.1f}%), high volatility ({volatility:.1f}%)"
            st, mt, lt = "Sideways movement", "Low conviction period", "Await momentum shift"
            buy, sell = "No [NO]", "No [NO]"
        
        return suggestion, reason, st, mt, lt, buy, sell
    
    def _ml_analysis_method(self, insights, prices):
        """DEPRECATED: Use _enhanced_ml_analysis_method instead for advisors"""
        return "See Enhanced ML Analysis", "Use the new ML system for advisor logic", "-", "-", "-", "-", "-"
    
    def _llama_analysis_method(self, insights, prices):
        """AI-powered analysis using Llama to analyze raw price data"""
        if len(prices) < 10:
            return "Hold", "Insufficient data for AI analysis", "Unknown", "Unknown", "Unknown", "No", "No"
        
        # Prepare price data for Llama analysis
        recent_prices = prices[-20:] if len(prices) >= 20 else prices  # Last 20 periods or all available
        price_changes = []
        for i in range(1, len(recent_prices)):
            change = (recent_prices[i] - recent_prices[i-1]) / recent_prices[i-1] * 100
            price_changes.append(change)
        
        # Create a data summary for Llama
        current_price = recent_prices[-1]
        avg_price = sum(recent_prices) / len(recent_prices)
        min_price = min(recent_prices)
        max_price = max(recent_prices)
        total_change = (recent_prices[-1] - recent_prices[0]) / recent_prices[0] * 100
        volatility = (max_price - min_price) / avg_price * 100
        
        # Format data for Llama prompt
        data_summary = f"""
Price Analysis Data:
- Current Price: ${current_price:.2f}
- Period Average: ${avg_price:.2f}
- Range: ${min_price:.2f} - ${max_price:.2f}
- Total Change: {total_change:+.2f}%
- Volatility: {volatility:.1f}%
- Recent Price Changes (%): {', '.join([f'{x:+.1f}' for x in price_changes[-10:]])}
- Data Points: {len(recent_prices)} periods
"""

        prompt = f"""You are a financial analyst. Analyze this cryptocurrency price data and provide trading insights.

{data_summary}

Based on this data, provide your analysis in EXACTLY this format:

Short-term outlook: [your assessment]
Medium-term outlook: [your assessment] 
Long-term outlook: [your assessment]
Buy recommendation: [Yes/No with brief reason]
Sell recommendation: [Yes/No with brief reason]
Overall suggestion: [Buy/Sell/Hold with confidence level]
Reasoning: [2-3 sentence explanation of your analysis]

Be concise and focus on what the price patterns suggest."""

        try:
            # Make synchronous call to Llama (using the async client in sync mode)
            import asyncio
            
            async def get_llama_analysis():
                try:
                    response = await ollama.AsyncClient().generate(model='llama3.2:latest', prompt=prompt)
                    return response['response'].strip()
                except Exception as e:
                    return f"AI analysis unavailable: {e}"
            
            # Run the async function synchronously
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            llama_response = loop.run_until_complete(get_llama_analysis())
            loop.close()
            
            # Parse Llama's response to extract structured data
            return self._parse_llama_response(llama_response, current_price, total_change)
            
        except Exception as e:
            # Fallback to rule-based analysis if Llama fails
            return self._fallback_ai_analysis(total_change, volatility, current_price, avg_price)
    
    def _parse_llama_response(self, response, current_price, total_change):
        """Parse Llama's response into structured format"""
        lines = response.split('\n')
        
        # Initialize defaults
        st = "AI assessment pending"
        mt = "AI assessment pending" 
        lt = "AI assessment pending"
        buy = "No [AI]"
        sell = "No [AI]"
        suggestion = f"<span style='color:#ffb300;'>AI Hold [ANALYZING]</span>"
        reason = "AI analysis in progress"
        
        # Parse response line by line
        for line in lines:
            line = line.strip().lower()
            if "short-term" in line:
                st = line.split(":", 1)[1].strip() if ":" in line else st
            elif "medium-term" in line:
                mt = line.split(":", 1)[1].strip() if ":" in line else mt
            elif "long-term" in line:
                lt = line.split(":", 1)[1].strip() if ":" in line else lt
            elif "buy recommendation" in line:
                buy_text = line.split(":", 1)[1].strip() if ":" in line else ""
                buy = "Yes [AI]" if "yes" in buy_text else "No [AI]"
            elif "sell recommendation" in line:
                sell_text = line.split(":", 1)[1].strip() if ":" in line else ""
                sell = "Yes [AI]" if "yes" in sell_text else "No [AI]"
            elif "overall suggestion" in line:
                suggestion_text = line.split(":", 1)[1].strip() if ":" in line else ""
                if "buy" in suggestion_text:
                    suggestion = f"<span style='color:#4caf50;'>AI Buy [RECOMMENDED]</span>"
                elif "sell" in suggestion_text:
                    suggestion = f"<span style='color:#e53935;'>AI Sell [RECOMMENDED]</span>"
                else:
                    suggestion = f"<span style='color:#ffb300;'>AI Hold [NEUTRAL]</span>"
            elif "reasoning" in line:
                reason = line.split(":", 1)[1].strip() if ":" in line else reason
        
        # Add price context to reasoning
        price_context = f"Current: ${current_price:.2f}, Change: {total_change:+.1f}%"
        reason = f"AI Analysis - {reason} ({price_context})"
        
        return suggestion, reason, st, mt, lt, buy, sell
    
    def _fallback_ai_analysis(self, total_change, volatility, current_price, avg_price):
        """Fallback analysis when Llama is unavailable"""
        # Simple rule-based fallback
        if total_change > 10 and volatility < 20:
            suggestion = f"<span style='color:#4caf50;'>AI Buy [FALLBACK]</span>"
            reason = f"Fallback AI: Strong upward trend ({total_change:+.1f}%) with moderate volatility"
            st, mt, lt = "Bullish pattern", "Upward momentum", "Positive trend"
            buy, sell = "Yes [AI]", "No [AI]"
        elif total_change < -10 and volatility < 20:
            suggestion = f"<span style='color:#e53935;'>AI Sell [FALLBACK]</span>"
            reason = f"Fallback AI: Strong downward trend ({total_change:+.1f}%) suggests weakness"
            st, mt, lt = "Bearish pattern", "Downward pressure", "Negative trend"
            buy, sell = "No [AI]", "Yes [AI]"
        else:
            suggestion = f"<span style='color:#ffb300;'>AI Hold [FALLBACK]</span>"
            reason = f"Fallback AI: Mixed signals, change: {total_change:+.1f}%, volatility: {volatility:.1f}%"
            st, mt, lt = "Unclear pattern", "Mixed signals", "Neutral outlook"
            buy, sell = "No [AI]", "No [AI]"
        
        return suggestion, reason, st, mt, lt, buy, sell

    def _generate_consensus(self, all_suggestions):
        # Consensus for raw values: use mean for numeric, union for arrays
        def mean(values):
            vals = [v for v in values if v is not None]
            return sum(vals) / len(vals) if vals else None

        consensus = {
            'method': 'Consensus',
            'high': mean([s.get('high') for s in all_suggestions]),
            'low': mean([s.get('low') for s in all_suggestions]),
            'rsi_value': mean([s.get('rsi_value') for s in all_suggestions]),
            'ma_value': mean([s.get('ma_value') for s in all_suggestions]),
            'ohlcv_array': sum([s.get('ohlcv_array', []) for s in all_suggestions], []),
        }
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
        # Prediction is always based on 30-day data analysis
        tf_label = "(based on 30-day analysis)"
        self.prediction_label.setText(
            f"<b>Predicted next price {tf_label}:</b> ${predicted_price:,.2f} ({direction}, {pct_change:+.2f}%)"
        )

    def on_timeframe_changed(self, timeframe):
        # Only update chart display, don't recalculate insights
        self.load_chart_data(timeframe)

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
    
    def toggle_price_chart(self):
        show = self.chart_toggle_btn.isChecked()
        self.price_graph.setVisible(show)
        self.divider1.setVisible(show)
        self.chart_toggle_btn.setText("Hide Price Chart" if show else "Show Price Chart")
    
    def toggle_advisor_section(self):
        show = self.advisors_toggle_btn.isChecked()
        self.suggestion_tabs.setVisible(show)
        self.divider3.setVisible(show)
        self.advisors_toggle_btn.setText("Hide Advisor Analysis" if show else "Show Advisor Analysis")
    
    def toggle_prediction_section(self):
        show = self.prediction_toggle_btn.isChecked()
        self.prediction_label.setVisible(show)
        self.prediction_toggle_btn.setText("Hide Price Prediction" if show else "Show Price Prediction")

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

    def _enhanced_ml_analysis_method(self, enhanced_ml_insights):
        """Use the enhanced ML analysis and pass raw data to advisors"""
        ml_analysis = enhanced_ml_insights.get('ml_analysis', {})
        ml_signals = enhanced_ml_insights.get('ml_signals', {})
        confidence = enhanced_ml_insights.get('ml_confidence', 0)
        technical_summary = enhanced_ml_insights.get('technical_summary', '')
        # Instead of buy/sell, just summarize the numbers for the advisors
        suggestion = f"<span style='color:#2196f3;'>ML Model Outputs</span>"
        reason = f"Raw ML predictions: {ml_analysis.get('predictions', {})}, Model scores: {ml_analysis.get('model_scores', {})}, Confidence: {confidence:.2f}"
        st = f"ML signals: {ml_signals}"
        mt = f"Feature importance: {ml_analysis.get('feature_importance', {})}"
        lt = technical_summary
        buy = "(see raw data)"
        sell = "(see raw data)"
        return suggestion, reason, st, mt, lt, buy, sell, {'ml_analysis': ml_analysis, 'ml_signals': ml_signals, 'confidence': confidence}

    def load_price_data(self, timeframe="7d"):
        """Load both chart and insights data (used for initial load and coin changes)"""
        self.load_chart_data(timeframe)
        self.load_insights_data()

# For standalone testing
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
