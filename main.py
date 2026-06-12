# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""AKDev - entry point."""
import sys
from PySide6.QtWidgets import QApplication

from ui import theme
from ui.hub import HubWindow
from ui.win import MainWin


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("AKDev")
    app.setStyleSheet(theme.STYLESHEET)

    win = MainWin()
    hub = HubWindow()

    def enter_workspace():
        hub.hide()
        win.show()

    def on_new():
        enter_workspace()
        win.start_new_project()

    def on_open():
        enter_workspace()
        win.start_open_project()

    hub.new_project_requested.connect(on_new)
    hub.open_project_requested.connect(on_open)

    hub.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
