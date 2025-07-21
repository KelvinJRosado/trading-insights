from PyQt5.QtWidgets import QWidget, QVBoxLayout, QToolTip
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

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
        self.data = []
        self._hover_cid = self.canvas.mpl_connect('motion_notify_event', self._on_hover)
        self._last_annotation = None

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
        self.data = data
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
        self.ax.grid(True)
        self.canvas.draw()

    def _on_hover(self, event):
        if not self.data or not event.inaxes:
            QToolTip.hideText()
            return
        # Find nearest data point
        dates, prices = zip(*self.data)
        if not dates:
            return
        xdata = mdates.date2num(dates)
        mouse_x = event.xdata
        if mouse_x is None:
            QToolTip.hideText()
            return
        idx = min(range(len(xdata)), key=lambda i: abs(xdata[i] - mouse_x))
        dt = dates[idx]
        price = prices[idx]
        tooltip_text = f"{dt.strftime('%Y-%m-%d %H:%M')}: ${price:,.2f}"
        QToolTip.showText(self.mapToGlobal(self.canvas.pos()) + event.guiEvent.pos(), tooltip_text, self)
