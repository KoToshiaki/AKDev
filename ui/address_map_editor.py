# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""Address Map Editor (PATCH_ADDRESS_MAP_EDITOR_V08).

A read+edit Dock that shows the resolved Address Map and lets the user override a
device's ``base`` / ``size`` (auto -> manual) on top of the MemoryLayout's automatic
placement.  Edits are validated (range / overlap / alignment) before Apply; with no
manual overrides the behaviour is identical to the current automatic layout.

The heavy lifting (override apply + validation) lives in ``core.devices`` /
``core.circuit`` as pure functions; this panel is the thin UI around them and the
MainWin integration methods (``address_editor_data`` / ``validate_address_map_overrides``
/ ``apply_address_map_overrides`` / ``reset_address_map_overrides``).
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem,
)
from PySide6.QtCore import Qt

from core.devices import parse_address_int

# Column layout (exposed for tests).
COL_NODE, COL_PART, COL_KIND, COL_ROLE, COL_MODE = 0, 1, 2, 3, 4
COL_BASE, COL_SIZE, COL_END, COL_RUNTIME, COL_OVERLAY, COL_STATUS = 5, 6, 7, 8, 9, 10
_HEADERS = ["node", "part", "kind", "role", "mode", "base", "size", "end",
            "runtime", "overlay", "status"]
_EDITABLE = (COL_MODE, COL_BASE, COL_SIZE)


def _hex(v) -> str:
    return f"0x{v:04x}" if isinstance(v, int) else str(v)


class AddressMapEditor(QDockWidget):
    """Dock panel: view the Address Map and edit per-device base/size overrides."""

    def __init__(self, win, parent: "QWidget | None" = None):
        super().__init__("Address Map", parent)
        self._win = win
        self.setAllowedAreas(
            Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea
            | Qt.BottomDockWidgetArea | Qt.TopDockWidgetArea
        )
        body = QWidget()
        layout = QVBoxLayout(body)

        self._status_lbl = QLabel("")
        layout.addWidget(self._status_lbl)

        self._table = QTableWidget(0, len(_HEADERS))
        self._table.setHorizontalHeaderLabels(_HEADERS)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.itemChanged.connect(self._on_item_changed)
        layout.addWidget(self._table)

        row = QHBoxLayout()
        self._apply_btn = QPushButton("Apply")
        self._reset_btn = QPushButton("Reset to Auto")
        self._refresh_btn = QPushButton("Refresh")
        self._apply_btn.clicked.connect(self._on_apply)
        self._reset_btn.clicked.connect(self._on_reset)
        self._refresh_btn.clicked.connect(self.refresh)
        for b in (self._apply_btn, self._reset_btn, self._refresh_btn):
            row.addWidget(b)
        layout.addLayout(row)

        self.setWidget(body)
        self._specs: list = []
        self._suspend = False     # guard itemChanged during programmatic fills
        self.refresh()

    # ------------------------------------------------------------------ data

    def refresh(self) -> None:
        """Reload the table from the MainWin's current auto specs + overrides."""
        specs, overrides, _layout = self._win.address_editor_data()
        self._specs = specs
        self._suspend = True
        self._table.setRowCount(len(specs))
        for r, s in enumerate(specs):
            nid = s.get("node_id")
            ov = overrides.get(nid) or {}
            manual = ov.get("mode") == "manual"
            base = ov.get("base") if manual else s.get("base")
            size = ov.get("size") if manual else s.get("size")
            end = (base + size - 1) if isinstance(base, int) and isinstance(size, int) else None
            vals = {
                COL_NODE: str(nid), COL_PART: str(s.get("label") or s.get("part_id") or ""),
                COL_KIND: str(s.get("kind")), COL_ROLE: str(s.get("role")),
                COL_MODE: "manual" if manual else "auto",
                COL_BASE: _hex(base), COL_SIZE: _hex(size), COL_END: _hex(end),
                COL_RUNTIME: "yes" if s.get("runtime_backed") else "no",
                COL_OVERLAY: str(s.get("overlay") or "-"), COL_STATUS: "",
            }
            for c, text in vals.items():
                item = QTableWidgetItem(text)
                if c not in _EDITABLE:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self._table.setItem(r, c, item)
        self._suspend = False
        self._preview()

    # --------------------------------------------------- collect / validate

    def collect_overrides(self):
        """Read the table into an overrides dict. Returns ``(overrides, parse_issues)``."""
        overrides: dict = {}
        parse_issues: list = []
        for r in range(self._table.rowCount()):
            mode = (self._table.item(r, COL_MODE).text() or "").strip().lower()
            nid = self._table.item(r, COL_NODE).text()
            if mode != "manual":
                continue
            try:
                base = parse_address_int(self._table.item(r, COL_BASE).text())
                size = parse_address_int(self._table.item(r, COL_SIZE).text())
            except ValueError:
                parse_issues.append({
                    "severity": "error", "code": "ADDRESS_INPUT_INVALID",
                    "message": f"{nid}: base/size is not a valid number",
                    "details": {"node": nid},
                })
                continue
            overrides[nid] = {"mode": "manual", "base": base, "size": size}
        return overrides, parse_issues

    def _preview(self) -> list:
        """Validate the current table state, update status cells, toggle Apply."""
        overrides, parse_issues = self.collect_overrides()
        issues = list(parse_issues)
        if not parse_issues:
            issues += self._win.validate_address_map_overrides(overrides)
        self._show_issues(issues)
        return issues

    def _show_issues(self, issues: list) -> None:
        by_node: dict = {}
        for i in issues:
            nid = i.get("details", {}).get("node")
            if nid is not None:
                by_node.setdefault(nid, []).append(i)
        self._suspend = True
        for r in range(self._table.rowCount()):
            nid = self._table.item(r, COL_NODE).text()
            ni = by_node.get(nid, [])
            if any(x["severity"] == "error" for x in ni):
                txt = "error: " + ",".join(x["code"] for x in ni if x["severity"] == "error")
            elif ni:
                txt = "warn: " + ",".join(x["code"] for x in ni)
            else:
                txt = "ok"
            self._table.item(r, COL_STATUS).setText(txt)
        self._suspend = False
        n_err = sum(1 for i in issues if i["severity"] == "error")
        n_warn = sum(1 for i in issues if i["severity"] == "warning")
        self._status_lbl.setText(
            "OK" if not issues else f"{n_err} error(s), {n_warn} warning(s)"
        )
        self.has_errors = n_err > 0
        self._apply_btn.setEnabled(not self.has_errors)

    # ------------------------------------------------------------- actions

    def _on_item_changed(self, _item) -> None:
        if not self._suspend:
            self._preview()

    def _on_apply(self) -> None:
        overrides, parse_issues = self.collect_overrides()
        issues = list(parse_issues)
        if not parse_issues:
            issues += self._win.validate_address_map_overrides(overrides)
        if any(i["severity"] == "error" for i in issues):
            self._show_issues(issues)
            return            # blocked — do not apply
        self._win.apply_address_map_overrides(overrides)
        self.refresh()

    def _on_reset(self) -> None:
        self._win.reset_address_map_overrides()
        self.refresh()
