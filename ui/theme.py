from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt

def set_dark_theme(window):
    pass  # No-op, dark mode fully removed

def set_light_theme(window):
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor('#faf9f6'))
    palette.setColor(QPalette.WindowText, QColor('#000000'))
    palette.setColor(QPalette.Base, QColor('#faf9f6'))
    palette.setColor(QPalette.AlternateBase, QColor(245, 245, 245))
    palette.setColor(QPalette.ToolTipBase, QColor('#000000'))
    palette.setColor(QPalette.ToolTipText, QColor('#000000'))
    palette.setColor(QPalette.Text, QColor('#000000'))
    palette.setColor(QPalette.Button, QColor(240, 240, 240))
    palette.setColor(QPalette.ButtonText, QColor('#000000'))
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(0, 122, 204))
    palette.setColor(QPalette.Highlight, QColor(0, 122, 204))
    palette.setColor(QPalette.HighlightedText, Qt.white)
    window.setPalette(palette)
    font_family = "'Segoe UI Emoji', 'Noto Color Emoji', 'Apple Color Emoji', 'sans-serif'"
    window.centralWidget().setStyleSheet(f"""
        QWidget {{ background: #faf9f6; color: #000000; font-family: {font_family}; }}
        QTabWidget::pane {{ border: none; background: #faf9f6; }}
        QTabBar::tab {{ background: #e0e4ea; color: #000000; min-width: 33%; padding: 10px; font-weight: bold; border: 1px solid #bbb; border-bottom: none; border-radius: 6px 6px 0 0; }}
        QTabBar::tab:selected {{ background: #fff; color: #000000; }}
        QTabBar::tab:!selected {{ background: #e0e4ea; color: #555; }}
        QFrame[frameShape="4"] {{ background: #bbb; height: 2px; }}
        QLabel#consensusLabel {{ font-size: 15px; font-weight: bold; padding: 12px; background: #e0e4ea; border-radius: 8px; color: #000000; }}
        QLabel#insightsLabel, QLabel#predictionLabel {{ color: #000000; }}
    """)
