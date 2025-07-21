from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QMenuBar, QAction, QStackedWidget, QApplication
from PyQt5.QtCore import Qt
from .theme import set_dark_theme, set_light_theme

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

        # Placeholders for sections
        self.price_graph_label = QLabel("[Price Graph Placeholder]", self)
        self.price_graph_label.setAlignment(Qt.AlignCenter)
        self.insights_label = QLabel("[Trading Insights Placeholder]", self)
        self.insights_label.setAlignment(Qt.AlignCenter)
        self.news_label = QLabel("[News Section Placeholder]", self)
        self.news_label.setAlignment(Qt.AlignCenter)

        self.layout.addWidget(self.price_graph_label)
        self.layout.addWidget(self.insights_label)
        self.layout.addWidget(self.news_label)

        set_dark_theme(self)

    def set_dark_mode(self):
        self.dark_action.setChecked(True)
        self.light_action.setChecked(False)
        set_dark_theme(self)

    def set_light_mode(self):
        self.dark_action.setChecked(False)
        self.light_action.setChecked(True)
        set_light_theme(self)

# For standalone testing
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
