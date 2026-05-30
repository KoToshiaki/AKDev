# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""Headless tests for Canvas Snap to Grid."""
import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF

_app = QApplication.instance() or QApplication(sys.argv)

from ui.canvas import Canvas, GridScene, PartNode

_PART_A = {"id": "cpu.ak32", "name": "AK32", "category": "cpu"}
_PART_B = {"id": "mem.ram",  "name": "RAM",  "category": "mem"}
_G      = GridScene.GRID_SIZE   # 20


def _make_canvas() -> Canvas:
    logs: list[str] = []
    return Canvas(log_fn=logs.append)


# ---------------------------------------------------------------------------
# Default state
# ---------------------------------------------------------------------------

def test_canvas_snap_default_off():
    canvas = _make_canvas()
    assert canvas._snap_enabled is False


def test_partnode_snap_default_off():
    node = PartNode(_PART_A, "n0001")
    assert node._snap_enabled is False


# ---------------------------------------------------------------------------
# Canvas.set_snap
# ---------------------------------------------------------------------------

def test_set_snap_true_updates_canvas_flag():
    canvas = _make_canvas()
    canvas.set_snap(True)
    assert canvas._snap_enabled is True


def test_set_snap_false_updates_canvas_flag():
    canvas = _make_canvas()
    canvas.set_snap(True)
    canvas.set_snap(False)
    assert canvas._snap_enabled is False


def test_set_snap_propagates_to_existing_nodes():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    canvas.add_part_at(_PART_B, QPointF(100.0, 0.0))
    canvas.set_snap(True)
    for item in canvas.scene().items():
        if isinstance(item, PartNode):
            assert item._snap_enabled is True


def test_set_snap_false_propagates_to_existing_nodes():
    canvas = _make_canvas()
    canvas.set_snap(True)
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    canvas.set_snap(False)
    for item in canvas.scene().items():
        if isinstance(item, PartNode):
            assert item._snap_enabled is False


# ---------------------------------------------------------------------------
# add_part_at — position snapping
# ---------------------------------------------------------------------------

def test_add_part_at_snap_on_rounds_to_grid():
    canvas = _make_canvas()
    canvas.set_snap(True)
    # 13.7 → round(13.7/20)*20 = 1*20 = 20
    # 8.3  → round(8.3/20)*20  = 0*20 = 0
    canvas.add_part_at(_PART_A, QPointF(13.7, 8.3))
    parts = canvas.export_parts()
    assert parts[0]["x"] == pytest.approx(20.0)
    assert parts[0]["y"] == pytest.approx(0.0)


def test_add_part_at_snap_on_exact_grid_unchanged():
    canvas = _make_canvas()
    canvas.set_snap(True)
    canvas.add_part_at(_PART_A, QPointF(40.0, 60.0))
    parts = canvas.export_parts()
    assert parts[0]["x"] == pytest.approx(40.0)
    assert parts[0]["y"] == pytest.approx(60.0)


def test_add_part_at_snap_off_preserves_fractional_position():
    canvas = _make_canvas()
    canvas.set_snap(False)
    canvas.add_part_at(_PART_A, QPointF(13.7, 8.3))
    parts = canvas.export_parts()
    assert parts[0]["x"] == pytest.approx(13.7)
    assert parts[0]["y"] == pytest.approx(8.3)


def test_add_part_at_snap_new_node_gets_snap_state():
    canvas = _make_canvas()
    canvas.set_snap(True)
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    nodes = [i for i in canvas.scene().items() if isinstance(i, PartNode)]
    assert len(nodes) == 1
    assert nodes[0]._snap_enabled is True


def test_add_part_at_no_snap_new_node_has_snap_false():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    nodes = [i for i in canvas.scene().items() if isinstance(i, PartNode)]
    assert nodes[0]._snap_enabled is False


# ---------------------------------------------------------------------------
# PartNode.itemChange — snap rounding during drag
# ---------------------------------------------------------------------------

def test_itemchange_snap_on_rounds_position():
    node = PartNode(_PART_A, "n0001")
    node.set_snap(True)
    # round(13.0/20)*20 = round(0.65)*20 = 1*20 = 20
    # round(38.0/20)*20 = round(1.9)*20  = 2*20 = 40
    result = node.itemChange(
        PartNode.GraphicsItemChange.ItemPositionChange,
        QPointF(13.0, 38.0),
    )
    assert result.x() == pytest.approx(20.0)
    assert result.y() == pytest.approx(40.0)


def test_itemchange_snap_off_preserves_position():
    node = PartNode(_PART_A, "n0001")
    node.set_snap(False)
    result = node.itemChange(
        PartNode.GraphicsItemChange.ItemPositionChange,
        QPointF(13.0, 28.0),
    )
    assert result.x() == pytest.approx(13.0)
    assert result.y() == pytest.approx(28.0)


def test_itemchange_snap_midpoint_rounds_correctly():
    """Values exactly at n+0.5 round per Python's round() (banker's rounding)."""
    node = PartNode(_PART_A, "n0001")
    node.set_snap(True)
    # 10.0 / 20 = 0.5 → round(0.5) = 0 (banker's rounding) → 0
    result = node.itemChange(
        PartNode.GraphicsItemChange.ItemPositionChange,
        QPointF(10.0, 30.0),   # 30/20=1.5 → round(1.5)=2 → 40
    )
    assert result.x() == pytest.approx(round(10.0 / _G) * _G)
    assert result.y() == pytest.approx(round(30.0 / _G) * _G)


# ---------------------------------------------------------------------------
# Grid constant
# ---------------------------------------------------------------------------

def test_grid_size_used_for_snap():
    assert _G == 20
