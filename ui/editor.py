# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""EditorTabs — closable part-editor tab widget."""
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QTabWidget, QTextEdit


class EditorTabs(QTabWidget):
    """Central tab editor. One tab per (node_id, ext) pair; no duplicates."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTabsClosable(True)
        self.setMovable(True)
        self.tabCloseRequested.connect(self._close_tab)
        self._open: dict[tuple[str, str], QTextEdit] = {}  # (node_id, ext) -> widget

    # ------------------------------------------------------------------ public

    def open_tab(self, part: dict, node_id: str, ext: str) -> str | None:
        """Open (or focus) a tab for the given node + extension.

        Returns the tab name if a new tab was created, None if already open.
        """
        key = (node_id, ext)
        if key in self._open:
            self.setCurrentWidget(self._open[key])
            return None

        tab_name = f"{part['name']} [{node_id}].{ext}"
        editor = QTextEdit()
        editor.setPlaceholderText(f"# {tab_name}\n")
        editor.setFont(QFont("Courier New", 10))
        self.addTab(editor, tab_name)
        self._open[key] = editor
        self.setCurrentWidget(editor)
        return tab_name

    # ------------------------------------------------------------------ private

    def _close_tab(self, index: int):
        widget = self.widget(index)
        key_to_remove = next(
            (k for k, w in self._open.items() if w is widget), None
        )
        if key_to_remove:
            del self._open[key_to_remove]
        self.removeTab(index)
