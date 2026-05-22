"""Main window — stub for Phase 1."""
from PySide6.QtWidgets import QMainWindow, QLabel
from PySide6.QtCore import Qt


class MainWin(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AKDev")
        self.resize(1280, 800)
        label = QLabel("AKDev — starting up…", alignment=Qt.AlignCenter)
        self.setCentralWidget(label)
