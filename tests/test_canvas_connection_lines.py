# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""Headless tests for ConnectionLine visual items on the Canvas."""
import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF

_app = QApplication.instance() or QApplication(sys.argv)

from ui.canvas import Canvas, ConnectionLine, PartNode, _NODE_W, _NODE_H

_PART_A = {"id": "cpu.ak32", "name": "AK32", "category": "cpu"}
_PART_B = {"id": "mem.ram",  "name": "RAM",  "category": "mem"}
_LIB    = {_PART_A["id"]: _PART_A, _PART_B["id"]: _PART_B}


def _make_canvas() -> Canvas:
    return Canvas(log_fn=[].append)


def _conn_lines(canvas: Canvas) -> list[ConnectionLine]:
    return [i for i in canvas.scene().items() if isinstance(i, ConnectionLine)]


# ---------------------------------------------------------------------------
# ConnectionLine class
# ---------------------------------------------------------------------------

def test_connection_line_conn_id():
    line = ConnectionLine("conn_0001", "n1", "n2", "bus")
    assert line.conn_id() == "conn_0001"


def test_connection_line_from_node_id():
    line = ConnectionLine("conn_0001", "node_a", "node_b", "bus")
    assert line.from_node_id() == "node_a"


def test_connection_line_to_node_id():
    line = ConnectionLine("conn_0001", "node_a", "node_b", "bus")
    assert line.to_node_id() == "node_b"


def test_connection_line_zvalue_below_zero():
    line = ConnectionLine("conn_0001", "n1", "n2", "bus")
    assert line.zValue() < 0


def test_connection_line_bus_wide_pen():
    line = ConnectionLine("c1", "n1", "n2", "bus")
    assert line.pen().widthF() > 2.0


def test_connection_line_signal_narrow_pen():
    line = ConnectionLine("c1", "n1", "n2", "signal")
    assert line.pen().widthF() <= 2.0


def test_connection_line_clock_narrow_pen():
    line = ConnectionLine("c1", "n1", "n2", "clock")
    assert line.pen().widthF() <= 2.0


def test_connection_line_update_line_sets_path():
    line = ConnectionLine("c1", "n1", "n2", "bus")
    p1 = QPointF(0.0, 0.0)
    p2 = QPointF(100.0, 50.0)
    line.update_line(p1, p2)
    path = line.path()
    assert not path.isEmpty()


def test_connection_line_update_line_changes_path():
    line = ConnectionLine("c1", "n1", "n2", "bus")
    line.update_line(QPointF(0.0, 0.0), QPointF(100.0, 0.0))
    path_a = line.path().boundingRect()
    line.update_line(QPointF(0.0, 0.0), QPointF(0.0, 100.0))
    path_b = line.path().boundingRect()
    assert path_a != path_b


# ---------------------------------------------------------------------------
# add_connection creates scene item
# ---------------------------------------------------------------------------

def test_add_connection_creates_line_item():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    canvas.add_part_at(_PART_B, QPointF(200.0, 0.0))
    canvas.add_connection("node_0001", "p1", "node_0002", "p2")
    assert len(_conn_lines(canvas)) == 1


def test_add_connection_line_has_conn_id():
    canvas = _make_canvas()
    canvas.add_connection("n1", "p1", "n2", "p2")
    line = _conn_lines(canvas)[0]
    assert line.conn_id() == "conn_0001"


def test_add_connection_line_zvalue():
    canvas = _make_canvas()
    canvas.add_connection("n1", "p1", "n2", "p2")
    line = _conn_lines(canvas)[0]
    assert line.zValue() < 0


def test_add_connection_bus_pen_width():
    canvas = _make_canvas()
    canvas.add_connection("n1", "p1", "n2", "p2", kind="bus")
    line = _conn_lines(canvas)[0]
    assert line.pen().widthF() > 2.0


def test_add_connection_signal_pen_width():
    canvas = _make_canvas()
    canvas.add_connection("n1", "p1", "n2", "p2", kind="signal")
    line = _conn_lines(canvas)[0]
    assert line.pen().widthF() <= 2.0


def test_add_multiple_connections_creates_multiple_lines():
    canvas = _make_canvas()
    canvas.add_connection("n1", "p1", "n2", "p2")
    canvas.add_connection("n2", "p3", "n3", "p4")
    assert len(_conn_lines(canvas)) == 2


# ---------------------------------------------------------------------------
# update_connections — line position follows nodes
# ---------------------------------------------------------------------------

def test_update_connections_sets_path_when_nodes_present():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    canvas.add_part_at(_PART_B, QPointF(200.0, 0.0))
    canvas.add_connection("node_0001", "p1", "node_0002", "p2")
    line = _conn_lines(canvas)[0]
    assert not line.path().isEmpty()


def test_update_connections_updates_path_after_move():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    canvas.add_part_at(_PART_B, QPointF(200.0, 0.0))
    canvas.add_connection("node_0001", "p1", "node_0002", "p2")
    line = _conn_lines(canvas)[0]
    rect_before = line.path().boundingRect()

    node_b = canvas.get_node("node_0002")
    node_b.setPos(QPointF(400.0, 0.0))
    canvas.update_connections()
    rect_after = line.path().boundingRect()
    assert rect_before != rect_after


def test_node_move_triggers_callback():
    """setPos on a node automatically calls update_connections via _pos_changed_cb."""
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    canvas.add_part_at(_PART_B, QPointF(200.0, 0.0))
    canvas.add_connection("node_0001", "p1", "node_0002", "p2")
    line = _conn_lines(canvas)[0]
    rect_before = line.path().boundingRect()

    node_b = canvas.get_node("node_0002")
    node_b.setPos(QPointF(400.0, 100.0))   # triggers _pos_changed_cb automatically
    rect_after = line.path().boundingRect()
    assert rect_before != rect_after


def test_update_connections_skips_missing_node():
    """Connection with a non-existent node_id should not crash."""
    canvas = _make_canvas()
    canvas.add_connection("ghost_1", "p1", "ghost_2", "p2")
    canvas.update_connections()   # must not raise


def test_conn_line_endpoint_is_port_position():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    canvas.add_part_at(_PART_B, QPointF(200.0, 0.0))
    canvas.add_connection("node_0001", "p1", "node_0002", "p2")
    line = _conn_lines(canvas)[0]
    # B2 fix: the wire endpoint must sit on the REAL port position (no grid gap),
    # not the grid-snapped one. node at (0,0): right edge = (_NODE_W, _NODE_H/2).
    expected_x = float(_NODE_W)
    expected_y = float(_NODE_H / 2)
    start = line.path().pointAtPercent(0.0)
    assert abs(start.x() - expected_x) < 1.0
    assert abs(start.y() - expected_y) < 1.0


# ---------------------------------------------------------------------------
# import_canvas restores line items
# ---------------------------------------------------------------------------

_SAVED_CONN = {
    "id":    "conn_0001",
    "from":  {"node_id": "node_0001", "port": "bus_master"},
    "to":    {"node_id": "node_0002", "port": "bus_slave"},
    "kind":  "bus",
    "width": 32,
    "label": "",
}

_SAVED_DATA = {
    "parts": [
        {"node_id": "node_0001", "part_id": _PART_A["id"],
         "x": 0.0, "y": 0.0, "sources": {"asm": None, "hdl": None}},
        {"node_id": "node_0002", "part_id": _PART_B["id"],
         "x": 200.0, "y": 0.0, "sources": {"asm": None, "hdl": None}},
    ],
    "connections": [_SAVED_CONN],
}


def test_import_canvas_creates_line_items():
    canvas = _make_canvas()
    canvas.import_canvas(_SAVED_DATA, _LIB)
    assert len(_conn_lines(canvas)) == 1


def test_import_canvas_line_has_correct_conn_id():
    canvas = _make_canvas()
    canvas.import_canvas(_SAVED_DATA, _LIB)
    line = _conn_lines(canvas)[0]
    assert line.conn_id() == "conn_0001"


def test_import_canvas_clear_removes_old_lines():
    canvas = _make_canvas()
    canvas.import_canvas(_SAVED_DATA, _LIB)
    assert len(_conn_lines(canvas)) == 1
    canvas.import_canvas({"parts": [], "connections": []}, {}, clear=True)
    assert len(_conn_lines(canvas)) == 0


def test_import_canvas_line_path_set_after_import():
    """Line path must be non-empty when both nodes are present."""
    canvas = _make_canvas()
    canvas.import_canvas(_SAVED_DATA, _LIB)
    line = _conn_lines(canvas)[0]
    assert not line.path().isEmpty()


def test_import_canvas_no_clear_keeps_existing_lines():
    canvas = _make_canvas()
    canvas.import_canvas(_SAVED_DATA, _LIB)
    extra = {
        "parts": [],
        "connections": [{
            "id": "conn_0002",
            "from": {"node_id": "node_0001", "port": "debug"},
            "to":   {"node_id": "node_0002", "port": "debug"},
            "kind": "signal", "width": 1, "label": "",
        }],
    }
    canvas.import_canvas(extra, _LIB, clear=False)
    assert len(_conn_lines(canvas)) == 2


# ---------------------------------------------------------------------------
# export_canvas data is unchanged by visual changes
# ---------------------------------------------------------------------------

def test_export_canvas_connections_data_unchanged():
    canvas = _make_canvas()
    canvas.add_connection("n1", "p1", "n2", "p2", kind="bus", width=32, label="test")
    data = canvas.export_canvas()
    conn = data["connections"][0]
    assert conn["id"]    == "conn_0001"
    assert conn["kind"]  == "bus"
    assert conn["width"] == 32
    assert conn["label"] == "test"


def test_export_canvas_not_affected_by_update_connections():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    canvas.add_connection("node_0001", "p1", "node_0002", "p2")
    canvas.update_connections()
    data = canvas.export_canvas()
    assert len(data["connections"]) == 1
