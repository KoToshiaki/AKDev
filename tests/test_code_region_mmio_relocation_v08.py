# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""PATCH_CODE_REGION_MMIO_RELOCATION_V08 — MemoryLayout (default = current behaviour)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF

_app = QApplication.instance() or QApplication(sys.argv)

from core.devices import (
    MemoryLayout, get_memory_layout, LEGACY, CIRCUIT_COMPAT, GAME16,
    make_device_spec, synthetic_spec, assign_mmio_bases,
    RAM_BASE, UART_BASE, UART_SIZE, CIRCUIT_RAM_SIZE, LEGACY_RAM_SIZE,
)
from core.circuit import build_address_map, build_address_map_from_devices, validate_address_map
from ui.win import MainWin, _CIRCUIT_RAM_SIZE, _SIM_RAM_SIZE
from core.project import create_project

_CPU  = {"id": "cpu.ak32", "name": "AK32", "category": "cpu"}
_RAM  = {"id": "mem.ram",  "name": "RAM",  "category": "mem"}
_UART = {"id": "io.uart",  "name": "UART", "category": "io"}
_HELLO_WORLD  = Path(__file__).parent / "test" / "hello_world.asm"
_RAM_SELFTEST = Path(__file__).parent / "test" / "ram_selftest.asm"


# ---------------------------------------------------------------------------
# MemoryLayout values
# ---------------------------------------------------------------------------

def test_circuit_compat_layout_values():
    L = CIRCUIT_COMPAT
    assert L.name == "circuit_compat"
    assert (L.ram_base, L.ram_size) == (0x0000, 0x10000)
    assert (L.mmio_base, L.mmio_stride, L.mmio_size) == (0x0100, 0x10, 0x08)
    assert L.mmio_inside_ram is True
    assert (L.code_base, L.reset_pc) == (0x0000, 0x0000)


def test_legacy_layout_values():
    L = LEGACY
    assert L.name == "legacy"
    assert L.ram_size == 0x0100
    assert L.mmio_base == 0x0100
    assert L.mmio_inside_ram is False
    assert L.reset_pc == 0x0000


def test_game16_layout_defined_not_default():
    assert GAME16.name == "game16"
    assert GAME16.ram_base == 0x8000 and GAME16.ram_size == 0x4000
    assert GAME16.mmio_base == 0xE000
    assert GAME16.mmio_inside_ram is False
    assert GAME16.stack_top == 0xBFFF
    # default is NOT game16
    assert get_memory_layout() is CIRCUIT_COMPAT


def test_get_memory_layout():
    assert get_memory_layout() is CIRCUIT_COMPAT
    assert get_memory_layout(None) is CIRCUIT_COMPAT
    assert get_memory_layout("circuit") is CIRCUIT_COMPAT
    assert get_memory_layout("circuit_compat") is CIRCUIT_COMPAT
    assert get_memory_layout("legacy") is LEGACY
    assert get_memory_layout("game16") is GAME16
    # unknown -> safe fallback to circuit_compat
    assert get_memory_layout("nonsense") is CIRCUIT_COMPAT


def test_constants_match_layouts():
    assert RAM_BASE == CIRCUIT_COMPAT.ram_base
    assert UART_BASE == CIRCUIT_COMPAT.mmio_base
    assert UART_SIZE == CIRCUIT_COMPAT.mmio_size
    assert CIRCUIT_RAM_SIZE == CIRCUIT_COMPAT.ram_size == 0x10000
    assert LEGACY_RAM_SIZE == LEGACY.ram_size == 0x0100


# ---------------------------------------------------------------------------
# default-layout compatibility
# ---------------------------------------------------------------------------

def test_make_device_spec_default_compat():
    ram = make_device_spec("n2", _RAM, mode="circuit")
    uart = make_device_spec("n3", _UART, mode="circuit")
    assert (ram["base"], ram["size"], ram["end"]) == (0x0000, 0x10000, 0xFFFF)
    assert (uart["base"], uart["size"], uart["end"]) == (0x0100, 0x08, 0x0107)
    ram_legacy = make_device_spec(None, _RAM, mode="legacy")
    assert (ram_legacy["base"], ram_legacy["size"]) == (0x0000, 0x0100)


def test_assign_mmio_default_compat():
    specs = assign_mmio_bases([
        make_device_spec("n3", _UART, mode="circuit"),
        make_device_spec("n4", _UART, mode="circuit"),
    ])
    assert (specs[0]["base"], specs[0]["end"]) == (0x0100, 0x0107)
    assert (specs[1]["base"], specs[1]["end"]) == (0x0110, 0x0117)


def test_build_address_map_from_devices_default_compat():
    a = build_address_map(mode="circuit", ram_node="n2", ram_base=0x0000,
                          ram_size=0x10000, uart_node="n3", uart_base=0x0100,
                          uart_size=0x0008)
    specs = assign_mmio_bases([
        {"kind": "ram", "node_id": "n2", "runtime_id": "sim_ram", "role": "memory",
         "base": 0x0000, "size": 0x10000, "label": "RAM", "addressable": True},
        {"kind": "uart", "node_id": "n3", "runtime_id": "sim_uart", "role": "mmio",
         "base": 0x0100, "size": 0x0008, "label": "UART", "addressable": True},
    ])
    b = build_address_map_from_devices("circuit", specs)
    assert a == b


def test_build_address_map_wrapper_legacy_unchanged():
    amap = build_address_map(mode="legacy", ram_node=None, ram_base=0x0000,
                             ram_size=0x0100, uart_node=None, uart_base=0x0100,
                             uart_size=0x0008)
    ram = next(d for d in amap["devices"] if d["kind"] == "ram")
    uart = next(d for d in amap["devices"] if d["kind"] == "uart")
    assert ram["attach_ranges"] == [(0x0000, 0x00FF)]
    assert ram["reserved"] == []
    assert uart["role"] == "io" and uart["overlay"] is None
    assert validate_address_map(amap) == []


# ---------------------------------------------------------------------------
# layout-aware behaviour
# ---------------------------------------------------------------------------

def test_assign_mmio_layout_aware():
    # game16: MMIO at 0xE000, 16-byte stride
    specs = assign_mmio_bases([
        make_device_spec("n3", _UART, layout=GAME16),
        make_device_spec("n4", _UART, layout=GAME16),
    ], layout=GAME16)
    assert specs[0]["base"] == 0xE000
    assert specs[1]["base"] == 0xE010


def test_mmio_inside_ram_true_carves():
    specs = [
        {"kind": "ram", "node_id": "r", "runtime_id": "sim_ram", "role": "memory",
         "base": 0x0000, "size": 0x10000, "label": "RAM", "addressable": True},
        {"kind": "uart", "node_id": "u", "runtime_id": "sim_uart", "role": "mmio",
         "base": 0x0100, "size": 0x0008, "label": "UART", "addressable": True},
    ]
    amap = build_address_map_from_devices("circuit", specs, layout=CIRCUIT_COMPAT)
    ram = next(d for d in amap["devices"] if d["kind"] == "ram")
    assert ram["attach_ranges"] == [(0x0000, 0x00FF), (0x0108, 0xFFFF)]
    assert ram["reserved"] == [(0x0100, 0x0107)]


def test_mmio_inside_ram_false_non_overlap():
    # A layout with mmio_inside_ram=False: RAM is NOT carved even if a window sits
    # geometrically within it (non-overlapping regions model — future game16-style).
    layout = MemoryLayout(name="t", ram_base=0x0000, ram_size=0x10000,
                          mmio_base=0x0100, mmio_stride=0x10, mmio_size=0x08,
                          mmio_inside_ram=False, code_base=0x0000, reset_pc=0x0000)
    specs = [
        {"kind": "ram", "node_id": "r", "runtime_id": "sim_ram", "role": "memory",
         "base": 0x0000, "size": 0x10000, "label": "RAM", "addressable": True},
        {"kind": "uart", "node_id": "u", "runtime_id": "sim_uart", "role": "mmio",
         "base": 0x0100, "size": 0x0008, "label": "UART", "addressable": True},
    ]
    amap = build_address_map_from_devices("x", specs, layout=layout)
    ram = next(d for d in amap["devices"] if d["kind"] == "ram")
    uart = next(d for d in amap["devices"] if d["kind"] == "uart")
    assert ram["attach_ranges"] == [(0x0000, 0xFFFF)]   # not carved
    assert ram["reserved"] == []
    assert uart["role"] == "io" and uart["overlay"] is None


# ---------------------------------------------------------------------------
# MainWin / runtime compatibility (default layout)
# ---------------------------------------------------------------------------

def _win(tmp_path):
    root = tmp_path / "proj"
    create_project(str(root), "proj")
    win = MainWin()
    win._project_root = root
    win._editor_tabs.set_project_root(root)
    return win, root


def _wire(win):
    win._canvas.add_part_at(_CPU,  QPointF(0.0, 0.0))     # node_0001
    win._canvas.add_part_at(_RAM,  QPointF(200.0, 0.0))   # node_0002
    win._canvas.add_part_at(_UART, QPointF(400.0, 0.0))   # node_0003
    win._canvas.add_connection("node_0001", "bus", "node_0002", "bus")
    win._canvas.add_connection("node_0001", "bus", "node_0003", "bus")


def _assign(win, root, src, name):
    dst = root / "tests" / "test"
    dst.mkdir(parents=True, exist_ok=True)
    (dst / name).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    win._canvas.set_node_source("node_0001", "asm", f"tests/test/{name}")


def test_mainwin_circuit_default_unchanged(tmp_path):
    win, root = _win(tmp_path)
    _wire(win)
    _assign(win, root, _HELLO_WORLD, "hello_world.asm")
    win.write_program()
    assert win._sim_ram.size == _CIRCUIT_RAM_SIZE
    assert win._sim_ram_node == "node_0002"
    assert win._sim_uart_node == "node_0003"
    assert win._sim_cpu_node == "node_0001"
    assert win._sim_ram.id == "sim_ram"
    assert win._sim_cpu.pc() == 0x0000            # reset_pc from layout (default 0)
    amap = win._runtime.address_map
    ram = next(d for d in amap["devices"] if d["kind"] == "ram")
    assert ram["attach_ranges"] == [(0x0000, 0x00FF), (0x0108, 0xFFFF)]
    win._do_run()
    assert "Hello World !" in win._sim_uart.output_text()


def test_mainwin_selftest_unchanged(tmp_path):
    win, root = _win(tmp_path)
    _wire(win)
    _assign(win, root, _RAM_SELFTEST, "ram_selftest.asm")
    win.write_program()
    win._do_run()
    assert "PASS" in win._sim_uart.output_text()


def test_mainwin_legacy_unchanged():
    win = MainWin()
    assert win._runtime.address_map["mode"] == "legacy"
    assert win._sim_ram.size == _SIM_RAM_SIZE
    assert win._sim_ram_node is None
    assert win._sim_cpu.pc() == 0x0000
