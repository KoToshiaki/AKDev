# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""PATCH_PORT_DIRECTION_WIDTH_VALIDATION_V08 — warning-only connection validation."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF

_app = QApplication.instance() or QApplication(sys.argv)

from core.port_validation import (
    find_port, validate_port_pair, validate_connection, validate_node_connections,
    PORT_MULTIPLE_DRIVERS, PORT_NO_DRIVER, PORT_ROLE_MISMATCH, PORT_WIDTH_MISMATCH,
    PORT_KIND_MISMATCH, PORT_NOT_FOUND, SELF_CONNECTION,
)
from ui.canvas import Canvas
from ui.port_detail import build_node_info, build_wire_info, render_detail


def _codes(issues):
    return {i["code"] for i in issues}


# v2 parts for canvas integration
_CPU = {"id": "cpu.ak32", "name": "CPU", "category": "cpu", "schema_version": 2,
        "ports": [{"name": "bus", "type": "bus.master", "role": "master",
                   "direction": "inout", "width": 32, "required": True, "description": ""},
                  {"name": "irq", "type": "irq", "role": None,
                   "direction": "in", "width": 1, "required": False, "description": ""}]}
_RAM = {"id": "mem.ram", "name": "RAM", "category": "mem", "schema_version": 2,
        "ports": [{"name": "bus", "type": "bus.slave", "role": "slave",
                   "direction": "inout", "width": 32, "required": True, "description": ""}]}
_GPIO = {"id": "io.gpio", "name": "GPIO", "category": "io", "schema_version": 2,
         "ports": [{"name": "gpio", "type": "gpio", "role": None,
                    "direction": "inout", "width": 1, "required": False, "description": ""}]}


# ---------------------------------------------------------------------------
# direction
# ---------------------------------------------------------------------------

def test_out_in_ok():
    assert validate_port_pair({"name": "a", "direction": "out"},
                              {"name": "b", "direction": "in"}) == []


def test_in_out_ok():
    assert validate_port_pair({"name": "a", "direction": "in"},
                              {"name": "b", "direction": "out"}) == []


def test_inout_inout_ok():
    assert validate_port_pair({"name": "a", "direction": "inout"},
                              {"name": "b", "direction": "inout"}) == []


def test_inout_in_and_inout_out_ok():
    assert validate_port_pair({"name": "a", "direction": "inout"},
                              {"name": "b", "direction": "in"}) == []
    assert validate_port_pair({"name": "a", "direction": "inout"},
                              {"name": "b", "direction": "out"}) == []


def test_out_out_multiple_drivers():
    assert _codes(validate_port_pair({"name": "a", "direction": "out"},
                                     {"name": "b", "direction": "out"})) == {PORT_MULTIPLE_DRIVERS}


def test_in_in_no_driver():
    assert _codes(validate_port_pair({"name": "a", "direction": "in"},
                                     {"name": "b", "direction": "in"})) == {PORT_NO_DRIVER}


def test_direction_missing_skips():
    assert validate_port_pair({"name": "a"}, {"name": "b", "direction": "out"}) == []


# ---------------------------------------------------------------------------
# role
# ---------------------------------------------------------------------------

def test_master_slave_ok():
    assert validate_port_pair(
        {"name": "a", "role": "master", "direction": "inout", "type": "bus.master", "width": 32},
        {"name": "b", "role": "slave", "direction": "inout", "type": "bus.slave", "width": 32}) == []


def test_master_master_mismatch():
    issues = validate_port_pair(
        {"name": "a", "role": "master", "direction": "inout", "type": "bus.master", "width": 32},
        {"name": "b", "role": "master", "direction": "inout", "type": "bus.master", "width": 32})
    assert _codes(issues) == {PORT_ROLE_MISMATCH}


def test_slave_slave_mismatch():
    issues = validate_port_pair(
        {"name": "a", "role": "slave", "direction": "inout", "type": "bus.slave", "width": 32},
        {"name": "b", "role": "slave", "direction": "inout", "type": "bus.slave", "width": 32})
    assert _codes(issues) == {PORT_ROLE_MISMATCH}


def test_role_none_skips():
    assert validate_port_pair({"name": "a", "role": None, "direction": "inout"},
                              {"name": "b", "role": None, "direction": "inout"}) == []


# ---------------------------------------------------------------------------
# width
# ---------------------------------------------------------------------------

def test_width_match_ok():
    assert validate_port_pair({"name": "a", "width": 32}, {"name": "b", "width": 32}) == []


def test_width_mismatch():
    assert PORT_WIDTH_MISMATCH in _codes(
        validate_port_pair({"name": "a", "width": 32}, {"name": "b", "width": 1}))


def test_width_none_skips():
    assert validate_port_pair({"name": "a", "width": None}, {"name": "b", "width": 32}) == []
    assert validate_port_pair({"name": "a", "width": None}, {"name": "b", "width": None}) == []


# ---------------------------------------------------------------------------
# kind / unknown / safety
# ---------------------------------------------------------------------------

def test_kind_same_ok():
    assert validate_port_pair({"name": "a", "type": "bus.master"},
                              {"name": "b", "type": "bus.slave"}) == []


def test_kind_mismatch():
    assert PORT_KIND_MISMATCH in _codes(
        validate_port_pair({"name": "a", "type": "bus.master"},
                           {"name": "b", "type": "clock"}))


def test_unknown_type_no_crash():
    issues = validate_port_pair({"name": "a", "type": "mystery.x"},
                                {"name": "b", "type": "other.y"})
    assert isinstance(issues, list)   # may flag kind mismatch, must not raise


def test_none_ports_no_crash():
    assert validate_port_pair(None, None) == []
    assert validate_port_pair({}, {}) == []


def test_find_port():
    assert find_port(_CPU, "bus")["type"] == "bus.master"
    assert find_port(_CPU, "nope") is None
    assert find_port(None, "bus") is None


# ---------------------------------------------------------------------------
# validate_connection — resolves + normalizes
# ---------------------------------------------------------------------------

def test_validate_connection_ok():
    assert validate_connection(_CPU, "bus", _RAM, "bus",
                               from_node_id="n1", to_node_id="n2", conn_id="c1") == []


def test_validate_connection_width_and_kind_mismatch():
    issues = validate_connection(_CPU, "bus", _GPIO, "gpio",
                                 from_node_id="n1", to_node_id="n2", conn_id="c1")
    codes = _codes(issues)
    assert PORT_WIDTH_MISMATCH in codes
    assert PORT_KIND_MISMATCH in codes


def test_validate_connection_irq_two_outputs_multiple_drivers():
    # v1 parts (no explicit direction) — normalization derives irq=out for peripherals
    uart = {"id": "io.uart", "ports": [{"name": "irq", "type": "irq"}]}
    timer = {"id": "io.timer", "ports": [{"name": "irq", "type": "irq"}]}
    issues = validate_connection(uart, "irq", timer, "irq")
    assert PORT_MULTIPLE_DRIVERS in _codes(issues)


def test_validate_connection_cpu_irq_to_uart_irq_ok():
    cpu = {"id": "cpu.ak32", "ports": [{"name": "irq", "type": "irq"}]}
    uart = {"id": "io.uart", "ports": [{"name": "irq", "type": "irq"}]}
    # CPU irq=in, UART irq=out -> in/out OK
    assert validate_connection(cpu, "irq", uart, "irq") == []


def test_validate_connection_port_not_found():
    issues = validate_connection(_CPU, "nope", _RAM, "bus", conn_id="c1")
    assert _codes(issues) == {PORT_NOT_FOUND}
    assert issues[0]["conn_id"] == "c1"


def test_validate_connection_none_parts_not_found():
    assert _codes(validate_connection(None, "bus", None, "bus")) == {PORT_NOT_FOUND}


def test_issue_has_endpoint_and_required_keys():
    issues = validate_connection(_CPU, "bus", _GPIO, "gpio",
                                 from_node_id="n1", to_node_id="n2", conn_id="c9")
    assert issues
    for i in issues:
        for k in ("severity", "code", "message", "details",
                  "from_node", "from_port", "to_node", "to_port", "conn_id"):
            assert k in i
        assert i["from_node"] == "n1" and i["to_node"] == "n2" and i["conn_id"] == "c9"


def test_validate_node_connections_self_connection():
    nodes = [{"node_id": "n1", "part": _CPU}]
    conns = [{"id": "c1", "from": {"node_id": "n1", "port": "bus"},
              "to": {"node_id": "n1", "port": "bus"}}]
    assert SELF_CONNECTION in _codes(validate_node_connections(nodes, conns))


# ---------------------------------------------------------------------------
# Canvas integration — warning only (connection always created)
# ---------------------------------------------------------------------------

def _canvas(log=None):
    return Canvas(log_fn=(log.append if log is not None else [].append))


def test_canvas_valid_connection_no_issues():
    log = []
    c = _canvas(log)
    c.add_part_at(_CPU, QPointF(0.0, 0.0))     # node_0001
    c.add_part_at(_RAM, QPointF(200.0, 0.0))   # node_0002
    conn = c.add_connection("node_0001", "bus", "node_0002", "bus")
    assert conn["validation"] == []
    assert c.connection_validation(conn["id"]) == []
    assert not any("Validation warning" in m for m in log)


def test_canvas_mismatch_warns_but_creates():
    log = []
    c = _canvas(log)
    c.add_part_at(_CPU, QPointF(0.0, 0.0))      # node_0001
    c.add_part_at(_GPIO, QPointF(200.0, 0.0))   # node_0002
    conn = c.add_connection("node_0001", "bus", "node_0002", "gpio")
    # connection is still created
    assert c.get_connection(conn["id"]) is not None
    codes = _codes(conn["validation"])
    assert PORT_WIDTH_MISMATCH in codes
    assert any("Validation warning" in m for m in log)


def test_canvas_role_mismatch_two_masters():
    c = _canvas()
    c.add_part_at(_CPU, QPointF(0.0, 0.0))      # node_0001
    c.add_part_at(_CPU, QPointF(0.0, 200.0))    # node_0002
    conn = c.add_connection("node_0001", "bus", "node_0002", "bus")
    assert PORT_ROLE_MISMATCH in _codes(conn["validation"])


def test_canvas_missing_validation_key_recomputes():
    c = _canvas()
    c.add_part_at(_CPU, QPointF(0.0, 0.0))
    c.add_part_at(_RAM, QPointF(200.0, 0.0))
    conn = c.add_connection("node_0001", "bus", "node_0002", "bus")
    del conn["validation"]                       # simulate an imported/legacy conn
    assert c.connection_validation(conn["id"]) == []   # recomputed, no crash


def test_canvas_node_validation_issues():
    c = _canvas()
    c.add_part_at(_CPU, QPointF(0.0, 0.0))
    c.add_part_at(_GPIO, QPointF(200.0, 0.0))
    c.add_connection("node_0001", "bus", "node_0002", "gpio")
    issues = c.node_validation_issues("node_0001")
    assert PORT_WIDTH_MISMATCH in _codes(issues)


# ---------------------------------------------------------------------------
# Port Detail rendering
# ---------------------------------------------------------------------------

def test_port_detail_wire_ok():
    c = _canvas()
    c.add_part_at(_CPU, QPointF(0.0, 0.0))
    c.add_part_at(_RAM, QPointF(200.0, 0.0))
    conn = c.add_connection("node_0001", "bus", "node_0002", "bus")
    info = build_wire_info(c, conn["id"])
    assert info["validation"] == []
    txt = render_detail(info)
    assert "Validation" in txt
    assert "OK" in txt


def test_port_detail_wire_warning():
    c = _canvas()
    c.add_part_at(_CPU, QPointF(0.0, 0.0))
    c.add_part_at(_GPIO, QPointF(200.0, 0.0))
    conn = c.add_connection("node_0001", "bus", "node_0002", "gpio")
    info = build_wire_info(c, conn["id"])
    assert info["validation"]
    txt = render_detail(info)
    assert "Validation" in txt
    assert "PORT_WIDTH_MISMATCH" in txt


def test_port_detail_node_shows_validation():
    c = _canvas()
    c.add_part_at(_CPU, QPointF(0.0, 0.0))
    c.add_part_at(_GPIO, QPointF(200.0, 0.0))
    c.add_connection("node_0001", "bus", "node_0002", "gpio")
    info = build_node_info(c, "node_0001")
    txt = render_detail(info)
    assert "Validation" in txt
    assert "PORT_WIDTH_MISMATCH" in txt
