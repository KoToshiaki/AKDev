# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""PATCH_VIRTUAL_CPU_STEP_TRACE_V05 — virtual runtime, 1-instruction step trace."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF

_app = QApplication.instance() or QApplication(sys.argv)

from asm.asm import assemble
from core.cpu import AK32Part
from core.dev import RamPart, UartPart
from core.runtime import VirtualCircuitRuntime, disasm
from core.sim import Bus
from ui.win import MainWin
from core.project import create_project

_CPU  = {"id": "cpu.ak32", "name": "AK32", "category": "cpu"}
_RAM  = {"id": "mem.ram",  "name": "RAM",  "category": "mem"}
_UART = {"id": "io.uart",  "name": "UART", "category": "io"}
_HELLO_WORLD = Path(__file__).parent / "test" / "hello_world.asm"
_HELLO = Path(__file__).parent.parent / "src" / "hello.asm"
_REL = "tests/test/hello_world.asm"

_HI_SRC = """\
LDI r2, 0x100
LDI r1, 72
OUT [r2], r1
LDI r1, 105
OUT [r2], r1
HALT
"""


# ---------------------------------------------------------------------------
# standalone runtime (no GUI)
# ---------------------------------------------------------------------------

def _fresh_runtime():
    bus  = Bus()
    ram  = RamPart("ram", "RAM", 0x100, 0)
    uart = UartPart("uart", "UART", 0x100)
    cpu  = AK32Part("cpu", "CPU", bus)
    bus.attach(ram, 0, 0x100)
    bus.attach(uart, 0x100, 8)
    return VirtualCircuitRuntime(bus, ram, uart, cpu)


def test_disasm_covers_isa():
    assert disasm(0x00000000) == "NOP"
    assert disasm(0x01000000) == "HALT"
    assert disasm(0x02020100) == "LDI r2, 0x100"
    assert disasm(0x03020100) == "OUT [r2], r1"
    assert disasm(0xFF000000).startswith("DW ")


def test_load_program_marks_loaded():
    rt = _fresh_runtime()
    assert rt.loaded is False
    rt.load_program(assemble(_HI_SRC), source_name="hi.asm")
    assert rt.loaded is True
    assert rt.loaded_program["source_name"] == "hi.asm"
    assert rt.step_count == 0


def test_step_advances_pc_and_traces():
    rt = _fresh_runtime()
    rt.load_program(assemble(_HI_SRC))
    trace = rt.step()                       # LDI r2, 0x100
    assert trace["pc_before"] == 0x0000
    assert trace["pc_after"] == 0x0004
    assert trace["instruction"] == "LDI r2, 0x100"
    assert trace["raw"] is not None
    assert rt.step_count == 1


def test_ldi_step_reports_register_change():
    rt = _fresh_runtime()
    rt.load_program(assemble(_HI_SRC))
    trace = rt.step()                       # LDI r2, 0x100
    assert "r2" in trace["register_changes"]
    before, after = trace["register_changes"]["r2"]
    assert before == "0x00000000"
    assert after == "0x00000100"


def test_out_step_reports_uart_io():
    rt = _fresh_runtime()
    rt.load_program(assemble(_HI_SRC))
    rt.step()   # LDI r2
    rt.step()   # LDI r1, 72
    trace = rt.step()   # OUT [r2], r1 -> 'H'
    assert trace["instruction"] == "OUT [r2], r1"
    assert trace["uart"] == "H"
    assert len(trace["io"]) == 1
    io = trace["io"][0]
    assert io["type"] == "write"
    assert io["device"] == "UART"
    assert io["addr"] == "0x0100"
    assert io["value"] == "0x48"
    assert trace["memory"] == []            # fetch excluded


def test_uart_grows_one_char_per_out():
    rt = _fresh_runtime()
    rt.load_program(assemble(_HI_SRC))
    rt.step(); rt.step(); rt.step()         # -> 'H'
    assert rt.uart_text() == "H"
    rt.step(); rt.step()                     # LDI r1,105 ; OUT -> 'i'
    assert rt.uart_text() == "Hi"


def test_run_is_repeated_step_hello_world():
    rt = _fresh_runtime()
    rt.load_program(assemble(_HELLO_WORLD.read_text(encoding="utf-8")))
    traces = rt.run()
    assert "Hello World !" in rt.uart_text()
    assert traces[-1]["halted"] is True
    assert len(rt.trace_history) == len(traces)


def test_step_after_halt_is_safe():
    rt = _fresh_runtime()
    rt.load_program(assemble(_HI_SRC))
    rt.run()
    assert rt.cpu.halted()
    count_before = rt.step_count
    trace = rt.step()                        # already halted
    assert trace["halted"] is True
    assert rt.step_count == count_before     # no advance


def test_reset_clears_trace_history():
    rt = _fresh_runtime()
    rt.load_program(assemble(_HI_SRC))
    rt.run()
    assert rt.trace_history
    rt.reset()
    assert rt.trace_history == []
    assert rt.step_count == 0
    assert not rt.cpu.halted()


def test_registers_and_memory_snapshot():
    rt = _fresh_runtime()
    binary = assemble(_HI_SRC)
    rt.load_program(binary)
    regs = rt.registers()
    assert regs["pc"] == 0x0000
    assert regs["halted"] is False
    assert len(regs["regs"]) == 16
    assert rt.memory_snapshot()[:len(binary)] == binary


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


def _assign_hello_world(win, root):
    # PATCH_VIRTUAL_CIRCUIT_RUNTIME_V05: a wired CPU+RAM+UART circuit is required.
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


def test_write_program_marks_runtime_loaded(tmp_path):
    win, root = _win(tmp_path)
    _assign_hello_world(win, root)
    assert win.write_program() is True
    assert win._runtime.loaded is True
    assert win._runtime.loaded_program["target_node_id"] == "node_0001"


def test_step_button_no_program_message(tmp_path):
    win, root = _win(tmp_path)
    win._do_step()
    assert "No program loaded. Use Write Program first." in win._log.toPlainText()


def test_step_button_advances_after_write(tmp_path):
    win, root = _win(tmp_path)
    _assign_hello_world(win, root)
    win.write_program()
    assert win._sim_cpu.pc() == 0x0000
    win._do_step()
    assert win._sim_cpu.pc() == 0x0004
    assert "[STEP 0001]" in win._log.toPlainText()


def test_step_button_logs_uart_for_out(tmp_path):
    win, root = _win(tmp_path)
    _assign_hello_world(win, root)
    win.write_program()
    win._do_step()   # LDI r2
    win._do_step()   # LDI r1, 'H'
    win._do_step()   # OUT -> 'H'
    log = win._log.toPlainText()
    assert "IO WRITE 0x0100" in log
    assert "UART 'H'" in log
    assert win._uart_console.toPlainText() == "H"


def test_run_button_outputs_hello_world(tmp_path):
    win, root = _win(tmp_path)
    _assign_hello_world(win, root)
    win.write_program()
    win._do_run()
    assert "Hello World !" in win._sim_uart.output_text()
    assert "Run finished:" in win._log.toPlainText()


def test_run_button_halted_message_in_log(tmp_path):
    win, root = _win(tmp_path)
    _assign_hello_world(win, root)
    win.write_program()
    win._do_run()
    assert "halted=True" in win._log.toPlainText()


def test_step_after_halt_logs_message(tmp_path):
    win, root = _win(tmp_path)
    _assign_hello_world(win, root)
    win.write_program()
    win._do_run()
    assert win._sim_cpu.halted()
    pc_before = win._sim_cpu.pc()
    win._do_step()
    assert win._sim_cpu.pc() == pc_before
    assert "CPU is halted" in win._log.toPlainText()


def test_panels_updated_after_step(tmp_path):
    win, root = _win(tmp_path)
    _assign_hello_world(win, root)
    win.write_program()
    win._do_step()   # LDI r2, 0x100
    # Register View row 0 = pc, row 1 = cycle
    assert win._reg_table.item(0, 1).text() == "0x0004"
    assert win._reg_table.item(1, 1).text() == "1"


def test_run_then_reset_clears_state(tmp_path):
    win, root = _win(tmp_path)
    _assign_hello_world(win, root)
    win.write_program()
    win._do_run()
    win._do_reset()
    assert win._sim_cycle == 0
    assert not win._sim_cpu.halted()
    assert win._uart_console.toPlainText() == ""
    assert win._runtime.trace_history == []


# ---------------------------------------------------------------------------
# regression
# ---------------------------------------------------------------------------

def test_existing_build_run_still_works(tmp_path):
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
