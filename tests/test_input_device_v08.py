# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""PATCH_INPUT_DEVICE_V08 — io.input MMIO device, read with the existing LD instruction."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF

_app = QApplication.instance() or QApplication(sys.argv)

from core.devices import (
    device_kind, device_role, is_addressable_kind, is_runtime_backed_kind,
    make_device_spec, assign_mmio_bases,
)
from core.dev import InputPart
from core.circuit import resolve_circuit, build_address_map_from_devices, validate_address_map
from ui.win import MainWin
from ui.lib import load_parts
from ui.address_map_editor import COL_NODE
from core.project import create_project

_CPU   = {"id": "cpu.ak32", "name": "AK32", "category": "cpu"}
_RAM   = {"id": "mem.ram",  "name": "RAM",  "category": "mem"}
_UART  = {"id": "io.uart",  "name": "UART", "category": "io"}
_INPUT = {"id": "io.input", "name": "Input", "category": "io"}
_HELLO_WORLD  = Path(__file__).parent / "test" / "hello_world.asm"
_RAM_SELFTEST = Path(__file__).parent / "test" / "ram_selftest.asm"

# Reads the Input KEY_STATE (Input window at 0x0110 when a UART occupies 0x0100).
_INPUT_READ_ASM = "LDI r1, 0x0110\nLD r2, [r1]\nHALT\n"


def _nodes(*specs):
    return [{"node_id": nid, "category": cat, "part_id": pid, "name": pid}
            for (nid, cat, pid) in specs]


# ---------------------------------------------------------------------------
# part / library
# ---------------------------------------------------------------------------

def test_io_input_in_library():
    cats, errors = load_parts()
    assert not errors, errors
    ids = {p["id"] for plist in cats.values() for p in plist}
    assert "io.input" in ids
    part = next(p for plist in cats.values() for p in plist if p["id"] == "io.input")
    assert part.get("schema_version") == 2
    bus = next(pt for pt in part["ports"] if pt["name"] == "bus")
    assert bus["role"] == "slave" and bus["direction"] == "inout"


# ---------------------------------------------------------------------------
# device registry
# ---------------------------------------------------------------------------

def test_device_kind_and_role():
    assert device_kind({"id": "io.input"}) == "input"
    assert device_role("input") == "mmio"
    assert is_addressable_kind("input") is True
    assert is_runtime_backed_kind("input") is True


def test_make_device_spec_input():
    s = make_device_spec("n4", _INPUT, mode="circuit")
    assert s["kind"] == "input"
    assert s["role"] == "mmio"
    assert s["addressable"] is True
    assert s["runtime_backed"] is True
    assert s["runtime_id"] == "sim_input"
    assert s["label"] == "INPUT"


# ---------------------------------------------------------------------------
# assign_mmio_bases — kind-based runtime-backing
# ---------------------------------------------------------------------------

def test_single_uart_unchanged():
    out = assign_mmio_bases([make_device_spec("n3", _UART, mode="circuit")])
    assert out[0]["base"] == 0x0100
    assert out[0]["runtime_backed"] is True
    assert out[0]["runtime_id"] == "sim_uart"


def test_multiple_uart_first_backed_only():
    out = assign_mmio_bases([make_device_spec("n3", _UART, mode="circuit"),
                             make_device_spec("n4", _UART, mode="circuit")])
    assert (out[0]["base"], out[0]["runtime_backed"]) == (0x0100, True)
    assert (out[1]["base"], out[1]["runtime_backed"]) == (0x0110, False)
    assert out[1]["runtime_id"] is None


def test_uart_and_input_both_backed():
    out = assign_mmio_bases([make_device_spec("n3", _UART, mode="circuit"),
                             make_device_spec("n4", _INPUT, mode="circuit")])
    uart = next(s for s in out if s["kind"] == "uart")
    inp = next(s for s in out if s["kind"] == "input")
    assert (uart["base"], uart["runtime_backed"], uart["runtime_id"]) == (0x0100, True, "sim_uart")
    assert (inp["base"], inp["runtime_backed"], inp["runtime_id"]) == (0x0110, True, "sim_input")


def test_input_then_uart_order():
    # encounter order decides windows: input first -> 0x0100, uart -> 0x0110
    out = assign_mmio_bases([make_device_spec("n4", _INPUT, mode="circuit"),
                             make_device_spec("n3", _UART, mode="circuit")])
    inp = next(s for s in out if s["kind"] == "input")
    uart = next(s for s in out if s["kind"] == "uart")
    assert inp["base"] == 0x0100 and inp["runtime_backed"] is True
    assert uart["base"] == 0x0110 and uart["runtime_backed"] is True


def test_two_inputs_first_backed_only():
    out = assign_mmio_bases([make_device_spec("n4", _INPUT, mode="circuit"),
                             make_device_spec("n5", _INPUT, mode="circuit")])
    assert out[0]["runtime_backed"] is True and out[0]["runtime_id"] == "sim_input"
    assert out[1]["runtime_backed"] is False


# ---------------------------------------------------------------------------
# InputPart runtime
# ---------------------------------------------------------------------------

def test_input_part_read_keys():
    p = InputPart("sim_input", "INPUT", base=0x0110)
    p.set_keys(0x10)
    assert p.read(0x0110) == 0x10        # KEY_STATE
    assert p.get_keys() == 0x10


def test_input_part_masks_to_8bit():
    p = InputPart("sim_input", "INPUT", base=0x0110)
    p.set_keys(0x1FF)
    assert p.read(0x0110) == 0xFF


def test_input_part_edge():
    p = InputPart("sim_input", "INPUT", base=0x0110)
    p.set_keys(0x01)
    p.set_keys(0x03)                     # bit1 newly pressed; bit0 still held
    assert p.read(0x0114) == 0x03        # EDGE_STATE accumulates rising edges
    p.write(0x0114, 0)                   # CLEAR_EDGE
    assert p.read(0x0114) == 0x00
    p.set_keys(0x04)
    assert p.read(0x0114) == 0x04
    p.clear_edge()
    assert p.read(0x0114) == 0x00


def test_input_part_reset_and_unknown_offsets():
    p = InputPart("sim_input", "INPUT", base=0x0110)
    p.set_keys(0x0F)
    p.reset()
    assert p.read(0x0110) == 0 and p.read(0x0114) == 0
    assert p.read(0x0118) == 0           # unknown offset -> 0
    p.write(0x0110, 0x55)                # KEY_STATE is read-only -> no-op
    assert p.read(0x0110) == 0


# ---------------------------------------------------------------------------
# resolve_circuit — Input collected as addressable device
# ---------------------------------------------------------------------------

def test_resolve_collects_input():
    nodes = _nodes(("n1", "cpu", "cpu.ak32"), ("n2", "mem", "mem.ram"),
                   ("n3", "io", "io.uart"), ("n4", "io", "io.input"))
    conns = [{"from_node": "n1", "to_node": n} for n in ("n2", "n3", "n4")]
    plan = resolve_circuit(nodes, conns)
    assert plan["ok"] is True
    assert plan["inputs"] == ["n4"]
    assert plan["uarts"] == ["n3"]
    kinds = {d["node_id"]: d["kind"] for d in plan["devices"]}
    assert kinds == {"n2": "ram", "n3": "uart", "n4": "input"}


def test_resolve_no_input_is_unchanged():
    nodes = _nodes(("n1", "cpu", "cpu.ak32"), ("n2", "mem", "mem.ram"),
                   ("n3", "io", "io.uart"))
    conns = [{"from_node": "n1", "to_node": n} for n in ("n2", "n3")]
    plan = resolve_circuit(nodes, conns)
    assert plan["inputs"] == []
    assert plan["ok"] is True            # Input is not required


def test_unconnected_input_not_collected():
    nodes = _nodes(("n1", "cpu", "cpu.ak32"), ("n2", "mem", "mem.ram"),
                   ("n3", "io", "io.uart"), ("n4", "io", "io.input"))
    conns = [{"from_node": "n1", "to_node": n} for n in ("n2", "n3")]  # n4 dangling
    plan = resolve_circuit(nodes, conns)
    assert plan["inputs"] == []
    assert plan["ok"] is True


# ---------------------------------------------------------------------------
# MainWin integration
# ---------------------------------------------------------------------------

def _win(tmp_path):
    root = tmp_path / "proj"
    create_project(str(root), "proj")
    win = MainWin()
    win._project_root = root
    win._editor_tabs.set_project_root(root)
    return win, root


def _wire_with_input(win):
    win._canvas.add_part_at(_CPU,   QPointF(0.0, 0.0))     # node_0001
    win._canvas.add_part_at(_RAM,   QPointF(200.0, 0.0))   # node_0002
    win._canvas.add_part_at(_UART,  QPointF(400.0, 0.0))   # node_0003
    win._canvas.add_part_at(_INPUT, QPointF(600.0, 0.0))   # node_0004
    win._canvas.add_connection("node_0001", "bus", "node_0002", "bus")
    win._canvas.add_connection("node_0001", "bus", "node_0003", "bus")
    win._canvas.add_connection("node_0001", "bus", "node_0004", "bus")


def _assign(win, root, text, name):
    dst = root / "tests" / "test"
    dst.mkdir(parents=True, exist_ok=True)
    (dst / name).write_text(text, encoding="utf-8")
    win._canvas.set_node_source("node_0001", "asm", f"tests/test/{name}")


def test_input_runtime_built_and_address_map(tmp_path):
    win, root = _win(tmp_path)
    _wire_with_input(win)
    _assign(win, root, _INPUT_READ_ASM, "input_read.asm")
    assert win.write_program() is True
    assert win._sim_input is not None
    assert win._sim_input_node == "node_0004"
    assert win._sim_input.id == "sim_input"
    amap = win._runtime.address_map
    uart = next(d for d in amap["devices"] if d["kind"] == "uart")
    inp = next(d for d in amap["devices"] if d["kind"] == "input")
    assert uart["base"] == 0x0100
    assert inp["base"] == 0x0110 and inp["end"] == 0x0117
    assert validate_address_map(amap) == []


def test_cpu_reads_input_via_ld(tmp_path):
    win, root = _win(tmp_path)
    _wire_with_input(win)
    _assign(win, root, _INPUT_READ_ASM, "input_read.asm")
    win.write_program()
    win.set_input_keys(0x10)            # press "A" (bit4)
    win._do_run()
    assert win._sim_cpu.regs()[2] == 0x10   # LD [0x0110] -> r2


def test_set_input_keys_no_input_is_noop(tmp_path):
    win, root = _win(tmp_path)
    win._canvas.add_part_at(_CPU,  QPointF(0.0, 0.0))
    win._canvas.add_part_at(_RAM,  QPointF(200.0, 0.0))
    win._canvas.add_part_at(_UART, QPointF(400.0, 0.0))
    win._canvas.add_connection("node_0001", "bus", "node_0002", "bus")
    win._canvas.add_connection("node_0001", "bus", "node_0003", "bus")
    _assign(win, root, _HELLO_WORLD.read_text(encoding="utf-8"), "hello_world.asm")
    win.write_program()
    assert win._sim_input is None
    win.set_input_keys(0x10)            # no-op, must not crash
    win._do_run()
    assert "Hello World !" in win._sim_uart.output_text()


def test_input_in_address_map_editor(tmp_path):
    win, root = _win(tmp_path)
    _wire_with_input(win)
    win._address_map_editor.refresh()
    nodes = {win._address_map_editor._table.item(r, COL_NODE).text()
             for r in range(win._address_map_editor._table.rowCount())}
    assert "node_0004" in nodes          # Input shown in the editor


def test_input_base_override(tmp_path):
    win, root = _win(tmp_path)
    _wire_with_input(win)
    win.apply_address_map_overrides(
        {"node_0004": {"mode": "manual", "base": 0x0120, "size": 0x08}})
    inp = next(d for d in win._runtime.address_map["devices"] if d["kind"] == "input")
    assert inp["base"] == 0x0120 and inp["end"] == 0x0127


# ---------------------------------------------------------------------------
# existing compatibility (no Input device)
# ---------------------------------------------------------------------------

def test_no_input_address_map_unchanged(tmp_path):
    win, root = _win(tmp_path)
    win._canvas.add_part_at(_CPU,  QPointF(0.0, 0.0))
    win._canvas.add_part_at(_RAM,  QPointF(200.0, 0.0))
    win._canvas.add_part_at(_UART, QPointF(400.0, 0.0))
    win._canvas.add_connection("node_0001", "bus", "node_0002", "bus")
    win._canvas.add_connection("node_0001", "bus", "node_0003", "bus")
    _assign(win, root, _HELLO_WORLD.read_text(encoding="utf-8"), "hello_world.asm")
    win.write_program()
    amap = win._runtime.address_map
    ram = next(d for d in amap["devices"] if d["kind"] == "ram")
    assert ram["attach_ranges"] == [(0x0000, 0x00FF), (0x0108, 0xFFFF)]
    assert not any(d["kind"] == "input" for d in amap["devices"])
    win._do_run()
    assert "Hello World !" in win._sim_uart.output_text()


def test_selftest_unchanged(tmp_path):
    win, root = _win(tmp_path)
    win._canvas.add_part_at(_CPU,  QPointF(0.0, 0.0))
    win._canvas.add_part_at(_RAM,  QPointF(200.0, 0.0))
    win._canvas.add_part_at(_UART, QPointF(400.0, 0.0))
    win._canvas.add_connection("node_0001", "bus", "node_0002", "bus")
    win._canvas.add_connection("node_0001", "bus", "node_0003", "bus")
    _assign(win, root, _RAM_SELFTEST.read_text(encoding="utf-8"), "ram_selftest.asm")
    win.write_program()
    win._do_run()
    assert "PASS" in win._sim_uart.output_text()


def test_legacy_mode_unchanged():
    win = MainWin()
    assert win._runtime.address_map["mode"] == "legacy"
    assert win._sim_input is None
