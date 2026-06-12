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

# PATCH_WIRE_STYLE_V05: compact wire color palette + width presets (no assets).
_WIRE_PALETTE = [
    "#66ccff", "#88ddaa", "#ffcc66", "#ff8888", "#ffee66", "#88aaff",
    "#cc88ff", "#ff88cc", "#ffffff", "#bbbbbb", "#888888", "#333333",
]
_WIRE_WIDTHS = [1.0, 2.0, 3.0, 5.0]


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
    # Wire style (PATCH_WIRE_STYLE_V05): (conn_id, hex) — empty hex = default color.
    wire_color_changed = Signal(str, str)
    wire_width_changed = Signal(str, float)
    wire_style_reset   = Signal(str)
    # Program sources (PATCH_PART_PROGRAM_ASSIGN_V05): (node_id, source_type).
    source_set_requested   = Signal(str, str)
    source_clear_requested = Signal(str, str)
    source_open_requested  = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._node_id = ""
        self._conn_id = ""
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

        # Wire section (PATCH_WIRE_STYLE_V05): shown only when a wire is selected.
        self._wire_box = self._build_wire_box()
        outer.addWidget(self._wire_box)
        self._wire_box.hide()

        # Program / Sources section (PATCH_PART_PROGRAM_ASSIGN_V05): node only.
        self._program_box = self._build_program_box()
        outer.addWidget(self._program_box)
        self._program_box.hide()

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

    # ----------------------------------------------------------------- wire box

    def _build_wire_box(self) -> QWidget:
        box = QWidget()
        lay = QVBoxLayout(box)
        lay.setContentsMargins(0, 4, 0, 0)
        lay.setSpacing(4)

        title = QLabel("Wire")
        title.setStyleSheet("font-weight: bold; color: #555;")
        lay.addWidget(title)

        # Info rows are rebuilt per selection.
        self._wire_info = QFormLayout()
        self._wire_info.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        lay.addLayout(self._wire_info)

        pal = QLabel("Color")
        pal.setStyleSheet("font-weight: bold; color: #555; margin-top: 4px;")
        lay.addWidget(pal)

        grid = QGridLayout()
        grid.setSpacing(2)
        self._wire_swatches: list[QPushButton] = []
        for i, hexc in enumerate(_WIRE_PALETTE):
            btn = QPushButton()
            btn.setFixedSize(16, 16)
            btn.setToolTip(hexc)
            btn.setStyleSheet(
                f"QPushButton {{ background: {hexc}; border: 1px solid #888; }}"
                f"QPushButton:hover {{ border: 2px solid #222; }}"
            )
            btn.clicked.connect(lambda _=False, h=hexc: self._on_wire_swatch(h))
            grid.addWidget(btn, i // 6, i % 6)
            self._wire_swatches.append(btn)
        lay.addLayout(grid)

        wlbl = QLabel("Width")
        wlbl.setStyleSheet("font-weight: bold; color: #555; margin-top: 4px;")
        lay.addWidget(wlbl)
        wrow = QHBoxLayout()
        for w in _WIRE_WIDTHS:
            b = QPushButton(f"{w:g}")
            b.setFixedWidth(28)
            b.clicked.connect(lambda _=False, ww=w: self._on_wire_width(ww))
            wrow.addWidget(b)
        wrow.addStretch()
        lay.addLayout(wrow)

        row = QHBoxLayout()
        default_btn = QPushButton("Default color")
        default_btn.clicked.connect(lambda: self._on_wire_swatch(""))
        row.addWidget(default_btn)
        reset_btn = QPushButton("Reset Style")
        reset_btn.clicked.connect(self._on_wire_reset)
        row.addWidget(reset_btn)
        row.addStretch()
        lay.addLayout(row)
        return box

    def _on_wire_swatch(self, hexc: str):
        if self._conn_id:
            self.wire_color_changed.emit(self._conn_id, hexc)

    def _on_wire_width(self, width: float):
        if self._conn_id:
            self.wire_width_changed.emit(self._conn_id, float(width))

    def _on_wire_reset(self):
        if self._conn_id:
            self.wire_style_reset.emit(self._conn_id)

    def wire_palette_size(self) -> int:
        """Number of wire color swatches (for tests)."""
        return len(self._wire_swatches)

    @staticmethod
    def _endpoint_text(side: dict) -> str:
        node = side.get("node_id", "?")
        port = side.get("logical_port") or side.get("port", "")
        vp   = side.get("visual_port_id", "")
        txt = node
        if port:
            txt += f" : {port}"
        if vp:
            txt += f"  ({vp})"
        return txt

    # -------------------------------------------------------------- program box

    def _build_program_box(self) -> QWidget:
        box = QWidget()
        lay = QVBoxLayout(box)
        lay.setContentsMargins(0, 4, 0, 0)
        lay.setSpacing(4)

        title = QLabel("Program / Sources")
        title.setStyleSheet("font-weight: bold; color: #555;")
        lay.addWidget(title)

        # Per-type value label + action buttons. ROM is display + Clear only.
        self._src_value: dict = {}
        for st, label, with_open in (("asm", "ASM", True),
                                     ("hdl", "HDL", True),
                                     ("rom", "ROM", False)):
            row_lbl = QLabel(label)
            row_lbl.setStyleSheet("font-weight: bold; margin-top: 2px;")
            lay.addWidget(row_lbl)
            val = QLabel("(none)")
            val.setStyleSheet("color: #666;")
            val.setWordWrap(True)
            lay.addWidget(val)
            self._src_value[st] = val
            btns = QHBoxLayout()
            set_b = QPushButton(f"Set {label}...")
            set_b.clicked.connect(lambda _=False, t=st: self._on_source_set(t))
            btns.addWidget(set_b)
            clr_b = QPushButton("Clear")
            clr_b.clicked.connect(lambda _=False, t=st: self._on_source_clear(t))
            btns.addWidget(clr_b)
            if with_open:
                open_b = QPushButton("Open")
                open_b.clicked.connect(lambda _=False, t=st: self._on_source_open(t))
                btns.addWidget(open_b)
            btns.addStretch()
            lay.addLayout(btns)

        # Loaded-to-circuit state (PATCH_CIRCUIT_WRITE_RUN_HELLO_V05).
        self._loaded_lbl = QLabel("Loaded: No")
        self._loaded_lbl.setStyleSheet("margin-top: 4px; color: #555;")
        self._loaded_lbl.setWordWrap(True)
        lay.addWidget(self._loaded_lbl)
        return box

    def _on_source_set(self, source_type: str):
        if self._node_id:
            self.source_set_requested.emit(self._node_id, source_type)

    def _on_source_clear(self, source_type: str):
        if self._node_id:
            self.source_clear_requested.emit(self._node_id, source_type)

    def _on_source_open(self, source_type: str):
        if self._node_id:
            self.source_open_requested.emit(self._node_id, source_type)

    @staticmethod
    def _source_text(val) -> str:
        if isinstance(val, dict):
            val = val.get("path")
        return str(val) if val else "(none)"

    def _fill_program_box(self, sources: "dict | None", loaded: "dict | None" = None):
        sources = sources or {}
        for st, lbl in self._src_value.items():
            lbl.setText(self._source_text(sources.get(st)))
        if loaded and loaded.get("status") == "loaded":
            tgt  = loaded.get("target_node_id", "")
            prog = str(loaded.get("path", "")).replace("\\", "/").rsplit("/", 1)[-1]
            self._loaded_lbl.setText(
                f"Loaded: Yes\nLoaded Target: {tgt}\nLoaded Program: {prog}"
            )
        else:
            self._loaded_lbl.setText("Loaded: No")

    # ------------------------------------------------------------------ public

    def show_none(self):
        self._node_id = ""
        self._conn_id = ""
        self._header.setText("(no selection)")
        self._header.setStyleSheet("font-style: italic; color: #888;")
        self._body.hide()
        self._visual_box.hide()
        self._wire_box.hide()
        self._program_box.hide()

    def show_multi(self, count: int):
        self._node_id = ""
        self._conn_id = ""
        self._header.setText(f"{count} items selected")
        self._header.setStyleSheet("font-style: italic; color: #888;")
        self._body.hide()
        self._visual_box.hide()
        self._wire_box.hide()
        self._program_box.hide()

    def show_part(self, part: dict, node_id: str = "", sources: "dict | None" = None,
                  loaded: "dict | None" = None):
        self._node_id = node_id
        self._conn_id = ""
        self._header.setText(part.get("name", "?"))
        self._header.setStyleSheet("font-weight: bold; font-size: 11px;")
        self._rebuild_form(part, node_id)
        self._body.show()
        self._wire_box.hide()
        self._visual_box.setVisible(bool(node_id))
        self._fill_program_box(sources, loaded)
        self._program_box.setVisible(bool(node_id))

    def show_wire(self, conn: dict):
        """Display a selected wire's info + style editing (PATCH_WIRE_STYLE_V05)."""
        self._node_id = ""
        self._conn_id = conn.get("id", "")
        self._header.setText("Wire")
        self._header.setStyleSheet("font-weight: bold; font-size: 11px;")
        self._body.hide()
        self._visual_box.hide()
        self._program_box.hide()

        while self._wire_info.rowCount():
            self._wire_info.removeRow(0)
        style = conn.get("style") or {}
        color = style.get("color", "")
        width = style.get("width")
        rows = [
            ("ID",    conn.get("id", "")),
            ("Kind",  conn.get("kind", "")),
            ("From",  self._endpoint_text(conn.get("from", {}))),
            ("To",    self._endpoint_text(conn.get("to", {}))),
            ("Color", color if color else "(kind default)"),
            ("Width", f"{width:g}" if width is not None else "(kind default)"),
        ]
        for label, value in rows:
            lbl = QLabel(label)
            lbl.setStyleSheet("font-weight: bold;")
            val = QLabel(str(value))
            val.setWordWrap(True)
            self._wire_info.addRow(lbl, val)

        self._wire_box.show()

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
