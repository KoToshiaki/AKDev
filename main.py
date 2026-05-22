# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""AKDev - entry point."""
import sys
from PySide6.QtWidgets import QApplication
from ui.win import MainWin


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("AKDev")
    win = MainWin()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
