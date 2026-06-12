# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""PATCH_WIRING_PORTS_V05 — Dynamic Visual Port tests."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPainterPath
from PySide6.QtCore import QPointF

_app = QApplication.instance() or QApplication(sys.argv)

from ui.canvas import Canvas, PartNode, _NODE_W, _NODE_H, _VP_RADIUS

_PART_A = {"id": "cpu.ak32", "name": "AK32", "category": "cpu"}
_PART_B = {"id": "mem.ram",  "name": "RAM",  "category": "mem"}
_LIB    = {_PART_A["id"]: _PART_A, _PART_B["id"]: _PART_B}


def _canvas() -> Canvas:
    return Canvas(log_fn=[].append)


def _pair() -> Canvas:
    c = _canvas()
    c.add_part_at(_PART_A, QPointF(0.0, 0.0))
    c.add_part_at(_PART_B, QPointF(200.0, 0.0))
    return c


# ---------------------------------------------------------------------------
# legacy port dot is hidden; parts start with 0 visual ports
# ---------------------------------------------------------------------------

def test_legacy_port_dot_hidden():
    node = PartNode(_PART_A, "node_0001")
    assert node._port_dot is not None          # kept for compat
    assert not node._port_dot.isVisible()      # but not shown on canvas


def test_node_starts_with_zero_visual_ports():
    node = PartNode(_PART_A, "node_0001")
    assert node.visual_ports() == []


# ---------------------------------------------------------------------------
# PartNode visual port API
# ---------------------------------------------------------------------------

def test_add_and_get_visual_port():
    node = PartNode(_PART_A, "node_0001")
    vp = {"id": "vp_0001", "side": "right", "offset": 20.0, "kind": "bus"}
    node.add_visual_port(vp)
    assert node.get_visual_port("vp_0001") is vp
    assert len(node.visual_ports()) == 1


def test_remove_visual_port():
    node = PartNode(_PART_A, "node_0001")
    node.add_visual_port({"id": "vp_0001", "side": "right", "offset": 20.0})
    node.remove_visual_port("vp_0001")
    assert node.visual_ports() == []


def test_visual_port_pos_each_side():
    node = PartNode(_PART_A, "node_0001")
    node.setPos(QPointF(10.0, 20.0))
    node.set_visual_ports([
        {"id": "r", "side": "right",  "offset": 30.0},
        {"id": "l", "side": "left",   "offset": 30.0},
        {"id": "t", "side": "top",    "offset": 40.0},
        {"id": "b", "side": "bottom", "offset": 40.0},
    ])
    assert node.visual_port_pos("r") == QPointF(10.0 + _NODE_W, 20.0 + 30.0)
    assert node.visual_port_pos("l") == QPointF(10.0, 20.0 + 30.0)
    assert node.visual_port_pos("t") == QPointF(10.0 + 40.0, 20.0)
    assert node.visual_port_pos("b") == QPointF(10.0 + 40.0, 20.0 + _NODE_H)


def test_visual_port_pos_missing_returns_none():
    node = PartNode(_PART_A, "node_0001")
    assert node.visual_port_pos("ghost") is None


# ---------------------------------------------------------------------------
# _create_visual_port + stacking
# ---------------------------------------------------------------------------

def test_create_visual_port_fields():
    c = _pair()
    vp = c._create_visual_port("node_0001", "right", "bus")
    assert vp["id"].startswith("vp_")
    assert vp["side"] == "right"
    assert vp["kind"] == "bus"
    assert vp["label"] == "bus"
    assert vp["locked"] is False


def test_create_visual_port_stacks_offsets():
    c = _pair()
    a = c._create_visual_port("node_0001", "right", "bus")
    b = c._create_visual_port("node_0001", "right", "bus")
    assert a["offset"] != b["offset"]


# ---------------------------------------------------------------------------
# _finish_wire creates visual ports and links the connection
# ---------------------------------------------------------------------------

def test_finish_wire_creates_visual_ports_on_both_nodes():
    c = _pair()
    c._begin_wire_from("node_0001", "bus")
    c._finish_wire("node_0002", "bus")
    assert len(c.get_node("node_0001").visual_ports()) == 1
    assert len(c.get_node("node_0002").visual_ports()) == 1


def test_finish_wire_connection_references_visual_ports():
    c = _pair()
    c._begin_wire_from("node_0001", "bus")
    c._finish_wire("node_0002", "bus")
    conn = c._connections[0]
    from_vp = c.get_node("node_0001").visual_ports()[0]["id"]
    to_vp = c.get_node("node_0002").visual_ports()[0]["id"]
    assert conn["from"]["visual_port_id"] == from_vp
    assert conn["to"]["visual_port_id"] == to_vp
    assert conn["from"]["logical_port"] == "bus"


def test_finish_wire_endpoint_at_visual_port():
    c = _pair()
    c._begin_wire_from("node_0001", "bus")
    c._finish_wire("node_0002", "bus")
    conn = c._connections[0]
    line = c._conn_items[conn["id"]]
    vp_pos = c.get_node("node_0001").visual_port_pos(conn["from"]["visual_port_id"])
    start = line.path().elementAt(0)
    assert start.x == pytest.approx(vp_pos.x())
    assert start.y == pytest.approx(vp_pos.y())


def test_visual_port_follows_node_move():
    c = _pair()
    c._begin_wire_from("node_0001", "bus")
    c._finish_wire("node_0002", "bus")
    conn = c._connections[0]
    c.get_node("node_0001").setPos(QPointF(60.0, 40.0))
    c.update_connections()
    vp_pos = c.get_node("node_0001").visual_port_pos(conn["from"]["visual_port_id"])
    start = c._conn_items[conn["id"]].path().elementAt(0)
    assert start.x == pytest.approx(vp_pos.x())
    assert start.y == pytest.approx(vp_pos.y())


# ---------------------------------------------------------------------------
# move / arrange API
# ---------------------------------------------------------------------------

def test_set_visual_port_offset():
    c = _pair()
    vp = c._create_visual_port("node_0001", "right", "bus")
    assert c.set_visual_port_offset("node_0001", vp["id"], 40.0) is True
    assert c.get_node("node_0001").get_visual_port(vp["id"])["offset"] == 40.0


def test_set_visual_port_offset_locked_rejected():
    c = _pair()
    vp = c._create_visual_port("node_0001", "right", "bus")
    vp["locked"] = True
    assert c.set_visual_port_offset("node_0001", vp["id"], 40.0) is False


def test_set_visual_port_side():
    c = _pair()
    vp = c._create_visual_port("node_0001", "right", "bus")
    assert c.set_visual_port_side("node_0001", vp["id"], "top") is True
    assert c.get_node("node_0001").get_visual_port(vp["id"])["side"] == "top"


def test_arrange_visual_ports_distributes():
    c = _pair()
    a = c._create_visual_port("node_0001", "right", "bus")
    b = c._create_visual_port("node_0001", "right", "bus")
    c.arrange_visual_ports("node_0001")
    offsets = sorted([
        c.get_node("node_0001").get_visual_port(a["id"])["offset"],
        c.get_node("node_0001").get_visual_port(b["id"])["offset"],
    ])
    # two ports on a 56px edge -> 1/3 and 2/3
    assert offsets[0] == pytest.approx(_NODE_H * 1 / 3, abs=0.5)
    assert offsets[1] == pytest.approx(_NODE_H * 2 / 3, abs=0.5)


def test_arrange_respects_locked():
    c = _pair()
    a = c._create_visual_port("node_0001", "right", "bus")
    a["locked"] = True
    a["offset"] = 5.0
    c._create_visual_port("node_0001", "right", "bus")
    c.arrange_visual_ports("node_0001")
    assert c.get_node("node_0001").get_visual_port(a["id"])["offset"] == 5.0


# ---------------------------------------------------------------------------
# export / import round-trip
# ---------------------------------------------------------------------------

def test_export_includes_visual_ports():
    c = _pair()
    c._create_visual_port("node_0001", "right", "bus")
    entry = [e for e in c.export_parts() if e["node_id"] == "node_0001"][0]
    assert "visual_ports" in entry
    assert entry["visual_ports"][0]["side"] == "right"


def test_export_omits_visual_ports_when_empty():
    c = _pair()
    entry = [e for e in c.export_parts() if e["node_id"] == "node_0001"][0]
    assert "visual_ports" not in entry


def test_import_restores_visual_ports():
    c = _pair()
    c._begin_wire_from("node_0001", "bus")
    c._finish_wire("node_0002", "bus")
    data = c.export_canvas()
    c2 = _canvas()
    c2.import_canvas(data, _LIB)
    assert len(c2.get_node("node_0001").visual_ports()) == 1
    conn = c2._connections[0]
    assert "visual_port_id" in conn["from"]


def test_import_bumps_vp_seq_no_collision():
    c = _pair()
    c._begin_wire_from("node_0001", "bus")
    c._finish_wire("node_0002", "bus")
    data = c.export_canvas()
    c2 = _canvas()
    c2.import_canvas(data, _LIB)
    new_id = c2._next_vp_id()
    existing_ids = {vp["id"] for n in c2.get_all_nodes() for vp in n.visual_ports()}
    assert new_id not in existing_ids


# ---------------------------------------------------------------------------
# delete sync: orphan visual ports pruned
# ---------------------------------------------------------------------------

def test_delete_node_prunes_orphan_visual_port():
    c = _pair()
    c._begin_wire_from("node_0001", "bus")
    c._finish_wire("node_0002", "bus")
    assert len(c.get_node("node_0002").visual_ports()) == 1
    c._remove_node("node_0001")          # removes connection
    # node_0002's visual port is now orphaned -> pruned
    assert c.get_node("node_0002").visual_ports() == []
    assert c._connections == []


# ---------------------------------------------------------------------------
# backward compatibility: connections without a visual port still work
# ---------------------------------------------------------------------------

def test_legacy_connection_without_vp_uses_edge():
    c = _pair()
    conn = c.add_connection("node_0001", "bus", "node_0002", "bus")
    assert "visual_port_id" not in conn["from"]
    line = c._conn_items[conn["id"]]
    start = line.path().elementAt(0)
    # falls back to node right edge raw position (no grid gap)
    assert start.x == pytest.approx(_NODE_W)
    assert start.y == pytest.approx(_NODE_H / 2)


# ---------------------------------------------------------------------------
# Bug 1: visual port dots stay inside the node's bounding rect (no ghost)
# ---------------------------------------------------------------------------

def _curve_types(line):
    p = line.path()
    return [p.elementAt(i).type for i in range(p.elementCount())]


def test_boundingrect_covers_edge_visual_port_dots():
    node = PartNode(_PART_A, "node_0001")
    br = node.boundingRect()
    # right/left/top/bottom dots are centered on the edges with _VP_RADIUS;
    # the bounding rect must include them so moving the node clears the old dots.
    assert br.right() >= _NODE_W + _VP_RADIUS
    assert br.left() <= -_VP_RADIUS
    assert br.top() <= -_VP_RADIUS
    assert br.bottom() >= _NODE_H + _VP_RADIUS


# ---------------------------------------------------------------------------
# Bug 2: dynamic (visual port) connections are curved; legacy stays grid
# ---------------------------------------------------------------------------

def test_dynamic_connection_is_curved():
    c = _pair()
    c._begin_wire_from("node_0001", "bus")
    c._finish_wire("node_0002", "bus")
    line = c._conn_items[c._connections[0]["id"]]
    assert QPainterPath.ElementType.CurveToElement in _curve_types(line)


def test_dynamic_connection_starts_at_visual_port():
    c = _pair()
    c._begin_wire_from("node_0001", "bus")
    c._finish_wire("node_0002", "bus")
    conn = c._connections[0]
    line = c._conn_items[conn["id"]]
    vp_pos = c.get_node("node_0001").visual_port_pos(conn["from"]["visual_port_id"])
    start = line.path().elementAt(0)        # MoveTo
    assert start.x == pytest.approx(vp_pos.x())
    assert start.y == pytest.approx(vp_pos.y())


def test_legacy_connection_not_curved():
    c = _pair()
    conn = c.add_connection("node_0001", "bus", "node_0002", "bus")
    line = c._conn_items[conn["id"]]
    assert QPainterPath.ElementType.CurveToElement not in _curve_types(line)


def test_curve_follows_node_move():
    c = _pair()
    c._begin_wire_from("node_0001", "bus")
    c._finish_wire("node_0002", "bus")
    conn = c._connections[0]
    c.get_node("node_0001").setPos(QPointF(70.0, 90.0))
    c.update_connections()
    vp_pos = c.get_node("node_0001").visual_port_pos(conn["from"]["visual_port_id"])
    start = c._conn_items[conn["id"]].path().elementAt(0)
    assert start.x == pytest.approx(vp_pos.x())
    assert start.y == pytest.approx(vp_pos.y())
