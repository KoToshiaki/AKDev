# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""PATCH_CPU_RAM_VALIDATION_V07 — CPU can ST/LD to the connected RAM (Canvas circuit)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF

_app = QApplication.instance() or QApplication(sys.argv)

from ui.win import MainWin
from core.project import create_project

_CPU  = {"id": "cpu.ak32", "name": "AK32", "category": "cpu"}
_RAM  = {"id": "mem.ram",  "name": "RAM",  "category": "mem"}
_UART = {"id": "io.uart",  "name": "UART", "category": "io"}

_REPO       = Path(__file__).parent.parent
_RAM_SELFTEST = Path(__file__).parent / "test" / "ram_selftest.asm"
_FIB        = _REPO / "src" / "fib.asm"
_HELLO      = _REPO / "src" / "hello.asm"

_SELFTEST_ADDR = 0x0200
_SELFTEST_VALUE = 0xABCD


def _win(tmp_path):
    root = tmp_path / "proj"
    create_project(str(root), "proj")
    win = MainWin()
    win._project_root = root
    win._editor_tabs.set_project_root(root)
    return win, root


def _wire_full(win):
    win._canvas.add_part_at(_CPU,  QPointF(0.0, 0.0))
    win._canvas.add_part_at(_RAM,  QPointF(200.0, 0.0))
    win._canvas.add_part_at(_UART, QPointF(400.0, 0.0))
    win._canvas.add_connection("node_0001", "bus", "node_0002", "bus")
    win._canvas.add_connection("node_0001", "bus", "node_0003", "bus")


def _assign(win, root, src_path, name):
    """Copy *src_path* into the project's tests/test/ and assign it to the CPU node."""
    dst = root / "tests" / "test"
    dst.mkdir(parents=True, exist_ok=True)
    (dst / name).write_text(src_path.read_text(encoding="utf-8"), encoding="utf-8")
    rel = f"tests/test/{name}"
    win._canvas.set_node_source("node_0001", "asm", rel)
    return rel


def _ram_word(win, addr):
    dump = win._runtime.memory_snapshot()
    return int.from_bytes(dump[addr:addr + 4], "little")


def _dev(amap, kind):
    return next(d for d in amap["devices"] if d["kind"] == kind)


def _in_ranges(addr, ranges):
    return any(lo <= addr <= hi for lo, hi in ranges)


# ---------------------------------------------------------------------------
# RAM selftest — ST / LD verified on the connected RAM
# ---------------------------------------------------------------------------

def test_ram_selftest_write_run_pass(tmp_path):
    win, root = _win(tmp_path)
    _wire_full(win)
    _assign(win, root, _RAM_SELFTEST, "ram_selftest.asm")
    assert win.write_program() is True
    win._do_run()
    assert "PASS" in win._sim_uart.output_text()
    assert "FAIL" not in win._sim_uart.output_text()


def test_ram_selftest_value_written(tmp_path):
    win, root = _win(tmp_path)
    _wire_full(win)
    _assign(win, root, _RAM_SELFTEST, "ram_selftest.asm")
    win.write_program()
    win._do_run()
    # the CPU's ST landed in the connected RAM at 0x0200
    assert _ram_word(win, _SELFTEST_ADDR) == _SELFTEST_VALUE


def test_ram_selftest_step_trace_has_mem_write_and_read(tmp_path):
    win, root = _win(tmp_path)
    _wire_full(win)
    _assign(win, root, _RAM_SELFTEST, "ram_selftest.asm")
    win.write_program()
    win._do_run()
    writes = [m for tr in win._runtime.trace_history for m in tr["memory"]
              if m["type"] == "write" and m["addr"] == "0x0200"]
    reads  = [m for tr in win._runtime.trace_history for m in tr["memory"]
              if m["type"] == "read" and m["addr"] == "0x0200"]
    assert writes, "expected a memory WRITE to 0x0200 in the step trace"
    assert reads,  "expected a memory READ from 0x0200 in the step trace"
    assert writes[0]["value"] == "0x0000abcd"


# ---------------------------------------------------------------------------
# Address Map integration
# ---------------------------------------------------------------------------

def test_selftest_addr_in_ram_not_uart(tmp_path):
    win, root = _win(tmp_path)
    _wire_full(win)
    _assign(win, root, _RAM_SELFTEST, "ram_selftest.asm")
    win.write_program()
    amap = win._runtime.address_map
    ram  = _dev(amap, "ram")
    uart = _dev(amap, "uart")
    assert _in_ranges(_SELFTEST_ADDR, ram["attach_ranges"])
    assert not _in_ranges(_SELFTEST_ADDR, uart["attach_ranges"])
    # the selftest address also sits within the RAM logical range
    assert ram["base"] <= _SELFTEST_ADDR <= ram["end"]


def test_uart_window_still_functional(tmp_path):
    win, root = _win(tmp_path)
    _wire_full(win)
    _assign(win, root, _RAM_SELFTEST, "ram_selftest.asm")
    win.write_program()
    win._sim_bus.write(0x0100, ord("Z"))     # 0x0100 routes to UART, not RAM
    assert "Z" in win._sim_uart.output_text()
    assert _ram_word(win, 0x0100) == 0        # RAM array at that offset untouched


# ---------------------------------------------------------------------------
# Fibonacci on the Canvas-derived runtime
# ---------------------------------------------------------------------------

def test_fibonacci_on_circuit_runtime(tmp_path):
    win, root = _win(tmp_path)
    _wire_full(win)
    _assign(win, root, _FIB, "fib.asm")
    assert win.write_program() is True
    win._do_run()
    vals = [_ram_word(win, 0x0040 + 4 * i) for i in range(8)]
    assert vals == [0, 1, 1, 2, 3, 5, 8, 13]


# ---------------------------------------------------------------------------
# legacy mode is unaffected
# ---------------------------------------------------------------------------

def test_legacy_build_run_hi(tmp_path):
    win, root = _win(tmp_path)
    win._editor_tabs.open_tab(_CPU, "node_0001", "asm", "hello.asm")
    from PySide6.QtWidgets import QTextEdit
    editor = win._editor_tabs.currentWidget()
    assert isinstance(editor, QTextEdit)
    editor.setPlainText(_HELLO.read_text(encoding="utf-8"))
    win._build()
    win._do_run()
    assert "Hi" in win._sim_uart.output_text()
