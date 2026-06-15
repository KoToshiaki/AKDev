# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""PATCH_VIRTUAL_CIRCUIT_RUNTIME_V05 — Canvas-derived virtual circuit runtime."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF

_app = QApplication.instance() or QApplication(sys.argv)

from core.circuit import resolve_circuit
from asm.asm import assemble
from ui.win import MainWin
from core.project import create_project

_CPU  = {"id": "cpu.ak32", "name": "AK32", "category": "cpu"}
_RAM  = {"id": "mem.ram",  "name": "RAM",  "category": "mem"}
_UART = {"id": "io.uart",  "name": "UART", "category": "io"}
_HELLO_WORLD = Path(__file__).parent / "test" / "hello_world.asm"
_HELLO = Path(__file__).parent.parent / "src" / "hello.asm"
_REL = "tests/test/hello_world.asm"


# ---------------------------------------------------------------------------
# resolve_circuit
# ---------------------------------------------------------------------------

def _nodes(*specs):
    return [{"node_id": nid, "category": cat, "part_id": pid, "name": pid}
            for (nid, cat, pid) in specs]


def test_resolve_full_circuit_ok():
    nodes = _nodes(("n1", "cpu", "cpu.ak32"),
                   ("n2", "mem", "mem.ram"),
                   ("n3", "io",  "io.uart"))
    conns = [{"from_node": "n1", "to_node": "n2"},
             {"from_node": "n1", "to_node": "n3"}]
    plan = resolve_circuit(nodes, conns)
    assert plan["ok"] is True
    assert plan["cpu"] == "n1"
    assert plan["rams"] == ["n2"]
    assert plan["uarts"] == ["n3"]
    assert plan["cpu_present"] is True


def test_resolve_cpu_ram_unwired():
    nodes = _nodes(("n1", "cpu", "cpu.ak32"),
                   ("n2", "mem", "mem.ram"),
                   ("n3", "io",  "io.uart"))
    conns = [{"from_node": "n1", "to_node": "n3"}]   # RAM not wired
    plan = resolve_circuit(nodes, conns)
    assert plan["ok"] is False
    assert any("RAM" in s for s in plan["issues"])


def test_resolve_cpu_uart_unwired():
    nodes = _nodes(("n1", "cpu", "cpu.ak32"),
                   ("n2", "mem", "mem.ram"),
                   ("n3", "io",  "io.uart"))
    conns = [{"from_node": "n1", "to_node": "n2"}]   # UART not wired
    plan = resolve_circuit(nodes, conns)
    assert plan["ok"] is False
    assert any("UART" in s for s in plan["issues"])


def test_resolve_no_cpu():
    nodes = _nodes(("n2", "mem", "mem.ram"), ("n3", "io", "io.uart"))
    plan = resolve_circuit(nodes, [])
    assert plan["ok"] is False
    assert plan["cpu_present"] is False


def test_resolve_multiple_cpu_issue():
    nodes = _nodes(("n1", "cpu", "cpu.ak32"), ("n4", "cpu", "cpu.ak32"),
                   ("n2", "mem", "mem.ram"), ("n3", "io", "io.uart"))
    conns = [{"from_node": "n1", "to_node": "n2"},
             {"from_node": "n1", "to_node": "n3"}]
    plan = resolve_circuit(nodes, conns)
    assert plan["ok"] is False
    assert any("multiple CPU" in s for s in plan["issues"])


def test_resolve_no_ram_part():
    nodes = _nodes(("n1", "cpu", "cpu.ak32"), ("n3", "io", "io.uart"))
    conns = [{"from_node": "n1", "to_node": "n3"}]
    plan = resolve_circuit(nodes, conns)
    assert plan["ok"] is False
    assert any("no RAM" in s for s in plan["issues"])


# ---------------------------------------------------------------------------
# MainWin: Canvas-derived runtime
# ---------------------------------------------------------------------------

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


def _assign_hw(win, root):
    dst = root / "tests" / "test"
    dst.mkdir(parents=True, exist_ok=True)
    (dst / "hello_world.asm").write_text(
        _HELLO_WORLD.read_text(encoding="utf-8"), encoding="utf-8"
    )
    win._canvas.set_node_source("node_0001", "asm", _REL)


def test_write_program_builds_runtime_from_plan(tmp_path):
    win, root = _win(tmp_path)
    _wire_full(win)
    _assign_hw(win, root)
    assert win.write_program() is True
    assert win._runtime.plan is not None
    assert win._runtime.plan["cpu"] == "node_0001"
    assert win._runtime.plan["rams"] == ["node_0002"]
    assert win._runtime.plan["uarts"] == ["node_0003"]
    assert "Circuit built:" in win._log.toPlainText()


def test_write_then_run_outputs_hello_world(tmp_path):
    win, root = _win(tmp_path)
    _wire_full(win)
    _assign_hw(win, root)
    assert win.write_program() is True
    win._do_run()
    assert "Hello World !" in win._sim_uart.output_text()


def test_write_loads_into_connected_ram(tmp_path):
    win, root = _win(tmp_path)
    _wire_full(win)
    _assign_hw(win, root)
    win.write_program()
    binary = assemble(_HELLO_WORLD.read_text(encoding="utf-8"))
    assert win._runtime.memory_snapshot()[:len(binary)] == binary


def test_unconnected_blocks_write(tmp_path):
    win, root = _win(tmp_path)
    win._canvas.add_part_at(_CPU, QPointF(0.0, 0.0))   # lone CPU
    _assign_hw(win, root)
    assert win.write_program() is False
    assert "blocked" in win._log.toPlainText()


def test_unconnected_blocks_run(tmp_path):
    win, root = _win(tmp_path)
    win._canvas.add_part_at(_CPU, QPointF(0.0, 0.0))
    win._do_run()
    assert "Run blocked" in win._log.toPlainText()


def test_unconnected_blocks_step(tmp_path):
    win, root = _win(tmp_path)
    win._canvas.add_part_at(_CPU, QPointF(0.0, 0.0))
    win._do_step()
    assert "Step blocked" in win._log.toPlainText()


def test_missing_uart_blocks(tmp_path):
    win, root = _win(tmp_path)
    win._canvas.add_part_at(_CPU, QPointF(0.0, 0.0))
    win._canvas.add_part_at(_RAM, QPointF(200.0, 0.0))
    win._canvas.add_connection("node_0001", "bus", "node_0002", "bus")  # RAM only
    _assign_hw(win, root)
    assert win.write_program() is False
    assert "UART" in win._log.toPlainText()


# ---------------------------------------------------------------------------
# legacy mode (no CPU on canvas) is unaffected
# ---------------------------------------------------------------------------

def test_legacy_editor_build_run_still_works(tmp_path):
    win, root = _win(tmp_path)
    win._editor_tabs.open_tab(_CPU, "node_0001", "asm", "hello.asm")
    from PySide6.QtWidgets import QTextEdit
    editor = win._editor_tabs.currentWidget()
    assert isinstance(editor, QTextEdit)
    editor.setPlainText(_HELLO.read_text(encoding="utf-8"))
    win._build()
    win._do_run()
    assert "Hi" in win._sim_uart.output_text()


def test_legacy_direct_ram_run_no_canvas():
    win = MainWin()
    binary = assemble("HALT\n")
    win._sim_ram.load_bytes(binary)
    win._do_run()   # no canvas parts → legacy mode, not blocked
    assert "Run finished" in win._log.toPlainText() or "halted" in win._log.toPlainText().lower()


def test_hello_asm_headless_hi_preserved():
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
