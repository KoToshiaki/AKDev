# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""PATCH_PORT_DRAG_CONNECT_V05 — drag from a visual port to connect."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPainterPath, QMouseEvent
from PySide6.QtCore import QPointF, QEvent, Qt

_app = QApplication.instance() or QApplication(sys.argv)

from ui.canvas import Canvas, PartNode, _VP_RADIUS

_PART_A = {"id": "cpu.ak32", "name": "AK32", "category": "cpu"}
_PART_B = {"id": "mem.ram",  "name": "RAM",  "category": "mem"}
_PART_C = {"id": "io.uart",  "name": "UART", "category": "io"}
_LIB    = {_PART_A["id"]: _PART_A, _PART_B["id"]: _PART_B, _PART_C["id"]: _PART_C}


def _canvas() -> Canvas:
    return Canvas(log_fn=[].append)


def _connected_pair() -> Canvas:
    """Two nodes with one existing connection (so node_0001 has a visual port)."""
    c = _canvas()
    c.add_part_at(_PART_A, QPointF(0.0, 0.0))
    c.add_part_at(_PART_B, QPointF(300.0, 0.0))
    c._begin_wire_from("node_0001", "bus")
    c._finish_wire("node_0002", "bus")
    return c


def _src_vp(c: Canvas) -> dict:
    return c.get_node("node_0001").visual_ports()[0]


# ---------------------------------------------------------------------------
# _visual_port_at
# ---------------------------------------------------------------------------

def test_visual_port_at_hits_existing_port():
    c = _connected_pair()
    vp = _src_vp(c)
    pos = c.get_node("node_0001").visual_port_pos(vp["id"])
    hit = c._visual_port_at(pos)
    assert hit is not None
    assert hit[1]["id"] == vp["id"]


def test_visual_port_at_misses_far_point():
    c = _connected_pair()
    assert c._visual_port_at(QPointF(9999.0, 9999.0)) is None


def test_visual_port_at_within_slack():
    c = _connected_pair()
    vp = _src_vp(c)
    pos = c.get_node("node_0001").visual_port_pos(vp["id"])
    near = QPointF(pos.x() + _VP_RADIUS, pos.y())
    assert c._visual_port_at(near) is not None


# ---------------------------------------------------------------------------
# start / cancel
# ---------------------------------------------------------------------------

def test_start_port_drag_sets_state_and_preview():
    c = _connected_pair()
    node = c.get_node("node_0001")
    c._start_port_drag(node, _src_vp(c))
    assert c._port_drag is not None
    assert c._port_drag["node_id"] == "node_0001"
    assert c._port_drag_preview is not None
    assert c._port_drag_preview in c.scene().items()


def test_cancel_port_drag_clears_state():
    c = _connected_pair()
    c._start_port_drag(c.get_node("node_0001"), _src_vp(c))
    preview = c._port_drag_preview
    c._cancel_port_drag()
    assert c._port_drag is None
    assert c._port_drag_preview is None
    assert preview.scene() is None


def test_update_preview_is_curved():
    c = _connected_pair()
    c._start_port_drag(c.get_node("node_0001"), _src_vp(c))
    c._update_port_drag_preview(QPointF(150.0, 120.0))
    types = [c._port_drag_preview.path().elementAt(i).type
             for i in range(c._port_drag_preview.path().elementCount())]
    assert QPainterPath.ElementType.CurveToElement in types


# ---------------------------------------------------------------------------
# finish
# ---------------------------------------------------------------------------

def test_finish_port_drag_creates_connection():
    c = _connected_pair()
    c.add_part_at(_PART_C, QPointF(600.0, 0.0))   # node_0003
    before = len(c._connections)
    src = _src_vp(c)
    c._start_port_drag(c.get_node("node_0001"), src)
    ok = c._finish_port_drag("node_0003")
    assert ok is True
    assert len(c._connections) == before + 1
    new = c._connections[-1]
    # source reuses the existing visual port; target gets a new one
    assert new["from"]["visual_port_id"] == src["id"]
    assert "visual_port_id" in new["to"]
    assert len(c.get_node("node_0003").visual_ports()) == 1


def test_finish_port_drag_connection_is_curved():
    c = _connected_pair()
    c.add_part_at(_PART_C, QPointF(600.0, 0.0))
    c._start_port_drag(c.get_node("node_0001"), _src_vp(c))
    c._finish_port_drag("node_0003")
    line = c._conn_items[c._connections[-1]["id"]]
    types = [line.path().elementAt(i).type for i in range(line.path().elementCount())]
    assert QPainterPath.ElementType.CurveToElement in types


def test_finish_port_drag_same_node_cancels():
    c = _connected_pair()
    before = len(c._connections)
    c._start_port_drag(c.get_node("node_0001"), _src_vp(c))
    ok = c._finish_port_drag("node_0001")
    assert ok is False
    assert len(c._connections) == before
    assert c._port_drag is None


def test_finish_port_drag_no_target_cancels():
    c = _connected_pair()
    before = len(c._connections)
    c._start_port_drag(c.get_node("node_0001"), _src_vp(c))
    ok = c._finish_port_drag(None)
    assert ok is False
    assert len(c._connections) == before


# ---------------------------------------------------------------------------
# Esc cancels
# ---------------------------------------------------------------------------

def test_escape_cancels_port_drag():
    c = _connected_pair()
    c._start_port_drag(c.get_node("node_0001"), _src_vp(c))
    from PySide6.QtGui import QKeyEvent
    c.keyPressEvent(QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Escape,
                              Qt.KeyboardModifier.NoModifier))
    assert c._port_drag is None


# ---------------------------------------------------------------------------
# mouse press / release integration
# ---------------------------------------------------------------------------

def test_mouse_press_on_port_starts_drag():
    c = _connected_pair()
    vp = _src_vp(c)
    scene_pt = c.get_node("node_0001").visual_port_pos(vp["id"])
    view_pt = c.mapFromScene(scene_pt)
    ev = QMouseEvent(QEvent.Type.MouseButtonPress, QPointF(view_pt),
                     Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton,
                     Qt.KeyboardModifier.NoModifier)
    c.mousePressEvent(ev)
    assert c._port_drag is not None


def test_mouse_press_off_port_does_not_start_drag():
    c = _connected_pair()
    far = c.mapFromScene(QPointF(9999.0, 9999.0))
    ev = QMouseEvent(QEvent.Type.MouseButtonPress, QPointF(far),
                     Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton,
                     Qt.KeyboardModifier.NoModifier)
    c.mousePressEvent(ev)
    assert c._port_drag is None


# ---------------------------------------------------------------------------
# export/import round-trip of a port-drag connection
# ---------------------------------------------------------------------------

def test_port_drag_connection_round_trips():
    c = _connected_pair()
    c.add_part_at(_PART_C, QPointF(600.0, 0.0))
    c._start_port_drag(c.get_node("node_0001"), _src_vp(c))
    c._finish_port_drag("node_0003")
    data = c.export_canvas()
    c2 = _canvas()
    c2.import_canvas(data, _LIB)
    assert len(c2._connections) == len(c._connections)
    assert all("visual_port_id" in cn["from"] for cn in c2._connections)


# ---------------------------------------------------------------------------
# existing right-click connection still works
# ---------------------------------------------------------------------------

def test_right_click_connection_still_works():
    c = _canvas()
    c.add_part_at(_PART_A, QPointF(0.0, 0.0))
    c.add_part_at(_PART_B, QPointF(300.0, 0.0))
    c._begin_wire_from("node_0001", "bus")
    c._finish_wire("node_0002", "bus")
    assert len(c._connections) == 1
    assert c._mode == "design"
