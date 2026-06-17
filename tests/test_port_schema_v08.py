# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""PATCH_PORT_SCHEMA_V08 — part.json ports schema normalization (v1 -> v2)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF

_app = QApplication.instance() or QApplication(sys.argv)

from core.ports import (
    SCHEMA_VERSION, normalize_port, normalize_part, normalize_ports,
    base_port_type, derive_role, derive_direction, derive_width, is_legacy_part,
)
from ui.lib import load_parts
from ui.port_detail import build_node_info, render_detail
from ui.canvas import Canvas


# ---------------------------------------------------------------------------
# derivation helpers
# ---------------------------------------------------------------------------

def test_base_port_type():
    assert base_port_type("bus.master") == "bus"
    assert base_port_type("serial.uart") == "serial"
    assert base_port_type("clock") == "clock"
    assert base_port_type("") == ""
    assert base_port_type(None) == ""


def test_derive_role():
    assert derive_role("bus.master") == "master"
    assert derive_role("bus.slave") == "slave"
    assert derive_role("clock") is None
    assert derive_role("irq") is None


def test_derive_width():
    assert derive_width("bus.master") == 32
    assert derive_width("bus.slave") == 32
    assert derive_width("clock") == 1
    assert derive_width("reset") == 1
    assert derive_width("irq") == 1
    assert derive_width("serial.uart") == 1
    assert derive_width("gpio") == 1
    assert derive_width("video.rgb") == 24
    assert derive_width("debug.jtag") is None     # unknown -> None
    assert derive_width("") is None


def test_derive_direction_basic():
    assert derive_direction("bus.master") == "inout"
    assert derive_direction("bus.slave") == "inout"
    assert derive_direction("clock") == "in"
    assert derive_direction("reset") == "in"
    assert derive_direction("serial.uart") == "inout"
    assert derive_direction("gpio") == "inout"
    assert derive_direction("video.rgb") == "out"
    assert derive_direction("debug.jtag") == "inout"   # unknown -> safe default


def test_derive_direction_irq_is_part_specific():
    # CPU consumes IRQ (in); peripherals produce it (out)
    assert derive_direction("irq", part_id="cpu.ak32") == "in"
    assert derive_direction("irq", part_id="io.uart") == "out"
    assert derive_direction("irq", part_id="io.timer") == "out"
    assert derive_direction("irq", part_id="video.regs") == "out"
    assert derive_direction("irq", part_id=None) == "out"


# ---------------------------------------------------------------------------
# normalize_port — v1 fill-in
# ---------------------------------------------------------------------------

def test_normalize_v1_port_fills_fields():
    p = normalize_port({"name": "bus", "type": "bus.master"}, part_id="cpu.ak32")
    assert p["role"] == "master"
    assert p["direction"] == "inout"
    assert p["width"] == 32
    assert p["required"] is True
    assert p["description"] == ""


def test_normalize_v1_irq_uses_part_id():
    cpu_irq = normalize_port({"name": "irq", "type": "irq"}, part_id="cpu.ak32")
    uart_irq = normalize_port({"name": "irq", "type": "irq"}, part_id="io.uart")
    assert cpu_irq["direction"] == "in"
    assert cpu_irq["required"] is False          # irq optional by default
    assert uart_irq["direction"] == "out"


def test_normalize_unknown_type_is_safe():
    p = normalize_port({"name": "x", "type": "mystery.thing"})
    assert p["role"] is None
    assert p["direction"] == "inout"
    assert p["width"] is None
    assert p["required"] is True


def test_normalize_port_missing_keys_does_not_crash():
    p = normalize_port({})
    assert p["direction"] == "inout"
    assert p["width"] is None
    assert "role" in p and "required" in p and "description" in p


# ---------------------------------------------------------------------------
# normalize_port — v2 explicit values preserved
# ---------------------------------------------------------------------------

def test_normalize_v2_preserves_explicit_values():
    src = {"name": "bus", "type": "bus.slave", "role": "master",
           "direction": "out", "width": 8, "required": False, "description": "x"}
    p = normalize_port(src, part_id="mem.ram")
    assert p["role"] == "master"          # not overwritten by derive (slave)
    assert p["direction"] == "out"
    assert p["width"] == 8
    assert p["required"] is False
    assert p["description"] == "x"


def test_normalize_v2_width_null_preserved():
    p = normalize_port({"name": "jtag", "type": "debug.jtag", "width": None})
    assert p["width"] is None             # explicit None kept, not re-derived


# ---------------------------------------------------------------------------
# normalize_part
# ---------------------------------------------------------------------------

def test_normalize_part_sets_schema_version_and_keeps_extras():
    part = {"id": "cpu.ak32", "name": "AK32", "category": "cpu",
            "ports": [{"name": "bus", "type": "bus.master"}],
            "editable": [{"name": "program", "type": "asm"}]}
    out = normalize_part(part)
    assert out["schema_version"] == SCHEMA_VERSION
    assert out["editable"] == [{"name": "program", "type": "asm"}]   # preserved
    assert out["ports"][0]["role"] == "master"


def test_is_legacy_part():
    assert is_legacy_part({"id": "x", "ports": []}) is True
    assert is_legacy_part({"id": "x", "schema_version": 2}) is False


def test_normalize_ports_empty():
    assert normalize_ports(None) == []
    assert normalize_ports([]) == []


# ---------------------------------------------------------------------------
# load_parts — every library part is v2 after load
# ---------------------------------------------------------------------------

def test_load_parts_all_v2():
    cats, errors = load_parts()
    assert not errors, f"part load errors: {errors}"
    parts = [p for plist in cats.values() for p in plist]
    assert parts
    for part in parts:
        assert part.get("schema_version") == SCHEMA_VERSION, part.get("id")
        for port in part["ports"]:
            for key in ("name", "type", "role", "direction", "width",
                        "required", "description"):
                assert key in port, f"{part['id']}.{port.get('name')} missing {key}"


def test_load_parts_cpu_irq_in_uart_irq_out():
    cats, _ = load_parts()
    by_id = {p["id"]: p for plist in cats.values() for p in plist}

    def _port(pid, name):
        return next(pt for pt in by_id[pid]["ports"] if pt["name"] == name)

    assert _port("cpu.ak32", "irq")["direction"] == "in"
    assert _port("io.uart", "irq")["direction"] == "out"
    assert _port("io.timer", "irq")["direction"] == "out"
    assert _port("video.regs", "irq")["direction"] == "out"
    assert _port("cpu.ak32", "bus")["role"] == "master"
    assert _port("mem.ram", "bus")["role"] == "slave"


# ---------------------------------------------------------------------------
# Port Detail integration — explicit values shown; legacy falls back
# ---------------------------------------------------------------------------

def _canvas_with(part) -> Canvas:
    c = Canvas(log_fn=[].append)
    c.set_part_library({part["id"]: part})
    c.add_part_at(part, QPointF(0.0, 0.0))
    return c


def test_port_detail_shows_v2_fields():
    cpu = normalize_part({"id": "cpu.ak32", "name": "AK32 CPU", "category": "cpu",
                          "ports": [{"name": "bus", "type": "bus.master"},
                                    {"name": "irq", "type": "irq"}]})
    c = _canvas_with(cpu)
    info = build_node_info(c, "node_0001")
    bus = next(p for p in info["logical_ports"] if p["name"] == "bus")
    irq = next(p for p in info["logical_ports"] if p["name"] == "irq")
    assert bus["role"] == "master"
    assert bus["direction"] == "inout"
    assert bus["width"] == 32
    assert irq["direction"] == "in"            # CPU irq is input
    txt = render_detail(info)
    assert "role=master" in txt
    assert "dir=inout" in txt
    assert "width=32" in txt


def test_port_detail_legacy_fallback():
    # a legacy v1 part (no direction/width/role) still renders via type inference
    legacy = {"id": "leg.x", "name": "Legacy", "category": "io",
              "ports": [{"name": "bus", "type": "bus.slave"}]}
    c = _canvas_with(legacy)
    info = build_node_info(c, "node_0001")
    bus = next(p for p in info["logical_ports"] if p["name"] == "bus")
    assert "slave" in bus["direction"]         # direction_from_type fallback
    assert bus["width"] == "-"                 # no width -> placeholder
    txt = render_detail(info)
    assert "Logical Ports" in txt
