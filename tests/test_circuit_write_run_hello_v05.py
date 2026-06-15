# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""PATCH_CIRCUIT_WRITE_RUN_HELLO_V05 — write assigned program to circuit, run hello world."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF

_app = QApplication.instance() or QApplication(sys.argv)

from asm.asm import assemble
from ui.prop import PropPanel
from ui.win import MainWin
from core.project import create_project

_CPU  = {"id": "cpu.ak32", "name": "AK32", "category": "cpu"}
_RAM  = {"id": "mem.ram",  "name": "RAM",  "category": "mem"}
_UART = {"id": "io.uart",  "name": "UART", "category": "io"}
_HELLO_WORLD = Path(__file__).parent / "test" / "hello_world.asm"
_HELLO = Path(__file__).parent.parent / "src" / "hello.asm"
_REL = "tests/test/hello_world.asm"


# ---------------------------------------------------------------------------
# the test ASM itself
# ---------------------------------------------------------------------------

def test_hello_world_asm_exists():
    assert _HELLO_WORLD.exists()
    assert _HELLO_WORLD.read_text(encoding="utf-8").strip()


def test_hello_world_asm_assembles():
    binary = assemble(_HELLO_WORLD.read_text(encoding="utf-8"))
    assert len(binary) > 0
    assert len(binary) % 4 == 0


# ---------------------------------------------------------------------------
# MainWin write_program → run
# ---------------------------------------------------------------------------

def _win(tmp_path):
    root = tmp_path / "proj"
    create_project(str(root), "proj")
    win = MainWin()
    win._project_root = root
    win._editor_tabs.set_project_root(root)
    return win, root


def _assign_hello_world(win, root):
    """Build a full CPU+RAM+UART circuit and assign hello_world.asm to the CPU.

    PATCH_VIRTUAL_CIRCUIT_RUNTIME_V05: execution now requires a wired circuit, so
    the test places + connects CPU↔RAM and CPU↔UART before Write Program.
    """
    win._canvas.add_part_at(_CPU,  QPointF(0.0, 0.0))     # node_0001 (CPU)
    win._canvas.add_part_at(_RAM,  QPointF(200.0, 0.0))   # node_0002 (RAM)
    win._canvas.add_part_at(_UART, QPointF(400.0, 0.0))   # node_0003 (UART)
    win._canvas.add_connection("node_0001", "bus", "node_0002", "bus")
    win._canvas.add_connection("node_0001", "bus", "node_0003", "bus")
    dst = root / "tests" / "test"
    dst.mkdir(parents=True, exist_ok=True)
    (dst / "hello_world.asm").write_text(
        _HELLO_WORLD.read_text(encoding="utf-8"), encoding="utf-8"
    )
    win._canvas.set_node_source("node_0001", "asm", _REL)


def test_assign_source_to_cpu(tmp_path):
    win, root = _win(tmp_path)
    _assign_hello_world(win, root)
    assert win._canvas.node_source("node_0001", "asm") == _REL


def test_write_program_loads_circuit(tmp_path):
    win, root = _win(tmp_path)
    _assign_hello_world(win, root)
    assert win.write_program() is True
    lp = win.loaded_program()
    assert lp is not None
    assert lp["source_type"] == "asm"
    assert lp["path"] == _REL
    assert lp["target_node_id"] == "node_0001"
    assert lp["status"] == "loaded"


def test_write_program_then_run_outputs_hello_world(tmp_path):
    win, root = _win(tmp_path)
    _assign_hello_world(win, root)
    assert win.write_program() is True
    win._do_run()
    assert "Hello World !" in win._sim_uart.output_text()


def test_write_program_log_message(tmp_path):
    win, root = _win(tmp_path)
    _assign_hello_world(win, root)
    win.write_program()
    log = win._log.toPlainText()
    assert "Program written to circuit: node_0001 <-" in log
    assert _REL in log


def _wire_only(win):
    """Place + wire CPU+RAM+UART without assigning a program (circuit is valid)."""
    win._canvas.add_part_at(_CPU,  QPointF(0.0, 0.0))
    win._canvas.add_part_at(_RAM,  QPointF(200.0, 0.0))
    win._canvas.add_part_at(_UART, QPointF(400.0, 0.0))
    win._canvas.add_connection("node_0001", "bus", "node_0002", "bus")
    win._canvas.add_connection("node_0001", "bus", "node_0003", "bus")


def test_write_program_no_source(tmp_path):
    win, root = _win(tmp_path)
    _wire_only(win)                                    # wired, but no source assigned
    assert win.write_program() is False
    assert "No ASM source assigned" in win._log.toPlainText()


def test_write_program_missing_path(tmp_path):
    win, root = _win(tmp_path)
    _wire_only(win)
    win._canvas.set_node_source("node_0001", "asm", "tests/test/nope.asm")
    assert win.write_program() is False
    assert "Program source not found" in win._log.toPlainText()


def test_write_program_blocked_when_unconnected(tmp_path):
    """Circuit-mode: a lone CPU (no RAM/UART wired) blocks Write Program."""
    win, root = _win(tmp_path)
    win._canvas.add_part_at(_CPU, QPointF(0.0, 0.0))   # no RAM/UART/wires
    assert win.write_program() is False
    assert "blocked" in win._log.toPlainText()


def test_properties_show_loaded_state(tmp_path):
    win, root = _win(tmp_path)
    _assign_hello_world(win, root)
    win.write_program()
    win._refresh_node_properties("node_0001")
    txt = win._prop_panel._loaded_lbl.text()
    assert "Loaded: Yes" in txt
    assert "node_0001" in txt
    assert "hello_world.asm" in txt


def test_properties_loaded_no_by_default(tmp_path):
    p = PropPanel()
    p.show_part(_CPU, "node_0001", {"asm": _REL})
    assert "Loaded: No" in p._loaded_lbl.text()


# ---------------------------------------------------------------------------
# regression: existing build / run paths intact
# ---------------------------------------------------------------------------

def test_existing_build_run_still_works(tmp_path):
    """No assigned source: editor-tab Build → Run still works (UART Hi)."""
    win, root = _win(tmp_path)
    win._editor_tabs.open_tab(_CPU, "node_0001", "asm", "hello.asm")
    from PySide6.QtWidgets import QTextEdit
    editor = win._editor_tabs.currentWidget()
    assert isinstance(editor, QTextEdit)
    editor.setPlainText(_HELLO.read_text(encoding="utf-8"))
    win._build()
    win._do_run()
    assert "Hi" in win._sim_uart.output_text()


def test_hello_asm_headless_hi_preserved():
    """The classic hello.asm path still assembles + runs to 'Hi'."""
    from core.sim import Bus
    from core.dev import RamPart, UartPart
    from core.cpu import AK32Part
    binary = assemble(_HELLO.read_text(encoding="utf-8"))
    ram = RamPart("ram", "RAM", 0x100, 0)
    uart = UartPart("uart", "UART", 0x100)
    bus = Bus()
    bus.attach(ram, 0, 0x100)
    bus.attach(uart, 0x100, 8)
    ram.load_bytes(binary)
    cpu = AK32Part("cpu", "CPU", bus)
    for _ in range(1000):
        cpu.tick()
        if cpu.halted():
            break
    assert "Hi" in uart.output_text()
