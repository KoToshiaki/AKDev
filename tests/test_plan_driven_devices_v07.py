# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""PATCH_PLAN_DRIVEN_DEVICES_V07 — Canvas plan builds the actual runtime devices."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF

_app = QApplication.instance() or QApplication(sys.argv)

from core.sim import BusError
from asm.asm import assemble
from ui.win import MainWin, _CIRCUIT_RAM_SIZE, _SIM_RAM_SIZE
from core.project import create_project

_CPU  = {"id": "cpu.ak32", "name": "AK32", "category": "cpu"}
_RAM  = {"id": "mem.ram",  "name": "RAM",  "category": "mem"}
_UART = {"id": "io.uart",  "name": "UART", "category": "io"}
_HELLO_WORLD = Path(__file__).parent / "test" / "hello_world.asm"
_HELLO = Path(__file__).parent.parent / "src" / "hello.asm"
_REL = "tests/test/hello_world.asm"


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


# ---------------------------------------------------------------------------
# plan-derived devices become the runtime's execution devices
# ---------------------------------------------------------------------------

def test_runtime_ram_is_plan_device(tmp_path):
    win, root = _win(tmp_path)
    _wire_full(win)
    _assign_hw(win, root)
    assert win.write_program() is True
    # the runtime executes on the same RAM/UART/CPU instances the win exposes
    assert win._runtime.ram is win._sim_ram
    assert win._runtime.uart is win._sim_uart
    assert win._runtime.cpu is win._sim_cpu


def test_circuit_ram_size_expanded(tmp_path):
    win, root = _win(tmp_path)
    _wire_full(win)
    _assign_hw(win, root)
    win.write_program()
    assert win._sim_ram.size == _CIRCUIT_RAM_SIZE
    assert win._sim_ram.size >= 0x10000


def test_plan_node_ids_recorded(tmp_path):
    win, root = _win(tmp_path)
    _wire_full(win)
    _assign_hw(win, root)
    win.write_program()
    assert win._sim_cpu_node  == "node_0001"
    assert win._sim_ram_node  == "node_0002"
    assert win._sim_uart_node == "node_0003"


def test_write_loads_into_connected_ram(tmp_path):
    win, root = _win(tmp_path)
    _wire_full(win)
    _assign_hw(win, root)
    win.write_program()
    binary = assemble(_HELLO_WORLD.read_text(encoding="utf-8"))
    assert win._runtime.memory_snapshot()[:len(binary)] == binary


def test_run_outputs_hello_world_on_connected_uart(tmp_path):
    win, root = _win(tmp_path)
    _wire_full(win)
    _assign_hw(win, root)
    win.write_program()
    win._do_run()
    assert "Hello World !" in win._sim_uart.output_text()


def test_expanded_ram_high_address_read_write(tmp_path):
    win, root = _win(tmp_path)
    _wire_full(win)
    _assign_hw(win, root)
    win.write_program()
    # a high address that the legacy 256-byte RAM could never reach
    win._sim_bus.write(0x2000, 0xDEADBEEF)
    assert win._sim_bus.read(0x2000) == 0xDEADBEEF


def test_uart_window_still_at_0x100(tmp_path):
    win, root = _win(tmp_path)
    _wire_full(win)
    _assign_hw(win, root)
    win.write_program()
    # 0x0100 routes to the UART (MMIO window), not RAM
    win._sim_bus.write(0x0100, ord("Z"))
    assert "Z" in win._sim_uart.output_text()


def test_step_trace_still_works(tmp_path):
    win, root = _win(tmp_path)
    _wire_full(win)
    _assign_hw(win, root)
    win.write_program()
    win._do_step()
    assert win._runtime.step_count == 1
    assert isinstance(win._runtime.last_trace, dict)
    assert "instruction" in win._runtime.last_trace


# ---------------------------------------------------------------------------
# legacy mode (no CPU on canvas) is unchanged
# ---------------------------------------------------------------------------

def test_legacy_ram_stays_small():
    win = MainWin()           # no canvas parts → legacy fixed circuit
    assert win._sim_ram.size == _SIM_RAM_SIZE
    assert win._sim_ram_node is None


def test_legacy_ram_rejects_high_address():
    win = MainWin()
    try:
        win._sim_bus.write(0x2000, 1)
        raised = False
    except BusError:
        raised = True
    assert raised is True


def test_legacy_editor_build_run_hi(tmp_path):
    win, root = _win(tmp_path)
    win._editor_tabs.open_tab(_CPU, "node_0001", "asm", "hello.asm")
    from PySide6.QtWidgets import QTextEdit
    editor = win._editor_tabs.currentWidget()
    assert isinstance(editor, QTextEdit)
    editor.setPlainText(_HELLO.read_text(encoding="utf-8"))
    win._build()
    win._do_run()
    assert "Hi" in win._sim_uart.output_text()


# ---------------------------------------------------------------------------
# unconnected circuit is still blocked
# ---------------------------------------------------------------------------

def test_unconnected_blocks_write(tmp_path):
    win, root = _win(tmp_path)
    win._canvas.add_part_at(_CPU, QPointF(0.0, 0.0))   # lone CPU
    _assign_hw(win, root)
    assert win.write_program() is False
    assert "blocked" in win._log.toPlainText()
