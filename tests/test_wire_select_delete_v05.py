# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""PATCH_WIRE_SELECT_DELETE_V05 — select and delete existing wires."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QMouseEvent, QKeyEvent
from PySide6.QtCore import QPointF, QEvent, Qt

_app = QApplication.instance() or QApplication(sys.argv)

from ui.canvas import Canvas, ConnectionLine

_PART_A = {"id": "cpu.ak32", "name": "AK32", "category": "cpu"}
_PART_B = {"id": "mem.ram",  "name": "RAM",  "category": "mem"}
_PART_C = {"id": "io.uart",  "name": "UART", "category": "io"}
_LIB    = {_PART_A["id"]: _PART_A, _PART_B["id"]: _PART_B, _PART_C["id"]: _PART_C}


def _canvas() -> Canvas:
    return Canvas(log_fn=[].append)


def _connected_pair() -> Canvas:
    """node_0001 → node_0002 with one Dynamic Visual Port connection."""
    c = _canvas()
    c.add_part_at(_PART_A, QPointF(0.0, 0.0))
    c.add_part_at(_PART_B, QPointF(300.0, 0.0))
    c._begin_wire_from("node_0001", "bus")
    c._finish_wire("node_0002", "bus")
    return c


def _only_conn_id(c: Canvas) -> str:
    return c._connections[0]["id"]


def _left_click(c: Canvas, scene_pos: QPointF) -> None:
    view_pt = c.mapFromScene(scene_pos)
    ev = QMouseEvent(
        QEvent.Type.MouseButtonPress, QPointF(view_pt),
        Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    c.mousePressEvent(ev)


def _press_delete(c: Canvas) -> None:
    ev = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Delete, Qt.KeyboardModifier.NoModifier)
    c.keyPressEvent(ev)


# ---------------------------------------------------------------------------
# selection
# ---------------------------------------------------------------------------

def test_set_selected_conn_marks_line():
    c = _connected_pair()
    cid = _only_conn_id(c)
    c._set_selected_conn(cid)
    assert c._selected_conn_id == cid
    assert c._conn_items[cid].is_selected() is True


def test_click_on_wire_selects_it():
    c = _connected_pair()
    cid = _only_conn_id(c)
    mid = c._conn_items[cid].path().pointAtPercent(0.5)
    _left_click(c, mid)
    assert c._selected_conn_id == cid


def test_selection_moves_between_wires():
    c = _connected_pair()
    c.add_part_at(_PART_C, QPointF(0.0, 200.0))
    c._begin_wire_from("node_0003", "bus")
    c._finish_wire("node_0002", "bus")
    cid1, cid2 = c._connections[0]["id"], c._connections[1]["id"]
    c._set_selected_conn(cid1)
    c._set_selected_conn(cid2)
    assert c._selected_conn_id == cid2
    assert c._conn_items[cid1].is_selected() is False
    assert c._conn_items[cid2].is_selected() is True


def test_click_blank_clears_selection():
    c = _connected_pair()
    c._set_selected_conn(_only_conn_id(c))
    _left_click(c, QPointF(0.0, -500.0))   # far from any wire/node
    assert c._selected_conn_id is None


# ---------------------------------------------------------------------------
# deletion API
# ---------------------------------------------------------------------------

def test_remove_connection_drops_data_and_item():
    c = _connected_pair()
    cid = _only_conn_id(c)
    line = c._conn_items[cid]
    assert c._remove_connection(cid) is True
    assert all(conn["id"] != cid for conn in c._connections)
    assert cid not in c._conn_items
    assert line.scene() is None


def test_remove_connection_prunes_orphan_visual_ports():
    c = _connected_pair()
    cid = _only_conn_id(c)
    assert c.get_node("node_0001").visual_ports()
    assert c.get_node("node_0002").visual_ports()
    c._remove_connection(cid)
    assert c.get_node("node_0001").visual_ports() == []
    assert c.get_node("node_0002").visual_ports() == []


def test_remove_connection_keeps_shared_fanout_port():
    """Fan-out: source vp shared by two connections must survive one deletion."""
    c = _connected_pair()
    c.add_part_at(_PART_C, QPointF(0.0, 200.0))
    src_vp = c.get_node("node_0001").visual_ports()[0]["id"]
    # Second connection re-using node_0001's existing visual port (port-drag style).
    c._start_port_drag(c.get_node("node_0001"), c.get_node("node_0001").visual_ports()[0])
    assert c._finish_port_drag("node_0003") is True
    first_id = c._connections[0]["id"]
    c._remove_connection(first_id)
    # node_0001's fan-out vp is still referenced by the second connection.
    remaining_vps = [vp["id"] for vp in c.get_node("node_0001").visual_ports()]
    assert src_vp in remaining_vps


def test_remove_connection_clears_selection_and_hover():
    c = _connected_pair()
    cid = _only_conn_id(c)
    c._set_selected_conn(cid)
    c._set_hover_conn(cid)
    c._remove_connection(cid)
    assert c._selected_conn_id is None
    assert c._hover_conn_id is None


def test_remove_connection_unknown_id_noop():
    c = _connected_pair()
    before = len(c._connections)
    assert c._remove_connection("conn_999") is False
    assert len(c._connections) == before


# ---------------------------------------------------------------------------
# Delete key
# ---------------------------------------------------------------------------

def test_delete_key_removes_selected_wire():
    c = _connected_pair()
    cid = _only_conn_id(c)
    c._set_selected_conn(cid)
    _press_delete(c)
    assert all(conn["id"] != cid for conn in c._connections)


def test_delete_key_without_selection_deletes_node():
    c = _connected_pair()
    c.get_node("node_0001").setSelected(True)
    assert c._selected_conn_id is None
    _press_delete(c)
    assert c.get_node("node_0001") is None


def test_delete_key_ignored_during_port_drag():
    c = _connected_pair()
    cid = _only_conn_id(c)
    c._set_selected_conn(cid)
    c._start_port_drag(c.get_node("node_0001"), c.get_node("node_0001").visual_ports()[0])
    _press_delete(c)   # port drag owns the flow; wire not removed
    assert any(conn["id"] == cid for conn in c._connections)


# ---------------------------------------------------------------------------
# node deletion integrity
# ---------------------------------------------------------------------------

def test_node_delete_clears_selected_wire():
    c = _connected_pair()
    cid = _only_conn_id(c)
    c._set_selected_conn(cid)
    c._remove_node("node_0001")
    assert c._selected_conn_id is None


# ---------------------------------------------------------------------------
# hover / active integration
# ---------------------------------------------------------------------------

def test_selected_priority_over_active_and_hover():
    line = ConnectionLine("c1", "n1", "n2", kind="bus")
    base = line.pen().widthF()
    line.set_active(True)
    line.set_hovered(True)
    line.set_selected(True)
    sel_width = line.pen().widthF()
    assert sel_width > base + 2.0          # selected style applied
    sel_color = line.pen().color().name()
    line.set_active(False)                 # active off, still selected
    assert line.pen().color().name() == sel_color
    assert abs(line.pen().widthF() - sel_width) < 0.01


def test_hover_conn_does_not_clear_selection():
    c = _connected_pair()
    cid = _only_conn_id(c)
    c._set_selected_conn(cid)
    c._set_hover_conn(cid)
    assert c._selected_conn_id == cid
    assert c._conn_items[cid].is_selected() is True


def test_deselect_restores_base_pen():
    line = ConnectionLine("c1", "n1", "n2", kind="signal")
    base_w = line.pen().widthF()
    base_c = line.pen().color().name()
    line.set_selected(True)
    line.set_selected(False)
    assert abs(line.pen().widthF() - base_w) < 0.01
    assert line.pen().color().name() == base_c


# ---------------------------------------------------------------------------
# regression
# ---------------------------------------------------------------------------

def test_right_click_connect_still_works():
    c = _canvas()
    c.add_part_at(_PART_A, QPointF(0.0, 0.0))
    c.add_part_at(_PART_B, QPointF(300.0, 0.0))
    c._begin_wire_from("node_0001", "bus")
    c._finish_wire("node_0002", "bus")
    assert len(c._connections) == 1


def test_port_drag_connect_still_works():
    c = _connected_pair()
    before = len(c._connections)
    c.add_part_at(_PART_C, QPointF(0.0, 200.0))
    c._start_port_drag(c.get_node("node_0001"), c.get_node("node_0001").visual_ports()[0])
    assert c._finish_port_drag("node_0003") is True
    assert len(c._connections) == before + 1


def test_export_import_roundtrip():
    c = _connected_pair()
    c._set_selected_conn(_only_conn_id(c))
    data = c.export_canvas()
    c2 = _canvas()
    c2.import_canvas(data, _LIB)
    assert len(c2._connections) == len(data["connections"])
    assert c2._selected_conn_id is None    # selection reset on import/clear
