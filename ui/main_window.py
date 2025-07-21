from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QMenuBar, QAction, QApplication, QComboBox, QHBoxLayout
from PyQt5.QtCore import Qt
from .theme import set_dark_theme, set_light_theme
from plots.price_graph import PriceGraphWidget
from data.fetch_prices import get_prices_for_timeframe

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

        # Placeholders for other sections
        self.insights_label = QLabel("[Trading Insights Placeholder]", self)
        self.insights_label.setAlignment(Qt.AlignCenter)
        self.news_label = QLabel("[News Section Placeholder]", self)
        self.news_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.insights_label)
        self.layout.addWidget(self.news_label)

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

    def on_timeframe_changed(self, timeframe):
        self.load_price_data(timeframe)

# For standalone testing
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
