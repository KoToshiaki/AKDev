# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""PATCH_MULTI_RAM_UART_ADDRESS_MAP_V08 — multiple UART/MMIO placement + device_kind resolve."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF

_app = QApplication.instance() or QApplication(sys.argv)

from core.circuit import (
    resolve_circuit, build_address_map, build_address_map_from_devices,
    validate_address_map, format_address_map_summary,
)
from core.devices import (
    make_device_spec, assign_mmio_bases, multi_device_warnings, MULTI_RAM_UNSUPPORTED,
)
from ui.win import MainWin, _CIRCUIT_RAM_SIZE, _SIM_RAM_SIZE
from core.project import create_project

_CPU  = {"id": "cpu.ak32", "name": "AK32", "category": "cpu"}
_RAM  = {"id": "mem.ram",  "name": "RAM",  "category": "mem"}
_UART = {"id": "io.uart",  "name": "UART", "category": "io"}
_VRAM = {"id": "mem.vram", "name": "VRAM", "category": "mem"}
_HELLO_WORLD = Path(__file__).parent / "test" / "hello_world.asm"
_RAM_SELFTEST = Path(__file__).parent / "test" / "ram_selftest.asm"


def _nodes(*specs):
    return [{"node_id": nid, "category": cat, "part_id": pid, "name": pid}
            for (nid, cat, pid) in specs]


# ---------------------------------------------------------------------------
# resolve_circuit: device_kind based classification (VRAM not RAM)
# ---------------------------------------------------------------------------

def test_resolve_vram_not_in_rams():
    nodes = _nodes(("n1", "cpu", "cpu.ak32"),
                   ("n2", "mem", "mem.vram"),     # VRAM, not RAM
                   ("n3", "io",  "io.uart"))
    conns = [{"from_node": "n1", "to_node": "n2"},
             {"from_node": "n1", "to_node": "n3"}]
    plan = resolve_circuit(nodes, conns)
    assert plan["rams"] == []                     # vram excluded
    assert "n2" not in plan["rams"]


def test_resolve_ram_in_rams():
    nodes = _nodes(("n1", "cpu", "cpu.ak32"),
                   ("n2", "mem", "mem.ram"),
                   ("n3", "io",  "io.uart"))
    conns = [{"from_node": "n1", "to_node": "n2"},
             {"from_node": "n1", "to_node": "n3"}]
    plan = resolve_circuit(nodes, conns)
    assert plan["rams"] == ["n2"]
    assert plan["uarts"] == ["n3"]
    assert plan["ok"] is True


def test_resolve_multiple_rams_and_uarts_listed():
    nodes = _nodes(("n1", "cpu", "cpu.ak32"),
                   ("n2", "mem", "mem.ram"), ("n3", "mem", "mem.ram"),
                   ("n4", "io", "io.uart"), ("n5", "io", "io.uart"))
    conns = [{"from_node": "n1", "to_node": n} for n in ("n2", "n3", "n4", "n5")]
    plan = resolve_circuit(nodes, conns)
    assert plan["rams"] == ["n2", "n3"]
    assert plan["uarts"] == ["n4", "n5"]


# ---------------------------------------------------------------------------
# assign_mmio_bases
# ---------------------------------------------------------------------------

def test_assign_mmio_single_uart_unchanged():
    specs = [make_device_spec("n3", _UART, mode="circuit")]
    out = assign_mmio_bases(specs)
    assert out[0]["base"] == 0x0100 and out[0]["end"] == 0x0107
    assert out[0]["runtime_backed"] is True
    assert out[0]["runtime_id"] == "sim_uart"


def test_assign_mmio_multiple_uarts():
    specs = [make_device_spec("n3", _UART, mode="circuit"),
             make_device_spec("n4", _UART, mode="circuit"),
             make_device_spec("n5", _UART, mode="circuit")]
    out = assign_mmio_bases(specs)
    assert (out[0]["base"], out[0]["end"]) == (0x0100, 0x0107)
    assert (out[1]["base"], out[1]["end"]) == (0x0110, 0x0117)
    assert (out[2]["base"], out[2]["end"]) == (0x0120, 0x0127)
    # only the first UART stays runtime-backed
    assert out[0]["runtime_backed"] is True
    assert out[1]["runtime_backed"] is False
    assert out[2]["runtime_backed"] is False


def test_assign_mmio_leaves_ram_cpu():
    specs = [make_device_spec("n1", _CPU, mode="circuit"),
             make_device_spec("n2", _RAM, mode="circuit"),
             make_device_spec("n3", _UART, mode="circuit")]
    out = assign_mmio_bases(specs)
    ram = next(s for s in out if s["kind"] == "ram")
    assert ram["base"] == 0x0000 and ram["size"] == _CIRCUIT_RAM_SIZE


# ---------------------------------------------------------------------------
# multi_device_warnings
# ---------------------------------------------------------------------------

def test_multi_ram_warning():
    specs = [make_device_spec("n2", _RAM, mode="circuit"),
             make_device_spec("n3", _RAM, mode="circuit")]
    issues = multi_device_warnings(specs)
    assert len(issues) == 1
    assert issues[0]["code"] == MULTI_RAM_UNSUPPORTED
    assert issues[0]["details"]["unsupported"] == ["n3"]


def test_single_ram_no_warning():
    specs = [make_device_spec("n2", _RAM, mode="circuit")]
    assert multi_device_warnings(specs) == []


# ---------------------------------------------------------------------------
# Address Map: multiple MMIO windows carve RAM correctly
# ---------------------------------------------------------------------------

def test_two_uart_windows_carve_ram():
    specs = assign_mmio_bases([
        make_device_spec("n2", _RAM, mode="circuit"),
        make_device_spec("n3", _UART, mode="circuit"),
        make_device_spec("n4", _UART, mode="circuit"),
    ])
    amap = build_address_map_from_devices("circuit", specs)
    ram = next(d for d in amap["devices"] if d["kind"] == "ram")
    assert ram["attach_ranges"] == [(0x0000, 0x00FF), (0x0108, 0x010F), (0x0118, 0xFFFF)]
    assert ram["reserved"] == [(0x0100, 0x0107), (0x0110, 0x0117)]
    assert validate_address_map(amap) == []
    uarts = [d for d in amap["devices"] if d["kind"] == "uart"]
    assert {u["base"] for u in uarts} == {0x0100, 0x0110}


def test_single_uart_address_map_unchanged():
    # The single RAM+UART address map must be identical to the legacy wrapper.
    specs = assign_mmio_bases([
        {"kind": "ram", "node_id": "n2", "runtime_id": "sim_ram", "role": "memory",
         "base": 0x0000, "size": 0x10000, "label": "RAM", "addressable": True},
        {"kind": "uart", "node_id": "n3", "runtime_id": "sim_uart", "role": "mmio",
         "base": 0x0100, "size": 0x0008, "label": "UART", "addressable": True},
    ])
    a = build_address_map_from_devices("circuit", specs)
    b = build_address_map(mode="circuit", ram_node="n2", ram_base=0x0000,
                          ram_size=0x10000, uart_node="n3", uart_base=0x0100,
                          uart_size=0x0008)
    assert a == b


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


def _assign(win, root, src, name):
    dst = root / "tests" / "test"
    dst.mkdir(parents=True, exist_ok=True)
    (dst / name).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    win._canvas.set_node_source("node_0001", "asm", f"tests/test/{name}")


def _wire_single(win):
    win._canvas.add_part_at(_CPU,  QPointF(0.0, 0.0))     # node_0001
    win._canvas.add_part_at(_RAM,  QPointF(200.0, 0.0))   # node_0002
    win._canvas.add_part_at(_UART, QPointF(400.0, 0.0))   # node_0003
    win._canvas.add_connection("node_0001", "bus", "node_0002", "bus")
    win._canvas.add_connection("node_0001", "bus", "node_0003", "bus")


def test_single_circuit_unchanged_and_runs(tmp_path):
    win, root = _win(tmp_path)
    _wire_single(win)
    _assign(win, root, _HELLO_WORLD, "hello_world.asm")
    win.write_program()
    assert win._sim_ram_node == "node_0002"
    assert win._sim_uart_node == "node_0003"
    assert win._sim_cpu_node == "node_0001"
    assert win._sim_ram.size == _CIRCUIT_RAM_SIZE
    amap = win._runtime.address_map
    ram = next(d for d in amap["devices"] if d["kind"] == "ram")
    uart = next(d for d in amap["devices"] if d["kind"] == "uart")
    assert ram["attach_ranges"] == [(0x0000, 0x00FF), (0x0108, 0xFFFF)]
    assert (uart["base"], uart["end"]) == (0x0100, 0x0107)
    win._do_run()
    assert "Hello World !" in win._sim_uart.output_text()


def test_selftest_still_passes(tmp_path):
    win, root = _win(tmp_path)
    _wire_single(win)
    _assign(win, root, _RAM_SELFTEST, "ram_selftest.asm")
    win.write_program()
    win._do_run()
    assert "PASS" in win._sim_uart.output_text()


def test_two_uarts_address_map_and_runtime(tmp_path):
    win, root = _win(tmp_path)
    win._canvas.add_part_at(_CPU,  QPointF(0.0, 0.0))     # node_0001
    win._canvas.add_part_at(_RAM,  QPointF(200.0, 0.0))   # node_0002
    win._canvas.add_part_at(_UART, QPointF(400.0, 0.0))   # node_0003 (UART1)
    win._canvas.add_part_at(_UART, QPointF(400.0, 200.0)) # node_0004 (UART2)
    win._canvas.add_connection("node_0001", "bus", "node_0002", "bus")
    win._canvas.add_connection("node_0001", "bus", "node_0003", "bus")
    win._canvas.add_connection("node_0001", "bus", "node_0004", "bus")
    _assign(win, root, _HELLO_WORLD, "hello_world.asm")
    win.write_program()
    amap = win._runtime.address_map
    uarts = sorted(d["base"] for d in amap["devices"] if d["kind"] == "uart")
    assert uarts == [0x0100, 0x0110]
    ram = next(d for d in amap["devices"] if d["kind"] == "ram")
    assert ram["attach_ranges"] == [(0x0000, 0x00FF), (0x0108, 0x010F), (0x0118, 0xFFFF)]
    assert validate_address_map(amap) == []
    # runtime still wraps only the first UART (case A)
    assert win._sim_uart_node == "node_0003"
    win._do_run()
    assert "Hello World !" in win._sim_uart.output_text()


def test_multiple_ram_warning_logged(tmp_path):
    win, root = _win(tmp_path)
    win._canvas.add_part_at(_CPU,  QPointF(0.0, 0.0))     # node_0001
    win._canvas.add_part_at(_RAM,  QPointF(200.0, 0.0))   # node_0002 (RAM1)
    win._canvas.add_part_at(_RAM,  QPointF(200.0, 200.0)) # node_0003 (RAM2)
    win._canvas.add_part_at(_UART, QPointF(400.0, 0.0))   # node_0004
    win._canvas.add_connection("node_0001", "bus", "node_0002", "bus")
    win._canvas.add_connection("node_0001", "bus", "node_0003", "bus")
    win._canvas.add_connection("node_0001", "bus", "node_0004", "bus")
    _assign(win, root, _HELLO_WORLD, "hello_world.asm")
    win.write_program()
    log = win._log.toPlainText()
    assert "MULTI_RAM_UNSUPPORTED" in log
    # only the first RAM is runtime-backed and address-mapped
    assert win._sim_ram_node == "node_0002"
    rams = [d for d in win._runtime.address_map["devices"] if d["kind"] == "ram"]
    assert len(rams) == 1
    # the first RAM still works
    win._do_run()
    assert "Hello World !" in win._sim_uart.output_text()


def test_vram_circuit_blocks_no_ram(tmp_path):
    # A CPU wired only to a VRAM (+UART): VRAM is not RAM -> circuit blocked (no RAM).
    win, root = _win(tmp_path)
    win._canvas.add_part_at(_CPU,  QPointF(0.0, 0.0))     # node_0001
    win._canvas.add_part_at(_VRAM, QPointF(200.0, 0.0))   # node_0002 (VRAM)
    win._canvas.add_part_at(_UART, QPointF(400.0, 0.0))   # node_0003
    win._canvas.add_connection("node_0001", "bus", "node_0002", "bus")
    win._canvas.add_connection("node_0001", "bus", "node_0003", "bus")
    _assign(win, root, _HELLO_WORLD, "hello_world.asm")
    assert win.write_program() is False           # no RAM -> blocked
    assert "blocked" in win._log.toPlainText()


def test_legacy_mode_unchanged():
    win = MainWin()
    assert win._runtime.address_map["mode"] == "legacy"
    assert win._sim_ram.size == _SIM_RAM_SIZE
    assert win._sim_ram_node is None
