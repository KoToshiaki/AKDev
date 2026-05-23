# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""v0.1 integration flow test: src/hello.asm -> Build -> Reset -> Run.

Validates the full pipeline end-to-end:
  1. Read src/hello.asm from disk
  2. assemble() -> binary
  3. Load into MainWin simulator RAM
  4. _do_reset() -> _do_run()
  5. Check UART Console, Register View, Bus Trace
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication

_app = QApplication.instance() or QApplication(sys.argv)

from asm.asm import assemble
from ui.win import MainWin

_HELLO_ASM = Path(__file__).parent.parent / "src" / "hello.asm"

# Row indices in the Register View table.
_ROW_PC     = 0
_ROW_CYCLE  = 1
_ROW_HALTED = 2
_ROW_R0     = 3   # r0 .. r15 follow sequentially


def _load_from_file(win: MainWin, path: Path) -> bytes:
    """Read an asm file, assemble it, load into win's RAM, and clear trace."""
    src    = path.read_text(encoding="utf-8")
    binary = assemble(src)
    win._sim_ram.reset()
    win._sim_ram.load_bytes(binary)
    win._sim_uart.reset()
    win._sim_cpu.reset()
    win._sim_cycle = 0
    win._pause_requested = False
    win._sim_bus.clear_trace()
    return binary


# ---------------------------------------------------------------------------
# v0.1 flow: hello.asm exists and assembles
# ---------------------------------------------------------------------------

def test_hello_asm_exists():
    """src/hello.asm is present and non-empty."""
    assert _HELLO_ASM.exists(), f"missing: {_HELLO_ASM}"
    assert _HELLO_ASM.stat().st_size > 0
    print(f"PASS hello.asm exists: {_HELLO_ASM}")


def test_hello_asm_assembles():
    """src/hello.asm assembles without error and produces 6 instructions."""
    src    = _HELLO_ASM.read_text(encoding="utf-8")
    binary = assemble(src)
    assert len(binary) == 6 * 4, f"expected 24 bytes, got {len(binary)}"
    print(f"PASS hello.asm assembles: {len(binary)} bytes")


# ---------------------------------------------------------------------------
# v0.1 flow: full Build -> Reset -> Run pipeline
# ---------------------------------------------------------------------------

def test_v01_uart_console_shows_hi():
    """UART Console shows 'Hi' after hello.asm Run."""
    win = MainWin()
    _load_from_file(win, _HELLO_ASM)
    win._do_reset()
    win._do_run()
    got = win._uart_console.toPlainText()
    assert got == "Hi", f"expected 'Hi', got {got!r}"
    print(f"PASS v0.1 UART Console: {got!r}")


def test_v01_register_view_r1_is_105():
    """Register View shows r1=0x00000069 (105) after hello.asm Run."""
    win = MainWin()
    _load_from_file(win, _HELLO_ASM)
    win._do_reset()
    win._do_run()
    r1 = win._reg_table.item(_ROW_R0 + 1, 1).text()
    assert r1 == "0x00000069", f"expected '0x00000069', got {r1!r}"
    print(f"PASS v0.1 r1 = {r1}")


def test_v01_register_view_halted():
    """Register View shows HALTED after hello.asm Run."""
    win = MainWin()
    _load_from_file(win, _HELLO_ASM)
    win._do_reset()
    win._do_run()
    halted = win._reg_table.item(_ROW_HALTED, 1).text()
    assert halted == "HALTED", f"expected 'HALTED', got {halted!r}"
    print(f"PASS v0.1 halted = {halted}")


def test_v01_register_view_pc_at_halt():
    """Register View shows pc pointing at HALT instruction (0x0014)."""
    win = MainWin()
    _load_from_file(win, _HELLO_ASM)
    win._do_reset()
    win._do_run()
    pc = win._reg_table.item(_ROW_PC, 1).text()
    assert pc == "0x0014", f"expected '0x0014', got {pc!r}"
    print(f"PASS v0.1 pc at HALT = {pc}")


def test_v01_bus_trace_write_H():
    """Bus Trace contains WRITE val=0x00000048 ('H') to UART."""
    win = MainWin()
    _load_from_file(win, _HELLO_ASM)
    win._do_reset()
    win._do_run()
    trace = win._bus_trace.toPlainText()
    assert "WRITE" in trace
    assert "addr=0x0100" in trace
    assert "val=0x00000048" in trace, f"0x48 not found:\n{trace}"
    print("PASS v0.1 bus trace: WRITE 'H' (0x48)")


def test_v01_bus_trace_write_i():
    """Bus Trace contains WRITE val=0x00000069 ('i') to UART."""
    win = MainWin()
    _load_from_file(win, _HELLO_ASM)
    win._do_reset()
    win._do_run()
    trace = win._bus_trace.toPlainText()
    assert "val=0x00000069" in trace, f"0x69 not found:\n{trace}"
    print("PASS v0.1 bus trace: WRITE 'i' (0x69)")


def test_v01_bus_trace_two_uart_writes():
    """Bus Trace shows exactly 2 WRITE entries to UART address 0x0100."""
    win = MainWin()
    _load_from_file(win, _HELLO_ASM)
    win._do_reset()
    win._do_run()
    lines = win._bus_trace.toPlainText().splitlines()
    uart_writes = [l for l in lines if "WRITE" in l and "addr=0x0100" in l]
    assert len(uart_writes) == 2, (
        f"expected 2 UART writes, got {len(uart_writes)}:\n"
        + "\n".join(uart_writes)
    )
    print(f"PASS v0.1 bus trace: {len(uart_writes)} UART writes")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
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
