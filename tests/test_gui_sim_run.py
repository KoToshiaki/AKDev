# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""Headless integration tests: Build -> Reset -> Run/Step via MainWin sim controls."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication

_app = QApplication.instance() or QApplication(sys.argv)

from asm.asm import assemble
from ui.win import MainWin

_HI_SRC = """\
LDI r2, 0x100
LDI r1, 72
OUT [r2], r1
LDI r1, 105
OUT [r2], r1
HALT
"""


def _load_hi(win: MainWin) -> None:
    """Assemble the Hi source and load it into win's simulator RAM."""
    binary = assemble(_HI_SRC)
    win._sim_ram.reset()
    win._sim_ram.load_bytes(binary)
    win._sim_uart.reset()
    win._sim_cpu.reset()
    win._sim_cycle = 0
    win._pause_requested = False


# ---------------------------------------------------------------------------
# Reset tests
# ---------------------------------------------------------------------------

def test_reset_clears_halted_and_pc():
    """_do_reset() brings CPU back to pc=0 and halted=False."""
    win = MainWin()
    _load_hi(win)
    # run to completion so CPU halts
    win._do_run()
    assert win._sim_cpu.halted()
    # now reset: CPU should be un-halted at pc=0
    win._do_reset()
    assert not win._sim_cpu.halted()
    assert win._sim_cpu.pc() == 0x0000
    assert win._sim_cycle == 0
    print("PASS reset: pc=0x0000  halted=False")


def test_reset_clears_uart():
    """_do_reset() clears accumulated UART output."""
    win = MainWin()
    _load_hi(win)
    win._do_run()
    assert win._sim_uart.output_text() == "Hi"
    win._do_reset()
    assert win._sim_uart.output_text() == ""
    print("PASS reset clears UART")


def test_reset_keeps_ram():
    """_do_reset() does NOT wipe RAM so Run after Reset still works."""
    win = MainWin()
    _load_hi(win)
    win._do_reset()            # reset without re-loading binary
    win._do_run()
    assert win._sim_uart.output_text() == "Hi"
    assert win._sim_cpu.halted()
    print("PASS reset keeps RAM -- Run after Reset produces 'Hi'")


# ---------------------------------------------------------------------------
# Step tests
# ---------------------------------------------------------------------------

def test_step_advances_pc():
    """Each _do_step() advances pc by 4."""
    win = MainWin()
    _load_hi(win)
    assert win._sim_cpu.pc() == 0x0000
    win._do_step()
    assert win._sim_cpu.pc() == 0x0004
    win._do_step()
    assert win._sim_cpu.pc() == 0x0008
    print("PASS step: pc advances by 4 per step")


def test_step_logs_uart_on_out():
    """_do_step() appends a UART log entry when OUT executes."""
    win = MainWin()
    _load_hi(win)
    # steps: LDI r2 | LDI r1,72 | OUT (prints 'H')
    win._do_step()  # LDI r2
    win._do_step()  # LDI r1, 72
    uart_before = win._sim_uart.output_text()
    win._do_step()  # OUT -> 'H'
    uart_after = win._sim_uart.output_text()
    assert uart_after == "H", f"expected 'H', got {uart_after!r}"
    print(f"PASS step: UART after 3 steps = {uart_after!r}")


def test_step_stops_at_halt():
    """_do_step() on a halted CPU logs a message and does not advance."""
    win = MainWin()
    _load_hi(win)
    win._do_run()
    assert win._sim_cpu.halted()
    pc_before = win._sim_cpu.pc()
    win._do_step()  # should be a no-op
    assert win._sim_cpu.pc() == pc_before
    print("PASS step: no advance when halted")


# ---------------------------------------------------------------------------
# Run tests
# ---------------------------------------------------------------------------

def test_run_outputs_hi_and_halts():
    """_do_run(): UART = 'Hi', CPU halted after full execution."""
    win = MainWin()
    _load_hi(win)
    win._do_run()
    assert win._sim_uart.output_text() == "Hi", (
        f"expected 'Hi', got {win._sim_uart.output_text()!r}"
    )
    assert win._sim_cpu.halted()
    print(f"PASS run: UART={win._sim_uart.output_text()!r}  halted=True")


def test_run_cycle_count():
    """_do_run(): sim_cycle equals the number of instructions executed."""
    win = MainWin()
    _load_hi(win)
    win._do_run()
    # Hi program: LDI r2, LDI r1, OUT, LDI r1, OUT, HALT = 6 instructions
    assert win._sim_cycle == 6, f"expected 6, got {win._sim_cycle}"
    print(f"PASS run: cycle count = {win._sim_cycle}")


def test_run_reset_run():
    """Build -> Run -> Reset -> Run again: UART='Hi' both times."""
    win = MainWin()
    _load_hi(win)
    win._do_run()
    assert win._sim_uart.output_text() == "Hi"
    win._do_reset()
    win._do_run()
    assert win._sim_uart.output_text() == "Hi"
    print("PASS run -> reset -> run: UART='Hi' both times")


# ---------------------------------------------------------------------------
# UART Console widget tests
# ---------------------------------------------------------------------------

def test_uart_console_shows_hi_after_run():
    """_uart_console widget shows 'Hi' after _do_run()."""
    win = MainWin()
    _load_hi(win)
    win._do_run()
    got = win._uart_console.toPlainText()
    assert got == "Hi", f"expected 'Hi', got {got!r}"
    print(f"PASS uart_console after run: {got!r}")


def test_uart_console_clears_on_reset():
    """_uart_console widget is empty after _do_reset()."""
    win = MainWin()
    _load_hi(win)
    win._do_run()
    assert win._uart_console.toPlainText() == "Hi"
    win._do_reset()
    got = win._uart_console.toPlainText()
    assert got == "", f"expected '', got {got!r}"
    print("PASS uart_console cleared on reset")


def test_uart_console_updates_per_step():
    """_uart_console shows partial output during step-by-step execution."""
    win = MainWin()
    _load_hi(win)
    # Hi program: LDI r2 | LDI r1,72 | OUT('H') | LDI r1,105 | OUT('i') | HALT
    win._do_step()  # LDI r2
    win._do_step()  # LDI r1, 72
    assert win._uart_console.toPlainText() == ""
    win._do_step()  # OUT -> 'H'
    assert win._uart_console.toPlainText() == "H"
    win._do_step()  # LDI r1, 105
    assert win._uart_console.toPlainText() == "H"
    win._do_step()  # OUT -> 'i'
    assert win._uart_console.toPlainText() == "Hi"
    print(f"PASS uart_console step-by-step: {win._uart_console.toPlainText()!r}")


# ---------------------------------------------------------------------------
# Pause flag test
# ---------------------------------------------------------------------------

def test_pause_sets_flag():
    """_do_pause() sets _pause_requested to True."""
    win = MainWin()
    assert not win._pause_requested
    win._do_pause()
    assert win._pause_requested
    print("PASS pause: flag set")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import tempfile

    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = failed = 0
    for fn in tests:
        try:
            fn()
            passed += 1
        except Exception as exc:
            print(f"  FAIL  {fn.__name__}: {exc}")
            import traceback
            traceback.print_exc()
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
