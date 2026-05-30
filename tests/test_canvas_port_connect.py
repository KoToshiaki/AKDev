# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""Headless tests for PortDot and port-click connection creation."""
import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF

_app = QApplication.instance() or QApplication(sys.argv)

from ui.canvas import Canvas, ConnectionLine, PartNode, PortDot, _NODE_W, _NODE_H

_PART_A = {"id": "cpu.ak32", "name": "AK32", "category": "cpu"}
_PART_B = {"id": "mem.ram",  "name": "RAM",  "category": "mem"}
_LIB    = {_PART_A["id"]: _PART_A, _PART_B["id"]: _PART_B}


def _make_canvas() -> Canvas:
    return Canvas(log_fn=[].append)


def _conn_lines(canvas: Canvas) -> list[ConnectionLine]:
    return [i for i in canvas.scene().items() if isinstance(i, ConnectionLine)]


# ---------------------------------------------------------------------------
# PortDot class — structure
# ---------------------------------------------------------------------------

def test_partnode_has_port_dot():
    node = PartNode(_PART_A, "node_0001")
    assert isinstance(node._port_dot, PortDot)


def test_port_dot_node_id():
    node = PartNode(_PART_A, "node_0001")
    assert node._port_dot.node_id() == "node_0001"


def test_port_dot_port_name():
    node = PartNode(_PART_A, "node_0001")
    assert node._port_dot.port_name() == "bus"


def test_port_dot_is_child_of_partnode():
    node = PartNode(_PART_A, "node_0001")
    assert node._port_dot.parentItem() is node


def test_port_dot_position_right_center():
    node = PartNode(_PART_A, "node_0001")
    pos = node._port_dot.pos()
    assert pos.x() == pytest.approx(_NODE_W)
    assert pos.y() == pytest.approx(_NODE_H / 2)


def test_port_dot_zvalue_above_partnode():
    node = PartNode(_PART_A, "node_0001")
    assert node._port_dot.zValue() > 0


def test_port_dot_set_pending_changes_brush():
    node = PartNode(_PART_A, "node_0001")
    dot = node._port_dot
    brush_normal = dot.brush().color().name()
    dot.set_pending(True)
    brush_pending = dot.brush().color().name()
    assert brush_normal != brush_pending


def test_port_dot_set_pending_false_restores_brush():
    node = PartNode(_PART_A, "node_0001")
    dot = node._port_dot
    original = dot.brush().color().name()
    dot.set_pending(True)
    dot.set_pending(False)
    assert dot.brush().color().name() == original


# ---------------------------------------------------------------------------
# Canvas._pending_port state machine
# ---------------------------------------------------------------------------

def test_pending_port_default_none():
    canvas = _make_canvas()
    assert canvas._pending_port is None


def test_first_port_click_sets_pending():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    node = canvas.get_node("node_0001")
    canvas._on_port_click(node._port_dot)
    assert canvas._pending_port is node._port_dot


def test_first_port_click_no_connection_yet():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    node = canvas.get_node("node_0001")
    canvas._on_port_click(node._port_dot)
    assert len(canvas._connections) == 0


def test_second_click_different_node_adds_connection():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    canvas.add_part_at(_PART_B, QPointF(200.0, 0.0))
    node_a = canvas.get_node("node_0001")
    node_b = canvas.get_node("node_0002")
    canvas._on_port_click(node_a._port_dot)
    canvas._on_port_click(node_b._port_dot)
    assert len(canvas._connections) == 1


def test_second_click_connection_from_field():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    canvas.add_part_at(_PART_B, QPointF(200.0, 0.0))
    node_a = canvas.get_node("node_0001")
    node_b = canvas.get_node("node_0002")
    canvas._on_port_click(node_a._port_dot)
    canvas._on_port_click(node_b._port_dot)
    conn = canvas._connections[0]
    assert conn["from"]["node_id"] == "node_0001"
    assert conn["from"]["port"]    == "bus"


def test_second_click_connection_to_field():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    canvas.add_part_at(_PART_B, QPointF(200.0, 0.0))
    node_a = canvas.get_node("node_0001")
    node_b = canvas.get_node("node_0002")
    canvas._on_port_click(node_a._port_dot)
    canvas._on_port_click(node_b._port_dot)
    conn = canvas._connections[0]
    assert conn["to"]["node_id"] == "node_0002"
    assert conn["to"]["port"]    == "bus"


def test_second_click_clears_pending():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    canvas.add_part_at(_PART_B, QPointF(200.0, 0.0))
    node_a = canvas.get_node("node_0001")
    node_b = canvas.get_node("node_0002")
    canvas._on_port_click(node_a._port_dot)
    canvas._on_port_click(node_b._port_dot)
    assert canvas._pending_port is None


def test_same_node_click_cancels_pending():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    node_a = canvas.get_node("node_0001")
    canvas._on_port_click(node_a._port_dot)
    canvas._on_port_click(node_a._port_dot)   # same dot
    assert canvas._pending_port is None


def test_same_node_no_connection_created():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    canvas.add_part_at(_PART_B, QPointF(200.0, 0.0))
    node_a = canvas.get_node("node_0001")
    canvas._on_port_click(node_a._port_dot)
    canvas._on_port_click(node_a._port_dot)   # same node — cancel
    assert len(canvas._connections) == 0


def test_same_node_via_other_port_also_cancels():
    """Two distinct PortDots on the same node_id should also cancel."""
    # Currently each node has one port, but the logic checks node_id, not dot identity.
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    node_a = canvas.get_node("node_0001")
    canvas._on_port_click(node_a._port_dot)
    # Manually create a second dot with the same node_id to test node_id check
    dot2 = PortDot("node_0001", "debug", node_a)
    canvas._on_port_click(dot2)
    assert canvas._pending_port is None
    assert len(canvas._connections) == 0


# ---------------------------------------------------------------------------
# Connection creates ConnectionLine in scene
# ---------------------------------------------------------------------------

def test_port_click_creates_connection_line():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    canvas.add_part_at(_PART_B, QPointF(200.0, 0.0))
    node_a = canvas.get_node("node_0001")
    node_b = canvas.get_node("node_0002")
    canvas._on_port_click(node_a._port_dot)
    canvas._on_port_click(node_b._port_dot)
    assert len(_conn_lines(canvas)) == 1


def test_port_click_line_path_not_empty():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    canvas.add_part_at(_PART_B, QPointF(200.0, 0.0))
    node_a = canvas.get_node("node_0001")
    node_b = canvas.get_node("node_0002")
    canvas._on_port_click(node_a._port_dot)
    canvas._on_port_click(node_b._port_dot)
    line = _conn_lines(canvas)[0]
    assert not line.path().isEmpty()


# ---------------------------------------------------------------------------
# Subsequent connections and callbacks
# ---------------------------------------------------------------------------

def test_after_connection_can_start_new():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    canvas.add_part_at(_PART_B, QPointF(200.0, 0.0))
    node_a = canvas.get_node("node_0001")
    node_b = canvas.get_node("node_0002")
    canvas._on_port_click(node_a._port_dot)
    canvas._on_port_click(node_b._port_dot)
    canvas._on_port_click(node_b._port_dot)   # start new
    assert canvas._pending_port is node_b._port_dot


def test_two_connections_both_created():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    canvas.add_part_at(_PART_B, QPointF(200.0, 0.0))
    node_a = canvas.get_node("node_0001")
    node_b = canvas.get_node("node_0002")
    canvas._on_port_click(node_a._port_dot)
    canvas._on_port_click(node_b._port_dot)   # conn 1: a→b
    canvas._on_port_click(node_b._port_dot)
    canvas._on_port_click(node_a._port_dot)   # conn 2: b→a
    assert len(canvas._connections) == 2
    assert len(_conn_lines(canvas)) == 2



def test_import_canvas_clear_resets_pending_port():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    node = canvas.get_node("node_0001")
    canvas._on_port_click(node._port_dot)
    assert canvas._pending_port is not None
    canvas.import_canvas({"parts": [], "connections": []}, {}, clear=True)
    assert canvas._pending_port is None
