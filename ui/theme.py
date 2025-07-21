from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt

def set_dark_theme(window):
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(30, 30, 30))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(40, 40, 40))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(45, 45, 45))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    window.setPalette(palette)
    # Style all widgets for dark mode
    font_family = "'Segoe UI Emoji', 'Noto Color Emoji', 'Apple Color Emoji', 'sans-serif'"
    window.centralWidget().setStyleSheet(f"""
        QWidget {{ background: #232b36; color: #fff; font-family: {font_family}; }}
        QTabWidget::pane {{ border: none; background: #232b36; }}
        QTabBar::tab {{ background: #232b36; color: #fff; min-width: 33%; padding: 10px; font-weight: bold; border: 1px solid #444; border-bottom: none; border-radius: 6px 6px 0 0; }}
        QTabBar::tab:selected {{ background: #2d3a4a; color: #fff; }}
        QTabBar::tab:!selected {{ background: #232b36; color: #bbb; }}
        QFrame[frameShape="4"] {{ background: #888; height: 2px; }}
        QLabel#consensusLabel {{ font-size: 15px; font-weight: bold; padding: 12px; background: #232b36; border-radius: 8px; color: #fff; }}
        QLabel#insightsLabel, QLabel#predictionLabel {{ color: #fff; }}
    """)

def set_light_theme(window):
    palette = QPalette()
    palette.setColor(QPalette.Window, Qt.white)
    palette.setColor(QPalette.WindowText, Qt.black)
    palette.setColor(QPalette.Base, Qt.white)
    palette.setColor(QPalette.AlternateBase, QColor(245, 245, 245))
    palette.setColor(QPalette.ToolTipBase, Qt.black)
    palette.setColor(QPalette.ToolTipText, Qt.black)
    palette.setColor(QPalette.Text, Qt.black)
    palette.setColor(QPalette.Button, QColor(240, 240, 240))
    palette.setColor(QPalette.ButtonText, Qt.black)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(0, 122, 204))
    palette.setColor(QPalette.Highlight, QColor(0, 122, 204))
    palette.setColor(QPalette.HighlightedText, Qt.white)
    window.setPalette(palette)
    # Style all widgets for light mode
    font_family = "'Segoe UI Emoji', 'Noto Color Emoji', 'Apple Color Emoji', 'sans-serif'"
    window.centralWidget().setStyleSheet(f"""
        QWidget {{ background: #f5f7fa; color: #222; font-family: {font_family}; }}
        QTabWidget::pane {{ border: none; background: #f5f7fa; }}
        QTabBar::tab {{ background: #e0e4ea; color: #222; min-width: 33%; padding: 10px; font-weight: bold; border: 1px solid #bbb; border-bottom: none; border-radius: 6px 6px 0 0; }}
        QTabBar::tab:selected {{ background: #fff; color: #222; }}
        QTabBar::tab:!selected {{ background: #e0e4ea; color: #888; }}
        QFrame[frameShape="4"] {{ background: #bbb; height: 2px; }}
        QLabel#consensusLabel {{ font-size: 15px; font-weight: bold; padding: 12px; background: #e0e4ea; border-radius: 8px; color: #222; }}
        QLabel#insightsLabel, QLabel#predictionLabel {{ color: #222; }}
    """)
