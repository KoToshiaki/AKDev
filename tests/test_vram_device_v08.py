# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""PATCH_VRAM_DEVICE_V08 — mem.vram writable framebuffer device + VramPart runtime.

VRAM is a writable memory device (kind=vram, role=memory): the CPU reaches it with
the existing LD/ST (32-bit little-endian words; no new instruction). For display it
is also a 1-byte-per-pixel image. Cleared to 0 on reset. Not placed unless a layout
(game16) or an Address Map Editor override gives it a base.
"""
import sys
import struct
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF

_app = QApplication.instance() or QApplication(sys.argv)

from core.devices import (
    device_kind, device_role, is_addressable_kind, is_runtime_backed_kind,
    make_device_spec, get_memory_layout,
    CIRCUIT_COMPAT, LEGACY, GAME16,
)
from core.dev import VramPart
from core.sim import BusError
from core.circuit import (
    resolve_circuit, validate_address_map, build_address_map_from_devices,
)
from ui.win import MainWin
from ui.lib import load_parts
from ui.run_status import render_status
from core.project import create_project

_CPU  = {"id": "cpu.ak32", "name": "AK32", "category": "cpu"}
_RAM  = {"id": "mem.ram",  "name": "RAM",  "category": "mem"}
_UART = {"id": "io.uart",  "name": "UART", "category": "io"}
_ROM  = {"id": "mem.rom",  "name": "ROM",  "category": "mem"}
_VRAM = {"id": "mem.vram", "name": "VRAM", "category": "mem"}
_HELLO_WORLD = Path(__file__).parent / "test" / "hello_world.asm"


def _nodes(*specs):
    return [{"node_id": nid, "category": cat, "part_id": pid, "name": pid}
            for (nid, cat, pid) in specs]


# ---------------------------------------------------------------------------
# part / library
# ---------------------------------------------------------------------------

def test_mem_vram_in_library():
    cats, errors = load_parts()
    assert not errors, errors
    ids = {p["id"] for plist in cats.values() for p in plist}
    assert "mem.vram" in ids
    part = next(p for plist in cats.values() for p in plist if p["id"] == "mem.vram")
    assert part.get("schema_version") == 2
    bus = next(pt for pt in part["ports"] if pt["name"] == "bus")
    assert bus["role"] == "slave" and bus["direction"] == "inout"
    names = {pt["name"] for pt in part["ports"]}
    assert {"bus", "clk", "reset"} <= names


# ---------------------------------------------------------------------------
# device registry
# ---------------------------------------------------------------------------

def test_device_kind_and_role():
    assert device_kind({"id": "mem.vram"}) == "vram"
    assert device_role("vram") == "memory"
    assert is_addressable_kind("vram") is True
    assert is_runtime_backed_kind("vram") is True


def test_vram_not_treated_as_ram():
    assert device_kind({"id": "mem.vram"}) != "ram"


def test_make_device_spec_vram_game16():
    s = make_device_spec("n5", _VRAM, mode="game16")
    assert s["kind"] == "vram"
    assert s["role"] == "memory"
    assert s["addressable"] is True
    assert s["runtime_backed"] is True
    assert s["runtime_id"] == "sim_vram"
    assert s["label"] == "VRAM"
    assert s["base"] == 0xC000 and s["size"] == 0x0400


def test_make_device_spec_vram_circuit_has_no_auto_base():
    s = make_device_spec("n5", _VRAM, mode="circuit")
    assert s["kind"] == "vram"
    assert s["runtime_id"] == "sim_vram"
    assert s["base"] is None and s["size"] is None
    assert s["attach_ranges"] == []


def test_layout_vram_regions():
    assert CIRCUIT_COMPAT.vram_base is None and CIRCUIT_COMPAT.vram_size is None
    assert LEGACY.vram_base is None and LEGACY.vram_size is None
    assert GAME16.vram_base == 0xC000 and GAME16.vram_size == 0x0400


def test_existing_layout_values_unchanged():
    # VRAM fields must not disturb established RAM/ROM/MMIO values.
    assert CIRCUIT_COMPAT.ram_base == 0x0000 and CIRCUIT_COMPAT.ram_size == 0x10000
    assert GAME16.rom_base == 0x0000 and GAME16.rom_size == 0x8000
    assert GAME16.ram_base == 0x8000 and GAME16.ram_size == 0x4000


# ---------------------------------------------------------------------------
# VramPart runtime
# ---------------------------------------------------------------------------

def test_vram_part_initial_zero():
    v = VramPart("sim_vram", "VRAM", size=0x400, base=0xC000)
    assert v.read(0xC000) == 0
    assert v.dump() == bytes(0x400)


def test_vram_part_write_read_word():
    v = VramPart("sim_vram", "VRAM", size=0x400, base=0xC000)
    v.write(0xC000, 0x12345678)
    assert v.read(0xC000) == 0x12345678
    # little-endian in the byte buffer
    assert v.dump()[:4] == bytes([0x78, 0x56, 0x34, 0x12])


def test_vram_part_pixel_view():
    v = VramPart("sim_vram", "VRAM", size=0x400, base=0xC000, width=32, height=32)
    v.set_pixel(0, 0, 0xAA)
    v.set_pixel(1, 0, 0xBB)
    assert v.pixel(0, 0) == 0xAA
    assert v.pixel(1, 0) == 0xBB
    # a word write stores 4 little-endian pixel bytes
    v.write(0xC000, 0x04030201)
    assert v.pixel(0, 0) == 0x01 and v.pixel(1, 0) == 0x02
    assert v.pixel(2, 0) == 0x03 and v.pixel(3, 0) == 0x04


def test_vram_part_set_pixel_masks_byte():
    v = VramPart("sim_vram", "VRAM", size=0x400, base=0x0000)
    v.set_pixel(0, 0, 0x1FF)
    assert v.pixel(0, 0) == 0xFF


def test_vram_part_reset_clears():
    v = VramPart("sim_vram", "VRAM", size=0x400, base=0xC000)
    v.write(0xC000, 0xDEADBEEF)
    v.reset()
    assert v.read(0xC000) == 0


def test_vram_part_out_of_range():
    v = VramPart("sim_vram", "VRAM", size=0x10, base=0xC000)
    try:
        v.read(0xD000)
        assert False, "expected BusError"
    except BusError:
        pass
    try:
        v.write(0xD000, 1)
        assert False, "expected BusError"
    except BusError:
        pass
    assert v.pixel(999, 999) == 0          # pixel view is defensive


def test_vram_part_pixel_out_of_range_setter_noop():
    v = VramPart("sim_vram", "VRAM", size=0x10, base=0x0000)
    v.set_pixel(999, 999, 0x55)            # no exception, no change
    assert v.dump() == bytes(0x10)


# ---------------------------------------------------------------------------
# resolve_circuit
# ---------------------------------------------------------------------------

def test_resolve_collects_vram():
    nodes = _nodes(("n1", "cpu", "cpu.ak32"), ("n2", "mem", "mem.ram"),
                   ("n3", "io", "io.uart"), ("n4", "mem", "mem.vram"))
    conns = [{"from_node": "n1", "to_node": n} for n in ("n2", "n3", "n4")]
    plan = resolve_circuit(nodes, conns)
    assert plan["ok"] is True
    assert plan["vrams"] == ["n4"]
    kinds = {d["node_id"]: d["kind"] for d in plan["devices"]}
    assert kinds["n4"] == "vram"


def test_resolve_no_vram_is_unchanged():
    nodes = _nodes(("n1", "cpu", "cpu.ak32"), ("n2", "mem", "mem.ram"),
                   ("n3", "io", "io.uart"))
    conns = [{"from_node": "n1", "to_node": n} for n in ("n2", "n3")]
    plan = resolve_circuit(nodes, conns)
    assert plan["vrams"] == []
    assert plan["ok"] is True            # VRAM is not required


def test_unconnected_vram_not_collected():
    nodes = _nodes(("n1", "cpu", "cpu.ak32"), ("n2", "mem", "mem.ram"),
                   ("n3", "io", "io.uart"), ("n4", "mem", "mem.vram"))
    conns = [{"from_node": "n1", "to_node": n} for n in ("n2", "n3")]  # n4 dangling
    plan = resolve_circuit(nodes, conns)
    assert plan["vrams"] == []
    assert plan["ok"] is True


# ---------------------------------------------------------------------------
# Address Map (game16 non-overlap + overlap detection)
# ---------------------------------------------------------------------------

def test_game16_rom_ram_vram_non_overlapping():
    rom  = make_device_spec("n4", _ROM,  mode="game16")
    ram  = make_device_spec("n2", _RAM,  mode="game16")
    vram = make_device_spec("n5", _VRAM, mode="game16")
    amap = build_address_map_from_devices("game16", [rom, ram, vram], layout=GAME16)
    v = next(d for d in amap["devices"] if d["kind"] == "vram")
    assert v["base"] == 0xC000 and v["end"] == 0xC3FF
    assert validate_address_map(amap) == []


def test_vram_ram_overlap_detected():
    vram = dict(make_device_spec("n5", _VRAM, mode="circuit"),
                base=0x0000, size=0x0400, end=0x03FF,
                attach_ranges=[(0x0000, 0x03FF)])
    ram = dict(make_device_spec("n2", _RAM, mode="circuit"))  # 0x0000-0xFFFF
    amap = build_address_map_from_devices("circuit", [vram, ram],
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


def _assign(win, root, text, name):
    dst = root / "tests" / "test"
    dst.mkdir(parents=True, exist_ok=True)
    (dst / name).write_text(text, encoding="utf-8")
    win._canvas.set_node_source("node_0001", "asm", f"tests/test/{name}")


def _wire_with_vram(win):
    win._canvas.add_part_at(_CPU,  QPointF(0.0, 0.0))     # node_0001
    win._canvas.add_part_at(_RAM,  QPointF(200.0, 0.0))   # node_0002
    win._canvas.add_part_at(_UART, QPointF(400.0, 0.0))   # node_0003
    win._canvas.add_part_at(_VRAM, QPointF(600.0, 0.0))   # node_0004
    win._canvas.add_connection("node_0001", "bus", "node_0002", "bus")
    win._canvas.add_connection("node_0001", "bus", "node_0003", "bus")
    win._canvas.add_connection("node_0001", "bus", "node_0004", "bus")


def _wire_with_rom_and_vram(win):
    win._canvas.add_part_at(_CPU,  QPointF(0.0, 0.0))     # node_0001
    win._canvas.add_part_at(_RAM,  QPointF(200.0, 0.0))   # node_0002
    win._canvas.add_part_at(_UART, QPointF(400.0, 0.0))   # node_0003
    win._canvas.add_part_at(_ROM,  QPointF(600.0, 0.0))   # node_0004
    win._canvas.add_part_at(_VRAM, QPointF(800.0, 0.0))   # node_0005
    for n in ("node_0002", "node_0003", "node_0004", "node_0005"):
        win._canvas.add_connection("node_0001", "bus", n, "bus")


def _wire_plain(win):
    win._canvas.add_part_at(_CPU,  QPointF(0.0, 0.0))
    win._canvas.add_part_at(_RAM,  QPointF(200.0, 0.0))
    win._canvas.add_part_at(_UART, QPointF(400.0, 0.0))
    win._canvas.add_connection("node_0001", "bus", "node_0002", "bus")
    win._canvas.add_connection("node_0001", "bus", "node_0003", "bus")


# VRAM at 0xC000 (size 0x400); RAM shrunk to 0x0000-0xBFFF so nothing overlaps.
def _vram_override():
    return {
        "node_0004": {"mode": "manual", "base": 0xC000, "size": 0x0400},
        "node_0002": {"mode": "manual", "base": 0x0000, "size": 0xC000},
    }


def test_vram_unplaced_in_circuit_compat_default(tmp_path):
    win, root = _win(tmp_path)
    _wire_with_vram(win)
    _assign(win, root, _HELLO_WORLD.read_text(encoding="utf-8"), "hello_world.asm")
    win.write_program()
    assert win._sim_vram is None                  # no override -> unplaced
    amap = win._runtime.address_map
    assert not any(d["kind"] == "vram" for d in amap["devices"])
    win._do_run()
    assert "Hello World !" in win._sim_uart.output_text()


def test_vram_runtime_built_with_override(tmp_path):
    win, root = _win(tmp_path)
    _wire_with_vram(win)
    win.apply_address_map_overrides(_vram_override())
    assert win._sim_vram is not None
    assert win._sim_vram_node == "node_0004"
    assert win._sim_vram.id == "sim_vram"
    amap = win._runtime.address_map
    v = next(d for d in amap["devices"] if d["kind"] == "vram")
    assert v["base"] == 0xC000 and v["end"] == 0xC3FF
    assert v["device_id"] == "sim_vram"
    assert validate_address_map(amap) == []


def test_cpu_writes_and_reads_vram(tmp_path):
    win, root = _win(tmp_path)
    _wire_with_vram(win)
    win.apply_address_map_overrides(_vram_override())
    prog = "LDI r1, 0xC000\nLDI r2, 0x00ff\nST [r1], r2\nLD r3, [r1]\nHALT\n"
    _assign(win, root, prog, "vram_rw.asm")
    win.write_program()
    win._do_run()
    assert win._sim_cpu.regs()[3] == 0x00FF       # read back what ST wrote
    assert win._sim_vram.dump()[:4] == bytes([0xFF, 0x00, 0x00, 0x00])  # little-endian


def test_rom_target_writes_vram(tmp_path):
    win, root = _win(tmp_path)
    _wire_with_rom_and_vram(win)
    # ROM 0x0000 / RAM 0x0200-0xBFFF / VRAM 0xC000 — non-overlapping.
    win.apply_address_map_overrides({
        "node_0004": {"mode": "manual", "base": 0x0000, "size": 0x0100},  # ROM
        "node_0002": {"mode": "manual", "base": 0x0200, "size": 0xBE00},  # RAM
        "node_0005": {"mode": "manual", "base": 0xC000, "size": 0x0400},  # VRAM
    })
    win.set_program_target("rom")
    prog = "LDI r1, 0xC000\nLDI r2, 0x00aa\nST [r1], r2\nHALT\n"
    _assign(win, root, prog, "rom_vram.asm")
    assert win.write_program() is True
    assert win._sim_cpu.pc() == win._sim_rom.base   # ROM target -> reset_pc = ROM base
    win._do_run()
    assert win._sim_vram.dump()[0] == 0xAA          # ROM-fetched code wrote VRAM
    assert win._sim_cpu.halted() is True


# ---------------------------------------------------------------------------
# existing compatibility (no VRAM device)
# ---------------------------------------------------------------------------

def test_no_vram_address_map_unchanged(tmp_path):
    win, root = _win(tmp_path)
    _wire_plain(win)
    _assign(win, root, _HELLO_WORLD.read_text(encoding="utf-8"), "hello_world.asm")
    win.write_program()
    amap = win._runtime.address_map
    ram = next(d for d in amap["devices"] if d["kind"] == "ram")
    assert ram["attach_ranges"] == [(0x0000, 0x00FF), (0x0108, 0xFFFF)]
    assert not any(d["kind"] == "vram" for d in amap["devices"])
    assert win._sim_vram is None
    win._do_run()
    assert "Hello World !" in win._sim_uart.output_text()


def test_legacy_mode_has_no_vram():
    win = MainWin()
    assert win._sim_vram is None


# ---------------------------------------------------------------------------
# Run Status
# ---------------------------------------------------------------------------

def test_run_status_vram_none():
    assert "VRAM: None" in render_status({"mode": "legacy"})


def test_run_status_vram_present():
    txt = render_status({"mode": "circuit",
                         "vram": {"base": 0xC000, "size": 0x0400}})
    assert "VRAM: base=0xc000 size=0x0400" in txt


def test_run_status_shows_vram_when_placed(tmp_path):
    win, root = _win(tmp_path)
    _wire_with_vram(win)
    win.apply_address_map_overrides(_vram_override())
    win._update_run_status()
    assert "VRAM: base=0xc000" in win._run_status.status_text()
