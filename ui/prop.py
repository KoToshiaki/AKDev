# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""Properties panel — displays selected PartNode details (read-only)."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QScrollArea, QFormLayout,
)


class PropPanel(QWidget):
    """Right-side panel that shows part information for the selected canvas node."""

    def __init__(self, parent=None):
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(6)

        self._header = QLabel("(no selection)")
        self._header.setStyleSheet("font-style: italic; color: #888;")
        outer.addWidget(self._header)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        outer.addWidget(sep)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        outer.addWidget(scroll)

        self._body = QWidget()
        self._form = QFormLayout(self._body)
        self._form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        self._form.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow
        )
        self._form.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(self._body)
        self._body.hide()

    # ------------------------------------------------------------------ public

    def show_none(self):
        self._header.setText("(no selection)")
        self._header.setStyleSheet("font-style: italic; color: #888;")
        self._body.hide()

    def show_multi(self, count: int):
        self._header.setText(f"{count} items selected")
        self._header.setStyleSheet("font-style: italic; color: #888;")
        self._body.hide()

    def show_part(self, part: dict, node_id: str = ""):
        self._header.setText(part.get("name", "?"))
        self._header.setStyleSheet("font-weight: bold; font-size: 11px;")
        self._rebuild_form(part, node_id)
        self._body.show()

    # ------------------------------------------------------------------ private

    def _rebuild_form(self, part: dict, node_id: str):
        while self._form.rowCount():
            self._form.removeRow(0)

        if node_id:
            self._add_row("Node", node_id)
        self._add_row("ID", part.get("id", ""))
        self._add_row("Category", part.get("category", ""))
        desc = part.get("description", "")
        if desc:
            self._add_row("Description", desc)

        ports = part.get("ports", [])
        if ports:
            self._add_section("Ports")
            for p in ports:
                self._form.addRow(QLabel(f"  {p['name']}: {p['type']}"))

        resources = part.get("resources", {})
        if resources:
            self._add_section("Resources")
            for key, val in resources.items():
                self._add_row(f"  {key}", str(val))

    def _add_row(self, label: str, value: str):
        lbl = QLabel(label)
        lbl.setStyleSheet("font-weight: bold;")
        val = QLabel(str(value))
        val.setWordWrap(True)
        self._form.addRow(lbl, val)

    def _add_section(self, title: str):
        sec = QLabel(title)
        sec.setStyleSheet("font-weight: bold; margin-top: 6px; color: #555;")
        self._form.addRow(sec)
