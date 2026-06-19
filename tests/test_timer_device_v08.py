# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""PATCH_TIMER_DEVICE_V08 — io.timer MMIO device + TimerPart deterministic tick.

Timer is a memory-mapped step counter (no wall clock, no interrupt): the runtime
advances it one tick per executed CPU instruction, so the value is reproducible.
Read with the existing LD, cleared with the existing ST (no new CPU instruction).
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
    make_device_spec, assign_mmio_bases, get_memory_layout,
)
from core.dev import TimerPart
from core.circuit import resolve_circuit, validate_address_map
from core.runtime import disasm
from ui.win import MainWin
from ui.lib import load_parts
from ui.run_status import render_status
from core.project import create_project

_CPU   = {"id": "cpu.ak32", "name": "AK32",  "category": "cpu"}
_RAM   = {"id": "mem.ram",  "name": "RAM",   "category": "mem"}
_UART  = {"id": "io.uart",  "name": "UART",  "category": "io"}
_INPUT = {"id": "io.input", "name": "INPUT", "category": "io"}
_TIMER = {"id": "io.timer", "name": "Timer", "category": "io"}
_HELLO_WORLD = Path(__file__).parent / "test" / "hello_world.asm"


def _nodes(*specs):
    return [{"node_id": nid, "category": cat, "part_id": pid, "name": pid}
            for (nid, cat, pid) in specs]


# ---------------------------------------------------------------------------
# part / library
# ---------------------------------------------------------------------------

def test_io_timer_in_library():
    cats, errors = load_parts()
    assert not errors, errors
    ids = {p["id"] for plist in cats.values() for p in plist}
    assert "io.timer" in ids
    part = next(p for plist in cats.values() for p in plist if p["id"] == "io.timer")
    assert part.get("schema_version") == 2
    bus = next(pt for pt in part["ports"] if pt["name"] == "bus")
    assert bus["role"] == "slave" and bus["direction"] == "inout"
    names = {pt["name"] for pt in part["ports"]}
    assert {"bus", "clk", "reset"} <= names


# ---------------------------------------------------------------------------
# device registry
# ---------------------------------------------------------------------------

def test_device_kind_and_role():
    assert device_kind({"id": "io.timer"}) == "timer"
    assert device_role("timer") == "mmio"
    assert is_addressable_kind("timer") is True
    assert is_runtime_backed_kind("timer") is True


def test_make_device_spec_timer():
    s = make_device_spec("n5", _TIMER, mode="circuit")
    assert s["kind"] == "timer"
    assert s["role"] == "mmio"
    assert s["addressable"] is True
    assert s["runtime_backed"] is True
    assert s["runtime_id"] == "sim_timer"
    assert s["label"] == "TIMER"


# ---------------------------------------------------------------------------
# Address Map placement
# ---------------------------------------------------------------------------

def test_mmio_bases_uart_input_timer():
    layout = get_memory_layout("circuit")
    specs = [
        make_device_spec("n1", _CPU,   layout=layout),
        make_device_spec("n2", _RAM,   layout=layout),
        make_device_spec("n3", _UART,  layout=layout),
        make_device_spec("n4", _INPUT, layout=layout),
        make_device_spec("n5", _TIMER, layout=layout),
    ]
    out = assign_mmio_bases(specs, layout=layout)
    by_kind = {s["kind"]: s for s in out}
    assert by_kind["uart"]["base"] == 0x0100
    assert by_kind["input"]["base"] == 0x0110
    assert by_kind["timer"]["base"] == 0x0120
    assert by_kind["timer"]["size"] == 0x08
    assert by_kind["timer"]["end"] == 0x0127


# ---------------------------------------------------------------------------
# resolve_circuit
# ---------------------------------------------------------------------------

def test_resolve_collects_timer():
    nodes = _nodes(("n1", "cpu", "cpu.ak32"), ("n2", "mem", "mem.ram"),
                   ("n3", "io", "io.uart"), ("n4", "io", "io.timer"))
    conns = [{"from_node": "n1", "to_node": n} for n in ("n2", "n3", "n4")]
    plan = resolve_circuit(nodes, conns)
    assert plan["ok"] is True
    assert plan["timers"] == ["n4"]
    kinds = {d["node_id"]: d["kind"] for d in plan["devices"]}
    assert kinds["n4"] == "timer"


def test_resolve_no_timer_is_unchanged():
    nodes = _nodes(("n1", "cpu", "cpu.ak32"), ("n2", "mem", "mem.ram"),
                   ("n3", "io", "io.uart"))
    conns = [{"from_node": "n1", "to_node": n} for n in ("n2", "n3")]
    plan = resolve_circuit(nodes, conns)
    assert plan["timers"] == []
    assert plan["ok"] is True            # Timer is not required


def test_unconnected_timer_not_collected():
    nodes = _nodes(("n1", "cpu", "cpu.ak32"), ("n2", "mem", "mem.ram"),
                   ("n3", "io", "io.uart"), ("n4", "io", "io.timer"))
    conns = [{"from_node": "n1", "to_node": n} for n in ("n2", "n3")]  # n4 dangling
    plan = resolve_circuit(nodes, conns)
    assert plan["timers"] == []
    assert plan["ok"] is True


# ---------------------------------------------------------------------------
# TimerPart unit
# ---------------------------------------------------------------------------

def test_timer_initial_zero():
    t = TimerPart("sim_timer", "TIMER", base=0x0120)
    assert t.read(0x0120) == 0
    assert t.read(0x0124) == 0


def test_timer_tick_increments():
    t = TimerPart("sim_timer", "TIMER", base=0x0120)
    for _ in range(5):
        t.tick()
    assert t.read(0x0120) == 5          # TICK
    assert t.read(0x0124) == 5          # DELTA (no clear yet)


def test_timer_clear_tick():
    t = TimerPart("sim_timer", "TIMER", base=0x0120)
    for _ in range(3):
        t.tick()
    t.write(0x0120, 0xDEAD)             # value ignored -> clear TICK + DELTA base
    assert t.read(0x0120) == 0
    assert t.read(0x0124) == 0


def test_timer_clear_delta_only():
    t = TimerPart("sim_timer", "TIMER", base=0x0120)
    for _ in range(4):
        t.tick()
    t.write(0x0124, 0)                  # clear DELTA base only
    assert t.read(0x0120) == 4          # TICK unchanged
    assert t.read(0x0124) == 0          # DELTA rebased
    t.tick()
    assert t.read(0x0120) == 5
    assert t.read(0x0124) == 1


def test_timer_reset():
    t = TimerPart("sim_timer", "TIMER", base=0x0120)
    for _ in range(7):
        t.tick()
    t.reset()
    assert t.read(0x0120) == 0 and t.read(0x0124) == 0


def test_timer_32bit_wrap():
    t = TimerPart("sim_timer", "TIMER", base=0x0000)
    t._tick = 0xFFFFFFFF
    t.tick()
    assert t.read(0x0000) == 0          # wraps to 0


def test_timer_out_of_range_read_zero():
    t = TimerPart("sim_timer", "TIMER", base=0x0120)
    assert t.read(0x0128) == 0          # defensive (outside the two registers)


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


def _wire_with_timer(win):
    # UART + Input + Timer so the MMIO running index puts Timer at 0x0120
    # (UART 0x0100 / Input 0x0110 / Timer 0x0120).
    win._canvas.add_part_at(_CPU,   QPointF(0.0, 0.0))     # node_0001
    win._canvas.add_part_at(_RAM,   QPointF(200.0, 0.0))   # node_0002
    win._canvas.add_part_at(_UART,  QPointF(400.0, 0.0))   # node_0003
    win._canvas.add_part_at(_INPUT, QPointF(600.0, 0.0))   # node_0004
    win._canvas.add_part_at(_TIMER, QPointF(800.0, 0.0))   # node_0005
    win._canvas.add_connection("node_0001", "bus", "node_0002", "bus")
    win._canvas.add_connection("node_0001", "bus", "node_0003", "bus")
    win._canvas.add_connection("node_0001", "bus", "node_0004", "bus")
    win._canvas.add_connection("node_0001", "bus", "node_0005", "bus")


def _wire_plain(win):
    win._canvas.add_part_at(_CPU,  QPointF(0.0, 0.0))
    win._canvas.add_part_at(_RAM,  QPointF(200.0, 0.0))
    win._canvas.add_part_at(_UART, QPointF(400.0, 0.0))
    win._canvas.add_connection("node_0001", "bus", "node_0002", "bus")
    win._canvas.add_connection("node_0001", "bus", "node_0003", "bus")


def test_timer_runtime_built_and_address_map(tmp_path):
    win, root = _win(tmp_path)
    _wire_with_timer(win)
    _assign(win, root, "NOP\nHALT\n", "nop.asm")
    assert win.write_program() is True
    assert win._sim_timer is not None
    assert win._sim_timer_node == "node_0005"
    assert win._sim_timer.id == "sim_timer"
    assert win._runtime.timer is win._sim_timer
    amap = win._runtime.address_map
    tmr = next(d for d in amap["devices"] if d["kind"] == "timer")
    assert tmr["base"] == 0x0120 and tmr["end"] == 0x0127
    assert tmr["device_id"] == "sim_timer"
    assert validate_address_map(amap) == []


def test_timer_tick_advances_with_steps(tmp_path):
    win, root = _win(tmp_path)
    _wire_with_timer(win)
    _assign(win, root, "NOP\nNOP\nNOP\nHALT\n", "nops.asm")
    win.write_program()
    assert win._sim_timer.tick_value() == 0      # reset on load
    win._runtime.step()
    win._runtime.step()
    win._runtime.step()
    assert win._sim_timer.tick_value() == 3       # one tick per executed step


def test_timer_reset_on_reload(tmp_path):
    win, root = _win(tmp_path)
    _wire_with_timer(win)
    _assign(win, root, "NOP\nNOP\nHALT\n", "nops.asm")
    win.write_program()
    win._runtime.step()
    win._runtime.step()
    assert win._sim_timer.tick_value() == 2
    win.write_program()                           # reload -> timer reset
    assert win._sim_timer.tick_value() == 0


def test_cpu_reads_timer_via_ld(tmp_path):
    win, root = _win(tmp_path)
    _wire_with_timer(win)
    # step0: LDI executes (tick->1). step1: LD reads timer (current tick == 1) -> r2.
    _assign(win, root, "LDI r1, 0x0120\nLD r2, [r1]\nHALT\n", "read_timer.asm")
    win.write_program()
    win._do_run()
    assert win._sim_cpu.regs()[2] == 1            # deterministic tick observed via LD


def test_cpu_clears_timer_via_st(tmp_path):
    win, root = _win(tmp_path)
    _wire_with_timer(win)
    # Read tick before clear into r2, ST-clear, then read after clear into r3.
    prog = (
        "NOP\nNOP\nNOP\nNOP\n"
        "LDI r1, 0x0120\n"
        "LD  r2, [r1]\n"     # r2 = tick before clear
        "ST  [r1], r0\n"     # clear tick
        "LD  r3, [r1]\n"     # r3 = tick after clear
        "HALT\n"
    )
    _assign(win, root, prog, "clear_timer.asm")
    win.write_program()
    win._do_run()
    r2 = win._sim_cpu.regs()[2]
    r3 = win._sim_cpu.regs()[3]
    assert r2 == 5                                # 4 NOP + LDI executed before read
    assert r3 == 1                                # cleared, then 1 step elapsed
    assert r3 < r2                                # ST clear took effect


# ---------------------------------------------------------------------------
# existing compatibility (no Timer device)
# ---------------------------------------------------------------------------

def test_no_timer_runtime_unchanged(tmp_path):
    win, root = _win(tmp_path)
    _wire_plain(win)
    _assign(win, root, _HELLO_WORLD.read_text(encoding="utf-8"), "hello_world.asm")
    win.write_program()
    assert win._sim_timer is None
    assert win._runtime.timer is None
    amap = win._runtime.address_map
    assert not any(d["kind"] == "timer" for d in amap["devices"])
    uart = next(d for d in amap["devices"] if d["kind"] == "uart")
    assert uart["base"] == 0x0100
    win._do_run()
    assert "Hello World !" in win._sim_uart.output_text()


def test_legacy_mode_has_no_timer():
    win = MainWin()
    assert win._sim_timer is None
    assert win._runtime.timer is None


# ---------------------------------------------------------------------------
# Run Status
# ---------------------------------------------------------------------------

def test_run_status_timer_none():
    assert "Timer: None" in render_status({"mode": "legacy"})


def test_run_status_timer_present():
    txt = render_status({"mode": "circuit",
                         "timer": {"tick": 42, "delta": 7, "base": 0x0120}})
    assert "Timer: tick=42 delta=7 @0x0120" in txt


def test_run_status_shows_timer_when_placed(tmp_path):
    win, root = _win(tmp_path)
    _wire_with_timer(win)
    _assign(win, root, "NOP\nHALT\n", "nop.asm")
    win.write_program()
    win._update_run_status()
    assert "Timer: tick=" in win._run_status.status_text()


# ---------------------------------------------------------------------------
# disasm unaffected (no new mnemonic)
# ---------------------------------------------------------------------------

def test_disasm_unknown_unchanged():
    assert disasm(0xFF000000) == "DW 0xff000000"
