# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""PATCH_WIRING_V05 (W9) — node deletion also removes attached wires."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QKeyEvent
from PySide6.QtCore import QPointF, QEvent, Qt

_app = QApplication.instance() or QApplication(sys.argv)

from ui.canvas import Canvas, ConnectionLine, PartNode

_PART_A = {"id": "cpu.ak32", "name": "AK32", "category": "cpu"}
_PART_B = {"id": "mem.ram",  "name": "RAM",  "category": "mem"}
_PART_C = {"id": "io.uart",  "name": "UART", "category": "io"}


def _canvas() -> Canvas:
    return Canvas(log_fn=[].append)


def _wired_pair() -> Canvas:
    c = _canvas()
    c.add_part_at(_PART_A, QPointF(0.0, 0.0))
    c.add_part_at(_PART_B, QPointF(200.0, 0.0))
    c.add_connection("node_0001", "bus", "node_0002", "bus")
    return c


def _conn_lines(c: Canvas) -> list:
    return [i for i in c.scene().items() if isinstance(i, ConnectionLine)]


# ---------------------------------------------------------------------------
# _remove_node — data + visual sync
# ---------------------------------------------------------------------------

def test_remove_node_drops_connection_data():
    c = _wired_pair()
    assert len(c._connections) == 1
    c._remove_node("node_0001")
    assert c._connections == []


def test_remove_node_drops_connection_line_item():
    c = _wired_pair()
    assert len(_conn_lines(c)) == 1
    c._remove_node("node_0001")
    assert _conn_lines(c) == []


def test_remove_node_drops_conn_items_dict():
    c = _wired_pair()
    c._remove_node("node_0002")
    assert c._conn_items == {}


def test_remove_node_removes_the_node():
    c = _wired_pair()
    c._remove_node("node_0001")
    assert c.get_node("node_0001") is None


def test_remove_node_keeps_unrelated_connection():
    c = _canvas()
    c.add_part_at(_PART_A, QPointF(0.0, 0.0))
    c.add_part_at(_PART_B, QPointF(200.0, 0.0))
    c.add_part_at(_PART_C, QPointF(400.0, 0.0))
    c.add_connection("node_0001", "bus", "node_0002", "bus")
    c.add_connection("node_0002", "bus", "node_0003", "bus")
    c._remove_node("node_0001")           # only the first connection touches it
    assert len(c._connections) == 1
    remaining = c._connections[0]
    assert "node_0001" not in (remaining["from"]["node_id"], remaining["to"]["node_id"])


def test_remove_node_returns_connection_count():
    c = _wired_pair()
    assert c._remove_node("node_0001") == 1


# ---------------------------------------------------------------------------
# export has no orphan after delete
# ---------------------------------------------------------------------------

def test_export_canvas_has_no_orphan_connection():
    c = _wired_pair()
    c._remove_node("node_0001")
    data = c.export_canvas()
    assert data["connections"] == []


# ---------------------------------------------------------------------------
# every delete path behaves the same
# ---------------------------------------------------------------------------

def test_delete_selected_removes_attached_wire():
    c = _wired_pair()
    c.get_node("node_0001").setSelected(True)
    c.delete_selected()
    assert c._connections == []
    assert _conn_lines(c) == []


def test_delete_key_removes_attached_wire():
    c = _wired_pair()
    c.get_node("node_0002").setSelected(True)
    ev = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Delete,
                   Qt.KeyboardModifier.NoModifier)
    c.keyPressEvent(ev)
    assert c._connections == []
    assert _conn_lines(c) == []


def test_delete_node_helper_removes_wire():
    c = _wired_pair()
    c._delete_node(c.get_node("node_0001"))
    assert c._connections == []


def test_multi_select_delete_removes_all_wires():
    c = _canvas()
    c.add_part_at(_PART_A, QPointF(0.0, 0.0))
    c.add_part_at(_PART_B, QPointF(200.0, 0.0))
    c.add_part_at(_PART_C, QPointF(400.0, 0.0))
    c.add_connection("node_0001", "bus", "node_0002", "bus")
    c.add_connection("node_0002", "bus", "node_0003", "bus")
    c.get_node("node_0001").setSelected(True)
    c.get_node("node_0002").setSelected(True)
    c.delete_selected()
    assert c._connections == []
    assert _conn_lines(c) == []


# ---------------------------------------------------------------------------
# deleting the wire-start node cancels the in-progress wire
# ---------------------------------------------------------------------------

def test_remove_wire_start_node_cancels_wire():
    c = _wired_pair()
    c._begin_wire_from("node_0001", "bus")
    assert c._mode == "wire"
    c._remove_node("node_0001")
    assert c._mode == "design"
    assert c._wire_from is None
