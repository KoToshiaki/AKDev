# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""PATCH_GAME_RUNTIME_MINIMAL_V08 — minimal game runtime (ROM + Input + Timer + VRAM).

This patch adds no new CPU instruction and no new runtime class: it places ROM,
Input, Timer and VRAM together, runs a sample program from ROM that reads Input /
Timer and writes VRAM with the existing LD/ST, and shows the framebuffer in a small
grayscale VRAM Viewer that refreshes with the existing Step/Run/Reset panels.

The standard game map is game16 (ROM 0x0000 / RAM 0x8000 / VRAM 0xC000 / MMIO 0xE000);
that layout is checked at unit level here. MainWin auto-selects circuit_compat, so the
integration tests place ROM/RAM/VRAM with Address Map Editor overrides (the proven
path) and read the real Input/Timer MMIO bases from the runtime rather than hardcoding.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF

_app = QApplication.instance() or QApplication(sys.argv)

from core.devices import (
    make_device_spec, assign_mmio_bases, get_memory_layout, GAME16,
)
from core.dev import VramPart
from core.circuit import build_address_map_from_devices, validate_address_map
from ui.win import MainWin
from ui.run_status import render_status
from ui.vram_viewer import VramViewer
from core.project import create_project

_CPU   = {"id": "cpu.ak32", "name": "AK32",  "category": "cpu"}
_RAM   = {"id": "mem.ram",  "name": "RAM",   "category": "mem"}
_UART  = {"id": "io.uart",  "name": "UART",  "category": "io"}
_ROM   = {"id": "mem.rom",  "name": "ROM",   "category": "mem"}
_INPUT = {"id": "io.input", "name": "INPUT", "category": "io"}
_TIMER = {"id": "io.timer", "name": "TIMER", "category": "io"}
_VRAM  = {"id": "mem.vram", "name": "VRAM",  "category": "mem"}
_HELLO_WORLD = Path(__file__).parent / "test" / "hello_world.asm"


# ---------------------------------------------------------------------------
# game16 layout — ROM 0x0000 / RAM 0x8000 / VRAM 0xC000 / MMIO 0xE000
# ---------------------------------------------------------------------------

def test_game16_layout_constants():
    assert GAME16.rom_base == 0x0000 and GAME16.rom_size == 0x8000
    assert GAME16.ram_base == 0x8000 and GAME16.ram_size == 0x4000
    assert GAME16.vram_base == 0xC000 and GAME16.vram_size == 0x0400
    assert GAME16.mmio_base == 0xE000


def test_game16_rom_ram_vram_non_overlapping():
    rom  = make_device_spec("n4", _ROM,  mode="game16")
    ram  = make_device_spec("n2", _RAM,  mode="game16")
    vram = make_device_spec("n7", _VRAM, mode="game16")
    amap = build_address_map_from_devices("game16", [rom, ram, vram], layout=GAME16)
    v = next(d for d in amap["devices"] if d["kind"] == "vram")
    assert v["base"] == 0xC000 and v["end"] == 0xC3FF
    assert validate_address_map(amap) == []


def test_game16_mmio_bases_uart_input_timer():
    # UART / Input / Timer are MMIO windows: in game16 they land at 0xE000/0xE010/0xE020
    # in encounter order; ROM/RAM/VRAM are memory-role and consume no MMIO slot.
    specs = [
        make_device_spec("n1", _CPU,   mode="game16"),
        make_device_spec("n2", _RAM,   mode="game16"),
        make_device_spec("n3", _UART,  mode="game16"),
        make_device_spec("n5", _INPUT, mode="game16"),
        make_device_spec("n6", _TIMER, mode="game16"),
        make_device_spec("n7", _VRAM,  mode="game16"),
    ]
    placed = assign_mmio_bases(specs, layout=GAME16)
    by_kind = {s["kind"]: s for s in placed}
    assert by_kind["uart"]["base"] == 0xE000
    assert by_kind["input"]["base"] == 0xE010
    assert by_kind["timer"]["base"] == 0xE020


def test_game16_all_devices_non_overlapping():
    specs = [
        make_device_spec("n1", _CPU,   mode="game16"),
        make_device_spec("n2", _RAM,   mode="game16"),
        make_device_spec("n3", _UART,  mode="game16"),
        make_device_spec("n4", _ROM,   mode="game16"),
        make_device_spec("n5", _INPUT, mode="game16"),
        make_device_spec("n6", _TIMER, mode="game16"),
        make_device_spec("n7", _VRAM,  mode="game16"),
    ]
    placed = assign_mmio_bases(specs, layout=GAME16)
    amap = build_address_map_from_devices("game16", placed, layout=GAME16)
    assert validate_address_map(amap) == []


# ---------------------------------------------------------------------------
# VramViewer (display layer — read-only, headless-checkable)
# ---------------------------------------------------------------------------

def test_vram_viewer_none_is_inactive():
    vw = VramViewer()
    vw.update_from_vram(None)
    assert vw.is_active() is False
    assert vw.snapshot() == b""
    assert vw.pixel(0, 0) == 0


def test_vram_viewer_reflects_vram():
    v = VramPart("sim_vram", "VRAM", size=0x400, base=0xC000, width=32, height=32)
    v.set_pixel(0, 0, 0xFF)
    v.set_pixel(1, 0, 0x80)
    v.set_pixel(0, 1, 0x10)
    vw = VramViewer()
    vw.update_from_vram(v)
    assert vw.is_active() is True
    assert vw.snapshot() == v.dump()
    assert vw.pixel(0, 0) == 0xFF
    assert vw.pixel(1, 0) == 0x80
    assert vw.pixel(0, 1) == 0x10


def test_vram_viewer_does_not_mutate_vram():
    v = VramPart("sim_vram", "VRAM", size=0x400, base=0xC000)
    v.write(0xC000, 0x04030201)
    before = v.dump()
    VramViewer().update_from_vram(v)
    assert v.dump() == before


# ---------------------------------------------------------------------------
# Run Status — minimal Game line
# ---------------------------------------------------------------------------

def test_run_status_game_none():
    assert "Game: None" in render_status({"mode": "legacy"})


def test_run_status_game_components():
    txt = render_status({"mode": "circuit", "game": "ROM+Input+Timer+VRAM"})
    assert "Game: ROM+Input+Timer+VRAM" in txt


# ---------------------------------------------------------------------------
# MainWin integration — circuit_compat + Address Map overrides
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


def _wire_game(win):
    """CPU + RAM + UART + ROM + Input + Timer + VRAM, all on the CPU bus."""
    win._canvas.add_part_at(_CPU,   QPointF(0.0, 0.0))      # node_0001
    win._canvas.add_part_at(_RAM,   QPointF(200.0, 0.0))    # node_0002
    win._canvas.add_part_at(_UART,  QPointF(400.0, 0.0))    # node_0003
    win._canvas.add_part_at(_ROM,   QPointF(600.0, 0.0))    # node_0004
    win._canvas.add_part_at(_INPUT, QPointF(800.0, 0.0))    # node_0005
    win._canvas.add_part_at(_TIMER, QPointF(1000.0, 0.0))   # node_0006
    win._canvas.add_part_at(_VRAM,  QPointF(1200.0, 0.0))   # node_0007
    for n in ("node_0002", "node_0003", "node_0004",
              "node_0005", "node_0006", "node_0007"):
        win._canvas.add_connection("node_0001", "bus", n, "bus")


def _wire_plain(win):
    win._canvas.add_part_at(_CPU,  QPointF(0.0, 0.0))
    win._canvas.add_part_at(_RAM,  QPointF(200.0, 0.0))
    win._canvas.add_part_at(_UART, QPointF(400.0, 0.0))
    win._canvas.add_connection("node_0001", "bus", "node_0002", "bus")
    win._canvas.add_connection("node_0001", "bus", "node_0003", "bus")


# ROM 0x0000-0x00FF / MMIO 0x0100-0x012F / RAM 0x0200-0xBFFF / VRAM 0xC000-0xC3FF.
# ROM stays below the MMIO window so UART/Input/Timer (0x0100/0x0110/0x0120) fit.
def _game_override():
    return {
        "node_0004": {"mode": "manual", "base": 0x0000, "size": 0x0100},  # ROM
        "node_0002": {"mode": "manual", "base": 0x0200, "size": 0xBE00},  # RAM
        "node_0007": {"mode": "manual", "base": 0xC000, "size": 0x0400},  # VRAM
    }


def _setup_game(tmp_path):
    win, root = _win(tmp_path)
    _wire_game(win)
    win.apply_address_map_overrides(_game_override())
    return win, root


def test_rom_input_timer_vram_coexist(tmp_path):
    win, _ = _setup_game(tmp_path)
    # All four game devices are runtime-backed at once.
    assert win._sim_rom is not None
    assert win._sim_input is not None
    assert win._sim_timer is not None
    assert win._sim_vram is not None
    # Address Map is overlap-free with all of them placed.
    amap = win._runtime.address_map
    assert validate_address_map(amap) == []
    kinds = {d["kind"] for d in amap["devices"]}
    assert {"rom", "ram", "vram"} <= kinds


def test_rom_target_writes_vram(tmp_path):
    win, root = _setup_game(tmp_path)
    win.set_program_target("rom")
    prog = "LDI r1, 0xC000\nLDI r2, 0x00AA\nST [r1], r2\nHALT\n"
    _assign(win, root, prog, "g_fixed.asm")
    assert win.write_program() is True
    assert win._sim_cpu.pc() == win._sim_rom.base    # ROM target -> reset_pc = ROM base
    win._do_run()
    assert win._sim_vram.dump()[0] == 0xAA
    assert win._sim_cpu.halted() is True


def test_input_value_written_to_vram(tmp_path):
    win, root = _setup_game(tmp_path)
    win.set_program_target("rom")
    in_base = win._sim_input.base                    # real MMIO base (read, not hardcoded)
    prog = (f"LDI r1, 0x{in_base:04X}\nLD r2, [r1]\n"
            f"LDI r3, 0xC000\nST [r3], r2\nHALT\n")
    _assign(win, root, prog, "g_input.asm")
    assert win.write_program() is True
    win.set_input_keys(0x05)                         # buttons 0 and 2 held
    win._do_run()
    assert win._sim_vram.dump()[0] == 0x05


def test_timer_value_written_to_vram(tmp_path):
    win, root = _setup_game(tmp_path)
    win.set_program_target("rom")
    tm_base = win._sim_timer.base                    # real MMIO base (read, not hardcoded)
    prog = (f"LDI r1, 0x{tm_base:04X}\nLD r2, [r1]\n"
            f"LDI r3, 0xC000\nST [r3], r2\nHALT\n")
    _assign(win, root, prog, "g_timer.asm")
    assert win.write_program() is True
    win._do_run()
    # The timer advances one tick per executed step, so a non-zero tick reached VRAM.
    assert win._sim_vram.dump()[0] != 0


def test_run_changes_vram_loop(tmp_path):
    win, root = _setup_game(tmp_path)
    win.set_program_target("rom")
    prog = ("LDI r1, 0xC000\nLDI r2, 0x0000\n"
            "loop:\nST [r1], r2\nADDI r2, r2, 1\nJMP loop\n")
    _assign(win, root, prog, "g_loop.asm")
    assert win.write_program() is True
    assert win._sim_vram.read(0xC000) == 0           # cleared before run
    win._do_run()                                    # stops at the 1000-cycle cap
    assert win._sim_cpu.halted() is False
    assert win._sim_vram.read(0xC000) != 0           # VRAM changed during the run


# ---------------------------------------------------------------------------
# Viewer refresh through the normal Step/Run panels
# ---------------------------------------------------------------------------

def test_viewer_refreshes_after_run(tmp_path):
    win, root = _setup_game(tmp_path)
    win.set_program_target("rom")
    prog = "LDI r1, 0xC000\nLDI r2, 0x00FF\nST [r1], r2\nHALT\n"
    _assign(win, root, prog, "g_view.asm")
    assert win.write_program() is True
    win._do_run()
    # The viewer mirrors the VRAM after the standard run refresh.
    assert win._vram_viewer.is_active() is True
    assert win._vram_viewer.snapshot() == win._sim_vram.dump()
    assert win._vram_viewer.pixel(0, 0) == 0xFF


def test_run_status_shows_game_components(tmp_path):
    win, _ = _setup_game(tmp_path)
    win._update_run_status()
    txt = win._run_status.status_text()
    assert "Game:" in txt
    assert "VRAM" in txt
    assert "Timer" in txt


# ---------------------------------------------------------------------------
# Existing compatibility — no VRAM / no game devices
# ---------------------------------------------------------------------------

def test_plain_circuit_unaffected(tmp_path):
    win, root = _win(tmp_path)
    _wire_plain(win)
    _assign(win, root, _HELLO_WORLD.read_text(encoding="utf-8"), "hello_world.asm")
    win.write_program()
    assert win._sim_vram is None
    assert win._vram_viewer.is_active() is False     # viewer harmless when unplaced
    win._do_run()
    assert "Hello World !" in win._sim_uart.output_text()


def test_legacy_window_viewer_inactive():
    win = MainWin()
    assert win._sim_vram is None
    assert win._vram_viewer.is_active() is False
    assert "Game: None" in win._run_status.status_text()
