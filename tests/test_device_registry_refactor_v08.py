# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""PATCH_DEVICE_REGISTRY_REFACTOR_V08 — device spec / list-driven runtime + Address Map."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF

_app = QApplication.instance() or QApplication(sys.argv)

from core.devices import (
    device_kind, device_role, is_addressable_kind, is_runtime_backed_kind,
    make_device_spec, build_device_specs, legacy_device_specs,
    RAM_BASE, CIRCUIT_RAM_SIZE, LEGACY_RAM_SIZE, UART_BASE, UART_SIZE,
)
from core.circuit import (
    build_address_map, build_address_map_from_devices,
    validate_address_map, format_address_map_summary,
)
from core.dev import RamPart
from ui.win import MainWin, _CIRCUIT_RAM_SIZE, _SIM_RAM_SIZE
from core.project import create_project

_CPU  = {"id": "cpu.ak32", "name": "AK32", "category": "cpu"}
_RAM  = {"id": "mem.ram",  "name": "RAM",  "category": "mem"}
_UART = {"id": "io.uart",  "name": "UART", "category": "io"}
_VRAM = {"id": "mem.vram", "name": "VRAM", "category": "mem"}
_HELLO_WORLD = Path(__file__).parent / "test" / "hello_world.asm"
_RAM_SELFTEST = Path(__file__).parent / "test" / "ram_selftest.asm"
_REL = "tests/test/hello_world.asm"


# ---------------------------------------------------------------------------
# device_kind classification
# ---------------------------------------------------------------------------

def test_device_kind_by_part_id():
    assert device_kind({"id": "cpu.ak32"}) == "cpu"
    assert device_kind({"id": "mem.ram"}) == "ram"
    assert device_kind({"id": "mem.vram"}) == "vram"
    assert device_kind({"id": "io.uart"}) == "uart"
    assert device_kind({"id": "io.gpio"}) == "gpio"
    assert device_kind({"id": "io.timer"}) == "timer"
    assert device_kind({"id": "video.regs"}) == "video_regs"
    assert device_kind({"id": "video.out"}) == "video_out"
    assert device_kind({"id": "bus.bridge"}) == "bridge"
    assert device_kind({"id": "fpga.generic"}) == "fpga"
    assert device_kind({"id": "fpga.ecp5_85f"}) == "fpga"


def test_device_kind_unknown_and_none():
    assert device_kind({"id": "weird.thing"}) == "unsupported"
    assert device_kind({}) == "unsupported"
    assert device_kind(None) == "unsupported"


def test_device_kind_vram_not_ram():
    # category is "mem" but part_id mem.vram must NOT become ram
    assert device_kind({"id": "mem.vram", "category": "mem"}) == "vram"
    assert device_kind({"id": "mem.vram", "category": "mem"}) != "ram"


# ---------------------------------------------------------------------------
# device spec
# ---------------------------------------------------------------------------

def test_ram_spec():
    s = make_device_spec("n2", _RAM, mode="circuit")
    assert s["kind"] == "ram"
    assert s["role"] == "memory"
    assert s["addressable"] is True
    assert s["runtime_backed"] is True
    assert s["runtime_id"] == "sim_ram"
    assert s["base"] == RAM_BASE and s["size"] == CIRCUIT_RAM_SIZE
    assert s["end"] == 0xFFFF


def test_uart_spec():
    s = make_device_spec("n3", _UART, mode="circuit")
    assert s["kind"] == "uart"
    assert s["addressable"] is True
    assert s["runtime_backed"] is True
    assert s["runtime_id"] == "sim_uart"
    assert (s["base"], s["size"], s["end"]) == (UART_BASE, UART_SIZE, 0x0107)


def test_cpu_spec_not_addressable():
    s = make_device_spec("n1", _CPU, mode="circuit")
    assert s["kind"] == "cpu"
    assert s["addressable"] is False
    assert s["runtime_backed"] is True
    assert s["runtime_id"] == "sim_cpu"


def test_vram_spec_addressable_and_runtime_backed():
    # PATCH_VRAM_DEVICE_V08: VRAM is now a runtime-backed writable framebuffer
    # (VramPart / sim_vram), no longer a placeholder kind.
    s = make_device_spec("n4", _VRAM, mode="circuit")
    assert s["kind"] == "vram"
    assert s["role"] == "memory"
    assert s["addressable"] is True
    assert s["runtime_backed"] is True
    assert s["runtime_id"] == "sim_vram"


def test_unsupported_spec_no_crash():
    s = make_device_spec("nX", {"id": "mystery.x", "category": "other"})
    assert s["kind"] == "unsupported"
    assert s["addressable"] is False
    assert s["runtime_backed"] is False


def test_ram_spec_legacy_size():
    s = make_device_spec(None, _RAM, mode="legacy")
    assert s["size"] == LEGACY_RAM_SIZE and s["end"] == 0x00FF


def test_helpers():
    assert device_role("ram") == "memory"
    assert device_role("uart") == "mmio"
    assert device_role("cpu") == "cpu"
    assert is_addressable_kind("ram") and is_addressable_kind("uart")
    assert not is_addressable_kind("cpu")
    assert is_runtime_backed_kind("ram") and is_runtime_backed_kind("vram")


def test_build_device_specs_and_legacy():
    specs = build_device_specs([{"node_id": "n1", "part": _CPU},
                                {"node_id": "n2", "part": _RAM}])
    assert [s["kind"] for s in specs] == ["cpu", "ram"]
    legacy = legacy_device_specs()
    assert [s["kind"] for s in legacy] == ["cpu", "ram", "uart"]
    assert all(s["node_id"] is None for s in legacy)


# ---------------------------------------------------------------------------
# Address Map: from-devices matches the legacy wrapper
# ---------------------------------------------------------------------------

def _ram_uart_specs(mode, ram_size):
    return [
        {"kind": "ram", "node_id": "n2", "runtime_id": "sim_ram",
         "base": 0x0000, "size": ram_size, "label": "RAM", "addressable": True},
        {"kind": "uart", "node_id": "n3", "runtime_id": "sim_uart",
         "base": 0x0100, "size": 0x0008, "label": "UART", "addressable": True},
    ]


def test_from_devices_matches_wrapper_circuit():
    a = build_address_map(mode="circuit", ram_node="n2", ram_base=0x0000,
                          ram_size=0x10000, uart_node="n3", uart_base=0x0100,
                          uart_size=0x0008)
    b = build_address_map_from_devices("circuit", _ram_uart_specs("circuit", 0x10000))
    assert a == b


def test_from_devices_matches_wrapper_legacy():
    a = build_address_map(mode="legacy", ram_node=None, ram_base=0x0000,
                          ram_size=0x0100, uart_node=None, uart_base=0x0100,
                          uart_size=0x0008)
    b = build_address_map_from_devices(
        "legacy",
        [{"kind": "ram", "node_id": None, "runtime_id": "sim_ram",
          "base": 0x0000, "size": 0x0100, "label": "RAM", "addressable": True},
         {"kind": "uart", "node_id": None, "runtime_id": "sim_uart",
          "base": 0x0100, "size": 0x0008, "label": "UART", "addressable": True}],
    )
    assert a == b


def test_from_devices_uart_window_and_valid():
    amap = build_address_map_from_devices("circuit", _ram_uart_specs("circuit", 0x10000))
    ram = next(d for d in amap["devices"] if d["kind"] == "ram")
    uart = next(d for d in amap["devices"] if d["kind"] == "uart")
    assert ram["attach_ranges"] == [(0x0000, 0x00FF), (0x0108, 0xFFFF)]
    assert ram["reserved"] == [(0x0100, 0x0107)]
    assert uart["attach_ranges"] == [(0x0100, 0x0107)]
    assert uart["role"] == "mmio" and uart["overlay"] == "ram"
    assert validate_address_map(amap) == []
    text = "\n".join(format_address_map_summary(amap))
    assert "RAM" in text and "0x0000-0xffff" in text and "MMIO" in text


# ---------------------------------------------------------------------------
# MainWin integration — behaviour unchanged
# ---------------------------------------------------------------------------

def _win(tmp_path):
    root = tmp_path / "proj"
    create_project(str(root), "proj")
    win = MainWin()
    win._project_root = root
    win._editor_tabs.set_project_root(root)
    return win, root


def _wire_full(win):
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


def test_circuit_runtime_devices_built(tmp_path):
    win, root = _win(tmp_path)
    _wire_full(win)
    _assign(win, root, _HELLO_WORLD, "hello_world.asm")
    win.write_program()
    assert win._sim_ram is win._runtime.ram
    assert win._sim_uart is win._runtime.uart
    assert win._sim_cpu is win._runtime.cpu
    assert win._sim_ram.size == _CIRCUIT_RAM_SIZE
    assert win._sim_ram_node == "node_0002"
    assert win._sim_uart_node == "node_0003"
    assert win._sim_cpu_node == "node_0001"
    assert win._sim_ram.id == "sim_ram"
    assert win._sim_uart.id == "sim_uart"
    assert win._sim_cpu.id == "sim_cpu"


def test_circuit_address_map_unchanged(tmp_path):
    win, root = _win(tmp_path)
    _wire_full(win)
    _assign(win, root, _HELLO_WORLD, "hello_world.asm")
    win.write_program()
    amap = win._runtime.address_map
    assert amap["mode"] == "circuit"
    ram = next(d for d in amap["devices"] if d["kind"] == "ram")
    uart = next(d for d in amap["devices"] if d["kind"] == "uart")
    assert ram["attach_ranges"] == [(0x0000, 0x00FF), (0x0108, 0xFFFF)]
    assert uart["base"] == 0x0100 and uart["end"] == 0x0107
    assert validate_address_map(amap) == []


def test_write_run_hello_world_still_works(tmp_path):
    win, root = _win(tmp_path)
    _wire_full(win)
    _assign(win, root, _HELLO_WORLD, "hello_world.asm")
    win.write_program()
    win._do_run()
    assert "Hello World !" in win._sim_uart.output_text()


def test_ram_selftest_still_passes(tmp_path):
    win, root = _win(tmp_path)
    _wire_full(win)
    _assign(win, root, _RAM_SELFTEST, "ram_selftest.asm")
    win.write_program()
    win._do_run()
    assert "PASS" in win._sim_uart.output_text()


def test_legacy_mode_unchanged():
    win = MainWin()                      # no canvas parts -> legacy
    assert win._runtime.address_map["mode"] == "legacy"
    assert win._sim_ram.size == _SIM_RAM_SIZE
    assert win._sim_ram_node is None
    assert win._sim_cpu.id == "sim_cpu"


def test_vram_not_used_as_ram_runtime(tmp_path):
    # A circuit whose "RAM" node is actually a VRAM. As of
    # PATCH_MULTI_RAM_UART_ADDRESS_MAP_V08, resolve_circuit classifies by device_kind,
    # so a mem.vram node is NOT listed in plan["rams"] (never treated as RAM).
    win, root = _win(tmp_path)
    win._canvas.add_part_at(_CPU,  QPointF(0.0, 0.0))     # node_0001
    win._canvas.add_part_at(_VRAM, QPointF(200.0, 0.0))   # node_0002 (VRAM, not RAM)
    win._canvas.add_part_at(_UART, QPointF(400.0, 0.0))   # node_0003
    win._canvas.add_connection("node_0001", "bus", "node_0002", "bus")
    win._canvas.add_connection("node_0001", "bus", "node_0003", "bus")
    plan = win._resolve_circuit_plan()
    assert "node_0002" not in plan["rams"]   # VRAM is not a RAM
    assert plan["rams"] == []                # the only mem node here is a VRAM
