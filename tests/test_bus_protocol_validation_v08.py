# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""PATCH_BUS_PROTOCOL_VALIDATION_V08 — warning-only bus-group diagnostics."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF

_app = QApplication.instance() or QApplication(sys.argv)

from core.bus_validation import (
    is_bus_port, build_bus_groups, validate_bus_group, validate_bus_protocol,
    BUS_NO_MASTER, BUS_MULTIPLE_MASTERS, BUS_NO_SLAVE,
)
from ui.canvas import Canvas
from ui.port_detail import build_node_info, build_wire_info, render_detail


def _codes(issues):
    return {i["code"] for i in issues}


# v2 parts
_CPU = {"id": "cpu.ak32", "name": "CPU", "category": "cpu", "schema_version": 2,
        "ports": [{"name": "bus", "type": "bus.master", "role": "master",
                   "direction": "inout", "width": 32, "required": True, "description": ""},
                  {"name": "clk", "type": "clock", "role": None,
                   "direction": "in", "width": 1, "required": True, "description": ""}]}
_RAM = {"id": "mem.ram", "name": "RAM", "category": "mem", "schema_version": 2,
        "ports": [{"name": "bus", "type": "bus.slave", "role": "slave",
                   "direction": "inout", "width": 32, "required": True, "description": ""}]}
_UART = {"id": "io.uart", "name": "UART", "category": "io", "schema_version": 2,
         "ports": [{"name": "bus", "type": "bus.slave", "role": "slave",
                    "direction": "inout", "width": 32, "required": True, "description": ""}]}
_BRIDGE = {"id": "bus.bridge", "name": "Bridge", "category": "bus", "schema_version": 2,
           "ports": [{"name": "master", "type": "bus.master", "role": "master",
                      "direction": "inout", "width": 32, "required": True, "description": ""},
                     {"name": "slave", "type": "bus.slave", "role": "slave",
                      "direction": "inout", "width": 32, "required": True, "description": ""}]}


def _nodes(*specs):
    return [{"node_id": nid, "part": part} for nid, part in specs]


def _conn(cid, fn, fp, tn, tp):
    return {"id": cid, "from": {"node_id": fn, "port": fp},
            "to": {"node_id": tn, "port": tp}}


# ---------------------------------------------------------------------------
# is_bus_port
# ---------------------------------------------------------------------------

def test_is_bus_port():
    assert is_bus_port({"type": "bus.master"}) is True
    assert is_bus_port({"type": "bus.slave"}) is True
    assert is_bus_port({"type": "bus"}) is True
    assert is_bus_port({"type": "clock"}) is False
    assert is_bus_port({"type": "irq"}) is False
    assert is_bus_port({"type": "video.rgb"}) is False
    assert is_bus_port(None) is False
    assert is_bus_port({}) is False


# ---------------------------------------------------------------------------
# build_bus_groups
# ---------------------------------------------------------------------------

def test_group_cpu_ram():
    nodes = _nodes(("n1", _CPU), ("n2", _RAM))
    conns = [_conn("c1", "n1", "bus", "n2", "bus")]
    groups = build_bus_groups(nodes, conns)
    assert len(groups) == 1
    g = groups[0]
    assert set(g["nodes"]) == {"n1", "n2"}
    assert len(g["masters"]) == 1 and len(g["slaves"]) == 1
    assert g["connections"] == ["c1"]


def test_non_bus_connection_ignored():
    # clk<->clk is not a bus edge -> no bus group
    nodes = _nodes(("n1", _CPU), ("n2", _RAM))
    conns = [{"id": "c1", "from": {"node_id": "n1", "port": "clk"},
              "to": {"node_id": "n2", "port": "clk"}}]
    # RAM has no clk port here -> not bus anyway; also clk isn't bus
    assert build_bus_groups(nodes, conns) == []


def test_bridge_splits_into_two_groups():
    # CPU.bus -> bridge.slave (group A) ; bridge.master -> RAM.bus (group B)
    nodes = _nodes(("n1", _CPU), ("nb", _BRIDGE), ("n2", _RAM))
    conns = [_conn("c1", "n1", "bus", "nb", "slave"),
             _conn("c2", "nb", "master", "n2", "bus")]
    groups = build_bus_groups(nodes, conns)
    assert len(groups) == 2
    for g in groups:                              # each group: 1 master + 1 slave
        assert len(g["masters"]) == 1 and len(g["slaves"]) == 1


def test_multiple_groups():
    nodes = _nodes(("n1", _CPU), ("n2", _RAM), ("n3", _CPU), ("n4", _RAM))
    conns = [_conn("c1", "n1", "bus", "n2", "bus"),
             _conn("c2", "n3", "bus", "n4", "bus")]
    assert len(build_bus_groups(nodes, conns)) == 2


# ---------------------------------------------------------------------------
# validate_bus_protocol — master/slave counts
# ---------------------------------------------------------------------------

def test_cpu_ram_ok():
    nodes = _nodes(("n1", _CPU), ("n2", _RAM))
    conns = [_conn("c1", "n1", "bus", "n2", "bus")]
    assert validate_bus_protocol(nodes, conns) == []


def test_cpu_ram_uart_ok():
    nodes = _nodes(("n1", _CPU), ("n2", _RAM), ("n3", _UART))
    conns = [_conn("c1", "n1", "bus", "n2", "bus"),
             _conn("c2", "n1", "bus", "n3", "bus")]
    assert validate_bus_protocol(nodes, conns) == []


def test_slaves_only_no_master():
    nodes = _nodes(("n2", _RAM), ("n3", _UART))
    conns = [_conn("c1", "n2", "bus", "n3", "bus")]
    assert _codes(validate_bus_protocol(nodes, conns)) == {BUS_NO_MASTER}


def test_masters_only_multiple_and_no_slave():
    nodes = _nodes(("n1", _CPU), ("n3", _CPU))
    conns = [_conn("c1", "n1", "bus", "n3", "bus")]
    codes = _codes(validate_bus_protocol(nodes, conns))
    assert BUS_MULTIPLE_MASTERS in codes
    assert BUS_NO_SLAVE in codes


def test_multiple_masters_with_slave():
    nodes = _nodes(("n1", _CPU), ("n3", _CPU), ("n2", _RAM))
    conns = [_conn("c1", "n1", "bus", "n2", "bus"),
             _conn("c2", "n3", "bus", "n2", "bus")]
    codes = _codes(validate_bus_protocol(nodes, conns))
    assert BUS_MULTIPLE_MASTERS in codes
    assert BUS_NO_SLAVE not in codes              # RAM slave is present


def test_target_cpu_annotated_in_details():
    nodes = _nodes(("n1", _CPU), ("n3", _CPU))
    conns = [_conn("c1", "n1", "bus", "n3", "bus")]
    issues = validate_bus_protocol(nodes, conns, target_cpu_id="n1")
    assert all("target_cpu_in_group" in i["details"] for i in issues)


# ---------------------------------------------------------------------------
# safety
# ---------------------------------------------------------------------------

def test_role_null_no_crash():
    part = {"id": "x.y", "ports": [{"name": "bus", "type": "bus"}]}   # bus, role None
    nodes = _nodes(("n1", part), ("n2", part))
    conns = [_conn("c1", "n1", "bus", "n2", "bus")]
    # both roles None -> no master, no slave -> warnings, but no crash
    codes = _codes(validate_bus_protocol(nodes, conns))
    assert BUS_NO_MASTER in codes and BUS_NO_SLAVE in codes


def test_missing_port_and_none_part_no_crash():
    nodes = _nodes(("n1", _CPU), ("n2", None))
    conns = [_conn("c1", "n1", "bus", "n2", "nope")]
    assert validate_bus_protocol(nodes, conns) == []   # not a resolvable bus edge


def test_empty_inputs():
    assert build_bus_groups([], []) == []
    assert validate_bus_protocol(None, None) == []


def test_validate_bus_group_direct():
    g = {"id": "g1", "nodes": ["n2"], "connections": ["c1"],
         "masters": [], "slaves": [{"node_id": "n2", "port": "bus"}]}
    assert _codes(validate_bus_group(g)) == {BUS_NO_MASTER}


# ---------------------------------------------------------------------------
# Canvas integration
# ---------------------------------------------------------------------------

def _canvas(log=None):
    return Canvas(log_fn=(log.append if log is not None else [].append))


def test_canvas_valid_bus_no_issue():
    log = []
    c = _canvas(log)
    c.add_part_at(_CPU, QPointF(0.0, 0.0))      # node_0001
    c.add_part_at(_RAM, QPointF(200.0, 0.0))    # node_0002
    conn = c.add_connection("node_0001", "bus", "node_0002", "bus")
    assert c.bus_validation() == []
    assert c.connection_bus_validation_issues(conn["id"]) == []
    assert not any("Bus validation warning" in m for m in log)


def test_canvas_multiple_masters_warns_but_creates():
    log = []
    c = _canvas(log)
    c.add_part_at(_CPU, QPointF(0.0, 0.0))      # node_0001
    c.add_part_at(_CPU, QPointF(0.0, 200.0))    # node_0002
    conn = c.add_connection("node_0001", "bus", "node_0002", "bus")
    assert c.get_connection(conn["id"]) is not None     # still created
    assert BUS_MULTIPLE_MASTERS in _codes(c.bus_validation())
    assert any("Bus validation warning" in m for m in log)


def test_canvas_no_master_warns():
    c = _canvas()
    c.add_part_at(_RAM, QPointF(0.0, 0.0))      # node_0001
    c.add_part_at(_UART, QPointF(200.0, 0.0))   # node_0002
    c.add_connection("node_0001", "bus", "node_0002", "bus")
    assert BUS_NO_MASTER in _codes(c.bus_validation())


def test_canvas_node_and_conn_bus_issues():
    c = _canvas()
    c.add_part_at(_CPU, QPointF(0.0, 0.0))      # node_0001
    c.add_part_at(_CPU, QPointF(0.0, 200.0))    # node_0002
    conn = c.add_connection("node_0001", "bus", "node_0002", "bus")
    assert BUS_MULTIPLE_MASTERS in _codes(c.node_bus_validation_issues("node_0001"))
    assert BUS_MULTIPLE_MASTERS in _codes(c.connection_bus_validation_issues(conn["id"]))


def test_canvas_non_bus_connection_no_bus_issue():
    # clk<->clk: CPU has clk, RAM has no clk -> not a bus edge anyway; ensure no bus issue
    c = _canvas()
    c.add_part_at(_CPU, QPointF(0.0, 0.0))      # node_0001 (has clk)
    c.add_part_at(_CPU, QPointF(0.0, 200.0))    # node_0002 (has clk)
    conn = c.add_connection("node_0001", "clk", "node_0002", "clk")
    assert c.connection_bus_validation_issues(conn["id"]) == []


def test_port_and_bus_validation_coexist():
    # CPU.bus (32, master) <-> RAM.bus (32, slave): no port issue, no bus issue
    c = _canvas()
    c.add_part_at(_CPU, QPointF(0.0, 0.0))
    c.add_part_at(_RAM, QPointF(200.0, 0.0))
    conn = c.add_connection("node_0001", "bus", "node_0002", "bus")
    assert c.connection_validation(conn["id"]) == []        # port layer
    assert c.connection_bus_validation_issues(conn["id"]) == []  # bus layer


# ---------------------------------------------------------------------------
# Port Detail
# ---------------------------------------------------------------------------

def test_port_detail_node_shows_bus_issue():
    c = _canvas()
    c.add_part_at(_CPU, QPointF(0.0, 0.0))
    c.add_part_at(_CPU, QPointF(0.0, 200.0))
    c.add_connection("node_0001", "bus", "node_0002", "bus")
    info = build_node_info(c, "node_0001")
    assert BUS_MULTIPLE_MASTERS in _codes(info["validation"])
    txt = render_detail(info)
    assert "BUS_MULTIPLE_MASTERS" in txt


def test_port_detail_wire_shows_bus_issue():
    c = _canvas()
    c.add_part_at(_CPU, QPointF(0.0, 0.0))
    c.add_part_at(_CPU, QPointF(0.0, 200.0))
    conn = c.add_connection("node_0001", "bus", "node_0002", "bus")
    info = build_wire_info(c, conn["id"])
    assert BUS_MULTIPLE_MASTERS in _codes(info["validation"])
    txt = render_detail(info)
    assert "Validation" in txt
    assert "BUS_MULTIPLE_MASTERS" in txt


def test_port_detail_valid_bus_ok():
    c = _canvas()
    c.add_part_at(_CPU, QPointF(0.0, 0.0))
    c.add_part_at(_RAM, QPointF(200.0, 0.0))
    conn = c.add_connection("node_0001", "bus", "node_0002", "bus")
    info = build_wire_info(c, conn["id"])
    assert info["validation"] == []
    assert "OK" in render_detail(info)
