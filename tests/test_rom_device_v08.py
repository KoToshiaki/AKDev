# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""PATCH_ROM_DEVICE_V08 — mem.rom read-only memory device + RomPart runtime."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF

_app = QApplication.instance() or QApplication(sys.argv)

from core.devices import (
    device_kind, device_role, is_addressable_kind, is_runtime_backed_kind,
    make_device_spec, get_memory_layout, CIRCUIT_COMPAT, LEGACY, GAME16,
)
from core.dev import RomPart
from core.sim import BusError
from core.circuit import (
    resolve_circuit, build_address_map_from_devices, validate_address_map,
)
from ui.win import MainWin
from ui.lib import load_parts
from ui.address_map_editor import COL_NODE
from core.project import create_project

_CPU  = {"id": "cpu.ak32", "name": "AK32", "category": "cpu"}
_RAM  = {"id": "mem.ram",  "name": "RAM",  "category": "mem"}
_UART = {"id": "io.uart",  "name": "UART", "category": "io"}
_ROM  = {"id": "mem.rom",  "name": "ROM",  "category": "mem"}
_HELLO_WORLD  = Path(__file__).parent / "test" / "hello_world.asm"
_RAM_SELFTEST = Path(__file__).parent / "test" / "ram_selftest.asm"


def _nodes(*specs):
    return [{"node_id": nid, "category": cat, "part_id": pid, "name": pid}
            for (nid, cat, pid) in specs]


# ---------------------------------------------------------------------------
# part / library
# ---------------------------------------------------------------------------

def test_mem_rom_in_library():
    cats, errors = load_parts()
    assert not errors, errors
    ids = {p["id"] for plist in cats.values() for p in plist}
    assert "mem.rom" in ids
    part = next(p for plist in cats.values() for p in plist if p["id"] == "mem.rom")
    assert part.get("schema_version") == 2
    bus = next(pt for pt in part["ports"] if pt["name"] == "bus")
    assert bus["role"] == "slave" and bus["direction"] == "inout"


# ---------------------------------------------------------------------------
# device registry
# ---------------------------------------------------------------------------

def test_device_kind_and_role():
    assert device_kind({"id": "mem.rom"}) == "rom"
    assert device_role("rom") == "memory"
    assert is_addressable_kind("rom") is True
    assert is_runtime_backed_kind("rom") is True


def test_make_device_spec_rom_game16():
    s = make_device_spec("n5", _ROM, mode="game16")
    assert s["kind"] == "rom"
    assert s["role"] == "memory"
    assert s["addressable"] is True
    assert s["runtime_backed"] is True
    assert s["runtime_id"] == "sim_rom"
    assert s["label"] == "ROM"
    assert s["base"] == 0x0000 and s["size"] == 0x8000


def test_make_device_spec_rom_circuit_has_no_auto_base():
    # circuit_compat has no ROM region: ROM is unplaced until an Editor override.
    s = make_device_spec("n5", _ROM, mode="circuit")
    assert s["kind"] == "rom"
    assert s["runtime_id"] == "sim_rom"
    assert s["base"] is None and s["size"] is None
    assert s["attach_ranges"] == []


# ---------------------------------------------------------------------------
# MemoryLayout / base_size
# ---------------------------------------------------------------------------

def test_layout_rom_regions():
    assert CIRCUIT_COMPAT.rom_base is None and CIRCUIT_COMPAT.rom_size is None
    assert LEGACY.rom_base is None and LEGACY.rom_size is None
    assert GAME16.rom_base == 0x0000 and GAME16.rom_size == 0x8000


def test_existing_layout_values_unchanged():
    # ROM fields must not disturb the established RAM/MMIO layout values.
    assert CIRCUIT_COMPAT.ram_base == 0x0000 and CIRCUIT_COMPAT.ram_size == 0x10000
    assert CIRCUIT_COMPAT.mmio_base == 0x0100 and CIRCUIT_COMPAT.mmio_size == 0x08
    assert CIRCUIT_COMPAT.reset_pc == 0x0000
    assert LEGACY.ram_size == 0x0100
    assert GAME16.ram_base == 0x8000 and GAME16.ram_size == 0x4000


# ---------------------------------------------------------------------------
# RomPart runtime
# ---------------------------------------------------------------------------

def test_rom_part_load_and_read():
    p = RomPart("sim_rom", "ROM", size=0x100, base=0x0000)
    p.load_bytes(bytes([0x78, 0x56, 0x34, 0x12]))
    assert p.read(0x0000) == 0x12345678          # 32-bit little-endian word


def test_rom_part_write_is_noop():
    p = RomPart("sim_rom", "ROM", size=0x100, base=0x0000)
    p.load_bytes(bytes([0x01, 0x00, 0x00, 0x00]))
    p.write(0x0000, 0xDEADBEEF)                   # read-only -> ignored, no error
    assert p.read(0x0000) == 0x00000001


def test_rom_part_reset_keeps_content():
    p = RomPart("sim_rom", "ROM", size=0x100, base=0x0000)
    p.load_bytes(bytes([0xFF, 0x00, 0x00, 0x00]))
    p.reset()                                     # ROM image survives reset
    assert p.read(0x0000) == 0x000000FF


def test_rom_part_dump():
    p = RomPart("sim_rom", "ROM", size=0x08, base=0x0000)
    p.load_bytes(b"\x01\x02\x03\x04")
    assert p.dump() == b"\x01\x02\x03\x04\x00\x00\x00\x00"


def test_rom_part_out_of_range():
    p = RomPart("sim_rom", "ROM", size=0x08, base=0x0000)
    # out-of-range read raises BusError (same policy as RamPart); write is a no-op.
    try:
        p.read(0x1000)
        assert False, "expected BusError"
    except BusError:
        pass
    p.write(0x1000, 1)                            # read-only -> silently ignored


def test_rom_part_base_offset():
    p = RomPart("sim_rom", "ROM", size=0x10, base=0x2000)
    p.load_bytes(bytes([0xAA, 0x00, 0x00, 0x00]), offset=4)
    assert p.read(0x2004) == 0x000000AA


# ---------------------------------------------------------------------------
# resolve_circuit — ROM collected as addressable device
# ---------------------------------------------------------------------------

def test_resolve_collects_rom():
    nodes = _nodes(("n1", "cpu", "cpu.ak32"), ("n2", "mem", "mem.ram"),
                   ("n3", "io", "io.uart"), ("n4", "mem", "mem.rom"))
    conns = [{"from_node": "n1", "to_node": n} for n in ("n2", "n3", "n4")]
    plan = resolve_circuit(nodes, conns)
    assert plan["ok"] is True
    assert plan["roms"] == ["n4"]
    kinds = {d["node_id"]: d["kind"] for d in plan["devices"]}
    assert kinds == {"n2": "ram", "n3": "uart", "n4": "rom"}


def test_resolve_no_rom_is_unchanged():
    nodes = _nodes(("n1", "cpu", "cpu.ak32"), ("n2", "mem", "mem.ram"),
                   ("n3", "io", "io.uart"))
    conns = [{"from_node": "n1", "to_node": n} for n in ("n2", "n3")]
    plan = resolve_circuit(nodes, conns)
    assert plan["roms"] == []
    assert plan["ok"] is True                     # ROM is not required


def test_unconnected_rom_not_collected():
    nodes = _nodes(("n1", "cpu", "cpu.ak32"), ("n2", "mem", "mem.ram"),
                   ("n3", "io", "io.uart"), ("n4", "mem", "mem.rom"))
    conns = [{"from_node": "n1", "to_node": n} for n in ("n2", "n3")]  # n4 dangling
    plan = resolve_circuit(nodes, conns)
    assert plan["roms"] == []
    assert plan["ok"] is True


# ---------------------------------------------------------------------------
# Address Map — game16 non-overlap and overlap detection
# ---------------------------------------------------------------------------

def test_game16_rom_ram_non_overlapping():
    rom = make_device_spec("n4", _ROM, mode="game16")
    ram = make_device_spec("n2", _RAM, mode="game16")
    amap = build_address_map_from_devices("game16", [rom, ram],
                                          layout=GAME16)
    r = next(d for d in amap["devices"] if d["kind"] == "rom")
    m = next(d for d in amap["devices"] if d["kind"] == "ram")
    assert r["base"] == 0x0000 and r["end"] == 0x7FFF
    assert m["base"] == 0x8000 and m["end"] == 0xBFFF
    assert validate_address_map(amap) == []


def test_rom_ram_overlap_detected():
    # Two memory devices on the same range -> unintended overlap.
    rom = dict(make_device_spec("n4", _ROM, mode="circuit"),
               base=0x0000, size=0x1000, end=0x0FFF,
               attach_ranges=[(0x0000, 0x0FFF)])
    ram = dict(make_device_spec("n2", _RAM, mode="circuit"))  # 0x0000-0xFFFF
    amap = build_address_map_from_devices("circuit", [rom, ram],
                                          layout=CIRCUIT_COMPAT)
    assert validate_address_map(amap)             # overlap reported


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


def _wire_with_rom(win):
    win._canvas.add_part_at(_CPU,  QPointF(0.0, 0.0))     # node_0001
    win._canvas.add_part_at(_RAM,  QPointF(200.0, 0.0))   # node_0002
    win._canvas.add_part_at(_UART, QPointF(400.0, 0.0))   # node_0003
    win._canvas.add_part_at(_ROM,  QPointF(600.0, 0.0))   # node_0004
    win._canvas.add_connection("node_0001", "bus", "node_0002", "bus")
    win._canvas.add_connection("node_0001", "bus", "node_0003", "bus")
    win._canvas.add_connection("node_0001", "bus", "node_0004", "bus")


def _wire_plain(win):
    win._canvas.add_part_at(_CPU,  QPointF(0.0, 0.0))
    win._canvas.add_part_at(_RAM,  QPointF(200.0, 0.0))
    win._canvas.add_part_at(_UART, QPointF(400.0, 0.0))
    win._canvas.add_connection("node_0001", "bus", "node_0002", "bus")
    win._canvas.add_connection("node_0001", "bus", "node_0003", "bus")


def _assign(win, root, text, name):
    dst = root / "tests" / "test"
    dst.mkdir(parents=True, exist_ok=True)
    (dst / name).write_text(text, encoding="utf-8")
    win._canvas.set_node_source("node_0001", "asm", f"tests/test/{name}")


def test_rom_unplaced_in_circuit_compat_default(tmp_path):
    # With no override the circuit_compat ROM has no base -> not placed, no runtime
    # Part, Hello World still runs on RAM/UART exactly as before.
    win, root = _win(tmp_path)
    _wire_with_rom(win)
    _assign(win, root, _HELLO_WORLD.read_text(encoding="utf-8"), "hello_world.asm")
    win.write_program()
    assert win._sim_rom is None                   # unplaced ROM is not runtime-backed
    amap = win._runtime.address_map
    assert not any(d["kind"] == "rom" for d in amap["devices"])
    win._do_run()
    assert "Hello World !" in win._sim_uart.output_text()


def test_rom_runtime_built_with_override(tmp_path):
    win, root = _win(tmp_path)
    _wire_with_rom(win)
    # Give the ROM a base/size and shrink RAM so nothing overlaps.
    win.apply_address_map_overrides({
        "node_0004": {"mode": "manual", "base": 0x0000, "size": 0x0100},
        "node_0002": {"mode": "manual", "base": 0x0200, "size": 0xFE00},
    })
    assert win._sim_rom is not None
    assert win._sim_rom_node == "node_0004"
    assert win._sim_rom.id == "sim_rom"
    amap = win._runtime.address_map
    rom = next(d for d in amap["devices"] if d["kind"] == "rom")
    assert rom["base"] == 0x0000 and rom["end"] == 0x00FF
    assert rom["device_id"] == "sim_rom"
    assert validate_address_map(amap) == []


def test_rom_is_read_only_through_bus(tmp_path):
    win, root = _win(tmp_path)
    _wire_with_rom(win)
    win.apply_address_map_overrides({
        "node_0004": {"mode": "manual", "base": 0x0000, "size": 0x0100},
        "node_0002": {"mode": "manual", "base": 0x0200, "size": 0xFE00},
    })
    win._sim_rom.load_bytes(bytes([0x11, 0x00, 0x00, 0x00]))
    win._sim_bus.write(0x0000, 0xDEADBEEF)        # bus write to ROM -> ignored
    assert win._sim_bus.read(0x0000) == 0x00000011


def test_rom_in_address_map_editor(tmp_path):
    win, root = _win(tmp_path)
    _wire_with_rom(win)
    win._address_map_editor.refresh()
    nodes = {win._address_map_editor._table.item(r, COL_NODE).text()
             for r in range(win._address_map_editor._table.rowCount())}
    assert "node_0004" in nodes                   # ROM shown in the editor


def test_rom_ram_overlap_blocks_apply(tmp_path):
    win, root = _win(tmp_path)
    _wire_with_rom(win)
    # ROM over 0x0000 while RAM (auto) still fills 64KB -> overlap error.
    issues = win.validate_address_map_overrides(
        {"node_0004": {"mode": "manual", "base": 0x0000, "size": 0x1000}})
    assert any(i["severity"] == "error" for i in issues)


# ---------------------------------------------------------------------------
# existing compatibility (no ROM device)
# ---------------------------------------------------------------------------

def test_no_rom_address_map_unchanged(tmp_path):
    win, root = _win(tmp_path)
    _wire_plain(win)
    _assign(win, root, _HELLO_WORLD.read_text(encoding="utf-8"), "hello_world.asm")
    win.write_program()
    amap = win._runtime.address_map
    ram = next(d for d in amap["devices"] if d["kind"] == "ram")
    assert ram["attach_ranges"] == [(0x0000, 0x00FF), (0x0108, 0xFFFF)]
    assert not any(d["kind"] == "rom" for d in amap["devices"])
    win._do_run()
    assert "Hello World !" in win._sim_uart.output_text()


def test_selftest_unchanged(tmp_path):
    win, root = _win(tmp_path)
    _wire_plain(win)
    _assign(win, root, _RAM_SELFTEST.read_text(encoding="utf-8"), "ram_selftest.asm")
    win.write_program()
    win._do_run()
    assert "PASS" in win._sim_uart.output_text()


def test_legacy_mode_unchanged():
    win = MainWin()
    assert win._runtime.address_map["mode"] == "legacy"
    assert win._sim_rom is None
