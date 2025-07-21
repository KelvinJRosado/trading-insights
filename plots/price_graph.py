from PyQt5.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates

class PriceGraphWidget(QWidget):
    def __init__(self, parent=None, dark_mode=True):
        super().__init__(parent)
        self.dark_mode = dark_mode
        self.figure = Figure(figsize=(5, 3))
        self.canvas = FigureCanvas(self.figure)
        layout = QVBoxLayout(self)
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        self.ax = self.figure.add_subplot(111)
        self.figure.tight_layout()
        self.set_theme(self.dark_mode)

    def set_theme(self, dark_mode):
        self.dark_mode = dark_mode
        if dark_mode:
            self.figure.set_facecolor('#1e1e1e')
            self.ax.set_facecolor('#232323')
            self.ax.tick_params(colors='white', which='both')
            self.ax.spines['bottom'].set_color('white')
            self.ax.spines['top'].set_color('white')
            self.ax.spines['right'].set_color('white')
            self.ax.spines['left'].set_color('white')
            self.ax.title.set_color('white')
            self.ax.yaxis.label.set_color('white')
            self.ax.xaxis.label.set_color('white')
        else:
            self.figure.set_facecolor('#ffffff')
            self.ax.set_facecolor('#f5f5f5')
            self.ax.tick_params(colors='black', which='both')
            self.ax.spines['bottom'].set_color('black')
            self.ax.spines['top'].set_color('black')
            self.ax.spines['right'].set_color('black')
            self.ax.spines['left'].set_color('black')
            self.ax.title.set_color('black')
            self.ax.yaxis.label.set_color('black')
            self.ax.xaxis.label.set_color('black')
        self.canvas.draw()

    def plot_prices(self, data, title="Bitcoin Price"):
        """
        data: list of (datetime, price) tuples
        """
        self.ax.clear()
        if self.dark_mode:
            self.ax.set_facecolor('#232323')
        else:
            self.ax.set_facecolor('#f5f5f5')
        if data:
            dates, prices = zip(*data)
            self.ax.plot(dates, prices, color='#42a5f5', linewidth=2)
            self.ax.set_title(title)
            self.ax.set_xlabel("Time")
            self.ax.set_ylabel("Price (USD)")
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
            self.ax.xaxis.set_major_locator(mdates.AutoDateLocator())
            self.figure.autofmt_xdate()
        self.canvas.draw()
