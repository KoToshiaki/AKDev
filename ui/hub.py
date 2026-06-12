# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""AKDev Hub — startup entry screen.

The Hub is the entry point shown before the Workspace. It lets the user
create or open a project and previews future entry points (recent projects,
templates, documentation). New / Open are exposed as signals so the host
(``main.py``) wires them to the existing project handlers in ``MainWin``.

This is a v0.5 prototype: Recent Projects is an empty placeholder and the
Templates cards have no behavior yet.
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QPushButton, QLabel, QFrame,
    QVBoxLayout, QHBoxLayout, QGridLayout, QSizePolicy,
)

from ui import theme


def _section_label(text: str) -> QLabel:
    lbl = QLabel(text)
    f = lbl.font()
    f.setPointSize(f.pointSize() + 1)
    f.setBold(True)
    lbl.setFont(f)
    return lbl


class _TemplateCard(QFrame):
    """A non-functional template card (prototype placeholder)."""

    def __init__(self, title: str, desc: str, enabled: bool = True):
        super().__init__()
        self.setObjectName("TemplateCard")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setMinimumSize(160, 90)
        self.title = title
        lay = QVBoxLayout(self)
        name = QLabel(title)
        nf = name.font()
        nf.setBold(True)
        name.setFont(nf)
        body = QLabel(desc)
        body.setWordWrap(True)
        body.setStyleSheet(f"color: {theme.TEXT_DIM};")
        lay.addWidget(name)
        lay.addWidget(body)
        lay.addStretch()
        self.setEnabled(enabled)


class HubWindow(QWidget):
    """Startup hub. Emits signals when the user picks New / Open."""

    new_project_requested = Signal()
    open_project_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{theme.APP_NAME} — Hub")
        self.resize(720, 560)

        root = QVBoxLayout(self)
        root.setContentsMargins(40, 32, 40, 32)
        root.setSpacing(18)

        # --- Title block -------------------------------------------------
        title = QLabel(theme.APP_NAME)
        tf = QFont(title.font())
        tf.setPointSize(34)
        tf.setBold(True)
        title.setFont(tf)
        title.setStyleSheet(f"color: {theme.ACCENT_HOVER};")

        subtitle = QLabel(theme.APP_TAGLINE)
        subtitle.setStyleSheet(f"color: {theme.TEXT_DIM};")

        root.addWidget(title)
        root.addWidget(subtitle)

        # --- Primary actions --------------------------------------------
        actions = QHBoxLayout()
        self._btn_new = QPushButton("+  New Project")
        self._btn_new.setObjectName("PrimaryButton")
        self._btn_new.setMinimumHeight(40)
        self._btn_open = QPushButton("Open Project")
        self._btn_open.setMinimumHeight(40)
        self._btn_new.clicked.connect(self.new_project_requested)
        self._btn_open.clicked.connect(self.open_project_requested)
        actions.addWidget(self._btn_new)
        actions.addWidget(self._btn_open)
        actions.addStretch()
        root.addLayout(actions)

        # --- Recent Projects (empty placeholder) ------------------------
        root.addWidget(_section_label("Recent Projects"))
        self._recent = QLabel("（なし — 最近開いたプロジェクトはここに表示されます）")
        self._recent.setStyleSheet(f"color: {theme.TEXT_DIM};")
        root.addWidget(self._recent)

        # --- Templates (cards only, no behavior yet) --------------------
        root.addWidget(_section_label("Templates"))
        cards = QGridLayout()
        self._template_cards = [
            _TemplateCard("AK32 Baremetal", "自作 AK32 CPU の最小プロジェクト"),
            _TemplateCard("Empty", "空のプロジェクト"),
            _TemplateCard("Coming soon", "テンプレートは今後追加されます", enabled=False),
        ]
        for i, card in enumerate(self._template_cards):
            cards.addWidget(card, 0, i)
        root.addLayout(cards)

        # --- Documentation / Quick Start --------------------------------
        root.addWidget(_section_label("Documentation / Quick Start"))
        docs = QLabel(
            "• Quick Start — docs/QUICKSTART.md\n"
            "• User Guide — docs/USER_GUIDE.md"
        )
        docs.setStyleSheet(f"color: {theme.TEXT_DIM};")
        root.addWidget(docs)

        root.addStretch()

    # ---- accessors (used by tests / host) ------------------------------

    def template_titles(self) -> list[str]:
        return [c.title for c in self._template_cards]
