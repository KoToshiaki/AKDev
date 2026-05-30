# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""Headless tests for Canvas UX Patch 1A: add_part_at / add_part / drag-drop API."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF

_app = QApplication.instance() or QApplication(sys.argv)

from ui.canvas import Canvas, PartNode

_PART_A = {"id": "cpu.ak32", "name": "AK32",  "category": "cpu"}
_PART_B = {"id": "mem.ram",  "name": "RAM",   "category": "mem"}
_PART_C = {"id": "io.uart",  "name": "UART",  "category": "io"}


def _make_canvas() -> Canvas:
    logs: list[str] = []
    return Canvas(log_fn=logs.append)


# ---------------------------------------------------------------------------
# add_part_at — position and export
# ---------------------------------------------------------------------------

def test_add_part_at_position():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(100.0, 200.0))
    parts = canvas.export_parts()
    assert len(parts) == 1
    assert parts[0]["x"] == 100.0
    assert parts[0]["y"] == 200.0


def test_add_part_at_part_id_recorded():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    parts = canvas.export_parts()
    assert parts[0]["part_id"] == "cpu.ak32"


def test_add_part_at_included_in_export():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(30.0, 40.0))
    ids = {p["part_id"] for p in canvas.export_parts()}
    assert "cpu.ak32" in ids


def test_add_part_at_multiple_parts_all_exported():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0,   0.0))
    canvas.add_part_at(_PART_B, QPointF(100.0, 0.0))
    parts = canvas.export_parts()
    assert len(parts) == 2
    ids = {p["part_id"] for p in parts}
    assert "cpu.ak32" in ids
    assert "mem.ram" in ids


def test_add_part_at_node_seq_increments():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    canvas.add_part_at(_PART_B, QPointF(50.0, 50.0))
    parts = canvas.export_parts()
    node_ids = {p["node_id"] for p in parts}
    assert len(node_ids) == 2  # distinct IDs

def test_add_part_at_places_partnode_in_scene():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    items = canvas.scene().items()
    assert any(isinstance(i, PartNode) for i in items)


# ---------------------------------------------------------------------------
# add_part — viewport-centre placement with _add_offset
# ---------------------------------------------------------------------------

def test_add_part_offset_cycles_after_8():
    """After 8 consecutive add_part() calls _add_offset resets to 0."""
    canvas = _make_canvas()
    for _ in range(8):
        canvas.add_part(_PART_A)
    assert canvas._add_offset == 0


def test_add_part_consecutive_positions_differ_by_20px():
    """Two consecutive add_part() calls produce positions 20 px apart."""
    canvas = _make_canvas()
    canvas.add_part(_PART_A)
    canvas.add_part(_PART_B)
    parts = canvas.export_parts()
    assert len(parts) == 2
    xs = sorted(p["x"] for p in parts)
    ys = sorted(p["y"] for p in parts)
    assert xs[1] - xs[0] == pytest.approx(20.0)
    assert ys[1] - ys[0] == pytest.approx(20.0)


def test_add_part_offset_advances_each_call():
    """_add_offset increments by 1 on every add_part() call."""
    canvas = _make_canvas()
    assert canvas._add_offset == 0
    canvas.add_part(_PART_A)
    assert canvas._add_offset == 1
    canvas.add_part(_PART_B)
    assert canvas._add_offset == 2


# ---------------------------------------------------------------------------
# set_part_library
# ---------------------------------------------------------------------------

def test_set_part_library_stores_mapping():
    canvas = _make_canvas()
    lib = {"cpu.ak32": _PART_A, "mem.ram": _PART_B}
    canvas.set_part_library(lib)
    assert canvas._part_library == lib


def test_set_part_library_replaces_previous():
    canvas = _make_canvas()
    canvas.set_part_library({"cpu.ak32": _PART_A})
    canvas.set_part_library({"mem.ram": _PART_B})
    assert "cpu.ak32" not in canvas._part_library
    assert "mem.ram" in canvas._part_library


# ---------------------------------------------------------------------------
# export_parts round-trip for drag-placed nodes (no-UI equivalent)
# ---------------------------------------------------------------------------

def test_export_parts_sources_default_none():
    """Nodes added via add_part_at have sources = {asm: None, hdl: None}."""
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    part = canvas.export_parts()[0]
    assert part["sources"] == {"asm": None, "hdl": None}
