# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""PATCH_PROGRAM_TARGET_ROM_V08 — Write Program load target (RAM default / ROM).

Default is RAM (existing behaviour, fully compatible). ROM target loads via
``RomPart.load_bytes`` (IDE loader, not the bus), sets the CPU reset PC to the ROM
base, and errors (no silent RAM fallback) when the ROM runtime is missing/unplaced,
the Address Map overlaps, or the program does not fit.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF

_app = QApplication.instance() or QApplication(sys.argv)

from ui.win import MainWin
from core.project import create_project, load_project, save_system

_CPU  = {"id": "cpu.ak32", "name": "AK32", "category": "cpu"}
_RAM  = {"id": "mem.ram",  "name": "RAM",  "category": "mem"}
_UART = {"id": "io.uart",  "name": "UART", "category": "io"}
_ROM  = {"id": "mem.rom",  "name": "ROM",  "category": "mem"}
_HELLO_WORLD  = Path(__file__).parent / "test" / "hello_world.asm"
_RAM_SELFTEST = Path(__file__).parent / "test" / "ram_selftest.asm"

# A tiny program: LDI r1, 123 ; HALT  ->  after run r1 == 123.
_TINY = "LDI r1, 123\nHALT\n"

# ROM placed at 0x0000 (size 0x100), RAM shrunk to 0x0200-0xFFFF so nothing overlaps.
# A factory (fresh nested dicts each call) avoids any shared-state surprises.
def _rom_override():
    return {
        "node_0004": {"mode": "manual", "base": 0x0000, "size": 0x0100},
        "node_0002": {"mode": "manual", "base": 0x0200, "size": 0xFE00},
    }


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


# ---------------------------------------------------------------------------
# project / persistence
# ---------------------------------------------------------------------------

def test_default_program_target_is_ram(tmp_path):
    win, _ = _win(tmp_path)
    assert win.program_target() == "ram"


def test_normalize_program_target():
    assert MainWin._normalize_program_target("ram") == "ram"
    assert MainWin._normalize_program_target("rom") == "rom"
    assert MainWin._normalize_program_target("nonsense") == "ram"
    assert MainWin._normalize_program_target(None) == "ram"
    assert MainWin._normalize_program_target(123) == "ram"


def test_missing_program_target_is_ram(tmp_path):
    # A system.json without program_target (old project) loads as RAM.
    _, root = _win(tmp_path)
    _, system = load_project(root)
    assert "program_target" not in system            # create_project writes none
    assert MainWin._normalize_program_target(system.get("program_target")) == "ram"


def test_program_target_persisted_to_system_json(tmp_path):
    win, root = _win(tmp_path)
    win.set_program_target("rom")
    win._persist_system()
    _, system = load_project(root)
    assert system["program_target"] == "rom"


def test_program_target_round_trip(tmp_path):
    win, root = _win(tmp_path)
    win.set_program_target("rom")            # set_program_target persists itself
    _, system = load_project(root)
    # Re-loading applies the same normalisation the Open flow uses.
    assert win._normalize_program_target(system.get("program_target")) == "rom"


def test_invalid_program_target_in_system_falls_back(tmp_path):
    _, root = _win(tmp_path)
    _, system = load_project(root)
    system["program_target"] = "garbage"
    save_system(root, system)
    _, system2 = load_project(root)
    assert MainWin._normalize_program_target(system2.get("program_target")) == "ram"


def test_set_invalid_target_falls_back_to_ram(tmp_path):
    win, _ = _win(tmp_path)
    win.set_program_target("rom")
    win.set_program_target("weird")
    assert win.program_target() == "ram"


# ---------------------------------------------------------------------------
# RAM target compatibility (default)
# ---------------------------------------------------------------------------

def test_ram_target_hello_world(tmp_path):
    win, root = _win(tmp_path)
    _wire_with_rom(win)
    _assign(win, root, _HELLO_WORLD.read_text(encoding="utf-8"), "hello_world.asm")
    assert win.program_target() == "ram"
    win.write_program()
    assert win._runtime.loaded is True
    assert any(win._sim_ram.dump())                  # program is in RAM
    assert win._sim_cpu.pc() == 0x0000               # layout reset PC
    win._do_run()
    assert "Hello World !" in win._sim_uart.output_text()


def test_ram_target_selftest(tmp_path):
    win, root = _win(tmp_path)
    _wire_plain(win)
    _assign(win, root, _RAM_SELFTEST.read_text(encoding="utf-8"), "ram_selftest.asm")
    win.write_program()
    win._do_run()
    assert "PASS" in win._sim_uart.output_text()


def test_legacy_mode_default_ram():
    win = MainWin()
    assert win.program_target() == "ram"
    assert win._runtime.address_map["mode"] == "legacy"


def test_ram_target_reset_pc_is_layout(tmp_path):
    # Even with a placed ROM, a RAM target keeps the layout reset PC (0x0000) and
    # loads into RAM, not ROM.
    win, root = _win(tmp_path)
    _wire_with_rom(win)
    win.apply_address_map_overrides(_rom_override())
    _assign(win, root, _TINY, "tiny.asm")
    assert win.program_target() == "ram"
    win.write_program()
    assert win._sim_cpu.pc() == 0x0000
    assert any(win._sim_ram.dump())                  # RAM holds the program
    assert not any(win._sim_rom.dump())              # ROM untouched


# ---------------------------------------------------------------------------
# ROM target load
# ---------------------------------------------------------------------------

def test_rom_target_loads_into_rom(tmp_path):
    win, root = _win(tmp_path)
    _wire_with_rom(win)
    win.apply_address_map_overrides(_rom_override())
    win.set_program_target("rom")
    _assign(win, root, _TINY, "tiny.asm")
    assert win.write_program() is True
    # Program bytes landed in ROM via the loader, not the bus (LDI r1,123 ; HALT).
    assert win._sim_rom.dump()[:8] == bytes.fromhex("7b00010200000001")
    # Working RAM is cleared (ROM holds the program), runtime marked loaded.
    assert not any(win._sim_ram.dump())
    assert win._runtime.loaded is True


def test_rom_target_reset_pc_is_rom_base(tmp_path):
    win, root = _win(tmp_path)
    _wire_with_rom(win)
    win.apply_address_map_overrides(_rom_override())
    win.set_program_target("rom")
    _assign(win, root, _TINY, "tiny.asm")
    win.write_program()
    assert win._sim_rom.base == 0x0000
    assert win._sim_cpu.pc() == win._sim_rom.base    # reset PC == ROM base


def test_rom_target_fetch_and_execute(tmp_path):
    win, root = _win(tmp_path)
    _wire_with_rom(win)
    win.apply_address_map_overrides(_rom_override())
    win.set_program_target("rom")
    _assign(win, root, _TINY, "tiny.asm")
    win.write_program()
    win._do_run()                                    # CPU fetches from ROM base
    assert win._sim_cpu.halted() is True
    assert win._sim_cpu.regs()[1] == 123             # LDI r1, 123 executed from ROM


# ---------------------------------------------------------------------------
# ROM target error handling (no silent RAM fallback)
# ---------------------------------------------------------------------------

def test_rom_target_no_rom_device_errors(tmp_path):
    win, root = _win(tmp_path)
    _wire_plain(win)                                 # no ROM on canvas
    win.set_program_target("rom")
    _assign(win, root, _TINY, "tiny.asm")
    assert win.write_program() is False
    assert win._sim_rom is None
    assert not any(win._sim_ram.dump())              # NOT loaded into RAM
    assert win._runtime.loaded is False


def test_rom_target_unplaced_rom_errors(tmp_path):
    # circuit_compat ROM with no override -> unplaced (no runtime) -> error.
    win, root = _win(tmp_path)
    _wire_with_rom(win)
    win.set_program_target("rom")
    _assign(win, root, _TINY, "tiny.asm")
    assert win.write_program() is False
    assert win._sim_rom is None
    assert not any(win._sim_ram.dump())
    assert win._runtime.loaded is False


def test_apply_overlapping_rom_is_rejected(tmp_path):
    # The editor blocks overlapping overrides before apply; applying one anyway is
    # rejected at bus-attach time (BusError) -> the overlap never reaches a runtime.
    from core.sim import BusError
    win, _ = _win(tmp_path)
    _wire_with_rom(win)
    raised = False
    try:
        # ROM over 0x0000 while RAM (auto) still fills 64KB -> overlap.
        win.apply_address_map_overrides(
            {"node_0004": {"mode": "manual", "base": 0x0000, "size": 0x1000}})
    except BusError:
        raised = True
    assert raised


def test_rom_target_overlap_in_map_errors(tmp_path):
    # Defensive guard: if the live Address Map ever contains an overlap, ROM target
    # Write Program errors instead of loading (no RAM fallback).
    from asm.asm import assemble_ex
    win, _ = _win(tmp_path)
    _wire_with_rom(win)
    win.apply_address_map_overrides(_rom_override())
    win.set_program_target("rom")
    # Inject an overlapping range into the live map to exercise the loader's check.
    win._runtime.address_map["devices"].append({
        "kind": "ram", "device_id": "ghost", "base": 0x0000, "end": 0x00FF,
        "attach_ranges": [(0x0000, 0x00FF)],
    })
    binary, _amap = assemble_ex(_TINY)
    assert win._load_program_to_rom(binary) is False
    assert not any(win._sim_rom.dump())              # nothing loaded into ROM
    assert win._runtime.loaded is False


def test_rom_target_size_exceeded_errors(tmp_path):
    # Tiny ROM (4 bytes) cannot hold the 8-byte program -> error, no RAM fallback.
    win, root = _win(tmp_path)
    _wire_with_rom(win)
    win.apply_address_map_overrides({
        "node_0004": {"mode": "manual", "base": 0x0000, "size": 0x0004},
        "node_0002": {"mode": "manual", "base": 0x0200, "size": 0xFE00},
    })
    win.set_program_target("rom")
    _assign(win, root, _TINY, "tiny.asm")
    assert win.write_program() is False
    assert not any(win._sim_ram.dump())
    assert win._runtime.loaded is False


# ---------------------------------------------------------------------------
# status / UI
# ---------------------------------------------------------------------------

def test_program_target_status_strings(tmp_path):
    win, root = _win(tmp_path)
    _wire_with_rom(win)
    assert win._program_target_status() == "RAM"
    win.set_program_target("rom")                    # ROM unplaced (no override yet)
    assert win._program_target_status() == "ROM (unplaced)"
    win.apply_address_map_overrides(_rom_override())
    assert win._program_target_status() == "ROM @0x0000"


def test_run_status_shows_program_target(tmp_path):
    win, _ = _win(tmp_path)
    win._update_run_status()
    assert "Program Target: RAM" in win._run_status.status_text()
