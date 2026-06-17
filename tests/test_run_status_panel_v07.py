# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""PATCH_RUN_STATUS_PANEL_V07 — a read-only summary panel of the execution state."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF

_app = QApplication.instance() or QApplication(sys.argv)

from ui.win import MainWin
from ui.run_status import RunStatusPanel, render_status
from core.project import create_project

_CPU  = {"id": "cpu.ak32", "name": "AK32", "category": "cpu"}
_RAM  = {"id": "mem.ram",  "name": "RAM",  "category": "mem"}
_UART = {"id": "io.uart",  "name": "UART", "category": "io"}

_REPO        = Path(__file__).parent.parent
_HELLO_WORLD = Path(__file__).parent / "test" / "hello_world.asm"
_RAM_SELFTEST = Path(__file__).parent / "test" / "ram_selftest.asm"
_HELLO       = _REPO / "src" / "hello.asm"


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


def _wire_full(win):
    win._canvas.add_part_at(_CPU,  QPointF(0.0, 0.0))     # node_0001 CPU
    win._canvas.add_part_at(_RAM,  QPointF(200.0, 0.0))   # node_0002 RAM
    win._canvas.add_part_at(_UART, QPointF(400.0, 0.0))   # node_0003 UART
    win._canvas.add_connection("node_0001", "bus", "node_0002", "bus")
    win._canvas.add_connection("node_0001", "bus", "node_0003", "bus")


def _two_cpu(win, *, wire_second_to="both"):
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


def _assign(win, root, node_id, src, name):
    rel = _copy_asm(root, src, name)
    win._canvas.set_node_source(node_id, "asm", rel)
    return rel


# ---------------------------------------------------------------------------
# render_status unit (defensive)
# ---------------------------------------------------------------------------

def test_render_status_handles_empty():
    txt = render_status({})
    assert "Run Status" in txt
    assert "Mode: legacy" in txt


def test_render_status_handles_none_fields():
    txt = render_status({"mode": "circuit", "target_cpu": None,
                         "program": None, "last_trace": None})
    assert "Target CPU: None" in txt
    assert "Loaded: No" in txt


# ---------------------------------------------------------------------------
# panel creation
# ---------------------------------------------------------------------------

def test_panel_exists_on_mainwin():
    win = MainWin()
    assert isinstance(win._run_status, RunStatusPanel)


def test_initial_status_is_legacy():
    win = MainWin()
    txt = win._run_status.status_text()
    assert "Mode: legacy" in txt
    assert "Target CPU: None" in txt
    assert "sim_ram (256B)" in txt
    assert "0x0100" in txt


# ---------------------------------------------------------------------------
# Write Program
# ---------------------------------------------------------------------------

def test_write_program_shows_circuit(tmp_path):
    win, root = _win(tmp_path)
    _wire_full(win)
    _assign(win, root, "node_0001", _HELLO_WORLD, "hello_world.asm")
    assert win.write_program() is True
    txt = win._run_status.status_text()
    assert "Mode: circuit" in txt
    assert "Target CPU: node_0001" in txt
    assert "node_0002" in txt           # connected RAM
    assert "node_0003" in txt           # connected UART
    assert "hello_world.asm" in txt     # loaded path
    assert "Loaded: Yes" in txt
    assert "Address Map" in txt


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

def test_run_updates_runtime_and_uart(tmp_path):
    win, root = _win(tmp_path)
    _wire_full(win)
    _assign(win, root, "node_0001", _HELLO_WORLD, "hello_world.asm")
    win.write_program()
    win._do_run()
    txt = win._run_status.status_text()
    assert "Hello World !" in txt
    assert "PC:" in txt
    assert "Step count: 0" not in txt   # something ran


def test_run_selftest_pass_shown(tmp_path):
    win, root = _win(tmp_path)
    _wire_full(win)
    _assign(win, root, "node_0001", _RAM_SELFTEST, "ram_selftest.asm")
    win.write_program()
    win._do_run()
    txt = win._run_status.status_text()
    assert "PASS" in txt


# ---------------------------------------------------------------------------
# Step
# ---------------------------------------------------------------------------

def test_step_shows_instruction_and_trace(tmp_path):
    win, root = _win(tmp_path)
    _wire_full(win)
    _assign(win, root, "node_0001", _HELLO_WORLD, "hello_world.asm")
    win.write_program()
    win._do_step()
    txt = win._run_status.status_text()
    assert "Last instruction:" in txt
    assert "PC before -> after:" in txt
    assert "Trace summary" in txt
    assert "REG r2:" in txt              # first instr LDI r2, 0x100 changes r2


# ---------------------------------------------------------------------------
# Reset
# ---------------------------------------------------------------------------

def test_reset_returns_to_initial(tmp_path):
    win, root = _win(tmp_path)
    _wire_full(win)
    _assign(win, root, "node_0001", _HELLO_WORLD, "hello_world.asm")
    win.write_program()
    win._do_run()
    win._do_reset()
    txt = win._run_status.status_text()
    assert "PC: 0x0000" in txt
    assert "Cycle: 0" in txt
    assert "Step count: 0" in txt
    assert "UART output: (none)" in txt


# ---------------------------------------------------------------------------
# Target CPU selection integration
# ---------------------------------------------------------------------------

def test_multi_cpu_selected_target_shown(tmp_path):
    win, root = _win(tmp_path)
    _two_cpu(win, wire_second_to="both")
    _assign(win, root, "node_0004", _HELLO_WORLD, "hello_world.asm")
    _select(win, "node_0004")
    win.write_program()
    txt = win._run_status.status_text()
    assert "Mode: circuit" in txt
    assert "Target CPU: node_0004" in txt


def test_ambiguous_does_not_crash(tmp_path):
    win, root = _win(tmp_path)
    _two_cpu(win, wire_second_to="both")
    _select(win, None)
    win._update_run_status()
    txt = win._run_status.status_text()
    assert "Mode: circuit" in txt
    assert "Target CPU: None" in txt
    assert "multiple CPU" in txt


def test_selected_cpu_unconnected_does_not_crash(tmp_path):
    win, root = _win(tmp_path)
    _two_cpu(win, wire_second_to="none")   # node_0004 dangling
    _select(win, "node_0004")
    win._update_run_status()
    txt = win._run_status.status_text()
    assert "Target CPU: node_0004" in txt
    assert "has no connected RAM" in txt


# ---------------------------------------------------------------------------
# legacy mode unaffected
# ---------------------------------------------------------------------------

def test_legacy_build_run_hi_with_panel(tmp_path):
    win, root = _win(tmp_path)
    win._editor_tabs.open_tab(_CPU, "node_0001", "asm", "hello.asm")
    from PySide6.QtWidgets import QTextEdit
    editor = win._editor_tabs.currentWidget()
    assert isinstance(editor, QTextEdit)
    editor.setPlainText(_HELLO.read_text(encoding="utf-8"))
    win._build()
    win._do_run()
    assert "Hi" in win._sim_uart.output_text()
    txt = win._run_status.status_text()
    assert "Mode: legacy" in txt
    assert "Hi" in txt
