# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""Ribbon-style command bar: category tabs + horizontal button row."""
from PySide6.QtWidgets import (
    QWidget, QTabBar, QStackedWidget,
    QHBoxLayout, QVBoxLayout, QToolButton,
)
from PySide6.QtCore import Qt

# v0.5 Patch 2: buttons size to their content (compact) instead of being
# stretched edge-to-edge. Width 0 => natural sizeHint; only a modest minimum
# height is enforced for clickability.
_BTN_MIN_W = 0
_BTN_MIN_H = 28
_RIBBON_MIN_H = 56


class RibbonBar(QWidget):
    """Category-tab command bar.

    Usage::
        ribbon = RibbonBar()
        ribbon.add_page("File", [action_new, action_open, action_save])
        ribbon.add_page("Tools", [])   # empty placeholder
    """

    def __init__(self, parent=None, *,
                 button_min_width: int = _BTN_MIN_W,
                 button_min_height: int = _BTN_MIN_H,
                 ribbon_min_height: int = _RIBBON_MIN_H):
        super().__init__(parent)
        self._btn_min_w = button_min_width
        self._btn_min_h = button_min_height
        self._page_actions: list[list] = []

        self._tab_bar = QTabBar()
        self._stack = QStackedWidget()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._tab_bar)
        layout.addWidget(self._stack)
        self._tab_bar.currentChanged.connect(self._stack.setCurrentIndex)
        self.setMinimumHeight(ribbon_min_height)

    def add_page(self, title: str, actions: list) -> None:
        """Add a ribbon page with a tab label and a row of tool buttons."""
        page = QWidget()
        row = QHBoxLayout(page)
        row.setContentsMargins(6, 2, 6, 2)
        row.setSpacing(2)
        for action in actions:
            btn = QToolButton()
            btn.setDefaultAction(action)
            btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
            # Compact: natural width (unless a positive min width was requested),
            # only a modest min height. Left-packed via the trailing stretch.
            if self._btn_min_w > 0:
                btn.setMinimumWidth(self._btn_min_w)
            btn.setMinimumHeight(self._btn_min_h)
            row.addWidget(btn, 0, Qt.AlignmentFlag.AlignLeft)
        row.addStretch()
        self._tab_bar.addTab(title)
        self._stack.addWidget(page)
        self._page_actions.append(list(actions))

    def page_count(self) -> int:
        return self._tab_bar.count()

    def page_title(self, idx: int) -> str:
        return self._tab_bar.tabText(idx)

    def page_action_texts(self, idx: int) -> list[str]:
        """Return the text of every action on the given page."""
        return [a.text() for a in self._page_actions[idx]]

    def button_min_size(self) -> tuple[int, int]:
        """Return (min_width, min_height) applied to each ribbon button."""
        return (self._btn_min_w, self._btn_min_h)
