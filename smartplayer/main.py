from __future__ import annotations

import sys
import os
import argparse

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from .ui.mainwindow import MainWindow

_STYLESHEET = """
QMainWindow { background-color: #2b2b2b; }
QWidget { color: #dddddd; }
QMenuBar { background-color: #333333; }
QMenuBar::item:selected { background-color: #555555; }
QMenu { background-color: #333333; color: #dddddd; }
QMenu::item:selected { background-color: #555555; }
QTableView { 
    background-color: #2b2b2b; 
    alternate-background-color: #323232;
    gridline-color: #444444;
    selection-background-color: #444444;
    color: #dddddd;
    border: 1px solid #444444;
}
QHeaderView::section {
    background-color: #333333;
    color: #dddddd;
    border: 1px solid #444444;
    padding: 4px;
}
QPushButton {
    background-color: #444444;
    color: #dddddd;
    border: 1px solid #555555;
    padding: 6px 16px;
    border-radius: 3px;
}
QPushButton:hover { background-color: #555555; }
QPushButton:pressed { background-color: #666666; }
QSlider::groove:horizontal {
    background: #444444;
    height: 6px;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #888888;
    width: 14px;
    margin: -4px 0;
    border-radius: 7px;
}
QSpinBox, QDoubleSpinBox, QComboBox, QLineEdit, QTextEdit {
    background-color: #3c3c3c;
    color: #dddddd;
    border: 1px solid #555555;
    padding: 4px;
    border-radius: 3px;
}
QTabWidget::pane { border: 1px solid #444444; background-color: #2b2b2b; }
QTabBar::tab {
    background-color: #333333;
    color: #dddddd;
    padding: 6px 16px;
    border: 1px solid #444444;
}
QTabBar::tab:selected { background-color: #2b2b2b; }
QStatusBar { background-color: #333333; color: #dddddd; }
QLabel { color: #dddddd; }
QDialog { background-color: #2b2b2b; }
"""


def main():
    parser = argparse.ArgumentParser(description="SmartPlayer - Cue player for stage productions")
    parser.add_argument("-f", "--file", help="Session file to open")
    parser.add_argument("--version", action="store_true", help="Show version")
    args = parser.parse_args()

    if args.version:
        from . import __version__
        print(f"SmartPlayer v{__version__}")
        return

    app = QApplication(sys.argv)
    app.setApplicationName("SmartPlayer")
    app.setOrganizationName("SmartPlayer")
    app.setStyle("Fusion")
    app.setStyleSheet(_STYLESHEET)

    window = MainWindow()
    window.show()

    if args.file and os.path.exists(os.path.abspath(args.file)):
        window.load_session(os.path.abspath(args.file))

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
