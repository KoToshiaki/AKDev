# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""PATCH_WIRE_HOVER_FEEDBACK_V05 — hover feedback for wiring interactions."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF

_app = QApplication.instance() or QApplication(sys.argv)

from ui.canvas import Canvas, ConnectionLine

_PART_A = {"id": "cpu.ak32", "name": "AK32", "category": "cpu"}
_PART_B = {"id": "mem.ram",  "name": "RAM",  "category": "mem"}
_LIB    = {_PART_A["id"]: _PART_A, _PART_B["id"]: _PART_B}


def _canvas() -> Canvas:
    return Canvas(log_fn=[].append)


def _connected_pair() -> Canvas:
    """Two nodes with one connection, so each end has a visual port."""
    c = _canvas()
    c.add_part_at(_PART_A, QPointF(0.0, 0.0))
    c.add_part_at(_PART_B, QPointF(300.0, 0.0))
    c._begin_wire_from("node_0001", "bus")
    c._finish_wire("node_0002", "bus")
    return c


def _src_vp(c: Canvas) -> dict:
    return c.get_node("node_0001").visual_ports()[0]


# ---------------------------------------------------------------------------
# visual port hover
# ---------------------------------------------------------------------------

def test_hover_vp_updates_state():
    c = _connected_pair()
    vp = _src_vp(c)
    pos = c.get_node("node_0001").visual_port_pos(vp["id"])
    c._update_hover(pos)
    assert c._hover_vp == {"node_id": "node_0001", "vp_id": vp["id"]}


def test_hover_vp_marks_partnode():
    c = _connected_pair()
    vp = _src_vp(c)
    pos = c.get_node("node_0001").visual_port_pos(vp["id"])
    c._update_hover(pos)
    assert c.get_node("node_0001").hover_port() == vp["id"]


def test_hover_vp_cleared_when_off_port():
    c = _connected_pair()
    vp = _src_vp(c)
    pos = c.get_node("node_0001").visual_port_pos(vp["id"])
    c._update_hover(pos)
    c._update_hover(QPointF(9999.0, 9999.0))
    assert c._hover_vp is None
    assert c.get_node("node_0001").hover_port() is None


def test_leave_event_clears_hover():
    c = _connected_pair()
    vp = _src_vp(c)
    pos = c.get_node("node_0001").visual_port_pos(vp["id"])
    c._update_hover(pos)
    c.leaveEvent(None)
    assert c._hover_vp is None
    assert c.get_node("node_0001").hover_port() is None


def test_hover_moves_between_ports():
    c = _connected_pair()
    vp1 = c.get_node("node_0001").visual_ports()[0]
    vp2 = c.get_node("node_0002").visual_ports()[0]
    c._update_hover(c.get_node("node_0001").visual_port_pos(vp1["id"]))
    c._update_hover(c.get_node("node_0002").visual_port_pos(vp2["id"]))
    assert c._hover_vp == {"node_id": "node_0002", "vp_id": vp2["id"]}
    assert c.get_node("node_0001").hover_port() is None
    assert c.get_node("node_0002").hover_port() == vp2["id"]


# ---------------------------------------------------------------------------
# wire hover (ConnectionLine)
# ---------------------------------------------------------------------------

def test_set_hovered_changes_pen():
    line = ConnectionLine("c1", "n1", "n2", kind="signal")
    base_width = line.pen().widthF()
    base_color = line.pen().color().name()
    line.set_hovered(True)
    assert line.is_hovered() is True
    assert (line.pen().widthF() != base_width
            or line.pen().color().name() != base_color)


def test_set_hovered_false_restores_pen():
    line = ConnectionLine("c1", "n1", "n2", kind="signal")
    base_width = line.pen().widthF()
    base_color = line.pen().color().name()
    line.set_hovered(True)
    line.set_hovered(False)
    assert abs(line.pen().widthF() - base_width) < 0.01
    assert line.pen().color().name() == base_color


def test_active_wins_over_hover():
    line = ConnectionLine("c1", "n1", "n2", kind="bus")
    line.set_active(True)
    active_width = line.pen().widthF()
    line.set_hovered(True)          # active still applied
    assert abs(line.pen().widthF() - active_width) < 0.01


def test_hover_restored_after_active_cleared():
    line = ConnectionLine("c1", "n1", "n2", kind="bus")
    base_width = line.pen().widthF()
    line.set_hovered(True)
    line.set_active(True)
    line.set_active(False)          # hover should remain in effect
    assert line.pen().widthF() > base_width


def test_connection_at_hits_path():
    c = _connected_pair()
    c.update_connections()
    line = next(iter(c._conn_items.values()))
    mid = line.path().pointAtPercent(0.5)
    assert c._connection_at(mid) is line


def test_update_hover_sets_wire():
    c = _connected_pair()
    c.update_connections()
    line = next(iter(c._conn_items.values()))
    mid = line.path().pointAtPercent(0.5)
    c._update_hover(mid)
    assert c._hover_conn_id == line.conn_id()
    assert line.is_hovered() is True


# ---------------------------------------------------------------------------
# port-drag drop highlight
# ---------------------------------------------------------------------------

def test_drop_highlight_on_other_node():
    c = _connected_pair()
    c._start_port_drag(c.get_node("node_0001"), _src_vp(c))
    c._update_drop_target("node_0002")
    assert c._hover_drop_node_id == "node_0002"
    assert c.get_node("node_0002").drop_highlight() is True


def test_drop_highlight_excludes_same_node():
    c = _connected_pair()
    c._start_port_drag(c.get_node("node_0001"), _src_vp(c))
    c._update_drop_target("node_0001")   # source part — not a candidate
    assert c._hover_drop_node_id is None
    assert c.get_node("node_0001").drop_highlight() is False


def test_drop_highlight_cleared_on_cancel():
    c = _connected_pair()
    c._start_port_drag(c.get_node("node_0001"), _src_vp(c))
    c._update_drop_target("node_0002")
    c._cancel_port_drag()
    assert c._hover_drop_node_id is None
    assert c.get_node("node_0002").drop_highlight() is False


def test_drop_highlight_cleared_on_finish():
    c = _connected_pair()
    c._start_port_drag(c.get_node("node_0001"), _src_vp(c))
    c._update_drop_target("node_0002")
    assert c._finish_port_drag("node_0002") is True
    assert c._hover_drop_node_id is None
    assert c.get_node("node_0002").drop_highlight() is False


def test_update_drop_target_noop_without_drag():
    c = _connected_pair()
    c._update_drop_target("node_0002")   # no active port drag
    assert c._hover_drop_node_id is None
    assert c.get_node("node_0002").drop_highlight() is False


# ---------------------------------------------------------------------------
# regression: existing flows are not broken
# ---------------------------------------------------------------------------

def test_port_drag_connect_still_works():
    c = _connected_pair()
    before = len(c.export_canvas()["connections"])
    c._start_port_drag(c.get_node("node_0001"), _src_vp(c))
    assert c._finish_port_drag("node_0002") is True
    assert len(c.export_canvas()["connections"]) == before + 1


def test_right_click_connect_still_works():
    c = _canvas()
    c.add_part_at(_PART_A, QPointF(0.0, 0.0))
    c.add_part_at(_PART_B, QPointF(300.0, 0.0))
    c._begin_wire_from("node_0001", "bus")
    c._finish_wire("node_0002", "bus")
    assert len(c.export_canvas()["connections"]) == 1


def test_export_import_roundtrip_with_hover_state():
    c = _connected_pair()
    # induce hover state, then round-trip
    vp = _src_vp(c)
    c._update_hover(c.get_node("node_0001").visual_port_pos(vp["id"]))
    data = c.export_canvas()
    c2 = _canvas()
    c2.import_canvas(data, _LIB)
    assert len(c2.export_canvas()["connections"]) == len(data["connections"])
    assert len(c2.get_all_nodes()) == len(c.get_all_nodes())
