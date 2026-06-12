# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""Properties panel — selected PartNode details + Visual (color) editing."""
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QFrame,
    QScrollArea, QFormLayout, QPushButton,
)

# PATCH_PART_VISUAL_V05: ~100-swatch palette generated in code (no assets).
_PALETTE_COLS = 10
_PALETTE_ROWS = 10


def _palette_colors() -> list[str]:
    """Return ~100 hex colors: a grayscale row + hue rows at varying brightness."""
    colors: list[str] = []
    # Row 0: grayscale ramp.
    for c in range(_PALETTE_COLS):
        v = round(255 * c / (_PALETTE_COLS - 1))
        colors.append(QColor(v, v, v).name())
    # Rows 1..N: hue across columns, brightness ramp down the rows.
    for r in range(1, _PALETTE_ROWS):
        val = round(255 * (_PALETTE_ROWS - r) / (_PALETTE_ROWS - 1))
        for c in range(_PALETTE_COLS):
            hue = round(360 * c / _PALETTE_COLS) % 360
            colors.append(QColor.fromHsv(hue, 220, max(50, val)).name())
    return colors


class PropPanel(QWidget):
    """Right-side panel: part info + a Visual section to recolor the node."""

    # (node_id, hex) — empty hex means "revert to category default".
    color_changed = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._node_id = ""
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

        # Visual section (kept outside the rebuilt form so swatches persist).
        self._visual_box = self._build_visual_box()
        outer.addWidget(self._visual_box)
        self._visual_box.hide()

    # --------------------------------------------------------------- visual box

    def _build_visual_box(self) -> QWidget:
        box = QWidget()
        lay = QVBoxLayout(box)
        lay.setContentsMargins(0, 4, 0, 0)
        lay.setSpacing(4)

        title = QLabel("Visual")
        title.setStyleSheet("font-weight: bold; color: #555;")
        lay.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(2)
        self._swatches: list[QPushButton] = []
        for i, hexc in enumerate(_palette_colors()):
            btn = QPushButton()
            btn.setFixedSize(16, 16)
            btn.setToolTip(hexc)
            btn.setStyleSheet(
                f"QPushButton {{ background: {hexc}; border: 1px solid #888; }}"
                f"QPushButton:hover {{ border: 2px solid #222; }}"
            )
            btn.clicked.connect(lambda _=False, h=hexc: self._on_swatch(h))
            grid.addWidget(btn, i // _PALETTE_COLS, i % _PALETTE_COLS)
            self._swatches.append(btn)
        lay.addLayout(grid)

        row = QHBoxLayout()
        default_btn = QPushButton("Default color")
        default_btn.clicked.connect(lambda: self._on_swatch(""))
        row.addWidget(default_btn)
        row.addStretch()
        lay.addLayout(row)
        return box

    def _on_swatch(self, hexc: str):
        if self._node_id:
            self.color_changed.emit(self._node_id, hexc)

    def palette_size(self) -> int:
        """Number of color swatches (for tests)."""
        return len(self._swatches)

    # ------------------------------------------------------------------ public

    def show_none(self):
        self._node_id = ""
        self._header.setText("(no selection)")
        self._header.setStyleSheet("font-style: italic; color: #888;")
        self._body.hide()
        self._visual_box.hide()

    def show_multi(self, count: int):
        self._node_id = ""
        self._header.setText(f"{count} items selected")
        self._header.setStyleSheet("font-style: italic; color: #888;")
        self._body.hide()
        self._visual_box.hide()

    def show_part(self, part: dict, node_id: str = ""):
        self._node_id = node_id
        self._header.setText(part.get("name", "?"))
        self._header.setStyleSheet("font-weight: bold; font-size: 11px;")
        self._rebuild_form(part, node_id)
        self._body.show()
        self._visual_box.setVisible(bool(node_id))

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
