# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""PATCH_VISUAL_PORT_MOVE_V05 — interactive (Alt+drag) visual port movement."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QMouseEvent, QKeyEvent
from PySide6.QtCore import QPointF, QEvent, Qt

_app = QApplication.instance() or QApplication(sys.argv)

from ui.canvas import Canvas, PartNode, _NODE_W, _NODE_H

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


def _src_vp(c: Canvas) -> dict:
    return c.get_node("node_0001").visual_ports()[0]


def _press(c: Canvas, scene_pos: QPointF, *, alt: bool = False) -> None:
    view_pt = c.mapFromScene(scene_pos)
    mods = Qt.KeyboardModifier.AltModifier if alt else Qt.KeyboardModifier.NoModifier
    ev = QMouseEvent(
        QEvent.Type.MouseButtonPress, QPointF(view_pt),
        Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, mods,
    )
    c.mousePressEvent(ev)


def _release(c: Canvas, scene_pos: QPointF) -> None:
    view_pt = c.mapFromScene(scene_pos)
    ev = QMouseEvent(
        QEvent.Type.MouseButtonRelease, QPointF(view_pt),
        Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
    )
    c.mouseReleaseEvent(ev)


def _press_escape(c: Canvas) -> None:
    ev = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier)
    c.keyPressEvent(ev)


# ---------------------------------------------------------------------------
# start: Alt vs no-Alt routing
# ---------------------------------------------------------------------------

def test_alt_press_on_vp_starts_move():
    c = _connected_pair()
    pos = c.get_node("node_0001").visual_port_pos(_src_vp(c)["id"])
    _press(c, pos, alt=True)
    assert c._port_move is not None
    assert c._port_move["vp_id"] == _src_vp(c)["id"]
    assert c._port_drag is None


def test_plain_press_on_vp_starts_port_drag():
    c = _connected_pair()
    pos = c.get_node("node_0001").visual_port_pos(_src_vp(c)["id"])
    _press(c, pos, alt=False)
    assert c._port_drag is not None
    assert c._port_move is None


def test_locked_vp_does_not_start_move():
    c = _connected_pair()
    _src_vp(c)["locked"] = True
    c._start_port_move(c.get_node("node_0001"), _src_vp(c))
    assert c._port_move is None


def test_start_marks_node_moving_port():
    c = _connected_pair()
    vp = _src_vp(c)
    c._start_port_move(c.get_node("node_0001"), vp)
    assert c.get_node("node_0001").moving_port() == vp["id"]


# ---------------------------------------------------------------------------
# update: edge constraint + wire follow
# ---------------------------------------------------------------------------

def test_update_changes_side_and_offset():
    c = _connected_pair()
    vp = _src_vp(c)
    c._start_port_move(c.get_node("node_0001"), vp)
    c._update_port_move(QPointF(0.0, 30.0))   # node_0001 local (0,30) → left edge
    assert vp["side"] == "left"
    assert vp["offset"] == 30.0


def test_update_changes_scene_pos():
    c = _connected_pair()
    vp = _src_vp(c)
    node = c.get_node("node_0001")
    before = node.visual_port_pos(vp["id"])
    c._start_port_move(node, vp)
    c._update_port_move(QPointF(70.0, 0.0))   # top edge
    after = node.visual_port_pos(vp["id"])
    assert after != before


def test_wire_endpoint_follows_move():
    c = _connected_pair()
    vp = _src_vp(c)
    node = c.get_node("node_0001")
    cid = c._connections[0]["id"]
    c._start_port_move(node, vp)
    c._update_port_move(QPointF(0.0, 40.0))   # left edge
    line = c._conn_items[cid]
    start = line.path().pointAtPercent(0.0)
    vp_pos = node.visual_port_pos(vp["id"])
    assert abs(start.x() - vp_pos.x()) < 0.5
    assert abs(start.y() - vp_pos.y()) < 0.5


def test_fanout_port_all_wires_follow():
    c = _connected_pair()
    c.add_part_at(_PART_C, QPointF(0.0, 200.0))
    node = c.get_node("node_0001")
    vp = node.visual_ports()[0]
    # second connection reusing node_0001's existing vp (fan-out)
    c._start_port_drag(node, vp)
    assert c._finish_port_drag("node_0003") is True
    fanout_conns = [cn for cn in c._connections
                    if cn["from"].get("visual_port_id") == vp["id"]]
    assert len(fanout_conns) == 2
    c._start_port_move(node, vp)
    c._update_port_move(QPointF(0.0, 20.0))   # left edge
    vp_pos = node.visual_port_pos(vp["id"])
    for cn in fanout_conns:
        start = c._conn_items[cn["id"]].path().pointAtPercent(0.0)
        assert abs(start.x() - vp_pos.x()) < 0.5
        assert abs(start.y() - vp_pos.y()) < 0.5


# ---------------------------------------------------------------------------
# finish / cancel
# ---------------------------------------------------------------------------

def test_release_confirms_move():
    c = _connected_pair()
    vp = _src_vp(c)
    node = c.get_node("node_0001")
    pos = node.visual_port_pos(vp["id"])
    _press(c, pos, alt=True)
    c._update_port_move(QPointF(0.0, 25.0))
    _release(c, QPointF(0.0, 25.0))
    assert c._port_move is None
    assert vp["side"] == "left"
    assert vp["offset"] == 25.0
    assert node.moving_port() is None


def test_escape_restores_original():
    c = _connected_pair()
    vp = _src_vp(c)
    orig_side, orig_off = vp["side"], vp["offset"]
    c._start_port_move(c.get_node("node_0001"), vp)
    c._update_port_move(QPointF(0.0, 10.0))
    assert vp["side"] == "left"
    _press_escape(c)
    assert c._port_move is None
    assert vp["side"] == orig_side
    assert vp["offset"] == orig_off


def test_right_click_restores_original():
    c = _connected_pair()
    vp = _src_vp(c)
    orig_side, orig_off = vp["side"], vp["offset"]
    c._start_port_move(c.get_node("node_0001"), vp)
    c._update_port_move(QPointF(70.0, 56.0))   # bottom edge
    assert vp["side"] == "bottom"
    # contextMenuEvent during move cancels and restores
    ev = QMouseEvent(
        QEvent.Type.MouseButtonPress, QPointF(c.mapFromScene(QPointF(70.0, 56.0))),
        Qt.MouseButton.RightButton, Qt.MouseButton.RightButton,
        Qt.KeyboardModifier.NoModifier,
    )
    c.contextMenuEvent(ev)
    assert c._port_move is None
    assert vp["side"] == orig_side
    assert vp["offset"] == orig_off


def test_move_does_not_select_node_or_wire():
    c = _connected_pair()
    vp = _src_vp(c)
    pos = c.get_node("node_0001").visual_port_pos(vp["id"])
    _press(c, pos, alt=True)
    c._update_port_move(QPointF(0.0, 30.0))
    assert c._selected_conn_id is None
    assert [i for i in c.scene().selectedItems()] == []


# ---------------------------------------------------------------------------
# persistence + regression
# ---------------------------------------------------------------------------

def test_export_import_keeps_moved_position():
    c = _connected_pair()
    vp = _src_vp(c)
    c._start_port_move(c.get_node("node_0001"), vp)
    c._update_port_move(QPointF(0.0, 18.0))   # left @ 18
    c._finish_port_move()
    data = c.export_canvas()
    c2 = _canvas()
    c2.import_canvas(data, _LIB)
    moved = c2.get_node("node_0001").visual_ports()[0]
    assert moved["side"] == "left"
    assert moved["offset"] == 18.0
    assert c2._port_move is None


def test_port_drag_connect_still_works():
    c = _connected_pair()
    before = len(c._connections)
    c.add_part_at(_PART_C, QPointF(0.0, 200.0))
    c._start_port_drag(c.get_node("node_0001"), _src_vp(c))
    assert c._finish_port_drag("node_0003") is True
    assert len(c._connections) == before + 1


def test_wire_select_delete_still_works():
    c = _connected_pair()
    cid = c._connections[0]["id"]
    c._set_selected_conn(cid)
    assert c._remove_connection(cid) is True
    assert all(cn["id"] != cid for cn in c._connections)


def test_right_click_connect_still_works():
    c = _canvas()
    c.add_part_at(_PART_A, QPointF(0.0, 0.0))
    c.add_part_at(_PART_B, QPointF(300.0, 0.0))
    c._begin_wire_from("node_0001", "bus")
    c._finish_wire("node_0002", "bus")
    assert len(c._connections) == 1


def test_edge_from_local_clamps_and_picks_side():
    node = PartNode(_PART_A, "node_0001")
    assert node.edge_from_local(QPointF(-50.0, 30.0))[0] == "left"
    assert node.edge_from_local(QPointF(_NODE_W + 50.0, 30.0))[0] == "right"
    assert node.edge_from_local(QPointF(70.0, -50.0))[0] == "top"
    assert node.edge_from_local(QPointF(70.0, _NODE_H + 50.0))[0] == "bottom"
    # offset clamped within node size
    side, off = node.edge_from_local(QPointF(-50.0, 999.0))
    assert 0.0 <= off <= _NODE_H
