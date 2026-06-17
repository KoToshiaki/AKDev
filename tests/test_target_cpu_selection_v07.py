# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""PATCH_TARGET_CPU_SELECTION_V07 — pick the selected CPU as the execution target."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

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

_REPO        = Path(__file__).parent.parent
_HELLO_WORLD = Path(__file__).parent / "test" / "hello_world.asm"
_RAM_SELFTEST = Path(__file__).parent / "test" / "ram_selftest.asm"
_HELLO       = _REPO / "src" / "hello.asm"


# ---------------------------------------------------------------------------
# resolve_circuit unit tests (target_cpu)
# ---------------------------------------------------------------------------

def _nodes(*specs):
    return [{"node_id": nid, "category": cat, "part_id": pid, "name": pid}
            for (nid, cat, pid) in specs]


def test_single_cpu_target_equals_cpu():
    nodes = _nodes(("n1", "cpu", "cpu.ak32"),
                   ("n2", "mem", "mem.ram"),
                   ("n3", "io",  "io.uart"))
    conns = [{"from_node": "n1", "to_node": "n2"},
             {"from_node": "n1", "to_node": "n3"}]
    plan = resolve_circuit(nodes, conns)
    assert plan["ok"] is True
    assert plan["cpu"] == "n1"
    assert plan["target_cpu"] == "n1"


def test_single_cpu_ignores_selection():
    nodes = _nodes(("n1", "cpu", "cpu.ak32"),
                   ("n2", "mem", "mem.ram"),
                   ("n3", "io",  "io.uart"))
    conns = [{"from_node": "n1", "to_node": "n2"},
             {"from_node": "n1", "to_node": "n3"}]
    # selecting a non-CPU node does not change the (single) target CPU
    plan = resolve_circuit(nodes, conns, target_cpu_id="n2")
    assert plan["ok"] is True
    assert plan["target_cpu"] == "n1"


def test_multiple_cpu_selected_is_target():
    nodes = _nodes(("n1", "cpu", "cpu.ak32"), ("n4", "cpu", "cpu.ak32"),
                   ("n2", "mem", "mem.ram"),  ("n3", "io", "io.uart"))
    conns = [{"from_node": "n4", "to_node": "n2"},
             {"from_node": "n4", "to_node": "n3"}]
    plan = resolve_circuit(nodes, conns, target_cpu_id="n4")
    assert plan["ok"] is True
    assert plan["target_cpu"] == "n4"
    assert plan["cpu"] == "n4"
    assert plan["rams"] == ["n2"]
    assert plan["uarts"] == ["n3"]


def test_multiple_cpu_no_selection_ambiguous():
    nodes = _nodes(("n1", "cpu", "cpu.ak32"), ("n4", "cpu", "cpu.ak32"),
                   ("n2", "mem", "mem.ram"),  ("n3", "io", "io.uart"))
    conns = [{"from_node": "n1", "to_node": "n2"},
             {"from_node": "n1", "to_node": "n3"}]
    plan = resolve_circuit(nodes, conns)
    assert plan["ok"] is False
    assert plan["target_cpu"] is None
    assert plan["cpu_present"] is True
    assert any("multiple CPU" in s for s in plan["issues"])
    assert any("Select one CPU" in s for s in plan["issues"])


def test_multiple_cpu_selected_unconnected_blocks():
    nodes = _nodes(("n1", "cpu", "cpu.ak32"), ("n4", "cpu", "cpu.ak32"),
                   ("n2", "mem", "mem.ram"),  ("n3", "io", "io.uart"))
    # n1 fully wired, n4 (selected) wired to nothing
    conns = [{"from_node": "n1", "to_node": "n2"},
             {"from_node": "n1", "to_node": "n3"}]
    plan = resolve_circuit(nodes, conns, target_cpu_id="n4")
    assert plan["ok"] is False
    assert plan["target_cpu"] == "n4"
    assert any("n4" in s and "RAM" in s for s in plan["issues"])
    assert any("n4" in s and "UART" in s for s in plan["issues"])


def test_nonselected_cpu_unconnected_does_not_block():
    nodes = _nodes(("n1", "cpu", "cpu.ak32"), ("n4", "cpu", "cpu.ak32"),
                   ("n2", "mem", "mem.ram"),  ("n3", "io", "io.uart"))
    # n1 (selected) fully wired, n4 dangling — n4 must not break n1's plan
    conns = [{"from_node": "n1", "to_node": "n2"},
             {"from_node": "n1", "to_node": "n3"}]
    plan = resolve_circuit(nodes, conns, target_cpu_id="n1")
    assert plan["ok"] is True
    assert plan["target_cpu"] == "n1"


# ---------------------------------------------------------------------------
# MainWin helpers
# ---------------------------------------------------------------------------

def _win(tmp_path):
    root = tmp_path / "proj"
    create_project(str(root), "proj")
    win = MainWin()
    win._project_root = root
    win._editor_tabs.set_project_root(root)
    return win, root


def _copy_asm(root, src, name):
    dst = root / "tests" / "test"
    dst.mkdir(parents=True, exist_ok=True)
    (dst / name).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    return f"tests/test/{name}"


def _select(win, node_id):
    win._canvas.scene().clearSelection()
    if node_id is not None:
        win._canvas.get_node(node_id).setSelected(True)


def _single_cpu(win):
    win._canvas.add_part_at(_CPU,  QPointF(0.0, 0.0))     # node_0001 CPU
    win._canvas.add_part_at(_RAM,  QPointF(200.0, 0.0))   # node_0002 RAM
    win._canvas.add_part_at(_UART, QPointF(400.0, 0.0))   # node_0003 UART
    win._canvas.add_connection("node_0001", "bus", "node_0002", "bus")
    win._canvas.add_connection("node_0001", "bus", "node_0003", "bus")


def _two_cpu(win, *, wire_second_to="both"):
    """node_0001 CPU (fully wired) + node_0004 CPU (wiring per wire_second_to).

    wire_second_to: "both" | "ram" | "uart" | "none".
    """
    win._canvas.add_part_at(_CPU,  QPointF(0.0, 0.0))     # node_0001 CPU
    win._canvas.add_part_at(_RAM,  QPointF(200.0, 0.0))   # node_0002 RAM
    win._canvas.add_part_at(_UART, QPointF(400.0, 0.0))   # node_0003 UART
    win._canvas.add_part_at(_CPU,  QPointF(0.0, 200.0))   # node_0004 CPU
    win._canvas.add_connection("node_0001", "bus", "node_0002", "bus")
    win._canvas.add_connection("node_0001", "bus", "node_0003", "bus")
    if wire_second_to in ("both", "ram"):
        win._canvas.add_connection("node_0004", "bus", "node_0002", "bus")
    if wire_second_to in ("both", "uart"):
        win._canvas.add_connection("node_0004", "bus", "node_0003", "bus")


# ---------------------------------------------------------------------------
# single CPU (unchanged behaviour)
# ---------------------------------------------------------------------------

def test_single_cpu_write_run_hello(tmp_path):
    win, root = _win(tmp_path)
    _single_cpu(win)
    rel = _copy_asm(root, _HELLO_WORLD, "hello_world.asm")
    win._canvas.set_node_source("node_0001", "asm", rel)
    assert win.write_program() is True
    win._do_run()
    assert "Hello World !" in win._sim_uart.output_text()
    assert win.loaded_program()["target_node_id"] == "node_0001"


# ---------------------------------------------------------------------------
# multiple CPU + selection
# ---------------------------------------------------------------------------

def test_multi_cpu_selected_runs(tmp_path):
    win, root = _win(tmp_path)
    _two_cpu(win, wire_second_to="both")
    rel = _copy_asm(root, _HELLO_WORLD, "hello_world.asm")
    win._canvas.set_node_source("node_0004", "asm", rel)
    _select(win, "node_0004")
    assert win.write_program() is True
    assert win.loaded_program()["target_node_id"] == "node_0004"
    win._do_run()
    assert "Hello World !" in win._sim_uart.output_text()
    assert "Target CPU: node_0004" in win._log.toPlainText()


def test_multi_cpu_nonselected_unconnected_still_runs(tmp_path):
    win, root = _win(tmp_path)
    _two_cpu(win, wire_second_to="none")   # node_0004 dangling
    rel = _copy_asm(root, _HELLO_WORLD, "hello_world.asm")
    win._canvas.set_node_source("node_0001", "asm", rel)
    _select(win, "node_0001")
    assert win.write_program() is True
    win._do_run()
    assert "Hello World !" in win._sim_uart.output_text()


def test_multi_cpu_uses_target_source(tmp_path):
    win, root = _win(tmp_path)
    _two_cpu(win, wire_second_to="both")
    hw  = _copy_asm(root, _HELLO_WORLD, "hello_world.asm")
    sft = _copy_asm(root, _RAM_SELFTEST, "ram_selftest.asm")
    win._canvas.set_node_source("node_0001", "asm", sft)   # non-target
    win._canvas.set_node_source("node_0004", "asm", hw)    # target
    _select(win, "node_0004")
    win.write_program()
    binary = assemble(_HELLO_WORLD.read_text(encoding="utf-8"))
    assert win._runtime.memory_snapshot()[:len(binary)] == binary
    win._do_run()
    assert "Hello World !" in win._sim_uart.output_text()


def test_multi_cpu_does_not_use_nonselected_source(tmp_path):
    win, root = _win(tmp_path)
    _two_cpu(win, wire_second_to="both")
    rel = _copy_asm(root, _HELLO_WORLD, "hello_world.asm")
    win._canvas.set_node_source("node_0001", "asm", rel)   # only the non-target CPU
    _select(win, "node_0004")                              # target has no source
    assert win.write_program() is False
    assert "No ASM source assigned to target CPU" in win._log.toPlainText()


# ---------------------------------------------------------------------------
# ambiguous (multiple CPU, none selected)
# ---------------------------------------------------------------------------

def test_multi_cpu_unselected_write_blocked(tmp_path):
    win, root = _win(tmp_path)
    _two_cpu(win, wire_second_to="both")
    rel = _copy_asm(root, _HELLO_WORLD, "hello_world.asm")
    win._canvas.set_node_source("node_0001", "asm", rel)
    _select(win, None)
    assert win.write_program() is False
    log = win._log.toPlainText()
    assert "multiple CPU" in log
    assert "Select one CPU" in log


def test_multi_cpu_unselected_run_blocked(tmp_path):
    win, root = _win(tmp_path)
    _two_cpu(win, wire_second_to="both")
    _select(win, None)
    win._do_run()
    assert "Run blocked" in win._log.toPlainText()
    assert "Select one CPU" in win._log.toPlainText()


def test_multi_cpu_unselected_step_blocked(tmp_path):
    win, root = _win(tmp_path)
    _two_cpu(win, wire_second_to="both")
    _select(win, None)
    win._do_step()
    assert "Step blocked" in win._log.toPlainText()
    assert "Select one CPU" in win._log.toPlainText()


# ---------------------------------------------------------------------------
# selected CPU unconnected (blocks even if another CPU is connected)
# ---------------------------------------------------------------------------

def test_selected_cpu_no_ram_blocks(tmp_path):
    win, root = _win(tmp_path)
    _two_cpu(win, wire_second_to="uart")   # node_0004 has UART but no RAM
    _select(win, "node_0004")
    win._do_run()
    log = win._log.toPlainText()
    assert "Run blocked" in log
    assert "node_0004" in log
    assert "has no connected RAM" in log


def test_selected_cpu_no_uart_blocks(tmp_path):
    win, root = _win(tmp_path)
    _two_cpu(win, wire_second_to="ram")    # node_0004 has RAM but no UART
    _select(win, "node_0004")
    win._do_run()
    log = win._log.toPlainText()
    assert "Run blocked" in log
    assert "node_0004" in log
    assert "has no connected UART" in log


def test_selected_cpu_unconnected_write_blocks_despite_other_cpu(tmp_path):
    win, root = _win(tmp_path)
    _two_cpu(win, wire_second_to="none")   # node_0001 fully wired, node_0004 dangling
    rel = _copy_asm(root, _HELLO_WORLD, "hello_world.asm")
    win._canvas.set_node_source("node_0004", "asm", rel)
    _select(win, "node_0004")
    assert win.write_program() is False
    assert "Write Program blocked" in win._log.toPlainText()


# ---------------------------------------------------------------------------
# legacy mode unaffected
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
